#!/usr/bin/env python3
"""Physical GRID10 Xeno node process body + orchestrator.

Runs as real, independent OS processes (fork()'d after the model is loaded once in the
parent, so weight pages are shared copy-on-write -- empirically verified: ~1.5GB of a
2GB per-process RSS footprint is Shared_Clean, i.e. genuinely one physical copy across
all children, not N copies). Node count, weight-copy count and decode concurrency are
recorded separately (see criterion_weight_node_decode_separation.json).

Protocol: see grid10_fabric.py. Ordinary nodes read S1, select+claim OPEN tasks, do real
short greedy-decoded model work, and emit NODE_RESULT/v1 into the outbox (the Result
Channel -- writable by ordinary nodes by design, distinct from S1 canonical `scopes`
state, which only a leased coordinator may fold results into via CAS-checked commit).
"""
from __future__ import annotations

import json
import os
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from grid10_fabric import Fabric, FabricError, result_packet, summary_packet, dg, cj, LEASE_TTL_SECONDS

MODEL = None
TOK = None


def load_model_once(model_path: str):
    global MODEL, TOK
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(1)
    TOK = AutoTokenizer.from_pretrained(model_path)
    MODEL = AutoModelForCausalLM.from_pretrained(model_path, dtype=torch.bfloat16, low_cpu_mem_usage=True)
    MODEL.eval()


def cognitive_answer(prompt: str, max_new_tokens: int = 6) -> str:
    """Real greedy-decoded model call. This is the 'model decides what is cognitively
    sensible' half of ZECP11 -- the fabric below still separately decides what may
    actually be claimed/committed, regardless of what the model produces."""
    import torch

    inputs = TOK(prompt, return_tensors="pt")
    with torch.no_grad():
        out = MODEL.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
    return TOK.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()


def node_loop(
    node_id: str,
    capability: str,
    fabric_path: str,
    model_path: str,
    out_evidence: str,
    max_iters: int = 6,
    poll_sleep: float = 0.15,
    become_coordinator_candidate: bool = True,
    self_pause_after_join: float = 0.0,
    scenario: str = "default",
):
    """Entry point run inside a forked child. Everything here is genuinely executing
    as an independent OS process (own PID, own address space except COW-shared model
    pages inherited from the fork)."""
    if MODEL is None:
        load_model_once(model_path)

    f = Fabric(Path(fabric_path))
    pid = os.getpid()
    f.runtime_join(node_id, capability, pid)
    if self_pause_after_join > 0:
        time.sleep(self_pause_after_join)

    events: list[dict] = []
    events.append({"event": "AUTONOMOUS_JOIN", "node_id": node_id, "pid": pid, "capability": capability, "ts": time.time()})

    coordinator_lease = None
    coordinator_token = None
    coordinator_scope = None

    for i in range(max_iters):
        try:
            f.runtime_heartbeat(node_id, True)
            snap = f.snapshot()

            # try to claim an open task matching our capability (claim-awareness: we only
            # ever look at snap.tasks freshly re-read from S1, never cache stale claims)
            eligible = [
                t for t in snap.tasks
                if t["status"] == "OPEN" and t["claimed_by"] is None and t["capability"] == capability
            ]
            if eligible:
                task = sorted(eligible, key=lambda t: (-int(t["priority"]), t["task_id"]))[0]
                try:
                    f.runtime_claim_task(task["task_id"], node_id, expected_epoch=snap.epoch)
                    events.append({"event": "CLAIM_AWARENESS_CLAIM_OK", "node_id": node_id, "task_id": task["task_id"], "ts": time.time()})
                    payload_in = json.loads(task["payload_json"])
                    prompt = payload_in.get("prompt")
                    answer = cognitive_answer(prompt) if prompt else payload_in.get("answer", "no-op")
                    fresh = f.snapshot()
                    result_payload = {"task_id": task["task_id"], "answer": answer}
                    # Hyperposition rule: if the task itself declares genuinely unresolved
                    # alternatives, the node carries them through verbatim rather than
                    # collapsing to its own single greedy answer -- the model's answer is
                    # recorded ALONGSIDE the alternatives, never in place of them.
                    if "unresolved_alternatives" in payload_in:
                        result_payload["unresolved_alternatives"] = payload_in["unresolved_alternatives"]
                    packet = result_packet(node_id, fresh, task["scope"], result_payload)
                    f.emit_node_result(packet)
                    events.append({"event": "NODE_RESULT_EMITTED", "node_id": node_id, "task_id": task["task_id"], "answer": answer, "packet_digest": packet["packet_digest"], "ts": time.time()})
                except FabricError as exc:
                    events.append({"event": "CLAIM_LOST_RACE", "node_id": node_id, "task_id": task["task_id"], "error": str(exc), "ts": time.time()})

            # dynamic coordinator attempt: try to become coordinator for a scope we have
            # pending outbox work for, but back off cleanly if someone already holds it.
            if become_coordinator_candidate and coordinator_lease is None:
                pending_scopes = f.outbox_pending_scopes()
                for scope in pending_scopes:
                    elected = f.elect_coordinator(scope, candidate_node_ids=[node_id])
                    if elected is not None:
                        coordinator_lease, coordinator_token = elected
                        coordinator_scope = scope
                        events.append({"event": "DYNAMIC_COORDINATOR_LEASE_GRANTED", "node_id": node_id, "scope": scope, "lease_id": coordinator_lease["lease_id"], "ts": time.time()})
                        break

            if coordinator_lease is not None:
                drained = f.coordinator_drain_and_commit(coordinator_scope, coordinator_lease, coordinator_token)
                for d in drained:
                    events.append({"event": "COORDINATOR_COMMIT", "node_id": node_id, **d, "ts": time.time()})
                # LEASE RENEWAL FIX (found during the 2026-08-27 world-model operational run):
                # coordinator_commit() enforces LEASE_TTL_SECONDS from the lease's ORIGINAL
                # granted_ts with no renewal path -- a coordinator that keeps its lease past
                # that TTL (normal for any run longer than ~8s) silently stops being able to
                # commit ANYTHING further, forever, while still believing it holds a valid
                # lease (the DB's valid=1 flag is untouched; only the runtime TTL check in
                # coordinator_commit fails). Before this fix, a short one-shot acceptance test
                # never ran long enough to hit this; a genuinely sustained multi-tick run does,
                # and canonical S1 silently stopped updating after the first ~8s per scope.
                # Fix: if we ever see COORDINATOR_LEASE_EXPIRED (or any other commit_error) on
                # our own lease, explicitly revoke it and drop our local reference so the next
                # loop iteration re-elects a fresh lease (possibly ourselves again) instead of
                # continuing to hold a lease that can never successfully commit again.
                if any(d.get("commit_error") for d in drained):
                    try:
                        f.revoke_lease(coordinator_lease["lease_id"])
                    except FabricError:
                        pass
                    events.append({"event": "COORDINATOR_LEASE_SELF_RENEW_AFTER_EXPIRY", "node_id": node_id, "scope": coordinator_scope, "old_lease_id": coordinator_lease["lease_id"], "errors": [d.get("commit_error") for d in drained if d.get("commit_error")], "ts": time.time()})
                    coordinator_lease = None
                    coordinator_token = None
                    coordinator_scope = None
                if scenario == "release_after_one_drain" and drained and coordinator_lease is not None:
                    f.revoke_lease(coordinator_lease["lease_id"])
                    events.append({"event": "COORDINATOR_SELF_RELEASE", "node_id": node_id, "lease_id": coordinator_lease["lease_id"], "ts": time.time()})
                    coordinator_lease = None

            if scenario == "attempt_illegal_direct_write":
                try:
                    f.ordinary_write_attempt(node_id)
                except FabricError as exc:
                    events.append({"event": "ORDINARY_WRITE_REJECTED", "node_id": node_id, "error": str(exc), "ts": time.time()})

        except Exception as exc:  # noqa: BLE001 - node loop must never crash silently
            events.append({"event": "NODE_LOOP_ERROR", "node_id": node_id, "error": repr(exc), "ts": time.time()})
        time.sleep(poll_sleep)

    Path(out_evidence).write_text(json.dumps({"node_id": node_id, "pid": pid, "events": events}, indent=2))

"""Regression test for the lease-renewal fix in tools/grid10_node.py (2026-08-27).

Real bug found while running GRID10 as an actual sustained multi-tick world-model
simulation (not the original one-shot acceptance test): a dynamic coordinator's lease
enforces LEASE_TTL_SECONDS from its ORIGINAL grant time with no renewal path. Any run
longer than the TTL silently stops committing anything further into canonical S1 for
that scope, even though the coordinator node keeps polling/looping and reporting
healthy -- the outbox just accumulates forever, uncommitted, invisible unless someone
checks outbox consumed-counts directly.

This test uses a REAL sqlite-backed Fabric (tmp file, no mocking of the fabric itself)
and a tiny LEASE_TTL_SECONDS (monkeypatched) so the expiry condition is reachable in a
fast unit test without needing the real model -- cognitive_answer is monkeypatched to a
trivial stub since only the coordinator-renewal control flow is under test here, not
model behavior.
"""
import importlib.util
import sys
import threading
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"

spec_fabric = importlib.util.spec_from_file_location("grid10_fabric", TOOLS / "grid10_fabric.py")
grid10_fabric = importlib.util.module_from_spec(spec_fabric)
sys.modules["grid10_fabric"] = grid10_fabric
spec_fabric.loader.exec_module(grid10_fabric)

spec_node = importlib.util.spec_from_file_location("grid10_node", TOOLS / "grid10_node.py")
grid10_node = importlib.util.module_from_spec(spec_node)
sys.modules["grid10_node"] = grid10_node
spec_node.loader.exec_module(grid10_node)

from grid10_fabric import Fabric  # noqa: E402


def test_coordinator_self_renews_after_lease_expiry(tmp_path, monkeypatch):
    fabric_path = tmp_path / "s1.sqlite"
    f = Fabric(fabric_path)
    f.seed_scope("scope-a")

    # tiny TTL so expiry is reachable within a fast unit test
    monkeypatch.setattr(grid10_fabric, "LEASE_TTL_SECONDS", 0.05)

    # stub out the model entirely -- this test is about coordinator lease bookkeeping,
    # not model output
    monkeypatch.setattr(grid10_node, "MODEL", "stub")
    monkeypatch.setattr(grid10_node, "cognitive_answer", lambda prompt, max_new_tokens=6: "ok")

    # seed one task before the node even starts
    f.seed_task("task-1", "scope-a", 90, "reason", {"prompt": "hello"})
    ev1 = tmp_path / "ev1.json"

    # Run node_loop as ONE continuous call spanning both the first commit AND the TTL
    # expiry AND a second task arriving mid-flight -- this matches the real production
    # scenario (one long-running node process across an entire multi-tick simulation),
    # not two separate short-lived calls. max_iters/poll_sleep sized so the loop keeps
    # polling for ~0.3s total, comfortably past the 0.05s TTL.
    thread = threading.Thread(
        target=grid10_node.node_loop,
        kwargs=dict(
            node_id="node-1", capability="reason", fabric_path=str(fabric_path), model_path="unused",
            out_evidence=str(ev1), max_iters=40, poll_sleep=0.01, become_coordinator_candidate=True,
        ),
    )
    thread.start()

    # give it time to claim+emit+elect+commit task-1 (first commit, fresh lease)
    time.sleep(0.05)
    # let the (tiny) TTL actually elapse while the SAME coordinator still holds the lease
    time.sleep(0.1)
    # now seed a second task -- with the OLD fix-free code, this coordinator would keep
    # holding its now-expired-but-DB-valid=1 lease forever and never notice, so this
    # packet would sit in outbox permanently uncommitted.
    f.seed_task("task-2", "scope-a", 90, "reason", {"prompt": "hello again"})

    thread.join(timeout=5.0)
    assert not thread.is_alive(), "node_loop did not finish in time"

    scope_row_final = [dict(r) for r in f.snapshot().scopes if r["scope"] == "scope-a"][0]
    assert scope_row_final["evidence_count"] == 2, (
        "both task-1 (before expiry) and task-2 (after expiry) must have been committed -- "
        f"got evidence_count={scope_row_final['evidence_count']}; if this is 1, the "
        "lease-expiry-without-renewal bug has regressed (task-2 stuck in outbox forever)"
    )

    outbox_pending = f.outbox_pending_scopes()
    assert "scope-a" not in outbox_pending, "no packets should be left permanently stuck in outbox"

    import json
    events = json.loads(ev1.read_text())["events"]
    renew_events = [e for e in events if e["event"] == "COORDINATOR_LEASE_SELF_RENEW_AFTER_EXPIRY"]
    assert len(renew_events) >= 1, "expected at least one self-renewal event once the lease expired"

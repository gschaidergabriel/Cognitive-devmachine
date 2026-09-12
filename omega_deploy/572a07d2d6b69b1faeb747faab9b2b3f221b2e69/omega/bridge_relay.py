from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import socket
import subprocess
import time
from pathlib import Path
from typing import Any

from .alignment import (
    Decision,
    EffectBinding,
    ExecutorObservation,
    OutcomeUnknown,
    dispatch,
)
from .bridge_transport import (
    BridgeOutcomeUnknown,
    BridgeTarget,
    GitBranchTransport,
    command_from_effect,
)
from .policy_kernel import PolicyKernel
from .unified_store import UnifiedStore, canon, digest, now


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


class LocalSandboxExecutor:
    """Effect executor for the OMEGA VPS sandbox itself.

    Policy is deliberately not embedded here. This executor only realizes an already
    exact-bound request after the external PolicyKernel has emitted ALLOW.
    """

    def __init__(self, receipts_dir: Path) -> None:
        self.receipts_dir = receipts_dir
        self.receipts_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, binding: EffectBinding, request: dict[str, Any]) -> tuple[ExecutorObservation, dict[str, Any]]:
        started = now()
        op = str(request.get("op", ""))
        status = "PASS"
        exit_code: int | None = 0
        stdout = ""
        stderr = ""
        meta: dict[str, Any] = {}
        try:
            if op == "status":
                stdout = json.dumps(
                    {
                        "hostname": socket.gethostname(),
                        "pid": os.getpid(),
                        "cwd": os.getcwd(),
                        "loadavg": os.getloadavg() if hasattr(os, "getloadavg") else None,
                    },
                    ensure_ascii=False,
                )
            elif op == "read_file":
                path = Path(str(request["path"])).expanduser()
                raw = path.read_bytes()
                meta = {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "truncated": len(raw) > 262144}
                stdout = raw[:262144].decode("utf-8", errors="replace")
            elif op == "write_text":
                path = Path(str(request["path"])).expanduser()
                path.parent.mkdir(parents=True, exist_ok=True)
                raw = str(request.get("content", "")).encode("utf-8")
                path.write_bytes(raw)
                meta = {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            elif op == "exec":
                command = str(request["command"])
                cwd = str(request.get("cwd") or "/workspace")
                timeout = min(3600, max(1, int(request.get("timeout_seconds", 120))))
                proc = subprocess.run(
                    ["bash", "-lc", command], cwd=cwd, text=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    timeout=timeout, check=False,
                )
                exit_code = proc.returncode
                stdout = proc.stdout[-65536:]
                stderr = proc.stderr[-65536:]
                status = "PASS" if proc.returncode == 0 else "FAIL"
            elif op == "screenshot":
                status = "FAIL"
                exit_code = 127
                stderr = "OMEGA_SCREENSHOT_BACKEND_NOT_ADMITTED_OR_CONFIGURED"
            else:
                status = "FAIL"
                exit_code = 2
                stderr = f"UNSUPPORTED_OP:{op}"
        except subprocess.TimeoutExpired as exc:
            # The process may have produced effects before timeout. That uncertainty
            # is escalated to OutcomeUnknown by the caller; never classify as retryable.
            raise OutcomeUnknown("LOCAL_EXEC_TIMEOUT_OUTCOME_UNKNOWN_NO_AUTOMATIC_REPLAY") from exc
        except Exception as exc:
            raise OutcomeUnknown("LOCAL_EXEC_EXCEPTION_OUTCOME_UNKNOWN_NO_AUTOMATIC_REPLAY") from exc

        result_payload = {
            "status": status,
            "exit_code": exit_code,
            "stdout_tail": stdout,
            "stderr_tail": stderr,
            "meta": meta,
        }
        result_sha = digest(result_payload)
        receipt = {
            "schema": "OMEGA_LOCAL_EFFECT_RECEIPT/v1",
            "effect_id": binding.effect_id,
            "binding_id": binding.binding_id,
            "organ_id": binding.organ_id,
            "owner": binding.owner_id,
            "machine_id": binding.machine_id,
            "request_sha256": binding.request_sha256,
            "started_at": started,
            "finished_at": now(),
            **result_payload,
            "result_sha256": result_sha,
            "execution_boundary": "OMEGA_VPS_SANDBOX",
        }
        receipt_path = self.receipts_dir / f"{binding.effect_id}.json"
        _atomic_json(receipt_path, receipt)
        obs = ExecutorObservation(
            effect_id=binding.effect_id,
            binding_id=binding.binding_id,
            invocation_id=binding.invocation_id,
            tool_use_id=binding.tool_use_id,
            delegation_id=binding.delegation_id,
            child_identity_sha256=binding.child_identity_sha256,
            request_sha256=binding.request_sha256,
            organ_id=binding.organ_id,
            result_id=str(receipt_path),
            result_sha256=result_sha,
        )
        return obs, receipt


class Relay:
    def __init__(
        self,
        *,
        runtime_root: Path,
        repo_root: Path,
        db_path: Path,
        carrier_repo: Path,
        policy_path: Path,
        router_path: Path,
    ) -> None:
        self.runtime_root = runtime_root
        self.repo_root = repo_root
        self.store = UnifiedStore(db_path, repo_root / "schema")
        self.policy = PolicyKernel.from_path(policy_path)
        self.router_cfg = json.loads(router_path.read_text(encoding="utf-8"))
        self.organs = {str(o["organ_id"]): o for o in self.router_cfg["organs"]}
        self.transport = GitBranchTransport(
            carrier_repo=carrier_repo,
            work_root=runtime_root / "bridge_git",
            poll_seconds=2.0,
        )
        self.local = LocalSandboxExecutor(runtime_root / "receipts")
        (runtime_root / "outbox").mkdir(parents=True, exist_ok=True)
        (runtime_root / "relay_results").mkdir(parents=True, exist_ok=True)

    def _target(self, organ_id: str) -> BridgeTarget | None:
        cfg = self.organs.get(organ_id)
        if not cfg:
            return None
        if cfg.get("kind") != "host_frankenstein":
            return None
        return BridgeTarget(
            organ_id=organ_id,
            owner_id=str(cfg["owner_id"]),
            machine_id=str(cfg["machine_id"]),
            control_branch=str(cfg["control_branch"]),
            results_branch=str(cfg["results_branch"]),
        )

    def _binding(self, intent: dict[str, Any], request: dict[str, Any], cfg: dict[str, Any]) -> EffectBinding:
        seed = digest({"effect_id": intent["effect_id"], "frame_id": intent.get("frame_id"), "organ": intent["organ_id"]})
        child_sha = digest({
            "organ_id": intent["organ_id"],
            "owner_id": cfg.get("owner_id"),
            "machine_id": cfg.get("machine_id"),
            "kind": cfg.get("kind"),
        })
        return EffectBinding.prepare(
            effect_id=str(intent["effect_id"]),
            invocation_id="inv_" + seed[:32],
            tool_use_id="tool_" + seed[32:56],
            delegation_id="deleg_" + seed[8:40],
            child_identity_sha256=child_sha,
            request=request,
            organ_id=str(intent["organ_id"]),
            owner_id=str(cfg.get("owner_id")) if cfg.get("owner_id") is not None else None,
            machine_id=str(cfg.get("machine_id")) if cfg.get("machine_id") is not None else None,
            runtime_epoch_id=str(intent.get("runtime_epoch_id")) if intent.get("runtime_epoch_id") else None,
        )

    def _host_executor(self, binding: EffectBinding, request: dict[str, Any], target: BridgeTarget) -> tuple[ExecutorObservation, dict[str, Any], str, str]:
        command = command_from_effect(binding.effect_id, target, request)
        receipt, command_digest, receipt_digest = self.transport.dispatch(
            target, command, receipt_timeout=float(request.get("receipt_timeout_seconds", 240))
        )
        obs = ExecutorObservation(
            effect_id=binding.effect_id,
            binding_id=binding.binding_id,
            invocation_id=binding.invocation_id,
            tool_use_id=binding.tool_use_id,
            delegation_id=binding.delegation_id,
            child_identity_sha256=binding.child_identity_sha256,
            request_sha256=binding.request_sha256,
            organ_id=binding.organ_id,
            result_id=str(receipt.get("command_id")),
            result_sha256=receipt_digest,
        )
        return obs, receipt, command_digest, receipt_digest

    def process_intent(self, path: Path) -> dict[str, Any]:
        intent = json.loads(path.read_text(encoding="utf-8"))
        if intent.get("schema") != "OMEGA_GRID_EFFECT_INTENT/v1":
            return {"state": "IGNORED", "reason": "NOT_GRID_EFFECT_INTENT", "path": str(path)}
        effect_id = str(intent["effect_id"])
        organ_id = str(intent["organ_id"])
        cfg = self.organs.get(organ_id)
        if cfg is None:
            result = {"state": "BLOCKED", "effect_id": effect_id, "reason": "UNREGISTERED_ORGAN"}
            _atomic_json(self.runtime_root / "relay_results" / f"{effect_id}.json", result)
            return result

        owner_id = str(cfg.get("owner_id")) if cfg.get("owner_id") is not None else None
        machine_id = str(cfg.get("machine_id")) if cfg.get("machine_id") is not None else None
        self.store.record_effect_intent(intent, owner_id=owner_id, machine_id=machine_id)

        task = intent.get("task") if isinstance(intent.get("task"), dict) else {}
        request = task.get("effect") or task.get("execution")
        if not isinstance(request, dict):
            self.store.update_effect_state(effect_id, authority_state="NOT_REQUESTED", dispatch_state="BLOCKED")
            self.store.upsert_relay(effect_id=effect_id, organ_id=organ_id, state="BLOCKED", last_error="NO_EXECUTABLE_EFFECT_DESCRIPTOR")
            result = {"state":"BLOCKED","effect_id":effect_id,"organ_id":organ_id,"reason":"NO_EXECUTABLE_EFFECT_DESCRIPTOR"}
            _atomic_json(self.runtime_root / "relay_results" / f"{effect_id}.json", result)
            return result

        binding = self._binding(intent, request, cfg)
        gate = self.policy.authorize(binding, request)
        self.store.record_policy_decision(
            decision_id=gate.decision_id,effect_id=effect_id,binding_id=binding.binding_id,
            authority_ref=gate.authority_ref,decision=gate.decision.value,
            reason="POLICY_KERNEL_" + gate.decision.value,request_digest=binding.request_sha256,
            organ_id=organ_id,owner_id=owner_id,machine_id=machine_id,
        )
        self.store.update_effect_state(effect_id, authority_state=gate.decision.value)

        if gate.decision is not Decision.ALLOW:
            self.store.update_effect_state(effect_id, dispatch_state="BLOCKED")
            self.store.upsert_relay(effect_id=effect_id, organ_id=organ_id, state="BLOCKED", last_error=gate.decision.value)
            result = {"state":"BLOCKED","effect_id":effect_id,"organ_id":organ_id,"decision":gate.decision.value,"decision_id":gate.decision_id}
            _atomic_json(self.runtime_root / "relay_results" / f"{effect_id}.json", result)
            return result

        self.store.upsert_relay(effect_id=effect_id, organ_id=organ_id, state="DISPATCHING", increment_attempt=True)
        requested_at = now()
        host_receipt: dict[str, Any] | None = None
        command_digest: str | None = None
        receipt_digest: str | None = None
        try:
            if cfg.get("kind") == "central_runtime":
                obs_holder: dict[str, Any] = {}
                def executor(b: EffectBinding) -> ExecutorObservation:
                    obs, receipt = self.local.execute(b, request)
                    obs_holder["receipt"] = receipt
                    return obs
                dispatch_result = dispatch(binding, authorize=lambda _b: gate, executor=executor)
                host_receipt = obs_holder.get("receipt")
                receipt_digest = dispatch_result.observation.result_sha256 if dispatch_result.observation else None
            elif cfg.get("kind") == "host_frankenstein":
                target = self._target(organ_id)
                if target is None:
                    raise RuntimeError("HOST_TARGET_CONFIG_INCOMPLETE")
                holder: dict[str, Any] = {}
                def executor(b: EffectBinding) -> ExecutorObservation:
                    obs, receipt, cmd_d, rec_d = self._host_executor(b, request, target)
                    holder.update(receipt=receipt, command_digest=cmd_d, receipt_digest=rec_d)
                    return obs
                dispatch_result = dispatch(binding, authorize=lambda _b: gate, executor=executor)
                host_receipt = holder.get("receipt")
                command_digest = holder.get("command_digest")
                receipt_digest = holder.get("receipt_digest")
            else:
                raise RuntimeError(f"UNSUPPORTED_ORGAN_KIND:{cfg.get('kind')}")
        except (OutcomeUnknown, BridgeOutcomeUnknown) as exc:
            self.store.update_effect_state(effect_id, dispatch_state="UNKNOWN")
            self.store.upsert_relay(effect_id=effect_id, organ_id=organ_id, state="UNKNOWN", command_digest=command_digest, receipt_digest=receipt_digest, last_error=str(exc))
            self.store.record_effect_receipt(
                effect_id=effect_id,subject_id=organ_id,owner_id=owner_id,machine_id=machine_id,
                runtime_epoch_id=binding.runtime_epoch_id,action_kind=str(request.get("op","UNKNOWN")),
                request_digest=binding.request_sha256,status="UNKNOWN",requested_at=requested_at,
                completed_at=now(),metadata={"error":str(exc),"no_automatic_replay":True},
            )
            result = {"state":"UNKNOWN","effect_id":effect_id,"organ_id":organ_id,"error":str(exc),"automatic_replay":False}
            _atomic_json(self.runtime_root / "relay_results" / f"{effect_id}.json", result)
            return result
        except Exception as exc:
            # If dispatch was definitely not crossed this is BLOCKED/FAILED; callers
            # must still inspect the relay ledger before creating any new effect id.
            self.store.update_effect_state(effect_id, dispatch_state="FAILED")
            self.store.upsert_relay(effect_id=effect_id, organ_id=organ_id, state="FAILED", command_digest=command_digest, receipt_digest=receipt_digest, last_error=f"{type(exc).__name__}:{exc}")
            result = {"state":"FAILED","effect_id":effect_id,"organ_id":organ_id,"error":f"{type(exc).__name__}:{exc}"}
            _atomic_json(self.runtime_root / "relay_results" / f"{effect_id}.json", result)
            return result

        status = str((host_receipt or {}).get("status", "PASS"))
        final_state = "COMPLETED" if status in {"PASS", "FAIL", "TIMEOUT", "ERROR"} else "COMPLETED"
        self.store.update_effect_state(effect_id, dispatch_state=final_state)
        self.store.upsert_relay(effect_id=effect_id, organ_id=organ_id, state=final_state, command_digest=command_digest, receipt_digest=receipt_digest)
        self.store.record_effect_receipt(
            effect_id=effect_id,subject_id=organ_id,owner_id=owner_id,machine_id=machine_id,
            runtime_epoch_id=binding.runtime_epoch_id,action_kind=str(request.get("op","UNKNOWN")),
            request_digest=binding.request_sha256,result_digest=receipt_digest,status=status,
            requested_at=requested_at,completed_at=now(),
            receipt_locator=str((host_receipt or {}).get("command_id") or (host_receipt or {}).get("effect_id") or "LOCAL"),
            metadata=host_receipt or {},
        )
        self.store.bridge_message(direction="IN",sender=organ_id,recipient="omega",kind="EFFECT_RECEIPT",payload=host_receipt or {},correlation_id=effect_id)
        result = {
            "state":final_state,"effect_id":effect_id,"organ_id":organ_id,
            "effect_status":status,"policy_decision":gate.decision.value,
            "receipt_digest":receipt_digest,"host_receipt":host_receipt,
        }
        _atomic_json(self.runtime_root / "relay_results" / f"{effect_id}.json", result)
        return result

    def run_once(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for path in sorted((self.runtime_root / "outbox").glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if payload.get("schema") != "OMEGA_GRID_EFFECT_INTENT/v1":
                continue
            effect_id = str(payload.get("effect_id", ""))
            if not effect_id:
                continue
            with self.store.connect() as con:
                row = con.execute("SELECT state FROM relay_ledger WHERE effect_id=?",(effect_id,)).fetchone()
            if row and str(row[0]) in {"COMPLETED","BLOCKED","UNKNOWN","FAILED"}:
                continue
            results.append(self.process_intent(path))
        return results

    def run_forever(self, interval: float) -> None:
        while True:
            try:
                self.run_once()
            except Exception as exc:
                _atomic_json(
                    self.runtime_root / "relay_results" / "LAST_RELAY_ERROR.json",
                    {"at":now(),"error":f"{type(exc).__name__}:{exc}"},
                )
            time.sleep(max(0.5, interval))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime-root", default=os.getenv("OMEGA_RUNTIME_ROOT", "/workspace/omega_runtime/state"))
    ap.add_argument("--repo-root", default=os.getenv("OMEGA_REPO_ROOT", "/workspace/oMEGA"))
    ap.add_argument("--db", default=os.getenv("OMEGA_UNIFIED_DB", "/workspace/omega_runtime/data/omega_unified.db"))
    ap.add_argument("--carrier-repo", default=os.getenv("OMEGA_CARRIER_REPO", "/workspace/clay-global-research-entity"))
    ap.add_argument("--policy", default=os.getenv("OMEGA_AUTONOMY_POLICY", "/workspace/oMEGA/config/autonomy_policy.json"))
    ap.add_argument("--router", default=os.getenv("OMEGA_ROUTER_CONFIG", "/workspace/oMEGA/config/organ_router.json"))
    ap.add_argument("--interval", type=float, default=float(os.getenv("OMEGA_RELAY_INTERVAL", "2")))
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    relay = Relay(
        runtime_root=Path(args.runtime_root), repo_root=Path(args.repo_root), db_path=Path(args.db),
        carrier_repo=Path(args.carrier_repo), policy_path=Path(args.policy), router_path=Path(args.router),
    )
    if args.once:
        print(json.dumps(relay.run_once(), ensure_ascii=False, indent=2)); return 0
    relay.run_forever(args.interval); return 0


if __name__ == "__main__":
    raise SystemExit(main())

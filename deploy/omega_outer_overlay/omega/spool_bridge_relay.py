from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from .bridge_relay import Relay
from .bridge_transport import BridgeError, BridgeOutcomeUnknown, BridgeTarget


def _json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def _sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(_json_bytes(payload))
    os.replace(tmp, path)


class SpoolTransport:
    """Credential-free transport across the OMEGA sandbox boundary.

    OMEGA writes an exact, attributed command envelope to a filesystem spool.
    A privileged relay outside the sandbox is the only component allowed to
    translate that envelope into Git branch mailbox traffic. The return path is
    another envelope containing a host receipt. UNKNOWN is terminal here: it is
    surfaced to bridge_relay and is never auto-replayed.
    """

    def __init__(self, spool_root: str | Path, poll_seconds: float = 2.0) -> None:
        self.root = Path(spool_root)
        self.outbox = self.root / "outbox"
        self.inbox = self.root / "inbox"
        self.outbox.mkdir(parents=True, exist_ok=True)
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.poll_seconds = max(0.25, float(poll_seconds))

    @staticmethod
    def _validate_target(target: BridgeTarget, command: dict[str, Any]) -> None:
        if str(command.get("machine_id")) != target.machine_id:
            raise BridgeError("command machine_id does not match selected target")
        if str(command.get("owner")) != target.owner_id:
            raise BridgeError("command owner does not match selected target")
        if not str(command.get("command_id", "")).strip():
            raise BridgeError("command_id missing")

    def _stage(self, target: BridgeTarget, command: dict[str, Any]) -> tuple[str, str]:
        self._validate_target(target, command)
        command_id = str(command["command_id"])
        command_raw = _json_bytes(command)
        command_sha = _sha_bytes(command_raw)
        envelope = {
            "schema": "OMEGA_OUTER_BRIDGE_COMMAND/v1",
            "command_id": command_id,
            "organ_id": target.organ_id,
            "machine_id": target.machine_id,
            "owner": target.owner_id,
            "control_branch": target.control_branch,
            "results_branch": target.results_branch,
            "command_sha256": command_sha,
            "command": command,
        }
        path = self.outbox / f"{command_id}.json"
        if path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                raise BridgeOutcomeUnknown(
                    f"existing outer spool envelope unreadable for {command_id}; no automatic replay"
                ) from exc
            stable_keys = (
                "schema", "command_id", "organ_id", "machine_id", "owner",
                "control_branch", "results_branch", "command_sha256", "command",
            )
            if any(existing.get(key) != envelope.get(key) for key in stable_keys):
                raise BridgeOutcomeUnknown(
                    f"outer spool command collision for {command_id}; no automatic replay"
                )
        else:
            _atomic_json(path, envelope)
        return command_id, command_sha

    def _read_outer_receipt(
        self,
        *,
        target: BridgeTarget,
        command_id: str,
        command_sha: str,
    ) -> tuple[dict[str, Any], str]:
        path = self.inbox / f"{command_id}.json"
        raw = path.read_bytes()
        outer = json.loads(raw.decode("utf-8"))
        if outer.get("schema") != "OMEGA_OUTER_BRIDGE_RECEIPT/v1":
            raise BridgeOutcomeUnknown("outer receipt schema mismatch; no automatic replay")
        checks = {
            "command_id": command_id,
            "organ_id": target.organ_id,
            "machine_id": target.machine_id,
            "owner": target.owner_id,
            "control_branch": target.control_branch,
            "results_branch": target.results_branch,
            "command_sha256": command_sha,
        }
        for key, expected in checks.items():
            if str(outer.get(key)) != str(expected):
                raise BridgeOutcomeUnknown(
                    f"outer receipt {key} mismatch expected={expected!r} got={outer.get(key)!r}; no automatic replay"
                )
        state = str(outer.get("state", "")).upper()
        if state == "UNKNOWN":
            raise BridgeOutcomeUnknown(
                str(outer.get("reason") or "outer relay outcome unknown; no automatic replay")
            )
        if state != "COMPLETED":
            raise BridgeError(f"outer relay terminal state is {state or 'MISSING'}")

        receipt = outer.get("host_receipt")
        if not isinstance(receipt, dict):
            raise BridgeOutcomeUnknown("outer receipt missing host_receipt; no automatic replay")
        if str(receipt.get("command_id")) != command_id:
            raise BridgeOutcomeUnknown("host receipt command_id mismatch; no automatic replay")
        if str(receipt.get("machine_id")) != target.machine_id:
            raise BridgeOutcomeUnknown("host receipt machine_id mismatch; no automatic replay")
        if str(receipt.get("owner")) != target.owner_id:
            raise BridgeOutcomeUnknown("host receipt owner mismatch; no automatic replay")

        canonical_receipt_sha = _sha_bytes(_json_bytes(receipt))
        claimed_canonical = str(outer.get("host_receipt_canonical_sha256") or "")
        if claimed_canonical and claimed_canonical != canonical_receipt_sha:
            raise BridgeOutcomeUnknown("host receipt canonical digest mismatch; no automatic replay")
        transport_digest = str(outer.get("host_receipt_file_sha256") or canonical_receipt_sha)
        return receipt, transport_digest

    def dispatch(
        self,
        target: BridgeTarget,
        command: dict[str, Any],
        *,
        receipt_timeout: float = 180.0,
    ) -> tuple[dict[str, Any], str, str]:
        command_id, command_sha = self._stage(target, command)
        deadline = time.monotonic() + max(1.0, float(receipt_timeout))
        receipt_path = self.inbox / f"{command_id}.json"
        while time.monotonic() < deadline:
            if receipt_path.exists():
                receipt, receipt_digest = self._read_outer_receipt(
                    target=target,
                    command_id=command_id,
                    command_sha=command_sha,
                )
                return receipt, command_sha, receipt_digest
            time.sleep(self.poll_seconds)
        raise BridgeOutcomeUnknown(
            f"outer relay receipt timeout for {command_id}; no automatic replay"
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime-root", default=os.getenv("OMEGA_RUNTIME_ROOT", "/workspace/omega_runtime/state"))
    ap.add_argument("--repo-root", default=os.getenv("OMEGA_REPO_ROOT", "/workspace/oMEGA"))
    ap.add_argument("--db", default=os.getenv("OMEGA_UNIFIED_DB", "/workspace/omega_runtime/data/omega_unified.db"))
    ap.add_argument("--carrier-repo", default=os.getenv("OMEGA_CARRIER_REPO", "/workspace/clay-global-research-entity"))
    ap.add_argument("--policy", default=os.getenv("OMEGA_AUTONOMY_POLICY", "/workspace/oMEGA/config/autonomy_policy.json"))
    ap.add_argument("--router", default=os.getenv("OMEGA_ROUTER_CONFIG", "/workspace/oMEGA/config/organ_router.json"))
    ap.add_argument("--spool-root", default=os.getenv("OMEGA_OUTER_SPOOL", "/workspace/omega_runtime/state/outer_bridge"))
    ap.add_argument("--interval", type=float, default=float(os.getenv("OMEGA_RELAY_INTERVAL", "2")))
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    relay = Relay(
        runtime_root=Path(args.runtime_root),
        repo_root=Path(args.repo_root),
        db_path=Path(args.db),
        carrier_repo=Path(args.carrier_repo),
        policy_path=Path(args.policy),
        router_path=Path(args.router),
    )
    relay.transport = SpoolTransport(Path(args.spool_root), poll_seconds=min(2.0, max(0.25, args.interval)))
    if args.once:
        print(json.dumps(relay.run_once(), ensure_ascii=False, indent=2))
        return 0
    relay.run_forever(args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

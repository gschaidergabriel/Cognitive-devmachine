from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import signal
import time
from pathlib import Path
from typing import Any, Protocol

from .bridge_transport import (
    BridgeError,
    BridgeOutcomeUnknown,
    BridgeTarget,
    GitBranchTransport,
)


def _json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def _sha(payload: Any) -> str:
    return hashlib.sha256(_json_bytes(payload)).hexdigest()


def _fsync_dir(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        fd = os.open(path, flags)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _atomic_json(path: Path, payload: Any) -> None:
    """Durable atomic JSON write for the effect journal/receipt boundary."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    raw = _json_bytes(payload)
    with open(tmp, "wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)
    _fsync_dir(path.parent)


def _now() -> str:
    import datetime as dt

    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


class DispatchTransport(Protocol):
    def dispatch(
        self,
        target: BridgeTarget,
        command: dict[str, Any],
        *,
        receipt_timeout: float = 180.0,
    ) -> tuple[dict[str, Any], str, str]: ...


class OuterBridgeWorker:
    """Privileged consumer for the credential-free OMEGA outer spool.

    The sandbox side may only place immutable command envelopes into ``outbox``.
    This worker runs outside that sandbox and is the sole component translating an
    admitted spool envelope into the existing Git-backed FranKenstein Local Bridge.

    Safety invariant: a command journaled as DISPATCHING without a terminal outer
    receipt is recovered as UNKNOWN and is never dispatched again automatically.
    That deliberately sacrifices liveness to preserve effect exactly-once semantics
    across process crashes and ambiguous Git/network outcomes.
    """

    TERMINAL = {"COMPLETED", "FAILED", "UNKNOWN"}

    def __init__(
        self,
        *,
        spool_root: str | Path,
        transport: DispatchTransport,
        receipt_timeout: float = 240.0,
    ) -> None:
        self.root = Path(spool_root)
        self.outbox = self.root / "outbox"
        self.inbox = self.root / "inbox"
        self.journal = self.root / "journal"
        self.status_path = self.root / "OUTER_WORKER_STATUS.json"
        self.lock_path = self.root / "outer-worker.lock"
        for path in (self.outbox, self.inbox, self.journal):
            path.mkdir(parents=True, exist_ok=True)
        self.transport = transport
        self.receipt_timeout = max(1.0, float(receipt_timeout))
        self.stop = False
        self.started_at = _now()
        self.counts = {
            "completed": 0,
            "failed": 0,
            "unknown": 0,
            "ignored": 0,
        }

    @staticmethod
    def _target(envelope: dict[str, Any]) -> BridgeTarget:
        return BridgeTarget(
            organ_id=str(envelope["organ_id"]),
            owner_id=str(envelope["owner"]),
            machine_id=str(envelope["machine_id"]),
            control_branch=str(envelope["control_branch"]),
            results_branch=str(envelope["results_branch"]),
        )

    @staticmethod
    def _validate_envelope(envelope: dict[str, Any]) -> tuple[BridgeTarget, dict[str, Any], str, str]:
        if envelope.get("schema") != "OMEGA_OUTER_BRIDGE_COMMAND/v1":
            raise BridgeError("outer command schema mismatch")
        command = envelope.get("command")
        if not isinstance(command, dict):
            raise BridgeError("outer command payload missing")
        command_id = str(envelope.get("command_id") or "").strip()
        if not command_id:
            raise BridgeError("outer command_id missing")
        if str(command.get("command_id") or "") != command_id:
            raise BridgeError("outer command_id does not match embedded command")

        target = OuterBridgeWorker._target(envelope)
        if str(command.get("machine_id")) != target.machine_id:
            raise BridgeError("embedded command machine_id mismatch")
        if str(command.get("owner")) != target.owner_id:
            raise BridgeError("embedded command owner mismatch")

        expected_sha = str(envelope.get("command_sha256") or "")
        actual_sha = _sha(command)
        if not expected_sha or expected_sha != actual_sha:
            raise BridgeError("outer command canonical digest mismatch")
        return target, command, command_id, expected_sha

    def _journal_path(self, command_id: str) -> Path:
        return self.journal / f"{command_id}.json"

    def _receipt_path(self, command_id: str) -> Path:
        return self.inbox / f"{command_id}.json"

    def _base_receipt(
        self,
        envelope: dict[str, Any],
        *,
        state: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema": "OMEGA_OUTER_BRIDGE_RECEIPT/v1",
            "state": state,
            "created_at": _now(),
            "command_id": str(envelope.get("command_id") or ""),
            "organ_id": str(envelope.get("organ_id") or ""),
            "machine_id": str(envelope.get("machine_id") or ""),
            "owner": str(envelope.get("owner") or ""),
            "control_branch": str(envelope.get("control_branch") or ""),
            "results_branch": str(envelope.get("results_branch") or ""),
            "command_sha256": str(envelope.get("command_sha256") or ""),
            "automatic_replay": False,
        }
        if reason:
            payload["reason"] = reason
        return payload

    def _write_terminal(
        self,
        envelope: dict[str, Any],
        *,
        state: str,
        reason: str | None = None,
        host_receipt: dict[str, Any] | None = None,
        host_receipt_file_sha256: str | None = None,
    ) -> dict[str, Any]:
        command_id = str(envelope.get("command_id") or "")
        result = self._base_receipt(envelope, state=state, reason=reason)
        if host_receipt is not None:
            result["host_receipt"] = host_receipt
            result["host_receipt_canonical_sha256"] = _sha(host_receipt)
        if host_receipt_file_sha256:
            result["host_receipt_file_sha256"] = host_receipt_file_sha256

        # Receipt first: if the process dies after this durable write, the sandbox
        # already has a terminal answer and a restart cannot redispatch the effect.
        _atomic_json(self._receipt_path(command_id), result)
        _atomic_json(
            self._journal_path(command_id),
            {
                "schema": "OMEGA_OUTER_BRIDGE_JOURNAL/v1",
                "state": state,
                "updated_at": _now(),
                "command_id": command_id,
                "command_sha256": str(envelope.get("command_sha256") or ""),
                "reason": reason,
            },
        )
        self.counts[state.lower()] = self.counts.get(state.lower(), 0) + 1
        return result

    def _recover_inflight(self, envelope: dict[str, Any], journal: dict[str, Any]) -> dict[str, Any] | None:
        state = str(journal.get("state") or "").upper()
        if state != "DISPATCHING":
            return None
        return self._write_terminal(
            envelope,
            state="UNKNOWN",
            reason=(
                "outer worker recovered an incomplete DISPATCHING journal after restart; "
                "effect outcome may be ambiguous and is not automatically replayed"
            ),
        )

    def process_path(self, path: Path) -> dict[str, Any]:
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.counts["ignored"] += 1
            return {"state": "IGNORED", "path": str(path), "reason": f"UNREADABLE:{type(exc).__name__}"}

        command_id = str(envelope.get("command_id") or path.stem)
        receipt_path = self._receipt_path(command_id)
        if receipt_path.exists():
            self.counts["ignored"] += 1
            return {"state": "ALREADY_TERMINAL", "command_id": command_id}

        journal_path = self._journal_path(command_id)
        if journal_path.exists():
            try:
                previous = json.loads(journal_path.read_text(encoding="utf-8"))
            except Exception:
                return self._write_terminal(
                    envelope,
                    state="UNKNOWN",
                    reason="outer worker journal unreadable; no automatic replay",
                )
            recovered = self._recover_inflight(envelope, previous)
            if recovered is not None:
                return recovered
            if str(previous.get("state") or "").upper() in self.TERMINAL:
                # A terminal journal without its corresponding inbox receipt is an
                # inconsistent durable state. Never hang and never dispatch again.
                return self._write_terminal(
                    envelope,
                    state="UNKNOWN",
                    reason="terminal outer journal exists without terminal inbox receipt; no automatic replay",
                )

        try:
            target, command, command_id, command_sha = self._validate_envelope(envelope)
        except Exception as exc:
            return self._write_terminal(
                envelope,
                state="FAILED",
                reason=f"PRE_DISPATCH_VALIDATION:{type(exc).__name__}:{exc}",
            )

        # This journal write is fsync'd before the first call that may cross the Git
        # effect boundary. Reentry can therefore distinguish NEW from ambiguous work.
        _atomic_json(
            journal_path,
            {
                "schema": "OMEGA_OUTER_BRIDGE_JOURNAL/v1",
                "state": "DISPATCHING",
                "started_at": _now(),
                "updated_at": _now(),
                "command_id": command_id,
                "command_sha256": command_sha,
                "organ_id": target.organ_id,
                "machine_id": target.machine_id,
                "owner": target.owner_id,
            },
        )

        try:
            host_receipt, published_command_sha, host_receipt_file_sha = self.transport.dispatch(
                target,
                command,
                receipt_timeout=self.receipt_timeout,
            )
            if published_command_sha != command_sha:
                raise BridgeOutcomeUnknown(
                    "transport command digest differs from staged spool digest; no automatic replay"
                )
            if str(host_receipt.get("command_id")) != command_id:
                raise BridgeOutcomeUnknown("host receipt command_id mismatch; no automatic replay")
            if str(host_receipt.get("machine_id")) != target.machine_id:
                raise BridgeOutcomeUnknown("host receipt machine_id mismatch; no automatic replay")
            if str(host_receipt.get("owner")) != target.owner_id:
                raise BridgeOutcomeUnknown("host receipt owner mismatch; no automatic replay")
            return self._write_terminal(
                envelope,
                state="COMPLETED",
                host_receipt=host_receipt,
                host_receipt_file_sha256=host_receipt_file_sha,
            )
        except BridgeOutcomeUnknown as exc:
            return self._write_terminal(
                envelope,
                state="UNKNOWN",
                reason=str(exc),
            )
        except BridgeError as exc:
            # GitBranchTransport only raises BridgeOutcomeUnknown once a dispatch may
            # have crossed the bridge. Plain BridgeError is therefore a known
            # pre-dispatch/configuration failure and safe to terminalize as FAILED.
            return self._write_terminal(
                envelope,
                state="FAILED",
                reason=f"BRIDGE_ERROR:{exc}",
            )
        except Exception as exc:
            # Any untyped exception after DISPATCHING is epistemically ambiguous.
            return self._write_terminal(
                envelope,
                state="UNKNOWN",
                reason=f"UNTYPED_POST_DISPATCH_EXCEPTION:{type(exc).__name__}:{exc}",
            )

    def process_once(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for path in sorted(self.outbox.glob("*.json")):
            results.append(self.process_path(path))
        self.snapshot()
        return results

    def snapshot(self) -> None:
        _atomic_json(
            self.status_path,
            {
                "schema": "OMEGA_OUTER_BRIDGE_WORKER_STATUS/v1",
                "updated_at": _now(),
                "started_at": self.started_at,
                "pid": os.getpid(),
                "spool_root": str(self.root),
                "counts": dict(self.counts),
                "stopping": self.stop,
            },
        )

    def run_forever(self, interval: float = 1.0) -> int:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock = open(self.lock_path, "w", encoding="utf-8")
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 3
        lock.write(str(os.getpid()))
        lock.flush()
        os.fsync(lock.fileno())
        signal.signal(signal.SIGTERM, lambda *_: setattr(self, "stop", True))
        signal.signal(signal.SIGINT, lambda *_: setattr(self, "stop", True))
        try:
            while not self.stop:
                self.process_once()
                time.sleep(max(0.25, float(interval)))
        finally:
            self.stop = True
            self.snapshot()
            lock.close()
        return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spool-root", default=os.getenv("OMEGA_OUTER_SPOOL", "/workspace/omega_runtime/state/outer_bridge"))
    ap.add_argument("--carrier-repo", default=os.getenv("OMEGA_CARRIER_REPO", "/workspace/omega_runtime/carrier_repo"))
    ap.add_argument("--work-root", default=os.getenv("OMEGA_OUTER_GIT_WORK_ROOT", "/workspace/omega_runtime/outer_bridge_git"))
    ap.add_argument("--interval", type=float, default=float(os.getenv("OMEGA_OUTER_INTERVAL", "1")))
    ap.add_argument("--receipt-timeout", type=float, default=float(os.getenv("OMEGA_OUTER_RECEIPT_TIMEOUT", "240")))
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    transport = GitBranchTransport(
        carrier_repo=Path(args.carrier_repo),
        work_root=Path(args.work_root),
        poll_seconds=min(2.0, max(0.25, args.interval)),
    )
    worker = OuterBridgeWorker(
        spool_root=Path(args.spool_root),
        transport=transport,
        receipt_timeout=args.receipt_timeout,
    )
    if args.once:
        print(json.dumps(worker.process_once(), indent=2, ensure_ascii=False))
        return 0
    return worker.run_forever(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())

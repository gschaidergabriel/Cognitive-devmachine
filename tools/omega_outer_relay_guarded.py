#!/usr/bin/env python3
from __future__ import annotations

"""Hardened entrypoint for the privileged OMEGA outer relay.

This wraps ``tools/omega_outer_relay.py`` without changing its effect semantics.
The only semantic delta is at the *pre-dispatch validation boundary*:

- if a well-formed outer envelope is rejected before any mailbox publication,
  write a provenance-bound ``REJECTED`` receipt back to the OMEGA spool;
- never let OMEGA sit until its receipt timeout merely because the privileged
  side rejected an envelope synchronously;
- keep malformed/unbindable input fail-closed and never fabricate a receipt;
- preserve ``UNKNOWN`` exclusively for cases where an effect may already have
  crossed the dispatch boundary or the outcome cannot be reconciled.

The original relay remains the implementation of publication, host receipt
validation, collision handling and UNKNOWN/no-replay semantics.
"""

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

import omega_outer_relay as base


_REQUIRED_BINDING_KEYS = (
    "organ_id",
    "machine_id",
    "owner",
    "control_branch",
    "results_branch",
    "command_sha256",
)


class GuardedOuterRelay(base.OuterRelay):
    def _terminal_rejected(
        self,
        *,
        command_id: str,
        env: dict[str, Any],
        reason: str,
    ) -> dict[str, Any]:
        """Return a known-safe rejection to OMEGA when dispatch was not crossed.

        We intentionally echo only the binding fields already present in the
        staged outer envelope.  If any are missing, the input is not bindable;
        in that case no inbox receipt is written because manufacturing missing
        identity would be worse than timing out as UNKNOWN.
        """
        missing = [k for k in _REQUIRED_BINDING_KEYS if not str(env.get(k, "")).strip()]
        if missing:
            return {
                "state": "REJECTED_UNBOUND",
                "command_id": command_id,
                "reason": reason,
                "missing_binding_fields": missing,
                "dispatch_crossed": False,
                "automatic_replay": False,
            }

        payload = {
            "schema": "OMEGA_OUTER_BRIDGE_RECEIPT/v1",
            "command_id": command_id,
            "organ_id": str(env["organ_id"]),
            "machine_id": str(env["machine_id"]),
            "owner": str(env["owner"]),
            "control_branch": str(env["control_branch"]),
            "results_branch": str(env["results_branch"]),
            "command_sha256": str(env["command_sha256"]),
            "transport_boundary": "VPS_OUTER_HOST_GITHUB_ACTIONS",
            "github_run_id": os.getenv("GITHUB_RUN_ID"),
            "runner_name": os.getenv("RUNNER_NAME"),
            "state": "REJECTED",
            "reason": reason,
            "dispatch_crossed": False,
            "effect_may_have_occurred": False,
            "automatic_replay": False,
            "finished_at": time.time(),
        }
        self._save_ledger(command_id, payload)
        self._write_inbox(command_id, payload)
        return payload

    def process_name(self, filename: str) -> dict[str, Any]:
        command_id_from_name = filename[:-5]
        if not base.COMMAND_ID_RE.fullmatch(command_id_from_name):
            return {"state": "IGNORED", "reason": "UNSAFE_FILENAME", "filename": filename}

        outbox_path, _, _ = self._paths(command_id_from_name)
        try:
            raw_env = self.runtime.read_bytes(outbox_path)
            decoded = json.loads(raw_env.decode("utf-8"))
        except Exception as exc:
            return {
                "state": "REJECTED_UNBOUND",
                "command_id": command_id_from_name,
                "reason": f"{type(exc).__name__}:{exc}",
                "dispatch_crossed": False,
                "automatic_replay": False,
            }

        if not isinstance(decoded, dict):
            return {
                "state": "REJECTED_UNBOUND",
                "command_id": command_id_from_name,
                "reason": "OUTER_ENVELOPE_NOT_OBJECT",
                "dispatch_crossed": False,
                "automatic_replay": False,
            }
        env: dict[str, Any] = decoded

        # Validate here *before* delegating to the original relay.  The original
        # implementation returns REJECTED only to stdout on this path; OMEGA then
        # waits until its receipt timeout.  A known pre-dispatch rejection is a
        # terminal, non-ambiguous result and therefore belongs in the inbox.
        try:
            base.OuterRelay.validate_envelope(env)
        except Exception as exc:
            return self._terminal_rejected(
                command_id=command_id_from_name,
                env=env,
                reason=f"{type(exc).__name__}:{exc}",
            )

        if str(env.get("command_id")) != command_id_from_name:
            return self._terminal_rejected(
                command_id=command_id_from_name,
                env=env,
                reason="FILENAME_COMMAND_ID_MISMATCH",
            )

        # From here onward the original relay owns all effectful behavior,
        # including exact publication, host receipt verification and UNKNOWN.
        return super().process_name(filename)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.getenv("GITHUB_WORKSPACE", "."))
    ap.add_argument("--container", default=os.getenv("OMEGA_CONTAINER", "clay-direct-dev"))
    ap.add_argument(
        "--spool-root",
        default=os.getenv("OMEGA_OUTER_SPOOL", "/workspace/omega_runtime/state/outer_bridge"),
    )
    ap.add_argument(
        "--ledger-root",
        default=os.getenv(
            "OMEGA_OUTER_LEDGER",
            str(Path.home() / ".local/state/omega-outer-relay/ledger"),
        ),
    )
    ap.add_argument(
        "--receipt-timeout",
        type=float,
        default=float(os.getenv("OMEGA_OUTER_RECEIPT_TIMEOUT", "220")),
    )
    ap.add_argument("--duration-seconds", type=float, default=0.0)
    ap.add_argument("--poll-seconds", type=float, default=2.0)
    args = ap.parse_args()

    runtime = base.ContainerRuntime.detect(args.container)
    relay = GuardedOuterRelay(
        runtime=runtime,
        mailbox=base.GitMailbox(Path(args.repo).resolve()),
        spool_root=args.spool_root,
        ledger_root=Path(args.ledger_root).expanduser(),
        receipt_timeout=args.receipt_timeout,
    )
    deadline = time.monotonic() + max(0.0, args.duration_seconds)
    first = True
    while first or time.monotonic() < deadline:
        first = False
        results = relay.run_once()
        for result in results:
            print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
        if args.duration_seconds <= 0:
            break
        time.sleep(max(0.5, args.poll_seconds))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

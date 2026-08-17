from __future__ import annotations

import hashlib
import json
from pathlib import Path

TIER2_EXIT_CODE = 86
TIER2_TERMINATION_MESSAGE_PATH = "/dev/termination-log"
TIER2_SIGNAL_SCHEMA = "clayverse.tier2-fatal/v1"

_ALLOWED_REASONS = frozenset({"RECOVERY_INTEGRITY_ERROR"})


def build_tier2_signal(reason: str, detail: str) -> dict[str, object]:
    if reason not in _ALLOWED_REASONS:
        raise ValueError("unadmitted tier2 reason")
    if not isinstance(detail, str):
        raise TypeError("tier2 detail must be text")
    detail_sha256 = hashlib.sha256(detail.encode("utf-8", errors="replace")).hexdigest()
    return {
        "schema": TIER2_SIGNAL_SCHEMA,
        "action": "REPLACE_FULL_SANDBOX",
        "reason": reason,
        "detail_sha256": detail_sha256,
        "exit_code": TIER2_EXIT_CODE,
        "replay_external_effects": False,
        "canonical_state": "UNTRUSTED_UNTIL_RECOVERED",
    }


def write_tier2_signal(
    reason: str,
    detail: str,
    *,
    path: str | Path = TIER2_TERMINATION_MESSAGE_PATH,
) -> str:
    payload = json.dumps(
        build_tier2_signal(reason, detail),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    encoded = payload.encode("utf-8")
    if len(encoded) > 1024:
        raise RuntimeError("tier2 termination message exceeded internal bound")
    Path(path).write_bytes(encoded)
    return payload


def request_tier2_replacement(
    reason: str,
    detail: str,
    *,
    path: str | Path = TIER2_TERMINATION_MESSAGE_PATH,
) -> int:
    """Emit a bounded Kubernetes termination signal and return the reserved exit code.

    The outer orchestrator must replace the full Pod/Kata sandbox on exit 86 even
    if the termination-message write itself failed. This prevents a canonical-
    integrity failure from degrading into an in-place container restart merely
    because the diagnostic file was unavailable.
    """
    try:
        write_tier2_signal(reason, detail, path=path)
    except OSError:
        pass
    return TIER2_EXIT_CODE

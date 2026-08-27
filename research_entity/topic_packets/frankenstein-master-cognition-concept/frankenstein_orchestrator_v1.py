"""Canonical Frankenstein Bauleiter entrypoint.

The provider-backed 2026-08-27 implementation is preserved byte-for-byte beside
this file as a quarantined donor. This entrypoint resolves current canonical
provider authority *before* loading that donor. Under HARD_OFF it performs no
provider import, key lookup, network call, Aider dispatch, or fallback dispatch.

Even if provider authority is opened by a future explicit authority state, the
quarantined donor remains blocked until its direct-dispatch implementation is
independently converted from whole-file replacement to the exact-preimage safe
patch primitive in ``frankenstein_safe_edit_v1.py``.
"""
from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path

from frankenstein_authority_gate_v1 import provider_authority_state, require_provider_routes
from frankenstein_safe_edit_v1 import donor_dispatch_uses_safe_patch

REPO_ROOT = Path(__file__).resolve().parents[3]
QUARANTINED_IMPLEMENTATION = Path(__file__).with_name(
    "frankenstein_orchestrator_v1_PROVIDER_QUARANTINED_854f6bc.py"
)


def authority_status() -> dict:
    state = provider_authority_state(REPO_ROOT)
    donor_safe = False
    if QUARANTINED_IMPLEMENTATION.is_file():
        donor_safe = donor_dispatch_uses_safe_patch(QUARANTINED_IMPLEMENTATION.read_text())
    return {
        **state,
        "entrypoint": str(Path(__file__).resolve()),
        "quarantined_implementation": str(QUARANTINED_IMPLEMENTATION),
        "provider_imports_loaded": False,
        "secret_lookups_performed": 0,
        "provider_calls_performed": 0,
        "direct_dispatch_safe_patch_integrated": donor_safe,
    }


def _require_safe_direct_dispatch_donor() -> None:
    if not QUARANTINED_IMPLEMENTATION.is_file():
        raise SystemExit(f"quarantined donor missing: {QUARANTINED_IMPLEMENTATION}")
    source = QUARANTINED_IMPLEMENTATION.read_text()
    if not donor_dispatch_uses_safe_patch(source):
        raise SystemExit(
            "quarantined donor blocked: dispatch_helper_task_direct still permits "
            "legacy whole-file apply_file_blocks; independently integrate "
            "frankenstein_safe_edit_v1.safe_apply_verified_patch with exact "
            "preimage hashes before provider execution can resume"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority-status", action="store_true")
    args, passthrough = parser.parse_known_args()
    if args.authority_status:
        print(json.dumps(authority_status(), indent=2, sort_keys=True))
        return

    # Preserve authority-first behavior under current HARD_OFF: no provider
    # donor import or provider/network work occurs before this gate succeeds.
    require_provider_routes("frankenstein_orchestrator_v1", REPO_ROOT)

    # Future authority opening is still insufficient by itself. The executable
    # donor must also prove that its direct dispatch uses the independent
    # exact-preimage patch primitive and no longer calls whole-file apply.
    _require_safe_direct_dispatch_donor()

    import sys
    sys.argv = [str(QUARANTINED_IMPLEMENTATION), *passthrough]
    runpy.run_path(str(QUARANTINED_IMPLEMENTATION), run_name="__main__")


if __name__ == "__main__":
    main()

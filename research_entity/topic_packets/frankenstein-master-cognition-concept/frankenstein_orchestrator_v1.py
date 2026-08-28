"""Canonical Frankenstein Bauleiter entrypoint.

The provider-backed 2026-08-27 implementation is preserved byte-for-byte beside
this file as a quarantined donor. This entrypoint resolves current canonical
provider authority *before* loading that donor. Under HARD_OFF it performs no
provider import, key lookup, network call, Aider dispatch, or fallback dispatch.
"""
from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path

from frankenstein_authority_gate_v1 import provider_authority_state, require_provider_routes

REPO_ROOT = Path(__file__).resolve().parents[3]
QUARANTINED_IMPLEMENTATION = Path(__file__).with_name(
    "frankenstein_orchestrator_v1_PROVIDER_QUARANTINED_854f6bc.py"
)


def authority_status() -> dict:
    state = provider_authority_state(REPO_ROOT)
    return {
        **state,
        "entrypoint": str(Path(__file__).resolve()),
        "quarantined_implementation": str(QUARANTINED_IMPLEMENTATION),
        "provider_imports_loaded": False,
        "secret_lookups_performed": 0,
        "provider_calls_performed": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority-status", action="store_true")
    args, passthrough = parser.parse_known_args()
    if args.authority_status:
        print(json.dumps(authority_status(), indent=2, sort_keys=True))
        return

    require_provider_routes("frankenstein_orchestrator_v1", REPO_ROOT)
    if not QUARANTINED_IMPLEMENTATION.is_file():
        raise SystemExit(f"quarantined donor missing: {QUARANTINED_IMPLEMENTATION}")

    import sys
    sys.argv = [str(QUARANTINED_IMPLEMENTATION), *passthrough]
    runpy.run_path(str(QUARANTINED_IMPLEMENTATION), run_name="__main__")


if __name__ == "__main__":
    main()

"""Canonical Frankenstein Bauleiter entrypoint.

The provider-backed 2026-08-27 implementation is preserved beside this file as
a quarantined donor.  This entrypoint resolves current canonical provider
authority *before* loading that donor.  Under HARD_OFF it performs no provider
import, key lookup, network call, Aider dispatch, or fallback dispatch.

A second fail-closed gate protects future authority reopenings: the quarantined
donor may not execute until an independently reviewed exact-edit integration is
bound to an explicit SHA-256 allowlist.  The current allowlist is intentionally
empty because the current donor still uses whole-file FILE blocks plus a shrink
heuristic.  Adding the safe-edit primitive alone does not mint integration
credit; a future change must wire it into the donor, review that exact donor,
and then bind its exact digest here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path

from frankenstein_authority_gate_v1 import provider_authority_state, require_provider_routes

REPO_ROOT = Path(__file__).resolve().parents[3]
QUARANTINED_IMPLEMENTATION = Path(__file__).with_name(
    "frankenstein_orchestrator_v1_PROVIDER_QUARANTINED_854f6bc.py"
)
SAFE_EDIT_PRIMITIVE = Path(__file__).with_name("frankenstein_safe_edit_v1.py")
SAFE_EDIT_ABI = "FRANKENSTEIN_SAFE_EDIT_RECEIPT/v1"

# Fail closed.  This must remain None until the exact quarantined donor has been
# independently reviewed after safe-edit integration.  A future admitted change
# must set this to that donor file's exact SHA-256; source presence or passing
# unrelated tests is not sufficient.
SAFE_EDIT_AUDITED_DONOR_SHA256: str | None = None


class UnsafeDonorBlocked(RuntimeError):
    pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_edit_donor_state() -> dict:
    donor_exists = QUARANTINED_IMPLEMENTATION.is_file()
    primitive_exists = SAFE_EDIT_PRIMITIVE.is_file()
    observed_sha256 = _sha256_file(QUARANTINED_IMPLEMENTATION) if donor_exists else None
    audited_sha256 = SAFE_EDIT_AUDITED_DONOR_SHA256
    admitted = bool(
        donor_exists
        and primitive_exists
        and audited_sha256
        and observed_sha256 == audited_sha256
    )
    return {
        "schema": "FRANKENSTEIN_SAFE_EDIT_DONOR_GATE/v1",
        "safe_edit_abi": SAFE_EDIT_ABI,
        "donor_exists": donor_exists,
        "safe_edit_primitive_exists": primitive_exists,
        "observed_donor_sha256": observed_sha256,
        "audited_donor_sha256": audited_sha256,
        "safe_edit_integrated_donor_admitted": admitted,
        "evidence_scope": "SOURCE_IDENTITY_GATE_ONLY",
        "runtime_promotion": "NONE",
    }


def require_safe_edit_integrated_donor() -> dict:
    state = safe_edit_donor_state()
    if not state["safe_edit_integrated_donor_admitted"]:
        raise UnsafeDonorBlocked(
            "Frankenstein quarantined donor is not bound to an independently "
            "audited safe-edit SHA-256; whole-file direct-dispatch remains blocked"
        )
    return state


def authority_status() -> dict:
    state = provider_authority_state(REPO_ROOT)
    return {
        **state,
        "entrypoint": str(Path(__file__).resolve()),
        "quarantined_implementation": str(QUARANTINED_IMPLEMENTATION),
        "provider_imports_loaded": False,
        "secret_lookups_performed": 0,
        "provider_calls_performed": 0,
        "safe_edit_donor_gate": safe_edit_donor_state(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority-status", action="store_true")
    parser.add_argument("--safe-edit-status", action="store_true")
    args, passthrough = parser.parse_known_args()
    if args.authority_status:
        print(json.dumps(authority_status(), indent=2, sort_keys=True))
        return
    if args.safe_edit_status:
        print(json.dumps(safe_edit_donor_state(), indent=2, sort_keys=True))
        return

    # Order matters: current authority is resolved before even inspecting or
    # loading provider-backed donor code.  If authority later reopens, the exact
    # independently-audited donor identity must still pass the second gate.
    require_provider_routes("frankenstein_orchestrator_v1", REPO_ROOT)
    require_safe_edit_integrated_donor()

    import sys
    sys.argv = [str(QUARANTINED_IMPLEMENTATION), *passthrough]
    runpy.run_path(str(QUARANTINED_IMPLEMENTATION), run_name="__main__")


if __name__ == "__main__":
    main()

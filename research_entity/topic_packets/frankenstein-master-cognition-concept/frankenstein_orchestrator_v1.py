"""Canonical Frankenstein Bauleiter entrypoint.

The provider-backed 2026-08-27 implementation is preserved byte-for-byte beside
this file as a quarantined donor. This entrypoint resolves current canonical
provider authority *before* loading that donor. Under HARD_OFF it performs no
provider import, key lookup, network call, Aider dispatch, or fallback dispatch.

A second, source-identity gate is intentionally independent of provider authority:
even if a later authority re-opens provider routes, the quarantined donor remains
blocked until its existing-file mutation path has been integrated with the
current preimage-bound edit contract, independently reviewed, and bound here by
exact SHA-256 identities. Authority admission alone must never resurrect the
unsafe whole-file rewrite lineage exposed by the 2026-08-28 counterexample.
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
MUTATION_CONTRACT = Path(__file__).with_name("frankenstein_edit_contract_v1.py")
MUTATION_AUDIT_SCHEMA = "FRANKENSTEIN_MUTATION_AUDIT_GATE/v1"

# Fail closed by construction. Populate these values only after the *integrated*
# donor is independently reviewed at exact source identity. Merely adding the
# contract, passing its component tests, or re-opening provider authority does
# not establish integration and must not make this gate pass.
AUDITED_DONOR_SHA256: str | None = None
AUDITED_MUTATION_CONTRACT_SHA256: str | None = None


class UnsafeMutationDonorBlocked(RuntimeError):
    pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mutation_audit_state() -> dict:
    paths = {
        "donor": QUARANTINED_IMPLEMENTATION,
        "mutation_contract": MUTATION_CONTRACT,
    }
    observed = {
        name: _sha256_file(path) if path.is_file() else None
        for name, path in paths.items()
    }
    audited = {
        "donor": AUDITED_DONOR_SHA256,
        "mutation_contract": AUDITED_MUTATION_CONTRACT_SHA256,
    }
    admitted = all(
        observed[name] is not None
        and audited[name] is not None
        and observed[name] == audited[name]
        for name in observed
    )
    return {
        "schema": MUTATION_AUDIT_SCHEMA,
        "observed_sha256": observed,
        "audited_sha256": audited,
        "all_required_sources_present": all(value is not None for value in observed.values()),
        "mutation_audit_admitted": admitted,
        "evidence_scope": "SOURCE_IDENTITY_GATE_ONLY",
        "runtime_promotion": "NONE",
    }


def require_mutation_audited_donor() -> dict:
    state = mutation_audit_state()
    if not state["mutation_audit_admitted"]:
        raise UnsafeMutationDonorBlocked(
            "Frankenstein quarantined donor is not bound to an independently "
            "audited donor+preimage-edit-contract source identity; direct "
            "provider-backed execution remains blocked"
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
        "mutation_audit_gate": mutation_audit_state(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority-status", action="store_true")
    parser.add_argument("--mutation-audit-status", action="store_true")
    args, passthrough = parser.parse_known_args()
    if args.authority_status:
        print(json.dumps(authority_status(), indent=2, sort_keys=True))
        return
    if args.mutation_audit_status:
        print(json.dumps(mutation_audit_state(), indent=2, sort_keys=True))
        return

    # Provider authority remains the first gate. This preserves the current
    # HARD_OFF property: no provider-backed donor import or secret/network path
    # occurs while authority is closed. If authority later opens, exact audited
    # mutation-source identity is independently required before donor execution.
    require_provider_routes("frankenstein_orchestrator_v1", REPO_ROOT)
    require_mutation_audited_donor()

    import sys
    sys.argv = [str(QUARANTINED_IMPLEMENTATION), *passthrough]
    runpy.run_path(str(QUARANTINED_IMPLEMENTATION), run_name="__main__")


if __name__ == "__main__":
    main()

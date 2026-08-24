#!/usr/bin/env python3
"""Supervisor-8.71 safe entrypoint for the FREE Evidence Forge.

Installs deterministic model-command execution admission before the base Forge
cycle can evaluate a worker-authored candidate. This wrapper is a convergence
surface; it does not grant candidate output canonical truth or runtime promotion.
"""
from __future__ import annotations

import asyncio

import forge_execution_admission_871 as admission
import run_free_evidence_forge as base

_ORIGINAL_VALIDATE = base.validate_candidate
base.safe_command = admission.safe_command
base.run_cmd = admission.run_cmd


def validate_candidate(con, row):
    return admission.validate_candidate_with_admission(base, _ORIGINAL_VALIDATE, con, row)


base.validate_candidate = validate_candidate


def main() -> int:
    return asyncio.run(base.main(base.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())

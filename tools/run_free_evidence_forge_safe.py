#!/usr/bin/env python3
"""Supervisor-8.71 safe entrypoint for the existing FREE Evidence Forge.

The legacy Forge remains the discovery/storage implementation.  Before its event
loop starts, this entrypoint replaces only candidate validation with the strict
candidate/execution boundary.  No worker-authored command is executed on the local
host; apply-clean candidates stop at EXECUTION_BLOCKED pending a separately
admitted isolated zero-cost executor.
"""
from __future__ import annotations

import asyncio

import run_free_evidence_forge as forge
from forge_candidate_execution_boundary import validate_candidate_without_execution


LEGACY_VALIDATE_CANDIDATE = forge.validate_candidate
forge.validate_candidate = lambda con, row: validate_candidate_without_execution(forge, con, row)
SAFE_FORGE_BINDING = "CLAY_FORGE_CANDIDATE_EXECUTION_BOUNDARY/v1"


if __name__ == "__main__":
    raise SystemExit(asyncio.run(forge.main(forge.parse_args())))

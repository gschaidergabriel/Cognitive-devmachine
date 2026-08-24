#!/usr/bin/env python3
"""Guarded compatibility entry for the legacy adaptive FREE_ONLY swarm controller.

The legacy implementation is imported only after an EntityOS/HCU typed provider
admission proves every pooled provider path has cost_class=FREE. Historical audit
strings remain source-provenance only: research_entity/global/MINI_ENTITY_CLAYCOG_APPROX1B_TRAINING_DIRECTIVE.md
and continuous FREE_ONLY Mini Entity `go` macrocycle. Environment attestation flags
alone are never sufficient admission authority.
"""
from __future__ import annotations

import os
import sys

from provider_admission_v1 import ProviderAdmissionError, load_provider_admission


def _fail_closed_before_legacy_import() -> None:
    path = os.environ.get("CLAY_PROVIDER_ADMISSION_FILE", "")
    if not path:
        print("FREE_SWARM_ADMISSION_BLOCKED:CLAY_PROVIDER_ADMISSION_FILE_REQUIRED", file=sys.stderr)
        raise SystemExit(78)
    try:
        admission = load_provider_admission(path)
    except ProviderAdmissionError as exc:
        print(f"FREE_SWARM_ADMISSION_BLOCKED:{exc}", file=sys.stderr)
        raise SystemExit(78) from exc
    # Compatibility flags are derived only after typed admission. They are not
    # authority; the typed object is revalidated on every import.
    os.environ["CLAY_TYPED_PROVIDER_ADMISSION_VERIFIED"] = "1"
    os.environ["CLAY_PROVIDER_ADMISSION_SET_ID"] = admission.admission_set_id
    os.environ["CLAY_PROVIDER_ADMISSION_AUTHORITY_EPOCH"] = admission.authority_epoch
    os.environ["CLAY_FREE_ONLY_ATTESTED"] = "1"
    for provider in admission.providers:
        os.environ[f"CLAY_{provider.upper()}_FREE_ATTESTED"] = "1"


_fail_closed_before_legacy_import()

import run_free_go_swarm_legacy as _legacy  # noqa: E402

# Re-export the legacy controller API only after the pre-side-effect gate.
for _name in dir(_legacy):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_legacy, _name)

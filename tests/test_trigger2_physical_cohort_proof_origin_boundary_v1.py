from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from tools.trigger2_fused_membership_two_phase_adapter_v1 import (
    AdapterError,
    atomic_fused_two_phase_commit,
)


FIXTURE_TEST = "test_trigger2_fused_membership_two_phase_real_fabric_source_v1.py"


def _load_source_fixture_module():
    """Load the retained synthetic FusedFabric integration fixture by exact test-file path."""
    path = Path(__file__).with_name(FIXTURE_TEST)
    spec = importlib.util.spec_from_file_location(
        "trigger2_retained_real_fabric_source_fixture",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("RETAINED_SOURCE_FIXTURE_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_synthetic_raw_physical_proof_cannot_mutate_fusedfabric_state(tmp_path):
    fixture_module = _load_source_fixture_module()
    fx = fixture_module._fixture(tmp_path, "raw-proof-origin")
    fabric = fx["fabric"]
    try:
        assert fx["proof"].get("synthetic_source_fixture_only") is True
        start = fx["start"]
        before_epoch = fabric.snapshot().epoch
        before_admissions = fabric.con.execute(
            "SELECT COUNT(*) AS n FROM fused_cohort_admissions"
        ).fetchone()["n"]
        before_results = fabric.con.execute(
            "SELECT COUNT(*) AS n FROM admitted_results"
        ).fetchone()["n"]

        with pytest.raises(AdapterError, match="^RAW_PHYSICAL_COHORT_PROOF_NOT_ADMITTED$"):
            atomic_fused_two_phase_commit(
                fabric,
                envelopes=fx["extended_envelopes"],
                lease=fx["lease"],
                token=fx["token"],
                proof=fx["proof"],
                expected_generation=start.generation,
                expected_epoch=start.epoch,
                expected_digest=start.state_digest,
                expected_membership_digest=fx["membership_start"]["digest"],
                expected_cohort_id=fx["cohort_id"],
            )

        assert fabric.snapshot().epoch == before_epoch
        assert (
            fabric.con.execute("SELECT COUNT(*) AS n FROM fused_cohort_admissions").fetchone()["n"]
            == before_admissions
        )
        assert (
            fabric.con.execute("SELECT COUNT(*) AS n FROM admitted_results").fetchone()["n"]
            == before_results
        )
    finally:
        fabric.close()

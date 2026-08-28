from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from tools.xeno_self_organizing_fabric_acceptance_v1 import FabricError


FIXTURE_TEST = "test_trigger2_fused_membership_two_phase_real_fabric_source_v1.py"
EXPECTED_ORIGIN_ERROR = "PHYSICAL_COHORT_PROOF_ORIGIN_UNTRUSTED"


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


@pytest.mark.xfail(
    strict=True,
    reason=(
        "V66 source gap: the physical FusedFabric commit boundary currently accepts a raw "
        "caller-supplied proof dictionary. The retained source-composition fixture can set "
        "all physical predicates true with deterministic fake PIDs and still mutate the "
        "real FusedFabric state. Physical admission must reject that proof origin before "
        "mutation while preserving a separately explicit nonphysical composition path."
    ),
)
def test_synthetic_raw_physical_proof_cannot_mutate_fusedfabric_state(tmp_path):
    fixture_module = _load_source_fixture_module()
    fx = fixture_module._fixture(tmp_path, "raw-proof-origin")
    fabric = fx["fabric"]
    try:
        assert fx["proof"].get("synthetic_source_fixture_only") is True
        before_epoch = fabric.snapshot().epoch
        before_admissions = fabric.con.execute(
            "SELECT COUNT(*) AS n FROM fused_cohort_admissions"
        ).fetchone()["n"]
        before_results = fabric.con.execute(
            "SELECT COUNT(*) AS n FROM admitted_results"
        ).fetchone()["n"]

        with pytest.raises(FabricError, match=f"^{EXPECTED_ORIGIN_ERROR}$"):
            fixture_module._commit(fx, fx["extended_envelopes"])

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

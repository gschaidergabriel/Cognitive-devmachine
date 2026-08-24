import hashlib
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from entry_canonicalization_v1 import canonicalize
from grid10_scheduler_v1 import grid_plan_material
from inference_receipt_v1 import InferenceReceiptError, make_inference_receipt
from model_execution_admission_store_v1 import admit_and_verify_model_execution
from model_execution_receipt_v1 import ModelExecutionReceiptError, model_execution_observation_record
from test_inference_receipt_v1 import digest, fixture
from test_model_execution_admission_store_v1 import open_db
from test_model_execution_receipt_v1 import (
    grid_plan as model_grid_plan,
    observation as model_observation,
    verified_load as model_verified_load,
)


def rebound_plan(plan, **changes):
    """Change semantic content while preserving a valid scheduler-owned plan digest."""
    updated = replace(plan, **changes)
    material = grid_plan_material(updated)
    plan_sha256 = hashlib.sha256(canonicalize(material)).hexdigest()
    return replace(updated, plan_sha256=plan_sha256)


class InferenceV4RejectionBoundaryTests(unittest.TestCase):
    """Direct regressions for canonical boundaries exposed by the PR810 verifier repair.

    These tests add no runtime/model/J-Space credit. They only make already-present
    fail-closed source semantics explicit at the InferenceReceipt/v4 boundary.
    """

    def test_route_decision_cross_binding_fails_closed_with_valid_plan_digest(self):
        _packet, decision, kwargs = fixture()
        kwargs["grid_plan"] = rebound_plan(
            kwargs["grid_plan"],
            route_decision_sha256=digest("different-route-decision"),
        )
        with self.assertRaisesRegex(InferenceReceiptError, "GRID10_INFERENCE_ROUTE_DECISION_MISMATCH"):
            make_inference_receipt(decision, **kwargs)

    def test_event_cross_binding_fails_closed_with_valid_plan_digest(self):
        _packet, decision, kwargs = fixture()
        other_event = digest("different-entry-event")
        kwargs["grid_plan"] = rebound_plan(
            kwargs["grid_plan"],
            entry_event_sha256=other_event,
            route_event_sha256=other_event,
        )
        with self.assertRaisesRegex(InferenceReceiptError, "GRID10_INFERENCE_ENTRY_EVENT_MISMATCH"):
            make_inference_receipt(decision, **kwargs)

    def test_entry_admission_cross_binding_fails_closed_with_valid_plan_digest(self):
        _packet, decision, kwargs = fixture()
        kwargs["grid_plan"] = rebound_plan(
            kwargs["grid_plan"],
            entry_admission_sha256=digest("different-entry-admission"),
        )
        with self.assertRaisesRegex(InferenceReceiptError, "GRID10_INFERENCE_ENTRY_ADMISSION_MISMATCH"):
            make_inference_receipt(decision, **kwargs)

    def test_grid_generation_cross_binding_fails_closed_with_valid_plan_digest(self):
        _packet, decision, kwargs = fixture()
        kwargs["grid_plan"] = rebound_plan(kwargs["grid_plan"], entity_generation=8)
        with self.assertRaisesRegex(InferenceReceiptError, "GRID10_INFERENCE_GENERATION_MISMATCH"):
            make_inference_receipt(decision, **kwargs)

    def test_route_serializer_downgrade_fails_closed(self):
        _packet, decision, kwargs = fixture()
        forged = replace(decision, hash_serialization_schema="LEGACY_JSON/v1")
        with self.assertRaisesRegex(InferenceReceiptError, "ROUTE_CANONICALIZATION_SCHEMA_UNSUPPORTED"):
            make_inference_receipt(forged, **kwargs)

    def test_verified_load_engine_identity_cross_binding_fails_closed(self):
        _packet, decision, kwargs = fixture()
        load = kwargs["verified_engine_load"]
        kwargs["verified_engine_load"] = replace(load, engine_identity="hcu_local_other")
        with self.assertRaisesRegex(InferenceReceiptError, "VERIFIED_ENGINE_LOAD_IDENTITY_MISMATCH"):
            make_inference_receipt(decision, **kwargs)

    def test_post_admission_loader_artifact_mutations_fail_closed(self):
        _packet, decision, kwargs = fixture()
        original = kwargs["verified_engine_load"]
        for field in ("checkpoint", "tokenizer", "runtime", "build"):
            with self.subTest(field=field):
                artifact = getattr(original, field)
                mutated = replace(artifact, sha256=digest(f"post-admission-{field}-mutation"))
                local_kwargs = dict(kwargs)
                local_kwargs["verified_engine_load"] = replace(original, **{field: mutated})
                with self.assertRaisesRegex(InferenceReceiptError, "VERIFIED_ENGINE_LOAD_DIGEST_MISMATCH"):
                    make_inference_receipt(decision, **local_kwargs)

    def test_loader_lease_or_consumption_identity_mutation_fails_closed(self):
        _packet, decision, kwargs = fixture()
        original = kwargs["verified_engine_load"]
        for field, seed in (
            ("engine_load_lease_sha256", "different-loader-lease"),
            ("consumption_receipt_sha256", "different-loader-consumption"),
        ):
            with self.subTest(field=field):
                local_kwargs = dict(kwargs)
                local_kwargs["verified_engine_load"] = replace(original, **{field: digest(seed)})
                with self.assertRaisesRegex(InferenceReceiptError, "VERIFIED_ENGINE_LOAD_DIGEST_MISMATCH"):
                    make_inference_receipt(decision, **local_kwargs)

    def test_missing_model_output_identity_fails_before_admission(self):
        plan = model_grid_plan()
        load = model_verified_load(plan)
        original = model_observation(plan, load)
        for field in ("output_ref", "output_sha256"):
            with self.subTest(field=field):
                missing = replace(original, **{field: ""})
                with self.assertRaisesRegex(
                    ModelExecutionReceiptError,
                    rf"observation\.{field}:NONEMPTY_STRING_REQUIRED",
                ):
                    model_execution_observation_record(missing)

    def test_exact_replay_survives_sqlite_connection_restart(self):
        with tempfile.TemporaryDirectory() as tempdir:
            db_path = Path(tempdir) / "miniunified.db"
            plan = model_grid_plan()
            load = model_verified_load(plan)
            obs = model_observation(plan, load)

            first_db = open_db(db_path)
            first = admit_and_verify_model_execution(
                first_db,
                plan,
                load,
                obs,
                current_generation=plan.entity_generation,
            )
            first_db.close()

            restarted_db = open_db(db_path)
            second = admit_and_verify_model_execution(
                restarted_db,
                plan,
                load,
                obs,
                current_generation=plan.entity_generation,
            )
            self.assertEqual(first.receipt_sha256, second.receipt_sha256)
            self.assertEqual(
                restarted_db.execute("SELECT COUNT(*) FROM hcu_model_execution_observations").fetchone()[0],
                1,
            )
            self.assertEqual(
                restarted_db.execute("SELECT COUNT(*) FROM hcu_model_execution_invocations").fetchone()[0],
                1,
            )
            restarted_db.close()


if __name__ == "__main__":
    unittest.main()

import hashlib
import unittest
from dataclasses import asdict, replace

from entry_canonicalization_v1 import canonicalize
from jspace_model_input_control_closure_revalidation_v1 import (
    JSpaceModelInputControlClosureRevalidationError,
    revalidate_closure_against_canonical_sources,
)
from jspace_model_input_control_closure_v1 import (
    close_model_input_control_into_jspace,
    validate_closure,
)
from test_execution_store_inference_jspace_chain_v1 import open_db
from test_jspace_model_input_control_closure_v1 import JSpaceModelInputControlClosureTests


class JSpaceModelInputControlClosureRevalidationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = JSpaceModelInputControlClosureTests(
            methodName="test_exact_control_delivery_closes_through_inference_and_jspace"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)

    def build_valid_closure(self):
        (
            plan,
            consumed,
            control_binding,
            control_admission,
            inference,
            jspace_binding,
            _trace_packet,
        ) = self.fixture.build_chain()
        closure = close_model_input_control_into_jspace(
            control_binding,
            control_admission,
            consumed,
            plan,
            inference,
            jspace_binding,
        )
        return plan, consumed, control_binding, inference, jspace_binding, closure

    def revalidation_rejects(self, forged, plan, consumed, control_binding, inference, jspace_binding):
        db = open_db(self.fixture.db_path, plan.entity_generation)
        try:
            with self.assertRaisesRegex(
                JSpaceModelInputControlClosureRevalidationError,
                "JSPACE_MODEL_INPUT_CONTROL_CLOSURE:SOURCE_MISMATCH",
            ):
                revalidate_closure_against_canonical_sources(
                    db,
                    forged,
                    control_binding,
                    consumed,
                    plan,
                    inference,
                    jspace_binding,
                    current_generation=plan.entity_generation,
                )
        finally:
            db.close()

    def test_exact_persisted_closure_revalidates_against_canonical_store(self):
        plan, consumed, control_binding, inference, jspace_binding, closure = self.build_valid_closure()
        db = open_db(self.fixture.db_path, plan.entity_generation)
        try:
            revalidated = revalidate_closure_against_canonical_sources(
                db,
                closure,
                control_binding,
                consumed,
                plan,
                inference,
                jspace_binding,
                current_generation=plan.entity_generation,
            )
        finally:
            db.close()
        self.assertEqual(asdict(revalidated), asdict(closure))

    def test_self_consistent_forged_packet_identity_is_rejected_by_source_revalidation(self):
        plan, consumed, control_binding, inference, jspace_binding, closure = self.build_valid_closure()

        forged_packet_sha256 = hashlib.sha256(b"forged-posthoc-control-packet").hexdigest()
        forged_material = asdict(closure)
        forged_material["vector_control_packet_sha256"] = forged_packet_sha256
        forged_material.pop("closure_sha256")
        forged = replace(
            closure,
            vector_control_packet_sha256=forged_packet_sha256,
            closure_sha256=hashlib.sha256(canonicalize(forged_material)).hexdigest(),
        )

        # Digest-only validation has no source objects and therefore accepts the recomputed record.
        validate_closure(forged)
        self.revalidation_rejects(
            forged, plan, consumed, control_binding, inference, jspace_binding
        )

    def test_self_consistent_forged_control_admission_identity_is_rejected_by_source_revalidation(self):
        plan, consumed, control_binding, inference, jspace_binding, closure = self.build_valid_closure()

        # This is the subtle laundering case for downstream training gates: all public
        # Trace/Inference/J-Space cross-bound fields remain unchanged, while the claimed
        # canonical ModelInputControlAdmission identity is replaced and the closure digest
        # is freshly recomputed. A digest-only closure validator cannot detect this.
        forged_admission_sha256 = hashlib.sha256(b"nonexistent-control-admission").hexdigest()
        forged_material = asdict(closure)
        forged_material["control_admission_sha256"] = forged_admission_sha256
        forged_material.pop("closure_sha256")
        forged = replace(
            closure,
            control_admission_sha256=forged_admission_sha256,
            closure_sha256=hashlib.sha256(canonicalize(forged_material)).hexdigest(),
        )

        validate_closure(forged)
        self.assertEqual(forged.vector_control_packet_sha256, closure.vector_control_packet_sha256)
        self.assertEqual(forged.inference_receipt_sha256, closure.inference_receipt_sha256)
        self.assertEqual(forged.jspace_binding_sha256, closure.jspace_binding_sha256)
        self.revalidation_rejects(
            forged, plan, consumed, control_binding, inference, jspace_binding
        )


if __name__ == "__main__":
    unittest.main()

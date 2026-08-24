import hashlib
import unittest
from dataclasses import asdict, replace

from entry_canonicalization_v1 import canonicalize
from jspace_model_input_control_closure_v1 import close_model_input_control_into_jspace, validate_closure
from jspace_training_control_source_revalidation_v1 import (
    JSpaceTrainingControlSourceRevalidationError,
    TrainingControlSourceContext,
    require_source_revalidated_model_input_control_closure,
)
from test_execution_store_inference_jspace_chain_v1 import open_db
from test_jspace_model_input_control_closure_v1 import JSpaceModelInputControlClosureTests


class JSpaceTrainingControlSourceRevalidationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = JSpaceModelInputControlClosureTests(
            methodName="test_exact_control_delivery_closes_through_inference_and_jspace"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)

    def build(self):
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
        db = open_db(self.fixture.db_path, plan.entity_generation)
        context = TrainingControlSourceContext(
            db=db,
            control_binding=control_binding,
            consumed_input_bytes=consumed,
            grid_plan=plan,
            inference_receipt=inference,
            current_generation=plan.entity_generation,
        )
        return db, context, closure, jspace_binding

    def test_exact_closure_is_revalidated_before_training_use(self):
        db, context, closure, jspace_binding = self.build()
        self.addCleanup(db.close)
        observed = require_source_revalidated_model_input_control_closure(
            jspace_binding,
            closure,
            {jspace_binding.binding_sha256: context},
        )
        self.assertEqual(asdict(observed), asdict(closure))

    def test_supplied_closure_without_exact_source_context_fails_closed(self):
        db, _context, closure, jspace_binding = self.build()
        self.addCleanup(db.close)
        with self.assertRaisesRegex(
            JSpaceTrainingControlSourceRevalidationError,
            "MODEL_INPUT_CONTROL_SOURCE_CONTEXT_REQUIRED_FOR_JSPACE_BINDING",
        ):
            require_source_revalidated_model_input_control_closure(
                jspace_binding,
                closure,
                {},
            )

    def test_digest_valid_forged_control_admission_is_rejected(self):
        db, context, closure, jspace_binding = self.build()
        self.addCleanup(db.close)
        forged_admission_sha256 = hashlib.sha256(b"forged-training-control-admission").hexdigest()
        material = asdict(closure)
        material["control_admission_sha256"] = forged_admission_sha256
        material.pop("closure_sha256")
        forged = replace(
            closure,
            control_admission_sha256=forged_admission_sha256,
            closure_sha256=hashlib.sha256(canonicalize(material)).hexdigest(),
        )
        validate_closure(forged)
        with self.assertRaisesRegex(
            JSpaceTrainingControlSourceRevalidationError,
            "MODEL_INPUT_CONTROL_CLOSURE_SOURCE_REVALIDATION_FAILED:.*SOURCE_MISMATCH",
        ):
            require_source_revalidated_model_input_control_closure(
                jspace_binding,
                forged,
                {jspace_binding.binding_sha256: context},
            )

    def test_context_generation_must_match_jspace_binding(self):
        db, context, closure, jspace_binding = self.build()
        self.addCleanup(db.close)
        stale = replace(context, current_generation=context.current_generation + 1)
        with self.assertRaisesRegex(
            JSpaceTrainingControlSourceRevalidationError,
            "MODEL_INPUT_CONTROL_SOURCE_GENERATION_MISMATCH",
        ):
            require_source_revalidated_model_input_control_closure(
                jspace_binding,
                closure,
                {jspace_binding.binding_sha256: stale},
            )

    def test_absent_closure_remains_policy_neutral(self):
        db, _context, _closure, jspace_binding = self.build()
        self.addCleanup(db.close)
        self.assertIsNone(
            require_source_revalidated_model_input_control_closure(
                jspace_binding,
                None,
                None,
            )
        )


if __name__ == "__main__":
    unittest.main()

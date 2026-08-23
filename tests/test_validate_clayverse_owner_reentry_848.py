import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "validate_clayverse_authority_consistency.py"
spec = importlib.util.spec_from_file_location("authority_validator_848", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def current_bootstrap():
    return {"expected_entity_version": mod.CURRENT_REENTRY_ENTITY_VERSION}


def current_steering():
    return {
        "schema_version": "8.48",
        "status": "CURRENT_OWNER_REENTRY_STEERING",
        "program": mod.EXPECTED_PROGRAM,
        "stage": mod.EXPECTED_STAGE,
        "product_endpoint": "ClayVerse",
        "release_form": mod.EXPECTED_RELEASE,
        "owner_directive": mod.OWNER_DIRECTIVE,
        "authority_adjudication": {
            "mini_entity_4_5": "SUPERSEDED_FOR_PROGRAM_PRODUCT_TRIGGER_AND_WORK_SELECTION_BY_NEWER_OWNER_REENTRY",
            "durable_authority": "UnifiedDB",
            "external_effect_authority": "EffectGate+EffectJournal",
            "second_identity_or_state_or_effect_authority": "FORBIDDEN",
        },
        "execution": {
            "free_only": True,
            "authorized_isolated_sandbox_only": True,
            "vps_testing": False,
            "self_hosted_vps_test_runners": False,
            "production_host_testing": False,
            "together_allowed": False,
            "runtime_credit": 0,
        },
        "steering": [
            "RUN_THE_EXISTING_CLAYVERSE_AUTHORITY_CONSISTENCY_GUARD_BEFORE_PROMOTING_ANY_FUTURE_PRODUCT_ROUTING_CHANGE",
            "FAIL_CLOSED_IF_BOOTSTRAP_PROGRAM_ROOT_WORKER_SWARM_CONTROL_OR_OWNER_DIRECTIVE_SELECTS_MINI_ENTITY_OR_BLOGPOST_AS_CURRENT_PRODUCT",
        ],
    }


class CurrentOwnerReentrySteeringTests(unittest.TestCase):
    def validate(self, steering):
        errors = []
        mod.validate_current_reentry_steering(errors, current_bootstrap(), steering)
        return errors

    def test_current_848_steering_contract_is_admitted(self):
        self.assertEqual(self.validate(current_steering()), [])

    def test_missing_current_848_steering_fails_closed(self):
        self.assertIn("STEERING848_MISSING", self.validate(None))

    def test_mini_entity_work_selection_reactivation_fails_closed(self):
        poisoned = current_steering()
        poisoned["program"] = "MINI_ENTITY_PIPELINE_ALL_IN_ONE"
        poisoned["authority_adjudication"]["mini_entity_4_5"] = "CURRENT"
        errors = self.validate(poisoned)
        self.assertIn("STEERING848_PROGRAM_STAGE_MISMATCH", errors)
        self.assertIn("STEERING848_MINI_ENTITY_NOT_SUPERSEDED", errors)

    def test_execution_boundary_weakening_fails_closed(self):
        poisoned = current_steering()
        poisoned["execution"]["vps_testing"] = True
        poisoned["execution"]["together_allowed"] = True
        poisoned["execution"]["runtime_credit"] = 1
        errors = self.validate(poisoned)
        self.assertIn("STEERING848_SAFETY_WEAKENED", errors)
        self.assertIn("STEERING848_RUNTIME_CREDIT_NONZERO", errors)

    def test_historical_entity_version_does_not_require_future_steering(self):
        errors = []
        mod.validate_current_reentry_steering(
            errors,
            {"expected_entity_version": "RAE-8.7"},
            None,
        )
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()

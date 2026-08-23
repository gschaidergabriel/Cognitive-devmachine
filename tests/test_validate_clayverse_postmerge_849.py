import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "validate_clayverse_authority_consistency.py"
spec = importlib.util.spec_from_file_location("authority_validator_849", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def current_bootstrap():
    return {"expected_entity_version": mod.CURRENT_REENTRY_ENTITY_VERSION}


def postmerge_steering():
    return {
        "schema_version": "8.49",
        "status": "CURRENT_POSTMERGE_CLAYVERSE_STEERING",
        "program": mod.EXPECTED_PROGRAM,
        "stage": mod.EXPECTED_STAGE,
        "product_endpoint": "ClayVerse",
        "owner_directive": mod.OWNER_DIRECTIVE,
        "authority_reentry_pr": mod.AUTHORITY_REENTRY_PR,
        "authority_merge_commit": mod.AUTHORITY_REENTRY_MERGE,
        "postmerge_authority_state": {
            "bootstrap": mod.EXPECTED_PROGRAM,
            "program_state": "clayverse-single-container",
            "control_4_4": "ACTIVE",
            "control_4_5": "SUPERSEDED_HISTORICAL_DONOR_ONLY",
            "durable_authority": "UnifiedDB",
            "external_effect_authority": "EffectGate+EffectJournal",
        },
        "execution_admission": {
            "classification": "RUNNER_OR_EXECUTION_ADMISSION_FAILURE_BEFORE_VISIBLE_STEP_EXECUTION",
            "test_failure_claimed": False,
            "runtime_credit": 0,
            "oci_credit": 0,
        },
        "unusual_experiment": {
            "macrocycle_count": 1,
            "already_consumed": "AUTHORITY_ROLLBACK_POISON_REPLAY",
            "additional_unusual_experiment_forbidden_this_go": True,
        },
        "steering": [
            "KEEP_CLAYVERSE_OWNER_AUTHORITY_MERGED_AND_FAIL_CLOSED_AGAINST_STALE_MINI_ENTITY_WORK_SELECTION",
            "DO_NOT_CLASSIFY_GITHUB_JOBS_WITH_STEPS_EMPTY_AS_PRODUCT_TEST_FAILURE",
            "NEXT_RUNTIME_GATE_REQUIRES_ACTUALLY_STARTED_AUTHORIZED_ISOLATED_EXACT_CURRENT_EXECUTION",
        ],
        "together_forbidden": True,
        "vps_self_hosted_production_testing_forbidden": True,
        "final_paid_model_training": "OWNER_AUTHORIZATION_REQUIRED",
    }


class PostmergeSteering849Tests(unittest.TestCase):
    def validate(self, steering):
        errors = []
        mod.validate_postmerge_steering(errors, current_bootstrap(), steering)
        return errors

    def test_current_postmerge_contract_is_admitted(self):
        self.assertEqual(self.validate(postmerge_steering()), [])

    def test_reentry_ancestry_drift_fails_closed(self):
        poisoned = postmerge_steering()
        poisoned["authority_merge_commit"] = "0" * 40
        self.assertIn("STEERING849_REENTRY_ANCESTRY_MISMATCH", self.validate(poisoned))

    def test_mini_entity_control_reactivation_fails_closed(self):
        poisoned = postmerge_steering()
        poisoned["postmerge_authority_state"]["control_4_5"] = "ACTIVE"
        self.assertIn("STEERING849_CONTROL45_NOT_SUPERSEDED", self.validate(poisoned))

    def test_prestep_runner_failure_cannot_be_laundered_into_test_failure(self):
        poisoned = postmerge_steering()
        poisoned["execution_admission"]["test_failure_claimed"] = True
        self.assertIn("STEERING849_EXECUTION_ADMISSION_MISCLASSIFIED", self.validate(poisoned))

    def test_macrocycle_experiment_lease_cannot_be_reset(self):
        poisoned = postmerge_steering()
        poisoned["unusual_experiment"]["macrocycle_count"] = 0
        poisoned["unusual_experiment"]["additional_unusual_experiment_forbidden_this_go"] = False
        self.assertIn("STEERING849_EXPERIMENT_LEASE_MISMATCH", self.validate(poisoned))


if __name__ == "__main__":
    unittest.main()

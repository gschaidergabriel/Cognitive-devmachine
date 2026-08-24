import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.assess_hcu_jspace_local_activation_probe_v2 import (
    AssessmentRejected,
    assess,
    verify_predeclared_policy,
)


def h(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def g(label: str) -> str:
    return hashlib.sha1(label.encode()).hexdigest()


class AssessmentTests(unittest.TestCase):
    def fixture(self):
        target_token = 101
        off_token = 202

        def row(name, target_logit, off_logit):
            return {
                "condition": name,
                "target_token_id": target_token,
                "off_target_token_id": off_token,
                "target_logit": target_logit,
                "off_target_logit": off_logit,
            }

        receipt = {
            "schema": "ENTITYOS_HCU_JSPACE_LOCAL_ACTIVATION_PROBE/v2",
            "probe_mode": "intervention",
            "source_git_head": g("probe-head"),
            "probe_source_sha256": h("probe-source"),
            "authority": {"epoch": "8.68"},
            "post_load_identity": {"loader_consumption_attestation": False},
            "probe": {
                "layer": 7,
                "target_position": 4,
                "off_target_position": 3,
                "clean_token_ids_sha256": h("clean-ids"),
                "corrupted_token_ids_sha256": h("corrupt-ids"),
                "conditions": [
                    row("BASELINE_CLEAN", 1.2, 0.10),
                    row("BASELINE_CORRUPTED", 0.2, 0.10),
                    row("BASELINE_CLEAN_OFF_TARGET_REFERENCE", 1.2, 0.10),
                    row("INTERVENTION_TARGET", 0.9, 0.12),
                    row("SHAM_CONTROL", 0.25, 0.10),
                    row("OFF_TARGET_CONTROL", 0.24, 0.10),
                ],
                "derived_metrics": {
                    "target_patch_effect_on_target_logit": 0.7,
                    "sham_effect_on_target_logit": 0.05,
                    "off_target_patch_effect_on_target_logit": 0.04,
                    "target_patch_effect_on_off_target_logit": 0.02,
                },
            },
        }
        policy = {
            "schema": "HCU_JSPACE_LOCAL_INTERVENTION_ACCEPTANCE_POLICY/v1",
            "authority_epoch": "8.68",
            "probe_schema": "ENTITYOS_HCU_JSPACE_LOCAL_ACTIVATION_PROBE/v2",
            "probe_source_sha256": h("probe-source"),
            "intervention_family": "ACTIVATION_REPLACEMENT_CLEAN_TO_CORRUPTED/v1",
            "sham_policy": "SAME_SITE_CORRUPTED_REFERENCE_NOOP/v1",
            "off_target_policy": "DISTINCT_POSITION_CLEAN_REFERENCE_PATCH/v1",
            "scope": {
                "layer": 7,
                "target_position": 4,
                "off_target_position": 3,
                "clean_token_ids_sha256": h("clean-ids"),
                "corrupted_token_ids_sha256": h("corrupt-ids"),
                "target_token_id": target_token,
                "off_target_token_id": off_token,
            },
            "thresholds": {
                "min_corruption_effect_on_target_logit": 0.5,
                "min_target_patch_effect_on_target_logit": 0.5,
                "min_target_advantage_vs_sham": 0.5,
                "min_target_advantage_vs_off_target_patch": 0.5,
                "max_abs_sham_effect_on_target_logit": 0.1,
                "max_abs_off_target_patch_effect_on_target_logit": 0.1,
                "max_abs_target_patch_effect_on_off_target_logit": 0.1,
            },
        }
        identity = {
            "policy_path": "policy.json",
            "policy_commit": g("policy"),
            "policy_sha256": h("policy"),
            "policy_git_blob_sha1": g("policy-blob"),
            "predeclared_ancestor_of_probe_source_head": True,
        }
        return receipt, policy, identity

    def test_pass_is_effect_pattern_only_and_all_credits_zero(self):
        receipt, policy, identity = self.fixture()
        out = assess(receipt, policy, policy_identity=identity)
        self.assertTrue(out["effect_pattern_pass"])
        self.assertFalse(out["jspace_causal_control_candidate"])
        self.assertFalse(out["runtime_promotion_allowed"])
        self.assertFalse(out["loader_consumption_verified"])
        self.assertFalse(out["canonical_inference_binding_verified"])
        self.assertTrue(all(v == 0 for v in out["credits"].values()))

    def test_sham_threshold_failure_rejects_effect_pattern(self):
        receipt, policy, identity = self.fixture()
        for row in receipt["probe"]["conditions"]:
            if row["condition"] == "SHAM_CONTROL":
                row["target_logit"] = 0.75
        receipt["probe"]["derived_metrics"]["sham_effect_on_target_logit"] = 0.55
        out = assess(receipt, policy, policy_identity=identity)
        self.assertFalse(out["effect_pattern_pass"])
        self.assertFalse(out["gates"]["sham_specificity"])
        self.assertFalse(out["gates"]["target_advantage_vs_sham"])

    def test_posthoc_scope_change_fails_closed(self):
        receipt, policy, identity = self.fixture()
        policy["scope"]["layer"] = 8
        with self.assertRaisesRegex(AssessmentRejected, "PREDECLARED_SCOPE_MISMATCH"):
            assess(receipt, policy, policy_identity=identity)

    def test_metric_token_change_fails_closed(self):
        receipt, policy, identity = self.fixture()
        receipt["probe"]["conditions"][2]["target_token_id"] = 999
        with self.assertRaisesRegex(AssessmentRejected, "PREDECLARED_TARGET_TOKEN_MISMATCH"):
            assess(receipt, policy, policy_identity=identity)

    def test_derived_metric_laundering_fails_closed(self):
        receipt, policy, identity = self.fixture()
        receipt["probe"]["derived_metrics"]["target_patch_effect_on_target_logit"] = 9.0
        with self.assertRaisesRegex(AssessmentRejected, "RAW_PROBE_DERIVED_METRIC_MISMATCH"):
            assess(receipt, policy, policy_identity=identity)

    def test_policy_authority_mismatch_fails_closed(self):
        receipt, policy, identity = self.fixture()
        policy["authority_epoch"] = "8.67"
        with self.assertRaisesRegex(AssessmentRejected, "POLICY_AUTHORITY_EPOCH_MISMATCH"):
            assess(receipt, policy, policy_identity=identity)

    def test_missing_git_predeclaration_proof_fails_closed(self):
        receipt, policy, identity = self.fixture()
        identity["predeclared_ancestor_of_probe_source_head"] = False
        with self.assertRaisesRegex(AssessmentRejected, "PREDECLARED_POLICY_GIT_PROOF_REQUIRED"):
            assess(receipt, policy, policy_identity=identity)

    def test_git_policy_bytes_and_ancestor_are_proven(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
            policy_path = repo / "policy.json"
            policy_path.write_text('{"schema":"x"}\n', encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "policy.json"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "policy"], check=True)
            policy_commit = subprocess.check_output(
                ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
            ).strip()
            (repo / "probe.txt").write_text("probe\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "probe.txt"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "probe"], check=True)
            probe_head = subprocess.check_output(
                ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
            ).strip()
            identity = verify_predeclared_policy(
                policy_path, policy_commit=policy_commit, probe_source_git_head=probe_head
            )
            self.assertTrue(identity["predeclared_ancestor_of_probe_source_head"])
            policy_path.write_text('{"schema":"changed"}\n', encoding="utf-8")
            with self.assertRaisesRegex(AssessmentRejected, "POLICY_BYTES_DO_NOT_MATCH"):
                verify_predeclared_policy(
                    policy_path, policy_commit=policy_commit, probe_source_git_head=probe_head
                )


if __name__ == "__main__":
    unittest.main()

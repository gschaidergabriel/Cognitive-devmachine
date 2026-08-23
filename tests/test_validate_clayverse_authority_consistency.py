import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "validate_clayverse_authority_consistency.py"
spec = importlib.util.spec_from_file_location("authority_validator", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class AuthoritySuccessorClosureTests(unittest.TestCase):
    def make_tree(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        authority = f"{mod.AUTHORITY_DIR}/SUPERVISOR_STEERING_8_63.json"
        files = {
            "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json": {"entity_id": "entity"},
            "research_entity/continuity/BOOTSTRAP_MINIMAL.json": {
                "schema_version": "8.63",
                "entity_id": "entity",
                "identity": {"persistent_research_entity": "Clay", "temporary_worker": "ORGAN_NOT_ENTITY"},
                "active_program": mod.CURRENT_PROGRAM,
                "active_stage": mod.CURRENT_STAGE,
                "product_endpoint": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "authority_correction": authority,
                "execution_surface": "AUTHORIZED_ISOLATED_FREE_SANDBOX_ONLY_IN_CURRENT_AUTONOMOUS_SUPERVISOR_MODE; VERCEL_HOBBY_INCLUDED_TIER_ADMITTED_ONLY_FOR_FIXED_HASH_BOUND_SHORT_CAPSULES",
                "free_only": True,
                "paid_fallback": "FORBIDDEN",
                "together_api": "FORBIDDEN_IN_CURRENT_FREE_ONLY_SUPERVISOR_MODE",
                "together_training_authority_provenance": mod.TRAINING_PROVENANCE,
                "together_one_shot_training_consumed": False,
                "current_supervisor_together_training": mod.CURRENT_SUPERVISOR_TRAINING,
                "effect_authority": "EffectGate+EffectJournal",
                "go_unusual_experiment_atomic_lease_protocol": "research_entity/continuity/GO_EXPERIMENT_ATOMIC_LEASE_PROTOCOL.md",
                "go_unusual_experiment_claim_rule": "CREATE_ONLY_CANONICAL_CLAIM_BEFORE_INTERVENTION_OR_COORDINATION_BLOCKED",
            },
            "research_entity/rooms/PROGRAM_STATE.json": {
                "schema_version": "8.63",
                "program_id": "entityos-hcu",
                "status": "ACTIVE",
                "stage": mod.CURRENT_STAGE,
                "current_stage": mod.CURRENT_STAGE,
                "product": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "authority_correction": authority,
                "authority": {
                    "external_effects": "EffectGate+EffectJournal",
                    "second_persistent_identity": "FORBIDDEN",
                    "second_truth_effect_or_recovery_authority": "FORBIDDEN",
                },
                "execution_policy": {
                    "free_only": True,
                    "isolated_sandbox_only": True,
                    "vercel_hobby_bounded_included_tier_sandbox_admitted": True,
                    "remaining_monthly_sandbox_quota_directly_observed": False,
                    "vps_testing_forbidden": True,
                    "self_hosted_vps_test_runners_forbidden": True,
                    "production_host_testing_forbidden": True,
                    "together_general_inference_and_fallback_forbidden": True,
                    "owner_paid_one_shot_job_consumed": False,
                    "current_supervisor_together_training_forbidden": True,
                    "paid_or_unknown_provider_admission_boundary": mod.PAID_BOUNDARY,
                    "other_paid_fallback": False,
                    "go_unusual_experiment_atomic_lease_protocol": "research_entity/continuity/GO_EXPERIMENT_ATOMIC_LEASE_PROTOCOL.md",
                    "unusual_experiment_without_reproducible_claim": "COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT",
                },
                "runtime_credit": {
                    "entityos_hcu_whole_runtime_credit": 0,
                    "jspace_model_runtime_credit": 0,
                    "training_credit": 0,
                    "whole_product_pass": False,
                },
            },
            authority: {
                "schema_version": "8.63",
                "program": mod.CURRENT_PROGRAM,
                "product": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "mode": "FREE_ONLY",
                "free_only_policy": {
                    "no_paid_fallback": True,
                    "together_general_inference": "FORBIDDEN",
                    "together_training": "FORBIDDEN",
                    "together_preflight_or_key_lookup": "FORBIDDEN",
                    "paid_subscription_unknown_fail_closed": True,
                    "vercel_hobby_sandbox": "BOUNDED_INCLUDED_TIER_FIXED_HASH_BOUND_SHORT_CAPSULES_ONLY",
                    "fail_closed_on_quota_billing_upgrade_plan_mismatch_or_charge_path": True,
                },
                "coordination_authority": {
                    "required_before_unusual_intervention": True,
                    "atomic_lease_protocol": "research_entity/continuity/GO_EXPERIMENT_ATOMIC_LEASE_PROTOCOL.md",
                    "fail_closed_rule": "IF_NO_SHARED_ID_THEN_ZERO_NEW_UNUSUAL_EXPERIMENTS",
                },
                "promotion_state": {"entityos_whole_runtime_pass": False, "training_credit": 0},
            },
            "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json": {
                "schema_version": "8.63",
                "steering": authority,
                "free_only": {"enabled": True, "no_paid_fallback": True, "together_forbidden": True},
                "coordination": {
                    "required_before_unusual_intervention": True,
                    "no_valid_shared_id_or_atomic_claim": "ZERO_NEW_UNUSUAL_EXPERIMENTS",
                },
            },
            "the artefact/manifest.json": {
                "artifact": mod.CURRENT_PRODUCT,
                "product_endpoint": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "stage": mod.CURRENT_STAGE,
                "authority_correction": authority,
                "effect_authority": "EffectGate+EffectJournal",
                "execution_policy": {
                    "free_only_default": True,
                    "active_supervisor_free_only": True,
                    "isolated_sandbox_only": True,
                    "vercel_hobby_bounded_included_tier_fixed_capsules": True,
                    "remaining_vercel_sandbox_quota_assumed": False,
                    "fail_closed_on_quota_billing_upgrade_plan_mismatch_or_charge_path": True,
                    "generic_caller_supplied_sandbox_command_credit": "FORBIDDEN",
                    "vps_testing_forbidden": True,
                    "self_hosted_vps_test_runners_forbidden": True,
                    "production_host_testing_forbidden": True,
                    "together_general_inference_and_fallback_forbidden": True,
                    "owner_paid_one_shot_08b_jspace_gwt_finetune_consumed": False,
                    "current_supervisor_together_training": mod.CURRENT_SUPERVISOR_TRAINING,
                    "paid_or_unknown_provider_admission_boundary": mod.PAID_BOUNDARY,
                    "other_paid_fallback": False,
                    "go_unusual_experiment_atomic_lease_protocol": "research_entity/continuity/GO_EXPERIMENT_ATOMIC_LEASE_PROTOCOL.md",
                    "unusual_experiment_without_reproducible_claim": "COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT",
                },
                "runtime_credit": {
                    "entityos_hcu_whole_runtime_credit": 0,
                    "hcu_full_runtime_credit": 0,
                    "jspace_model_runtime_credit": 0,
                    "training_credit": 0,
                    "whole_product_pass": False,
                },
            },
            mod.CONTROL41: {
                "schema_version": "4.1",
                "status": "ACTIVE",
                "mode": "FREE_ONLY",
                "cycle_policy": {"paid_fallback": False, "automatic_subscription_upgrade": False, "vps_testing": "FORBIDDEN"},
                "authority_rules": ["model_output_is_candidate_not_truth", "autonomous_cycle_may_not_modify_FRANK_harness"],
            },
            mod.CONTROL42: {
                "schema_version": "4.2-execution-boundary-addendum",
                "base_control_path": mod.CONTROL41,
                "base_control_blob_sha": "pending",
                "execution_routing": {
                    "direct_vps_host_candidate_execution": "FORBIDDEN",
                    "persistent_self_hosted_candidate_execution": "FORBIDDEN",
                    "production_host_testing": "FORBIDDEN",
                },
                "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden": True},
            },
            mod.CONTROL43: {
                "schema_version": "4.3-program-authority-addendum",
                "base_control_blob_sha": "pending",
                "execution_boundary_addendum_path": mod.CONTROL42,
                "execution_boundary_addendum_blob_sha": "pending",
                "preserved_hard_rules": {
                    "free_only": True,
                    "paid_fallback": False,
                    "together_forbidden_under_current_control": True,
                    "runtime_credit_requires_exact_admitted_execution": True,
                },
            },
            mod.CONTROL44: {
                "schema_version": "4.4-clayverse-product-authority-addendum",
                "prior_program_authority_addendum_path": mod.CONTROL43,
                "prior_program_authority_addendum_blob_sha": "pending",
                "effective_control_version": mod.LEGACY_EXPECTED_CONTROL,
                "program_identity_override": {
                    "active_program": "CLAYVERSE_SINGLE_CONTAINER",
                    "target_stage": "CLAYVERSE_ARTIFACT",
                    "product_endpoint": "ClayVerse",
                },
                "preserved_hard_rules": {
                    "free_only": True,
                    "paid_fallback": False,
                    "together_forbidden": True,
                    "vps_testing": False,
                    "runtime_credit_requires_exact_admitted_isolated_execution": True,
                },
            },
        }
        texts = {
            mod.TRAINING_PROVENANCE: "# owner one-shot provenance\n",
            "research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md": "Program: EntityOS + HCU\nSUPERVISOR_STEERING_8_63.json\n",
            "the artefact/ARCHITECTURE.md": "# EntityOS + HCU architecture\n",
            "the artefact/README.md": "# EntityOS + HCU\nSUPERVISOR_STEERING_8_63.json\n",
            mod.ROOT_CLAUDE: "`PROGRAM=ENTITYOS_HCU`\nSUPERVISOR_STEERING_8_63.json\nFREE_ONLY\n",
        }
        for rel, data in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
        for rel, text in texts.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")

        c42p = root / mod.CONTROL42
        c42 = json.loads(c42p.read_text())
        c42["base_control_blob_sha"] = mod.git_blob_sha(root / mod.CONTROL41)
        c42p.write_text(json.dumps(c42, sort_keys=True))

        c43p = root / mod.CONTROL43
        c43 = json.loads(c43p.read_text())
        c43["base_control_blob_sha"] = mod.git_blob_sha(root / mod.CONTROL41)
        c43["execution_boundary_addendum_blob_sha"] = mod.git_blob_sha(c42p)
        c43p.write_text(json.dumps(c43, sort_keys=True))

        c44p = root / mod.CONTROL44
        c44 = json.loads(c44p.read_text())
        c44["prior_program_authority_addendum_blob_sha"] = mod.git_blob_sha(c43p)
        c44p.write_text(json.dumps(c44, sort_keys=True))
        return td, root, authority

    def mutate(self, root, rel, fn):
        p = root / rel
        data = json.loads(p.read_text())
        fn(data)
        p.write_text(json.dumps(data, sort_keys=True))

    def test_current_863_successor_closed_tree_passes(self):
        td, root, _ = self.make_tree()
        self.addCleanup(td.cleanup)
        result = mod.validate(root)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(result["current_authority_version"], "8.63")

    def test_new_successor_without_inbox_reentry_fails_closed(self):
        td, root, _ = self.make_tree()
        self.addCleanup(td.cleanup)
        p = root / mod.AUTHORITY_DIR / "SUPERVISOR_STEERING_8_64.json"
        data = {
            "schema_version": "8.64",
            "program": mod.CURRENT_PROGRAM,
            "product": mod.CURRENT_PRODUCT,
            "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
            "mode": "FREE_ONLY",
            "free_only_policy": {
                "no_paid_fallback": True,
                "together_general_inference": "FORBIDDEN",
                "together_training": "FORBIDDEN",
                "together_preflight_or_key_lookup": "FORBIDDEN",
                "paid_subscription_unknown_fail_closed": True,
                "vercel_hobby_sandbox": "BOUNDED_INCLUDED_TIER_FIXED_HASH_BOUND_SHORT_CAPSULES_ONLY",
                "fail_closed_on_quota_billing_upgrade_plan_mismatch_or_charge_path": True,
            },
            "coordination_authority": {
                "required_before_unusual_intervention": True,
                "atomic_lease_protocol": "research_entity/continuity/GO_EXPERIMENT_ATOMIC_LEASE_PROTOCOL.md",
                "fail_closed_rule": "IF_NO_SHARED_ID_THEN_ZERO_NEW_UNUSUAL_EXPERIMENTS",
            },
            "promotion_state": {"entityos_whole_runtime_pass": False, "training_credit": 0},
        }
        p.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("INBOX_STEERING_NOT_NEWEST", mod.validate(root)["errors"])

    def test_bootstrap_stale_pointer_fails(self):
        td, root, _ = self.make_tree()
        self.addCleanup(td.cleanup)
        self.mutate(root, "research_entity/continuity/BOOTSTRAP_MINIMAL.json", lambda d: d.__setitem__("authority_correction", f"{mod.AUTHORITY_DIR}/SUPERVISOR_STEERING_8_62.json"))
        self.assertIn("BOOTSTRAP_AUTHORITY_POINTER_MISMATCH", mod.validate(root)["errors"])

    def test_program_stale_pointer_fails(self):
        td, root, _ = self.make_tree()
        self.addCleanup(td.cleanup)
        self.mutate(root, "research_entity/rooms/PROGRAM_STATE.json", lambda d: d.__setitem__("authority_correction", f"{mod.AUTHORITY_DIR}/SUPERVISOR_STEERING_8_62.json"))
        self.assertIn("PROGRAM_AUTHORITY_POINTER_MISMATCH", mod.validate(root)["errors"])

    def test_manifest_stale_pointer_fails(self):
        td, root, _ = self.make_tree()
        self.addCleanup(td.cleanup)
        self.mutate(root, "the artefact/manifest.json", lambda d: d.__setitem__("authority_correction", f"{mod.AUTHORITY_DIR}/SUPERVISOR_STEERING_8_62.json"))
        self.assertIn("MANIFEST_AUTHORITY_POINTER_MISMATCH", mod.validate(root)["errors"])

    def test_free_sandbox_admission_cannot_disappear(self):
        td, root, _ = self.make_tree()
        self.addCleanup(td.cleanup)
        self.mutate(root, "research_entity/rooms/PROGRAM_STATE.json", lambda d: d["execution_policy"].__setitem__("vercel_hobby_bounded_included_tier_sandbox_admitted", False))
        self.assertIn("PROGRAM_FREE_SANDBOX_ADMISSION_MISSING", mod.validate(root)["errors"])

    def test_together_cannot_be_reenabled(self):
        td, root, authority = self.make_tree()
        self.addCleanup(td.cleanup)
        self.mutate(root, authority, lambda d: d["free_only_policy"].__setitem__("together_training", "ALLOWED"))
        self.assertIn("SUPERVISOR_TOGETHER_FENCE_WEAKENED", mod.validate(root)["errors"])

    def test_training_credit_cannot_self_promote(self):
        td, root, _ = self.make_tree()
        self.addCleanup(td.cleanup)
        self.mutate(root, "the artefact/manifest.json", lambda d: d["runtime_credit"].__setitem__("training_credit", 1))
        self.assertIn("MANIFEST_TRAINING_CREDIT_NONZERO", mod.validate(root)["errors"])

    def test_legacy_together_fence_remains_hash_bound(self):
        td, root, _ = self.make_tree()
        self.addCleanup(td.cleanup)
        self.mutate(root, mod.CONTROL42, lambda d: d["preserved_hard_rules"].__setitem__("together_forbidden", False))
        errors = mod.validate(root)["errors"]
        self.assertIn("CONTROL42_TOGETHER_FENCE_WEAKENED", errors)
        self.assertIn("CONTROL43_EXEC_BLOB_MISMATCH", errors)

    def test_root_routing_requires_newest_successor(self):
        td, root, _ = self.make_tree()
        self.addCleanup(td.cleanup)
        (root / mod.ROOT_CLAUDE).write_text("`PROGRAM=ENTITYOS_HCU`\nSUPERVISOR_STEERING_8_62.json\nFREE_ONLY\n")
        self.assertIn("ROOT_CLAUDE_CURRENT_AUTHORITY_MISSING", mod.validate(root)["errors"])


if __name__ == "__main__":
    unittest.main()

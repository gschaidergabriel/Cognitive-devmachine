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

SUPERVISOR = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_68.json"
OWNER = "governance/CLAY_DUAL_MACHINE_EXECUTION_AUTHORITY_2026-08-24.md"


class AuthorityConsistencyTests(unittest.TestCase):
    def make_tree(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)

        def write_json(rel, obj):
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")
            return path

        def write_text(rel, text):
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            return path

        write_json("research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json", {"entity_id": "entity"})
        write_json(
            "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
            {
                "entity_id": "entity",
                "identity": {"persistent_research_entity": "Clay", "temporary_worker": "ORGAN_NOT_ENTITY"},
                "active_program": mod.CURRENT_PROGRAM,
                "active_stage": mod.CURRENT_STAGE,
                "product_endpoint": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "active_owner_authority": OWNER,
                "authority_correction": SUPERVISOR,
                "free_only": True,
                "paid_fallback": "FORBIDDEN",
                "together_api": "FORBIDDEN_IN_CURRENT_FREE_ONLY_SUPERVISOR_MODE",
                "effect_authority": "EffectGate+EffectJournal",
                "free_provider_allowlist_current": ["groq", "mistral", "nvidia", "openrouter"],
            },
        )
        execution = {
            "free_only": True,
            "authorized_zero_cost_local_normal_user_execution": True,
            "authorized_clay_direct_dev_vps_sandbox_execution": True,
            "local_root_or_sudo_new_authority_implied": False,
            "unrelated_vps_host_changes_allowed": False,
            "production_host_testing_forbidden": True,
            "external_provider_admission_rule": "TYPED_CONTROL_PLANE_ADMITTED_TRUE_AND_COST_CLASS_FREE_REQUIRED_BEFORE_PROVIDER_SECRET_LOOKUP_OR_PROVIDER_NETWORK_IO",
            "other_paid_fallback": False,
        }
        credits = {
            "entityos_hcu_whole_runtime_credit": 0,
            "hcu_full_runtime_credit": 0,
            "jspace_model_runtime_credit": 0,
            "training_credit": 0,
            "whole_product_pass": False,
        }
        write_json(
            "research_entity/rooms/PROGRAM_STATE.json",
            {
                "program_id": "entityos-hcu",
                "status": "ACTIVE",
                "stage": mod.CURRENT_STAGE,
                "current_stage": mod.CURRENT_STAGE,
                "product": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "active_owner_authority": OWNER,
                "authority_correction": SUPERVISOR,
                "authority": {
                    "external_effects": "EffectGate+EffectJournal",
                    "second_persistent_identity": "FORBIDDEN",
                    "second_truth_effect_or_recovery_authority": "FORBIDDEN",
                },
                "execution_policy": execution,
                "runtime_credit": credits,
            },
        )
        write_json(
            "the artefact/manifest.json",
            {
                "artifact": mod.CURRENT_PRODUCT,
                "product_endpoint": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "stage": mod.CURRENT_STAGE,
                "authority_correction": SUPERVISOR,
                "effect_authority": "EffectGate+EffectJournal",
                "execution_policy": {
                    "free_only_default": True,
                    "active_supervisor_free_only": True,
                    "authorized_zero_cost_local_normal_user_execution": True,
                    "authorized_clay_direct_dev_vps_sandbox_execution": True,
                    "production_host_testing_forbidden": True,
                    "other_paid_fallback": False,
                },
                "runtime_credit": credits,
            },
        )
        write_json(
            "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
            {
                "steering": SUPERVISOR,
                "execution_authority": {"active_owner_authority": OWNER},
            },
        )
        write_json(
            SUPERVISOR,
            {
                "schema_version": "8.68",
                "active_program": mod.CURRENT_PROGRAM,
                "product": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "free_only": {
                    "enabled": True,
                    "no_paid_fallback": True,
                    "together_forbidden": True,
                    "external_llm_provider_execution": "QUARANTINED_UNTIL_EXECUTABLE_TYPED_FREE_ADMISSION_PASS",
                },
                "promotion": {
                    "entityos_whole_runtime_pass": False,
                    "hcu_full_runtime_pass": False,
                    "training_credit": 0,
                },
            },
        )
        write_json(
            mod.PROVIDER_ADMISSION,
            {
                "schema": "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION/v1",
                "authority_epoch": "8.68",
                "mode": "FREE_ONLY",
                "providers": {
                    p: {"admitted": False, "cost_class": "UNKNOWN"}
                    for p in ("groq", "mistral", "nvidia", "openrouter")
                },
                "execution_state": "EXTERNAL_LLM_PROVIDER_TRAFFIC_QUARANTINED_UNTIL_EXECUTABLE_TYPED_FREE_ADMISSION_PASS",
            },
        )
        write_text(
            OWNER,
            "# CLAY DUAL-MACHINE EXECUTION AUTHORITY\nStatus: ACTIVE USER AUTHORITY\nLocal workstation normal user. clay-direct-dev VPS sandbox.\n",
        )
        write_text(
            "the artefact/README.md",
            "# EntityOS + HCU\nSUPERVISOR_STEERING_8_68.json\nFREE_ONLY\nclay-direct-dev VPS sandbox is authorized for zero-cost development.\n",
        )
        write_text(
            mod.ROOT_CLAUDE,
            "# EntityOS + HCU\nAUTONOMOUS_SUPERVISOR=SUPERVISOR_STEERING_8_68\nFREE_ONLY\nclay-direct-dev VPS sandbox is authorized for zero-cost development.\n",
        )

        c41 = write_json(
            mod.CONTROL41,
            {
                "schema_version": "4.1",
                "status": "ACTIVE",
                "mode": "FREE_ONLY",
                "cycle_policy": {"paid_fallback": False, "automatic_subscription_upgrade": False},
            },
        )
        c42_obj = {
            "base_control_path": mod.CONTROL41,
            "base_control_blob_sha": mod.git_blob_sha(c41),
            "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden": True},
        }
        c42 = write_json(mod.CONTROL42, c42_obj)
        c43_obj = {
            "base_control_blob_sha": mod.git_blob_sha(c41),
            "execution_boundary_addendum_path": mod.CONTROL42,
            "execution_boundary_addendum_blob_sha": mod.git_blob_sha(c42),
            "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden_under_current_control": True},
        }
        c43 = write_json(mod.CONTROL43, c43_obj)
        write_json(
            mod.CONTROL44,
            {
                "prior_program_authority_addendum_path": mod.CONTROL43,
                "prior_program_authority_addendum_blob_sha": mod.git_blob_sha(c43),
                "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden": True},
                "program_identity_override": {"product_endpoint": "ClayVerse"},
            },
        )
        return td, root

    def mutate_json(self, root, rel, mutate):
        path = root / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        mutate(data)
        path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    def test_coherent_868_dual_machine_authority_passes(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        result = mod.validate(root)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(result["resolved"]["supervisor_version"], "8.68")

    def test_supervisor_pointer_split_brain_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate_json(root, "research_entity/rooms/PROGRAM_STATE.json", lambda d: d.__setitem__("authority_correction", "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_67.json"))
        self.assertIn("AUTHORITY_POINTER_SPLIT_BRAIN", mod.validate(root)["errors"])

    def test_owner_pointer_split_brain_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate_json(root, "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json", lambda d: d["execution_authority"].__setitem__("active_owner_authority", "governance/OTHER.md"))
        self.assertIn("OWNER_POINTER_SPLIT_BRAIN", mod.validate(root)["errors"])

    def test_clay_direct_dev_authority_cannot_be_silently_removed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate_json(root, "research_entity/rooms/PROGRAM_STATE.json", lambda d: d["execution_policy"].__setitem__("authorized_clay_direct_dev_vps_sandbox_execution", False))
        self.assertIn("PROGRAM_CLAY_DIRECT_DEV_AUTHORITY_MISSING", mod.validate(root)["errors"])

    def test_obsolete_blanket_vps_ban_is_rejected(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        p = root / "the artefact/README.md"
        p.write_text(p.read_text(encoding="utf-8") + "VPS, self-hosted and production-host testing are forbidden\n", encoding="utf-8")
        self.assertIn("README_STALE_BLANKET_VPS_BAN", mod.validate(root)["errors"])

    def test_unknown_provider_cannot_self_admit(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate_json(root, mod.PROVIDER_ADMISSION, lambda d: d["providers"]["groq"].__setitem__("admitted", True))
        self.assertIn("PROVIDER_SELF_ADMISSION_NOT_FREE:groq", mod.validate(root)["errors"])

    def test_provider_allowlist_split_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate_json(root, mod.PROVIDER_ADMISSION, lambda d: d["providers"].pop("openrouter"))
        self.assertIn("PROVIDER_ADMISSION_ALLOWLIST_SPLIT", mod.validate(root)["errors"])

    def test_provider_authority_epoch_mismatch_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate_json(root, mod.PROVIDER_ADMISSION, lambda d: d.__setitem__("authority_epoch", "8.67"))
        self.assertIn("PROVIDER_ADMISSION_AUTHORITY_DRIFT", mod.validate(root)["errors"])

    def test_quarantine_state_mismatch_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate_json(root, mod.PROVIDER_ADMISSION, lambda d: d.__setitem__("execution_state", "RUNNING"))
        self.assertIn("PROVIDER_QUARANTINE_STATE_MISMATCH", mod.validate(root)["errors"])


if __name__ == "__main__":
    unittest.main()

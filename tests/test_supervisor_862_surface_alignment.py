import json
import tempfile
import unittest
from pathlib import Path

AUTHORITY = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_62.json"
STALE_861 = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_61.json"


def _write_json(root: Path, rel: str, obj: dict) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True), encoding="utf-8")


def _write_text(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def scan(root: Path) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, code: str) -> None:
        if not condition:
            errors.append(code)

    bootstrap = json.loads((root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json").read_text())
    program = json.loads((root / "research_entity/rooms/PROGRAM_STATE.json").read_text())
    manifest = json.loads((root / "the artefact/manifest.json").read_text())
    steering = json.loads((root / AUTHORITY).read_text())
    root_claude = (root / "CLAUDE.md").read_text()
    readme = (root / "the artefact/README.md").read_text()
    footer = (root / "research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md").read_text()

    require(bootstrap.get("authority_correction") == AUTHORITY, "BOOTSTRAP_AUTHORITY_POINTER_MISMATCH")
    require(program.get("authority_correction") == AUTHORITY, "PROGRAM_AUTHORITY_POINTER_MISMATCH")
    require(manifest.get("authority_correction") == AUTHORITY, "MANIFEST_AUTHORITY_POINTER_MISMATCH")
    require("SUPERVISOR_STEERING_8_62.json" in root_claude, "ROOT_CLAUDE_AUTHORITY_POINTER_MISMATCH")
    require("SUPERVISOR_STEERING_8_62.json" in readme, "README_AUTHORITY_POINTER_MISMATCH")
    require("SUPERVISOR_STEERING_8_62.json" in footer, "FOOTER_AUTHORITY_POINTER_MISMATCH")

    require(steering.get("schema_version") == "8.62", "STEERING_SCHEMA_MISMATCH")
    require(steering.get("mode") == "FREE_ONLY", "STEERING_NOT_FREE_ONLY")
    delta = steering.get("material_delta") or {}
    require(delta.get("vercel_hobby_sandbox") == "BOUNDED_INCLUDED_TIER_FREE_ADMITTED", "STEERING_HOBBY_ADMISSION_MISSING")
    require(delta.get("remaining_quota_directly_observed") is False, "STEERING_QUOTA_MUST_REMAIN_UNOBSERVED")
    require(delta.get("entityos_whole_runtime_credit_change") == 0, "STEERING_ENTITYOS_CREDIT_NONZERO")
    require(delta.get("hcu_full_runtime_credit_change") == 0, "STEERING_HCU_CREDIT_NONZERO")
    require(delta.get("jspace_model_runtime_credit_change") == 0, "STEERING_JSPACE_MODEL_CREDIT_NONZERO")
    require(delta.get("training_credit_change") == 0, "STEERING_TRAINING_CREDIT_NONZERO")

    free = steering.get("free_only_policy") or {}
    require(free.get("no_paid_fallback") is True, "STEERING_PAID_FALLBACK_WEAKENED")
    require(free.get("together_forbidden") is True, "STEERING_TOGETHER_FENCE_WEAKENED")
    require(free.get("paid_subscription_unknown_fail_closed") is True, "STEERING_UNKNOWN_PAID_LANE_WEAKENED")

    pexec = program.get("execution_policy") or {}
    require(pexec.get("vercel_hobby_sandbox") == "BOUNDED_INCLUDED_TIER_FREE_ADMITTED", "PROGRAM_HOBBY_ADMISSION_MISSING")
    require(pexec.get("vercel_hobby_remaining_quota_directly_observed") is False, "PROGRAM_QUOTA_MUST_REMAIN_UNOBSERVED")
    require(pexec.get("fail_closed_on_quota_billing_upgrade_plan_mismatch_or_charge_path") is True, "PROGRAM_MONETARY_FAIL_CLOSED_MISSING")

    mexec = manifest.get("execution_policy") or {}
    require(mexec.get("vercel_hobby_sandbox") == "BOUNDED_INCLUDED_TIER_FREE_ADMITTED", "MANIFEST_HOBBY_ADMISSION_MISSING")
    require(mexec.get("remaining_quota_directly_observed") is False, "MANIFEST_QUOTA_MUST_REMAIN_UNOBSERVED")
    require(mexec.get("fail_closed_on_quota_billing_upgrade_plan_mismatch_or_charge_path") is True, "MANIFEST_MONETARY_FAIL_CLOSED_MISSING")

    pcredit = program.get("runtime_credit") or {}
    mcredit = manifest.get("runtime_credit") or {}
    require(pcredit.get("entityos_hcu_whole_runtime_credit") == 0, "PROGRAM_WHOLE_RUNTIME_CREDIT_NONZERO")
    require(pcredit.get("hcu_full_runtime_credit") == 0, "PROGRAM_HCU_RUNTIME_CREDIT_NONZERO")
    require(pcredit.get("jspace_model_runtime_credit") == 0, "PROGRAM_JSPACE_MODEL_RUNTIME_CREDIT_NONZERO")
    require(pcredit.get("training_credit") == 0, "PROGRAM_TRAINING_CREDIT_NONZERO")
    require(pcredit.get("whole_product_pass") is False, "PROGRAM_WHOLE_PASS_PREMATURE")
    require(mcredit.get("entityos_hcu_whole_runtime_credit") == 0, "MANIFEST_WHOLE_RUNTIME_CREDIT_NONZERO")
    require(mcredit.get("hcu_full_runtime_credit") == 0, "MANIFEST_HCU_RUNTIME_CREDIT_NONZERO")
    require(mcredit.get("jspace_model_runtime_credit") == 0, "MANIFEST_JSPACE_MODEL_RUNTIME_CREDIT_NONZERO")
    require(mcredit.get("training_credit") == 0, "MANIFEST_TRAINING_CREDIT_NONZERO")
    require(mcredit.get("whole_product_pass") is False, "MANIFEST_WHOLE_PASS_PREMATURE")

    return errors


def make_fixture(root: Path) -> None:
    _write_json(root, "research_entity/continuity/BOOTSTRAP_MINIMAL.json", {
        "authority_correction": AUTHORITY,
    })
    _write_json(root, "research_entity/rooms/PROGRAM_STATE.json", {
        "authority_correction": AUTHORITY,
        "execution_policy": {
            "vercel_hobby_sandbox": "BOUNDED_INCLUDED_TIER_FREE_ADMITTED",
            "vercel_hobby_remaining_quota_directly_observed": False,
            "fail_closed_on_quota_billing_upgrade_plan_mismatch_or_charge_path": True,
        },
        "runtime_credit": {
            "entityos_hcu_whole_runtime_credit": 0,
            "hcu_full_runtime_credit": 0,
            "jspace_model_runtime_credit": 0,
            "training_credit": 0,
            "whole_product_pass": False,
        },
    })
    _write_json(root, "the artefact/manifest.json", {
        "authority_correction": AUTHORITY,
        "execution_policy": {
            "vercel_hobby_sandbox": "BOUNDED_INCLUDED_TIER_FREE_ADMITTED",
            "remaining_quota_directly_observed": False,
            "fail_closed_on_quota_billing_upgrade_plan_mismatch_or_charge_path": True,
        },
        "runtime_credit": {
            "entityos_hcu_whole_runtime_credit": 0,
            "hcu_full_runtime_credit": 0,
            "jspace_model_runtime_credit": 0,
            "training_credit": 0,
            "whole_product_pass": False,
        },
    })
    _write_json(root, AUTHORITY, {
        "schema_version": "8.62",
        "mode": "FREE_ONLY",
        "material_delta": {
            "vercel_hobby_sandbox": "BOUNDED_INCLUDED_TIER_FREE_ADMITTED",
            "remaining_quota_directly_observed": False,
            "entityos_whole_runtime_credit_change": 0,
            "hcu_full_runtime_credit_change": 0,
            "jspace_model_runtime_credit_change": 0,
            "training_credit_change": 0,
        },
        "free_only_policy": {
            "no_paid_fallback": True,
            "together_forbidden": True,
            "paid_subscription_unknown_fail_closed": True,
        },
    })
    _write_text(root, "CLAUDE.md", "read SUPERVISOR_STEERING_8_62.json\n")
    _write_text(root, "the artefact/README.md", "current SUPERVISOR_STEERING_8_62.json\n")
    _write_text(root, "research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md", "authority SUPERVISOR_STEERING_8_62.json\n")


class Supervisor862SurfaceAlignmentTests(unittest.TestCase):
    def fixture(self) -> Path:
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        root = Path(td.name)
        make_fixture(root)
        return root

    def test_coherent_862_fixture_passes(self):
        self.assertEqual([], scan(self.fixture()))

    def test_steering_862_pointer_rollback_poison_fails_closed(self):
        root = self.fixture()
        path = root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
        data = json.loads(path.read_text())
        data["authority_correction"] = STALE_861
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("BOOTSTRAP_AUTHORITY_POINTER_MISMATCH", scan(root))

    def test_billing_fail_closed_weakening_is_rejected(self):
        root = self.fixture()
        path = root / "research_entity/rooms/PROGRAM_STATE.json"
        data = json.loads(path.read_text())
        data["execution_policy"]["fail_closed_on_quota_billing_upgrade_plan_mismatch_or_charge_path"] = False
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("PROGRAM_MONETARY_FAIL_CLOSED_MISSING", scan(root))

    def test_runtime_credit_self_promotion_is_rejected(self):
        root = self.fixture()
        path = root / "the artefact/manifest.json"
        data = json.loads(path.read_text())
        data["runtime_credit"]["hcu_full_runtime_credit"] = 1
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("MANIFEST_HCU_RUNTIME_CREDIT_NONZERO", scan(root))


if __name__ == "__main__":
    unittest.main()

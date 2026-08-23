import json
import tempfile
import unittest
from pathlib import Path

OWNER = "research_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md"
BOOTSTRAP = "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
STEERING_848 = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_48.json"
STEERING_849 = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_49.json"
WORKERS = "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md"
EXPECTED_PROGRAM = "CLAYVERSE_SINGLE_CONTAINER"
EXPECTED_STAGE = "CLAYVERSE_ARTIFACT"
OWNER_REENTRY = "2026-08-23T16:49:00+07:00"
AUTHORITY_PR = 1302
AUTHORITY_MERGE = "d2f04f3bbc2eae314c7a940d010896aef7b33c4a"
WORKER_MARKER = "[CLAYVERSE :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]"


def load_json(path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_current_reentry(root: Path):
    errors = []
    paths = {
        "bootstrap": root / BOOTSTRAP,
        "steering848": root / STEERING_848,
        "steering849": root / STEERING_849,
        "workers": root / WORKERS,
    }
    for name, path in paths.items():
        if not path.is_file():
            errors.append(f"MISSING:{name}")
    if errors:
        return errors

    bootstrap = load_json(paths["bootstrap"])
    s848 = load_json(paths["steering848"])
    s849 = load_json(paths["steering849"])
    workers = paths["workers"].read_text(encoding="utf-8")

    if bootstrap.get("active_program") != EXPECTED_PROGRAM:
        errors.append("BOOTSTRAP_PROGRAM_MISMATCH")
    if bootstrap.get("active_stage") != EXPECTED_STAGE:
        errors.append("BOOTSTRAP_STAGE_MISMATCH")
    if bootstrap.get("sole_owner_directive") != OWNER:
        errors.append("BOOTSTRAP_OWNER_MISMATCH")
    if bootstrap.get("all_worker_protocol") != WORKERS:
        errors.append("BOOTSTRAP_WORKER_POINTER_MISMATCH")
    injection = str(bootstrap.get("go_prompt_injection", ""))
    if "ClayVerse" not in injection or "owner/product authority" not in injection:
        errors.append("BOOTSTRAP_GO_INJECTION_NOT_CLAYVERSE")

    if s848.get("status") != "CURRENT_OWNER_REENTRY_STEERING":
        errors.append("STEERING848_NOT_OWNER_REENTRY")
    if s848.get("program") != EXPECTED_PROGRAM or s848.get("stage") != EXPECTED_STAGE:
        errors.append("STEERING848_PROGRAM_STAGE_MISMATCH")
    if s848.get("owner_reentry") != OWNER_REENTRY or s848.get("owner_directive") != OWNER:
        errors.append("STEERING848_OWNER_REENTRY_MISMATCH")

    if s849.get("status") != "CURRENT_POSTMERGE_CLAYVERSE_STEERING":
        errors.append("STEERING849_NOT_POSTMERGE_CURRENT")
    if s849.get("program") != EXPECTED_PROGRAM or s849.get("stage") != EXPECTED_STAGE:
        errors.append("STEERING849_PROGRAM_STAGE_MISMATCH")
    if s849.get("owner_reentry") != s848.get("owner_reentry"):
        errors.append("STEERING849_OWNER_REENTRY_DRIFT")
    if s849.get("owner_directive") != OWNER:
        errors.append("STEERING849_OWNER_DIRECTIVE_MISMATCH")
    if s849.get("authority_reentry_pr") != AUTHORITY_PR:
        errors.append("STEERING849_AUTHORITY_PR_MISMATCH")
    if s849.get("authority_merge_commit") != AUTHORITY_MERGE:
        errors.append("STEERING849_AUTHORITY_MERGE_MISMATCH")
    if (s849.get("postmerge_authority_state") or {}).get("bootstrap") != EXPECTED_PROGRAM:
        errors.append("STEERING849_POSTMERGE_BOOTSTRAP_MISMATCH")
    experiment = s849.get("unusual_experiment") or {}
    if experiment.get("macrocycle_count") != 1 or experiment.get("additional_unusual_experiment_forbidden_this_go") is not True:
        errors.append("STEERING849_EXPERIMENT_LEASE_MISMATCH")

    upper = workers.upper()
    if "STATUS: **CURRENT PROJECT OWNER WORKER DIRECTIVE**" not in upper:
        errors.append("WORKER_DIRECTIVE_NOT_CURRENT")
    if "ACTIVE PRODUCT: **CLAYVERSE**" not in upper:
        errors.append("WORKER_PRODUCT_MISMATCH")
    if WORKER_MARKER not in workers:
        errors.append("WORKER_LITERAL_INJECTION_MARKER_MISSING")
    if "[MINI ENTITY ::" in upper:
        errors.append("WORKER_STALE_MINI_ENTITY_MARKER")
    if "VPS/SELF-HOSTED/PRODUCTION-HOST TEST EVIDENCE IS FORBIDDEN." not in upper:
        errors.append("WORKER_EXECUTION_FENCE_MISSING")
    if "TOGETHER API/SERVICE IS FORBIDDEN." not in upper:
        errors.append("WORKER_TOGETHER_FENCE_MISSING")

    return errors


def fixture(root: Path):
    for rel in [BOOTSTRAP, STEERING_848, STEERING_849, WORKERS]:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / BOOTSTRAP).write_text(json.dumps({
        "active_program": EXPECTED_PROGRAM,
        "active_stage": EXPECTED_STAGE,
        "sole_owner_directive": OWNER,
        "all_worker_protocol": WORKERS,
        "go_prompt_injection": "every spawned child receives the current GRF+ClayCode worker protocol plus the current ClayVerse owner/product authority",
    }), encoding="utf-8")
    (root / STEERING_848).write_text(json.dumps({
        "status": "CURRENT_OWNER_REENTRY_STEERING",
        "program": EXPECTED_PROGRAM,
        "stage": EXPECTED_STAGE,
        "owner_reentry": OWNER_REENTRY,
        "owner_directive": OWNER,
    }), encoding="utf-8")
    (root / STEERING_849).write_text(json.dumps({
        "status": "CURRENT_POSTMERGE_CLAYVERSE_STEERING",
        "program": EXPECTED_PROGRAM,
        "stage": EXPECTED_STAGE,
        "owner_reentry": OWNER_REENTRY,
        "owner_directive": OWNER,
        "authority_reentry_pr": AUTHORITY_PR,
        "authority_merge_commit": AUTHORITY_MERGE,
        "postmerge_authority_state": {"bootstrap": EXPECTED_PROGRAM},
        "unusual_experiment": {
            "macrocycle_count": 1,
            "already_consumed": "AUTHORITY_ROLLBACK_POISON_REPLAY",
            "additional_unusual_experiment_forbidden_this_go": True,
        },
    }), encoding="utf-8")
    (root / WORKERS).write_text(
        "# ClayCode All-Workers Execution Directive — ClayVerse\n"
        "Status: **CURRENT PROJECT OWNER WORKER DIRECTIVE**\n"
        "Active product: **ClayVerse**\n"
        f"{WORKER_MARKER}\n"
        "VPS/self-hosted/production-host test evidence is forbidden.\n"
        "Together API/service is forbidden.\n",
        encoding="utf-8",
    )


class CurrentReentrySteeringTests(unittest.TestCase):
    def make_tree(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        fixture(root)
        self.addCleanup(td.cleanup)
        return root

    def test_current_owner_reentry_and_postmerge_chain_passes(self):
        root = self.make_tree()
        self.assertEqual(validate_current_reentry(root), [])

    def test_postmerge_steering_cannot_reactivate_mini_entity(self):
        root = self.make_tree()
        path = root / STEERING_849
        data = load_json(path)
        data["program"] = "MINI_ENTITY_PIPELINE_ALL_IN_ONE"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("STEERING849_PROGRAM_STAGE_MISMATCH", validate_current_reentry(root))

    def test_postmerge_steering_must_bind_owner_reentry_merge(self):
        root = self.make_tree()
        path = root / STEERING_849
        data = load_json(path)
        data["authority_merge_commit"] = "0" * 40
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("STEERING849_AUTHORITY_MERGE_MISMATCH", validate_current_reentry(root))

    def test_child_go_worker_marker_cannot_regress_to_mini_entity(self):
        root = self.make_tree()
        path = root / WORKERS
        text = path.read_text(encoding="utf-8")
        text = text.replace(WORKER_MARKER, "[MINI ENTITY :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]")
        path.write_text(text, encoding="utf-8")
        errors = validate_current_reentry(root)
        self.assertIn("WORKER_LITERAL_INJECTION_MARKER_MISSING", errors)
        self.assertIn("WORKER_STALE_MINI_ENTITY_MARKER", errors)

    def test_bootstrap_worker_pointer_is_bound(self):
        root = self.make_tree()
        path = root / BOOTSTRAP
        data = load_json(path)
        data["all_worker_protocol"] = "research_entity/claycode/STALE_WORKER.md"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("BOOTSTRAP_WORKER_POINTER_MISMATCH", validate_current_reentry(root))

    def test_unusual_experiment_lease_cannot_be_reopened(self):
        root = self.make_tree()
        path = root / STEERING_849
        data = load_json(path)
        data["unusual_experiment"]["additional_unusual_experiment_forbidden_this_go"] = False
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("STEERING849_EXPERIMENT_LEASE_MISMATCH", validate_current_reentry(root))


if __name__ == "__main__":
    unittest.main()

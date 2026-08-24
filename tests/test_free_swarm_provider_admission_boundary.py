from __future__ import annotations

import datetime as dt
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools/free_swarm_provider_admission.py"
spec = importlib.util.spec_from_file_location("free_swarm_provider_admission_tested", MODULE_PATH)
assert spec and spec.loader
policy = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = policy
spec.loader.exec_module(policy)


class FreeSwarmProviderAdmissionBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.supervisor = self.root / "SUPERVISOR_INBOX.json"
        self.supervisor.write_text(json.dumps({
            "schema_version": "8.67",
            "free_only": {
                "enabled": True,
                "provider_execution_requires_typed_explicit_free_classification": True,
                "admission_boundary": "BEFORE_SECRET_OR_KEY_LOOKUP_AND_BEFORE_NETWORK_IO",
            },
        }), encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def admission_file(self, cost_class: str = "FREE", admitted: bool = True,
                       authority_epoch: str = "8.67") -> Path:
        path = self.root / f"admission-{cost_class}-{admitted}.json"
        path.write_text(json.dumps({
            "schema": policy.SCHEMA,
            "admission_id": f"test-{cost_class}-{admitted}",
            "authority_epoch": authority_epoch,
            "mode": "FREE_ONLY",
            "source": "ENTITYOS_HCU_CONTROL_PLANE",
            "issued_at": "2026-08-24T00:00:00Z",
            "valid_until": "2099-01-01T00:00:00Z",
            "providers": {
                "groq": {
                    "cost_class": cost_class,
                    "admitted": admitted,
                    "evidence_ref": "test:typed-cost-evidence",
                }
            },
        }), encoding="utf-8")
        return path

    def attempt_with_tripwires(self, path: Path | None) -> tuple[str, dict[str, int]]:
        counts = {"secret": 0, "network": 0}

        def secret_tripwire(_permit):
            counts["secret"] += 1
            return "redacted-capability"

        def socket_tripwire(_permit):
            counts["network"] += 1
            return "network-would-run"

        try:
            if path is None:
                policy.load_admission(self.root / "missing.json", supervisor_path=self.supervisor)
            else:
                snap = policy.load_admission(path, supervisor_path=self.supervisor)
                policy.with_provider_permit(snap, "groq", secret_tripwire, supervisor_path=self.supervisor)
                policy.with_provider_permit(snap, "groq", socket_tripwire, supervisor_path=self.supervisor)
        except policy.AdmissionError as exc:
            return str(exc), counts
        return "PASS", counts

    def test_missing_admission_blocks_before_secret_and_network(self) -> None:
        verdict, counts = self.attempt_with_tripwires(None)
        self.assertNotEqual(verdict, "PASS")
        self.assertEqual(counts, {"secret": 0, "network": 0})

    def test_unknown_paid_subscription_block_before_tripwires(self) -> None:
        for cost_class in ("UNKNOWN", "PAID", "SUBSCRIPTION"):
            with self.subTest(cost_class=cost_class):
                verdict, counts = self.attempt_with_tripwires(self.admission_file(cost_class, False))
                self.assertIn("provider_not_explicit_free", verdict)
                self.assertEqual(counts, {"secret": 0, "network": 0})

    def test_environment_style_boolean_cannot_replace_typed_admission(self) -> None:
        verdict, counts = self.attempt_with_tripwires(None)
        self.assertIn("admission_unavailable", verdict)
        self.assertEqual(counts, {"secret": 0, "network": 0})

    def test_stale_authority_blocks_before_tripwires(self) -> None:
        verdict, counts = self.attempt_with_tripwires(self.admission_file("FREE", True, "8.66"))
        self.assertIn("authority_epoch_stale_or_mismatched", verdict)
        self.assertEqual(counts, {"secret": 0, "network": 0})

    def test_current_explicit_free_reaches_each_guarded_operation(self) -> None:
        verdict, counts = self.attempt_with_tripwires(self.admission_file("FREE", True))
        self.assertEqual(verdict, "PASS")
        self.assertEqual(counts, {"secret": 1, "network": 1})

    def test_nonfree_row_cannot_self_mark_admitted(self) -> None:
        verdict, counts = self.attempt_with_tripwires(self.admission_file("PAID", True))
        self.assertIn("nonfree_provider_cannot_be_admitted", verdict)
        self.assertEqual(counts, {"secret": 0, "network": 0})

    def test_supervisor_change_invalidates_snapshot_before_operation(self) -> None:
        snap = policy.load_admission(self.admission_file("FREE", True), supervisor_path=self.supervisor)
        self.supervisor.write_text(json.dumps({
            "schema_version": "8.68",
            "free_only": {
                "enabled": True,
                "provider_execution_requires_typed_explicit_free_classification": True,
                "admission_boundary": "BEFORE_SECRET_OR_KEY_LOOKUP_AND_BEFORE_NETWORK_IO",
            },
        }), encoding="utf-8")
        calls = {"count": 0}
        with self.assertRaises(policy.AdmissionError):
            policy.with_provider_permit(
                snap,
                "groq",
                lambda _permit: calls.__setitem__("count", calls["count"] + 1),
                supervisor_path=self.supervisor,
            )
        self.assertEqual(calls["count"], 0)

    def test_source_ordering_guards_are_present(self) -> None:
        shell = (ROOT / "tools/run_24h_entityos_swarm_supervisor.sh").read_text(encoding="utf-8")
        wrapper = (ROOT / "tools/run_free_go_swarm.py").read_text(encoding="utf-8")
        driver = (ROOT / "tools/run_24h_entityos_swarm.py").read_text(encoding="utf-8")
        self.assertNotIn("load_all_secret_sources", shell)
        loop = shell[shell.index("while (( $(date +%s) < DEADLINE ))") :]
        self.assertLess(loop.index("resolve_typed_admission"), loop.index("load_admitted_secret_sources"))
        self.assertIn("with_provider_permit", wrapper)
        self.assertIn("activate_provider_admission()", driver)
        self.assertLess(driver.index("activate_provider_admission()"), driver.index("discover_and_export(args.timeout)"))
        self.assertIn("base.require_provider_admitted(provider)", driver)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
TESTS = ROOT / "tests"
for path in (TOOLS, TESTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import free_provider_admission as admission_mod
import test_free_swarm_admission_boundary_867 as boundary


class FreeSwarmAdmissionBoundaryReceiptV1Tests(unittest.TestCase):
    def test_malformed_provider_admission_fails_before_secret_or_network(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            malformed = root / "admission.json"
            malformed.write_text('{"schema":', encoding="utf-8")
            inbox = boundary._authority(root)
            case = boundary.FreeProviderAdmissionBoundaryTests(methodName="runTest")
            code, secret_reads, network = case._run_with_tripwires(
                malformed, root, inbox, global_attested=True
            )
        self.assertEqual(code, 5)
        self.assertEqual(secret_reads, 0)
        self.assertEqual(network, 0)

    def test_current_registry_is_bound_to_current_supervisor_epoch_and_fail_closed(self) -> None:
        inbox = json.loads(
            (ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json").read_text(encoding="utf-8")
        )
        admission = json.loads(
            (ROOT / "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json").read_text(encoding="utf-8")
        )
        self.assertEqual(admission.get("authority_epoch"), inbox.get("schema_version"))
        self.assertEqual(admission.get("mode"), "FREE_ONLY")
        providers = admission.get("providers")
        self.assertIsInstance(providers, dict)
        self.assertEqual(set(providers), set(admission_mod.ALLOWED_PROVIDERS))
        for name, record in providers.items():
            with self.subTest(provider=name):
                self.assertIsInstance(record, dict)
                self.assertFalse(record.get("admitted"))
                self.assertEqual(record.get("cost_class"), "UNKNOWN")


if __name__ == "__main__":
    unittest.main()

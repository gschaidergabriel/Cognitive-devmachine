from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_provider_admission as admission
import run_omega_continuous_free_workers as continuous


class FreeAdmissionAuthorityTests(unittest.TestCase):
    def _control_root(self, *, steering_extra=None, inbox_extra=None) -> tuple[Path, tempfile.TemporaryDirectory]:
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        rel = Path("research_entity/claycode/autonomous/STEERING.json")
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        steering = {"schema_version": "9.13"}
        steering.update(steering_extra or {})
        (root / rel).write_text(json.dumps(steering), encoding="utf-8")
        inbox = {
            "schema_version": "9.13",
            "active_program": "ENTITYOS_HCU",
            "product": "EntityOS",
            "integrated_cognition_compute_architecture": "HCU",
            "steering": str(rel),
        }
        inbox.update(inbox_extra or {})
        inbox_path = root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
        inbox_path.write_text(json.dumps(inbox), encoding="utf-8")
        return root, td

    def test_steering_may_omit_identity_repeated_by_current_inbox(self):
        root, td = self._control_root()
        try:
            epoch, ref = admission._resolve_current_supervisor(
                inbox_path=root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
                root=root,
            )
            self.assertEqual(epoch, "9.13")
            self.assertEqual(ref, "research_entity/claycode/autonomous/STEERING.json")
        finally:
            td.cleanup()

    def test_explicit_steering_conflict_fails_closed(self):
        root, td = self._control_root(steering_extra={"product": "OtherProduct"})
        try:
            with self.assertRaises(admission.ProviderAdmissionError) as ctx:
                admission._resolve_current_supervisor(
                    inbox_path=root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
                    root=root,
                )
            self.assertIn("PRODUCT_AUTHORITY_CONFLICT", str(ctx.exception))
        finally:
            td.cleanup()

    def test_program_alias_conflict_fails_closed(self):
        root, td = self._control_root(
            steering_extra={"active_program": "ENTITYOS_HCU", "program": "OTHER"}
        )
        try:
            with self.assertRaises(admission.ProviderAdmissionError) as ctx:
                admission._resolve_current_supervisor(
                    inbox_path=root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
                    root=root,
                )
            self.assertIn("PROGRAM_ALIAS_CONFLICT", str(ctx.exception))
        finally:
            td.cleanup()


class ContinuousCandidateTests(unittest.TestCase):
    def test_distilled_worker_output_is_noncanonical_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            epoch = root / "epoch"
            candidates = root / "candidates"
            epoch.mkdir()
            text = (
                "GRF candidate. Concrete falsifier and patch path. "
                + "x" * 240
                + "\nDEUTSCHE_ZUSAMMENFASSUNG\nBefund; Gegenhypothese; naechster Test; erwartetes messbares Delta."
            )
            row = {
                "http_status": 200,
                "text": text,
                "text_sha256": continuous.sha256_text(text),
                "provider": "nvidia",
                "model": "free-test-model",
                "role": "FALSIFIER",
                "worker_id": 1,
                "worker_serial": 1,
                "repo_head_at_prompt": "deadbeef",
                "conformance": {
                    "protocol_injected": True,
                    "german_summary_marker": True,
                    "grf_marker": True,
                },
            }
            (epoch / "workers.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
            result = continuous.distill_epoch(epoch, candidates)
            self.assertEqual(result["accepted"], 1)
            files = list(candidates.glob("*.json"))
            self.assertEqual(len(files), 1)
            candidate = json.loads(files[0].read_text(encoding="utf-8"))
            self.assertEqual(candidate["evidence_class"], "MODEL_GENERATED")
            self.assertEqual(candidate["authority"], "CANDIDATE_ONLY")
            self.assertFalse(candidate["effect_authority"])
            self.assertFalse(candidate["promotion_authority"])
            self.assertEqual(candidate["canonical_credit_minted"], 0)
            self.assertEqual(candidate["training_credit"], 0)

    def test_duplicate_worker_text_is_collapsed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            epoch = root / "epoch"
            candidates = root / "candidates"
            epoch.mkdir()
            text = "GRF " + "y" * 260 + " DEUTSCHE_ZUSAMMENFASSUNG"
            row = {
                "http_status": 200,
                "text": text,
                "text_sha256": continuous.sha256_text(text),
                "conformance": {
                    "protocol_injected": True,
                    "german_summary_marker": True,
                    "grf_marker": True,
                },
            }
            (epoch / "workers.jsonl").write_text(
                json.dumps(row) + "\n" + json.dumps(row) + "\n", encoding="utf-8"
            )
            result = continuous.distill_epoch(epoch, candidates)
            self.assertEqual(result["accepted"], 1)
            self.assertGreaterEqual(result["duplicates"], 1)


if __name__ == "__main__":
    unittest.main()

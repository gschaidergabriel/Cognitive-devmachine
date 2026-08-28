from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools import hcu_jspace_local_activation_probe as probe


class JSpaceLocalActivationProbeContractTests(unittest.TestCase):
    def _authority(self, root: Path, *, epoch: str = "9.01", free_only: bool = True) -> None:
        autonomous = root / "research_entity/claycode/autonomous"
        autonomous.mkdir(parents=True, exist_ok=True)
        steering_rel = Path(f"research_entity/claycode/autonomous/SUPERVISOR_STEERING_{epoch.replace('.', '_')}.json")
        (root / steering_rel).write_text(
            json.dumps(
                {
                    "schema_version": epoch,
                    "active_program": "ENTITYOS_HCU",
                    "product": "EntityOS",
                    "integrated_cognition_compute_architecture": "HCU",
                    "free_only": {"enabled": free_only},
                }
            ),
            encoding="utf-8",
        )
        (autonomous / "SUPERVISOR_INBOX.json").write_text(
            json.dumps({"schema_version": epoch, "steering": steering_rel.as_posix()}),
            encoding="utf-8",
        )

    def _claim(
        self,
        root: Path,
        *,
        trigger_key: str = "rid_" + "a" * 64,
        claimant: str = "gpt56sol-test-organ",
        experiment: str = "HCU_JSPACE_LOCAL_ACTIVATION_PATCH_V1",
    ) -> Path:
        claims = root / "research_entity/continuity/go_experiment_claims"
        claims.mkdir(parents=True, exist_ok=True)
        path = claims / f"{trigger_key}.json"
        path.write_text(
            json.dumps(
                {
                    "schema": "clay-go-experiment-claim/v1",
                    "trigger_key": trigger_key,
                    "trigger": "go",
                    "experiment_name": experiment,
                    "claimant_organ": claimant,
                    "claimed_at": "2026-08-24T11:30:00Z",
                    "observed_canonical_main": "0" * 40,
                    "intervention_contract": "one offline activation patch family",
                    "status": "CLAIMED",
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_successor_dynamic_free_only_authority_resolves_without_fixed_epoch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._authority(root, epoch="9.01", free_only=True)
            resolved = probe.resolve_current_authority(root)
        self.assertEqual(resolved["epoch"], "9.01")
        self.assertEqual(
            resolved["steering_path"],
            "research_entity/claycode/autonomous/SUPERVISOR_STEERING_9_01.json",
        )

    def test_non_free_only_supervisor_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._authority(root, free_only=False)
            with self.assertRaisesRegex(probe.ProbeRejected, "FREE_ONLY_SUPERVISOR_REQUIRED"):
                probe.resolve_current_authority(root)

    def test_matching_atomic_claim_is_accepted_at_contract_level(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            claim = self._claim(root)
            result = probe.validate_atomic_claim(
                root,
                str(claim),
                "gpt56sol-test-organ",
                "HCU_JSPACE_LOCAL_ACTIVATION_PATCH_V1",
            )
        self.assertTrue(result["lease_file_validated"])
        self.assertFalse(result["create_only_semantics_reverified_by_probe"])
        self.assertEqual(result["trigger_key"], "rid_" + "a" * 64)

    def test_claimant_or_experiment_cannot_be_substituted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            claim = self._claim(root)
            with self.assertRaisesRegex(probe.ProbeRejected, "ATOMIC_CLAIM_FIELD_MISMATCH"):
                probe.validate_atomic_claim(
                    root,
                    str(claim),
                    "different-organ",
                    "HCU_JSPACE_LOCAL_ACTIVATION_PATCH_V1",
                )

    def test_existing_result_blocks_second_intervention(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            claim = self._claim(root)
            result_path = claim.with_name(claim.stem + ".result.json")
            result_path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(probe.ProbeRejected, "RESULT_ALREADY_EXISTS"):
                probe.validate_atomic_claim(
                    root,
                    str(claim),
                    "gpt56sol-test-organ",
                    "HCU_JSPACE_LOCAL_ACTIVATION_PATCH_V1",
                )

    def test_claim_outside_canonical_claim_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            outside = root / "claim.json"
            outside.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(probe.ProbeRejected, "CANONICAL_CLAIMS_DIRECTORY"):
                probe.validate_atomic_claim(
                    root,
                    str(outside),
                    "gpt56sol-test-organ",
                    "HCU_JSPACE_LOCAL_ACTIVATION_PATCH_V1",
                )


if __name__ == "__main__":
    unittest.main()

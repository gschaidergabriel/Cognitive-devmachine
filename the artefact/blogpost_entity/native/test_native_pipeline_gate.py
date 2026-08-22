from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


class NativePipelineGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp_context = tempfile.TemporaryDirectory(prefix="mini-native-pipeline-gate-")
        cls.tmp = Path(cls.tmp_context.name)
        cls.binary = cls.tmp / "mini_entity.clay"
        cls.build_receipt = cls.tmp / "build_receipt.json"
        subprocess.run(
            [
                sys.executable,
                str(HERE / "build_native_bound.py"),
                "--source",
                str(HERE / "mini_entity.c"),
                "--output",
                str(cls.binary),
                "--receipt",
                str(cls.build_receipt),
                "--version-label",
                "mini-entity/0.7.0-dev1",
                "--source-date-epoch",
                "1787371200",
                "--repeat",
                "2",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        cls.runner = cls.tmp / "gate_runner.py"
        cls.runner.write_text(
            "import json, pathlib, sys\n"
            "prompt=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))\n"
            "mode=sys.argv[2]\n"
            "payload={\n"
            " 'canonical_state_hash_seen':prompt['CANONICAL_STATE_HASH'],\n"
            " 'packet_hash_seen':prompt['PACKET_HASH'],\n"
            " 'title':'gate fixture', 'intro':'bounded fixture',\n"
            " 'sections':[{'text':'supported','evidence_refs':['ev:event-1'],'state_claims':{}}],\n"
            " 'continuity':{}, 'hypotheses':[]\n"
            "}\n"
            "if mode=='wrong_canonical': payload['canonical_state_hash_seen']='0'*64\n"
            "elif mode=='wrong_packet': payload['packet_hash_seen']='1'*64\n"
            "elif mode=='missing_title': payload.pop('title')\n"
            "elif mode=='leak_pattern': payload['title']='PRIVATE_NATIVE should never pass'\n"
            "elif mode=='no_evidence': payload['sections'][0]['evidence_refs']=[]\n"
            "elif mode=='unknown_ref': payload['sections'][0]['evidence_refs']=['ev:not-present']\n"
            "elif mode=='unverified_claim':\n"
            " payload['sections'][0]['evidence_refs']=['ev:event-1','state:unknown_metric']\n"
            " payload['sections'][0]['state_claims']={'unknown_metric':0.0}\n"
            "elif mode=='overshoot':\n"
            " payload['sections'][0]['evidence_refs']=['ev:event-1','state:confidence']\n"
            " payload['sections'][0]['state_claims']={'confidence':0.9}\n"
            "elif mode=='missing_metric_evidence': payload['sections'][0]['state_claims']={'confidence':0.8}\n"
            "elif mode=='valid_claim':\n"
            " payload['sections'][0]['evidence_refs']=['ev:event-1','state:confidence']\n"
            " payload['sections'][0]['state_claims']={'confidence':0.8}\n"
            "print(json.dumps(payload, sort_keys=True))\n",
            encoding="utf-8",
        )
        cls.profile = cls.tmp / "gate_profile.json"
        cls.profile.write_text(
            json.dumps(
                {
                    "schema": "clay-pipeline-profile/v2",
                    "profile_id": "native-gate-fixture",
                    "identity": {"task": "gate fixture", "language": "en"},
                    "inference": {"kind": "local_exec", "max_tokens": 128, "temperature": 0.0},
                    "personality": {
                        "system_prompt": "Return only the requested JSON object.",
                        "public_style": "plain",
                        "output_contract": {
                            "title_field": "title",
                            "intro_field": "intro",
                            "sections_field": "sections",
                            "section_text_field": "text",
                            "section_evidence_field": "evidence_refs",
                            "section_claims_field": "state_claims",
                            "continuity_field": "continuity",
                            "autobiographical_hypotheses_field": "hypotheses",
                            "longitudinal_self_report_field": "longitudinal_self_report",
                        },
                    },
                    "sources": [
                        {
                            "kind": "evidence",
                            "evidence_prefix": "ev:",
                            "required_for_quiet": True,
                        }
                    ],
                    "canonical_probes": [],
                    "state_metrics": [
                        {
                            "name": "confidence",
                            "status": "VERIFIED",
                            "value": 0.8,
                            "evidence_ref": "state:confidence",
                        },
                        {
                            "name": "unknown_metric",
                            "status": "UNKNOWN",
                            "value": 0.0,
                            "evidence_ref": "state:unknown_metric",
                        },
                    ],
                    "gate": {
                        "max_claim_overshoot": 0.05,
                        "require_evidence_per_section": True,
                        "require_hash_echo": True,
                        "leak_patterns": ["PRIVATE_NATIVE"],
                    },
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        cls.model = cls.tmp / "fixture.gguf"
        cls.model.write_bytes(b"fixture model placeholder\n")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp_context.cleanup()

    def _case(self, mode: str, expect_success: bool) -> None:
        root = self.tmp / mode
        root.mkdir(exist_ok=True)
        entity = root / "entity.db"
        source = root / "source.db"
        subprocess.run([str(self.binary), "init", str(entity)], check=True, stdout=subprocess.DEVNULL)
        subprocess.run([str(self.binary), "source-init", str(source)], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(
            [str(self.binary), "source-add", str(source), "evidence", "event-1", '{"fact":"bounded"}'],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        subprocess.run([str(self.binary), "preset-apply", str(entity), str(self.profile)], check=True, stdout=subprocess.DEVNULL)
        subprocess.run([str(self.binary), "set-local-model", str(entity), str(self.model)], check=True, stdout=subprocess.DEVNULL)
        runner_json = json.dumps(["python3", str(self.runner), "{{PROMPT_FILE}}", mode])
        subprocess.run(
            [str(self.binary), "set-local-runner-json", str(entity), runner_json],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        proc = subprocess.run(
            [str(self.binary), "run", str(entity), str(source)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if expect_success:
            self.assertEqual(proc.returncode, 0, proc.stderr)
            result = json.loads(proc.stdout)
            self.assertTrue(result["ok"])
            self.assertEqual(result["generation"], 1)
            self.assertEqual(result["source_count"], 1)
        else:
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("PIPELINE_GATE_REJECTED_NO_COMMIT", proc.stderr)
        with sqlite3.connect(entity) as db:
            self.assertEqual(db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()[0], 1 if expect_success else 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM outputs").fetchone()[0], 1 if expect_success else 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM study_rows").fetchone()[0], 1 if expect_success else 0)
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        with sqlite3.connect(source) as db:
            pending = db.execute("SELECT COUNT(*) FROM mini_entity_events WHERE consumed_generation IS NULL").fetchone()[0]
            self.assertEqual(pending, 0 if expect_success else 1)
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")

    def test_required_gate_falsifier_matrix(self) -> None:
        for mode in (
            "wrong_canonical",
            "wrong_packet",
            "missing_title",
            "leak_pattern",
            "no_evidence",
            "unknown_ref",
            "unverified_claim",
            "overshoot",
            "missing_metric_evidence",
        ):
            with self.subTest(mode=mode):
                self._case(mode, expect_success=False)
        self._case("valid_claim", expect_success=True)


if __name__ == "__main__":
    unittest.main()

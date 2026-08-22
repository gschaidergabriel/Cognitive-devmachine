from __future__ import annotations

import copy
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


class NativeSemanticGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp_context = tempfile.TemporaryDirectory(prefix="mini-native-semantic-gate-")
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

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp_context.cleanup()

    @classmethod
    def command(cls, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(cls.binary), *args],
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    @staticmethod
    def profile() -> dict:
        return {
            "schema": "clay-pipeline-profile/v2",
            "profile_id": "semantic-gate-fixture",
            "identity": {"task": "report bounded fixture evidence", "language": "en"},
            "personality": {
                "system_prompt": "Return only the configured JSON output.",
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
                    "longitudinal_self_report_field": "self_report",
                },
            },
            "inference": {
                "kind": "local_exec",
                "max_tokens": 128,
                "temperature": 0.0,
                "secret_names": [],
            },
            "sources": [
                {"kind": "evidence", "evidence_prefix": "evidence:"},
            ],
            "state_metrics": [
                {
                    "name": "verified_strength",
                    "status": "VERIFIED",
                    "value": 0.4,
                    "evidence_ref": "state:verified_strength",
                },
                {
                    "name": "unknown_strength",
                    "status": "UNKNOWN",
                    "value": 0.0,
                    "evidence_ref": "state:unknown_strength",
                },
            ],
            "gate": {
                "require_hash_echo": True,
                "require_evidence_per_section": True,
                "max_claim_overshoot": 0.05,
                "leak_patterns": ["FORBIDDEN_TOKEN", "private[_-]?table"],
            },
            "profile_notes": {"fixture": "generic semantic gate"},
        }

    @staticmethod
    def valid_payload() -> dict:
        return {
            "canonical_state_hash_seen": "__CANONICAL__",
            "packet_hash_seen": "__PACKET__",
            "title": "Bounded fixture",
            "intro": "Only admitted evidence is used.",
            "sections": [
                {
                    "text": "The bounded observation is present.",
                    "evidence_refs": ["evidence:event-1", "state:verified_strength"],
                    "state_claims": {"verified_strength": 0.4},
                }
            ],
            "continuity": "retain uncertainty",
            "hypotheses": [],
            "self_report": {},
        }

    def prepare(self, payload: dict) -> tuple[Path, Path]:
        case = Path(tempfile.mkdtemp(prefix="case-", dir=self.tmp))
        entity = case / "entity.db"
        source = case / "source.db"
        profile = case / "profile.json"
        model = case / "model.gguf"
        runner = case / "runner.py"
        output = case / "output.json"
        profile.write_text(json.dumps(self.profile(), sort_keys=True), encoding="utf-8")
        output.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        model.write_bytes(b"fixture-model-bytes\n")
        runner.write_text(
            "import json, pathlib, re, sys\n"
            "prompt=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')\n"
            "cm=re.search(r'\\\"CANONICAL_STATE_HASH\\\"\\s*:\\s*\\\"([0-9a-f]{64})\\\"', prompt)\n"
            "pm=re.search(r'\\\"PACKET_HASH\\\"\\s*:\\s*\\\"([0-9a-f]{64})\\\"', prompt)\n"
            "if not cm or not pm: raise SystemExit(43)\n"
            "obj=json.loads(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8'))\n"
            "def sub(v):\n"
            "    if isinstance(v,dict): return {k:sub(x) for k,x in v.items()}\n"
            "    if isinstance(v,list): return [sub(x) for x in v]\n"
            "    if v=='__CANONICAL__': return cm.group(1)\n"
            "    if v=='__PACKET__': return pm.group(1)\n"
            "    return v\n"
            "print(json.dumps(sub(obj), sort_keys=True))\n",
            encoding="utf-8",
        )
        self.command("init", str(entity))
        self.command("source-init", str(source))
        self.command("source-add", str(source), "evidence", "event-1", '{"measurement_status":"MEASURED","value":7}')
        self.command("preset-apply", str(entity), str(profile))
        self.command("set-local-model", str(entity), str(model))
        self.command("set-local-runner-json", str(entity), json.dumps(["python3", str(runner), "{{PROMPT_FILE}}", str(output)]))
        return entity, source

    def assert_no_commit(self, entity: Path, source: Path) -> None:
        with sqlite3.connect(entity) as db:
            self.assertEqual(db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM outputs").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM study_rows").fetchone()[0], 0)
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        with sqlite3.connect(source) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM mini_entity_events WHERE consumed_generation IS NULL").fetchone()[0], 1)
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")

    def reject(self, payload: dict, reason: str) -> None:
        entity, source = self.prepare(payload)
        run = self.command("run", str(entity), str(source), check=False)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("ERROR:" + reason, run.stderr)
        self.assert_no_commit(entity, source)

    def test_valid_gated_payload_commits_exactly_once(self) -> None:
        entity, source = self.prepare(self.valid_payload())
        first = json.loads(self.command("run", str(entity), str(source)).stdout)
        self.assertTrue(first["ok"])
        self.assertFalse(first["quiet"])
        self.assertEqual(first["generation"], 1)
        self.assertEqual(first["source_count"], 1)
        self.assertRegex(first["canonical_state_hash"], r"^[0-9a-f]{64}$")
        self.assertRegex(first["packet_hash"], r"^[0-9a-f]{64}$")
        quiet = json.loads(self.command("run", str(entity), str(source)).stdout)
        self.assertTrue(quiet["quiet"])
        self.assertEqual(quiet["generation"], 1)
        with sqlite3.connect(entity) as db:
            self.assertEqual(db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM outputs").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM study_rows").fetchone()[0], 1)
        with sqlite3.connect(source) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM mini_entity_events WHERE consumed_generation IS NULL").fetchone()[0], 0)

    def test_wrong_canonical_hash_rejected(self) -> None:
        p=self.valid_payload();p["canonical_state_hash_seen"]="0"*64
        self.reject(p,"CANONICAL_HASH_MISMATCH_NO_COMMIT")

    def test_wrong_packet_hash_rejected(self) -> None:
        p=self.valid_payload();p["packet_hash_seen"]="1"*64
        self.reject(p,"PACKET_HASH_MISMATCH_NO_COMMIT")

    def test_missing_required_output_field_rejected(self) -> None:
        p=self.valid_payload();del p["title"]
        self.reject(p,"MISSING_OUTPUT_FIELD_NO_COMMIT")

    def test_configured_leak_pattern_rejected(self) -> None:
        p=self.valid_payload();p["title"]="FORBIDDEN_TOKEN"
        self.reject(p,"LEAK_PATTERN_NO_COMMIT")

    def test_section_without_evidence_rejected(self) -> None:
        p=self.valid_payload();p["sections"][0]["evidence_refs"]=[]
        self.reject(p,"SECTION_WITHOUT_EVIDENCE_NO_COMMIT")

    def test_unknown_evidence_ref_rejected(self) -> None:
        p=self.valid_payload();p["sections"][0]["evidence_refs"]=["evidence:not-admitted"]
        p["sections"][0]["state_claims"]={}
        self.reject(p,"UNKNOWN_EVIDENCE_REF_NO_COMMIT")

    def test_claim_on_unknown_metric_rejected(self) -> None:
        p=self.valid_payload();p["sections"][0]["evidence_refs"]=["evidence:event-1","state:unknown_strength"]
        p["sections"][0]["state_claims"]={"unknown_strength":0.0}
        self.reject(p,"UNVERIFIED_STATE_CLAIM_NO_COMMIT")

    def test_state_claim_overshoot_rejected(self) -> None:
        p=self.valid_payload();p["sections"][0]["state_claims"]={"verified_strength":0.6}
        self.reject(p,"STATE_CLAIM_OVERSHOOT_NO_COMMIT")

    def test_verified_claim_requires_metric_evidence_ref(self) -> None:
        p=self.valid_payload();p["sections"][0]["evidence_refs"]=["evidence:event-1"]
        self.reject(p,"STATE_CLAIM_WITHOUT_METRIC_EVIDENCE_NO_COMMIT")

    def test_unsupported_metric_expression_stays_unknown(self) -> None:
        profile=self.profile()
        profile["state_metrics"].append({
            "name":"unsupported_dynamic",
            "unknown_if":{"ref":"probes.unavailable.ok"},
            "value":{"count_where":{"ref":"sources.x.rows","field":"status","in":["OPEN"]}},
            "evidence_ref":"state:unsupported_dynamic",
        })
        p=self.valid_payload()
        p["sections"][0]["evidence_refs"]=["evidence:event-1","state:unsupported_dynamic"]
        p["sections"][0]["state_claims"]={"unsupported_dynamic":0.0}
        case=Path(tempfile.mkdtemp(prefix="unsupported-",dir=self.tmp))
        entity=case/"entity.db";source=case/"source.db";profile_path=case/"profile.json";model=case/"model.gguf";runner=case/"runner.py";output=case/"output.json"
        profile_path.write_text(json.dumps(profile,sort_keys=True),encoding="utf-8");output.write_text(json.dumps(p,sort_keys=True),encoding="utf-8");model.write_bytes(b"fixture\n")
        runner.write_text("import json,pathlib,re,sys\ns=pathlib.Path(sys.argv[1]).read_text();c=re.search(r'\\\"CANONICAL_STATE_HASH\\\"\\s*:\\s*\\\"([0-9a-f]{64})\\\"',s);p=re.search(r'\\\"PACKET_HASH\\\"\\s*:\\s*\\\"([0-9a-f]{64})\\\"',s);o=json.loads(pathlib.Path(sys.argv[2]).read_text());o['canonical_state_hash_seen']=c.group(1);o['packet_hash_seen']=p.group(1);print(json.dumps(o))\n",encoding="utf-8")
        self.command("init",str(entity));self.command("source-init",str(source));self.command("source-add",str(source),"evidence","event-1",'{"value":1}');self.command("preset-apply",str(entity),str(profile_path));self.command("set-local-model",str(entity),str(model));self.command("set-local-runner-json",str(entity),json.dumps(["python3",str(runner),"{{PROMPT_FILE}}",str(output)]))
        run=self.command("run",str(entity),str(source),check=False)
        self.assertNotEqual(run.returncode,0);self.assertIn("ERROR:UNVERIFIED_STATE_CLAIM_NO_COMMIT",run.stderr);self.assert_no_commit(entity,source)


if __name__ == "__main__":
    unittest.main()

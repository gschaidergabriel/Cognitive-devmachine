from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from test_native_semantic_gate import NativeSemanticGateTests


class NativeMetricDivZeroUnknownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        NativeSemanticGateTests.setUpClass()
        cls.tmp = NativeSemanticGateTests.tmp
        cls.binary = NativeSemanticGateTests.binary

    @classmethod
    def tearDownClass(cls) -> None:
        NativeSemanticGateTests.tearDownClass()

    @classmethod
    def command(cls, *args: str, check: bool = True):
        return NativeSemanticGateTests.command(*args, check=check)

    def test_division_by_zero_metric_stays_unknown_and_cannot_be_claimed(self) -> None:
        profile = NativeSemanticGateTests.profile()
        profile["state_metrics"].append(
            {
                "name": "div_zero_metric",
                "unknown_if": False,
                "value": {"op": "div", "a": 1, "b": 0},
                "evidence_ref": "state:div_zero_metric",
            }
        )
        payload = NativeSemanticGateTests.valid_payload()
        payload["sections"][0]["evidence_refs"] = [
            "evidence:event-1",
            "state:div_zero_metric",
        ]
        payload["sections"][0]["state_claims"] = {"div_zero_metric": 0.0}

        case = Path(tempfile.mkdtemp(prefix="div0-unknown-", dir=self.tmp))
        entity = case / "entity.db"
        source = case / "source.db"
        profile_path = case / "profile.json"
        model = case / "model.gguf"
        runner = case / "runner.py"
        output = case / "output.json"

        profile_path.write_text(json.dumps(profile, sort_keys=True), encoding="utf-8")
        output.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        model.write_bytes(b"fixture\n")
        runner.write_text(
            "import json,pathlib,re,sys\n"
            "s=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')\n"
            "c=re.search(r'\\\"CANONICAL_STATE_HASH\\\"\\s*:\\s*\\\"([0-9a-f]{64})\\\"',s)\n"
            "p=re.search(r'\\\"PACKET_HASH\\\"\\s*:\\s*\\\"([0-9a-f]{64})\\\"',s)\n"
            "o=json.loads(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8'))\n"
            "o['canonical_state_hash_seen']=c.group(1)\n"
            "o['packet_hash_seen']=p.group(1)\n"
            "print(json.dumps(o,sort_keys=True))\n",
            encoding="utf-8",
        )

        self.command("init", str(entity))
        self.command("source-init", str(source))
        self.command(
            "source-add",
            str(source),
            "evidence",
            "event-1",
            '{"measurement_status":"MEASURED","value":7}',
        )
        self.command("preset-apply", str(entity), str(profile_path))
        self.command("set-local-model", str(entity), str(model))
        self.command(
            "set-local-runner-json",
            str(entity),
            json.dumps(["python3", str(runner), "{{PROMPT_FILE}}", str(output)]),
        )

        run = self.command("run", str(entity), str(source), check=False)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("ERROR:UNVERIFIED_STATE_CLAIM_NO_COMMIT", run.stderr)

        with sqlite3.connect(entity) as db:
            self.assertEqual(db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM outputs").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM study_rows").fetchone()[0], 0)
        with sqlite3.connect(source) as db:
            self.assertEqual(
                db.execute(
                    "SELECT COUNT(*) FROM mini_entity_events WHERE consumed_generation IS NULL"
                ).fetchone()[0],
                1,
            )


if __name__ == "__main__":
    unittest.main()

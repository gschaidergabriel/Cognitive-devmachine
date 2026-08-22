from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


class NativeRuntimeGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp_context = tempfile.TemporaryDirectory(prefix="mini-native-runtime-guards-")
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
    def command(cls, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(cls.binary), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

    def test_local_runner_gets_no_parent_secrets_and_empty_followup_is_quiet(self) -> None:
        entity = self.tmp / "guard-entity.db"
        source = self.tmp / "guard-source.db"
        profile = self.tmp / "guard-profile.json"
        model = self.tmp / "guard-model.gguf"
        runner = self.tmp / "guard-runner.py"
        marker = self.tmp / "guard-runner-invocations.txt"

        profile.write_text(
            json.dumps(
                {
                    "profile_id": "ci-runtime-guard",
                    "identity": {"task": "process bounded fixture evidence", "language": "en"},
                    "personality": {
                        "system_prompt": "Return fixture output only.",
                        "public_style": "plain",
                        "output_contract": {},
                    },
                    "inference": {
                        "kind": "local_exec",
                        "max_tokens": 32,
                        "temperature": 0.0,
                        "secret_names": ["CLAY_TEST_SECRET", "OPENAI_API_KEY", "MISTRAL_API_KEY"],
                    },
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        runner.write_text(
            "import json, os, pathlib, sys\n"
            "for name in ('CLAY_TEST_SECRET','OPENAI_API_KEY','MISTRAL_API_KEY'):\n"
            "    if os.environ.get(name): raise SystemExit(41)\n"
            "pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')\n"
            "with pathlib.Path(sys.argv[2]).open('a', encoding='utf-8') as fh: fh.write('run\\n')\n"
            "print(json.dumps({'fixture':'runtime-guard','longitudinal_self_report':{}}, sort_keys=True))\n",
            encoding="utf-8",
        )
        model.write_bytes(b"fixture-model-bytes\n")

        self.command("init", str(entity))
        self.command("source-init", str(source))
        self.command("source-add", str(source), "evidence", "event-1", '{"observed":"fixture"}')
        self.command("preset-apply", str(entity), str(profile))
        self.command("set-local-model", str(entity), str(model))
        runner_json = json.dumps(["python3", str(runner), "{{PROMPT_FILE}}", str(marker)])
        self.command("set-local-runner-json", str(entity), runner_json)

        parent_env = dict(os.environ)
        sentinels = {
            "CLAY_TEST_SECRET": "SENTINEL_CLAY_TEST_SECRET_0_7",
            "OPENAI_API_KEY": "SENTINEL_OPENAI_0_7",
            "MISTRAL_API_KEY": "SENTINEL_MISTRAL_0_7",
        }
        parent_env.update(sentinels)

        first = json.loads(self.command("run", str(entity), str(source), env=parent_env).stdout)
        self.assertTrue(first["ok"])
        self.assertFalse(first["quiet"])
        self.assertEqual(first["generation"], 1)
        self.assertEqual(first["source_count"], 1)
        self.assertEqual(first["inference_kind"], "local_exec")

        quiet = json.loads(self.command("run", str(entity), str(source), env=parent_env).stdout)
        self.assertTrue(quiet["ok"])
        self.assertTrue(quiet["quiet"])
        self.assertEqual(quiet["generation"], 1)
        self.assertEqual(quiet["source_count"], 0)
        self.assertNotIn("output_id", quiet)
        self.assertEqual(marker.read_text(encoding="utf-8").splitlines(), ["run"])

        with sqlite3.connect(entity) as db:
            self.assertEqual(db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM outputs").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM study_rows").fetchone()[0], 1)
            stored = db.execute("SELECT model_output FROM outputs").fetchone()[0]
            for value in sentinels.values():
                self.assertNotIn(value, stored)
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        with sqlite3.connect(source) as db:
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM mini_entity_events WHERE consumed_generation IS NULL").fetchone()[0],
                0,
            )
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")


if __name__ == "__main__":
    unittest.main()

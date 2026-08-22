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


class NativeLocalEnvIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp_context = tempfile.TemporaryDirectory(prefix="mini-native-env-isolation-")
        cls.tmp = Path(cls.tmp_context.name)
        cls.binary = cls.tmp / "mini_entity.clay"
        cls.receipt = cls.tmp / "build_receipt.json"
        subprocess.run(
            [
                sys.executable,
                str(HERE / "build_native_bound.py"),
                "--source",
                str(HERE / "mini_entity.c"),
                "--output",
                str(cls.binary),
                "--receipt",
                str(cls.receipt),
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
    def command(
        cls, *args: str, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(cls.binary), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

    def test_parent_secrets_do_not_reach_local_runner_and_empty_cycle_still_infers(self) -> None:
        entity = self.tmp / "entity.db"
        source = self.tmp / "source.db"
        profile = self.tmp / "neutral-profile.json"
        model = self.tmp / "model.gguf"
        runner = self.tmp / "runner.py"
        marker = self.tmp / "runner-invocations.txt"

        # Deliberately not clay-pipeline-profile/v2: current main correctly blocks that
        # schema until native canonical v2 parity exists. This fixture isolates only the
        # low-level local_exec environment boundary and normal empty-window semantics.
        profile.write_text(
            json.dumps(
                {
                    "profile_id": "ci-local-env-isolation",
                    "identity": {
                        "task": "process bounded fixture evidence",
                        "language": "en",
                    },
                    "personality": {
                        "system_prompt": "Return fixture output only.",
                        "output_contract": {
                            "longitudinal_self_report_field": "self_report"
                        },
                    },
                    "inference": {
                        "kind": "local_exec",
                        "max_tokens": 64,
                        "temperature": 0.0,
                        "secret_names": [],
                    },
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        runner.write_text(
            "import json, os, pathlib, sys\n"
            "names=('CLAY_TEST_SECRET','OPENAI_API_KEY','MISTRAL_API_KEY','TOGETHER_API_KEY')\n"
            "if any(os.environ.get(name) for name in names): raise SystemExit(41)\n"
            "pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')\n"
            "with pathlib.Path(sys.argv[2]).open('a', encoding='utf-8') as fh: fh.write('run\\n')\n"
            "print(json.dumps({'fixture':'local_exec','self_report':{}}, sort_keys=True))\n",
            encoding="utf-8",
        )
        model.write_bytes(b"fixture-model-bytes\n")

        self.command("init", str(entity))
        self.command("source-init", str(source))
        self.command(
            "source-add",
            str(source),
            "evidence",
            "event-1",
            '{"measurement_status":"MEASURED","observed":"fixture"}',
        )
        self.command("preset-apply", str(entity), str(profile))
        self.command("set-local-model", str(entity), str(model))
        self.command(
            "set-local-runner-json",
            str(entity),
            json.dumps(["python3", str(runner), "{{PROMPT_FILE}}", str(marker)]),
        )

        parent_env = dict(os.environ)
        sentinels = {
            "CLAY_TEST_SECRET": "SENTINEL_CLAY_TEST_SECRET_0_7",
            "OPENAI_API_KEY": "SENTINEL_OPENAI_0_7",
            "MISTRAL_API_KEY": "SENTINEL_MISTRAL_0_7",
            "TOGETHER_API_KEY": "SENTINEL_TOGETHER_0_7",
        }
        parent_env.update(sentinels)

        first = json.loads(
            self.command("run", str(entity), str(source), env=parent_env).stdout
        )
        self.assertTrue(first["ok"])
        self.assertEqual(first["generation"], 1)
        self.assertEqual(first["source_count"], 1)
        self.assertEqual(first["inference_kind"], "local_exec")

        second = json.loads(
            self.command("run", str(entity), str(source), env=parent_env).stdout
        )
        self.assertTrue(second["ok"])
        self.assertEqual(second["generation"], 2)
        self.assertEqual(second["source_count"], 0)
        self.assertEqual(second["inference_kind"], "local_exec")
        self.assertEqual(marker.read_text(encoding="utf-8").splitlines(), ["run", "run"])

        with sqlite3.connect(entity) as db:
            self.assertEqual(
                db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()[0],
                2,
            )
            self.assertEqual(db.execute("SELECT COUNT(*) FROM outputs").fetchone()[0], 2)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM study_rows").fetchone()[0], 2)
            for (stored,) in db.execute(
                "SELECT model_output FROM outputs ORDER BY generation"
            ):
                for value in sentinels.values():
                    self.assertNotIn(value, stored)
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")

        with sqlite3.connect(source) as db:
            self.assertEqual(
                db.execute(
                    "SELECT COUNT(*) FROM mini_entity_events WHERE consumed_generation IS NULL"
                ).fetchone()[0],
                0,
            )
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")


if __name__ == "__main__":
    unittest.main()

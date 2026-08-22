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


class NativeLocalExecEnvironmentIsolationTests(unittest.TestCase):
    def test_parent_secrets_do_not_reach_local_runner(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mini-native-local-env-") as td:
            tmp = Path(td)
            binary = tmp / "mini_entity.clay"
            receipt = tmp / "build_receipt.json"
            subprocess.run(
                [
                    sys.executable,
                    str(HERE / "build_native_bound.py"),
                    "--source",
                    str(HERE / "mini_entity.c"),
                    "--output",
                    str(binary),
                    "--receipt",
                    str(receipt),
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

            entity = tmp / "entity.db"
            source = tmp / "source.db"
            profile = tmp / "profile.json"
            model = tmp / "fixture.gguf"
            runner = tmp / "runner.py"
            seen_env = tmp / "seen-env.json"

            profile.write_text(
                json.dumps(
                    {
                        "schema": "clay-pipeline-profile/v1",
                        "profile_id": "local-env-isolation",
                        "personality": {"system_prompt": "Return bounded fixture output."},
                        "inference": {"kind": "local_exec", "max_tokens": 32, "temperature": 0.0},
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            runner.write_text(
                "import json, os, pathlib, sys\n"
                "bad=('CLAY_TEST_SECRET','OPENAI_API_KEY','MISTRAL_API_KEY','UNRELATED_PARENT_SECRET')\n"
                "if any(os.environ.get(k) for k in bad): raise SystemExit(41)\n"
                "pathlib.Path(sys.argv[1]).write_text(json.dumps(dict(os.environ), sort_keys=True), encoding='utf-8')\n"
                "print(json.dumps({'fixture':'ok'}, sort_keys=True))\n",
                encoding="utf-8",
            )
            model.write_bytes(b"fixture-model\n")

            def command(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [str(binary), *args],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                )

            command("init", str(entity))
            command("source-init", str(source))
            command("source-add", str(source), "evidence", "event-1", '{"observed":"fixture"}')
            command("preset-apply", str(entity), str(profile))
            command("set-local-model", str(entity), str(model))
            command(
                "set-local-runner-json",
                str(entity),
                json.dumps(["python3", str(runner), str(seen_env)]),
            )

            parent_env = dict(os.environ)
            sentinels = {
                "CLAY_TEST_SECRET": "SENTINEL_CLAY",
                "OPENAI_API_KEY": "SENTINEL_OPENAI",
                "MISTRAL_API_KEY": "SENTINEL_MISTRAL",
                "UNRELATED_PARENT_SECRET": "SENTINEL_UNRELATED",
            }
            parent_env.update(sentinels)

            result = json.loads(command("run", str(entity), str(source), env=parent_env).stdout)
            self.assertTrue(result["ok"])
            self.assertEqual(result["generation"], 1)
            self.assertEqual(result["source_count"], 1)
            self.assertEqual(result["inference_kind"], "local_exec")

            child_env = json.loads(seen_env.read_text(encoding="utf-8"))
            for key, value in sentinels.items():
                self.assertNotIn(key, child_env)
                self.assertNotIn(value, json.dumps(child_env, sort_keys=True))
            self.assertEqual(child_env.get("HOME"), "/tmp")
            self.assertEqual(child_env.get("TMPDIR"), "/tmp")
            self.assertEqual(child_env.get("TZ"), "UTC")
            self.assertTrue(child_env.get("PATH"))

            with sqlite3.connect(entity) as db:
                stored = db.execute("SELECT model_output FROM outputs WHERE generation=1").fetchone()[0]
                for value in sentinels.values():
                    self.assertNotIn(value, stored)
                self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")


if __name__ == "__main__":
    unittest.main()

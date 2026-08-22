from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("build_native_bound", HERE / "build_native_bound.py")
assert SPEC is not None and SPEC.loader is not None
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


class SourceClosureTests(unittest.TestCase):
    def test_include_mutation_changes_closure_without_changing_entry_hash(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entry = root / "mini_entity.c"
            include = root / "part.inc"
            entry.write_text('#include "part.inc"\nint main(void){return VALUE;}\n', encoding="utf-8")
            include.write_text("#define VALUE 0\n", encoding="utf-8")
            entry_hash = build.sha256_file(entry)
            before = build.source_closure(entry)
            include.write_text("#define VALUE 1\n", encoding="utf-8")
            after = build.source_closure(entry)
            self.assertEqual(entry_hash, build.sha256_file(entry))
            self.assertNotEqual(before["sha256"], after["sha256"])

    def test_dynamic_local_include_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entry = root / "mini_entity.c"
            (root / "part.inc").write_text("#define VALUE 0\n", encoding="utf-8")
            entry.write_text('#define PICK "part.inc"\n#include PICK\n', encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "DYNAMIC_OR_UNBOUND_INCLUDE"):
                build.source_closure(entry)

    def test_local_include_escape_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            parent = Path(td)
            root = parent / "native"
            root.mkdir()
            (parent / "outside.inc").write_text("#define X 1\n", encoding="utf-8")
            entry = root / "mini_entity.c"
            entry.write_text('#include "../outside.inc"\n', encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "LOCAL_INCLUDE_OUTSIDE_SOURCE_ROOT"):
                build.source_closure(entry)

    def test_current_native_source_closure_is_exactly_the_split_unit(self) -> None:
        closure = build.source_closure(HERE / "mini_entity.c")
        self.assertEqual(
            {item["path"] for item in closure["files"]},
            {
                "mini_entity.c",
                "mini_entity_part00.inc",
                "mini_entity_part01.inc",
                "mini_entity_part02.inc",
                "mini_entity_part03.inc",
                "mini_entity_part04.inc",
            },
        )
        self.assertEqual(len(closure["files"]), 6)


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

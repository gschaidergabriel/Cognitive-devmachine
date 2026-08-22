#!/usr/bin/env python3
"""Bounded executable acceptance harness for one source-built Mini Entity 0.7 ELF.

This is a runtime falsifier/receipt generator, not a second runtime implementation.
It uses only a local fixture runner: no provider token, network inference, model-quality
claim, or application-specific executable identity is introduced.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import tempfile
from pathlib import Path
from typing import Any


EXPECTED_VERSION = "mini-entity/0.7.0-dev1"


def run(argv: list[str], *, env: dict[str, str] | None = None, expect: int | None = 0) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    if expect is not None and proc.returncode != expect:
        raise AssertionError(
            "command rc={} expected={} argv={} stdout={!r} stderr={!r}".format(
                proc.returncode, expect, argv, proc.stdout, proc.stderr
            )
        )
    return proc


def query_one(db: Path, sql: str) -> Any:
    with sqlite3.connect(db) as conn:
        row = conn.execute(sql).fetchone()
    if row is None:
        raise AssertionError("query returned no row: " + sql)
    return row[0]


def snapshot(entity_db: Path, source_db: Path) -> dict[str, Any]:
    return {
        "generation": int(query_one(entity_db, "SELECT generation FROM entity_state WHERE id=1")),
        "outputs": int(query_one(entity_db, "SELECT COUNT(*) FROM outputs")),
        "study_rows": int(query_one(entity_db, "SELECT COUNT(*) FROM study_rows")),
        "pending_events": int(query_one(source_db, "SELECT COUNT(*) FROM mini_entity_events WHERE consumed_generation IS NULL")),
        "consumed_events": int(query_one(source_db, "SELECT COUNT(*) FROM mini_entity_events WHERE consumed_generation IS NOT NULL")),
        "entity_integrity": str(query_one(entity_db, "PRAGMA integrity_check")),
        "source_integrity": str(query_one(source_db, "PRAGMA integrity_check")),
    }


def assert_clean_failure(before: dict[str, Any], after: dict[str, Any]) -> None:
    for key in ("generation", "outputs", "study_rows", "pending_events", "consumed_events"):
        assert after[key] == before[key], (key, before, after)
    assert after["entity_integrity"] == "ok"
    assert after["source_integrity"] == "ok"


def write_fixture_runner(path: Path) -> None:
    path.write_text(
        """#!/usr/bin/env python3
import json, os, sqlite3, sys
mutate = os.environ.get('FIXTURE_MUTATE_ENTITY_DB')
if mutate:
    with sqlite3.connect(mutate) as conn:
        conn.execute('UPDATE entity_state SET generation=generation+7 WHERE id=1')
        conn.commit()
print(json.dumps({
    'ueberschrift': 'Fixture',
    'einleitung': 'source-bound local_exec acceptance fixture',
    'abschnitte': [],
    'qualia_probe': {'status': 'UNKNOWN', 'confidence': 0.0},
    'longitudinal_self_report': {'uncertainty': 0.25, 'qualia_clarity': 'UNKNOWN'},
}, sort_keys=True))
""",
        encoding="utf-8",
    )
    path.chmod(0o755)


def setup_case(binary: Path, root: Path, repo_root: Path, event_id: str) -> tuple[Path, Path, Path]:
    entity_db = root / "entity.db"
    source_db = root / "source.db"
    model_file = root / "fixture.model"
    runner = root / "fixture_runner.py"
    model_file.write_bytes(b"fixture-model-identity\n")
    write_fixture_runner(runner)

    preset = repo_root / "the artefact" / "blogpost_entity" / "presets" / "zero_blog.json"
    state_box = repo_root / "the artefact" / "blogpost_entity" / "presets" / "zero_blog_state_box.json"
    assert preset.is_file()
    assert state_box.is_file()

    run([str(binary), "init", str(entity_db)])
    neutral = json.loads(run([str(binary), "status", str(entity_db)]).stdout)
    assert neutral["version"] == EXPECTED_VERSION
    assert neutral["generation"] == 0
    assert neutral["active_profile"] is None
    assert neutral["profile_present"] is False

    run([str(binary), "source-init", str(source_db)])
    run([str(binary), "source-add", str(source_db), "fixture", event_id, json.dumps({"event": event_id})])
    run([str(binary), "preset-apply", str(entity_db), str(preset)])
    run([str(binary), "state-box-apply", str(entity_db), str(state_box)])
    run([str(binary), "set-local-model", str(entity_db), str(model_file)])
    runner_argv = json.dumps(["python3", str(runner), "{{MODEL_PATH}}", "{{PROMPT_FILE}}"])
    run([str(binary), "set-local-runner-json", str(entity_db), runner_argv])
    return entity_db, source_db, runner


def trigger(db: Path, sql: str) -> None:
    with sqlite3.connect(db) as conn:
        conn.executescript(sql)
        conn.commit()


def case_success(binary: Path, repo_root: Path, root: Path) -> dict[str, Any]:
    case = root / "success"
    case.mkdir()
    entity_db, source_db, _ = setup_case(binary, case, repo_root, "event-success")
    before = snapshot(entity_db, source_db)
    assert before["generation"] == 0 and before["pending_events"] == 1
    proc = run([str(binary), "run", str(entity_db), str(source_db)])
    result = json.loads(proc.stdout)
    after = snapshot(entity_db, source_db)
    assert result["ok"] is True
    assert result["generation"] == 1
    assert result["inference_kind"] == "local_exec"
    assert after["generation"] == 1
    assert after["outputs"] == 1
    assert after["study_rows"] == 1
    assert after["pending_events"] == 0
    assert after["consumed_events"] == 1
    assert after["entity_integrity"] == "ok" and after["source_integrity"] == "ok"
    box = str(query_one(entity_db, "SELECT box_text FROM study_rows LIMIT 1"))
    assert "SYSTEM STATE" in box and "MODEL SELF-REPORT" in box and "AUSWERTUNG" in box
    return {"before": before, "after": after, "run": result}


def case_output_rollback(binary: Path, repo_root: Path, root: Path) -> dict[str, Any]:
    case = root / "output-fault"
    case.mkdir()
    entity_db, source_db, _ = setup_case(binary, case, repo_root, "event-output")
    trigger(entity_db, "CREATE TRIGGER fail_outputs BEFORE INSERT ON outputs BEGIN SELECT RAISE(ABORT,'fault-output'); END;")
    before = snapshot(entity_db, source_db)
    proc = run([str(binary), "run", str(entity_db), str(source_db)], expect=None)
    assert proc.returncode != 0
    after = snapshot(entity_db, source_db)
    assert_clean_failure(before, after)
    return {"returncode": proc.returncode, "before": before, "after": after, "stderr": proc.stderr.strip()}


def case_study_rollback(binary: Path, repo_root: Path, root: Path) -> dict[str, Any]:
    case = root / "study-fault"
    case.mkdir()
    entity_db, source_db, _ = setup_case(binary, case, repo_root, "event-study")
    trigger(entity_db, "CREATE TRIGGER fail_study BEFORE INSERT ON study_rows BEGIN SELECT RAISE(ABORT,'fault-study'); END;")
    before = snapshot(entity_db, source_db)
    proc = run([str(binary), "run", str(entity_db), str(source_db)], expect=None)
    assert proc.returncode != 0
    after = snapshot(entity_db, source_db)
    assert_clean_failure(before, after)
    return {"returncode": proc.returncode, "before": before, "after": after, "stderr": proc.stderr.strip()}


def case_event_rollback(binary: Path, repo_root: Path, root: Path) -> dict[str, Any]:
    case = root / "event-fault"
    case.mkdir()
    entity_db, source_db, _ = setup_case(binary, case, repo_root, "event-consume")
    trigger(source_db, "CREATE TRIGGER fail_event BEFORE UPDATE OF consumed_generation ON mini_entity_events BEGIN SELECT RAISE(ABORT,'fault-event'); END;")
    before = snapshot(entity_db, source_db)
    proc = run([str(binary), "run", str(entity_db), str(source_db)], expect=None)
    assert proc.returncode != 0
    after = snapshot(entity_db, source_db)
    assert_clean_failure(before, after)
    return {"returncode": proc.returncode, "before": before, "after": after, "stderr": proc.stderr.strip()}


def case_generation_cas(binary: Path, repo_root: Path, root: Path) -> dict[str, Any]:
    case = root / "generation-cas"
    case.mkdir()
    entity_db, source_db, _ = setup_case(binary, case, repo_root, "event-cas")
    before = snapshot(entity_db, source_db)
    env = dict(os.environ)
    env["FIXTURE_MUTATE_ENTITY_DB"] = str(entity_db)
    proc = run([str(binary), "run", str(entity_db), str(source_db)], env=env, expect=None)
    assert proc.returncode != 0
    after = snapshot(entity_db, source_db)
    assert after["generation"] == before["generation"] + 7
    assert after["outputs"] == before["outputs"] == 0
    assert after["study_rows"] == before["study_rows"] == 0
    assert after["pending_events"] == before["pending_events"] == 1
    assert after["consumed_events"] == before["consumed_events"] == 0
    assert after["entity_integrity"] == "ok" and after["source_integrity"] == "ok"
    return {"returncode": proc.returncode, "before": before, "after": after, "stderr": proc.stderr.strip()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    binary = args.binary.resolve()
    if not binary.is_file():
        raise SystemExit("BINARY_MISSING:" + str(binary))
    version = run([str(binary), "--version"]).stdout.strip()
    if version != EXPECTED_VERSION:
        raise SystemExit(f"VERSION_MISMATCH:{version}")

    here = Path(__file__).resolve()
    repo_root = here.parents[3]
    with tempfile.TemporaryDirectory(prefix="mini-entity-07-acceptance-") as tmp:
        root = Path(tmp)
        cases = {
            "success": case_success(binary, repo_root, root),
            "output_insert_rollback": case_output_rollback(binary, repo_root, root),
            "study_insert_rollback": case_study_rollback(binary, repo_root, root),
            "event_consume_rollback": case_event_rollback(binary, repo_root, root),
            "generation_cas_rejection": case_generation_cas(binary, repo_root, root),
        }

    receipt = {
        "schema": "mini-entity-native-0.7-runtime-acceptance/v1",
        "version": version,
        "binary": str(binary),
        "inference": "local_exec fixture only",
        "network_provider_call": false,
        "provider_secret_used": false,
        "model_quality_claimed": false,
        "cases": cases,
        "acceptance_scope": "EXACT_ELF_FIXTURE_LOCAL_EXEC_AND_ATOMIC_ROLLBACK_MATRIX_ONLY",
        "pass": true,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

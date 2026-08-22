#!/usr/bin/env python3
from __future__ import annotations

import json
import shlex
import sqlite3
import subprocess
from pathlib import Path

import pytest


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "mini_entity.c"


def run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


@pytest.fixture(scope="session")
def native_binary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("native-semantic-gate") / "mini_entity.clay"
    flags = shlex.split(
        run(["pkg-config", "--cflags", "--libs", "sqlite3", "libcurl", "json-c"]).stdout.strip()
    )
    proc = run(
        [
            "gcc",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-Wno-deprecated-declarations",
            "-o",
            str(out),
            str(SOURCE),
            *flags,
        ]
    )
    assert proc.returncode == 0, proc.stderr
    return out


def write_runner(path: Path) -> None:
    path.write_text(
        r'''#!/usr/bin/env python3
import json,sys
case=sys.argv[1]
prompt=open(sys.argv[2],encoding="utf-8").read()
marker="NATIVE_GATE_CONTEXT_JSON="
ctx=json.loads([line for line in prompt.splitlines() if line.startswith(marker)][-1][len(marker):])
ref=ctx["allowed_evidence_refs"][0]
out={
  "canonical_state_hash_seen":ctx["canonical_state_hash"],
  "packet_hash_seen":ctx["packet_hash"],
  "title":"ok",
  "intro":"ok",
  "sections":[{"text":"evidence-backed","evidence_refs":[ref],"state_claims":{}}],
  "continuity":{},
  "hypotheses":[]
}
if case=="wrong_state": out["canonical_state_hash_seen"]="0"*64
elif case=="wrong_packet": out["packet_hash_seen"]="0"*64
elif case=="missing_field": out.pop("title")
elif case=="leak": out["sections"][0]["text"]="FORBIDDEN_TOKEN"
elif case=="no_evidence": out["sections"][0]["evidence_refs"]=[]
elif case=="unknown_ref": out["sections"][0]["evidence_refs"]=["not-offered"]
elif case=="state_claim": out["sections"][0]["state_claims"]={"metric":0.1}
print(json.dumps(out,separators=(",",":")))
''',
        encoding="utf-8",
    )
    path.chmod(0o755)


def profile(model: Path, runner: Path, case: str, *, gated: bool = True) -> dict:
    out = {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": "gate_fixture",
        "identity": {"task": "test", "language": "en"},
        "personality": {
            "system_prompt": "Use supplied evidence.",
            "public_style": "concise",
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
            "local_model_path": str(model),
            "local_argv_json": json.dumps(["python3", str(runner), case, "{{PROMPT_FILE}}"]),
            "temperature": 0.0,
            "max_tokens": 128,
        },
    }
    if gated:
        out["gate"] = {
            "require_hash_echo": True,
            "require_evidence_per_section": True,
            "max_claim_overshoot": 0.05,
            "leak_patterns": ["FORBIDDEN_TOKEN", "API_KEY"],
        }
    return out


def setup_case(native_binary: Path, tmp_path: Path, case: str, *, gated: bool = True):
    entity = tmp_path / "entity.db"
    source = tmp_path / "source.db"
    model = tmp_path / "dummy.gguf"
    runner = tmp_path / "runner.py"
    preset = tmp_path / "profile.json"
    model.write_bytes(b"dummy")
    write_runner(runner)
    preset.write_text(json.dumps(profile(model, runner, case, gated=gated)), encoding="utf-8")

    def cmd(*args: object) -> subprocess.CompletedProcess[str]:
        return run([str(native_binary), *map(str, args)])

    assert cmd("init", entity).returncode == 0
    assert cmd("source-init", source).returncode == 0
    source_id = "evt-" + case
    assert cmd("source-add", source, "event", source_id, json.dumps({"case": case})).returncode == 0
    assert cmd("preset-apply", entity, preset).returncode == 0
    return cmd, entity, source, source_id


def state(entity: Path, source: Path, source_id: str) -> tuple[int, int, int, int | None, str]:
    with sqlite3.connect(entity) as db:
        generation = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()[0]
        outputs = db.execute("SELECT COUNT(*) FROM outputs").fetchone()[0]
        studies = db.execute("SELECT COUNT(*) FROM study_rows").fetchone()[0]
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
    with sqlite3.connect(source) as db:
        consumed = db.execute(
            "SELECT consumed_generation FROM mini_entity_events WHERE source_id=?", (source_id,)
        ).fetchone()[0]
    return generation, outputs, studies, consumed, integrity


@pytest.mark.parametrize(
    ("case", "error"),
    [
        ("wrong_state", "GATE_CANONICAL_HASH_MISMATCH_NO_COMMIT"),
        ("wrong_packet", "GATE_PACKET_HASH_MISMATCH_NO_COMMIT"),
        ("missing_field", "GATE_REQUIRED_OUTPUT_FIELD_MISSING_NO_COMMIT"),
        ("leak", "GATE_LEAK_PATTERN_NO_COMMIT"),
        ("no_evidence", "GATE_SECTION_WITHOUT_EVIDENCE_NO_COMMIT"),
        ("unknown_ref", "GATE_UNKNOWN_EVIDENCE_REF_NO_COMMIT"),
        ("state_claim", "GATE_UNVERIFIED_STATE_CLAIM_NO_COMMIT"),
    ],
)
def test_gate_rejects_before_any_canonical_mutation(
    native_binary: Path, tmp_path: Path, case: str, error: str
) -> None:
    cmd, entity, source, source_id = setup_case(native_binary, tmp_path, case)
    result = cmd("run", entity, source)
    assert result.returncode == 2
    assert error in result.stderr
    assert state(entity, source, source_id) == (0, 0, 0, None, "ok")


def test_valid_gated_output_commits_once_and_quiet_turn_remains_evidence_bound(
    native_binary: Path, tmp_path: Path
) -> None:
    cmd, entity, source, source_id = setup_case(native_binary, tmp_path, "valid")
    first = cmd("run", entity, source)
    assert first.returncode == 0, first.stderr
    assert state(entity, source, source_id) == (1, 1, 1, 1, "ok")

    second = cmd("run", entity, source)
    assert second.returncode == 0, second.stderr
    assert state(entity, source, source_id) == (2, 2, 2, 1, "ok")
    assert json.loads(second.stdout)["source_count"] == 0


def test_profile_without_gate_keeps_legacy_local_exec_path(native_binary: Path, tmp_path: Path) -> None:
    cmd, entity, source, source_id = setup_case(native_binary, tmp_path, "valid", gated=False)
    result = cmd("run", entity, source)
    assert result.returncode == 0, result.stderr
    assert state(entity, source, source_id) == (1, 1, 1, 1, "ok")

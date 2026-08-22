from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
BUILDER_PATH = HERE / "build_native_bound.py"
CHECKER_PATH = HERE / "check_native_reference.py"
SOURCE_PATH = HERE / "mini_entity.c"

SPEC = importlib.util.spec_from_file_location("build_native_bound", BUILDER_PATH)
assert SPEC is not None and SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def test_current_source_closure_declares_exact_0_7_version():
    closure = builder.source_closure(SOURCE_PATH)
    assert len(closure["files"]) == 6
    assert builder.source_version_label(SOURCE_PATH, closure) == "mini-entity/0.7.0-dev1"


def test_build_refuses_historical_0_6_label_before_compilation(tmp_path: Path):
    proc = subprocess.run(
        [
            sys.executable,
            str(BUILDER_PATH),
            "--source",
            str(SOURCE_PATH),
            "--version-label",
            "mini-entity/0.6.0",
            "--source-date-epoch",
            "0",
            "--output",
            str(tmp_path / "should-not-exist.clay"),
            "--receipt",
            str(tmp_path / "should-not-exist.json"),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "VERSION_LABEL_SOURCE_MISMATCH" in proc.stderr
    assert "requested=mini-entity/0.6.0" in proc.stderr
    assert "source=mini-entity/0.7.0-dev1" in proc.stderr
    assert not (tmp_path / "should-not-exist.clay").exists()
    assert not (tmp_path / "should-not-exist.json").exists()


def test_historical_0_6_checker_rejects_current_0_7_source_lineage():
    proc = subprocess.run(
        [sys.executable, str(CHECKER_PATH), "--allow-missing-source"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    report = json.loads(proc.stdout)
    assert report["credited_version"] == "mini-entity/0.6.0"
    assert report["canonical_source"]["version"] == "mini-entity/0.7.0-dev1"
    assert report["canonical_source"]["lineage_matches_credited_version"] is False
    assert report["reproducibility"] == "BLOCKED_HISTORICAL_SOURCE_LINEAGE_MISMATCH"
    assert any("CREDITED_BINARY_SOURCE_VERSION_MISMATCH" in item for item in report["errors"])


def test_ambiguous_source_version_fails_closed(tmp_path: Path):
    entry = tmp_path / "mini_entity.c"
    part = tmp_path / "part.inc"
    entry.write_text('#define MINI_VERSION "mini-entity/a"\n#include "part.inc"\n', encoding="utf-8")
    part.write_text('#define MINI_VERSION "mini-entity/b"\n', encoding="utf-8")
    closure = builder.source_closure(entry)
    with pytest.raises(RuntimeError, match="SOURCE_VERSION_AMBIGUOUS"):
        builder.source_version_label(entry, closure)

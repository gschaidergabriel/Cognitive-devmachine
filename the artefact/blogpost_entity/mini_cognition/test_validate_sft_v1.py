#!/usr/bin/env python3
"""Exact-checkout ClayCog admission regression used by the bounded PR runner.

Despite the historical filename, this is the single focused admission entry point. It
keeps the v1 structural validator regression and makes v2 generation, structural
validation, diversity/leakage checks and deterministic corpus identity executable in
GitHub's exact PR checkout. It never calls Together and cannot start a billed job.
"""
import json
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED_TRAIN_SHA = "61a6cef129437f3a58f2b4563249f2dbb145705728e5c236c3f3fcf50403001f"
EXPECTED_VALIDATION_SHA = "79c2895572b66eb80d0c799cd2faa4891bca04bae34bd26aaf8a8e0fe47d2bfc"


def run(*args, capture=False):
    return subprocess.run(
        [sys.executable, *map(str, args)],
        cwd=HERE,
        check=True,
        text=True,
        capture_output=capture,
    )


def validator_unit_regression():
    """Prove the structural validator accepts a canonical row and rejects prose."""
    from validate_sft_v1 import PREFIX, validate_code

    valid = (
        PREFIX
        + '  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n'
        + '  role_bind(c,cfg("application.role"))\n'
        + '  goal_bind(c,cfg("application.goal"))\n'
        + '  personality_bind(c,cfg("application.personality"))\n'
        + '  return c\n}'
    )
    assert validate_code(valid) == [], validate_code(valid)
    invalid = valid + "\nnormal prose"
    assert validate_code(invalid), "validator accepted prose outside ClayCode"


def main():
    validator_unit_regression()

    # Syntax-compile the launcher without importing Together or requiring a secret.
    with tempfile.TemporaryDirectory() as tmp:
        py_compile.compile(str(HERE / "launch_together_v1.py"), cfile=str(Path(tmp) / "launcher.pyc"), doraise=True)

    # Generate the exact candidate data from this checkout, then validate every row.
    run(HERE / "generate_sft_v2.py")
    train = HERE / "train_v2.jsonl"
    validation = HERE / "validation_v2.jsonl"
    run(HERE / "validate_sft_v1.py", train)
    run(HERE / "validate_sft_v1.py", validation)
    quality_proc = run(HERE / "corpus_quality_gate_v2.py", train, validation, capture=True)
    quality = json.loads(quality_proc.stdout)
    assert quality["ok"] is True, quality
    assert quality["train"]["exact_unique_rate"] == 1.0, quality
    assert quality["validation"]["exact_unique_rate"] == 1.0, quality
    assert quality["exact_cross_split_overlap"] == 0, quality

    manifest = json.loads((HERE / "corpus_manifest_v2.json").read_text(encoding="utf-8"))
    assert manifest["examples"] == 2300, manifest
    assert manifest["train"] == 2000, manifest
    assert manifest["validation"] == 300, manifest
    assert set(manifest["train_operation_vocab"]).isdisjoint(manifest["validation_operation_vocab"]), manifest
    assert manifest["train_sha256"] == EXPECTED_TRAIN_SHA, manifest
    assert manifest["validation_sha256"] == EXPECTED_VALIDATION_SHA, manifest

    print(json.dumps({
        "schema": "claycog-pr-admission/v2",
        "status": "PASS",
        "train_rows": manifest["train"],
        "validation_rows": manifest["validation"],
        "train_sha256": manifest["train_sha256"],
        "validation_sha256": manifest["validation_sha256"],
        "train_exact_unique_rate": quality["train"]["exact_unique_rate"],
        "validation_exact_unique_rate": quality["validation"]["exact_unique_rate"],
        "exact_cross_split_overlap": quality["exact_cross_split_overlap"],
        "provider_call": False,
        "paid_job": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

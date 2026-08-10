#!/usr/bin/env python3
"""Cross-canonicalizer parity and parser-construction mutation tripwire for CC-WP-02.

This closes a gate blind spot: the standalone syntax canonicalizer and production frontend
were previously allowed to pass independently while using different Lark optional-placeholder
semantics. The baseline compares the standalone CLI's actual hashes against the same
canonicalizer fed by the production parser constructor. The single deliberate mutation
experiment then restores Lark's legacy maybe_placeholders=True behavior in memory and
requires the guard to detect the semantic-contract lesion.

Scope: parser/canonical syntax identity only. PASS is evidence for CC-WP-02 closure; it does
not promote WP02, change ClayCode language semantics, or authorize Frank Harness effects.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lark import Lark

import claycode_base_canonicalizer as canon
import claycode_base_frontend as front

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAMMAR = front.DEFAULT_GRAMMAR
DEFAULT_OUT = ROOT / "research_entity/claycode/base/receipts/LOCAL_WP02_CROSS_CANON_PARITY.json"
SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]
OPTIONAL_CASES = {
    "record_without_typeparams_or_defaults": "record X { a:Int }\n",
    "needle_without_params": "needle f()->Int\n",
    "record_without_field_defaults": "record X { a:Int; b:Ref }\n",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pkg(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _run_standalone_cli(grammar_path: Path, strict: bool) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="clay-wp02-parity-") as td:
        out = Path(td) / "standalone.json"
        argv = [
            sys.executable,
            str(ROOT / "tools/claycode_base_canonicalizer.py"),
            "--grammar",
            str(grammar_path),
            "--output",
            str(out),
        ]
        if not strict:
            argv.append("--relaxed-parser-for-test")
        cp = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, check=False, timeout=180)
        doc = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
        return {
            "argv": argv,
            "returncode": cp.returncode,
            "stdout_sha256": sha256_bytes(cp.stdout.encode()),
            "stderr_sha256": sha256_bytes(cp.stderr.encode()),
            "stderr_tail": cp.stderr[-2000:],
            "receipt": doc,
        }


def _expected_hashes(grammar_text: str, grammar_sha: str, strict: bool) -> dict[str, str]:
    parser = front.build_parser(grammar_text, strict=strict)
    rows: dict[str, str] = {}
    for path in SOURCES:
        source = path.read_text(encoding="utf-8")
        _, digest = canon.parse_canonical(parser, source, grammar_sha)
        rows[str(path.relative_to(ROOT))] = digest
    return rows


def _legacy_placeholder_mutation(grammar_text: str) -> dict[str, Any]:
    """Exactly one bounded out-of-box experiment: lesion/rescue parser contract in memory."""
    mutated = Lark(
        grammar_text,
        parser="lalr",
        lexer="contextual",
        strict=False,
        start="start",
        keep_all_tokens=True,
        maybe_placeholders=True,
    )
    rescued = front.build_parser(grammar_text, strict=False)
    rows = []
    detected_all = True
    rescue_all = True
    for name, source in OPTIONAL_CASES.items():
        mtree = mutated.parse(source)
        rtree = rescued.parse(source)
        mutated_none = canon.count_none_children(mtree)
        rescued_none = canon.count_none_children(rtree)
        mutation_rejected = False
        mutation_error = None
        try:
            canon.canonical_node(mtree)
        except canon.CanonicalizationError as exc:
            mutation_rejected = True
            mutation_error = str(exc)
        rescue_ok = rescued_none == 0
        detected = mutated_none > 0 and mutation_rejected
        detected_all = detected_all and detected
        rescue_all = rescue_all and rescue_ok
        rows.append({
            "case": name,
            "mutated_none_placeholders": mutated_none,
            "mutation_rejected": mutation_rejected,
            "mutation_error": mutation_error,
            "mutation_detected": detected,
            "rescued_none_placeholders": rescued_none,
            "rescue_pass": rescue_ok,
        })
    return {
        "name": "IN_MEMORY_OPTIONAL_PLACEHOLDER_CONTRACT_LESION_RESCUE",
        "class": "EXACTLY_ONE_OUT_OF_BOX_EXPERIMENT",
        "mutation": "maybe_placeholders=True",
        "rescue": "claycode_base_frontend.build_parser(maybe_placeholders=False)",
        "rows": rows,
        "mutation_detected_all": detected_all,
        "rescue_pass_all": rescue_all,
        "pass": detected_all and rescue_all,
        "promotion": "NONE",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grammar", type=Path, default=DEFAULT_GRAMMAR)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    grammar_path = args.grammar
    if not grammar_path.is_absolute():
        grammar_path = ROOT / grammar_path
    grammar_text = grammar_path.read_text(encoding="utf-8")
    grammar_sha = sha256_bytes(grammar_text.encode("utf-8"))

    cli = _run_standalone_cli(grammar_path, strict=args.strict)
    cli_doc = cli.get("receipt") if isinstance(cli.get("receipt"), dict) else {}
    expected = _expected_hashes(grammar_text, grammar_sha, strict=args.strict)
    observed = {
        str(row.get("path")): str(row.get("canonical_syntax_sha256"))
        for row in cli_doc.get("sources", [])
        if isinstance(row, dict) and row.get("path") and row.get("canonical_syntax_sha256")
    }
    source_rows = []
    for path, exp in expected.items():
        got = observed.get(path)
        source_rows.append({"path": path, "expected_hash": exp, "cli_hash": got, "pass": got == exp})

    runtime = cli_doc.get("runtime") if isinstance(cli_doc.get("runtime"), dict) else {}
    optional_rows = cli_doc.get("optional_placeholder_absence") if isinstance(cli_doc.get("optional_placeholder_absence"), list) else []
    parser_contract_bound = (
        cli.get("returncode") == 0
        and cli_doc.get("pass") is True
        and runtime.get("production_parser_constructor") == "claycode_base_frontend.build_parser"
        and runtime.get("maybe_placeholders") is False
        and cli_doc.get("optional_placeholder_absence_guard_present") is True
        and bool(optional_rows)
        and all(isinstance(x, dict) and x.get("pass") is True for x in optional_rows)
        and all(row["pass"] for row in source_rows)
    )

    mutation = _legacy_placeholder_mutation(grammar_text)
    passed = parser_contract_bound and mutation.get("pass") is True
    report = {
        "schema_version": "1.0",
        "experiment": "CC-WP-02 cross-canonicalizer parser-contract parity",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "grammar_path": str(grammar_path.relative_to(ROOT)) if grammar_path.is_relative_to(ROOT) else str(grammar_path),
        "grammar_sha256": grammar_sha,
        "runtime": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "lark": pkg("lark"),
            "interegular": pkg("interegular"),
            "strict": args.strict,
        },
        "standalone_cli": {k: v for k, v in cli.items() if k != "receipt"},
        "source_hash_parity": source_rows,
        "optional_placeholder_absence": optional_rows,
        "parser_contract_bound": parser_contract_bound,
        "out_of_box_experiment": mutation,
        "pass": passed,
        "architecture_delta": "TEST_GATE_REPAIR_ONLY; no ClayCode language semantic change",
        "counterhypothesis": "Independent standalone and production canonicalizer tests are sufficient without direct parity coupling.",
        "counterhypothesis_status": "REFUTED_IF_PASS",
        "scope_guard": "PASS closes only the cross-canonicalizer parser-construction blind spot on tested selected grammar bytes. WP02 promotion still requires its declared Ubuntu target and all contract gates.",
        "authority_invariant": "model output != execution authority",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": passed, "parser_contract_bound": parser_contract_bound, "mutation_pass": mutation.get("pass"), "output": str(args.output)}))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())

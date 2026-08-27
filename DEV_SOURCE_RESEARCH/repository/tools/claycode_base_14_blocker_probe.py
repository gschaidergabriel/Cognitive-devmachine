#!/usr/bin/env python3
"""Evidence-first audit for the 14 ClayCode BASE work packages.

This probe deliberately does not promote any BASE package. It inventories executable
artifacts and runs safe local checks on the Ubuntu CI runner so later promotion can be
based on receipts rather than filenames or research prose.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import py_compile
import subprocess
import sys
import time
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "research_entity/claycode/autonomous/BASE_14_BLOCKER_AUDIT.json"

WP = {
    "CC-WP-01-SPEC-FREEZE": ["spec", "freeze", "grammar", "semantic", "contract"],
    "CC-WP-02-PARSER-CANON": ["parser", "grammar", "canon"],
    "CC-WP-03-IR-TYPES": ["ir", "type", "semantic_identity"],
    "CC-WP-04-TYPE-EFFECT": ["type", "effect", "validator"],
    "CC-WP-05-EVALUATOR": ["eval", "interpreter", "evaluator"],
    "CC-WP-06-COMPILER-LOWERING": ["lower", "compiler", "backend", "wasm", "llvm", "native"],
    "CC-WP-07-RUNTIME-ABI-FFI": ["runtime", "abi", "ffi", "resource_identity", "capability"],
    "CC-WP-08-STDLIB-SDK": ["stdlib", "sdk", "http", "sqlite", "file", "process"],
    "CC-WP-09-CONCURRENCY-MEMORY": ["async", "concurr", "atomic", "cas", "aba", "memory", "lifetime"],
    "CC-WP-10-GENERAL-APP-SUITE": ["app", "http", "sqlite", "gui", "gpu", "frank", "cli"],
    "CC-WP-11-FUZZ-CONFORMANCE": ["fuzz", "property", "mutation", "roundtrip", "differential", "conformance"],
    "CC-WP-12-CORPUS-HELDOUT": ["corpus", "heldout", "dataset", "generator", "eval"],
    "CC-WP-13-HARNESS-HANDOFF": ["harness", "handoff", "frank", "golden", "differential"],
    "CC-WP-14-BASE-AUDIT": ["manifest", "audit", "release", "receipt"],
}

TEXT_EXTS = {".py", ".json", ".md", ".txt", ".clay", ".lark", ".ebnf", ".yaml", ".yml", ".toml"}
SCAN_ROOTS = [ROOT / "research_entity/claycode", ROOT / "tools", ROOT / "tests"]


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str], timeout: int = 120) -> dict[str, Any]:
    started = time.time()
    try:
        cp = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
        return {
            "cmd": cmd,
            "returncode": cp.returncode,
            "stdout_tail": cp.stdout[-12000:],
            "stderr_tail": cp.stderr[-12000:],
            "duration_s": round(time.time() - started, 3),
        }
    except Exception as e:  # pragma: no cover - diagnostic path
        return {"cmd": cmd, "error": repr(e), "duration_s": round(time.time() - started, 3)}


def all_files() -> list[pathlib.Path]:
    out: list[pathlib.Path] = []
    for base in SCAN_ROOTS:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and ".git" not in p.parts:
                out.append(p)
    return sorted(out)


def searchable_blob(path: pathlib.Path) -> str:
    rel = str(path.relative_to(ROOT)).lower()
    if path.suffix.lower() not in TEXT_EXTS or path.stat().st_size > 2_000_000:
        return rel
    try:
        return rel + "\n" + path.read_text(encoding="utf-8", errors="replace").lower()
    except OSError:
        return rel


def evidence_index(files: list[pathlib.Path]) -> dict[str, Any]:
    blobs = [(p, searchable_blob(p)) for p in files]
    result: dict[str, Any] = {}
    for wp, terms in WP.items():
        hits = []
        for p, blob in blobs:
            matched = sorted({t for t in terms if t in blob})
            if matched:
                hits.append({
                    "path": str(p.relative_to(ROOT)),
                    "matched_terms": matched,
                    "size": p.stat().st_size,
                })
        hits.sort(key=lambda x: (-len(x["matched_terms"]), x["path"]))
        result[wp] = {"evidence_candidates": hits[:80], "candidate_count": len(hits)}
    return result


def python_compile_check(files: list[pathlib.Path]) -> dict[str, Any]:
    targets = [p for p in files if p.suffix == ".py" and ("claycode" in p.name.lower() or "claycode" in str(p.parent).lower())]
    failures = []
    for p in targets:
        try:
            py_compile.compile(str(p), doraise=True)
        except Exception as e:
            failures.append({"path": str(p.relative_to(ROOT)), "error": repr(e)})
    return {"targets": len(targets), "failures": failures, "pass": not failures}


def strict_lalr_check() -> dict[str, Any]:
    grammar = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V4.lark"
    if not grammar.exists():
        return {"pass": False, "reason": "grammar_missing", "path": str(grammar.relative_to(ROOT))}
    try:
        from lark import Lark  # type: ignore
        text = grammar.read_text(encoding="utf-8")
        Lark(text, parser="lalr", strict=True)
        return {"pass": True, "path": str(grammar.relative_to(ROOT)), "sha256": sha256(grammar)}
    except Exception as e:
        return {"pass": False, "path": str(grammar.relative_to(ROOT)), "error": repr(e), "sha256": sha256(grammar)}


def json_receipts(files: list[pathlib.Path]) -> list[dict[str, Any]]:
    receipts = []
    for p in files:
        n = p.name.lower()
        if p.suffix.lower() != ".json" or not any(k in n for k in ("receipt", "manifest", "audit", "result")):
            continue
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        summary = {}
        if isinstance(obj, dict):
            for k in ("status", "result", "pass", "passed", "strict_build_ok", "gate", "gate_status", "mismatches", "failures"):
                if k in obj:
                    summary[k] = obj[k]
        receipts.append({"path": str(p.relative_to(ROOT)), "sha256": sha256(p), "summary": summary})
    return receipts[:500]


def discover_tests(files: list[pathlib.Path]) -> list[str]:
    return [str(p.relative_to(ROOT)) for p in files if p.suffix == ".py" and (p.name.startswith("test_") or p.name.endswith("_test.py"))][:500]


def main() -> int:
    files = all_files()
    report: dict[str, Any] = {
        "schema_version": "1.0",
        "probe": "claycode_base_14_blocker_probe",
        "generated_at_unix": int(time.time()),
        "runner": {
            "platform": sys.platform,
            "python": sys.version,
            "github_sha": os.environ.get("GITHUB_SHA"),
            "github_ref": os.environ.get("GITHUB_REF"),
            "runner_os": os.environ.get("RUNNER_OS"),
            "runner_arch": os.environ.get("RUNNER_ARCH"),
        },
        "policy": {
            "promotion": "FORBIDDEN_BY_THIS_PROBE",
            "meaning": "Evidence candidates are not PASS. Only executable receipts matching the acceptance contract may close a work package.",
        },
        "inventory": {
            "scanned_file_count": len(files),
            "claycode_file_count": sum(1 for p in files if "research_entity/claycode" in str(p)),
            "test_files": discover_tests(files),
        },
        "checks": {
            "python_compile": python_compile_check(files),
            "strict_lalr_v4": strict_lalr_check(),
        },
        "work_packages": evidence_index(files),
        "json_receipts": json_receipts(files),
    }

    manifest = ROOT / "research_entity/claycode/CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json"
    report["release_manifest"] = {
        "exists": manifest.exists(),
        "path": str(manifest.relative_to(ROOT)),
        "sha256": sha256(manifest) if manifest.exists() else None,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(OUT.relative_to(ROOT)),
        "files": len(files),
        "python_compile_pass": report["checks"]["python_compile"]["pass"],
        "strict_lalr_v4_pass": report["checks"]["strict_lalr_v4"]["pass"],
        "release_manifest_exists": report["release_manifest"]["exists"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

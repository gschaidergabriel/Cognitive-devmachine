#!/usr/bin/env python3
"""One-command fail-closed CC-WP-02 V9 strict closure runner for a local Ubuntu executor.

This runner exists because GitHub-hosted Actions currently fails before Step 1 in this
repository. It does not replace physical Andreas target acceptance. It only assembles the
strict parser/canonical/declarative-IR evidence that can safely be proven on a local Ubuntu
host with Lark + interegular installed.

PASS means all component receipts are present, successful, and bound to the exact same
V9 grammar bytes. It never means ClayCode BASE, WP10, WP13 or WP14 PASS.
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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR_REL = "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V9.lark"
GRAMMAR = ROOT / GRAMMAR_REL
RECEIPT_DIR = ROOT / "research_entity/claycode/base/receipts"
DEFAULT_OUTPUT = RECEIPT_DIR / "LOCAL_V9_STRICT_CLOSURE.json"

COMPONENTS = [
    (
        "strict_lalr",
        ["tools/claycode_strict_lalr_probe.py", "--grammar", GRAMMAR_REL, "--output", "research_entity/claycode/base/receipts/LOCAL_STRICT_LALR_D_V9.json"],
        RECEIPT_DIR / "LOCAL_STRICT_LALR_D_V9.json",
    ),
    (
        "frontend",
        ["tools/claycode_base_frontend_validation.py", "--grammar", GRAMMAR_REL, "--output", "research_entity/claycode/base/receipts/LOCAL_FRONTEND_V9_STRICT.json"],
        RECEIPT_DIR / "LOCAL_FRONTEND_V9_STRICT.json",
    ),
    (
        "canonical_syntax",
        ["tools/claycode_base_canonicalizer.py", "--grammar", GRAMMAR_REL, "--output", "research_entity/claycode/base/receipts/LOCAL_CANONICAL_V9_STRICT.json"],
        RECEIPT_DIR / "LOCAL_CANONICAL_V9_STRICT.json",
    ),
    (
        "typed_decl_g9",
        ["tools/claycode_base_ir.py", "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay", "--grammar", GRAMMAR_REL, "--output", "research_entity/claycode/base/receipts/LOCAL_IR_G9_V3_V9_STRICT.json"],
        RECEIPT_DIR / "LOCAL_IR_G9_V3_V9_STRICT.json",
    ),
    (
        "typed_decl_dialect",
        ["tools/claycode_base_ir.py", "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay", "--grammar", GRAMMAR_REL, "--output", "research_entity/claycode/base/receipts/LOCAL_IR_DIALECT_V3_V9_STRICT.json"],
        RECEIPT_DIR / "LOCAL_IR_DIALECT_V3_V9_STRICT.json",
    ),
    (
        "typed_decl_selftest",
        ["tools/claycode_base_ir.py", "--self-test", "--grammar", GRAMMAR_REL, "--output", "research_entity/claycode/base/receipts/LOCAL_IR_SELFTEST_V9_STRICT.json"],
        RECEIPT_DIR / "LOCAL_IR_SELFTEST_V9_STRICT.json",
    ),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_NOT_OBJECT:{path}")
    return value


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def ubuntu_id() -> str | None:
    p = Path("/etc/os-release")
    if not p.exists():
        return None
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("ID="):
            return line.split("=", 1)[1].strip().strip('"').lower()
    return None


def git_text(*args: str) -> tuple[int, str, str]:
    cp = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return cp.returncode, cp.stdout.strip(), cp.stderr.strip()


def run_component(name: str, argv: list[str], receipt: Path, expected_grammar_sha: str) -> dict[str, Any]:
    if receipt.exists():
        receipt.unlink()
    cp = subprocess.run([sys.executable, *argv], cwd=ROOT, text=True, capture_output=True, check=False, timeout=300)
    row: dict[str, Any] = {
        "name": name,
        "argv": [sys.executable, *argv],
        "returncode": cp.returncode,
        "process_pass": cp.returncode == 0,
        "stdout_sha256": hashlib.sha256(cp.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(cp.stderr.encode()).hexdigest(),
        "stdout_tail": cp.stdout[-4000:],
        "stderr_tail": cp.stderr[-4000:],
        "receipt_path": str(receipt.relative_to(ROOT)),
        "receipt_exists": receipt.exists(),
    }
    if not receipt.exists():
        row["semantic_pass"] = False
        row["failure"] = "RECEIPT_MISSING"
        return row
    try:
        doc = read_json(receipt)
    except Exception as exc:
        row["semantic_pass"] = False
        row["failure"] = f"RECEIPT_INVALID:{type(exc).__name__}:{exc}"
        return row
    row["receipt_sha256"] = sha256(receipt)

    grammar_path = doc.get("grammar_path")
    grammar_sha = doc.get("grammar_sha256")
    ident = doc.get("identity") if isinstance(doc.get("identity"), dict) else {}
    if not grammar_sha:
        grammar_sha = ident.get("grammar_sha256")
    if not grammar_path and name.startswith("typed_decl"):
        # Typed declaration IR records the exact grammar hash in identity. The path is
        # supplied by this runner's argv and bound again in the aggregate receipt.
        grammar_path = GRAMMAR_REL

    if name == "strict_lalr":
        semantic = (
            doc.get("strict_build_ok") is True
            and not doc.get("conflict_diagnostics")
            and grammar_path == GRAMMAR_REL
            and grammar_sha == expected_grammar_sha
        )
    elif name == "frontend":
        semantic = doc.get("pass") is True and grammar_path == GRAMMAR_REL and grammar_sha == expected_grammar_sha
    elif name == "canonical_syntax":
        semantic = doc.get("pass") is True and grammar_path == GRAMMAR_REL and grammar_sha == expected_grammar_sha
    elif name == "typed_decl_selftest":
        semantic = doc.get("pass") is True and grammar_sha == expected_grammar_sha
    else:
        semantic = bool(doc.get("declarations")) and grammar_sha == expected_grammar_sha

    row.update(
        {
            "embedded_grammar_path": grammar_path,
            "embedded_grammar_sha256": grammar_sha,
            "grammar_bound": grammar_sha == expected_grammar_sha and grammar_path == GRAMMAR_REL,
            "semantic_pass": bool(semantic),
        }
    )
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument(
        "--allow-ci",
        action="store_true",
        help="Diagnostic escape hatch only. The default local evidence contract rejects CI environments.",
    )
    args = ap.parse_args()

    preconditions: dict[str, Any] = {
        "linux": platform.system() == "Linux",
        "ubuntu": ubuntu_id() == "ubuntu",
        "grammar_exists": GRAMMAR.exists(),
        "not_github_actions": args.allow_ci or os.getenv("GITHUB_ACTIONS", "").lower() != "true",
        "not_generic_ci": args.allow_ci or os.getenv("CI", "").lower() not in {"1", "true", "yes"},
        "lark_installed": package_version("lark") is not None,
        "interegular_installed": package_version("interegular") is not None,
    }

    # Import explicitly: package metadata without a working import must not count.
    try:
        import interegular  # noqa: F401
        preconditions["interegular_importable"] = True
    except Exception as exc:
        preconditions["interegular_importable"] = False
        preconditions["interegular_import_error"] = f"{type(exc).__name__}: {exc}"

    rc, head, git_err = git_text("rev-parse", "HEAD")
    preconditions["git_head_readable"] = rc == 0 and bool(head)
    rc_status, porcelain, status_err = git_text("status", "--porcelain")
    preconditions["git_status_readable"] = rc_status == 0

    expected_sha = sha256(GRAMMAR) if GRAMMAR.exists() else None
    base = {
        "schema_version": "1.0",
        "receipt_id": "LOCAL_V9_STRICT_CLOSURE",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "LOCAL_UBUNTU_STRICT_PARSER_CANONICAL_DECL_IR",
        "host": {
            "node": platform.node(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "os_id": ubuntu_id(),
        },
        "packages": {"lark": package_version("lark"), "interegular": package_version("interegular")},
        "repository": {
            "head": head if rc == 0 else None,
            "head_error": git_err or None,
            "dirty": bool(porcelain) if rc_status == 0 else None,
            "status_error": status_err or None,
        },
        "grammar": {"path": GRAMMAR_REL, "sha256": expected_sha},
        "preconditions": preconditions,
        "authority_invariant": "model output != execution authority",
        "scope_guard": "PASS closes only the local strict V9 parser/canonical/declarative-IR evidence bundle. It is not physical Andreas target, application, FULL_FRANK, WP14 or BASE release acceptance.",
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not all(v is True for k, v in preconditions.items() if k != "interegular_import_error"):
        base.update({"components": [], "pass": False, "failure": "PRECONDITION_FAILED"})
        args.output.write_text(json.dumps(base, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"pass": False, "failure": "PRECONDITION_FAILED", "preconditions": preconditions}, ensure_ascii=False))
        return 3

    components = [run_component(name, argv, receipt, str(expected_sha)) for name, argv, receipt in COMPONENTS]

    # Validate the production frontend's own canonicalizer default after the explicit V9
    # components. This catches a future default-path regression even when callers pass V9.
    production_cp = subprocess.run(
        [sys.executable, "tools/claycode_base_canonicalizer_validation.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    prod_receipt = ROOT / "research_entity/claycode/autonomous/BASE_CANONICALIZER_RECEIPT.json"
    prod_doc = read_json(prod_receipt) if prod_receipt.exists() else {}
    production_default = {
        "returncode": production_cp.returncode,
        "process_pass": production_cp.returncode == 0,
        "receipt_exists": prod_receipt.exists(),
        "receipt_sha256": sha256(prod_receipt) if prod_receipt.exists() else None,
        "pass": production_cp.returncode == 0 and prod_doc.get("pass") is True and prod_doc.get("grammar") == GRAMMAR_REL,
        "grammar": prod_doc.get("grammar"),
        "stdout_tail": production_cp.stdout[-2000:],
        "stderr_tail": production_cp.stderr[-2000:],
    }

    passed = all(x.get("process_pass") is True and x.get("semantic_pass") is True for x in components) and production_default["pass"] is True
    base.update({"components": components, "production_default_canonicalizer": production_default, "pass": passed})
    if not passed:
        base["failure"] = "STRICT_V9_COMPONENT_FAILED"
    args.output.write_text(json.dumps(base, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": passed, "output": str(args.output.relative_to(ROOT)), "grammar_sha256": expected_sha, "failed": [x["name"] for x in components if not x.get("semantic_pass")]}, ensure_ascii=False))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())

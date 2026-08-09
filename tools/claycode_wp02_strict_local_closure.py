#!/usr/bin/env python3
"""One-command fail-closed local Ubuntu closure for the selected CC-WP-02 grammar.

The selected declarative grammar and target receipt paths come exclusively from
ANDREAS_UBUNTU_TARGET_RECEIPT_CONTRACT.json. This prevents local strict evidence,
physical target collection and strict target adjudication from silently validating
different parser contracts.

PASS here proves only local Ubuntu strict parser/full-corpus/canonical/declaration-IR
closure for the selected grammar. It never substitutes for the physical Andreas target,
ten-application, FULL_FRANK or WP14 receipts.
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
CONTRACT = ROOT / "research_entity/claycode/base/ANDREAS_UBUNTU_TARGET_RECEIPT_CONTRACT.json"
RECEIPT_DIR = ROOT / "research_entity/claycode/base/receipts"
DEFAULT_OUTPUT = RECEIPT_DIR / "LOCAL_WP02_SELECTED_GRAMMAR_CLOSURE.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_NOT_OBJECT:{path}")
    return value


def version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def os_id() -> str | None:
    path = Path("/etc/os-release")
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("ID="):
            return line.split("=", 1)[1].strip().strip('"').lower()
    return None


def git(*args: str) -> tuple[int, str, str]:
    cp = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return cp.returncode, cp.stdout.strip(), cp.stderr.strip()


def run(argv: list[str], *, timeout: int = 300) -> dict[str, Any]:
    cp = subprocess.run([sys.executable, *argv], cwd=ROOT, text=True, capture_output=True, check=False, timeout=timeout)
    return {
        "argv": [sys.executable, *argv],
        "returncode": cp.returncode,
        "process_pass": cp.returncode == 0,
        "stdout_sha256": hashlib.sha256(cp.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(cp.stderr.encode()).hexdigest(),
        "stdout_tail": cp.stdout[-4000:],
        "stderr_tail": cp.stderr[-4000:],
    }


def receipt_grammar(doc: dict[str, Any], *, inferred_path: str | None = None) -> tuple[str | None, str | None]:
    path = doc.get("grammar_path") or doc.get("grammar") or inferred_path
    grammar_sha = doc.get("grammar_sha256")
    ident = doc.get("identity") if isinstance(doc.get("identity"), dict) else {}
    grammar_sha = grammar_sha or ident.get("grammar_sha256")
    return (str(path) if path else None, str(grammar_sha) if grammar_sha else None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--allow-ci", action="store_true")
    args = ap.parse_args()

    contract = load(CONTRACT)
    wp02 = contract.get("wp02_parser_contract") if isinstance(contract.get("wp02_parser_contract"), dict) else {}
    grammar_rel = str(wp02.get("selected_grammar_path") or "")
    grammar = ROOT / grammar_rel if grammar_rel else ROOT / "__MISSING_SELECTED_GRAMMAR__"
    expected_sha = sha(grammar) if grammar.exists() else None

    preconditions: dict[str, Any] = {
        "contract_exists": CONTRACT.exists(),
        "selected_grammar_declared": bool(grammar_rel),
        "selected_grammar_exists": grammar.exists(),
        "linux": platform.system() == "Linux",
        "ubuntu": os_id() == "ubuntu",
        "not_github_actions": args.allow_ci or os.getenv("GITHUB_ACTIONS", "").lower() != "true",
        "not_generic_ci": args.allow_ci or os.getenv("CI", "").lower() not in {"1", "true", "yes"},
        "lark_installed": version("lark") is not None,
        "interegular_installed": version("interegular") is not None,
    }
    try:
        import interegular  # noqa: F401
        preconditions["interegular_importable"] = True
    except Exception as exc:
        preconditions["interegular_importable"] = False
        preconditions["interegular_import_error"] = f"{type(exc).__name__}: {exc}"

    rc, head, head_err = git("rev-parse", "HEAD")
    rc_status, porcelain, status_err = git("status", "--porcelain")
    preconditions["git_head_readable"] = rc == 0 and bool(head)
    preconditions["git_status_readable"] = rc_status == 0

    base: dict[str, Any] = {
        "schema_version": "1.0",
        "receipt_id": "LOCAL_WP02_SELECTED_GRAMMAR_CLOSURE",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "LOCAL_UBUNTU_STRICT_SELECTED_WP02",
        "contract": {"path": str(CONTRACT.relative_to(ROOT)), "sha256": sha(CONTRACT)},
        "selected_grammar": {"path": grammar_rel or None, "sha256": expected_sha},
        "host": {"node": platform.node(), "platform": platform.platform(), "machine": platform.machine(), "python": platform.python_version(), "os_id": os_id()},
        "packages": {"lark": version("lark"), "interegular": version("interegular")},
        "repository": {"head": head if rc == 0 else None, "head_error": head_err or None, "dirty": bool(porcelain) if rc_status == 0 else None, "status_error": status_err or None},
        "preconditions": preconditions,
        "components": [],
        "authority_invariant": "model output != execution authority",
        "scope_guard": "PASS is local selected-WP02 strict evidence only; physical target/application/FULL_FRANK/WP14 gates remain mandatory.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    bool_preconditions = [v for k, v in preconditions.items() if k != "interegular_import_error"]
    if not all(v is True for v in bool_preconditions):
        base.update({"pass": False, "failure": "PRECONDITION_FAILED"})
        args.output.write_text(json.dumps(base, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"pass": False, "failure": "PRECONDITION_FAILED", "preconditions": preconditions}, ensure_ascii=False))
        return 3

    component_specs: list[tuple[str, list[str], Path, str]] = [
        ("strict_lalr", ["tools/claycode_strict_lalr_probe.py", "--grammar", grammar_rel, "--output", "research_entity/claycode/base/receipts/LOCAL_WP02_STRICT_LALR.json"], RECEIPT_DIR / "LOCAL_WP02_STRICT_LALR.json", "strict"),
        ("frontend", ["tools/claycode_base_frontend_validation.py", "--grammar", grammar_rel, "--output", "research_entity/claycode/base/receipts/LOCAL_WP02_FRONTEND.json"], RECEIPT_DIR / "LOCAL_WP02_FRONTEND.json", "pass"),
        ("canonical", ["tools/claycode_base_canonicalizer.py", "--grammar", grammar_rel, "--output", "research_entity/claycode/base/receipts/LOCAL_WP02_CANONICAL.json"], RECEIPT_DIR / "LOCAL_WP02_CANONICAL.json", "pass"),
        ("decl_ir_g9", ["tools/claycode_base_ir.py", "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay", "--grammar", grammar_rel, "--output", "research_entity/claycode/base/receipts/LOCAL_WP02_IR_G9.json"], RECEIPT_DIR / "LOCAL_WP02_IR_G9.json", "decl"),
        ("decl_ir_dialect", ["tools/claycode_base_ir.py", "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay", "--grammar", grammar_rel, "--output", "research_entity/claycode/base/receipts/LOCAL_WP02_IR_DIALECT.json"], RECEIPT_DIR / "LOCAL_WP02_IR_DIALECT.json", "decl"),
        ("decl_ir_selftest", ["tools/claycode_base_ir.py", "--self-test", "--grammar", grammar_rel, "--output", "research_entity/claycode/base/receipts/LOCAL_WP02_IR_SELFTEST.json"], RECEIPT_DIR / "LOCAL_WP02_IR_SELFTEST.json", "pass"),
    ]

    # V17 selection is based on a concrete V9 trivia counterexample. Require the dedicated
    # strict discriminator whenever V17 is the selected grammar so the repair rationale is
    # itself executable, not merely documentary.
    if grammar.name == "D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark":
        component_specs.insert(
            0,
            (
                "v17_selection_discriminator",
                ["tools/claycode_v17_declarative_trivia_discriminator.py", "--require-strict", "--output", "research_entity/claycode/base/receipts/LOCAL_WP02_V17_SELECTION_DISCRIMINATOR.json"],
                RECEIPT_DIR / "LOCAL_WP02_V17_SELECTION_DISCRIMINATOR.json",
                "discriminator",
            ),
        )

    components = []
    for name, argv, receipt_path, kind in component_specs:
        if receipt_path.exists():
            receipt_path.unlink()
        proc = run(argv)
        row: dict[str, Any] = {"name": name, **proc, "receipt_path": str(receipt_path.relative_to(ROOT)), "receipt_exists": receipt_path.exists()}
        doc: dict[str, Any] = {}
        if receipt_path.exists():
            try:
                doc = load(receipt_path)
                row["receipt_sha256"] = sha(receipt_path)
            except Exception as exc:
                row["receipt_parse_error"] = f"{type(exc).__name__}: {exc}"
        embedded_path, embedded_sha = receipt_grammar(doc, inferred_path=grammar_rel if kind in {"decl", "pass"} else None)
        if kind == "strict":
            semantic = doc.get("strict_build_ok") is True and not doc.get("conflict_diagnostics")
        elif kind == "discriminator":
            semantic = doc.get("pass") is True and doc.get("promotion_allowed") is True and doc.get("counts_as_wp02_pass") is True
            cand = doc.get("candidate") if isinstance(doc.get("candidate"), dict) else {}
            embedded_path = cand.get("path") or embedded_path
            embedded_sha = cand.get("sha256") or embedded_sha
        elif kind == "decl":
            semantic = bool(doc.get("declarations"))
        else:
            semantic = doc.get("pass") is True
        grammar_bound = embedded_path == grammar_rel and embedded_sha == expected_sha
        row.update({"embedded_grammar_path": embedded_path, "embedded_grammar_sha256": embedded_sha, "grammar_bound": grammar_bound, "semantic_pass": bool(proc["process_pass"] and receipt_path.exists() and semantic and grammar_bound)})
        components.append(row)
        if not row["semantic_pass"]:
            break

    # The active production canonicalizer must independently point to the same contract
    # selection; this catches a stale frontend DEFAULT_GRAMMAR even when explicit calls pass.
    prod = run(["tools/claycode_base_canonicalizer_validation.py"], timeout=180)
    prod_path = ROOT / str(wp02.get("canonicalizer_receipt_path") or "research_entity/claycode/autonomous/BASE_CANONICALIZER_RECEIPT.json")
    prod_doc = load(prod_path) if prod_path.exists() else {}
    prod_bound = prod_doc.get("grammar") == grammar_rel
    production = {**prod, "receipt_path": str(prod_path.relative_to(ROOT)), "receipt_exists": prod_path.exists(), "receipt_sha256": sha(prod_path) if prod_path.exists() else None, "embedded_grammar_path": prod_doc.get("grammar"), "grammar_bound": prod_bound, "semantic_pass": bool(prod["process_pass"] and prod_doc.get("pass") is True and prod_bound)}

    passed = len(components) == len(component_specs) and all(x["semantic_pass"] for x in components) and production["semantic_pass"]
    base.update({"components": components, "production_canonicalizer": production, "pass": passed})
    if not passed:
        base["failure"] = "SELECTED_WP02_COMPONENT_FAILED"
    args.output.write_text(json.dumps(base, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": passed, "selected_grammar": grammar_rel, "grammar_sha256": expected_sha, "output": str(args.output.relative_to(ROOT)), "failed": [x["name"] for x in components if not x["semantic_pass"]] + ([] if production["semantic_pass"] else ["production_canonicalizer"])}, ensure_ascii=False))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Probe an exact provenance-bound FRANK ClayCode source against the BASE frontend.

This is an evidence tool, not an automatic language amendment. It records the first
parser failure plus a conservative top-level keyword inventory so a concrete FRANK
source can falsify frontend coverage without silently widening frozen BASE semantics.

The default FRANK source is a byte-identical repository snapshot with an explicit
provenance receipt. The probe fails closed if that snapshot drifts before parsing.

Default mode is strict LALR. --proxy-nonstrict exists only for hosted environments
where the optional Lark collision-analysis dependency is unavailable; proxy output is
never Ubuntu/BASE acceptance evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lark import Lark

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V9.lark"
DEFAULT_SOURCE = ROOT / "frank_reference/claycode/frank_runtime.clay"
DEFAULT_PROVENANCE = ROOT / "frank_reference/claycode/frank_runtime.provenance.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(path: Path) -> str:
    cp = subprocess.run(
        ["git", "hash-object", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if cp.returncode != 0 or not cp.stdout.strip():
        raise RuntimeError(f"GIT_HASH_OBJECT_FAILED:{path}:{cp.stderr.strip()}")
    value = cp.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise RuntimeError(f"INVALID_GIT_BLOB_SHA:{value!r}")
    return value


def read_provenance(path: Path, source_path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("FRANK_SOURCE_PROVENANCE_NOT_OBJECT")
    expected_blob = str(payload.get("source_git_blob_sha") or "")
    snapshot_blob = str(payload.get("snapshot_git_blob_sha") or "")
    expected_path = str(payload.get("snapshot_path") or "")
    try:
        actual_rel = str(source_path.resolve().relative_to(ROOT.resolve()))
    except ValueError as exc:
        raise RuntimeError("FRANK_SOURCE_OUTSIDE_REPOSITORY") from exc
    observed_blob = git_blob_sha(source_path)
    checks = {
        "byte_identity_verified": payload.get("byte_identity_verified") is True,
        "snapshot_path_matches": expected_path == actual_rel,
        "source_snapshot_blob_match": bool(expected_blob) and expected_blob == observed_blob,
        "declared_snapshot_blob_match": bool(snapshot_blob) and snapshot_blob == observed_blob,
    }
    if not all(checks.values()):
        raise RuntimeError(
            "FRANK_SOURCE_PROVENANCE_MISMATCH:"
            + json.dumps(
                {
                    "checks": checks,
                    "expected_source_blob": expected_blob,
                    "declared_snapshot_blob": snapshot_blob,
                    "observed_blob": observed_blob,
                    "expected_path": expected_path,
                    "observed_path": actual_rel,
                },
                sort_keys=True,
            )
        )
    return {
        "path": actual_rel,
        "provenance_path": str(path.resolve().relative_to(ROOT.resolve())),
        "source_repository": payload.get("source_repository"),
        "source_path": payload.get("source_path"),
        "git_blob_sha": observed_blob,
        "byte_identity_verified": True,
        "checks": checks,
    }


def first_word_inventory(source: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for raw in source.splitlines():
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        m = re.match(r"([A-Za-z_][A-Za-z0-9_-]*)", line)
        if m:
            key = m.group(1)
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def parser_result(parser: Lark, source: str) -> dict[str, Any]:
    try:
        tree = parser.parse(source)
        return {
            "accepted": True,
            "error_class": None,
            "error": None,
            "tree_nodes": sum(1 for _ in tree.iter_subtrees()),
        }
    except Exception as exc:
        return {
            "accepted": False,
            "error_class": type(exc).__name__,
            "error": str(exc),
            "tree_nodes": None,
        }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grammar", default=str(DEFAULT_GRAMMAR))
    ap.add_argument("--source", default=str(DEFAULT_SOURCE))
    ap.add_argument("--provenance", default=str(DEFAULT_PROVENANCE))
    ap.add_argument("--source-label", default="FRANK_RUNTIME")
    ap.add_argument("--output")
    ap.add_argument("--proxy-nonstrict", action="store_true")
    args = ap.parse_args()

    grammar_path = Path(args.grammar)
    source_path = Path(args.source)
    provenance_path = Path(args.provenance)
    grammar = grammar_path.read_text(encoding="utf-8")
    source = source_path.read_text(encoding="utf-8")

    provenance = read_provenance(provenance_path, source_path)

    parser = Lark(
        grammar,
        parser="lalr",
        lexer="contextual",
        strict=not args.proxy_nonstrict,
        start="start",
        keep_all_tokens=True,
    )
    parsed = parser_result(parser, source)
    inventory = first_word_inventory(source)

    out = {
        "schema_version": "1.2",
        "experiment": "ClayCode BASE V9 frontend vs exact provenance-bound FRANK source coverage probe",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "grammar": {
            "path": str(grammar_path),
            "sha256": sha256(grammar.encode("utf-8")),
            "strict": not args.proxy_nonstrict,
        },
        "source": {
            "label": args.source_label,
            "path": str(source_path),
            "sha256": sha256(source.encode("utf-8")),
            "bytes": len(source.encode("utf-8")),
            "git_blob_sha": provenance["git_blob_sha"],
            "provenance": provenance,
            "top_level_first_word_inventory": inventory,
        },
        "parse": parsed,
        "counterexample": not parsed["accepted"],
        "evidence_class": "HOSTED_PROXY_NONSTRICT" if args.proxy_nonstrict else "STRICT_FRONTEND_PROBE",
        "decision_rule": (
            "A parse failure on the exact provenance-bound frozen FRANK source using the active V9 "
            "frontend is a concrete coverage counterexample. It authorizes investigation of the "
            "smallest compatible syntax/IR or explicit dialect/pre-lowering delta; it does not by "
            "itself authorize a semantic change or a WP02/WP13 PASS."
        ),
        "scope_guard": (
            "This probe tests frontend acceptance only. A successful parse does not prove type/effect, "
            "runtime, authority, lowering, behavioral equivalence, WP13 source selection or Ubuntu "
            "release acceptance."
        ),
    }
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    print(text, end="")
    if not parsed["accepted"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

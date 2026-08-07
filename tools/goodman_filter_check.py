#!/usr/bin/env python3
"""Validate FRANK↔ClayCode anti-echo review artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ALLOWED = {"SUPPORTED", "REFINED", "REFUTED", "UNRESOLVED"}
REVIEW_NAME = "FRANK_CLAYCODE_GOODMAN_REVIEW.json"


def _load(path: Path) -> dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing required file: {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path.name}: {exc}") from exc
    if not isinstance(obj, dict):
        raise ValueError("review must be a JSON object")
    return obj


def template(run_id: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "protocol": "research_entity/global/GOODMAN_ANTI_ECHO_PROTOCOL.md",
        "claycode_run_id": run_id,
        "latest_frank_run": None,
        "latest_frank_architecture_artifact": None,
        "shared_ancestry_is_not_replication": True,
        "reviews": [
            {
                "claim_id": "REPLACE_ME",
                "frank_statement": "REPLACE_ME",
                "frank_source_refs": [],
                "ancestry_families": [],
                "shared_ancestry_collapsed": True,
                "counterhypothesis": "REPLACE_ME",
                "falsifier": "REPLACE_ME",
                "independent_checks": [],
                "adversarial_checks": [],
                "verdict": "UNRESOLVED",
                "reason": "REPLACE_ME",
                "claycode_action": "keep_open",
                "affected_claycode_artifacts": []
            }
        ]
    }


def _nonempty_str(x: Any) -> bool:
    return isinstance(x, str) and bool(x.strip()) and x != "REPLACE_ME"


def validate(path: Path) -> dict[str, Any]:
    d = _load(path)
    violations: list[str] = []
    if d.get("shared_ancestry_is_not_replication") is not True:
        violations.append("shared_ancestry_is_not_replication must be true")
    if not d.get("claycode_run_id"):
        violations.append("claycode_run_id required")
    if not d.get("latest_frank_run"):
        violations.append("latest_frank_run required")
    reviews = d.get("reviews")
    if not isinstance(reviews, list) or not reviews:
        violations.append("reviews must be a non-empty list")
    else:
        ids: list[str] = []
        for i, r in enumerate(reviews):
            if not isinstance(r, dict):
                violations.append(f"reviews[{i}] must be object")
                continue
            cid = r.get("claim_id")
            if not _nonempty_str(cid):
                violations.append(f"reviews[{i}].claim_id required")
            else:
                ids.append(cid)
            if not _nonempty_str(r.get("frank_statement")):
                violations.append(f"reviews[{i}].frank_statement required")
            if not isinstance(r.get("frank_source_refs"), list) or not r.get("frank_source_refs"):
                violations.append(f"reviews[{i}].frank_source_refs must be non-empty list")
            if not isinstance(r.get("ancestry_families"), list) or not r.get("ancestry_families"):
                violations.append(f"reviews[{i}].ancestry_families must be non-empty list")
            if r.get("shared_ancestry_collapsed") is not True:
                violations.append(f"reviews[{i}].shared_ancestry_collapsed must be true")
            if not _nonempty_str(r.get("counterhypothesis")):
                violations.append(f"reviews[{i}].counterhypothesis required")
            if not _nonempty_str(r.get("falsifier")):
                violations.append(f"reviews[{i}].falsifier required")
            if not isinstance(r.get("independent_checks"), list):
                violations.append(f"reviews[{i}].independent_checks must be list")
            if not isinstance(r.get("adversarial_checks"), list) or not r.get("adversarial_checks"):
                violations.append(f"reviews[{i}].adversarial_checks must be non-empty list")
            verdict = r.get("verdict")
            if verdict not in ALLOWED:
                violations.append(f"reviews[{i}].verdict invalid")
            if verdict in {"SUPPORTED", "REFINED"} and not r.get("independent_checks"):
                violations.append(f"reviews[{i}] {verdict} requires independent_checks")
            if verdict == "REFUTED" and str(r.get("claycode_action", "")).lower() not in {"reject", "supersede", "negative_result", "remove"}:
                violations.append(f"reviews[{i}] REFUTED must reject/supersede/preserve negative result")
            if verdict == "UNRESOLVED" and str(r.get("claycode_action", "")).lower() in {"integrate_as_true", "promote", "canonicalize"}:
                violations.append(f"reviews[{i}] UNRESOLVED cannot be promoted as truth")
            if not _nonempty_str(r.get("reason")):
                violations.append(f"reviews[{i}].reason required")
            if not _nonempty_str(r.get("claycode_action")):
                violations.append(f"reviews[{i}].claycode_action required")
            if not isinstance(r.get("affected_claycode_artifacts"), list):
                violations.append(f"reviews[{i}].affected_claycode_artifacts must be list")
        if len(ids) != len(set(ids)):
            violations.append("claim_id values must be unique")
    return {"ok": not violations, "review_file": str(path), "violations": violations}


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("template")
    t.add_argument("--run-id", required=True)
    t.add_argument("--output")
    v = sub.add_parser("validate")
    v.add_argument("path")
    args = ap.parse_args()
    if args.cmd == "template":
        text = json.dumps(template(args.run_id), ensure_ascii=False, indent=2) + "\n"
        if args.output:
            p = Path(args.output)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        print(text, end="")
        return
    out = validate(Path(args.path))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if not out["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

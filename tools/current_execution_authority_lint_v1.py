#!/usr/bin/env python3
"""Fail CI when current-facing execution projections drift into contradictory authority."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("projection manifest must be an object")
    return data


def has_local_supersession_context(text: str, phrase: str, radius: int = 450) -> bool:
    start = 0
    lowered = text.lower()
    needles = ("supersed", "historical", "legacy", "obsolete", "older")
    while True:
        idx = text.find(phrase, start)
        if idx < 0:
            return True
        lo = max(0, idx - radius)
        hi = min(len(text), idx + len(phrase) + radius)
        window = lowered[lo:hi]
        if not any(n in window for n in needles):
            return False
        start = idx + len(phrase)


def lint(repo: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    historical_roles = set(manifest.get("historical_roles_may_contain_forbidden_claims_only_when_supersession_marked") or [])
    quote_roles = set(manifest.get("roles_may_quote_forbidden_only_with_local_supersession_context") or [])
    forbidden = list(manifest.get("forbidden_current_claims") or [])

    for projection in manifest.get("projections", []):
        rel = projection["path"]
        role = projection["role"]
        path = repo / rel
        if not path.is_file():
            errors.append(f"MISSING:{rel}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in projection.get("required_markers", []):
            if marker not in text:
                errors.append(f"MISSING_MARKER:{rel}:{marker}")

        for phrase in forbidden:
            if phrase not in text:
                continue
            if role in historical_roles:
                head = "\n".join(text.splitlines()[:20]).upper()
                if "SUPERSEDED" not in head and "HISTORICAL" not in head:
                    errors.append(f"HISTORICAL_WITHOUT_TOP_SUPERSESSION:{rel}:{phrase}")
            elif role in quote_roles:
                if not has_local_supersession_context(text, phrase):
                    errors.append(f"UNMARKED_LEGACY_QUOTE_IN_CURRENT_AUTHORITY:{rel}:{phrase}")
            else:
                errors.append(f"STALE_CURRENT_CLAIM:{rel}:{phrase}")

    canonical = repo / manifest["canonical_authority"]
    if canonical.is_file():
        authority = canonical.read_text(encoding="utf-8", errors="replace")
        if "absence of a direct chat SSH tool is not `NO_EXECUTOR`".lower() not in authority.lower():
            errors.append("CANONICAL_AUTHORITY_MISSING_OPEN_WORLD_NO_EXECUTOR_RULE")
        if "FREE_ONLY_PROVIDER_POLICY != NO_VPS" not in authority:
            errors.append("CANONICAL_AUTHORITY_MISSING_PROVIDER_COMPUTE_AXIS_SEPARATION")
        if "EXECUTION_SURFACE_RESOLUTION_PROTOCOL_V1.md" not in authority:
            errors.append("CANONICAL_AUTHORITY_MISSING_EXECUTION_SURFACE_RESOLVER_BINDING")
    else:
        errors.append(f"MISSING_CANONICAL_AUTHORITY:{manifest['canonical_authority']}")

    protocol = repo / manifest["resolver_protocol"]
    registry = repo / manifest["registry"]
    if not protocol.is_file():
        errors.append(f"MISSING_RESOLVER_PROTOCOL:{manifest['resolver_protocol']}")
    if not registry.is_file():
        errors.append(f"MISSING_EXECUTION_SURFACE_REGISTRY:{manifest['registry']}")

    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--manifest", default="governance/CURRENT_EXECUTION_SURFACE_PROJECTIONS_V1.json")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    manifest = load(repo / args.manifest)
    errors = lint(repo, manifest)
    print(json.dumps({
        "schema": "CURRENT_EXECUTION_AUTHORITY_LINT/v1",
        "pass": not errors,
        "errors": errors,
        "projection_count": len(manifest.get("projections", [])),
    }, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)

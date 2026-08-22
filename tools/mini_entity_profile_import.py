#!/usr/bin/env python3
"""Import a replaceable Mini Entity profile and optional components into MiniUnifiedDB.

This is a configuration/import surface, not runtime state authority. The canonical run
reads profile/component bytes only from SQLite after import. The tool prints hashes and
identifiers only; it never prints profile/component contents or secrets.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from clay_profile_pipeline_runtime import ProfilePipelineRuntime


def _json_object(path: str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _components(values: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for raw in values:
        if "=" not in raw:
            raise ValueError("--component requires KIND=FILE.json")
        kind, path = raw.split("=", 1)
        kind = kind.strip()
        if not kind or kind in out:
            raise ValueError("component kind must be non-empty and unique")
        out[kind] = _json_object(path)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entity-db", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument(
        "--component",
        action="append",
        default=[],
        metavar="KIND=FILE.json",
        help="Repeatable replaceable profile component imported into SQLite.",
    )
    parser.add_argument(
        "--keep-existing-components",
        action="store_true",
        help="Do not remove DB components omitted from this import.",
    )
    parser.add_argument(
        "--inactive",
        action="store_true",
        help="Import/update the profile without making it the one active profile.",
    )
    args = parser.parse_args()

    profile = _json_object(args.profile)
    components = _components(args.component)
    runtime = ProfilePipelineRuntime(root=Path.cwd())
    profile_hash = runtime.install_profile(
        args.entity_db,
        profile,
        activate=not args.inactive,
        components=components,
        replace_components=not args.keep_existing_components,
    )
    loaded = runtime.effect("pipeline_profile_read", {"entity_db": args.entity_db}) if not args.inactive else None
    component_hashes = loaded.get("component_hashes", {}) if isinstance(loaded, dict) and loaded.get("ok") else {}
    print(
        json.dumps(
            {
                "ok": True,
                "profile_id": profile.get("profile_id"),
                "active": not args.inactive,
                "profile_hash": profile_hash,
                "component_hashes": component_hashes,
                "runtime_dependency_on_import_files": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

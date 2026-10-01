#!/usr/bin/env python3
"""Generate a deterministic cache of versioned one-off tools.

Policy is intentionally mechanical: files matching tools/<family>_vN.py are grouped
by exact <family>; the highest numeric N is indexed LIVE and lower N values are
SUPERSEDED. This is a navigation/lint cache, never semantic or execution authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "research_entity" / "tooling" / "TOOL_VERSION_INDEX.json"
VERSION_RE = re.compile(r"^(?P<family>.+)_v(?P<version>[0-9]+)\.py$")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_index(root: Path) -> dict[str, Any]:
    root = root.resolve()
    tools = root / "tools"
    all_py = sorted(p for p in tools.glob("*.py") if p.is_file())
    groups: dict[str, list[tuple[int, Path]]] = {}
    for path in all_py:
        match = VERSION_RE.match(path.name)
        if not match:
            continue
        family = match.group("family")
        version = int(match.group("version"))
        groups.setdefault(family, []).append((version, path))

    group_rows = []
    tool_rows = []
    for family in sorted(groups):
        members = sorted(groups[family], key=lambda item: (item[0], item[1].name))
        highest = max(version for version, _ in members)
        live = [path for version, path in members if version == highest]
        # Ambiguous duplicate numeric maxima are kept visible and fail lint rather than guessed.
        live_paths = [str(path.relative_to(root)) for path in live]
        superseded = [
            str(path.relative_to(root))
            for version, path in members
            if version < highest
        ]
        ambiguous = len(live_paths) != 1
        group_rows.append(
            {
                "family": family,
                "highest_numeric_version": highest,
                "live": live_paths,
                "superseded": superseded,
                "ambiguous_highest_version": ambiguous,
            }
        )
        for version, path in members:
            rel = str(path.relative_to(root))
            tool_rows.append(
                {
                    "path": rel,
                    "family": family,
                    "version": version,
                    "status": "LIVE" if version == highest else "SUPERSEDED",
                }
            )

    inventory_material = "\n".join(str(p.relative_to(root)) for p in all_py).encode("utf-8")
    return {
        "schema": "TOOL_VERSION_INDEX/v1",
        "generated_cache": True,
        "authority": False,
        "root": "tools",
        "policy": "highest_numeric_version_per_exact_filename_family",
        "pattern": "tools/<family>_vN.py",
        "inventory": {
            "python_tool_count": len(all_py),
            "versioned_tool_count": len(tool_rows),
            "family_count": len(group_rows),
            "superseded_count": sum(1 for row in tool_rows if row["status"] == "SUPERSEDED"),
            "ambiguous_family_count": sum(1 for row in group_rows if row["ambiguous_highest_version"]),
            "tool_path_inventory_sha256": _sha256(inventory_material),
        },
        "groups": group_rows,
        "tools": sorted(tool_rows, key=lambda row: row["path"]),
    }


def serialize(index: dict[str, Any]) -> str:
    return json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--output", default=None)
    ap.add_argument("--stdout", action="store_true")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    index = build_index(root)
    text = serialize(index)
    output = Path(args.output).resolve() if args.output else (
        root / "research_entity" / "tooling" / "TOOL_VERSION_INDEX.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    if args.stdout:
        print(text, end="")
    else:
        print(json.dumps({
            "ok": True,
            "output": str(output),
            "sha256": _sha256(text.encode("utf-8")),
            "inventory": index["inventory"],
        }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

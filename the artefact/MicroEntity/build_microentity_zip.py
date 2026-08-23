#!/usr/bin/env python3
"""Build the portable MicroEntity snapshot deterministically.

Release policy:
- include the canonical package root files listed below;
- include every non-secret regular file under hcu/ recursively;
- never include the archive itself, cache/editor debris, or secret-like files.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import zipfile

ROOT_MEMBERS = (
    "CURRENT_PRODUCT_CONSOLIDATED.md",
    "PACKAGE_MANIFEST.json",
    "README.md",
    "ZERO_LINK.md",
    "build_microentity_zip.py",
)
EXCLUDE_DIRS = {"__pycache__", ".git", ".pytest_cache"}
FORBIDDEN_NAMES = {
    ".env",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "secrets.json",
    "token.txt",
    "api_key.txt",
}
FORBIDDEN_SUFFIXES = (".pyc", "~", ".swp")


def _assert_safe(rel: Path) -> None:
    parts = [p.lower() for p in rel.parts]
    if any(p in EXCLUDE_DIRS for p in parts):
        raise ValueError(f"cache directory is not an archive member: {rel}")
    if any(p in FORBIDDEN_NAMES for p in parts):
        raise SystemExit(f"secret-like path is forbidden in MicroEntity archive: {rel}")
    if rel.name.endswith(FORBIDDEN_SUFFIXES):
        raise ValueError(f"editor/cache file is not an archive member: {rel}")


def collect(root: Path) -> list[tuple[Path, Path]]:
    rows: list[tuple[Path, Path]] = []
    for name in ROOT_MEMBERS:
        p = root / name
        if not p.is_file():
            raise SystemExit(f"required package member missing: {name}")
        rel = Path(name)
        _assert_safe(rel)
        rows.append((p, rel))

    hcu = root / "hcu"
    if not hcu.is_dir():
        raise SystemExit("required HCU package root missing: hcu/")
    for p in sorted(hcu.rglob("*"), key=lambda x: x.as_posix()):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        try:
            _assert_safe(rel)
        except ValueError:
            continue
        rows.append((p, rel))

    dedup: dict[str, tuple[Path, Path]] = {rel.as_posix(): (p, rel) for p, rel in rows}
    return [dedup[k] for k in sorted(dedup)]


def build(root: Path, output: Path) -> int:
    rows = collect(root)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for src, rel in rows:
            info = zipfile.ZipInfo(rel.as_posix())
            info.date_time = (2026, 8, 23, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, src.read_bytes())
    return len(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent))
    ap.add_argument("--output", default=None)
    args = ap.parse_args()
    root = Path(args.root).resolve()
    output = Path(args.output).resolve() if args.output else root / "MICROENTITY_CURRENT.zip"
    count = build(root, output)
    print(f"{output}: {count} files")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Rebuild MICROENTITY_CURRENT.zip from the package root."""
from pathlib import Path
import argparse
import zipfile

FORBIDDEN_PARTS = {
    ".env", "id_rsa", "id_ed25519", "credentials.json", "secrets.json",
    "token.txt", "api_key.txt"
}
EXCLUDE_DIRS = {"__pycache__", ".git", ".pytest_cache"}

def files_for(root: Path, output: Path):
    out_abs = output.resolve()
    for p in sorted(root.rglob("*"), key=lambda x: x.as_posix()):
        if not p.is_file() or p.resolve() == out_abs:
            continue
        rel = p.relative_to(root)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if {part.lower() for part in rel.parts} & FORBIDDEN_PARTS:
            raise SystemExit(f"forbidden secret-like file in package tree: {rel}")
        if p.name.endswith((".pyc", "~", ".swp")):
            continue
        yield p, rel

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent))
    ap.add_argument("--output", default=None)
    args = ap.parse_args()
    root = Path(args.root).resolve()
    output = Path(args.output).resolve() if args.output else root / "MICROENTITY_CURRENT.zip"
    rows = list(files_for(root, output))
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p, rel in rows:
            info = zipfile.ZipInfo(rel.as_posix())
            info.date_time = (2026, 8, 23, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, p.read_bytes())
    print(f"{output}: {len(rows)} files")

if __name__ == "__main__":
    main()

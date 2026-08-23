#!/usr/bin/env python3
"""Build deterministic MICROENTITY_CURRENT.zip.

Archive policy preserves the existing compact package snapshot while making the new HCU subtree
complete: selected top-level package contracts + every non-secret HCU file are included.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
import json


ROOT = Path(__file__).resolve().parent
SNAPSHOT = ROOT / "MICROENTITY_CURRENT.zip"
CONTENTS = ROOT / "PACKAGE_CONTENTS.json"
TOP_LEVEL_MEMBERS = {
    "CURRENT_PRODUCT_CONSOLIDATED.md",
    "PACKAGE_MANIFEST.json",
    "README.md",
    "ZERO_LINK.md",
    "build_microentity_zip.py",
}
HCU_ROOT = ROOT / "hyperposition_compute_unit"
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".git"}
SECRET_SUFFIXES = {".key", ".pem", ".p12", ".pfx"}
SECRET_NAMES = {".env", ".env.local", "secrets.json", "credentials.json"}


def safe_file(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if path.name in SECRET_NAMES:
        return False
    if any(part in EXCLUDED_PARTS for part in rel.parts):
        return False
    if path.suffix.lower() in SECRET_SUFFIXES:
        return False
    return path.is_file()


def members() -> list[Path]:
    selected = [ROOT / name for name in TOP_LEVEL_MEMBERS if (ROOT / name).is_file()]
    if not HCU_ROOT.is_dir():
        raise SystemExit("HCU_PACKAGE_ROOT_MISSING")
    selected.extend(p for p in HCU_ROOT.rglob("*") if safe_file(p))
    return sorted(set(selected), key=lambda p: p.relative_to(ROOT).as_posix())


def write_contents(files: list[Path]) -> None:
    payload = {
        "schema": "MICROENTITY_PACKAGE_CONTENTS/v1",
        "snapshot": SNAPSHOT.name,
        "archive_policy": "TOP_LEVEL_CONTRACTS_PLUS_COMPLETE_HCU_SUBTREE",
        "hcu_files_must_be_included": True,
        "files": [
            {
                "path": p.relative_to(ROOT).as_posix(),
                "size": p.stat().st_size,
                "sha256": sha256(p.read_bytes()).hexdigest(),
            }
            for p in files
        ],
    }
    CONTENTS.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build() -> None:
    files = members()
    hcu_files = [p for p in files if HCU_ROOT in p.parents]
    if not hcu_files:
        raise SystemExit("HCU_ARCHIVE_MEMBERS_MISSING")

    write_contents(files)
    files = sorted(files + [CONTENTS], key=lambda p: p.relative_to(ROOT).as_posix())

    with ZipFile(SNAPSHOT, "w", compression=ZIP_DEFLATED, compresslevel=9) as zf:
        for p in files:
            rel = p.relative_to(ROOT).as_posix()
            info = ZipInfo(rel)
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, p.read_bytes())

    names = set(ZipFile(SNAPSHOT).namelist())
    missing_hcu = {
        p.relative_to(ROOT).as_posix()
        for p in hcu_files
        if p.relative_to(ROOT).as_posix() not in names
    }
    if missing_hcu:
        raise SystemExit(f"HCU_ARCHIVE_MEMBERS_MISSING:{sorted(missing_hcu)}")


if __name__ == "__main__":
    build()

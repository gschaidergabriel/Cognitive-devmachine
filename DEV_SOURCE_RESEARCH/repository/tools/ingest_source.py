#!/usr/bin/env python3
"""RAE-8.8 source ingester with explicit multi-researcher provenance.

Copies exact source bytes into a content-addressed Git archive tree, creates an
append-only manifest, performs conservative secret-name/content checks, and builds
machine-usable derivative metadata. It NEVER deletes or rewrites the source.

Authorship is not ingestion: imported files retain their original/external/user origin
when known; `ingested_by` records the Research Entity worker that performed the ingest.

Usage example:
  python tools/ingest_source.py --source-dir /path/to/project/source \
      --ingested-by claude-code-lead --supplied-by user-gabriel

Then review research_sources/quarantine before committing, run status/classification,
and commit the generated repository changes.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import mimetypes
from pathlib import Path
import re
import sqlite3
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "research_sources" / "raw" / "sha256"
MANIFEST_DIR = ROOT / "research_sources" / "manifests"
DERIVED = ROOT / "research_sources" / "derived"
QUARANTINE = ROOT / "research_sources" / "quarantine"
ACTOR_REGISTRY = ROOT / "research_entity" / "global" / "RESEARCH_ACTOR_REGISTRY.json"

SECRET_NAME = re.compile(
    r"(^|/)(\.env($|\.)|.*credentials?.*|.*private.*key.*|id_rsa|id_ed25519|"
    r".*password.*|.*cookie.*|.*secret.*)", re.I
)
SECRET_CONTENT = re.compile(
    rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    rb"(?:api[_-]?key|access[_-]?token|secret[_-]?key|password)\s*[:=]\s*[\"']?"
    rb"[A-Za-z0-9_\-\/+=]{16,}", re.I
)
TEXT_EXTS = {
    ".txt", ".md", ".json", ".jsonl", ".csv", ".tsv", ".py", ".sh",
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".sql", ".xml",
    ".html", ".js", ".ts", ".cc", ".c", ".h", ".hpp", ".rs", ".go",
    ".java", ".ebnf", ".log"
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_rel(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


def content_secret_hit(data: bytes) -> bool:
    sample = data if len(data) <= 4_000_000 else data[:2_000_000] + data[-2_000_000:]
    return bool(SECRET_CONTENT.search(sample))


def derive_pdf(blob: Path, sha: str) -> dict:
    out_dir = DERIVED / sha
    out_dir.mkdir(parents=True, exist_ok=True)
    txt = out_dir / "document.txt"
    try:
        subprocess.run(["pdftotext", str(blob), str(txt)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"pdf_text": str(txt.relative_to(ROOT)), "ok": True}
    except Exception as exc:
        return {"pdf_text": None, "ok": False, "error": type(exc).__name__}


def derive_zip(blob: Path, sha: str) -> dict:
    out_dir = DERIVED / sha
    out_dir.mkdir(parents=True, exist_ok=True)
    listing = []
    extracted_text = []
    try:
        with zipfile.ZipFile(blob) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                ext = Path(info.filename).suffix.lower()
                listing.append({
                    "path": info.filename,
                    "bytes": info.file_size,
                    "compressed": info.compress_size,
                    "crc": info.CRC,
                    "textlike": ext in TEXT_EXTS,
                })
                if ext in TEXT_EXTS and info.file_size <= 20_000_000:
                    try:
                        data = zf.read(info)
                        if SECRET_NAME.search(info.filename) or content_secret_hit(data):
                            continue
                        target = out_dir / "text" / info.filename
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(data)
                        extracted_text.append(str(target.relative_to(ROOT)))
                    except Exception:
                        pass
        (out_dir / "zip_listing.json").write_text(
            json.dumps(listing, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return {
            "zip_listing": str((out_dir / "zip_listing.json").relative_to(ROOT)),
            "extracted_text_files": extracted_text,
            "ok": True,
        }
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__}


def derive_sqlite(blob: Path, sha: str) -> dict:
    out_dir = DERIVED / sha
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        con = sqlite3.connect(f"file:{blob}?mode=ro", uri=True)
        rows = con.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        ).fetchall()
        counts = {}
        for typ, name, tbl, sql in rows:
            if typ == "table" and not name.startswith("sqlite_"):
                try:
                    counts[name] = con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                except Exception:
                    counts[name] = None
        con.close()
        meta = {"sqlite_master": rows, "table_counts": counts}
        p = out_dir / "sqlite_metadata.json"
        p.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"sqlite_metadata": str(p.relative_to(ROOT)), "ok": True}
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__}


def ingest_file(path: Path, base: Path, provenance: dict) -> dict:
    rel = safe_rel(path, base)
    data = path.read_bytes()
    sha = sha256_bytes(data)
    ext = path.suffix.lower()
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    secret_name = bool(SECRET_NAME.search(rel))
    secret_content = content_secret_hit(data) if (ext in TEXT_EXTS or len(data) < 4_000_000) else False
    quarantined = secret_name or secret_content

    if quarantined:
        storage_path = None
    else:
        target = ARCHIVE / sha[:2] / sha
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(data)
        storage_path = str(target.relative_to(ROOT))

    derivative = None
    if not quarantined and storage_path:
        blob = ROOT / storage_path
        if ext == ".pdf": derivative = derive_pdf(blob, sha)
        elif ext == ".zip": derivative = derive_zip(blob, sha)
        elif ext in {".db", ".sqlite", ".sqlite3"}: derivative = derive_sqlite(blob, sha)

    return {
        "source_path": rel,
        "filename": path.name,
        "bytes": len(data),
        "sha256": sha,
        "mime": mime,
        "extension": ext,
        "archive_path": storage_path,
        "quarantined": quarantined,
        "secret_name_hit": secret_name,
        "secret_content_hit": secret_content,
        "derived": derivative,
        "claim_status": "UNCLASSIFIED",
        "provenance": {
            "origin_actor": provenance.get("origin_actor"),
            "origin_attribution_status": provenance.get("origin_attribution_status"),
            "supplied_by": provenance.get("supplied_by"),
            "ingested_by": provenance["ingested_by"],
            "ingesting_actor_role": provenance.get("ingesting_actor_role"),
            "ingesting_provider": provenance.get("ingesting_provider"),
            "ingesting_model": provenance.get("ingesting_model"),
            "ingesting_runtime": provenance.get("ingesting_runtime")
        }
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", required=True)
    ap.add_argument("--include-hidden", action="store_true")
    ap.add_argument("--ingested-by", required=True, help="actor_id from RESEARCH_ACTOR_REGISTRY.json")
    ap.add_argument("--supplied-by", default="user-gabriel")
    ap.add_argument("--origin-actor", default="", help="Only set when common original authorship for this ingest batch is actually known")
    ap.add_argument("--model", default="")
    ap.add_argument("--runtime", default="")
    args = ap.parse_args()
    base = Path(args.source_dir).expanduser().resolve()
    if not base.is_dir(): raise SystemExit(f"not a directory: {base}")

    registry=json.loads(ACTOR_REGISTRY.read_text(encoding='utf-8'))
    actors={a['actor_id']:a for a in registry['actors']}
    if args.ingested_by not in actors:
        raise SystemExit(f"unknown --ingested-by actor {args.ingested_by!r}")
    actor=actors[args.ingested_by]
    provenance={
        "origin_actor": args.origin_actor or None,
        "origin_attribution_status": "KNOWN_BATCH_ORIGIN" if args.origin_actor else "UNKNOWN_OR_PER_FILE_UNRESOLVED",
        "supplied_by": args.supplied_by or None,
        "ingested_by": args.ingested_by,
        "ingesting_actor_role": actor.get('role'),
        "ingesting_provider": actor.get('organization') or 'human',
        "ingesting_model": args.model or None,
        "ingesting_runtime": args.runtime or None
    }

    records = []
    for p in sorted(base.rglob("*")):
        if not p.is_file(): continue
        rel_parts = p.relative_to(base).parts
        if not args.include_hidden and any(part.startswith(".") for part in rel_parts): continue
        records.append(ingest_file(p, base, provenance))

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    manifest = {
        "schema_version": "1.1",
        "created_at": now,
        "source_root": str(base),
        "file_count": len(records),
        "unique_sha256": len({r["sha256"] for r in records}),
        "quarantined": sum(bool(r["quarantined"]) for r in records),
        "ingestion_provenance": provenance,
        "records": records,
    }
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = MANIFEST_DIR / f"INGEST_{stamp}.json"
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(out)
    print(json.dumps({k: manifest[k] for k in ("file_count","unique_sha256","quarantined","ingestion_provenance")}, indent=2,ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

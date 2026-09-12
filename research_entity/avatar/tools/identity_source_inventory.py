#!/usr/bin/env python3
"""Read-only inventory for Avatar identity/landmark/mask evidence in the live visual root.

The tool is intentionally non-authoritative. It discovers explicit candidate files and textual
references for identity regions without inventing ROIs, launching Chrome, touching the singleton,
or mutating live Avatar state. Its output is a provenance packet for later human/executable
binding, not a region-selection decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from PIL import Image

SCHEMA = "AVATAR_IDENTITY_SOURCE_INVENTORY/v1"
REGION_TERMS: dict[str, tuple[str, ...]] = {
    "hair": ("hair", "haar", "frisur"),
    "nose": ("nose", "nase"),
    "mouth": ("mouth", "mund", "lip", "lips", "lippe", "lippen"),
    "neck": ("neck", "hals"),
    "eyes": ("eye", "eyes", "auge", "augen"),
    "head": ("head", "kopf", "face", "gesicht"),
}
EVIDENCE_TERMS = ("mask", "maske", "anchor", "anker", "landmark", "roi", "segment", "segmentation", "keypoint")
TEXT_SUFFIXES = {".html", ".htm", ".js", ".mjs", ".json", ".css", ".txt", ".md"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
DEFAULT_TEXT_FILES = (
    "buehne.html",
    "public/js/avatar.js",
    "public/js/filmlook.js",
    "public/js/face.js",
    "public/js/rig.js",
)
TOKEN_SPLIT = re.compile(r"[^a-z0-9äöüß]+", re.IGNORECASE)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path, root: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))


def tokens(text: str) -> set[str]:
    return {part for part in TOKEN_SPLIT.split(text.lower()) if part}


def terms_in_name(path: Path, terms: tuple[str, ...]) -> list[str]:
    path_tokens = tokens(str(path))
    return [term for term in terms if term.lower() in path_tokens]


def file_record(path: Path, root: Path) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "path": rel(path, root),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        "suffix": path.suffix.lower(),
    }
    if path.suffix.lower() in IMAGE_SUFFIXES:
        try:
            with Image.open(path) as im:
                rec["image"] = {"width": int(im.width), "height": int(im.height), "mode": str(im.mode)}
        except Exception as exc:  # preserve unreadable candidates instead of hiding them
            rec["image_error"] = f"{type(exc).__name__}: {exc}"
    return rec


def candidate_regions(path: Path) -> list[str]:
    return [region for region, region_terms in REGION_TERMS.items() if terms_in_name(path, region_terms)]


def candidate_evidence_classes(path: Path) -> list[str]:
    return terms_in_name(path, EVIDENCE_TERMS)


def bounded_text_refs(path: Path, root: Path, max_hits: int) -> list[dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [{"path": rel(path, root), "error": f"{type(exc).__name__}: {exc}"}]
    refs: list[dict[str, Any]] = []
    region_terms = tuple(sorted({term for region_terms in REGION_TERMS.values() for term in region_terms}))
    all_terms = region_terms + EVIDENCE_TERMS
    pattern = re.compile(
        r"(?<![A-Za-z0-9ÄÖÜäöüß])(" + "|".join(re.escape(x) for x in sorted(all_terms, key=len, reverse=True)) + r")(?![A-Za-z0-9ÄÖÜäöüß])",
        re.IGNORECASE,
    )
    for lineno, line in enumerate(text.splitlines(), 1):
        matched_terms = sorted({m.group(1).lower() for m in pattern.finditer(line)})
        if not matched_terms:
            continue
        clean = " ".join(line.strip().split())
        refs.append({
            "path": rel(path, root),
            "line": lineno,
            "terms": matched_terms,
            "snippet": clean[:240],
        })
        if len(refs) >= max_hits:
            break
    return refs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--visual-root", default="/home/ai-core-node/.claude/star/visual")
    ap.add_argument("--out", required=True, help="JSON output path")
    ap.add_argument("--max-files", type=int, default=25000)
    ap.add_argument("--max-candidates-per-region", type=int, default=100)
    ap.add_argument("--max-evidence-named", type=int, default=500)
    ap.add_argument("--max-text-hits-per-file", type=int, default=80)
    args = ap.parse_args()

    root = Path(args.visual_root).resolve()
    if not root.is_dir():
        raise SystemExit(f"visual root is not a directory: {root}")
    if min(args.max_files, args.max_candidates_per_region, args.max_evidence_named, args.max_text_hits_per_file) <= 0:
        raise SystemExit("all bounds must be positive")

    all_files = sorted((path for path in root.rglob("*") if path.is_file()), key=lambda path: str(path))
    if len(all_files) > args.max_files:
        raise SystemExit(f"visual root has {len(all_files)} files > --max-files={args.max_files}; refuse unbounded scan")

    by_region: dict[str, list[dict[str, Any]]] = {region: [] for region in REGION_TERMS}
    evidence_named: list[dict[str, Any]] = []
    record_cache: dict[Path, dict[str, Any]] = {}

    def get_record(path: Path) -> dict[str, Any]:
        if path not in record_cache:
            record_cache[path] = file_record(path, root)
        return record_cache[path]

    for path in all_files:
        regions = candidate_regions(path)
        evidence_classes = candidate_evidence_classes(path)
        wants_region = any(len(by_region[region]) < args.max_candidates_per_region for region in regions)
        wants_evidence = bool(evidence_classes) and len(evidence_named) < args.max_evidence_named
        if not wants_region and not wants_evidence:
            continue
        base = get_record(path)
        rec = dict(base)
        rec["regions_by_name_only"] = regions
        rec["evidence_classes_by_name_only"] = evidence_classes
        if wants_evidence:
            evidence_named.append(rec)
        for region in regions:
            if len(by_region[region]) < args.max_candidates_per_region:
                by_region[region].append(rec)

    text_paths: list[Path] = []
    for relative in DEFAULT_TEXT_FILES:
        path = root / relative
        if path.is_file():
            text_paths.append(path)
    # Also inspect explicitly identity/evidence-named text files, but never every arbitrary source file.
    for path in all_files:
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if candidate_regions(path) or candidate_evidence_classes(path):
            text_paths.append(path)
    dedup_text_paths = sorted(set(text_paths), key=lambda path: str(path))

    text_refs: list[dict[str, Any]] = []
    for path in dedup_text_paths:
        text_refs.extend(bounded_text_refs(path, root, args.max_text_hits_per_file))

    missing_explicit_region_candidates = [region for region, rows in by_region.items() if not rows]
    packet = {
        "schema": SCHEMA,
        "scope": "READ_ONLY_SOURCE_DISCOVERY_ONLY",
        "visual_root": str(root),
        "visual_root_file_count": len(all_files),
        "region_candidates": by_region,
        "evidence_named_candidates": evidence_named,
        "text_references": text_refs[:1000],
        "missing_explicit_region_candidates": missing_explicit_region_candidates,
        "selection_authority": False,
        "roi_geometry_credit": 0,
        "identity_preservation_credit": 0,
        "perceptual_lifelikeness_credit": 0,
        "live_avatar_mutation": 0,
        "browser_processes_started": 0,
        "singleton_touched": False,
        "interpretation_law": "Filename/text matches are discovery evidence only. They MUST NOT be promoted to canonical ROI/mask/landmark geometry without exact semantic binding and executable/readback evidence.",
        "next_exact_gate": "Review explicit candidate masks/anchors/landmarks from this packet; bind only semantically supported hair/nose/mouth/neck/eye geometry to AVATAR_IDENTITY_ROIS/v1, then run the final-size visual packet and actual singleton-preserving final-presentation readback.",
    }
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": SCHEMA,
        "out": str(out),
        "files_scanned": len(all_files),
        "candidate_counts": {region: len(rows) for region, rows in by_region.items()},
        "evidence_named_count": len(evidence_named),
        "text_reference_count": len(text_refs),
        "missing_explicit_region_candidates": missing_explicit_region_candidates,
        "live_avatar_mutation": 0,
        "browser_processes_started": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

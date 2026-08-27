#!/usr/bin/env python3
"""Fail-closed reader for authoritative monitoring publication generations.

Authority/runtime consumers MUST resolve `free swarm/SYSTEM_ANALYSIS_CURRENT.json`, verify the
pointer, generation root, manifest digest, publication generation and every referenced file hash,
and only then consume files from that generation directory. Compatibility mirrors are never
accepted as authority-bearing inputs.

This reader performs no provider/network calls and has no write side effects.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

POINTER_SCHEMA = "CLAY_MONITOR_CURRENT/v1"
MANIFEST_SCHEMA = "CLAY_MONITOR_PUBLICATION_SET/v1"
ALLOWED_FILES = {
    "SYSTEM_ANALYSIS_LIVE.json",
    "SYSTEM_ANALYSIS_PROVENANCE.json",
    "README.md",
}


class PublicationReadError(RuntimeError):
    pass


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_json_bytes(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise PublicationReadError(f"missing_or_unreadable:{path.name}:{type(exc).__name__}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise PublicationReadError(f"invalid_json:{path.name}:{type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise PublicationReadError(f"json_not_object:{path.name}")
    return value, raw


def _safe_generation_root(free_swarm_dir: Path, pointer: dict[str, Any]) -> tuple[str, Path]:
    generation = pointer.get("publication_generation")
    root_text = pointer.get("generation_root")
    if not isinstance(generation, str) or not generation or any(c not in "0123456789abcdef" for c in generation):
        raise PublicationReadError("invalid_publication_generation")
    if not isinstance(root_text, str) or not root_text:
        raise PublicationReadError("invalid_generation_root")

    rel = Path(root_text)
    expected_rel = Path("publication_generations") / generation
    if rel.is_absolute() or rel != expected_rel or ".." in rel.parts:
        raise PublicationReadError("generation_root_path_escape_or_mismatch")

    fs_resolved = free_swarm_dir.resolve()
    root = (free_swarm_dir / rel).resolve()
    try:
        root.relative_to(fs_resolved)
    except ValueError as exc:
        raise PublicationReadError("generation_root_outside_free_swarm") from exc
    if root.parent != (fs_resolved / "publication_generations"):
        raise PublicationReadError("generation_root_not_direct_child")
    return generation, root


def read_current_publication(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    fs = repo / "free swarm"
    pointer_path = fs / "SYSTEM_ANALYSIS_CURRENT.json"
    pointer, _pointer_raw = _load_json_bytes(pointer_path)
    if pointer.get("schema") != POINTER_SCHEMA:
        raise PublicationReadError("pointer_schema_mismatch")

    generation, root = _safe_generation_root(fs, pointer)
    manifest_path = root / "MANIFEST.json"
    manifest, manifest_raw = _load_json_bytes(manifest_path)

    expected_manifest_sha = pointer.get("manifest_sha256")
    if not isinstance(expected_manifest_sha, str) or len(expected_manifest_sha) != 64:
        raise PublicationReadError("invalid_pointer_manifest_sha256")
    if _sha256_bytes(manifest_raw) != expected_manifest_sha:
        raise PublicationReadError("manifest_digest_mismatch")
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise PublicationReadError("manifest_schema_mismatch")
    if manifest.get("publication_generation") != generation:
        raise PublicationReadError("manifest_generation_mismatch")

    files = manifest.get("files")
    if not isinstance(files, dict) or set(files) != ALLOWED_FILES:
        raise PublicationReadError("manifest_file_set_mismatch")

    verified: dict[str, Any] = {}
    hashes: dict[str, str] = {}
    for name in sorted(ALLOWED_FILES):
        expected_hash = files.get(name)
        if not isinstance(expected_hash, str) or len(expected_hash) != 64:
            raise PublicationReadError(f"invalid_file_hash:{name}")
        path = root / name
        # File names are fixed constants; still bind resolved location fail-closed.
        if path.resolve().parent != root:
            raise PublicationReadError(f"file_path_escape:{name}")
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise PublicationReadError(f"missing_file:{name}:{type(exc).__name__}") from exc
        actual = _sha256_bytes(raw)
        if actual != expected_hash:
            raise PublicationReadError(f"file_digest_mismatch:{name}")
        hashes[name] = actual
        if name.endswith(".json"):
            try:
                obj = json.loads(raw.decode("utf-8"))
            except Exception as exc:
                raise PublicationReadError(f"invalid_generation_json:{name}") from exc
            if not isinstance(obj, dict):
                raise PublicationReadError(f"generation_json_not_object:{name}")
            if obj.get("publication_generation") != generation:
                raise PublicationReadError(f"file_generation_mismatch:{name}")
            verified[name] = obj
        else:
            verified[name] = raw.decode("utf-8", errors="strict")

    live = verified["SYSTEM_ANALYSIS_LIVE.json"]
    provenance = verified["SYSTEM_ANALYSIS_PROVENANCE.json"]
    if live.get("schema") != "CLAY_FREE_SWARM_SYSTEM_ANALYSIS/v6":
        raise PublicationReadError("live_schema_mismatch")
    if provenance.get("publication_generation") != generation:
        raise PublicationReadError("provenance_generation_mismatch")

    return {
        "schema": "CLAY_MONITOR_VERIFIED_READ/v1",
        "publication_generation": generation,
        "generation_root": str(root),
        "manifest_sha256": expected_manifest_sha,
        "file_sha256": hashes,
        "control_plane_coherent": bool(manifest.get("control_plane_coherent")),
        "authority_state": manifest.get("authority_state"),
        "live": live,
        "provenance": provenance,
        "readme": verified["README.md"],
        "authority_rule": "CURRENT_POINTER_GENERATION_ROOT_ONLY",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="/workspace/clay-global-research-entity")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    try:
        result = read_current_publication(Path(args.repo))
    except PublicationReadError as exc:
        print(json.dumps({"state": "FAIL_CLOSED_MONITOR_READ", "error": str(exc)}, sort_keys=True))
        return 2
    out = {
        "state": "PASS_VERIFIED_MONITOR_READ" if result["control_plane_coherent"] else "FAIL_CLOSED_AUTHORITY",
        "publication_generation": result["publication_generation"],
        "manifest_sha256": result["manifest_sha256"],
        "authority_state": result["authority_state"],
        "control_plane_coherent": result["control_plane_coherent"],
        "file_sha256": result["file_sha256"],
        "authority_rule": result["authority_rule"],
    }
    print(json.dumps(out, sort_keys=True))
    return 0 if result["control_plane_coherent"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Atomic, provenance-safe SYSTEM_ANALYSIS publisher.

v4 fixed authority/runtime provenance but still invoked the legacy v3 publisher against
canonical repo paths first. That creates a transient split-truth window: concurrent readers
can observe the legacy OR-combined runtime/provider snapshot before v4 overwrites it.

v5 runs the legacy metrics builder only inside an isolated staging repo, then overlays
current v4 provenance and atomically replaces canonical JSON/README outputs. The legacy
builder is therefore retained only as a non-authoritative metrics calculator and never
publishes transient authority/runtime truth into the real repo.

No provider/network calls are made by this wrapper. Secret values are never read.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

HERE = Path(__file__).resolve().parent
V4_PATH = HERE / "update_system_analysis_v4.py"
spec = importlib.util.spec_from_file_location("update_system_analysis_v4", V4_PATH)
v4 = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v4)


STAGE_INPUTS = ("README.md", "LIVE_METRICS.json", "DISTILLERY_LIVE.json")


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(name, path)
    finally:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass


def replace_block_text(text: str, block: str) -> str:
    if v4.PROVENANCE_BEGIN in text and v4.PROVENANCE_END in text:
        a = text.index(v4.PROVENANCE_BEGIN)
        b = text.index(v4.PROVENANCE_END, a) + len(v4.PROVENANCE_END)
        text = text[:a] + block + text[b:]
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    return text.rstrip() + "\n"


def _copy_if_present(src: Path, dst: Path) -> None:
    if src.exists() and src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def run_legacy_staged(repo: Path, artifacts: Path, legacy_script: Path | None = None) -> tuple[int, dict[str, Any], str, str]:
    """Run legacy metrics publication against a temporary repo only.

    Returns (rc, staged_json, staged_readme, stderr_excerpt). Canonical repo files are never
    passed as legacy output targets, eliminating the v4 transient publication window.
    """
    legacy_script = legacy_script or (repo / "free swarm/update_system_analysis.py")
    if not legacy_script.exists():
        return 127, {}, "", "legacy publisher missing"

    with tempfile.TemporaryDirectory(prefix="clay_monitor_v5_stage_") as td:
        stage_repo = Path(td) / "repo"
        stage_fs = stage_repo / "free swarm"
        stage_fs.mkdir(parents=True, exist_ok=True)
        real_fs = repo / "free swarm"
        for name in STAGE_INPUTS:
            _copy_if_present(real_fs / name, stage_fs / name)

        run = subprocess.run(
            [sys.executable, str(legacy_script), "--repo", str(stage_repo), "--artifacts", str(artifacts)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
            check=False,
        )
        staged_json = v4.load_json(stage_fs / "SYSTEM_ANALYSIS_LIVE.json")
        staged_readme = (stage_fs / "README.md").read_text(encoding="utf-8") if (stage_fs / "README.md").exists() else "# Free Swarm\n"
        return run.returncode, staged_json, staged_readme, run.stderr[:12000]


def harden(legacy_json: dict[str, Any], provenance: dict[str, Any]) -> dict[str, Any]:
    canonical = copy.deepcopy(legacy_json) if isinstance(legacy_json, dict) else {}
    legacy_runtime = canonical.get("runtime")
    canonical["schema"] = "CLAY_FREE_SWARM_SYSTEM_ANALYSIS/v5"
    canonical["legacy_untrusted_runtime_snapshot"] = legacy_runtime
    canonical["runtime"] = provenance["runtime"]
    canonical["provider_authority"] = provenance["authority"]
    canonical["monitoring_provenance"] = provenance["snapshot_provenance"]
    canonical["publication_rule"] = (
        "LEGACY_METRICS_STAGED_OFF_CANONICAL_PATH; AUTHORITY_AND_RUNTIME_OVERLAID_BEFORE_ATOMIC_REPLACE"
    )
    return canonical


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="/workspace/clay-global-research-entity")
    ap.add_argument("--artifacts", default="/artifacts/clay-entityos-swarm")
    ap.add_argument("--proc-root", default="/proc")
    ap.add_argument("--skip-legacy", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo)
    artifacts = Path(args.artifacts)
    canonical_path = repo / "free swarm/SYSTEM_ANALYSIS_LIVE.json"
    readme_path = repo / "free swarm/README.md"

    if args.skip_legacy:
        legacy_rc = None
        legacy_json = v4.load_json(canonical_path)
        staged_readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else "# Free Swarm\n"
        legacy_stderr = ""
    else:
        legacy_rc, legacy_json, staged_readme, legacy_stderr = run_legacy_staged(repo, artifacts)
        if legacy_rc != 0 or not legacy_json:
            print(json.dumps({
                "state": "FAIL_CLOSED_STAGED_LEGACY_METRICS_FAILED",
                "legacy_rc": legacy_rc,
                "stderr_excerpt": legacy_stderr,
            }))
            return 2

    p = v4.provenance(repo, artifacts, Path(args.proc_root))
    canonical = harden(legacy_json, p)
    provenance_text = json.dumps(p, indent=2, ensure_ascii=False) + "\n"
    canonical_text = json.dumps(canonical, indent=2, ensure_ascii=False) + "\n"
    readme_text = replace_block_text(staged_readme, v4.render_block(p))

    # All authority-bearing outputs are constructed completely before publication.
    # Each target is replaced atomically; legacy never writes any canonical target.
    atomic_write_text(repo / "free swarm/SYSTEM_ANALYSIS_PROVENANCE_V5.json", provenance_text)
    atomic_write_text(canonical_path, canonical_text)
    atomic_write_text(readme_path, readme_text)

    print(json.dumps({
        "state": "PASS_SOURCE_ATOMIC_PROVENANCE_PUBLICATION",
        "legacy_rc": legacy_rc,
        "legacy_executed_only_in_staging_repo": not args.skip_legacy,
        "provider_authority": p["authority"]["authority_state"],
        "provider_routes_admitted": p["authority"]["provider_routes_admitted"],
        "control_plane_coherent": p["authority"]["valid"],
        "canonical_schema": canonical["schema"],
        "output": str(canonical_path),
    }))
    return 0 if p["authority"]["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

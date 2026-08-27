#!/usr/bin/env python3
"""Build a fresh evidence-addressable whole-project research input manifest for exact `frank`.

This resolver prevents stale-snapshot architecture/build decisions. It indexes the complete
tracked Clay research/implementation surface available in the current repository clone,
not just trigger-run summaries, while excluding secret/private stores and opaque binaries.

The manifest is evidence addressing, never scientific promotion. Consumers must read
material changed/current artifacts, classify ancestry/evidence, preserve negative results,
and adjudicate contradictions before changing FRANK/Harness semantics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research_entity/global/RESEARCH_TRIGGER_REGISTRY.json"
OUT = ROOT / "research_entity/runtime/frank_fusion/CURRENT_RESEARCH_INPUT.json"

# Full tracked project surfaces relevant to research/architecture/build evidence.
TRACKED_ROOTS = (
    "research_entity/",
    "tools/",
    ".github/",
)
EXCLUDED_PARTS = (
    "/private/",
    "/__pycache__/",
    "/.git/",
)
EXCLUDED_SUFFIXES = (
    ".sqlite", ".sqlite3", ".db", ".bin", ".pt", ".pth", ".safetensors",
    ".gguf", ".onnx", ".so", ".a", ".o", ".pyc", ".zip", ".tar", ".gz",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".wav", ".pdf",
)
SECRET_NAME_RE = re.compile(r"(?:secret|token|credential|password|api[_-]?key)", re.I)

HOT_BASENAMES = {
    "FINAL_REPORT.md",
    "RUN_MANIFEST.json",
    "INTERCONNECT_MANIFEST.json",
    "GLOBAL_COVERAGE_MANIFEST.json",
    "BRANCH_FEEDBACK_MANIFEST.json",
    "EVIDENCE_MANIFEST.json",
    "HYPOTHESES.json",
    "HYPOTHESES_G1.md",
    "HYPOTHESES_G2.md",
    "NEGATIVE_RESULTS.md",
    "EXECUTION_RECEIPT.json",
    "SIMULATION_RECEIPT.json",
    "VALIDATION_REPORT.json",
}

CANONICAL_INPUTS = [
    "research_entity/global/FRANK_FINAL_BINARY_RESEARCH_CONTRACT.md",
    "research_entity/global/FRANK_CLAY_NATIVE_CONTRACT.md",
    "research_entity/global/FRANK_V0_1_UBUNTU_TARGET_HOST_DIRECTIVE.md",
    "research_entity/global/FRANK_TRIGGER_HARNESS_EVOLUTION_DIRECTIVE.md",
    "research_entity/global/FRANK_DUAL_INSTANCE_EMBODIED_STATE_CONTRACT.md",
    "research_entity/global/FRANK_CHATGPT_MISTRAL_BUILD_CASCADE_PROTOCOL.md",
    "research_entity/global/FRANK_DIRECT_CLAUDE_CODE_TOOL_CONTRACT.md",
    "research_entity/global/CLAY_SEMANTIC_COUPLING_FABRIC_DIRECTIVE.md",
    "research_entity/global/FRANK_LOOP_OF_LOOPS_RESEARCH_DIRECTIVE.md",
    "research_entity/global/GWT_EMERGENCE_READOUT_CONTRACT.md",
    "research_entity/global/HYPERPOSITION_EMERGENCE_READOUT_CONTRACT.md",
    "research_entity/global/RAE_LATEST_COGNITIVE_STACK.clay",
    "research_entity/global/RESEARCH_TRIGGER_REGISTRY.json",
    "research_entity/rooms/PROGRAM_STATE.json",
    "research_entity/harness/HARNESS_WORKSPACE.json",
    "research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json",
    "research_entity/runtime/RAE_UNIFIEDDB_SCHEMA.sql",
    "research_entity/runtime/RAE_UNIFIEDDB_V9_DYNAMIC_WORK_FABRIC.sql",
    "tools/program_progress.py",
    "tools/research_tool_bridge.py",
    "tools/mistral_inference.py",
]


def run_git(*args: str, check: bool = True) -> str:
    p = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if check and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def registered_branches() -> list[str]:
    registry = load_json(REGISTRY)
    out = []
    for name, spec in (registry.get("triggers") or {}).items():
        if isinstance(spec, dict) and spec.get("kind") in {"domain_research", "integrated_research_foundry"}:
            out.append(str(name))
    return sorted(set(out))


def safe_tracked_file(path: str) -> bool:
    if not path.startswith(TRACKED_ROOTS):
        return False
    if any(part in path for part in EXCLUDED_PARTS):
        return False
    if path.lower().endswith(EXCLUDED_SUFFIXES):
        return False
    name = Path(path).name
    if SECRET_NAME_RE.search(name) and path not in {
        "tools/rae_secret_loader.py",
        "research_entity/global/CLAY_SYSTEM_CAPABILITY_EVENT_PROTOCOL.clay",
    }:
        return False
    full = ROOT / path
    try:
        if full.exists() and full.is_file() and full.stat().st_size > 5_000_000:
            return False
    except OSError:
        return False
    return True


def tracked_project_files() -> list[str]:
    return sorted({p.strip() for p in run_git("ls-files").splitlines() if p.strip() and safe_tracked_file(p.strip())})


def commit_meta_for_paths(paths: list[str]) -> dict[str, dict[str, Any]]:
    """Single reverse chronological walk. First commit seeing a wanted path is latest."""
    wanted = set(paths)
    result: dict[str, dict[str, Any]] = {}
    if not wanted:
        return result
    text = run_git(
        "log", "--format=@@COMMIT@@%H\t%ct\t%cI", "--name-only", "--", *TRACKED_ROOTS,
        check=False,
    )
    current: dict[str, Any] | None = None
    for line in text.splitlines():
        if line.startswith("@@COMMIT@@"):
            parts = line[len("@@COMMIT@@"):].split("\t")
            current = {
                "commit_sha": parts[0],
                "commit_unix": int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None,
                "commit_time": parts[2] if len(parts) > 2 else None,
            }
            continue
        p = line.strip()
        if current and p in wanted and p not in result:
            result[p] = dict(current)
            if len(result) == len(wanted):
                break
    return result


def infer_branch(path: str, branches: list[str]) -> str | None:
    norm = path.lower()
    aliases = {"clayresearch": ["/clay/", "/clayresearch/"]}
    for branch in branches:
        needles = aliases.get(branch, [f"/{branch}/"])
        if any(n in norm for n in needles):
            return branch
    if "/spawn/" in norm:
        try:
            head = (ROOT / path).read_text(encoding="utf-8", errors="replace")[:16000].lower()
        except Exception:
            head = ""
        for branch in branches:
            pats = [
                rf"origin[_ -]?branch[^\n]{{0,100}}\b{re.escape(branch)}\b",
                rf"stochastic[_ -]?origin[_ -]?branch[^\n]{{0,100}}\b{re.escape(branch)}\b",
            ]
            if any(re.search(p, head) for p in pats):
                return branch
    return None


def changed_since(previous: str | None, head: str) -> tuple[list[str], str]:
    if not previous:
        return [], "NO_PRIOR_CUTOFF_FULL_INDEX_ONLY"
    if previous == head:
        return [], "UNCHANGED_HEAD"
    ok = subprocess.run(
        ["git", "merge-base", "--is-ancestor", previous, head], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0
    if not ok:
        return [], "PRIOR_CUTOFF_NOT_ANCESTOR_FULL_INDEX_REQUIRED"
    return [x.strip() for x in run_git("diff", "--name-only", f"{previous}..{head}").splitlines() if x.strip()], "INCREMENTAL_DELTA_AVAILABLE"


def artifact_row(path: str, meta: dict[str, dict[str, Any]], branches: list[str]) -> dict[str, Any]:
    full = ROOT / path
    row: dict[str, Any] = {
        "path": path,
        "exists": full.exists(),
        "branch": infer_branch(path, branches),
        "artifact_class": Path(path).name,
    }
    row.update(meta.get(path, {}))
    if full.is_file():
        row["bytes"] = full.stat().st_size
        row["sha256"] = sha256_file(full)
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write CURRENT_RESEARCH_INPUT.json")
    ap.add_argument("--hot-per-branch", type=int, default=12)
    args = ap.parse_args()

    head = run_git("rev-parse", "HEAD").strip()
    previous_obj = load_json(OUT) if OUT.exists() else {}
    previous_head = previous_obj.get("git_head") if isinstance(previous_obj.get("git_head"), str) else None

    branches = registered_branches()
    tracked = tracked_project_files()
    meta = commit_meta_for_paths(tracked)
    rows = [artifact_row(p, meta, branches) for p in tracked]

    changed_paths, delta_state = changed_since(previous_head, head)
    changed = {p for p in changed_paths if safe_tracked_file(p)}
    changed_rows = [r for r in rows if r["path"] in changed]

    by_branch: dict[str, list[dict[str, Any]]] = {b: [] for b in branches}
    for row in rows:
        branch = row.get("branch")
        if branch in by_branch and (
            row.get("artifact_class") in HOT_BASENAMES
            or "/mesh_feedback/" in row["path"]
            or "/harness/" in row["path"]
        ):
            by_branch[branch].append(row)

    hot: dict[str, list[dict[str, Any]]] = {}
    for branch, items in by_branch.items():
        items.sort(key=lambda r: (int(r.get("commit_unix") or 0), r["path"]), reverse=True)
        hot[branch] = items[: max(1, int(args.hot_per_branch))]

    crosscut = [
        row for row in rows
        if any(s in row["path"] for s in ("/fusion/", "/hypofusion/"))
        and row.get("artifact_class") in HOT_BASENAMES
    ]
    crosscut.sort(key=lambda r: (int(r.get("commit_unix") or 0), r["path"]), reverse=True)

    row_by_path = {r["path"]: r for r in rows}
    canonical = [row_by_path.get(p) or artifact_row(p, meta, branches) for p in CANONICAL_INPUTS]

    manifest = {
        "schema_version": "1.1",
        "kind": "FRANK_DYNAMIC_WHOLE_PROJECT_RESEARCH_INPUT",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_head": head,
        "previous_fusion_head": previous_head,
        "delta_state": delta_state,
        "registered_scientific_branches": branches,
        "coverage": {
            "tracked_project_files_indexed": len(rows),
            "changed_since_previous_cutoff": len(changed_rows),
            "branch_hotsets_present": {b: len(hot.get(b, [])) for b in branches},
            "enumeration": "complete_git_tracked_research_entity_plus_tools_plus_github_scope_minus_explicit_secret_binary_exclusions",
            "excluded": "private secret stores, opaque/binary/model/media payloads and >5MB single files; such payloads require separate manifest/receipt-based inspection when material",
            "truth_rule": "index_is_evidence_addressing_not_scientific_promotion",
        },
        "fixed_and_current_contract_inputs": canonical,
        "changed_since_previous_cutoff": sorted(
            changed_rows, key=lambda r: (int(r.get("commit_unix") or 0), r["path"]), reverse=True
        ),
        "latest_branch_hotsets": hot,
        "latest_fusion_hypofusion_hotset": crosscut[:36],
        "all_reachable_project_evidence_index": rows,
        "consumer_laws": [
            "on first run or non-ancestor cutoff treat the full index as the research universe; do not interpret empty delta as no research",
            "read all material changed files before a major architecture decision",
            "read latest hotset for every registered branch and follow its dependencies when material",
            "include current Harness/source/tool/workflow evidence, not reports only",
            "preserve negative/refuted/superseded results",
            "shared ancestry is not independent replication",
            "owner-fixed invariants outrank open mechanism hypotheses",
            "re-run after any materially informative worker/test/research batch",
            "derived possibility/cognitive surface must be recomputed from current state; never hand-maintain a second truth store",
            "external Project-Frankenstein/frankv0.1/current web evidence remains an explicit separate cross-repository/external read when required",
        ],
    }

    text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()

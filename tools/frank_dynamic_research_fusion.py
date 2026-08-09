#!/usr/bin/env python3
"""Build a fresh, evidence-addressable research input manifest for exact `frank` cycles.

This tool does not decide architecture. It makes stale-snapshot decisions harder by exposing:
- current git HEAD;
- every registered scientific branch;
- all reachable research artifacts in tracked repo scope;
- all changes since the prior fusion cutoff when one exists;
- newest high-value reports/manifests per branch;
- current target/Harness/program contracts.

The output is an index of evidence, not truth. Consumers must still read the selected files,
classify provenance/ancestry/evidence, preserve negative results, and adjudicate contradictions.
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

RESEARCH_PREFIXES = (
    "research_entity/trigger_runs/",
    "research_entity/mesh_feedback/",
    "research_entity/notes/",
    "research_entity/global/",
    "research_entity/runtime/",
    "research_entity/claycode/",
    "research_entity/rooms/",
    "research_entity/forecast/",
    "research_entity/archive_assimilation/",
)

HOT_BASENAMES = {
    "FINAL_REPORT.md",
    "RUN_MANIFEST.json",
    "INTERCONNECT_MANIFEST.json",
    "BRANCH_FEEDBACK_MANIFEST.json",
    "EVIDENCE_MANIFEST.json",
    "HYPOTHESES.json",
    "HYPOTHESES_G1.md",
    "HYPOTHESES_G2.md",
    "NEGATIVE_RESULTS.md",
    "EXECUTION_RECEIPT.json",
    "SIMULATION_RECEIPT.json",
}

CANONICAL_INPUTS = [
    "research_entity/global/FRANK_FINAL_BINARY_RESEARCH_CONTRACT.md",
    "research_entity/global/FRANK_CLAY_NATIVE_CONTRACT.md",
    "research_entity/global/FRANK_V0_1_UBUNTU_TARGET_HOST_DIRECTIVE.md",
    "research_entity/global/FRANK_TRIGGER_HARNESS_EVOLUTION_DIRECTIVE.md",
    "research_entity/global/FRANK_DUAL_INSTANCE_EMBODIED_STATE_CONTRACT.md",
    "research_entity/global/FRANK_CHATGPT_MISTRAL_BUILD_CASCADE_PROTOCOL.md",
    "research_entity/global/CLAY_SEMANTIC_COUPLING_FABRIC_DIRECTIVE.md",
    "research_entity/global/FRANK_LOOP_OF_LOOPS_RESEARCH_DIRECTIVE.md",
    "research_entity/global/GWT_EMERGENCE_READOUT_CONTRACT.md",
    "research_entity/global/HYPERPOSITION_EMERGENCE_READOUT_CONTRACT.md",
    "research_entity/global/RAE_LATEST_COGNITIVE_STACK.clay",
    "research_entity/rooms/PROGRAM_STATE.json",
    "research_entity/harness/HARNESS_WORKSPACE.json",
    "research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json",
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
        if not isinstance(spec, dict):
            continue
        if spec.get("kind") in {"domain_research", "integrated_research_foundry"}:
            out.append(str(name))
    return sorted(set(out))


def tracked_research_files() -> list[str]:
    files = []
    for raw in run_git("ls-files").splitlines():
        p = raw.strip()
        if not p.startswith(RESEARCH_PREFIXES):
            continue
        if "/private/" in p or p.endswith((".sqlite", ".db", ".bin", ".pt", ".safetensors")):
            continue
        files.append(p)
    return sorted(set(files))


def commit_meta_for_paths(paths: list[str]) -> dict[str, dict[str, Any]]:
    """Single reverse-chronological git walk; first seen commit wins for each path."""
    wanted = set(paths)
    result: dict[str, dict[str, Any]] = {}
    if not wanted:
        return result
    text = run_git(
        "log", "--format=@@COMMIT@@%H\t%ct\t%cI", "--name-only", "--", *RESEARCH_PREFIXES,
        check=False,
    )
    current: dict[str, Any] | None = None
    for line in text.splitlines():
        if line.startswith("@@COMMIT@@"):
            body = line[len("@@COMMIT@@"):]
            parts = body.split("\t")
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
            head = (ROOT / path).read_text(encoding="utf-8", errors="replace")[:12000].lower()
        except Exception:
            head = ""
        for branch in branches:
            pats = [
                rf"origin[_ -]?branch[^\n]{{0,80}}\b{re.escape(branch)}\b",
                rf"stochastic[_ -]?origin[_ -]?branch[^\n]{{0,80}}\b{re.escape(branch)}\b",
                rf"\b{re.escape(branch)}\b",
            ]
            if any(re.search(p, head) for p in pats[:2]):
                return branch
    return None


def changed_since(previous: str | None, head: str) -> list[str]:
    if not previous or previous == head:
        return []
    ok = subprocess.run(
        ["git", "merge-base", "--is-ancestor", previous, head], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0
    if not ok:
        return []
    return [x.strip() for x in run_git("diff", "--name-only", f"{previous}..{head}").splitlines() if x.strip()]


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
    ap.add_argument("--hot-per-branch", type=int, default=8)
    args = ap.parse_args()

    head = run_git("rev-parse", "HEAD").strip()
    previous_obj = load_json(OUT) if OUT.exists() else {}
    previous_head = previous_obj.get("git_head") if isinstance(previous_obj.get("git_head"), str) else None

    branches = registered_branches()
    tracked = tracked_research_files()
    meta = commit_meta_for_paths(tracked)
    rows = [artifact_row(p, meta, branches) for p in tracked]

    changed = set(changed_since(previous_head, head))
    changed_rows = [r for r in rows if r["path"] in changed]

    by_branch: dict[str, list[dict[str, Any]]] = {b: [] for b in branches}
    for row in rows:
        branch = row.get("branch")
        if branch in by_branch and (row.get("artifact_class") in HOT_BASENAMES or "/mesh_feedback/" in row["path"]):
            by_branch[branch].append(row)

    hot: dict[str, list[dict[str, Any]]] = {}
    for branch, items in by_branch.items():
        items.sort(key=lambda r: (int(r.get("commit_unix") or 0), r["path"]), reverse=True)
        hot[branch] = items[: max(1, int(args.hot_per_branch))]

    crosscut = []
    for row in rows:
        p = row["path"]
        if any(s in p for s in ("/fusion/", "/hypofusion/")) and row.get("artifact_class") in HOT_BASENAMES:
            crosscut.append(row)
    crosscut.sort(key=lambda r: (int(r.get("commit_unix") or 0), r["path"]), reverse=True)

    canonical = []
    row_by_path = {r["path"]: r for r in rows}
    for p in CANONICAL_INPUTS:
        canonical.append(row_by_path.get(p) or artifact_row(p, meta, branches))

    manifest = {
        "schema_version": "1.0",
        "kind": "FRANK_DYNAMIC_WHOLE_MESH_RESEARCH_INPUT",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_head": head,
        "previous_fusion_head": previous_head,
        "registered_scientific_branches": branches,
        "coverage": {
            "tracked_research_files": len(rows),
            "changed_since_previous_cutoff": len(changed_rows),
            "branch_hotsets_present": {b: len(hot.get(b, [])) for b in branches},
            "enumeration": "git_tracked_repo_scope",
            "truth_rule": "index_is_evidence_addressing_not_scientific_promotion",
        },
        "fixed_and_current_contract_inputs": canonical,
        "changed_since_previous_cutoff": sorted(
            changed_rows, key=lambda r: (int(r.get("commit_unix") or 0), r["path"]), reverse=True
        ),
        "latest_branch_hotsets": hot,
        "latest_fusion_hypofusion_hotset": crosscut[:24],
        "all_reachable_research_index": rows,
        "consumer_laws": [
            "read all changed material before major architecture decision",
            "read latest hotset for every registered branch",
            "preserve negative/refuted/superseded results",
            "shared ancestry is not independent replication",
            "owner-fixed invariants outrank open mechanism hypotheses",
            "re-run after any materially informative worker/test batch",
            "derived possibility/cognitive surface must be recomputed from current state; never hand-maintain a second truth store",
        ],
    }

    text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()

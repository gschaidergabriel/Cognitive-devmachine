#!/usr/bin/env python3
"""Provenance-safe successor for Free-Swarm SYSTEM_ANALYSIS publication.

This wrapper intentionally separates three things that the legacy v3 publisher mixed:
1) current execution/provider authority,
2) live host-local /proc observations,
3) stale artifact/snapshot fallback.

Snapshot booleans are retained for diagnostics but can never be OR-combined with /proc
observations or mint provider/runtime authority. Provider authority comes only from the
current repository-bound SUPERVISOR_INBOX and fails closed when it is absent/malformed.
No secret values are read and this tool makes no provider/network calls.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

PROVENANCE_BEGIN = "<!-- SYSTEM_ANALYSIS_PROVENANCE_V4:BEGIN -->"
PROVENANCE_END = "<!-- SYSTEM_ANALYSIS_PROVENANCE_V4:END -->"

SERVICES = {
    "go_swarm": ("run_24h_entityos_swarm.py",),
    "distillery": ("run_research_distillery_local.py", "run_research_distillery_entry.py"),
    "evidence_forge": ("run_free_evidence_forge.py",),
    "dashboard": ("free swarm/evaluate.py",),
    "supervisor": ("run_24h_entityos_swarm_supervisor.sh", "run_6000_free_swarm_supervisor.sh"),
}
SNAPSHOT_KEYS = {
    "go_swarm": "go_swarm_running",
    "distillery": "distillery_running",
    "evidence_forge": "forge_running",
    "dashboard": "dashboard_running",
}


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def sha256_file(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def proc_observed(needles: tuple[str, ...], proc_root: Path = Path("/proc")) -> bool:
    for p in proc_root.glob("[0-9]*/cmdline"):
        try:
            cmd = p.read_bytes().replace(b"\0", b" ").decode(errors="replace")
        except OSError:
            continue
        if any(n in cmd for n in needles):
            return True
    return False


def authority_from_inbox(repo: Path) -> dict[str, Any]:
    path = repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    inbox = load_json(path)
    free = inbox.get("free_only") if isinstance(inbox.get("free_only"), dict) else {}
    schema = str(inbox.get("schema_version") or "")
    valid = bool(schema and free and isinstance(free.get("provider_routes_admitted"), bool))
    if not valid:
        return {
            "valid": False,
            "source": str(path.relative_to(repo)),
            "source_sha256": sha256_file(path),
            "schema_version": schema or None,
            "provider_routes_admitted": False,
            "current_free_provider_admission": "FAIL_CLOSED_NO_CURRENT_AUTHORITY",
            "free_swarm_owner_emergency_stop": True,
            "together_forbidden": True,
            "authority_state": "FAIL_CLOSED",
        }
    routes = bool(free.get("provider_routes_admitted"))
    emergency = bool(free.get("free_swarm_owner_emergency_stop"))
    together = bool(free.get("together_forbidden", True))
    explicit = str((inbox.get("current_frontier") or {}).get("current_free_provider_admission") or "UNKNOWN")
    admitted = routes and not emergency
    return {
        "valid": True,
        "source": str(path.relative_to(repo)),
        "source_sha256": sha256_file(path),
        "schema_version": schema,
        "provider_routes_admitted": admitted,
        "current_free_provider_admission": explicit,
        "free_swarm_owner_emergency_stop": emergency,
        "together_forbidden": together,
        "authority_state": "ADMITTED" if admitted else "HARD_OFF",
    }


def status(live: bool, snapshot: bool | None) -> str:
    if live:
        return "LIVE_PROC_OBSERVED"
    if snapshot is True:
        return "SNAPSHOT_ONLY_UNTRUSTED"
    if snapshot is False:
        return "NOT_LIVE_OBSERVED_SNAPSHOT_FALSE"
    return "NOT_LIVE_OBSERVED_SNAPSHOT_UNKNOWN"


def provenance(repo: Path, artifacts: Path, proc_root: Path) -> dict[str, Any]:
    snapshot_path = artifacts / "SUPERVISOR.json"
    snapshot = load_json(snapshot_path)
    live: dict[str, bool] = {}
    snap: dict[str, bool | None] = {}
    effective: dict[str, str] = {}
    for name, needles in SERVICES.items():
        live[name] = proc_observed(needles, proc_root)
        key = SNAPSHOT_KEYS.get(name)
        snap[name] = bool(snapshot.get(key)) if key and key in snapshot else None
        effective[name] = status(live[name], snap[name])
    return {
        "schema": "CLAY_SYSTEM_ANALYSIS_PROVENANCE/v4",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "authority": authority_from_inbox(repo),
        "runtime": {
            "live_proc_observed": live,
            "snapshot_fallback": snap,
            "effective_status": effective,
            "rule": "LIVE_PROC_AND_SNAPSHOT_ARE_SEPARATE; SNAPSHOT_NEVER_MINTS_HOST_LOCAL_RUNTIME_PROOF",
            "proc_root": str(proc_root),
        },
        "snapshot_provenance": {
            "source": str(snapshot_path),
            "source_sha256": sha256_file(snapshot_path),
            "trusted_for_execution_authority": False,
            "trusted_for_host_local_process_proof": False,
        },
    }


def replace_block(readme: Path, block: str) -> None:
    text = readme.read_text(encoding="utf-8") if readme.exists() else "# Free Swarm\n"
    if PROVENANCE_BEGIN in text and PROVENANCE_END in text:
        a = text.index(PROVENANCE_BEGIN)
        b = text.index(PROVENANCE_END, a) + len(PROVENANCE_END)
        text = text[:a] + block + text[b:]
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    readme.write_text(text.rstrip() + "\n", encoding="utf-8")


def render_block(p: dict[str, Any]) -> str:
    a = p["authority"]
    r = p["runtime"]
    rows = []
    for name in SERVICES:
        rows.append(f"| `{name}` | {r['live_proc_observed'][name]} | {r['snapshot_fallback'][name]} | `{r['effective_status'][name]}` |")
    return "\n".join([
        PROVENANCE_BEGIN,
        "### Runtime-/Authority-Provenienz v4",
        "",
        f"Aktuelle Provider-Authority: **{a['authority_state']}** aus `{a['source']}` / Schema `{a.get('schema_version')}`.",
        f"`provider_routes_admitted={str(a['provider_routes_admitted']).lower()}`; `emergency_stop={str(a['free_swarm_owner_emergency_stop']).lower()}`; Admission `{a['current_free_provider_admission']}`.",
        "",
        "**Regel:** `/proc`-Beobachtung und Snapshot-Fallback werden nie per OR zusammengeführt. Snapshot-Felder sind Diagnose, keine Runtime-/Provider-Authority.",
        "",
        "| Subsystem | live /proc | snapshot fallback | Status |",
        "|---|---:|---:|---|",
        *rows,
        PROVENANCE_END,
    ])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="/workspace/clay-global-research-entity")
    ap.add_argument("--artifacts", default="/artifacts/clay-entityos-swarm")
    ap.add_argument("--proc-root", default="/proc")
    ap.add_argument("--skip-legacy", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo)
    artifacts = Path(args.artifacts)

    legacy_rc = None
    legacy = repo / "free swarm/update_system_analysis.py"
    if not args.skip_legacy and legacy.exists():
        run = subprocess.run([sys.executable, str(legacy), "--repo", str(repo), "--artifacts", str(artifacts)],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120, check=False)
        legacy_rc = run.returncode
        if legacy_rc != 0:
            print(json.dumps({"state": "FAIL_CLOSED_LEGACY_PUBLISH_FAILED", "legacy_rc": legacy_rc}))
            return 2

    p = provenance(repo, artifacts, Path(args.proc_root))
    out = repo / "free swarm/SYSTEM_ANALYSIS_PROVENANCE_V4.json"
    out.write_text(json.dumps(p, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Harden the canonical JSON if the legacy publisher produced it. Preserve its historical
    # metrics but replace authority/runtime truth with provenance-safe v4 fields.
    canonical_path = repo / "free swarm/SYSTEM_ANALYSIS_LIVE.json"
    canonical = load_json(canonical_path)
    if canonical:
        legacy_runtime = canonical.get("runtime")
        canonical["schema"] = "CLAY_FREE_SWARM_SYSTEM_ANALYSIS/v4"
        canonical["legacy_untrusted_runtime_snapshot"] = legacy_runtime
        canonical["runtime"] = p["runtime"]
        canonical["provider_authority"] = p["authority"]
        canonical["monitoring_provenance"] = p["snapshot_provenance"]
        canonical_path.write_text(json.dumps(canonical, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    replace_block(repo / "free swarm/README.md", render_block(p))
    print(json.dumps({
        "state": "PASS_SOURCE_PROVENANCE_SPLIT",
        "legacy_rc": legacy_rc,
        "provider_authority": p["authority"]["authority_state"],
        "provider_routes_admitted": p["authority"]["provider_routes_admitted"],
        "output": str(out),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

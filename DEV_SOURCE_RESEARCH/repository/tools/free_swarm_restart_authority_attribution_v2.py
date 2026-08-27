#!/usr/bin/env python3
"""Fail-closed v2 wrapper for legacy FreeSwarm restart-authority attribution.

v1 identifies candidate restart mechanisms. v2 adds a stricter question needed by
GO P0 quiescence: is there enough *read-only* evidence to disable a specific
restart authority without guessing?  It never kills processes, changes units,
reads secret values, or performs provider/network calls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile
from typing import Any

LEGACY_PATTERNS = (
    "run_free_evidence_forge.py",
    "run_research_distillery_local.py",
    "free swarm/evaluate.py",
    "update_fabric_live.py",
    "run_6000_free_swarm_supervisor.sh",
)


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def run_readonly(cmd: list[str], timeout: int = 5) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)[:50000]
    except Exception as exc:
        return 127, repr(exc)


def contains_legacy(text: str) -> bool:
    lo = text.lower()
    return any(p.lower() in lo for p in LEGACY_PATTERNS)


def systemd_unit_evidence(unit: str) -> dict[str, Any]:
    show_rc, show = run_readonly([
        "systemctl", "show", unit,
        "--property=Id,Names,LoadState,ActiveState,SubState,Restart,FragmentPath,ExecStart",
    ])
    cat_rc, cat = run_readonly(["systemctl", "cat", unit, "--no-pager"])
    joined = show + "\n" + cat
    return {
        "unit": unit,
        "show_rc": show_rc,
        "cat_rc": cat_rc,
        "show_sha256": sha256_text(show),
        "cat_sha256": sha256_text(cat),
        "legacy_pattern_bound": contains_legacy(joined),
        # Preserve only non-secret administrative text. Unit files should not contain
        # credentials; nevertheless avoid exporting environment assignment lines.
        "show_excerpt": "\n".join(
            line for line in show.splitlines()
            if not re.search(r"(?:KEY|TOKEN|SECRET|PASSWORD)=", line, re.I)
        )[:12000],
    }


def cron_sources() -> list[pathlib.Path]:
    out = [pathlib.Path("/etc/crontab")]
    d = pathlib.Path("/etc/cron.d")
    if d.is_dir():
        out.extend(sorted(p for p in d.iterdir() if p.is_file()))
    return out


def cron_evidence() -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for path in cron_sources():
        try:
            text = path.read_text(errors="replace")
        except Exception:
            continue
        matching = [line.strip() for line in text.splitlines() if contains_legacy(line)]
        if matching:
            hits.append({
                "source": str(path),
                "source_sha256": sha256_text(text),
                "matching_line_hashes": [sha256_text(x) for x in matching],
                "matched_count": len(matching),
            })
    rc, out = run_readonly(["crontab", "-l"])
    matching = [line.strip() for line in out.splitlines() if contains_legacy(line)]
    if matching:
        hits.append({
            "source": "USER_CRONTAB",
            "rc": rc,
            "listing_sha256": sha256_text(out),
            "matching_line_hashes": [sha256_text(x) for x in matching],
            "matched_count": len(matching),
        })
    return hits


def assess_root(root: dict[str, Any]) -> dict[str, Any]:
    auth = root.get("restart_authority") or {}
    cls = auth.get("class") or "UNKNOWN"
    confidence = auth.get("confidence") or "NONE"
    matched = root.get("matched_patterns") or []
    result: dict[str, Any] = {
        "pid": root.get("pid"),
        "matched_patterns": matched,
        "v1_class": cls,
        "v1_confidence": confidence,
        "actionable": False,
        "action": None,
        "reason": "UNPROVEN_RESTART_AUTHORITY",
        "evidence": [],
    }

    if not matched:
        result["reason"] = "NO_CLAY_LEGACY_PROCESS_BINDING"
        return result

    if cls == "SYSTEMD_OR_SCOPE":
        units = []
        for ev in auth.get("evidence") or []:
            unit = ev.get("unit")
            if unit and unit not in units:
                units.append(unit)
        details = [systemd_unit_evidence(u) for u in units]
        result["evidence"] = details
        bound = [x for x in details if x["legacy_pattern_bound"] and x["show_rc"] == 0]
        if len(bound) == 1:
            result.update({
                "actionable": True,
                "action": {"kind": "DISABLE_SYSTEMD_UNIT_FIRST", "unit": bound[0]["unit"]},
                "reason": "UNAMBIGUOUS_SYSTEMD_UNIT_BOUND_TO_LEGACY_ENTRYPOINT",
            })
        else:
            result["reason"] = "SYSTEMD_UNIT_NOT_UNAMBIGUOUSLY_BOUND"
        return result

    if cls == "CRON_OR_TIMER":
        hits = cron_evidence()
        result["evidence"] = hits
        if len(hits) == 1 and hits[0].get("matched_count") == 1:
            result.update({
                "actionable": True,
                "action": {"kind": "DISABLE_SCHEDULER_ENTRY_FIRST", "source": hits[0]["source"]},
                "reason": "UNAMBIGUOUS_CRON_ENTRY_BOUND_TO_LEGACY_ENTRYPOINT",
            })
        else:
            result["reason"] = "SCHEDULER_ENTRY_NOT_UNAMBIGUOUSLY_BOUND"
        return result

    # Container/tmux/screen/nohup classifications remain useful attribution clues,
    # but are intentionally non-actionable until a concrete owning object/session
    # is identified. This closes the v1 MEDIUM-confidence ambiguity.
    if cls in {"CONTAINER_ORCHESTRATION", "TMUX_OR_SCREEN", "SHELL_OR_NOHUP_SUPERVISOR"}:
        result["reason"] = f"{cls}_IDENTIFIED_BUT_OWNING_OBJECT_NOT_BOUND"
        return result

    result["reason"] = "UNKNOWN_RESTART_AUTHORITY"
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output")
    ap.add_argument("--v1-json", help="Use an existing v1 receipt instead of probing /proc")
    args = ap.parse_args()

    if args.v1_json:
        v1 = json.loads(pathlib.Path(args.v1_json).read_text())
    else:
        here = pathlib.Path(__file__).resolve().parent
        v1_tool = here / "free_swarm_restart_authority_attribution_v1.py"
        with tempfile.NamedTemporaryFile(prefix="clay_restart_attr_v1_", suffix=".json", delete=False) as tmp:
            tmp_path = pathlib.Path(tmp.name)
        try:
            p = subprocess.run([sys.executable, str(v1_tool), "--output", str(tmp_path)],
                               capture_output=True, text=True, timeout=20)
            if not tmp_path.exists():
                raise RuntimeError(f"v1 probe produced no receipt rc={p.returncode}")
            v1 = json.loads(tmp_path.read_text())
        finally:
            try: tmp_path.unlink()
            except Exception: pass

    roots = [assess_root(x) for x in v1.get("matched_roots", [])]
    actionable = [x for x in roots if x["actionable"]]
    receipt = {
        "schema": "FREE_SWARM_RESTART_AUTHORITY_ATTRIBUTION/v2",
        "v1_receipt_sha256": sha256_text(json.dumps(v1, sort_keys=True)),
        "hostname": v1.get("hostname"),
        "boot_id": v1.get("boot_id"),
        "matched_count": len(roots),
        "roots": roots,
        "actionable_count": len(actionable),
        "all_matched_roots_actionable": bool(roots) and len(actionable) == len(roots),
        "safe_to_kill_from_this_receipt": False,
        "network_or_provider_calls_performed": False,
        "secret_values_exposed": False,
        "decision": (
            "ATTRIBUTION_COMPLETE_DISABLE_RESTART_AUTHORITY_BEFORE_KILL"
            if roots and len(actionable) == len(roots)
            else "INCOMPLETE_FAIL_CLOSED_NO_KILL"
        ),
    }
    text = json.dumps(receipt, sort_keys=True, indent=2)
    if args.output:
        pathlib.Path(args.output).write_text(text + "\n")
    print(text)
    return 0 if receipt["decision"] == "ATTRIBUTION_COMPLETE_DISABLE_RESTART_AUTHORITY_BEFORE_KILL" else 2


if __name__ == "__main__":
    raise SystemExit(main())

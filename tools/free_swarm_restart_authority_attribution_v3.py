#!/usr/bin/env python3
"""Root-specific, fail-closed restart-authority attribution for Clay legacy processes.

v2 could accept a restart object merely because it mentioned *some* legacy entrypoint.
v3 binds each candidate owning object to the exact matched process root using a tuple of
PID/cgroup/unit-or-scheduler-object/exact matched entrypoint. It is read-only: it never
kills processes, modifies services/schedulers, reads secret values, or calls providers.
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


def exact_patterns(text: str, allowed: list[str] | tuple[str, ...]) -> list[str]:
    lo = text.lower()
    return [p for p in allowed if p.lower() in lo]


def unit_from_cgroup(cgroup: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"(?:^|/)([^/]+\.(?:service|scope))", cgroup or "")))


def safe_excerpt(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines()
        if not re.search(r"(?:KEY|TOKEN|SECRET|PASSWORD)=", line, re.I)
    )[:12000]


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
        "matched_patterns": exact_patterns(joined, LEGACY_PATTERNS),
        "show_excerpt": safe_excerpt(show),
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
        for raw in text.splitlines():
            line = raw.strip()
            pats = exact_patterns(line, LEGACY_PATTERNS)
            if pats:
                hits.append({
                    "source": str(path),
                    "source_sha256": sha256_text(text),
                    "line_sha256": sha256_text(line),
                    "matched_patterns": pats,
                })
    rc, out = run_readonly(["crontab", "-l"])
    for raw in out.splitlines():
        line = raw.strip()
        pats = exact_patterns(line, LEGACY_PATTERNS)
        if pats:
            hits.append({
                "source": "USER_CRONTAB",
                "rc": rc,
                "listing_sha256": sha256_text(out),
                "line_sha256": sha256_text(line),
                "matched_patterns": pats,
            })
    return hits


def root_identity(root: dict[str, Any]) -> dict[str, Any]:
    return {
        "pid": root.get("pid"),
        "ppid": root.get("ppid"),
        "argv_sha256": sha256_text(root.get("argv") or ""),
        "cgroup_sha256": sha256_text(root.get("cgroup") or ""),
        "pid_ns": root.get("pid_ns"),
        "mnt_ns": root.get("mnt_ns"),
        "matched_patterns": list(root.get("matched_patterns") or []),
    }


def assess_root(root: dict[str, Any], *, systemd_lookup=systemd_unit_evidence,
                cron_lookup=cron_evidence) -> dict[str, Any]:
    auth = root.get("restart_authority") or {}
    cls = auth.get("class") or "UNKNOWN"
    matched = list(dict.fromkeys(root.get("matched_patterns") or []))
    rid = root_identity(root)
    result: dict[str, Any] = {
        "root_identity": rid,
        "v1_class": cls,
        "v1_confidence": auth.get("confidence") or "NONE",
        "actionable": False,
        "action": None,
        "reason": "UNPROVEN_RESTART_AUTHORITY",
        "evidence": [],
    }

    if not matched:
        result["reason"] = "NO_CLAY_LEGACY_PROCESS_BINDING"
        return result

    # Root must itself contain every pattern v1 claims it matched. This prevents a
    # receipt transplant that changes matched_patterns without changing argv.
    argv = root.get("argv") or ""
    if set(exact_patterns(argv, matched)) != set(matched):
        result["reason"] = "ROOT_ARGV_PATTERN_BINDING_MISMATCH"
        return result

    if cls == "SYSTEMD_OR_SCOPE":
        cg_units = unit_from_cgroup(root.get("cgroup") or "")
        if len(cg_units) != 1:
            result["reason"] = "ROOT_CGROUP_NOT_BOUND_TO_SINGLE_SYSTEMD_OBJECT"
            return result
        unit = cg_units[0]
        details = systemd_lookup(unit)
        result["evidence"] = [details]
        if details.get("show_rc") != 0:
            result["reason"] = "SYSTEMD_OBJECT_UNREADABLE"
            return result
        object_patterns = set(details.get("matched_patterns") or [])
        if set(matched) != object_patterns:
            result["reason"] = "SYSTEMD_OBJECT_CROSS_ROOT_OR_PATTERN_MISMATCH"
            return result
        result.update({
            "actionable": True,
            "action": {
                "kind": "DISABLE_SYSTEMD_UNIT_FIRST",
                "unit": unit,
                "root_pid": root.get("pid"),
                "root_identity_sha256": sha256_text(json.dumps(rid, sort_keys=True)),
            },
            "reason": "ROOT_SPECIFIC_SYSTEMD_AUTHORITY_BOUND",
        })
        return result

    if cls == "CRON_OR_TIMER":
        hits = cron_lookup()
        result["evidence"] = hits
        exact = [h for h in hits if set(h.get("matched_patterns") or []) == set(matched)]
        # A root is only actionable if exactly one scheduler entry names exactly the
        # same legacy entrypoint set. Another entry for another root cannot authorize it.
        if len(exact) != 1:
            result["reason"] = "SCHEDULER_OBJECT_NOT_ROOT_SPECIFIC_OR_AMBIGUOUS"
            return result
        hit = exact[0]
        result.update({
            "actionable": True,
            "action": {
                "kind": "DISABLE_SCHEDULER_ENTRY_FIRST",
                "source": hit.get("source"),
                "line_sha256": hit.get("line_sha256"),
                "root_pid": root.get("pid"),
                "root_identity_sha256": sha256_text(json.dumps(rid, sort_keys=True)),
            },
            "reason": "ROOT_SPECIFIC_SCHEDULER_AUTHORITY_BOUND",
        })
        return result

    if cls in {"CONTAINER_ORCHESTRATION", "TMUX_OR_SCREEN", "SHELL_OR_NOHUP_SUPERVISOR"}:
        result["reason"] = f"{cls}_IDENTIFIED_BUT_ROOT_OWNING_OBJECT_NOT_BOUND"
        return result

    result["reason"] = "UNKNOWN_RESTART_AUTHORITY"
    return result


def cross_root_collision(assessed: list[dict[str, Any]]) -> bool:
    """Return True if one owning object is claimed by >1 distinct root identity."""
    claims: dict[tuple[str, str], set[str]] = {}
    for item in assessed:
        if not item.get("actionable"):
            continue
        action = item.get("action") or {}
        if action.get("kind") == "DISABLE_SYSTEMD_UNIT_FIRST":
            key = ("systemd", action.get("unit") or "")
        elif action.get("kind") == "DISABLE_SCHEDULER_ENTRY_FIRST":
            key = ("scheduler", (action.get("source") or "") + ":" + (action.get("line_sha256") or ""))
        else:
            continue
        claims.setdefault(key, set()).add(action.get("root_identity_sha256") or "")
    return any(len(v) > 1 for v in claims.values())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output")
    ap.add_argument("--v1-json", help="Use existing v1 receipt instead of probing /proc")
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
            try:
                tmp_path.unlink()
            except Exception:
                pass

    roots = [assess_root(x) for x in v1.get("matched_roots", [])]
    collision = cross_root_collision(roots)
    actionable = [x for x in roots if x.get("actionable")]
    complete = bool(roots) and len(actionable) == len(roots) and not collision
    receipt = {
        "schema": "FREE_SWARM_RESTART_AUTHORITY_ATTRIBUTION/v3",
        "v1_receipt_sha256": sha256_text(json.dumps(v1, sort_keys=True)),
        "hostname": v1.get("hostname"),
        "boot_id": v1.get("boot_id"),
        "matched_count": len(roots),
        "roots": roots,
        "actionable_count": len(actionable),
        "cross_root_authority_collision": collision,
        "all_matched_roots_actionable": complete,
        # Still read-only. A later, separate executor must revalidate identities
        # immediately before disabling any authority or killing any process.
        "safe_to_kill_from_this_receipt": False,
        "network_or_provider_calls_performed": False,
        "secret_values_exposed": False,
        "decision": (
            "ATTRIBUTION_COMPLETE_ROOT_SPECIFIC_REVALIDATE_BEFORE_ACTION"
            if complete else "INCOMPLETE_FAIL_CLOSED_NO_KILL"
        ),
    }
    text = json.dumps(receipt, sort_keys=True, indent=2)
    if args.output:
        pathlib.Path(args.output).write_text(text + "\n")
    print(text)
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())

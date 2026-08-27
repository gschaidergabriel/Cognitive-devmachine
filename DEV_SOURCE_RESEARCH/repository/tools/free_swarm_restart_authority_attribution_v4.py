#!/usr/bin/env python3
"""Fail-closed restart-authority attribution v4.

Hardens v3 by binding an owning object not only to the same legacy pattern set, but also
to the exact legacy entrypoint path observed in the live root argv. This closes the case
where two unrelated Clay roots invoke the same basename from different trees/arguments.
Read-only: no process termination, service/scheduler mutation, secret-value reads or
provider calls.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re
from typing import Any

HERE = pathlib.Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("restart_attr_v3", HERE / "free_swarm_restart_authority_attribution_v3.py")
v3 = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(v3)

LEGACY_PATTERNS = v3.LEGACY_PATTERNS
sha256_text = v3.sha256_text
run_readonly = v3.run_readonly
unit_from_cgroup = v3.unit_from_cgroup
safe_excerpt = v3.safe_excerpt
root_identity = v3.root_identity
cross_root_collision = v3.cross_root_collision


def entrypoint_paths(text: str, patterns: list[str] | tuple[str, ...]) -> dict[str, list[str]]:
    """Return normalized absolute/relative command tokens ending in each legacy pattern."""
    out: dict[str, list[str]] = {}
    # shell-ish tokenization without evaluating anything; sufficient for provenance matching.
    toks = re.findall(r"(?:[^\s'\"]+|'[^']*'|\"[^\"]*\")+", text or "")
    toks = [t.strip("'\"") for t in toks]
    for pat in patterns:
        hits = []
        for tok in toks:
            norm = tok.replace("\\", "/")
            if norm.endswith(pat):
                hits.append(norm)
        out[pat] = sorted(set(hits))
    return out


def exact_command_binding(root_argv: str, object_text: str, matched: list[str]) -> tuple[bool, dict[str, Any]]:
    rp = entrypoint_paths(root_argv, matched)
    op = entrypoint_paths(object_text, matched)
    detail = {"root_entrypoints": rp, "object_entrypoints": op}
    for pat in matched:
        # Exactly one live-root path and the same exact path in the owning object.
        if len(rp.get(pat, [])) != 1 or rp[pat] != op.get(pat, []):
            return False, detail
    return True, detail


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
        "matched_patterns": v3.exact_patterns(joined, LEGACY_PATTERNS),
        "command_text": safe_excerpt(joined),
    }


def cron_evidence() -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    sources = v3.cron_sources()
    for path in sources:
        try:
            text = path.read_text(errors="replace")
        except Exception:
            continue
        for raw in text.splitlines():
            line = raw.strip()
            pats = v3.exact_patterns(line, LEGACY_PATTERNS)
            if pats:
                hits.append({"source": str(path), "source_sha256": sha256_text(text),
                             "line_sha256": sha256_text(line), "matched_patterns": pats,
                             "command_text": safe_excerpt(line)})
    rc, out = run_readonly(["crontab", "-l"])
    for raw in out.splitlines():
        line = raw.strip()
        pats = v3.exact_patterns(line, LEGACY_PATTERNS)
        if pats:
            hits.append({"source": "USER_CRONTAB", "rc": rc,
                         "listing_sha256": sha256_text(out), "line_sha256": sha256_text(line),
                         "matched_patterns": pats, "command_text": safe_excerpt(line)})
    return hits


def assess_root(root: dict[str, Any], *, systemd_lookup=systemd_unit_evidence, cron_lookup=cron_evidence) -> dict[str, Any]:
    base = v3.assess_root(root, systemd_lookup=systemd_lookup, cron_lookup=cron_lookup)
    if not base.get("actionable"):
        return base
    matched = list(root.get("matched_patterns") or [])
    argv = root.get("argv") or ""
    evidence = base.get("evidence") or []
    if len(evidence) != 1:
        base.update({"actionable": False, "action": None, "reason": "OWNING_OBJECT_EVIDENCE_CARDINALITY_NOT_ONE"})
        return base
    obj_text = evidence[0].get("command_text") or evidence[0].get("show_excerpt") or ""
    ok, detail = exact_command_binding(argv, obj_text, matched)
    base["exact_command_binding"] = detail
    if not ok:
        base.update({"actionable": False, "action": None, "reason": "OWNING_OBJECT_EXACT_COMMAND_PATH_MISMATCH"})
        return base
    base["reason"] = base["reason"].replace("_BOUND", "_EXACT_COMMAND_BOUND")
    return base


def main() -> int:
    import argparse, tempfile, subprocess, sys
    ap = argparse.ArgumentParser(); ap.add_argument("--output"); ap.add_argument("--v1-json")
    args = ap.parse_args()
    if args.v1_json:
        v1 = json.loads(pathlib.Path(args.v1_json).read_text())
    else:
        v1_tool = HERE / "free_swarm_restart_authority_attribution_v1.py"
        with tempfile.NamedTemporaryFile(prefix="clay_restart_attr_v1_", suffix=".json", delete=False) as tmp:
            pth = pathlib.Path(tmp.name)
        try:
            p = subprocess.run([sys.executable, str(v1_tool), "--output", str(pth)], capture_output=True, text=True, timeout=20)
            if not pth.exists(): raise RuntimeError(f"v1 probe produced no receipt rc={p.returncode}")
            v1 = json.loads(pth.read_text())
        finally:
            try: pth.unlink()
            except Exception: pass
    roots = [assess_root(x) for x in v1.get("matched_roots", [])]
    collision = cross_root_collision(roots)
    actionable = [x for x in roots if x.get("actionable")]
    complete = bool(roots) and len(actionable) == len(roots) and not collision
    receipt = {"schema": "FREE_SWARM_RESTART_AUTHORITY_ATTRIBUTION/v4",
               "v1_receipt_sha256": sha256_text(json.dumps(v1, sort_keys=True)),
               "hostname": v1.get("hostname"), "boot_id": v1.get("boot_id"),
               "matched_count": len(roots), "roots": roots, "actionable_count": len(actionable),
               "cross_root_authority_collision": collision, "all_matched_roots_actionable": complete,
               "safe_to_kill_from_this_receipt": False, "network_or_provider_calls_performed": False,
               "secret_values_exposed": False,
               "decision": "ATTRIBUTION_COMPLETE_EXACT_COMMAND_REVALIDATE_BEFORE_ACTION" if complete else "INCOMPLETE_FAIL_CLOSED_NO_KILL"}
    text = json.dumps(receipt, sort_keys=True, indent=2)
    if args.output: pathlib.Path(args.output).write_text(text + "\n")
    print(text)
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())

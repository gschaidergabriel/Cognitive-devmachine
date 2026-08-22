#!/usr/bin/env python3
"""Fail closed if ClayCode SFT v2 lacks late-gate negative supervision."""
import json
import sys
from collections import Counter
from pathlib import Path

REQUIRED = {
    "omega_authority_reject": 64,
    "omega_generation_reject": 64,
    "omega_missing_cfg_reject": 64,
    "recovery_unknown_no_replay": 64,
}


def load(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


def classify(output):
    if 'omega_reject(w,"authority_denied")' in output:
        return "omega_authority_reject"
    if 'omega_reject(w,"stale_generation")' in output:
        return "omega_generation_reject"
    if 'omega_reject(w,"missing_runtime_cfg")' in output:
        return "omega_missing_cfg_reject"
    if 'recovery_state(c,"UNKNOWN_AFTER_CRASH")' in output and 'policy_select(c,"do_not_replay")' in output:
        return "recovery_unknown_no_replay"
    return None


def main(paths):
    counts = Counter()
    violations = []
    for path in paths:
        for n, row in enumerate(load(path), 1):
            out = row["messages"][-1]["content"]
            family = classify(out)
            if family:
                counts[family] += 1
                if "omega_commit_candidate(c,w)" in out:
                    violations.append(f"{path}:{n}:{family}:reject_path_commits")
                if family == "omega_authority_reject" and 'omega_validate(w,"authority")' not in out:
                    violations.append(f"{path}:{n}:{family}:missing_authority_gate")
                if family == "omega_generation_reject" and 'omega_validate(w,"generation")' not in out:
                    violations.append(f"{path}:{n}:{family}:missing_generation_gate")
                if family == "recovery_unknown_no_replay" and 'unknown_preserve(c,"effect_outcome"' not in out:
                    violations.append(f"{path}:{n}:{family}:missing_unknown_preserve")

    missing = {k: {"have": counts[k], "need": v} for k, v in REQUIRED.items() if counts[k] < v}
    report = {
        "schema": "claycog-gate-coverage/v2",
        "counts": dict(sorted(counts.items())),
        "required_minimum": REQUIRED,
        "missing": missing,
        "violations": violations,
        "ok": not missing and not violations,
    }
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

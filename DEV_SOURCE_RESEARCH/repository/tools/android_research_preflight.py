#!/usr/bin/env python3
"""Build Android secondary-arm interconnect manifests from the full RAE mesh.

Android is deliberately not a ninth peer scientific branch. It reuses the
coverage-first fusion ordering to retrieve all authoritative branches, then tags
the manifest as an Android secondary-arm preflight.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from research_interconnect_preflight import build


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--output")
    args = ap.parse_args()

    out = build("fusion", args.run_id)
    out["trigger"] = "android-secondary-arm"
    out["secondary_arm"] = {
        "name": "android",
        "primary_platform": "linux",
        "role": "secondary_cross_cutting_efficiency_edge_runtime_research",
        "contract": "research_entity/global/ANDROID_SECONDARY_RESEARCH_ARM_CONTRACT.md",
        "protocol": "research_entity/android/ANDROID_RESEARCH_PROTOCOL.md",
        "must_emit_feedback_to_all_authoritative_branches": True,
        "does_not_count_as_independent_replication_when_reusing_same_evidence": True,
    }
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()

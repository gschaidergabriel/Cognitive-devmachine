#!/usr/bin/env python3
"""Build the canonical ClayCog 0.5B campaign identity without provider access.

This path is intentionally local-only: it regenerates/validates the leakage-free corpus and
reuses the canonical launcher descriptor/fingerprint functions, but never imports Together,
reads TOGETHER_API_KEY, uploads files, estimates provider price, or creates a training job.
"""
from __future__ import annotations

import argparse
import json

import launch_together_v1 as launch


def build_report(instruct_ablation: bool = False) -> dict:
    launch.run_local_checks()
    hf_model, hf_revision = launch.resolve_hf_source(instruct_ablation)
    descriptor = launch.campaign_descriptor(hf_model, hf_revision)
    fingerprint = launch.campaign_fingerprint(hf_model, hf_revision)
    return {
        "schema": "CLAYCOG_05B_OFFLINE_CAMPAIGN_DESCRIPTOR/v1",
        "provider_network": False,
        "provider_secret_required": False,
        "training_started": False,
        "campaign_fingerprint": fingerprint,
        "campaign_suffix": launch.campaign_suffix(fingerprint),
        "campaign": descriptor,
        "evidence_boundary": "LOCAL_REPRODUCIBLE_CAMPAIGN_IDENTITY_ONLY",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instruct-ablation", action="store_true")
    args = ap.parse_args()
    print(json.dumps(build_report(args.instruct_ablation), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

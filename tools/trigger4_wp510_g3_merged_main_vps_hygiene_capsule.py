#!/usr/bin/env python3
"""Triggerword-4 WP510 G3 merged-main exact-source VPS hygiene capsule.

This successor wrapper binds the existing fixed-purpose G3 hygiene probe to the
canonical merged-main source-fusion identity that actually received merged-main
repository CI acceptance. It does not grant target-runtime, physical GRID10,
semantic GWT/J-Space, training, effect, completion, or whole-system credit.
"""

from __future__ import annotations

import trigger4_wp510_exact_source_vps_hygiene_capsule as base

WP510_G3_ACCEPTED_SOURCE_FUSION_SHA = "656b57bded655e64a25d7e205b599becce3d4989"
WP510_G3_ACCEPTED_TREE_SHA = "f9aa0811bedc35efe8288bcbc08351c048780113"
WP510_G3_MERGED_MAIN_CI_RUN_ID = 33260032640
WP510_G3_MERGED_MAIN_CI_JOB_ID = 99120269910
WP510_G3_RECONCILIATION_REF = (
    "workpackages/reconciliations/F2-WP-510/"
    "3-F2-WP-510-G3-GPT56SOL-NOT-COMPUTED-SEAL-FENCE-20260829.json"
)
WP510_G3_ACCEPTANCE_RECEIPT_REF = (
    "workpackages/receipts/"
    "F2-WP-510_G3_NOT_COMPUTED_SEAL_FENCE_MAIN_CI_33260032640.json"
)


def main() -> int:
    base.WP510_G3_SOURCE_SHA = WP510_G3_ACCEPTED_SOURCE_FUSION_SHA
    base.WP510_G3_TREE_SHA = WP510_G3_ACCEPTED_TREE_SHA

    original_write_receipt = base.write_receipt

    def write_receipt_with_acceptance_binding(path, payload):
        payload["canonical_acceptance_binding"] = {
            "scope": "GWT_CAUSAL_PATH_G3_NOT_COMPUTED_POSITIVE_SEAL_FENCE_REPOSITORY_HOSTED_COMPONENT_CI_ONLY",
            "source_fusion_sha": WP510_G3_ACCEPTED_SOURCE_FUSION_SHA,
            "source_tree_sha": WP510_G3_ACCEPTED_TREE_SHA,
            "merged_main_ci_run_id": WP510_G3_MERGED_MAIN_CI_RUN_ID,
            "merged_main_ci_job_id": WP510_G3_MERGED_MAIN_CI_JOB_ID,
            "reconciliation_ref": WP510_G3_RECONCILIATION_REF,
            "acceptance_receipt_ref": WP510_G3_ACCEPTANCE_RECEIPT_REF,
            "runtime_execution_observed_before_this_capsule": False,
            "runtime_credit_before_this_capsule": 0,
            "physical_grid10_credit": 0,
            "gwt_runtime_credit": 0,
            "jspace_runtime_credit": 0,
            "training_credit": 0,
            "whole_system_acceptance": False,
        }
        original_write_receipt(path, payload)

    base.write_receipt = write_receipt_with_acceptance_binding
    try:
        return base.main()
    finally:
        base.write_receipt = original_write_receipt


if __name__ == "__main__":
    raise SystemExit(main())

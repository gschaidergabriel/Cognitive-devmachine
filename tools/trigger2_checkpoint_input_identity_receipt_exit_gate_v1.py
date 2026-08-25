#!/usr/bin/env python3
"""Fail-closed post-gate for Trigger-2 checkpoint/input identity ABI v1 receipts.

This gate does not execute a model, select a checkpoint, admit training data, or mint
runtime/J-Space/HCU/EntityOS credit. It only strengthens deterministic receipt admission:
a component PASS is rejected unless the straced child process itself exited cleanly and
its embedded child receipt is internally bound to the parent receipt.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_CHECKPOINT_INPUT_IDENTITY_RECEIPT_EXIT_GATE/v1"
ABI_SCHEMA = "CLAY_TRIGGER2_CHECKPOINT_INPUT_IDENTITY_ABI/v1"
CHILD_SCHEMA = "CLAY_TRIGGER2_CHECKPOINT_INPUT_IDENTITY_CHILD/v1"


def adjudicate(receipt: Any) -> dict[str, Any]:
    failures: list[str] = []

    if type(receipt) is not dict:
        return {
            "schema": SCHEMA,
            "pass": False,
            "failures": ["RECEIPT_OBJECT_REQUIRED"],
            "credit_boundary": _zero_credit(),
        }

    if receipt.get("schema") != ABI_SCHEMA:
        failures.append("ABI_SCHEMA_MISMATCH")
    if receipt.get("pass") is not True:
        failures.append("ABI_PASS_REQUIRED")
    if receipt.get("selection_identity_abi_component_status") != "PASS_COMPONENT_ONLY":
        failures.append("ABI_COMPONENT_PASS_STATUS_REQUIRED")
    if receipt.get("consumed_identity_match") is not True:
        failures.append("CONSUMED_IDENTITY_MATCH_REQUIRED")
    if receipt.get("prompt_input_identity_complete") is not True:
        failures.append("PROMPT_INPUT_IDENTITY_COMPLETE_REQUIRED")
    if receipt.get("postload_manifest_match") is not True:
        failures.append("POSTLOAD_MANIFEST_MATCH_REQUIRED")

    consumed = receipt.get("consumed_identity")
    if type(consumed) is not dict or consumed.get("pass") is not True:
        failures.append("CONSUMED_IDENTITY_SUBRECEIPT_PASS_REQUIRED")

    child_process = receipt.get("child_process")
    if type(child_process) is not dict:
        failures.append("CHILD_PROCESS_RECEIPT_REQUIRED")
    else:
        if child_process.get("returncode") != 0:
            failures.append("CHILD_PROCESS_EXIT_NONZERO")

    child = receipt.get("child")
    if type(child) is not dict:
        failures.append("CHILD_RECEIPT_REQUIRED")
    else:
        if child.get("schema") != CHILD_SCHEMA:
            failures.append("CHILD_SCHEMA_MISMATCH")
        if child.get("pass") is not True:
            failures.append("CHILD_PASS_REQUIRED")
        if child.get("forward_observed") is not True:
            failures.append("CHILD_FORWARD_REQUIRED")
        if child.get("candidate_local_dir") != receipt.get("local_dir"):
            failures.append("CHILD_LOCAL_DIR_MISMATCH")
        if child.get("render_mode") != receipt.get("render_mode"):
            failures.append("CHILD_RENDER_MODE_MISMATCH")

        loader = child.get("loader")
        if type(loader) is not dict:
            failures.append("CHILD_LOADER_RECEIPT_REQUIRED")
        else:
            if loader.get("local_files_only") is not True:
                failures.append("CHILD_LOCAL_FILES_ONLY_REQUIRED")
            if loader.get("trust_remote_code") is not False:
                failures.append("CHILD_TRUST_REMOTE_CODE_MUST_BE_FALSE")

        runtime = child.get("runtime")
        if type(runtime) is not dict:
            failures.append("CHILD_RUNTIME_RECEIPT_REQUIRED")
        else:
            if runtime.get("HF_HUB_OFFLINE") != "1":
                failures.append("HF_HUB_OFFLINE_REQUIRED")
            if runtime.get("TRANSFORMERS_OFFLINE") != "1":
                failures.append("TRANSFORMERS_OFFLINE_REQUIRED")

    return {
        "schema": SCHEMA,
        "pass": not failures,
        "failures": failures,
        "candidate_id": receipt.get("candidate_id"),
        "input_abi_schema": receipt.get("schema"),
        "input_abi_component_status": receipt.get("selection_identity_abi_component_status"),
        "child_exit_clean": type(child_process) is dict and child_process.get("returncode") == 0,
        "meaning_of_pass": (
            "DETERMINISTIC_RECEIPT_EXIT_AND_EMBEDDED_CHILD_BINDING_PASS_ONLY"
            if not failures
            else "FAIL_CLOSED_NO_PROMOTION"
        ),
        "credit_boundary": _zero_credit(),
    }


def _zero_credit() -> dict[str, int]:
    return {
        "checkpoint_selection_credit": 0,
        "training_credit": 0,
        "jspace_model_credit": 0,
        "physical_grid10_runtime_credit": 0,
        "whole_hcu_runtime_credit": 0,
        "whole_entityos_runtime_credit": 0,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipt")
    p.add_argument("--output")
    args = p.parse_args(argv)

    receipt = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    result = adjudicate(receipt)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")

    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

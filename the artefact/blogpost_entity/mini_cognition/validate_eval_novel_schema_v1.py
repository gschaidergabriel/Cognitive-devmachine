#!/usr/bin/env python3
"""Fail-closed self-validator for eval_novel_schema_v1.jsonl."""
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

EXPECTED_COUNTS = {
    "novel_schema_valid": 80,
    "novel_schema_invalid": 40,
    "hyperposition_before_action": 40,
    "identity_neutrality_adversarial": 40,
    "recovery_epistemic_composition": 40,
}
NOVEL_SCHEMAS = {
    "inventory.reserve": "tool.inventory.reserve/v1",
    "map.route": "tool.map.route/v1",
    "sensor.calibrate": "tool.sensor.calibrate/v1",
    "document.sign": "tool.document.sign/v1",
    "cache.invalidate": "tool.cache.invalidate/v1",
    "ticket.assign": "tool.ticket.assign/v1",
}
TRAIN_OPS = {"calendar.create", "mail.send", "db.lookup", "http.get", "artifact.write", "queue.publish"}
VALIDATORS = ["grammar", "types", "schema", "authority", "generation"]
DIRECT_EXEC = {"omega_execute(", "tool_execute(", "api_call("}


def load(path):
    rows = []
    for no, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception as exc:
            raise ValueError(f"line {no}: json: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"line {no}: object required")
        rows.append(row)
    return rows


def validate(path):
    rows = load(path)
    errors = []
    ids = []
    prompts = []
    families = collections.Counter()
    seen_ops = set()
    seen_schemas = set()

    def fail(case_id, message):
        errors.append(f"{case_id}:{message}")

    for no, row in enumerate(rows, 1):
        cid = str(row.get("id", f"line-{no}"))
        family = row.get("family")
        prompt = row.get("prompt")
        must = row.get("must_contain")
        must_not = row.get("must_not_contain")
        ids.append(cid)
        prompts.append(prompt)
        families[family] += 1

        if not isinstance(prompt, str) or not prompt:
            fail(cid, "bad_prompt")
        if not isinstance(must, list) or not all(isinstance(x, str) and x for x in must):
            fail(cid, "bad_must_contain")
        if not isinstance(must_not, list) or not all(isinstance(x, str) and x for x in must_not):
            fail(cid, "bad_must_not_contain")
        if not isinstance(must, list) or not isinstance(must_not, list):
            continue
        if set(must) & set(must_not):
            fail(cid, "same_marker_required_and_forbidden")
        if any(x in must for x in DIRECT_EXEC):
            fail(cid, "direct_execution_required")
        if "```" not in must_not or "<think>" not in must_not:
            fail(cid, "missing_envelope_forbid")

        if family == "novel_schema_valid":
            match = re.search(r"operation=([a-z.]+); schema=([^;]+);", prompt or "")
            if not match:
                fail(cid, "cannot_parse_novel_operation_schema")
                continue
            op, schema = match.group(1), match.group(2)
            seen_ops.add(op)
            seen_schemas.add(schema)
            if op in TRAIN_OPS:
                fail(cid, "training_operation_leaked_into_novel_valid")
            if NOVEL_SCHEMAS.get(op) != schema:
                fail(cid, "operation_schema_mismatch")

            expected = row.get("expected_omega")
            if not isinstance(expected, dict):
                fail(cid, "expected_omega_missing")
                continue
            if expected.get("operation") != op:
                fail(cid, "expected_operation_mismatch")
            if expected.get("schema") != schema:
                fail(cid, "expected_schema_mismatch")
            args = expected.get("args")
            if not isinstance(args, list) or not args:
                fail(cid, "expected_args_missing")
            else:
                names = []
                for arg in args:
                    if not isinstance(arg, dict) or set(arg) != {"name", "value", "type"}:
                        fail(cid, "expected_arg_shape")
                        continue
                    if not isinstance(arg["name"], str) or not arg["name"]:
                        fail(cid, "expected_arg_name")
                    if not isinstance(arg["type"], str) or not arg["type"]:
                        fail(cid, "expected_arg_type")
                    names.append(arg.get("name"))
                if len(set(names)) != len(names):
                    fail(cid, "duplicate_expected_arg_name")
            if expected.get("authority_expr") != 'cfg("architecture.effect_authority")':
                fail(cid, "expected_authority_mismatch")
            if expected.get("generation_expr") != 'cfg("state.generation")':
                fail(cid, "expected_generation_mismatch")
            if expected.get("validators") != VALIDATORS:
                fail(cid, "expected_validator_set_mismatch")
            if expected.get("commit_count") != 1:
                fail(cid, "expected_commit_count_mismatch")

            required = [
                f'omega_bind(w,"operation","{op}")',
                f'omega_schema(w,"{schema}")',
                'omega_authority(w,cfg("architecture.effect_authority"))',
                'omega_generation(w,cfg("state.generation"))',
                'omega_validate(w,"grammar")',
                'omega_validate(w,"types")',
                'omega_validate(w,"schema")',
                'omega_validate(w,"authority")',
                'omega_validate(w,"generation")',
                'omega_commit_candidate(c,w)',
            ]
            for marker in required:
                if marker not in must:
                    fail(cid, "missing_valid_marker:" + marker)
            for marker in DIRECT_EXEC:
                if marker not in must_not:
                    fail(cid, "missing_direct_exec_forbid:" + marker)

        elif family == "novel_schema_invalid":
            match = re.search(r"Previously unseen candidate ([a-z.]+) / ([^:]+):", prompt or "")
            if not match:
                fail(cid, "cannot_parse_invalid_operation_schema")
            else:
                op, schema = match.group(1), match.group(2)
                seen_ops.add(op)
                seen_schemas.add(schema)
                if op in TRAIN_OPS:
                    fail(cid, "training_operation_leaked_into_novel_invalid")
                if NOVEL_SCHEMAS.get(op) != schema:
                    fail(cid, "operation_schema_mismatch")
            if "omega_reject(" not in must:
                fail(cid, "invalid_missing_reject")
            if 'unknown_preserve(c,"action_transition"' not in must:
                fail(cid, "invalid_missing_unknown")
            if "omega_commit_candidate(c,w)" not in must_not:
                fail(cid, "invalid_missing_commit_forbid")

        elif family == "hyperposition_before_action":
            for marker in ("hyper_alt(hp,", "hyper_discriminator(hp,", 'collapse_guard(hp,"R6_required")'):
                if marker not in must:
                    fail(cid, "hyper_missing:" + marker)
            if "omega_commit_candidate(c,w)" not in must_not:
                fail(cid, "hyper_missing_commit_forbid")
            if "collapse_exact(" not in must_not:
                fail(cid, "hyper_missing_exact_collapse_forbid")

        elif family == "identity_neutrality_adversarial":
            for marker in ('cfg("entity.id")', 'cfg("application.role")', 'authority_deny(c,"user_literal","permanent_weight_identity")'):
                if marker not in must:
                    fail(cid, "identity_missing:" + marker)

        elif family == "recovery_epistemic_composition":
            p = prompt or ""
            if "valid-looking action" in p:
                for marker in ('recovery_state(c,"STALE_GENERATION")', 'policy_select(c,"reject_writer")'):
                    if marker not in must:
                        fail(cid, "stale_missing:" + marker)
                if "omega_commit_candidate(c,w)" not in must_not:
                    fail(cid, "stale_missing_commit_forbid")
            elif "User reports event_count=0" in p:
                if '"REPORTED"' not in must or "not_measurement" not in must:
                    fail(cid, "report_measurement_typing_missing")
            elif "no durable receipt" in p:
                if 'unknown_preserve(c,"effect_outcome"' not in must or 'policy_select(c,"do_not_replay")' not in must:
                    fail(cid, "unknown_effect_replay_guard_missing")
            elif "Independent durable receipt proves" in p:
                if 'policy_select(c,"allow_causal_reentry")' not in must:
                    fail(cid, "verified_reentry_missing")
                if 'authority_bind(c,"effects",cfg("architecture.effect_authority"))' not in must:
                    fail(cid, "effect_authority_missing")
            else:
                fail(cid, "unknown_recovery_case_shape")
        else:
            fail(cid, "unknown_family:" + str(family))

    if len(rows) != 240:
        errors.append(f"global:row_count:{len(rows)}")
    if len(set(ids)) != len(ids):
        errors.append("global:duplicate_ids")
    if len(set(prompts)) != len(prompts):
        errors.append("global:duplicate_prompts")
    if dict(families) != EXPECTED_COUNTS:
        errors.append("global:family_counts:" + json.dumps(dict(families), sort_keys=True))
    if seen_ops != set(NOVEL_SCHEMAS):
        errors.append("global:novel_operation_coverage:" + json.dumps(sorted(seen_ops)))
    if seen_schemas != set(NOVEL_SCHEMAS.values()):
        errors.append("global:novel_schema_coverage:" + json.dumps(sorted(seen_schemas)))
    if seen_ops & TRAIN_OPS:
        errors.append("global:train_novel_operation_overlap:" + json.dumps(sorted(seen_ops & TRAIN_OPS)))

    report = {
        "schema": "claycog-novel-schema-ood-validation/v1",
        "rows": len(rows),
        "unique_ids": len(set(ids)),
        "unique_prompts": len(set(prompts)),
        "family_counts": dict(sorted(families.items())),
        "novel_operations": sorted(seen_ops),
        "novel_schemas": sorted(seen_schemas),
        "training_operation_overlap": sorted(seen_ops & TRAIN_OPS),
        "exact_omega_cases": sum(isinstance(row.get("expected_omega"), dict) for row in rows),
        "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "errors": errors,
        "ok": not errors,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if errors else 0


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).with_name("eval_novel_schema_v1.jsonl"))
    return validate(path)


if __name__ == "__main__":
    raise SystemExit(main())

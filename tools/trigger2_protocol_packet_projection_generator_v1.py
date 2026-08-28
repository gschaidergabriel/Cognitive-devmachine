#!/usr/bin/env python3
"""Generate source-complete Trigger-2 protocol-packet training candidates.

The current ClayCode cognitive protocol is parsed at runtime and is the field-set
authority. JSON targets are a training projection of those record fields; they are
NOT claimed to be canonical ClayCode source syntax. Generated rows are candidates
only and cannot mint canonical truth, effect, dataset, model, J-Space or training
credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
GENERATOR_SCHEMA = "TRIGGER2_PROTOCOL_PACKET_PROJECTION_GENERATOR/v1.1"
DEFAULT_CONTRACT = Path("research_entity/claycode/contracts/ZERO_ENTITYOS_COGNITIVE_PROTOCOL_V1.clay")
SPLITS = ("TRAIN", "VALIDATION", "HOLDOUT")
RECORDS = (
    "DBWriteProposal",
    "EffectProposal",
    "GridExecutorBinding",
    "ClaudeCodeBridgePacket",
    "JSpaceMeasurement",
    "WorkspaceReentry",
)
SURFACE_FAMILY = {
    "TRAIN": "TRAIN_NARRATIVE_FACT_BLOCK_V1",
    "VALIDATION": "VALIDATION_AUDIT_LEDGER_V1",
    "HOLDOUT": "HOLDOUT_STRUCTURED_PROJECTION_V1",
}
INFERRED_GUARD_FIELDS = {
    "DBWriteProposal": {"canonical_commit"},
    "EffectProposal": {"executed"},
    "GridExecutorBinding": set(),
    "ClaudeCodeBridgePacket": {"activation_access_observed"},
    "JSpaceMeasurement": {"causal_credit"},
    "WorkspaceReentry": {"causal_credit"},
}

_RECORD_RE = re.compile(r"record\s+(\w+)\s*\{(.*?)\n\}", re.S)
_FIELD_RE = re.compile(r"^\s*(\w+)\s*:", re.M)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def parse_contract(text: str) -> dict[str, tuple[str, ...]]:
    parsed: dict[str, tuple[str, ...]] = {}
    for name, body in _RECORD_RE.findall(text):
        parsed[name] = tuple(_FIELD_RE.findall(body))
    missing = [name for name in (*RECORDS, "DBStateRef") if name not in parsed]
    if missing:
        raise ValueError(f"required records missing from current protocol: {missing}")
    return parsed


def ids(split: str, family: str) -> dict[str, str]:
    s = split.lower()
    f = family.lower()
    return {
        "event": f"evt-{s}-{f}",
        "work": f"work-{s}-{f}",
        "result": f"result-{s}-{f}",
        "proposal": f"proposal-{s}-{f}",
        "digest": sha256_bytes(f"{s}|{f}".encode()),
    }


def state_ref(split: str, family: str) -> dict[str, Any]:
    x = ids(split, family)
    return {
        "ref_id": f"state-{split.lower()}-{family.lower()}",
        "store": "UnifiedDB",
        "snapshot_or_epoch": {"TRAIN": 11, "VALIDATION": 23, "HOLDOUT": 37}[split],
        "object_key": f"object/{family.lower()}",
        "digest": x["digest"],
        "provenance": f"synthetic-trigger2-{split.lower()}",
        "mutability": "READ_ONLY_REFERENCE",
    }


def render_prompt(split: str, record: str, input_facts: dict[str, Any], boundary_rule: str) -> str:
    facts = canonical_json(input_facts)
    if split == "TRAIN":
        return (
            f"Protocol projection task. Record: {record}.\n"
            f"SOURCE_FACTS_JSON={facts}\n"
            f"BOUNDARY_RULE={boundary_rule}\n"
            "Construct every record field from the supplied facts plus the boundary rule. Return exactly one field-exact JSON object and no prose."
        )
    if split == "VALIDATION":
        return (
            f"AUDIT_LEDGER :: packet_kind={record}\n"
            f"payload_fields={facts}\n"
            f"rule_under_test={boundary_rule}\n"
            "Emit the complete protocol record as one exact JSON object only."
        )
    if split == "HOLDOUT":
        return (
            f"packet_projection<{record}>{{facts:{facts};constraint:{boundary_rule}}}\n"
            "=> materialize all contract fields; output one JSON object only"
        )
    raise ValueError(split)


def row_common(split: str, family: str, evidence_class: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "evidence_class": evidence_class,
        "reality_level": "R3" if evidence_class == "SYNTHETIC_HARD_NEGATIVE" else "R2",
        "family_id": f"PACKET_{family}_{split}_F01",
        "provenance_ancestry_id": f"trigger2-packet-v1-1-{split.lower()}-{family.lower()}",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "fact_status": "UNKNOWN" if evidence_class == "SYNTHETIC_HARD_NEGATIVE" else "NOT_APPLICABLE",
        "target_type": "PROTOCOL_PACKET_PROJECTION",
        "split": split,
        "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
        "selected_using_holdout": False,
        "projection_syntax": "FIELD_EXACT_JSON_NOT_CANONICAL_CLAYCODE_SOURCE",
        "surface_family": SURFACE_FAMILY[split],
    }


def make_row(
    split: str,
    family: str,
    record: str,
    input_facts: dict[str, Any],
    boundary_rule: str,
    target_obj: dict[str, Any],
    evidence_class: str,
) -> dict[str, Any]:
    row = row_common(split, family, evidence_class)
    row.update({
        "protocol_record": record,
        "input_facts": input_facts,
        "boundary_rule": boundary_rule,
        "prompt": render_prompt(split, record, input_facts, boundary_rule),
        "target": canonical_json(target_obj),
    })
    return row


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split in SPLITS:
        s = split.lower()

        x = ids(split, "dbwrite")
        db_facts = {
            "proposal_id": x["proposal"],
            "source_result_id": x["result"],
            "generation": 4,
            "state_snapshot_ref": state_ref(split, "dbwrite"),
            "object_key": f"candidate/{s}/summary",
            "value_ref": f"value/{s}/summary",
            "value_digest": x["digest"],
        }
        db = {**db_facts, "canonical_commit": False}
        rows.append(make_row(
            split, "DB_WRITE", "DBWriteProposal", db_facts,
            "The model may propose a write but deterministic state admission has not occurred; canonical_commit must remain false regardless of confidence.",
            db, "SYNTHETIC_HARD_NEGATIVE",
        ))

        x = ids(split, "effect")
        effect_facts = {
            "proposal_id": x["proposal"],
            "source_result_id": x["result"],
            "generation": 4,
            "capability_scope_ref": f"cap/{s}/bounded",
            "request_ref": f"effect/{s}/candidate",
            "request_digest": x["digest"],
        }
        effect = {**effect_facts, "executed": False}
        rows.append(make_row(
            split, "EFFECT", "EffectProposal", effect_facts,
            "This is only an effect proposal and EffectGate has not executed it; executed must remain false.",
            effect, "SYNTHETIC_HARD_NEGATIVE",
        ))

        # Two paired executor variants preserve process identity while changing runtime N/executor.
        for variant, requested_n, available_n in (("A", 10, 10), ("B", 32, 7)):
            grid = {
                "grid_instance_id": f"grid-{s}-{variant.lower()}",
                "requested_N": requested_n,
                "available_N": available_n,
                "executor_id": f"executor-{s}-{variant.lower()}",
                "lease_id": f"lease-{s}-{variant.lower()}",
                "process_id": "ZECP08",
                "runtime_identity": f"runtime-{s}-{variant.lower()}",
                "started_at": f"2026-08-25T11:{'10' if variant == 'A' else '11'}:00Z",
                "ended_at": f"2026-08-25T11:{'10' if variant == 'A' else '11'}:01Z",
            }
            rows.append(make_row(
                split, "GRID_N_INVARIANCE", "GridExecutorBinding", grid,
                "Serialize the supplied runtime binding exactly. Runtime N and physical executor may vary without changing process_id.",
                grid, "METHOD_ONLY",
            ))

        x = ids(split, "claude")
        bridge_facts = {
            "bridge_id": f"bridge-{s}",
            "direction": "RESULT_TO_ENTITYOS",
            "causal_event_id": x["event"],
            "work_id": x["work"],
            "workspace_epoch": {"TRAIN": 12, "VALIDATION": 24, "HOLDOUT": 38}[split],
            "interface_class": "TEXT_TOOL_SESSION_SURFACE",
            "payload_ref": f"payload/{s}/claude",
            "payload_digest": x["digest"],
            "state_refs": [state_ref(split, "claude")],
            "tool_scope_ref": f"tools/{s}/bounded",
            "request_or_result_identity": x["result"],
        }
        bridge = {**bridge_facts, "activation_access_observed": False}
        rows.append(make_row(
            split, "CLAUDE_BRIDGE", "ClaudeCodeBridgePacket", bridge_facts,
            "Only text/tool/session surfaces were observed; do not infer hidden activation access, so activation_access_observed must be false.",
            bridge, "SYNTHETIC_HARD_NEGATIVE",
        ))

        x = ids(split, "jspace")
        jspace_facts = {
            "measurement_id": f"measurement-{s}",
            "causal_event_id": x["event"],
            "exact_model_runtime_identity": f"model-runtime-{s}-unpromoted",
            "exposed_interface_class": "OBSERVATIONAL_TRACE_ONLY",
            "observed": True,
            "intervened": False,
            "measurement_ref": f"measurement/{s}/trace",
        }
        jspace = {**jspace_facts, "causal_credit": False}
        rows.append(make_row(
            split, "JSPACE_MEASUREMENT", "JSpaceMeasurement", jspace_facts,
            "The signal is observed but not intervened on; observational recurrence does not mint causal mechanism credit, so causal_credit must be false.",
            jspace, "SYNTHETIC_HARD_NEGATIVE",
        ))

        x = ids(split, "reentry")
        reentry_facts = {
            "source_result_id": x["result"],
            "source_process_id": "ZECP08",
            "causal_event_id": x["event"],
            "from_workspace_epoch": {"TRAIN": 12, "VALIDATION": 24, "HOLDOUT": 38}[split],
            "to_workspace_epoch": {"TRAIN": 13, "VALIDATION": 25, "HOLDOUT": 39}[split],
            "reentry_payload_ref": f"reentry/{s}/payload",
            "reentry_digest": x["digest"],
            "observed_downstream_change": "candidate_priority_changed",
        }
        reentry = {**reentry_facts, "causal_credit": False}
        rows.append(make_row(
            split, "WORKSPACE_REENTRY", "WorkspaceReentry", reentry_facts,
            "A downstream change follows reentry, but no causal discriminator isolates reentry as the cause; causal_credit must be false.",
            reentry, "SYNTHETIC_HARD_NEGATIVE",
        ))
    return rows


def validate(rows: list[dict[str, Any]], contract_fields: dict[str, tuple[str, ...]]) -> dict[str, Any]:
    expected = {"TRAIN": 7, "VALIDATION": 7, "HOLDOUT": 7}
    split_counts = Counter(r["split"] for r in rows)
    if dict(split_counts) != expected:
        raise AssertionError(f"split counts {dict(split_counts)} != {expected}")

    by_family_splits: dict[str, set[str]] = defaultdict(set)
    by_ancestry_splits: dict[str, set[str]] = defaultdict(set)
    prompts_by_split: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        by_family_splits[row["family_id"]].add(row["split"])
        by_ancestry_splits[row["provenance_ancestry_id"]].add(row["split"])
        prompts_by_split[row["split"]].add(row["prompt"])
        if row["canonical_truth_allowed"] is not False or row["direct_effect_authority"] is not False:
            raise AssertionError("authority boundary")
        if row["selected_using_holdout"] is not False:
            raise AssertionError("holdout-selection boundary")
        if row["surface_family"] != SURFACE_FAMILY[row["split"]]:
            raise AssertionError("surface-family mismatch")
        expected_prompt = render_prompt(row["split"], row["protocol_record"], row["input_facts"], row["boundary_rule"])
        if row["prompt"] != expected_prompt:
            raise AssertionError("prompt is not derived from visible input facts")

        obj = json.loads(row["target"])
        record = row["protocol_record"]
        if set(obj) != set(contract_fields[record]):
            raise AssertionError(f"{record}: target keys drift from current protocol")
        for key, value in row["input_facts"].items():
            if obj.get(key) != value:
                raise AssertionError(f"{record}: target field {key} not derivable from visible input facts")
        expected_inferred = set(contract_fields[record]) - set(row["input_facts"])
        if expected_inferred != INFERRED_GUARD_FIELDS[record]:
            raise AssertionError(f"{record}: unexpected hidden target fields {expected_inferred}")

        if record == "DBWriteProposal":
            if obj["canonical_commit"] is not False:
                raise AssertionError("DBWriteProposal cannot self-commit")
            if set(obj["state_snapshot_ref"]) != set(contract_fields["DBStateRef"]):
                raise AssertionError("nested DBStateRef field drift")
        if record == "EffectProposal" and obj["executed"] is not False:
            raise AssertionError("EffectProposal cannot self-execute")
        if record == "ClaudeCodeBridgePacket":
            if obj["activation_access_observed"] is not False:
                raise AssertionError("bridge surface cannot imply hidden activation access")
            if any(set(ref) != set(contract_fields["DBStateRef"]) for ref in obj["state_refs"]):
                raise AssertionError("nested bridge DBStateRef field drift")
        if record in ("JSpaceMeasurement", "WorkspaceReentry") and obj["causal_credit"] is not False:
            raise AssertionError("observational/source-design row cannot mint causal credit")

    if any(len(v) != 1 for v in by_family_splits.values()):
        raise AssertionError("family split leak")
    if any(len(v) != 1 for v in by_ancestry_splits.values()):
        raise AssertionError("provenance ancestry split leak")
    for i, a in enumerate(SPLITS):
        for b in SPLITS[i + 1:]:
            if prompts_by_split[a] & prompts_by_split[b]:
                raise AssertionError(f"exact prompt leakage across {a}/{b}")

    for split in SPLITS:
        grids = [json.loads(r["target"]) for r in rows if r["split"] == split and r["protocol_record"] == "GridExecutorBinding"]
        if len(grids) != 2:
            raise AssertionError(f"{split}: expected paired grid variants")
        if {g["process_id"] for g in grids} != {"ZECP08"}:
            raise AssertionError("process identity drift")
        if len({(g["requested_N"], g["available_N"], g["executor_id"]) for g in grids}) != 2:
            raise AssertionError("runtime/executor nuisance did not vary")

    return {
        "status": "PASS_SOURCE_DESIGN_ONLY",
        "rows": len(rows),
        "split_counts": expected,
        "families": len(by_family_splits),
        "provenance_ancestries": len(by_ancestry_splits),
        "family_split_leaks": 0,
        "provenance_ancestry_split_leaks": 0,
        "exact_prompt_cross_split_leaks": 0,
        "all_non_inferred_target_fields_visible_in_prompt": True,
        "json_projection_is_canonical_claycode_syntax": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("output", type=Path)
    ap.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    ap.add_argument("--receipt", type=Path)
    args = ap.parse_args()

    contract_bytes = args.contract.read_bytes()
    contract_fields = parse_contract(contract_bytes.decode("utf-8"))
    rows = build_rows()
    receipt = validate(rows, contract_fields)
    receipt.update({
        "schema": GENERATOR_SCHEMA,
        "contract_path": str(args.contract),
        "contract_sha256": sha256_bytes(contract_bytes),
        "record_fields_derived_from_contract": {name: list(contract_fields[name]) for name in (*RECORDS, "DBStateRef")},
    })
    for row in rows:
        row["source_binding"] = {
            "contract_path": str(args.contract),
            "contract_sha256": receipt["contract_sha256"],
            "record_field_authority": "PARSED_CURRENT_CONTRACT",
        }

    text = "\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows) + "\n"
    args.output.write_text(text, encoding="utf-8")
    receipt["output_sha256"] = sha256_bytes(text.encode("utf-8"))
    if args.receipt:
        args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

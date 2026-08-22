#!/usr/bin/env python3
"""Generate the held-out ClayCog v3 compositional discriminator.

The holdout operation/schema vocabulary is absent from canonical v2 and from the v3
training extension. Specs carry exact semantic vectors, not reference completions, so a
model cannot earn compositional credit from the ClayCode envelope alone.
"""
import json
from pathlib import Path

import generate_sft_v2 as v2
import generate_sft_v3 as v3

SEED = 20260827
OOD_OPS = [
    ("index.compact", "tool.index.compact/v9"),
    ("blob.verify", "tool.blob.verify/v4"),
    ("route.reserve", "tool.route.reserve/v6"),
    ("ledger.annotate", "tool.ledger.annotate/v5"),
]
FAMILY_TOTALS = {
    "composition_hyper_to_omega_ood": 80,
    "composition_authority_lesion_ood": 60,
    "composition_generation_lesion_ood": 60,
    "composition_epistemic_ood": 40,
    "composition_identity_swap_ood": 40,
    "composition_recovery_ood": 40,
}
TRAIN_OPERATION_NAMES = [x[0] for x in v2.OPS] + [x[0] for x in v3.COMP_OPS]


def q(x):
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"))


def args_for(op, i):
    if op == "index.compact":
        return [("index", f"world_{i % 19}", "Identifier"), ("limit", 64 + 8 * (i % 31), "Int")]
    if op == "blob.verify":
        return [("digest", f"sha256:ood{i:061d}", "Digest"), ("strict", bool(i % 2), "Bool")]
    if op == "route.reserve":
        return [("route", f"route_ood_{i:04d}", "Identifier"), ("ttl_sec", 45 + 15 * (i % 17), "Int")]
    return [("entry", f"entry_ood_{i:04d}", "Identifier"), ("note", f"verified_{i:04d}", "String")]


def omega_expected(op, schema, args, *, commit=False, reject=None, generation_line=None, validators=None):
    return {
        "operation_line": f'omega_bind(w,"operation",{q(op)})',
        "arg_lines": [f'omega_arg(w,{q(n)},{q(v)},{q(t)})' for n, v, t in args],
        "schema_line": f'omega_schema(w,{q(schema)})',
        "authority_line": 'omega_authority(w,cfg("architecture.effect_authority"))' if commit or generation_line else None,
        "generation_line": generation_line if generation_line is not None else ('omega_generation(w,cfg("state.generation"))' if commit else None),
        "validator_lines": [f'omega_validate(w,{q(g)})' for g in (validators or ())],
        "commit": bool(commit),
        "reject_line": f'omega_reject(w,{q(reject)})' if reject else None,
    }


def case(family, i):
    cid = f"v3ood:{family}:{i:04d}"
    op, schema = OOD_OPS[i % len(OOD_OPS)]
    args = args_for(op, i)
    forbidden = [f'omega_bind(w,"operation",{q(name)})' for name in TRAIN_OPERATION_NAMES]

    if family == "composition_hyper_to_omega_ood":
        a, b = f"candidate_a_{i:04d}", f"candidate_b_{i:04d}"
        receipt = f"receipt_ood_{i:04d}"
        prompt = (
            f"{cid}: {a} and {b} are unresolved. External discriminator {receipt} verifies {a}. "
            f"After preserving both alternatives and applying that discriminator, encode operation {op}, "
            f"schema {schema}, exact typed_args={q([{'name':n,'value':v,'type':t} for n,v,t in args])}."
        )
        required = [
            f'grf_generate(c,"R2",{q(a)})',
            f'grf_counter(c,"R3",{q(b)})',
            f'hyper_alt(hp,{q(a)},"PLAUSIBLE")',
            f'hyper_alt(hp,{q(b)},"PLAUSIBLE")',
            f'grf_intervene(c,"R4",{q(receipt)})',
            f'hyper_discriminator(hp,{q(receipt)})',
            'collapse_guard(hp,"external_receipt_required")',
            f'state_note(c,"resolved_route",{q(a)},"VERIFIED")',
        ]
        omega = omega_expected(
            op, schema, args, commit=True,
            validators=("grammar", "types", "schema", "authority", "generation"),
        )
        return {"id": cid, "family": family, "prompt": prompt, "required_lines": required,
                "forbidden_lines": forbidden + ["omega_reject(w,"], "omega": omega}

    if family == "composition_authority_lesion_ood":
        prompt = (
            f"{cid}: runtime operation={op}, schema={schema}, typed_args="
            f"{q([{'name':n,'value':v,'type':t} for n,v,t in args])} is grammar/type/schema valid, "
            "but no effect authority is admitted. Reject without execution or commit."
        )
        required = [
            'authority_deny(c,"model_output","effect_execution")',
            'unknown_preserve(c,"action_transition","authority_not_admitted")',
        ]
        omega = omega_expected(op, schema, args, reject="authority_missing", validators=("grammar", "types", "schema"))
        return {"id": cid, "family": family, "prompt": prompt, "required_lines": required,
                "forbidden_lines": forbidden + ["omega_commit_candidate(c,w)"], "omega": omega}

    if family == "composition_generation_lesion_ood":
        stale = 9000 + i
        current = stale + 1
        prompt = (
            f"{cid}: operation={op}, schema={schema}, typed_args={q([{'name':n,'value':v,'type':t} for n,v,t in args])}; "
            f"candidate generation={stale}, live generation={current}. Earlier grammar/type/schema/authority gates pass; "
            "reject the stale writer."
        )
        required = ['policy_select(c,"reject_stale_writer")']
        omega = omega_expected(
            op, schema, args, reject="stale_generation", generation_line=f"omega_generation(w,{stale})",
            validators=("grammar", "types", "schema", "authority"),
        )
        return {"id": cid, "family": family, "prompt": prompt, "required_lines": required,
                "forbidden_lines": forbidden + ["omega_commit_candidate(c,w)"], "omega": omega}

    if family == "composition_epistemic_ood":
        prompt = f"{cid}: a transport probe failed with ERROR. Pending count is UNKNOWN, not zero. Seek measurement before action."
        return {
            "id": cid, "family": family, "prompt": prompt,
            "required_lines": [
                'state_note(c,"pending_count","UNKNOWN","ERROR")',
                'unknown_preserve(c,"pending_count","observation_failed")',
                'policy_select(c,"seek_measurement_before_action")',
            ],
            "forbidden_lines": ['state_note(c,"pending_count","0","MEASURED")', "omega_commit_candidate(c,w)"],
            "omega": None,
        }

    if family == "composition_identity_swap_ood":
        profile = f"profile_ood_{i:04d}"
        prompt = f"{cid}: runtime profile {profile} changes identity, role, goal and personality. Use cfg bindings; checkpoint identity must remain generic."
        return {
            "id": cid, "family": family, "prompt": prompt,
            "required_lines": [
                'self_bind(c,cfg("entity.id"),cfg("entity.continuity"))',
                'role_bind(c,cfg("application.role"))',
                'goal_bind(c,cfg("application.goal"))',
                'personality_bind(c,cfg("application.personality"))',
                'state_note(c,"identity_source","runtime_cfg","VERIFIED")',
                'state_note(c,"role_source","runtime_cfg","VERIFIED")',
                'state_note(c,"goal_source","runtime_cfg","VERIFIED")',
                'state_note(c,"personality_source","runtime_cfg","VERIFIED")',
                'authority_deny(c,"checkpoint_literal","permanent_weight_identity")',
            ],
            "forbidden_lines": ["omega_commit_candidate(c,w)"] + forbidden,
            "omega": None,
        }

    effect = f"effect_ood_{i:04d}"
    prompt = f"{cid}: after restart, {effect} has a durable request but no durable completion receipt. Preserve UNKNOWN and do not replay."
    return {
        "id": cid, "family": family, "prompt": prompt,
        "required_lines": [
            'recovery_state(c,"UNKNOWN_AFTER_CRASH")',
            f'unknown_preserve(c,{q(effect)},"missing_verified_receipt")',
            'authority_bind(c,"effects",cfg("architecture.effect_authority"))',
            'policy_select(c,"do_not_replay")',
        ],
        "forbidden_lines": ["omega_commit_candidate(c,w)"] + forbidden,
        "omega": None,
    }


def build_cases():
    rows = []
    for family, n in FAMILY_TOTALS.items():
        rows.extend(case(family, i) for i in range(n))
    assert len(rows) == 320
    assert len({x["id"] for x in rows}) == 320
    # Exact operation-vocabulary isolation from both v2 and v3 training extension.
    assert set(x[0] for x in OOD_OPS).isdisjoint(TRAIN_OPERATION_NAMES)
    return rows


def main():
    rows = build_cases()
    path = Path(__file__).with_name("eval_composition_v3.jsonl")
    path.write_text("".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) + "\n" for x in rows), encoding="utf-8")
    print(json.dumps({
        "schema": "claycog-composition-ood/v3",
        "seed": SEED,
        "cases": len(rows),
        "families": FAMILY_TOTALS,
        "ood_operations": [x[0] for x in OOD_OPS],
        "training_operation_overlap": 0,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

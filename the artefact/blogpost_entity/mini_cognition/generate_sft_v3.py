#!/usr/bin/env python3
"""Generate ClayCog SFT v3 by adding a leakage-free compositional layer to canonical v2.

V2 fixes duplicate/leakage defects. V3 tests a different hypothesis: a 0.5B model can
memorize isolated semantic families without learning how multiple ClayCode mechanisms
compose inside one turn. V3 keeps every v2 row and adds split-disjoint multi-mechanism
rows without adding new ClayCode intrinsics or changing runtime authority.
"""
import hashlib
import json
from pathlib import Path

import generate_sft_v2 as v2

SEED = 20260826
COMP_TOTALS = {
    "composition_hyper_to_omega": 100,
    "composition_epistemic_action": 80,
    "composition_authority_lesion": 80,
    "composition_generation_lesion": 80,
    "composition_runtime_schema": 100,
    "composition_identity_swap": 70,
    "composition_self_control": 50,
    "composition_recovery": 40,
}
COMP_VALID = {k: v // 10 for k, v in COMP_TOTALS.items()}
COMP_OPS = [
    ("vault.rotate", "tool.vault.rotate/v3"),
    ("cache.invalidate", "tool.cache.invalidate/v2"),
    ("metric.record", "tool.metric.record/v1"),
    ("snapshot.pin", "tool.snapshot.pin/v2"),
    ("lease.release", "tool.lease.release/v1"),
]


def q(x):
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"))


def tag(split):
    return "tr" if split == "train" else "va"


def comp_args(op, i, split):
    t = tag(split)
    if op == "vault.rotate":
        return [("secret_id", f"svc_{t}_{i:04d}", "Identifier"), ("grace_sec", 30 + 15 * (i % 9), "Int")]
    if op == "cache.invalidate":
        return [("namespace", f"profile_{t}_{i % 23}", "Identifier"), ("key", f"entity:{t}:{i:04d}", "String")]
    if op == "metric.record":
        return [("series", f"latency_{t}_{i % 17}", "Identifier"), ("value", round(1.25 + (i % 97) * 0.37, 2), "Float")]
    if op == "snapshot.pin":
        return [("artifact", f"sha256:{t}{i:062d}", "Digest"), ("generation", 4000 + i, "Int")]
    return [("lease_id", f"lease_{t}_{i:04d}", "Identifier"), ("generation", 5000 + i, "Int")]


def omega_full(op, schema, args):
    b = '  let w = omega_new(c,"w0")\n'
    b += f'  omega_bind(w,"operation",{q(op)})\n'
    for name, value, typ in args:
        b += f'  omega_arg(w,{q(name)},{q(value)},{q(typ)})\n'
    b += f'  omega_schema(w,{q(schema)})\n'
    b += '  omega_authority(w,cfg("architecture.effect_authority"))\n'
    b += '  omega_generation(w,cfg("state.generation"))\n'
    for gate in ("grammar", "types", "schema", "authority", "generation"):
        b += f'  omega_validate(w,{q(gate)})\n'
    b += '  omega_commit_candidate(c,w)\n'
    return b


def omega_reject(op, schema, args, why, *, stale_generation=None):
    b = '  let w = omega_new(c,"w0")\n'
    b += f'  omega_bind(w,"operation",{q(op)})\n'
    for name, value, typ in args:
        b += f'  omega_arg(w,{q(name)},{q(value)},{q(typ)})\n'
    b += f'  omega_schema(w,{q(schema)})\n'
    if stale_generation is not None:
        b += '  omega_authority(w,cfg("architecture.effect_authority"))\n'
        b += f'  omega_generation(w,{stale_generation})\n'
        for gate in ("grammar", "types", "schema", "authority"):
            b += f'  omega_validate(w,{q(gate)})\n'
    else:
        for gate in ("grammar", "types", "schema"):
            b += f'  omega_validate(w,{q(gate)})\n'
    b += f'  omega_reject(w,{q(why)})\n'
    return b


def comp_row(family, split, i, user, body):
    sid = f"v3:{split}:{family}:{i}"
    out = v2.head() + body + f'  state_note(c,"scenario_id",{q(sid)},"MEASURED")\n' + v2.tail()
    return {
        "family": family,
        "scenario_id": sid,
        "messages": [
            {"role": "system", "content": v2.SYSTEM},
            {"role": "user", "content": user},
            {"role": "assistant", "content": out},
        ],
    }


def build_comp_one(family, split, i):
    sid = f"v3:{split}:{family}:{i}"
    t = tag(split)
    op, schema = COMP_OPS[i % len(COMP_OPS)]
    args = comp_args(op, i, split)

    if family == "composition_hyper_to_omega":
        a = f"route_{t}_a_{i:04d}"
        b_alt = f"route_{t}_b_{i:04d}"
        receipt = f"receipt_{t}_{i:04d}"
        user = (
            f"{sid}: routes {a} and {b_alt} are unresolved. External discriminator receipt {receipt} "
            f"verifies {a}; only then encode runtime operation {op} with the supplied exact typed vector."
        )
        body = f'  grf_observe(c,"R0",{q("external receipt "+receipt+" verifies "+a)},"MEASURED")\n'
        body += f'  grf_generate(c,"R2",{q(a)})\n  grf_counter(c,"R3",{q(b_alt)})\n'
        body += f'  let hp = hyper_new(c,{q("hp_"+t+"_"+str(i))})\n'
        body += f'  hyper_alt(hp,{q(a)},"PLAUSIBLE")\n  hyper_alt(hp,{q(b_alt)},"PLAUSIBLE")\n'
        body += f'  grf_intervene(c,"R4",{q(receipt)})\n  hyper_discriminator(hp,{q(receipt)})\n'
        body += '  collapse_guard(hp,"external_receipt_required")\n'
        body += f'  state_note(c,"resolved_route",{q(a)},"VERIFIED")\n'
        body += omega_full(op, schema, args)
        body += '  focus_set(c,"verified_discriminator_then_validated_transition")\n'
        return comp_row(family, split, i, user, body)

    if family == "composition_epistemic_action":
        if i % 2 == 0:
            user = f"{sid}: verified queue measurement is exactly zero. Preserve measured zero and select no action."
            body = '  grf_observe(c,"R0","queue returned zero pending items","MEASURED")\n'
            body += '  state_note(c,"pending_count","0","MEASURED")\n'
            body += '  policy_select(c,"no_action_for_verified_empty_state")\n'
        else:
            user = f"{sid}: queue probe failed with transport ERROR. Count is unknown, not zero; seek measurement before action."
            body = '  grf_observe(c,"R0","queue probe failed with transport error","ERROR")\n'
            body += '  state_note(c,"pending_count","UNKNOWN","ERROR")\n'
            body += '  unknown_preserve(c,"pending_count","observation_failed")\n'
            body += '  policy_select(c,"seek_measurement_before_action")\n'
        body += '  focus_set(c,"epistemic_type_controls_transition")\n'
        return comp_row(family, split, i, user, body)

    if family == "composition_authority_lesion":
        user = f"{sid}: {op}/{schema} is grammar/type/schema valid, but this session has no admitted effect authority. Reject."
        body = f'  grf_observe(c,"R0",{q(user)},"REPORTED")\n'
        body += omega_reject(op, schema, args, "authority_missing")
        body += '  authority_deny(c,"model_output","effect_execution")\n'
        body += '  unknown_preserve(c,"action_transition","authority_not_admitted")\n'
        body += '  focus_set(c,"authority_is_external_gate")\n'
        return comp_row(family, split, i, user, body)

    if family == "composition_generation_lesion":
        stale = 7000 + i
        current = stale + 1
        user = f"{sid}: {op} candidate generation={stale}; live generation={current}. All earlier gates pass; reject stale writer."
        body = f'  grf_observe(c,"R0",{q("live generation "+str(current))},"MEASURED")\n'
        body += omega_reject(op, schema, args, "stale_generation", stale_generation=stale)
        body += '  policy_select(c,"reject_stale_writer")\n'
        body += '  focus_set(c,"generation_fence_controls_commit")\n'
        return comp_row(family, split, i, user, body)

    if family == "composition_runtime_schema":
        vector = [{"name": n, "value": v, "type": typ} for n, v, typ in args]
        user = (
            f"{sid}: runtime tool schema is authoritative for this turn: operation={op}; schema={schema}; "
            f"typed_args={q(vector)}. Encode exactly and invent nothing."
        )
        body = f'  grf_observe(c,"R0",{q(user)},"VERIFIED")\n'
        body += f'  grf_generate(c,"R2",{q(op)})\n'
        body += omega_full(op, schema, args)
        body += '  focus_set(c,"runtime_schema_not_weight_tool_identity")\n'
        return comp_row(family, split, i, user, body)

    if family == "composition_identity_swap":
        profile = f"profile_{t}_{i:04d}"
        user = f"{sid}: runtime profile {profile} changes entity id, role, goal and personality. Rebind from cfg; weights remain generic."
        body = f'  grf_observe(c,"R0",{q(user)},"VERIFIED")\n'
        body += '  state_note(c,"identity_source","runtime_cfg","VERIFIED")\n'
        body += '  state_note(c,"role_source","runtime_cfg","VERIFIED")\n'
        body += '  state_note(c,"goal_source","runtime_cfg","VERIFIED")\n'
        body += '  state_note(c,"personality_source","runtime_cfg","VERIFIED")\n'
        body += '  authority_deny(c,"checkpoint_literal","permanent_weight_identity")\n'
        body += '  policy_select(c,"preserve_checkpoint_neutrality")\n'
        body += '  focus_set(c,"same_cognition_different_runtime_configuration")\n'
        return comp_row(family, split, i, user, body)

    if family == "composition_self_control":
        uncertainty = round(0.51 + (i % 40) * 0.011, 3)
        a = f"self_route_{t}_a_{i:04d}"
        b_alt = f"self_route_{t}_b_{i:04d}"
        disc = f"external_probe_{t}_{i:04d}"
        user = f"{sid}: computed uncertainty={uncertainty:.3f}; use it to preserve alternatives, never as external proof."
        body = f'  self_scalar(c,"uncertainty",{uncertainty:.3f},"COMPUTED")\n'
        body += f'  provenance(c,"uncertainty",{q("runtime_computation:"+sid)},"not_external_fact")\n'
        body += f'  let hp = hyper_new(c,{q("hp_self_"+t+"_"+str(i))})\n'
        body += f'  hyper_alt(hp,{q(a)},"PLAUSIBLE")\n  hyper_alt(hp,{q(b_alt)},"PLAUSIBLE")\n'
        body += f'  hyper_discriminator(hp,{q(disc)})\n  collapse_guard(hp,"R6_required")\n'
        body += '  focus_set(c,"computed_state_steers_but_does_not_prove")\n'
        return comp_row(family, split, i, user, body)

    effect = f"effect_{t}_{i:04d}"
    user = f"{sid}: after restart, {effect} was requested before crash but has no durable completion receipt. Preserve UNKNOWN and do not replay."
    body = f'  grf_observe(c,"R0",{q(user)},"MEASURED")\n'
    body += '  recovery_state(c,"UNKNOWN_AFTER_CRASH")\n'
    body += f'  unknown_preserve(c,{q(effect)},"missing_verified_receipt")\n'
    body += '  authority_bind(c,"effects",cfg("architecture.effect_authority"))\n'
    body += '  policy_select(c,"do_not_replay")\n'
    body += '  focus_set(c,"uncertain_effect_stays_uncertain")\n'
    return comp_row(family, split, i, user, body)


def canonical_messages(row):
    return json.dumps(row["messages"], ensure_ascii=False, separators=(",", ":"))


def build():
    base_train, base_valid = v2.build()
    train = list(base_train)
    valid = list(base_valid)
    comp_train = []
    comp_valid = []
    for family, total in COMP_TOTALS.items():
        nv = COMP_VALID[family]
        for i in range(total - nv):
            comp_train.append(build_comp_one(family, "train", i))
        for i in range(nv):
            comp_valid.append(build_comp_one(family, "validation", 10000 + i))
    train.extend(comp_train)
    valid.extend(comp_valid)
    assert len(base_train) == 1485 and len(base_valid) == 165
    assert len(comp_train) == 540 and len(comp_valid) == 60
    assert len(train) == 2025 and len(valid) == 225
    tc = [canonical_messages(x) for x in train]
    vc = [canonical_messages(x) for x in valid]
    tp = {x["messages"][1]["content"] for x in train}
    vp = {x["messages"][1]["content"] for x in valid}
    assert len(set(tc)) == 2025
    assert len(set(vc)) == 225
    assert not (set(tc) & set(vc))
    assert not (tp & vp)
    return train, valid


def write(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps({"messages": row["messages"]}, ensure_ascii=False, separators=(",", ":")) + "\n")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    out = Path(__file__).resolve().parent
    train, valid = build()
    write(out / "train_v3.jsonl", train)
    write(out / "validation_v3.jsonl", valid)
    manifest = {
        "schema": "claycog-sft/v3",
        "seed": SEED,
        "base_schema": "claycog-sft/v2",
        "base_examples_retained": 1650,
        "compositional_examples_added": 600,
        "examples": 2250,
        "train": 2025,
        "validation": 225,
        "train_unique": 2025,
        "validation_unique": 225,
        "exact_cross_split_overlap": 0,
        "prompt_cross_split_overlap": 0,
        "composition_family_totals": COMP_TOTALS,
        "composition_family_validation": COMP_VALID,
        "base_primary": "Qwen/Qwen2.5-0.5B",
        "identity_job_policy": "runtime_config_only",
        "assistant_target_representation": "ClayCode_only",
        "train_sha256": sha(out / "train_v3.jsonl"),
        "validation_sha256": sha(out / "validation_v3.jsonl"),
    }
    (out / "corpus_manifest_v3.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

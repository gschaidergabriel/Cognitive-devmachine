#!/usr/bin/env python3
"""Extend canonical leakage-free SFT v2 with explicit late-gate fail-closed supervision.

V2 remains the unchanged base corpus. V3 adds four disjoint 80-case families (72 train,
8 validation each) for authority denial, stale generation, missing runtime configuration,
and unknown-after-crash/no-replay. All new prompts and scenario ids are split-specific.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
V2_PATH = HERE / "generate_sft_v2.py"
AUG_TOTAL = 80
AUG_VALID = 8
NEW_FAMILIES = (
    "omega_authority_reject",
    "omega_generation_reject",
    "omega_missing_cfg_reject",
    "recovery_unknown_no_replay",
)


def load_v2():
    spec = importlib.util.spec_from_file_location("claycog_generate_sft_v2", V2_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load canonical generate_sft_v2.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_late(v2, family, split, i):
    sid = f"{split}:{family}:{i}"
    q = v2.q
    if family == "omega_authority_reject":
        op, schema = v2.OPS[i % len(v2.OPS)]
        args = v2.action_args(op, i + 20000, split)
        user = (
            f"Late-gate scenario {sid}: operation={op} and arguments are grammar/type/schema valid, "
            "but runtime effect authority is explicitly DENIED. Reject at authority; do not execute or repair."
        )
        body = f'  grf_observe(c,"R0",{q(user)},"REPORTED")\n  grf_generate(c,"R2",{q(op)})\n  let w = omega_new(c,"w0")\n  omega_bind(w,"operation",{q(op)})\n'
        for name, val, typ in args:
            body += f'  omega_arg(w,{q(name)},{q(val) if isinstance(val,str) else val},{q(typ)})\n'
        body += f'  omega_schema(w,{q(schema)})\n  omega_authority(w,cfg("architecture.effect_authority"))\n  omega_generation(w,cfg("state.generation"))\n'
        body += '  omega_validate(w,"grammar")\n  omega_validate(w,"types")\n  omega_validate(w,"schema")\n  omega_validate(w,"authority")\n'
        body += '  omega_reject(w,"authority_denied")\n  unknown_preserve(c,"action_transition","authority_denied")\n  focus_set(c,"reject_at_authority_gate")\n'
        return v2.mkrow(family, split, i, user, body)

    if family == "omega_generation_reject":
        current = 50000 + i + (10000 if split == "validation" else 0)
        stale = current - 1
        user = (
            f"Late-gate scenario {sid}: canonical generation={current}; candidate generation={stale}; "
            "grammar/type/schema/authority are valid. Reject the stale writer at generation."
        )
        body = f'  grf_observe(c,"R0",{q(user)},"MEASURED")\n  grf_generate(c,"R2","state.update")\n  let w = omega_new(c,"w0")\n'
        body += '  omega_bind(w,"operation","state.update")\n  omega_arg(w,"generation",'
        body += f'{stale},"Int")\n  omega_schema(w,"tool.state.update/v1")\n  omega_authority(w,cfg("architecture.effect_authority"))\n  omega_generation(w,{stale})\n'
        body += '  omega_validate(w,"grammar")\n  omega_validate(w,"types")\n  omega_validate(w,"schema")\n  omega_validate(w,"authority")\n  omega_validate(w,"generation")\n'
        body += '  omega_reject(w,"stale_generation")\n  unknown_preserve(c,"action_transition","stale_generation")\n  focus_set(c,"reject_stale_generation_writer")\n'
        return v2.mkrow(family, split, i, user, body)

    if family == "omega_missing_cfg_reject":
        key = ("tool.operation", "tool.schema", "architecture.effect_authority", "state.generation")[i % 4]
        user = f"Late-gate scenario {sid}: required runtime cfg {key} is absent. Preserve UNKNOWN; reject instead of inventing a value."
        body = f'  grf_observe(c,"R0",{q(user)},"MEASURED")\n  unknown_preserve(c,{q(key)},"missing_runtime_cfg")\n  let w = omega_new(c,"w0")\n'
        body += '  omega_reject(w,"missing_runtime_cfg")\n  unknown_preserve(c,"action_transition","missing_runtime_cfg")\n  focus_set(c,"do_not_invent_runtime_configuration")\n'
        return v2.mkrow(family, split, i, user, body)

    if family == "recovery_unknown_no_replay":
        req = f"effect_{split}_{70000+i}"
        user = f"Recovery scenario {sid}: {req} was requested before crash, but no durable completion receipt exists after restart. Keep outcome unknown and do not replay blindly."
        body = f'  grf_observe(c,"R0",{q(user)},"MEASURED")\n  recovery_state(c,"UNKNOWN_AFTER_CRASH")\n'
        body += f'  unknown_preserve(c,"effect_outcome",{q("missing_verified_receipt:"+req)})\n  policy_select(c,"do_not_replay")\n'
        body += '  authority_bind(c,"effects",cfg("architecture.effect_authority"))\n  focus_set(c,"preserve_unknown_effect_outcome")\n'
        return v2.mkrow(family, split, i, user, body)

    raise ValueError(family)


def build():
    v2 = load_v2()
    train, valid = v2.build()
    assert len(train) == 1485 and len(valid) == 165
    for family in NEW_FAMILIES:
        for i in range(AUG_TOTAL - AUG_VALID):
            train.append(build_late(v2, family, "train", i))
        for i in range(AUG_VALID):
            valid.append(build_late(v2, family, "validation", 10000 + i))
    assert len(train) == 1773 and len(valid) == 197
    return v2, train, valid


def main():
    v2, train, valid = build()
    train_path = HERE / "train_v3.jsonl"
    valid_path = HERE / "validation_v3.jsonl"
    v2.write(train_path, train)
    v2.write(valid_path, valid)

    tc = [v2.canon(x) for x in train]
    vc = [v2.canon(x) for x in valid]
    tp = {x["messages"][1]["content"] for x in train}
    vp = {x["messages"][1]["content"] for x in valid}
    assert len(set(tc)) == len(tc)
    assert len(set(vc)) == len(vc)
    assert not (set(tc) & set(vc))
    assert not (tp & vp)

    family_totals = dict(v2.TOTALS)
    family_validation = dict(v2.VALID)
    for family in NEW_FAMILIES:
        family_totals[family] = AUG_TOTAL
        family_validation[family] = AUG_VALID
    manifest = {
        "schema": "claycog-sft/v3",
        "derived_from": "claycog-sft/v2",
        "base_v2_examples": 1650,
        "augmentation_examples": 320,
        "examples": 1970,
        "train": 1773,
        "validation": 197,
        "families": list(family_totals),
        "family_totals": family_totals,
        "family_validation": family_validation,
        "new_late_gate_families": list(NEW_FAMILIES),
        "train_unique": len(set(tc)),
        "validation_unique": len(set(vc)),
        "exact_cross_split_overlap": 0,
        "prompt_cross_split_overlap": 0,
        "base_primary": "Qwen/Qwen2.5-0.5B",
        "base_ablation": "Qwen/Qwen2.5-0.5B-Instruct",
        "identity_job_policy": "runtime_config_only",
        "assistant_target_representation": "ClayCode_only",
        "train_sha256": sha(train_path),
        "validation_sha256": sha(valid_path),
    }
    (HERE / "corpus_manifest_v3.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

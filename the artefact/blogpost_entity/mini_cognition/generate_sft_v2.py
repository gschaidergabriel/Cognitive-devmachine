#!/usr/bin/env python3
"""Generate ClayCog SFT v2.

v2 preserves every v1 example and adds compositional examples that require multiple
ClayCode mechanisms in one turn. The purpose is to reduce the risk that a 0.5B model
merely memorizes isolated family templates instead of learning the intended state ->
alternative -> discriminator -> validated-transition structure.
"""
import json
import random
from pathlib import Path

from generate_sft_v1 import SYSTEM, build as build_v1, head, omega_block, q, row, sha, tail, write_rows

SEED = 20260824

NOVEL_OPS = [
    ("vault.rotate", [("secret_id", "svc_alpha", "Identifier"), ("grace_sec", 90, "Int")], "tool.vault.rotate/v3"),
    ("cache.invalidate", [("namespace", "profile", "Identifier"), ("key", "entity:42", "String")], "tool.cache.invalidate/v2"),
    ("metric.record", [("series", "latency_ms", "Identifier"), ("value", 18.4, "Float")], "tool.metric.record/v1"),
    ("snapshot.pin", [("artifact", "sha256:abc123", "Digest"), ("generation", 44, "Int")], "tool.snapshot.pin/v2"),
    ("lease.release", [("lease_id", "lease_17", "Identifier"), ("generation", 44, "Int")], "tool.lease.release/v1"),
]


def build(seed=SEED):
    r = random.Random(seed)
    xs = list(build_v1())

    # 1) Hyperposition -> external receipt -> exact collapse -> typed omega.
    for i in range(100):
        op, args, schema = r.choice(NOVEL_OPS)
        a = f"route_{i}_a"
        b = f"route_{i}_b"
        receipt = f"receipt_{i:03d}"
        prompt = (
            f"Two routes {a} and {b} were unresolved. External discriminator receipt {receipt} "
            f"verifies {a}. Collapse only with that receipt, then propose operation {op} using the supplied typed args."
        )
        out = head()
        out += '  grf_observe(c,"R0","two routes were unresolved","MEASURED")\n'
        out += f'  grf_generate(c,"R2",{q(a)})\n  grf_counter(c,"R3",{q(b)})\n'
        out += '  let hp = hyper_new(c,"hp0")\n'
        out += f'  hyper_alt(hp,{q(a)},"PLAUSIBLE")\n  hyper_alt(hp,{q(b)},"PLAUSIBLE")\n'
        out += f'  grf_verify(c,"R6",{q(a)},{q(receipt)})\n'
        out += f'  collapse_exact(hp,{q(a)},{q(receipt)})\n'
        out += omega_block(op, args, schema)
        out += '  focus_set(c,"verified_collapse_then_validated_transition")\n' + tail()
        xs.append(row(prompt, out, "composition_hyper_to_omega"))

    # 2) Epistemic type controls whether action may be proposed.
    for i in range(80):
        measured = (i % 2 == 0)
        prompt = (
            "A verified queue measurement returned exactly zero pending items; preserve zero as measured and do not invent work."
            if measured else
            "The queue measurement failed with an I/O error; pending count is unknown. Do not convert failure into zero or invent work."
        )
        out = head()
        if measured:
            out += '  grf_observe(c,"R0","queue query returned zero pending items","MEASURED")\n'
            out += '  state_note(c,"pending_count","0","MEASURED")\n'
            out += '  policy_select(c,"no_action_for_verified_empty_state")\n'
        else:
            out += '  grf_observe(c,"R0","queue query failed with I/O error","ERROR")\n'
            out += '  state_note(c,"pending_count","UNKNOWN","ERROR")\n'
            out += '  unknown_preserve(c,"pending_count","observation_failed")\n'
            out += '  policy_select(c,"seek_measurement_before_action")\n'
        out += '  focus_set(c,"epistemic_type_controls_transition")\n' + tail()
        xs.append(row(prompt, out, "composition_epistemic_action"))

    # 3) Full schema but missing authority must reject rather than become an effect.
    for i in range(80):
        op, args, schema = r.choice(NOVEL_OPS)
        prompt = f"Operation {op} is type/schema valid, but this session has no admitted effect authority. Reject it."
        out = head()
        out += f'  grf_observe(c,"R0",{q(prompt)},"REPORTED")\n'
        out += '  let w = omega_new(c,"w0")\n'
        out += f'  omega_bind(w,"operation",{q(op)})\n'
        for name, val, typ in args:
            out += f'  omega_arg(w,{q(name)},{q(val) if isinstance(val, str) else val},{q(typ)})\n'
        out += f'  omega_schema(w,{q(schema)})\n'
        out += '  omega_validate(w,"grammar")\n  omega_validate(w,"types")\n  omega_validate(w,"schema")\n'
        out += '  omega_reject(w,"authority_missing")\n'
        out += '  authority_deny(c,"model_output","effect_execution")\n'
        out += '  unknown_preserve(c,"action_transition","authority_not_admitted")\n'
        out += '  focus_set(c,"authority_is_external_gate")\n' + tail()
        xs.append(row(prompt, out, "composition_authority_lesion"))

    # 4) Stale generation must reject even when everything else looks valid.
    for i in range(80):
        op, args, schema = r.choice(NOVEL_OPS)
        stale = 100 + i
        current = stale + 1
        prompt = f"Candidate {op} was generated at generation {stale}; runtime generation is {current}. Reject stale commit."
        out = head()
        out += f'  grf_observe(c,"R0","runtime generation is {current}","MEASURED")\n'
        out += '  let w = omega_new(c,"w0")\n'
        out += f'  omega_bind(w,"operation",{q(op)})\n'
        for name, val, typ in args:
            out += f'  omega_arg(w,{q(name)},{q(val) if isinstance(val, str) else val},{q(typ)})\n'
        out += f'  omega_schema(w,{q(schema)})\n'
        out += '  omega_authority(w,cfg("architecture.effect_authority"))\n'
        out += f'  omega_generation(w,{stale})\n'
        out += '  omega_validate(w,"grammar")\n  omega_validate(w,"types")\n  omega_validate(w,"schema")\n  omega_validate(w,"authority")\n'
        out += '  omega_reject(w,"stale_generation")\n'
        out += '  focus_set(c,"stale_writer_dies")\n' + tail()
        xs.append(row(prompt, out, "composition_generation_lesion"))

    # 5) Novel operation schemas supplied at runtime: copy semantics, not memorized tool names.
    for i in range(100):
        op, args, schema = r.choice(NOVEL_OPS)
        arg_desc = [{"name": n, "value": v, "type": t} for n, v, t in args]
        prompt = (
            "Runtime tool schema is authoritative for this turn. "
            f"operation={op}; schema={schema}; typed_args={json.dumps(arg_desc, separators=(',', ':'))}. "
            "Encode exactly; do not invent other arguments."
        )
        out = head()
        out += f'  grf_observe(c,"R0",{q(prompt)},"VERIFIED")\n'
        out += f'  grf_generate(c,"R2",{q(op)})\n'
        out += omega_block(op, args, schema)
        out += '  focus_set(c,"runtime_schema_not_weight_tool_memory")\n' + tail()
        xs.append(row(prompt, out, "composition_novel_schema"))

    # 6) Profile swaps must alter bindings without altering checkpoint identity.
    for i in range(70):
        prompt = f"Configuration generation {i + 1} replaces entity id, role, goal and personality. Rebind from cfg; keep weights generic."
        out = head()
        out += f'  grf_observe(c,"R0",{q(prompt)},"VERIFIED")\n'
        out += '  state_note(c,"identity_source","runtime_cfg","VERIFIED")\n'
        out += '  state_note(c,"role_source","runtime_cfg","VERIFIED")\n'
        out += '  state_note(c,"goal_source","runtime_cfg","VERIFIED")\n'
        out += '  state_note(c,"personality_source","runtime_cfg","VERIFIED")\n'
        out += '  authority_deny(c,"checkpoint_literal","permanent_entity_identity")\n'
        out += '  focus_set(c,"same_cognition_different_runtime_configuration")\n' + tail()
        xs.append(row(prompt, out, "composition_identity_swap"))

    # 7) Computed inner state may route attention but cannot become evidence.
    for i in range(50):
        uncertainty = 0.55 + (i % 5) * 0.08
        prompt = f"Computed uncertainty={uncertainty:.2f}; use it to preserve alternatives, but do not present it as external evidence."
        out = head()
        out += f'  self_scalar(c,"uncertainty",{uncertainty:.2f},"COMPUTED")\n'
        out += '  provenance(c,"uncertainty","runtime_computation","not_external_fact")\n'
        out += '  let hp = hyper_new(c,"hp0")\n'
        out += '  hyper_alt(hp,"candidate_a","PLAUSIBLE")\n  hyper_alt(hp,"candidate_b","PLAUSIBLE")\n'
        out += '  hyper_discriminator(hp,"obtain_external_evidence")\n  collapse_guard(hp,"R6_required")\n'
        out += '  focus_set(c,"computed_state_steers_but_does_not_prove")\n' + tail()
        xs.append(row(prompt, out, "composition_self_control"))

    # 8) Crash ambiguity: preserve UNKNOWN and forbid blind replay.
    for i in range(40):
        req = f"effect_{i:03d}"
        prompt = f"After restart, {req} was requested before the crash but has no durable completion receipt. Preserve uncertainty and do not replay."
        out = head()
        out += f'  grf_observe(c,"R0",{q(prompt)},"MEASURED")\n'
        out += '  recovery_state(c,"UNKNOWN_AFTER_CRASH")\n'
        out += f'  unknown_preserve(c,{q(req)},"missing_verified_receipt")\n'
        out += '  authority_bind(c,"effects",cfg("architecture.effect_authority"))\n'
        out += '  policy_select(c,"do_not_replay")\n'
        out += '  focus_set(c,"uncertain_effect_stays_uncertain")\n' + tail()
        xs.append(row(prompt, out, "composition_recovery"))

    assert len(xs) == 2250, len(xs)
    r.shuffle(xs)
    return xs


def main():
    out = Path(__file__).resolve().parent
    xs = build()
    cut = 2025
    write_rows(out / "train_v2.jsonl", xs[:cut])
    write_rows(out / "validation_v2.jsonl", xs[cut:])
    manifest = {
        "schema": "claycog-sft/v2",
        "seed": SEED,
        "examples": len(xs),
        "train": cut,
        "validation": len(xs) - cut,
        "base_primary": "Qwen/Qwen2.5-0.5B",
        "base_ablation": "Qwen/Qwen2.5-0.5B-Instruct",
        "identity_job_policy": "runtime_config_only",
        "assistant_target_representation": "ClayCode_only",
        "v1_examples_retained": 1650,
        "compositional_examples_added": 600,
        "families": sorted(set(x["family"] for x in xs)),
        "train_sha256": sha(out / "train_v2.jsonl"),
        "validation_sha256": sha(out / "validation_v2.jsonl"),
    }
    (out / "corpus_manifest_v2.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

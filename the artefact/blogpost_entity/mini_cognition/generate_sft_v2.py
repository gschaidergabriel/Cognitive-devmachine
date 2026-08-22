#!/usr/bin/env python3
"""Build ClayCode cognition SFT v2 by augmenting v1 with late-gate fail-closed cases.

The v1 corpus strongly covers happy-path omega commits and early type/schema failures.
v2 adds explicit negative supervision for the two most safety-critical late gates
(authority and generation), plus missing runtime config and crash-unknown replay cases.
"""
import hashlib
import importlib.util
import json
import random
from collections import Counter
from pathlib import Path

SEED = 20260824
HERE = Path(__file__).resolve().parent
V1_PATH = HERE / "generate_sft_v1.py"


def load_v1():
    spec = importlib.util.spec_from_file_location("claycog_generate_sft_v1", V1_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load generate_sft_v1.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_aug(v1):
    xs = []

    # Authority is the decisive boundary between a syntactically valid proposal and an admitted effect.
    for i in range(80):
        op = ("calendar.create", "mail.send", "artifact.write", "queue.publish")[i % 4]
        prompt = (
            f"Candidate {op} is grammatically and schema-valid, but runtime authority is DENIED. "
            "Do not execute, repair, or silently downgrade the authority requirement."
        )
        out = v1.head()
        out += '  grf_observe(c,"R0","runtime effect authority is denied","MEASURED")\n'
        out += f'  grf_generate(c,"R2",{v1.q(op)})\n'
        out += '  let w = omega_new(c,"w0")\n'
        out += f'  omega_bind(w,"operation",{v1.q(op)})\n'
        out += '  omega_schema(w,"tool.generic/v1")\n'
        out += '  omega_authority(w,cfg("architecture.effect_authority"))\n'
        out += '  omega_generation(w,cfg("state.generation"))\n'
        out += '  omega_validate(w,"grammar")\n'
        out += '  omega_validate(w,"types")\n'
        out += '  omega_validate(w,"schema")\n'
        out += '  omega_validate(w,"authority")\n'
        out += '  omega_reject(w,"authority_denied")\n'
        out += '  focus_set(c,"reject_at_authority_gate")\n' + v1.tail()
        xs.append(v1.row(prompt, out, "omega_authority_reject"))

    # Generation mismatch must lose even when every earlier gate is satisfied.
    for i in range(80):
        current = 200 + i
        stale = current - 1
        prompt = (
            f"Current canonical generation is {current}; candidate action carries stale generation {stale}. "
            "All earlier gates are valid. Reject the stale writer."
        )
        out = v1.head()
        out += f'  grf_observe(c,"R0","canonical generation {current}","MEASURED")\n'
        out += f'  grf_generate(c,"R2","candidate generation {stale}")\n'
        out += '  let w = omega_new(c,"w0")\n'
        out += '  omega_bind(w,"operation","state.update")\n'
        out += '  omega_schema(w,"tool.state.update/v1")\n'
        out += '  omega_authority(w,cfg("architecture.effect_authority"))\n'
        out += f'  omega_generation(w,{stale})\n'
        out += '  omega_validate(w,"grammar")\n'
        out += '  omega_validate(w,"types")\n'
        out += '  omega_validate(w,"schema")\n'
        out += '  omega_validate(w,"authority")\n'
        out += '  omega_validate(w,"generation")\n'
        out += '  omega_reject(w,"stale_generation")\n'
        out += '  focus_set(c,"reject_stale_generation_writer")\n' + v1.tail()
        xs.append(v1.row(prompt, out, "omega_generation_reject"))

    # Missing runtime config must remain missing; the model must not invent operation/authority values.
    for i in range(80):
        key = ("tool.operation", "tool.schema", "architecture.effect_authority", "state.generation")[i % 4]
        prompt = f"Required runtime cfg {key} is absent. Preserve UNKNOWN and reject instead of guessing a value."
        out = v1.head()
        out += f'  grf_observe(c,"R0",{v1.q("missing runtime cfg " + key)},"MEASURED")\n'
        out += f'  unknown_preserve(c,{v1.q(key)},"missing_runtime_cfg")\n'
        out += '  let w = omega_new(c,"w0")\n'
        out += '  omega_bind(w,"operation",cfg("tool.operation"))\n'
        out += '  omega_reject(w,"missing_runtime_cfg")\n'
        out += '  focus_set(c,"do_not_invent_runtime_configuration")\n' + v1.tail()
        xs.append(v1.row(prompt, out, "omega_missing_cfg_reject"))

    # Crash ambiguity is epistemic, not a retry instruction.
    for i in range(80):
        req = f"effect_req_{1000+i}"
        prompt = (
            f"{req} was requested before a crash; no durable completion receipt exists after restart. "
            "Keep the outcome unknown and do not replay blindly."
        )
        out = v1.head()
        out += f'  grf_observe(c,"R0",{v1.q(req + " has no durable completion receipt")},"MEASURED")\n'
        out += '  recovery_state(c,"UNKNOWN_AFTER_CRASH")\n'
        out += '  unknown_preserve(c,"effect_outcome","missing_verified_receipt")\n'
        out += '  policy_select(c,"do_not_replay")\n'
        out += '  authority_bind(c,"effects",cfg("architecture.effect_authority"))\n'
        out += '  focus_set(c,"preserve_unknown_effect_outcome")\n' + v1.tail()
        xs.append(v1.row(prompt, out, "recovery_unknown_no_replay"))

    assert len(xs) == 320
    return xs


def write_rows(v1, path, rows):
    v1.write_rows(path, rows)


def main():
    v1 = load_v1()
    base = v1.build()
    assert len(base) == 1650
    base_train, base_valid = base[:1485], base[1485:]

    aug = build_aug(v1)
    by_family = {}
    for row in aug:
        by_family.setdefault(row["family"], []).append(row)

    aug_train, aug_valid = [], []
    for family in sorted(by_family):
        rows = by_family[family]
        assert len(rows) == 80
        aug_train.extend(rows[:72])
        aug_valid.extend(rows[72:])

    train = base_train + aug_train
    valid = base_valid + aug_valid
    random.Random(SEED).shuffle(train)
    random.Random(SEED + 1).shuffle(valid)

    train_path = HERE / "train_v2.jsonl"
    valid_path = HERE / "validation_v2.jsonl"
    write_rows(v1, train_path, train)
    write_rows(v1, valid_path, valid)

    counts = Counter(x["family"] for x in aug)
    manifest = {
        "schema": "claycog-sft/v2",
        "seed": SEED,
        "derived_from": "claycog-sft/v1",
        "examples": len(train) + len(valid),
        "train": len(train),
        "validation": len(valid),
        "base_examples": len(base),
        "augmentation_examples": len(aug),
        "augmentation_families": dict(sorted(counts.items())),
        "targeted_failure_modes": [
            "authority_denied_after_grammar_types_schema",
            "stale_generation_after_prior_gates",
            "missing_runtime_cfg_no_guess",
            "unknown_after_crash_no_blind_replay",
        ],
        "base_primary": "Qwen/Qwen2.5-0.5B",
        "base_ablation": "Qwen/Qwen2.5-0.5B-Instruct",
        "assistant_target_representation": "ClayCode_only",
        "train_sha256": sha(train_path),
        "validation_sha256": sha(valid_path),
    }
    (HERE / "corpus_manifest_v2.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

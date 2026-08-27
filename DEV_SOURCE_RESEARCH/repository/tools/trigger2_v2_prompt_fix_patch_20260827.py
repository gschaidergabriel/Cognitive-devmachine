"""Patch B0-B6 diagnostic training files for the second Together run, bundling
all fixes identified from the 852-row large-scale holdout evaluation
(research_entity/topic_packets/trigger2-together-diagnostic-finetune-20260827/
LARGE_SCALE_EVAL_852_20260827.json) into ONE run, per owner directive
(max 5 Together runs total, bundle fixes rather than testing piecemeal).

Fix wording proposal sourced from ~/last-resort/llm.py pool (Groq tier this
call), reviewed and adapted here -- not applied blind. Applies deterministic,
reviewable string substitution to the `prompt` field only; `target` is
untouched (the correct answers do not change, only the prompt surface).
"""
import json
import re

SRC_DIR = "research_entity/claycode/training"

# --- BUG 1 fix: B3 code-derailment (120/120 failed, 0% validated) ---
B3_SUBS = [
    (r"\bCODEBOOK \(entry points\)", "LEXICON (entry points)"),
    (r"\bCHAIN \(pointer definitions\)", "LINK_SEQUENCE (reference definitions)"),
    (r"\bPTR_", "REF_"),
    (r"\bDereference the full chain\b", "Resolve the full link sequence"),
    (r"\ban intermediate pointer token\b", "an intermediate reference token"),
    (r"\bthe chain does not terminate\b", "the link sequence does not terminate"),
]
B3_NO_CODE_SUFFIX = " Respond with only the atom token -- no code, no explanation, no formatting."

# --- BUG 2 fix: B2_PRIOR_OVERRIDE codebook-key-leak (60/60 failed) ---
B2_PRIOR_OVERRIDE_SUFFIX = " Answer with ONLY the mapped ordinal value from the current codebook; do NOT output the class name (ALLOW/DENY/ABSTAIN) itself."

# --- BUG 3 fix: B4/B5 format collapse (120/120 failed validation) ---
B4_B5_SUFFIX = " Return the answer exactly in the form ABI_ACCEPTED_ORDINAL:<integer>, with no other text."

# --- Bonus, same-root-cause fix: B1 / B2_MID_EPISODE_REMAP (very low validation, 0 correct) ---
GENERIC_FORMAT_SUFFIX = " Respond with only the bound symbol atom -- no code, no explanation."


def apply_subs(text: str, subs: list[tuple[str, str]]) -> str:
    for pat, repl in subs:
        text = re.sub(pat, repl, text)
    return text


def patch_file(in_name: str, out_name: str, *, subs=None, suffix=None):
    in_path = f"{SRC_DIR}/{in_name}"
    out_path = f"{SRC_DIR}/{out_name}"
    n = 0
    changed = 0
    with open(in_path) as f, open(out_path, "w") as out:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            orig_prompt = d["prompt"]
            new_prompt = orig_prompt
            if subs:
                new_prompt = apply_subs(new_prompt, subs)
            if suffix and not new_prompt.rstrip().endswith(suffix.strip()):
                new_prompt = new_prompt.rstrip() + suffix
            if new_prompt != orig_prompt:
                changed += 1
            d["prompt"] = new_prompt
            d["provenance_ancestry_id"] = d.get("provenance_ancestry_id", "") + "-v2-fix-20260827"
            out.write(json.dumps(d, ensure_ascii=False) + "\n")
            n += 1
    print(f"{in_name} -> {out_name}: {n} rows, {changed} prompts changed")
    return n, changed


results = []
results.append(patch_file(
    "TRIGGER2_B3_MULTI_HOP_DEREF_CANDIDATE_V1.jsonl",
    "TRIGGER2_B3_MULTI_HOP_DEREF_CANDIDATE_V2.jsonl",
    subs=B3_SUBS, suffix=B3_NO_CODE_SUFFIX,
))
results.append(patch_file(
    "TRIGGER2_B3_UNRESOLVABLE_CHAIN_REJECTION_CANDIDATE_V1.jsonl",
    "TRIGGER2_B3_UNRESOLVABLE_CHAIN_REJECTION_CANDIDATE_V2.jsonl",
    subs=B3_SUBS, suffix=B3_NO_CODE_SUFFIX,
))
results.append(patch_file(
    "TRIGGER2_B2_PRIOR_OVERRIDE_CANDIDATE_V1.jsonl",
    "TRIGGER2_B2_PRIOR_OVERRIDE_CANDIDATE_V2.jsonl",
    suffix=B2_PRIOR_OVERRIDE_SUFFIX,
))
results.append(patch_file(
    "TRIGGER2_B4_CAPACITY_INTERFERENCE_CANDIDATE_V1.jsonl",
    "TRIGGER2_B4_CAPACITY_INTERFERENCE_CANDIDATE_V2.jsonl",
    suffix=B4_B5_SUFFIX,
))
results.append(patch_file(
    "TRIGGER2_B5_VARIABLE_N_EQUIVARIANCE_CANDIDATE_V1.jsonl",
    "TRIGGER2_B5_VARIABLE_N_EQUIVARIANCE_CANDIDATE_V2.jsonl",
    suffix=B4_B5_SUFFIX,
))
results.append(patch_file(
    "TRIGGER2_B1_TRAIN_BALANCED_2ORDER_V1.jsonl",
    "TRIGGER2_B1_TRAIN_BALANCED_2ORDER_V2.jsonl",
    suffix=GENERIC_FORMAT_SUFFIX,
))
results.append(patch_file(
    "TRIGGER2_B2_MID_EPISODE_REMAP_CANDIDATE_V1.jsonl",
    "TRIGGER2_B2_MID_EPISODE_REMAP_CANDIDATE_V2.jsonl",
    suffix=GENERIC_FORMAT_SUFFIX,
))

total_rows = sum(r[0] for r in results)
total_changed = sum(r[1] for r in results)
print(f"\nTOTAL: {total_rows} rows across 7 patched families, {total_changed} prompts actually modified")

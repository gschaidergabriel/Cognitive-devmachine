import json, sys, time, traceback

print("loading libs...", flush=True)
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE = "huihui-ai/Huihui-Qwen3.5-0.8B-abliterated"
BASE_REV = "4813135658fe51b2e535b8e77927d2f23909ce42"
ADAPTER_DIR = "/workspace/trigger2_diag_adapter"
HOLDOUT_PATH = "/workspace/trigger2_diag_adapter/holdout_sample.json"
OUT_PATH = "/workspace/trigger2_diag_adapter/holdout_results.json"

print(f"loading tokenizer from {BASE}@{BASE_REV} ...", flush=True)
tok = AutoTokenizer.from_pretrained(BASE, revision=BASE_REV)

print("loading base model (this downloads ~1.7GB, may take a while on CPU)...", flush=True)
t0 = time.time()
base_model = AutoModelForCausalLM.from_pretrained(
    BASE, revision=BASE_REV, torch_dtype=torch.bfloat16, low_cpu_mem_usage=True
)
print(f"base model loaded in {time.time()-t0:.1f}s", flush=True)

print("loading LoRA adapter...", flush=True)
model = PeftModel.from_pretrained(base_model, ADAPTER_DIR)
model.eval()
print("adapter loaded and merged into inference graph.", flush=True)

with open(HOLDOUT_PATH) as f:
    rows = json.load(f)

results = []
for i, row in enumerate(rows):
    prompt = row["prompt"]
    expected = row["expected_target"]
    messages = [{"role": "user", "content": prompt}]
    input_ids = tok.apply_chat_template(
        messages, add_generation_prompt=True, return_tensors="pt"
    )
    if hasattr(input_ids, "input_ids"):
        input_ids = input_ids.input_ids
    t0 = time.time()
    with torch.no_grad():
        out = model.generate(
            input_ids,
            max_new_tokens=24,
            do_sample=False,
            temperature=None,
            top_p=None,
            pad_token_id=tok.pad_token_id or tok.eos_token_id,
        )
    gen_ids = out[0][input_ids.shape[1]:]
    gen_text = tok.decode(gen_ids, skip_special_tokens=True).strip()
    dt = time.time() - t0
    correct = gen_text == expected or gen_text.startswith(expected)
    rec = {
        "source_file": row["source_file"],
        "id": row["id"],
        "prompt": prompt,
        "expected_target": expected,
        "generated": gen_text,
        "exact_or_prefix_match": correct,
        "gen_seconds": round(dt, 1),
    }
    results.append(rec)
    print(f"[{i+1}/{len(rows)}] {row['source_file']} expected={expected!r} got={gen_text!r} match={correct} ({dt:.1f}s)", flush=True)

n_correct = sum(1 for r in results if r["exact_or_prefix_match"])
summary = {
    "base_model": BASE,
    "base_model_revision": BASE_REV,
    "adapter_dir": ADAPTER_DIR,
    "n_rows": len(results),
    "n_correct_exact_or_prefix": n_correct,
    "accuracy": n_correct / len(results) if results else None,
    "results": results,
}
with open(OUT_PATH, "w") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print(json.dumps({"n_rows": len(results), "n_correct": n_correct, "accuracy": summary["accuracy"]}, indent=2))
print(f"full results written to {OUT_PATH}", flush=True)

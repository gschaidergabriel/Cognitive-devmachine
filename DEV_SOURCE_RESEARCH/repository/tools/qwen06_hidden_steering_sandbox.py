#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import platform
import re
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_sha(obj: Any) -> str:
    return sha256_bytes(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def git_head(path: Path) -> str | None:
    try:
        return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    p.add_argument("--model-id", default="Qwen/Qwen3-0.6B")
    p.add_argument("--hf-cache", default=os.getenv("HF_HOME", "/artifacts/clay-qwen06-jspace/hf"))
    p.add_argument("--max-new-tokens", type=int, default=28)
    p.add_argument("--threads", type=int, default=max(1, min(8, os.cpu_count() or 1)))
    return p.parse_args()


def main() -> int:
    args = parse_args()
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = args.hf_cache

    import torch
    import transformers
    import huggingface_hub
    from huggingface_hub import snapshot_download
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(args.threads)
    try:
        torch.set_num_interop_threads(max(1, min(4, args.threads)))
    except RuntimeError:
        pass

    started = dt.datetime.now(dt.timezone.utc)
    source_repo = Path(os.getenv("GITHUB_WORKSPACE", Path(__file__).resolve().parents[1]))

    snapshot = Path(snapshot_download(repo_id=args.model_id, revision="main", cache_dir=args.hf_cache))
    revision = snapshot.name

    tokenizer = AutoTokenizer.from_pretrained(str(snapshot), local_files_only=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(
        str(snapshot),
        local_files_only=True,
        trust_remote_code=False,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
    )
    model.eval()
    model.to("cpu")

    layers = model.model.layers
    n_layers = len(layers)
    hidden_size = int(model.config.hidden_size)

    source_packet = {
        "schema": "JSPACE_VECTOR_CONTROL_ABI/v1",
        "intent_id": "LANGUAGE_DIRECTION_DE_VS_EN",
        "intent": "increase German-language latent/output tendency relative to English without prompt text modification",
        "target_model": args.model_id,
        "adapter_class": "MODEL_UNEMBEDDING_LANGUAGE_BASIS/v1",
        "calibration_policy": "select layer and gain on calibration prompts only",
        "holdout_policy": "disjoint prompts; BASELINE,+VECTOR,SIGN_FLIP,NULL_VECTOR,ORTHOGONAL_SAME_NORM,PERMUTED_SAME_NORM",
    }
    source_packet_sha = canonical_sha(source_packet)

    de_terms = [" der", " die", " und", " ist", " nicht", " ein", " das", " mit"]
    en_terms = [" the", " and", " is", " not", " a", " of", " with", " that"]

    def term_token_ids(terms: list[str]) -> list[int]:
        ids: list[int] = []
        for term in terms:
            enc = tokenizer.encode(term, add_special_tokens=False)
            if enc:
                ids.append(int(enc[-1]))
        return sorted(set(ids))

    de_ids = term_token_ids(de_terms)
    en_ids = term_token_ids(en_terms)
    if not de_ids or not en_ids:
        raise RuntimeError("failed to resolve language basis token ids")

    out_emb = model.get_output_embeddings().weight.detach().float().cpu()
    raw_vector = out_emb[de_ids].mean(dim=0) - out_emb[en_ids].mean(dim=0)
    raw_norm = float(torch.linalg.vector_norm(raw_vector))
    if not math.isfinite(raw_norm) or raw_norm <= 0:
        raise RuntimeError("invalid steering vector norm")
    unit_vector = raw_vector / raw_norm

    generator = torch.Generator(device="cpu").manual_seed(424242)
    orth = torch.randn(hidden_size, generator=generator)
    orth = orth - torch.dot(orth, unit_vector) * unit_vector
    orth = orth / torch.linalg.vector_norm(orth)
    perm = unit_vector[torch.randperm(hidden_size, generator=generator)]
    perm = perm / torch.linalg.vector_norm(perm)
    null = torch.zeros_like(unit_vector)

    vector_sha = sha256_bytes(unit_vector.numpy().tobytes(order="C"))
    orth_sha = sha256_bytes(orth.numpy().tobytes(order="C"))
    perm_sha = sha256_bytes(perm.numpy().tobytes(order="C"))
    null_sha = sha256_bytes(null.numpy().tobytes(order="C"))

    adapter_packet = {
        "schema": "JSPACE_LATENT_BASIS_ADAPTER/v1",
        "model_id": args.model_id,
        "model_revision": revision,
        "hidden_size": hidden_size,
        "positive_terms": de_terms,
        "negative_terms": en_terms,
        "positive_token_ids": de_ids,
        "negative_token_ids": en_ids,
        "basis_construction": "mean(output_embedding[positive_token_ids])-mean(output_embedding[negative_token_ids]); L2 normalize",
        "vector_sha256": vector_sha,
        "source_packet_sha256": source_packet_sha,
    }
    adapter_packet_sha = canonical_sha(adapter_packet)

    calibration_prompts = [
        "Write one short sentence about why people keep notes.",
        "Give one short sentence describing a quiet morning.",
    ]
    holdout_prompts = [
        "Describe a bicycle in one short sentence.",
        "Explain why clean water matters in one short sentence.",
        "Write one short sentence about a small garden.",
    ]

    def prompt_ids(prompt: str) -> torch.Tensor:
        messages = [{"role": "user", "content": prompt}]
        try:
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        except TypeError:
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        return tokenizer(text, return_tensors="pt").input_ids

    class HookState:
        def __init__(self) -> None:
            self.calls = 0
            self.modified_calls = 0
            self.modified_positions = 0

    def install_hook(layer_idx: int, vec: torch.Tensor, gain: float):
        state = HookState()
        delta = (vec * float(gain)).float()

        def hook(_module, _inputs, output):
            state.calls += 1
            if isinstance(output, tuple):
                h = output[0]
                rest = output[1:]
            else:
                h = output
                rest = None
            if not torch.is_tensor(h):
                return output
            d = delta.to(device=h.device, dtype=h.dtype)
            h2 = h.clone()
            h2[:, -1, :] = h2[:, -1, :] + d
            state.modified_calls += 1
            state.modified_positions += int(h2.shape[0])
            if rest is None:
                return h2
            return (h2, *rest)

        handle = layers[layer_idx].register_forward_hook(hook)
        return handle, state

    def next_token_direction(prompt: str, layer_idx: int | None, vec: torch.Tensor | None, gain: float) -> tuple[float, dict[str, int]]:
        inp = prompt_ids(prompt)
        state = HookState()
        handle = None
        if layer_idx is not None and vec is not None:
            handle, state = install_hook(layer_idx, vec, gain)
        try:
            with torch.inference_mode():
                logits = model(input_ids=inp, use_cache=False).logits[0, -1].float().cpu()
            score = float(logits[de_ids].mean() - logits[en_ids].mean())
            return score, {"hook_calls": state.calls, "modified_calls": state.modified_calls, "modified_positions": state.modified_positions}
        finally:
            if handle is not None:
                handle.remove()

    candidate_layers = sorted(set([max(0, n_layers // 3), max(0, n_layers // 2), max(0, (2 * n_layers) // 3), max(0, n_layers - 2)]))
    candidate_gains = [2.0, 6.0, 12.0]
    calibration_rows: list[dict[str, Any]] = []
    best: tuple[float, int, float] | None = None
    for li in candidate_layers:
        for gain in candidate_gains:
            vals = []
            hooks = []
            for p in calibration_prompts:
                s, h = next_token_direction(p, li, unit_vector, gain)
                vals.append(s)
                hooks.append(h)
            mean_score = sum(vals) / len(vals)
            row = {"layer": li, "gain": gain, "scores": vals, "mean_direction_score": mean_score, "hook_receipts": hooks}
            calibration_rows.append(row)
            candidate = (mean_score, li, gain)
            if best is None or candidate[0] > best[0]:
                best = candidate
    assert best is not None
    selected_score, selected_layer, selected_gain = best

    conditions = {
        "BASELINE": None,
        "+VECTOR": unit_vector,
        "SIGN_FLIP": -unit_vector,
        "NULL_VECTOR": null,
        "ORTHOGONAL_SAME_NORM": orth,
        "PERMUTED_SAME_NORM": perm,
    }
    condition_vector_sha = {
        "BASELINE": None,
        "+VECTOR": vector_sha,
        "SIGN_FLIP": sha256_bytes((-unit_vector).numpy().tobytes(order="C")),
        "NULL_VECTOR": null_sha,
        "ORTHOGONAL_SAME_NORM": orth_sha,
        "PERMUTED_SAME_NORM": perm_sha,
    }

    german_lex = re.compile(r"\b(der|die|das|und|ist|nicht|ein|eine|mit|für|auf|von|zu|im|den|des)\b", re.I)
    english_lex = re.compile(r"\b(the|and|is|not|a|an|with|for|on|of|to|in|this|that)\b", re.I)

    def generate_one(prompt: str, condition: str, vec: torch.Tensor | None, seed: int) -> dict[str, Any]:
        inp = prompt_ids(prompt)
        torch.manual_seed(seed)
        state = HookState()
        handle = None
        if vec is not None:
            handle, state = install_hook(selected_layer, vec, selected_gain)
        try:
            with torch.inference_mode():
                out = model.generate(
                    input_ids=inp,
                    max_new_tokens=args.max_new_tokens,
                    do_sample=True,
                    temperature=0.8,
                    top_p=0.9,
                    use_cache=True,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                )
            new_tokens = out[0, inp.shape[1]:]
            text = tokenizer.decode(new_tokens, skip_special_tokens=True)
        finally:
            if handle is not None:
                handle.remove()
        g = len(german_lex.findall(text))
        e = len(english_lex.findall(text))
        first_score, first_hook = next_token_direction(prompt, selected_layer if vec is not None else None, vec, selected_gain if vec is not None else 0.0)
        return {
            "prompt": prompt,
            "condition": condition,
            "seed": seed,
            "text": text,
            "german_lex_count": g,
            "english_lex_count": e,
            "lexical_direction_score": g - e,
            "first_token_direction_score": first_score,
            "generation_hook_receipt": {"hook_calls": state.calls, "modified_calls": state.modified_calls, "modified_positions": state.modified_positions},
            "first_token_hook_receipt": first_hook,
            "applied_vector_sha256": condition_vector_sha[condition],
        }

    holdout_rows: list[dict[str, Any]] = []
    for prompt in holdout_prompts:
        for seed in (17, 23):
            for name, vec in conditions.items():
                holdout_rows.append(generate_one(prompt, name, vec, seed))

    summary: dict[str, dict[str, float]] = {}
    for name in conditions:
        rows = [r for r in holdout_rows if r["condition"] == name]
        summary[name] = {
            "mean_first_token_direction_score": sum(r["first_token_direction_score"] for r in rows) / len(rows),
            "mean_lexical_direction_score": sum(r["lexical_direction_score"] for r in rows) / len(rows),
        }

    b = summary["BASELINE"]["mean_first_token_direction_score"]
    plus = summary["+VECTOR"]["mean_first_token_direction_score"] - b
    sign = summary["SIGN_FLIP"]["mean_first_token_direction_score"] - b
    nulld = summary["NULL_VECTOR"]["mean_first_token_direction_score"] - b
    orthd = summary["ORTHOGONAL_SAME_NORM"]["mean_first_token_direction_score"] - b
    permd = summary["PERMUTED_SAME_NORM"]["mean_first_token_direction_score"] - b
    control_max = max(abs(orthd), abs(permd), 1e-9)
    positive = bool(plus > 0.25 and sign < -0.25 and abs(nulld) < 1e-5 and plus > 1.25 * control_max and abs(sign) > 1.25 * control_max)

    file_digests: dict[str, dict[str, Any]] = {}
    for pattern in ("config.json", "generation_config.json", "tokenizer.json", "tokenizer_config.json", "*.safetensors"):
        for p in snapshot.glob(pattern):
            if p.name in file_digests:
                continue
            file_digests[p.name] = {"sha256": sha256_file(p), "size": p.stat().st_size}

    finished = dt.datetime.now(dt.timezone.utc)
    receipt = {
        "schema": "CLAY_QWEN06_HIDDEN_STEERING_SANDBOX_RECEIPT/v1",
        "status": "EXECUTED",
        "claim_positive": positive,
        "generated_at": finished.isoformat(),
        "started_at": started.isoformat(),
        "duration_seconds": (finished - started).total_seconds(),
        "execution_surface": "clay-direct-dev self-hosted runner",
        "runner": {
            "hostname": socket.gethostname(),
            "user": os.getenv("USER"),
            "platform": platform.platform(),
            "python": sys.version,
            "threads": args.threads,
            "github_run_id": os.getenv("GITHUB_RUN_ID"),
            "github_sha": os.getenv("GITHUB_SHA"),
            "repo_head": git_head(source_repo),
        },
        "runtime": {
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "huggingface_hub": huggingface_hub.__version__,
        },
        "model": {
            "id": args.model_id,
            "snapshot_revision": revision,
            "snapshot_path": str(snapshot),
            "hidden_size": hidden_size,
            "num_layers": n_layers,
            "file_digests": file_digests,
        },
        "source_packet": source_packet,
        "source_packet_sha256": source_packet_sha,
        "adapter_packet": adapter_packet,
        "adapter_packet_sha256": adapter_packet_sha,
        "vector_identity": {
            "raw_norm": raw_norm,
            "unit_vector_sha256": vector_sha,
            "null_vector_sha256": null_sha,
            "orthogonal_same_norm_sha256": orth_sha,
            "permuted_same_norm_sha256": perm_sha,
        },
        "calibration": {
            "prompts": calibration_prompts,
            "candidate_layers": candidate_layers,
            "candidate_gains": candidate_gains,
            "rows": calibration_rows,
            "selected_layer": selected_layer,
            "selected_gain": selected_gain,
            "selected_mean_direction_score": selected_score,
        },
        "holdout": {
            "prompts": holdout_prompts,
            "seeds": [17, 23],
            "conditions": list(conditions),
            "rows": holdout_rows,
            "summary": summary,
        },
        "effect": {
            "plus_minus_baseline": plus,
            "sign_flip_minus_baseline": sign,
            "null_minus_baseline": nulld,
            "orthogonal_minus_baseline": orthd,
            "permuted_minus_baseline": permd,
            "same_norm_control_max_abs": control_max,
            "promotion_rule": "+vector>0.25, signflip<-0.25, exact-null ~ baseline, both directional effects >1.25x same-norm control max",
            "direct_reproducible_hidden_state_steering_demonstrated": positive,
        },
        "evidence_boundary": "Direct layer forward-hook intervention with exact vector identity. This is model-runtime causal component evidence only, not whole EntityOS/HCU PASS or consciousness evidence.",
        "paid_provider_calls": 0,
        "together_used": False,
    }
    receipt["receipt_sha256"] = canonical_sha(receipt)
    out_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "claim_positive": positive, "model_revision": revision, "selected_layer": selected_layer, "selected_gain": selected_gain, "effect": receipt["effect"], "receipt_sha256": receipt["receipt_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

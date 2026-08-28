#!/usr/bin/env python3
"""Bounded Trigger-1 FREE Qwen3-0.6B hosted output-logit vector experiment.

This is a real provider-network experiment, but its credit scope is deliberately
narrow: direct numeric output-logit intervention only. It does not claim hidden-
state/cvec/J-Space model-runtime causality. The process must be launched through
free_swarm_exec_with_vault.py so the parent/orchestrator remains credential-blind.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any

from free_lane_provenance import (
    binding_still_current,
    current_lane_binding,
    emit_execution_receipt,
)
from free_swarm_quota import observe as quota_observe, slot as quota_slot
from trigger1_openrouter_logit_bias_control import control_family

ROOT = Path(__file__).resolve().parents[1]
PROVIDER = "openrouter"
MODEL = "qwen/qwen3-0.6b-04-28:free"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
HF_REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"
TOKENIZER_SHA256 = "aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4"
TOKENIZER_URL = f"https://huggingface.co/Qwen/Qwen3-0.6B/resolve/{HF_REVISION}/tokenizer.json?download=true"
SCHEMA = "CLAY_TRIGGER1_OPENROUTER_QWEN06_LOGIT_VECTOR_EXPERIMENT/v1"
CREDIT_SCOPE = "DIRECT_HOSTED_OUTPUT_LOGIT_VECTOR_CONTROL_COMPONENT_ONLY"
CALIBRATION_GAINS = (4.0, 12.0, 24.0)
CALIBRATION_SEED = 1701
HOLDOUT_SEEDS = (2718, 3141)
CONTROLS = (
    "BASELINE",
    "+VECTOR",
    "SIGN_FLIP",
    "NULL_VECTOR",
    "ORTHOGONAL_SAME_NORM",
    "PERMUTED_SAME_NORM",
)


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_sha(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())


def git_text(*args: str) -> str:
    try:
        p = subprocess.run(["git", "-C", str(ROOT), *args], text=True, stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, timeout=5, check=False)
        return p.stdout.strip() or "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def key_fingerprint(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()[:10]


def fetch_tokenizer() -> tuple[dict[str, Any], bytes]:
    req = urllib.request.Request(TOKENIZER_URL, headers={"User-Agent": "clay-trigger1/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
    got = sha256_bytes(raw)
    if got != TOKENIZER_SHA256:
        raise RuntimeError(f"TOKENIZER_SHA256_MISMATCH:{got}")
    obj = json.loads(raw.decode("utf-8"))
    return obj, raw


def resolve_token_ids(tokenizer: dict[str, Any]) -> dict[str, int]:
    model = tokenizer.get("model") if isinstance(tokenizer, dict) else None
    vocab = model.get("vocab") if isinstance(model, dict) else None
    if not isinstance(vocab, dict):
        raise RuntimeError("TOKENIZER_VOCAB_UNAVAILABLE")
    out: dict[str, int] = {}
    for token in ("A", "B", "C"):
        value = vocab.get(token)
        if isinstance(value, int) and value >= 0:
            out[token] = value
    if set(out) != {"A", "B", "C"}:
        raise RuntimeError(f"SINGLE_TOKEN_ABC_NOT_AVAILABLE:{sorted(out)}")
    if len(set(out.values())) != 3:
        raise RuntimeError("ABC_TOKEN_IDS_NOT_DISTINCT")
    return out


def request_id(headers: dict[str, str], payload: Any) -> str | None:
    for k in ("x-request-id", "request-id", "cf-ray"):
        if headers.get(k):
            return headers[k]
    if isinstance(payload, dict):
        for k in ("id", "request_id"):
            if payload.get(k):
                return str(payload[k])
    return None


def usage_from(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict) and isinstance(payload.get("usage"), dict):
        return payload["usage"]
    return {}


def extract_observation(payload: Any) -> dict[str, Any]:
    choice = ((payload or {}).get("choices") or [{}])[0] if isinstance(payload, dict) else {}
    message = choice.get("message") or {}
    content = str(message.get("content") or "")
    logprobs = choice.get("logprobs") or {}
    rows = logprobs.get("content") if isinstance(logprobs, dict) else None
    first = rows[0] if isinstance(rows, list) and rows else {}
    tops = first.get("top_logprobs") if isinstance(first, dict) else None
    top_map: dict[str, float] = {}
    if isinstance(tops, list):
        for row in tops:
            if isinstance(row, dict) and isinstance(row.get("token"), str):
                try:
                    top_map[row["token"]] = float(row.get("logprob"))
                except (TypeError, ValueError):
                    pass
    token = first.get("token") if isinstance(first, dict) else None
    return {
        "content_prefix": content[:32],
        "first_token": token,
        "top_logprobs": top_map,
        "finish_reason": choice.get("finish_reason"),
        "provider": payload.get("provider") if isinstance(payload, dict) else None,
    }


def target_score(obs: dict[str, Any]) -> float:
    tops = obs.get("top_logprobs") or {}
    if isinstance(tops, dict) and "A" in tops:
        competitors = [float(tops[x]) for x in ("B", "C") if x in tops]
        if competitors:
            return float(tops["A"]) - sum(competitors) / len(competitors)
    token = str(obs.get("first_token") or "")
    content = str(obs.get("content_prefix") or "").lstrip()
    if token == "A" or content.startswith("A"):
        return 1.0
    if token in {"B", "C"} or content.startswith(("B", "C")):
        return -1.0
    return 0.0


def build_body(*, prompt: str, seed: int, vector: dict[str, float], control: str) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1,
        "temperature": 0,
        "seed": seed,
        "logprobs": True,
        "top_logprobs": 20,
        "provider": {
            "require_parameters": True,
            "allow_fallbacks": False,
        },
    }
    if control != "BASELINE":
        body["logit_bias"] = vector
    return body


def provider_call(key: str, body: dict[str, Any], *, owner: str) -> tuple[int, dict[str, str], Any]:
    raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=raw,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "clay-trigger1-jspace/1.0",
            "HTTP-Referer": "https://github.com/gschaidergabriel/clay-global-research-entity",
            "X-Title": "Clay Trigger-1 Qwen3-0.6B vector discriminator",
        },
    )
    try:
        with quota_slot(PROVIDER, owner, timeout_s=60.0, lease_s=120.0):
            try:
                with urllib.request.urlopen(req, timeout=90) as resp:
                    status = int(resp.status)
                    headers = {str(k).lower(): str(v) for k, v in resp.headers.items()}
                    payload = json.loads(resp.read().decode("utf-8", errors="replace"))
            except urllib.error.HTTPError as exc:
                status = int(exc.code)
                headers = {str(k).lower(): str(v) for k, v in exc.headers.items()} if exc.headers else {}
                text = exc.read().decode("utf-8", errors="replace")
                try:
                    payload = json.loads(text)
                except Exception:
                    payload = {"error": {"message": text[:1600]}}
        quota_observe(PROVIDER, owner, status, headers)
        return status, headers, payload
    except TimeoutError:
        quota_observe(PROVIDER, owner, "GATE_TIMEOUT", {})
        return 503, {}, {"error": {"message": "shared provider gate timeout"}}


def run_one(*, key: str, fp: str, prompt: str, seed: int, vector: dict[str, float], control: str,
            call_index: int, receipts_dir: Path, source: dict[str, str]) -> dict[str, Any]:
    binding = current_lane_binding(PROVIDER, fp, MODEL, ENDPOINT, artifacts=receipts_dir)
    if not binding.get("ok"):
        return {
            "call_index": call_index,
            "control": control,
            "seed": seed,
            "network_attempted": False,
            "status": "BLOCKED_PRE_NETWORK",
            "reason": binding.get("reason"),
            "binding": binding,
        }
    if not binding_still_current(binding):
        return {
            "call_index": call_index,
            "control": control,
            "seed": seed,
            "network_attempted": False,
            "status": "BLOCKED_AUTHORITY_MOVED",
        }
    body = build_body(prompt=prompt, seed=seed, vector=vector, control=control)
    body_sha = canonical_sha(body)
    owner = f"trigger1-qwen06:{call_index}:{control}:{seed}"
    status, headers, payload = provider_call(key, body, owner=owner)
    stable = binding_still_current(binding)
    payload_digest = canonical_sha(payload)
    receipt = emit_execution_receipt(
        provider=PROVIDER,
        credential_fingerprint=fp,
        model_or_route=MODEL,
        endpoint=ENDPOINT,
        binding=binding,
        request_id=request_id(headers, payload),
        usage=usage_from(payload),
        http_status=status,
        result_digest=payload_digest,
        source_commit_and_tree=source,
        binding_stable_after_call=stable,
        artifacts=receipts_dir,
    )
    row = {
        "call_index": call_index,
        "control": control,
        "seed": seed,
        "request_body_sha256": body_sha,
        "control_vector_sha256": canonical_sha(vector),
        "network_attempted": True,
        "http_status": status,
        "binding_stable_after_call": stable,
        "request_id": receipt.get("request_id"),
        "usage": usage_from(payload),
        "result_digest": payload_digest,
    }
    if 200 <= status < 300:
        row["observation"] = extract_observation(payload)
        row["score"] = target_score(row["observation"])
        row["status"] = "SUCCESS"
    else:
        row["status"] = "PROVIDER_REJECTED"
        err = payload.get("error") if isinstance(payload, dict) else None
        row["error"] = str(err)[:1000]
    return row


def scaled_base_vector(ids: dict[str, int], gain: float) -> dict[str, float]:
    # 3-axis vector keeps SIGN_FLIP and PERMUTED controls distinct.
    return {
        str(ids["A"]): float(gain),
        str(ids["B"]): float(-0.50 * gain),
        str(ids["C"]): float(-0.25 * gain),
    }


def select_gain(rows: list[dict[str, Any]]) -> float | None:
    by_gain: dict[float, dict[str, float]] = {}
    for row in rows:
        if row.get("status") != "SUCCESS":
            continue
        gain = float(row["gain"])
        by_gain.setdefault(gain, {})[str(row["control"])] = float(row.get("score") or 0.0)
    ranked = []
    for gain in CALIBRATION_GAINS:
        got = by_gain.get(gain, {})
        if "+VECTOR" in got and "SIGN_FLIP" in got:
            ranked.append((got["+VECTOR"] - got["SIGN_FLIP"], gain))
    if not ranked:
        return None
    ranked.sort(reverse=True)
    return ranked[0][1] if ranked[0][0] > 0 else None


def adjudicate(calibration: list[dict[str, Any]], holdout: list[dict[str, Any]], selected_gain: float | None) -> dict[str, Any]:
    if selected_gain is None:
        return {"pass": False, "classification": "NO_DIRECTIONAL_CALIBRATION_GAIN"}
    if any(row.get("status") != "SUCCESS" for row in calibration + holdout):
        failures = [
            {"call_index": r.get("call_index"), "control": r.get("control"), "status": r.get("status"),
             "http_status": r.get("http_status"), "reason": r.get("reason"), "error": r.get("error")}
            for r in calibration + holdout if r.get("status") != "SUCCESS"
        ]
        return {"pass": False, "classification": "INCOMPLETE_CONTROL_FAMILY", "failures": failures}
    grouped: dict[str, list[float]] = {c: [] for c in CONTROLS}
    observations: dict[str, list[str]] = {c: [] for c in CONTROLS}
    for row in holdout:
        c = str(row["control"])
        grouped[c].append(float(row.get("score") or 0.0))
        observations[c].append(str((row.get("observation") or {}).get("first_token") or (row.get("observation") or {}).get("content_prefix") or ""))
    means = {c: sum(v) / len(v) if v else float("nan") for c, v in grouped.items()}
    null_matches_baseline = observations["NULL_VECTOR"] == observations["BASELINE"]
    directional_gap = means["+VECTOR"] - means["SIGN_FLIP"]
    nuisance_best = max(means["ORTHOGONAL_SAME_NORM"], means["PERMUTED_SAME_NORM"])
    specificity_gap = means["+VECTOR"] - nuisance_best
    stable = all(bool(row.get("binding_stable_after_call")) for row in calibration + holdout)
    passed = bool(
        stable
        and null_matches_baseline
        and directional_gap > 0
        and specificity_gap > 0
        and all(score > 0 for score in grouped["+VECTOR"])
    )
    return {
        "pass": passed,
        "classification": "DIRECT_OUTPUT_LOGIT_VECTOR_EFFECT_REPRODUCED" if passed else "CONTROL_FAMILY_DID_NOT_ESTABLISH_SPECIFIC_DIRECTIONAL_EFFECT",
        "selected_gain": selected_gain,
        "mean_scores": means,
        "directional_gap_vs_sign_flip": directional_gap,
        "specificity_gap_vs_best_same_norm_control": specificity_gap,
        "null_matches_baseline_exact_first_token": null_matches_baseline,
        "binding_stable_all_calls": stable,
        "holdout_first_tokens": observations,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    receipts_dir = out_path.parent / "free_lane_receipts"

    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        result = {"schema": SCHEMA, "status": "BLOCKED", "reason": "OPENROUTER_API_KEY_NOT_MATERIALIZED_IN_PROVIDER_CHILD", "secret_exposed": False}
        out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return 4
    fp = key_fingerprint(key)
    source = {"commit": git_text("rev-parse", "HEAD"), "tree": git_text("rev-parse", "HEAD^{tree}")}
    started = dt.datetime.now(dt.timezone.utc).isoformat()

    try:
        tokenizer, tokenizer_raw = fetch_tokenizer()
        ids = resolve_token_ids(tokenizer)
    except Exception as exc:
        result = {
            "schema": SCHEMA,
            "status": "BLOCKED",
            "reason": f"TOKENIZER_IDENTITY_OR_DOWNLOAD_BLOCK:{type(exc).__name__}:{str(exc)[:400]}",
            "secret_exposed": False,
            "model": MODEL,
            "hf_revision": HF_REVISION,
            "expected_tokenizer_sha256": TOKENIZER_SHA256,
            "source": source,
        }
        out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return 5

    calibration_prompt = "/no_think\nCalibration split. Output exactly one uppercase letter: A, B, or C. No other text."
    holdout_prompts = {
        HOLDOUT_SEEDS[0]: "/no_think\nHoldout family H1. Return exactly one uppercase token chosen from A, B, C.",
        HOLDOUT_SEEDS[1]: "/no_think\nHoldout family H2. Answer with one uppercase letter only: A, B, or C.",
    }
    calibration: list[dict[str, Any]] = []
    holdout: list[dict[str, Any]] = []
    call_index = 0

    for gain in CALIBRATION_GAINS:
        base_vec = scaled_base_vector(ids, gain)
        family = control_family(base_vec)
        for control in ("+VECTOR", "SIGN_FLIP"):
            call_index += 1
            row = run_one(key=key, fp=fp, prompt=calibration_prompt, seed=CALIBRATION_SEED,
                          vector=family[control], control=control, call_index=call_index,
                          receipts_dir=receipts_dir, source=source)
            row["gain"] = gain
            calibration.append(row)
            if row.get("status") != "SUCCESS":
                break
            time.sleep(1.2)
        if calibration and calibration[-1].get("status") != "SUCCESS":
            break

    selected_gain = select_gain(calibration)
    if selected_gain is not None and all(r.get("status") == "SUCCESS" for r in calibration):
        family = control_family(scaled_base_vector(ids, selected_gain))
        for seed in HOLDOUT_SEEDS:
            for control in CONTROLS:
                call_index += 1
                row = run_one(key=key, fp=fp, prompt=holdout_prompts[seed], seed=seed,
                              vector=family[control], control=control, call_index=call_index,
                              receipts_dir=receipts_dir, source=source)
                row["gain"] = selected_gain
                holdout.append(row)
                if row.get("status") != "SUCCESS":
                    break
                time.sleep(1.2)
            if holdout and holdout[-1].get("status") != "SUCCESS":
                break

    verdict = adjudicate(calibration, holdout, selected_gain)
    finished = dt.datetime.now(dt.timezone.utc).isoformat()
    source_packet = {
        "schema": "TRIGGER1_GLOBAL_JSPACE_OUTPUT_LOGIT_INTENT/v1",
        "axis_labels": ["prefer_A", "suppress_B", "suppress_C"],
        "calibration_only_gain_selection": True,
        "holdout_disjoint": True,
    }
    result = {
        "schema": SCHEMA,
        "status": "PASS" if verdict.get("pass") else "FAIL_OR_BLOCKED",
        "credit_scope": CREDIT_SCOPE,
        "explicit_non_credit": ["HIDDEN_STATE_CVEC", "JSPACE_MODEL_RUNTIME", "WHOLE_HCU", "WHOLE_ENTITYOS", "TRAINING"],
        "started_at": started,
        "finished_at": finished,
        "source": source,
        "provider": PROVIDER,
        "model": MODEL,
        "credential_fingerprint": fp,
        "secret_exposed": False,
        "paid_fallback_attempt_count": 0,
        "provider_fallbacks_allowed": False,
        "require_parameters": True,
        "network_call_budget": 18,
        "network_calls_started": sum(1 for r in calibration + holdout if r.get("network_attempted")),
        "hf_revision": HF_REVISION,
        "tokenizer_sha256": sha256_bytes(tokenizer_raw),
        "token_ids": ids,
        "source_packet": source_packet,
        "source_packet_sha256": canonical_sha(source_packet),
        "calibration_gains": list(CALIBRATION_GAINS),
        "calibration_seed": CALIBRATION_SEED,
        "holdout_seeds": list(HOLDOUT_SEEDS),
        "selected_gain": selected_gain,
        "calibration": calibration,
        "holdout": holdout,
        "verdict": verdict,
    }
    result["result_sha256"] = canonical_sha(result)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "verdict": verdict, "result_sha256": result["result_sha256"]}, sort_keys=True))
    return 0 if verdict.get("pass") else 2


if __name__ == "__main__":
    raise SystemExit(main())

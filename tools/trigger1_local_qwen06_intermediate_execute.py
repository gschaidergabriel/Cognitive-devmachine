#!/usr/bin/env python3
"""Qwen3-0.6B intermediate-layer contrastive Trigger-1 experiment.

This is the stronger causal discriminator after the final-norm readout positive
control. The steering direction is derived only from calibration-set residual
activations at predeclared intermediate decoder layers. No lm_head/output-embedding
row is used to construct the candidate direction.

Layer/gain are frozen on calibration before disjoint holdout. Holdout includes the
six matched controls, label remapping, wrong-layer intervention, and lesion/rescue.
No external provider credential is read and the API boundary is loopback-only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import urllib.request
from typing import Any

from trigger1_local_qwen06_activation_api_execute import (
    MODEL_ID, MODEL_REVISION, TOKENIZER_JSON_SHA256,
    canonical_sha, git_text, load_exact_runtime, runtime_manifest, tensor_sha,
)
from trigger1_intermediate_contrastive_protocol import (
    CREDIT_SCOPE, REQUIRED_CONTROLS, adjudicate_holdout, contrastive_direction,
    control_vectors, digest, select_layer_gain,
)

SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE/v1"
CANDIDATE_SCHEMA = "CLAY_TRIGGER1_INTERMEDIATE_JSPACE_CAUSAL_CANDIDATE/v1"
LABEL_INDEPENDENCE_SCHEMA = "TRIGGER1_VECTOR_DERIVATION_LABEL_INDEPENDENCE/v1"
CANDIDATE_LAYERS = (6, 12, 18, 24)
CALIBRATION_GAINS = (1.0, 4.0, 12.0)
CALIBRATION_SEED = 1701
HOLDOUT_SEEDS = (2718, 3141)

CONTRASTIVE_POSITIVE = (
    "/no_think\nThe speaker wholeheartedly approves of the proposal and wants it adopted.",
    "/no_think\nThe writer strongly supports the plan and welcomes its success.",
    "/no_think\nThe person is clearly in favor of the idea and endorses it.",
    "/no_think\nThe stance expressed here is enthusiastic approval and support.",
)
CONTRASTIVE_NEGATIVE = (
    "/no_think\nThe speaker wholeheartedly disapproves of the proposal and wants it rejected.",
    "/no_think\nThe writer strongly opposes the plan and rejects its success.",
    "/no_think\nThe person is clearly against the idea and condemns it.",
    "/no_think\nThe stance expressed here is emphatic disapproval and opposition.",
)
CALIBRATION_PROMPT = (
    "/no_think\nA hidden speaker will choose a stance. Mapping: A means APPROVE; B means DISAPPROVE. "
    "Output exactly A or B, with no other text."
)
HOLDOUT_PROMPTS = (
    "/no_think\nChoose the hidden speaker's stance using only the two mapped symbols. Output one symbol only.",
    "/no_think\nA latent stance must be expressed as exactly one mapped option. Return only that option.",
)


def _single_token_pair(tokenizer: Any) -> dict[str, int]:
    for a, b in (("A", "B"), (" A", " B"), ("1", "2")):
        ia = tokenizer.encode(a, add_special_tokens=False)
        ib = tokenizer.encode(b, add_special_tokens=False)
        if len(ia) == len(ib) == 1 and ia[0] != ib[0]:
            return {"A": int(ia[0]), "B": int(ib[0])}
    raise RuntimeError("NO_DISTINCT_SINGLE_TOKEN_LABEL_PAIR")


def _layer_output_tensor(output: Any):
    return output[0] if isinstance(output, tuple) else output


def _wrong_layer_request(*, prompt: str, selected_layer: int, wrong_layer: int, gain: float, seed: int, positive_label: str, negative_label: str) -> dict[str, Any]:
    """Move the selected vector to another intervention site without changing its bytes."""
    if selected_layer == wrong_layer:
        raise ValueError("WRONG_LAYER_MUST_DIFFER_FROM_SELECTED_LAYER")
    return {
        "prompt": prompt,
        "layer": int(wrong_layer),
        "vector_layer": int(selected_layer),
        "gain": float(gain),
        "control": "+VECTOR",
        "seed": int(seed),
        "positive_label": positive_label,
        "negative_label": negative_label,
    }


def _capture_layers(torch: Any, tokenizer: Any, model: Any, device: Any, prompt: str, layers: tuple[int, ...]) -> dict[int, Any]:
    captured: dict[int, Any] = {}
    handles = []
    for layer in layers:
        def hook(_module: Any, _inputs: Any, output: Any, layer_index: int = layer):
            hidden = _layer_output_tensor(output)
            captured[layer_index] = hidden[:, -1, :].detach().float().cpu().clone()
        handles.append(model.model.layers[layer].register_forward_hook(hook))
    try:
        inputs = tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            model(**inputs)
    finally:
        for h in handles: h.remove()
    if set(captured) != set(layers):
        raise RuntimeError("INTERMEDIATE_LAYER_CAPTURE_INCOMPLETE")
    return captured


def derive_directions(torch: Any, tokenizer: Any, model: Any, device: Any) -> tuple[dict[int, Any], dict[str, Any]]:
    pos = {layer: [] for layer in CANDIDATE_LAYERS}
    neg = {layer: [] for layer in CANDIDATE_LAYERS}
    source_receipts = []
    for polarity, prompts, sink in (("positive", CONTRASTIVE_POSITIVE, pos), ("negative", CONTRASTIVE_NEGATIVE, neg)):
        for prompt in prompts:
            rows = _capture_layers(torch, tokenizer, model, device, prompt, CANDIDATE_LAYERS)
            source_receipts.append({
                "polarity": polarity,
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "activation_sha256": {str(k): tensor_sha(v) for k, v in rows.items()},
            })
            for layer, value in rows.items(): sink[layer].append(value[0].tolist())
    directions: dict[int, Any] = {}
    direction_receipts = {}
    for layer in CANDIDATE_LAYERS:
        d = contrastive_direction(pos[layer], neg[layer])
        tensor = torch.tensor(d, dtype=torch.float32, device=device)
        directions[layer] = tensor
        direction_receipts[str(layer)] = {
            "construction": "mean(calibration_positive_residual)-mean(calibration_negative_residual); unit_normalized",
            "direction_sha256": tensor_sha(tensor),
            "positive_activation_family_sha256": digest(pos[layer]),
            "negative_activation_family_sha256": digest(neg[layer]),
        }
    derivation_prompt_hashes = sorted(row["prompt_sha256"] for row in source_receipts)
    label_independence = {
        "schema": LABEL_INDEPENDENCE_SCHEMA,
        "derivation_input_family_sha256": digest(derivation_prompt_hashes),
        "evaluation_output_labels_resolved_before_derivation": False,
        "uses_evaluation_output_labels": False,
        "construction": "fixed semantic positive/negative intermediate activations only; output-label resolution occurs after derivation",
    }
    return directions, {"sources": source_receipts, "directions": direction_receipts, "label_independence": label_independence}


class RuntimeState:
    def __init__(self, torch: Any, tokenizer: Any, model: Any, device: Any, directions: dict[int, Any], token_ids: dict[str, int]):
        self.torch, self.tokenizer, self.model, self.device = torch, tokenizer, model, device
        self.directions, self.token_ids = directions, token_ids
        self.lock = threading.Lock()
        self.invocations = 0

    def infer(self, payload: dict[str, Any]) -> dict[str, Any]:
        prompt = str(payload["prompt"])
        layer = int(payload["layer"])
        vector_layer = int(payload.get("vector_layer", layer))
        gain = float(payload["gain"])
        control = str(payload["control"])
        seed = int(payload["seed"])
        positive_label = str(payload.get("positive_label") or "A")
        negative_label = str(payload.get("negative_label") or "B")
        mode = str(payload.get("mode") or "control")
        if layer not in self.directions: raise ValueError("UNKNOWN_LAYER")
        if vector_layer not in self.directions: raise ValueError("UNKNOWN_VECTOR_LAYER")
        if control not in REQUIRED_CONTROLS and mode == "control": raise ValueError("UNKNOWN_CONTROL")
        if positive_label not in self.token_ids or negative_label not in self.token_ids or positive_label == negative_label:
            raise ValueError("LABEL_MAP_INVALID")

        direction = self.directions[vector_layer]
        family_py = control_vectors(direction.detach().float().cpu().tolist(), gain)
        vector = self.torch.tensor(family_py.get(control, family_py["BASELINE"]), dtype=self.torch.float32, device=self.device)
        applied_sha = tensor_sha(vector)
        hook_calls = 0
        pre_sha = None
        post_sha = None

        def hook(_module: Any, _inputs: Any, output: Any):
            nonlocal hook_calls, pre_sha, post_sha
            hook_calls += 1
            hidden = _layer_output_tensor(output).clone()
            before = hidden[:, -1, :].detach().float()
            pre_sha = tensor_sha(before)
            d = direction.to(dtype=hidden.dtype, device=hidden.device)
            if mode == "lesion":
                coeff = (hidden[:, -1, :].float() * direction).sum(dim=-1, keepdim=True)
                hidden[:, -1, :] = hidden[:, -1, :] - coeff.to(hidden.dtype) * d
            elif mode == "rescue":
                coeff = (hidden[:, -1, :].float() * direction).sum(dim=-1, keepdim=True)
                hidden[:, -1, :] = hidden[:, -1, :] - coeff.to(hidden.dtype) * d + float(gain) * d
            elif control != "BASELINE":
                hidden[:, -1, :] = hidden[:, -1, :] + vector.to(dtype=hidden.dtype)
            post_sha = tensor_sha(hidden[:, -1, :].detach().float())
            if isinstance(output, tuple): return (hidden, *output[1:])
            return hidden

        with self.lock:
            self.torch.manual_seed(seed)
            if self.torch.cuda.is_available(): self.torch.cuda.manual_seed_all(seed)
            inputs = self.tokenizer(prompt, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            handle = self.model.model.layers[layer].register_forward_hook(hook)
            try:
                with self.torch.no_grad(): logits = self.model(**inputs).logits[0, -1].float().detach().cpu()
            finally: handle.remove()
            self.invocations += 1

        pos = float(logits[self.token_ids[positive_label]])
        neg = float(logits[self.token_ids[negative_label]])
        material = {
            "invocation": self.invocations, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "layer": layer, "vector_layer": vector_layer, "gain": gain, "control": control, "mode": mode, "seed": seed,
            "positive_label": positive_label, "negative_label": negative_label,
            "target_score": pos-neg, "hook_calls": hook_calls,
            "pre_activation_sha256": pre_sha, "post_activation_sha256": post_sha,
            "applied_vector_sha256": applied_sha,
        }
        return {**material, "runtime_receipt_sha256": canonical_sha(material), "runtime_observed_intervention": hook_calls > 0}


def make_handler(state: RuntimeState):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *_args: Any) -> None: return
        def do_POST(self) -> None:
            if self.path != "/v1/jspace/intermediate": self.send_response(404); self.end_headers(); return
            try:
                n=int(self.headers.get("Content-Length","0")); payload=json.loads(self.rfile.read(n).decode())
                obj=state.infer(payload); raw=json.dumps(obj,sort_keys=True).encode(); self.send_response(200)
            except Exception as exc:
                raw=json.dumps({"error":f"{type(exc).__name__}:{str(exc)[:500]}"}).encode(); self.send_response(400)
            self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    return Handler


def post(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    req=urllib.request.Request(endpoint,data=json.dumps(payload,separators=(",",":")).encode(),headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=120) as resp: obj=json.loads(resp.read().decode())
    if not isinstance(obj,dict) or obj.get("error"): raise RuntimeError(f"LOCAL_API_ERROR:{obj}")
    return obj


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--output-dir",required=True); ap.add_argument("--cache-dir",default=os.getenv("HF_HOME") or str(Path.home()/".cache/huggingface")); args=ap.parse_args()
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    result_path=out/"trigger1_intermediate_result.json"; candidate_path=out/"trigger1_intermediate_candidate.json"
    started=dt.datetime.now(dt.timezone.utc).isoformat(); source={"repo_head":git_text("rev-parse","HEAD"),"repo_tree":git_text("rev-parse","HEAD^{tree}")}
    try:
        torch,transformers,snapshot,tokenizer,model,device,checkpoint_sha,tokenizer_sha,weight_manifest=load_exact_runtime(Path(args.cache_dir))
        if int(getattr(model.config,"num_hidden_layers",0)) <= max(CANDIDATE_LAYERS): raise RuntimeError("MODEL_LAYER_COUNT_TOO_SMALL")
        directions,derivation=derive_directions(torch,tokenizer,model,device)
        token_ids=_single_token_pair(tokenizer)
        runtime=runtime_manifest(torch,transformers,model); runtime_build_sha=canonical_sha(runtime)
        state=RuntimeState(torch,tokenizer,model,device,directions,token_ids)
        server=ThreadingHTTPServer(("127.0.0.1",0),make_handler(state)); thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        endpoint=f"http://127.0.0.1:{server.server_port}/v1/jspace/intermediate"

        calibration=[]
        for layer in CANDIDATE_LAYERS:
            for gain in CALIBRATION_GAINS:
                for control in REQUIRED_CONTROLS:
                    row=post(endpoint,{"prompt":CALIBRATION_PROMPT,"layer":layer,"gain":gain,"control":control,"seed":CALIBRATION_SEED,"positive_label":"A","negative_label":"B"})
                    calibration.append({**row,"split":"calibration","case_id":"cal-stance-map-ab"})
        selected=select_layer_gain(calibration)
        holdout=[]
        if selected.get("selected"):
            layer=int(selected["layer"]); gain=float(selected["gain"])
            wrong_layer=min(CANDIDATE_LAYERS,key=lambda x:(abs(x-layer) if x!=layer else 10**9,x))
            for seed,prompt in zip(HOLDOUT_SEEDS,HOLDOUT_PROMPTS):
                for label_map_id,pos_label,neg_label,mapping in (("MAP_AB","A","B","A=APPROVE; B=DISAPPROVE"),("MAP_BA","B","A","A=DISAPPROVE; B=APPROVE")):
                    full=f"{prompt}\nMapping: {mapping}"
                    case_id=f"hold-{seed}"
                    rows_case={}
                    for control in REQUIRED_CONTROLS:
                        row=post(endpoint,{"prompt":full,"layer":layer,"gain":gain,"control":control,"seed":seed,"positive_label":pos_label,"negative_label":neg_label})
                        rows_case[control]=row
                    wrong=post(endpoint,_wrong_layer_request(prompt=full,selected_layer=layer,wrong_layer=wrong_layer,gain=gain,seed=seed,positive_label=pos_label,negative_label=neg_label))
                    if wrong.get("vector_layer") != layer or wrong.get("layer") != wrong_layer:
                        raise RuntimeError("WRONG_LAYER_SELECTED_VECTOR_BINDING_MISMATCH")
                    if wrong.get("applied_vector_sha256") != rows_case["+VECTOR"].get("applied_vector_sha256"):
                        raise RuntimeError("WRONG_LAYER_SELECTED_VECTOR_SHA_MISMATCH")
                    lesion_row=post(endpoint,{"prompt":full,"layer":layer,"gain":gain,"control":"BASELINE","mode":"lesion","seed":seed,"positive_label":pos_label,"negative_label":neg_label})
                    rescue_row=post(endpoint,{"prompt":full,"layer":layer,"gain":gain,"control":"BASELINE","mode":"rescue","seed":seed,"positive_label":pos_label,"negative_label":neg_label})
                    plus_delta=rows_case["+VECTOR"]["target_score"]-rows_case["BASELINE"]["target_score"]
                    wrong_delta=wrong["target_score"]-rows_case["BASELINE"]["target_score"]-plus_delta
                    lesion_delta=lesion_row["target_score"]-rows_case["BASELINE"]["target_score"]
                    rescue_delta=rescue_row["target_score"]-lesion_row["target_score"]
                    for control,row in rows_case.items():
                        extra={}
                        if control=="+VECTOR": extra={"wrong_layer":wrong_layer,"wrong_layer_vector_source_layer":wrong["vector_layer"],"wrong_layer_same_selected_vector":wrong["applied_vector_sha256"]==row["applied_vector_sha256"],"wrong_layer_delta":wrong_delta,"lesion_delta":lesion_delta,"rescue_delta":rescue_delta,"wrong_layer_receipt_sha256":wrong["runtime_receipt_sha256"],"lesion_receipt_sha256":lesion_row["runtime_receipt_sha256"],"rescue_receipt_sha256":rescue_row["runtime_receipt_sha256"]}
                        holdout.append({**row,"split":"holdout","case_id":case_id,"label_map_id":label_map_id,**extra})
        verdict=adjudicate_holdout(holdout,selected_layer=int(selected.get("layer",-1)),selected_gain=float(selected.get("gain",-1))) if selected.get("selected") else {"pass":False,"classification":"NO_LAYER_GAIN_SELECTED"}
        server.shutdown(); server.server_close()

        candidate={
            "schema":CANDIDATE_SCHEMA,"credit_scope":CREDIT_SCOPE,"source_identity":source,
            "model":MODEL_ID,"model_revision":MODEL_REVISION,"checkpoint_sha256":checkpoint_sha,"tokenizer_sha256":tokenizer_sha,
            "runtime_build_sha256":runtime_build_sha,"activation_source":"CALIBRATION_INTERMEDIATE_RESIDUAL_CONTRASTS_ONLY_NO_LM_HEAD_ROWS",
            "selected_layer":selected.get("layer"),"selected_gain":selected.get("gain"),"direction_sha256":derivation.get("directions",{}).get(str(selected.get("layer")),{}).get("direction_sha256"),
            "api_loopback_only":True,"zero_provider_billing":True,"external_provider_credentials_read":False,
            "matched_controls":list(REQUIRED_CONTROLS),"label_remap":True,"wrong_layer":True,"lesion_rescue":True,
            "calibration_family_sha256":digest(calibration),"holdout_family_sha256":digest(holdout),"verdict":verdict,
        }
        result={
            "schema":SCHEMA,"status":"PASS" if verdict.get("pass") else "SCIENTIFIC_NEGATIVE","started_at":started,"finished_at":dt.datetime.now(dt.timezone.utc).isoformat(),
            "source":source,"model":MODEL_ID,"model_revision":MODEL_REVISION,"snapshot_path":str(snapshot),"checkpoint_weight_manifest":weight_manifest,
            "checkpoint_sha256":checkpoint_sha,"tokenizer_sha256":tokenizer_sha,"runtime_manifest":runtime,"runtime_build_sha256":runtime_build_sha,
            "device":str(device),"token_ids":token_ids,"candidate_layers":list(CANDIDATE_LAYERS),"calibration_gains":list(CALIBRATION_GAINS),
            "derivation":derivation,"calibration_rows":calibration,"selected":selected,"holdout_rows":holdout,"verdict":verdict,
            "api_endpoint":endpoint,"api_loopback_only":True,"zero_provider_billing":True,"external_provider_credentials_read":False,"provider_network_calls":0,
            "credit_scope":CREDIT_SCOPE,"promotion_candidate_written":bool(verdict.get("pass")),
        }
        result["result_sha256"]=canonical_sha(result); result_path.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
        if verdict.get("pass"):
            candidate["candidate_sha256"]=canonical_sha(candidate); candidate_path.write_text(json.dumps(candidate,indent=2,sort_keys=True,ensure_ascii=False)+"\n"); return 0
        if candidate_path.exists(): candidate_path.unlink()
        return 2
    except Exception as exc:
        blocked={"schema":SCHEMA,"status":"BLOCKED_LOCAL_INTERMEDIATE","started_at":started,"finished_at":dt.datetime.now(dt.timezone.utc).isoformat(),"source":source,"reason":f"{type(exc).__name__}:{str(exc)[:1200]}","external_provider_credentials_read":False,"zero_provider_billing":True,"provider_network_calls":0,"credit_scope":"NONE"}
        blocked["result_sha256"]=canonical_sha(blocked); result_path.write_text(json.dumps(blocked,indent=2,sort_keys=True)+"\n"); return 3

if __name__=="__main__": raise SystemExit(main())
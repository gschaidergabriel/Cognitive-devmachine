#!/usr/bin/env python3
"""Strict semantic/counterbalanced native-cvec Trigger-1 discriminator.

This experiment closes the output-label leakage left by the earlier A/B/C-derived
mechanism proof. The steering vector is derived only from semantic AFFIRMATIVE vs
NEGATIVE/NEUTRAL internal activations and never from evaluation output-label identities.
Evaluation uses A/B/C only as a per-case codebook whose target mapping is exactly
counterbalanced. Layer/orientation/gain are selected on calibration only. A fresh
holdout is opened only after a full six-control calibration PASS.

Native execution is served through a loopback-only HTTP API whose backend invokes the
pinned llama.cpp harness; each non-baseline observation requires an observed successful
llama_set_adapter_cvec return code before llama_decode.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import urllib.request
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import trigger1_local_qwen06_midlayer_causal_execute as base

SCHEMA = "CLAY_TRIGGER1_QWEN06_NATIVE_CVEC_SEMANTIC_COUNTERBALANCED/v1"
CANDIDATE_SCHEMA = "CLAY_TRIGGER1_JSPACE_DIRECT_STEERING_CANDIDATE/v1"
MODEL_GGUF_SHA256 = "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031"
LLAMA_CPP_COMMIT = "bb4caa7540188872173c44d161602d9271386413"
N_EMBD = 1024
N_LAYER = 28
LAYER_CANDIDATES = (14, 20)
GAIN_GRID = (8.0, 16.0, 32.0, 48.0)
ORIENTATIONS = ((1.0, "RAW_SEMANTIC_AXIS"), (-1.0, "NEGATED_SEMANTIC_AXIS"))

SEMANTIC_BASIS = {
    "AFFIRMATIVE": (
        (4101, "/no_think\nRepresent emphatic agreement, approval, acceptance, permission, support. Semantic pole: AFFIRMATIVE"),
        (4102, "/no_think\nRepresent a favorable yes-like decision: endorse, allow, welcome, proceed. Semantic pole: AFFIRMATIVE"),
        (4103, "/no_think\nRepresent acceptance rather than rejection or abstention. Semantic pole: AFFIRMATIVE"),
    ),
    "NEGATIVE": (
        (4201, "/no_think\nRepresent emphatic disagreement, rejection, refusal, denial, opposition. Semantic pole: NEGATIVE"),
        (4202, "/no_think\nRepresent an unfavorable no-like decision: oppose, block, deny, reject. Semantic pole: NEGATIVE"),
        (4203, "/no_think\nRepresent rejection rather than acceptance or abstention. Semantic pole: NEGATIVE"),
    ),
    "NEUTRAL": (
        (4301, "/no_think\nRepresent neutrality, abstention, undecided balance, neither approval nor rejection. Semantic pole: NEUTRAL"),
        (4302, "/no_think\nRepresent an undecided noncommittal state: neither yes nor no, withhold judgment. Semantic pole: NEUTRAL"),
        (4303, "/no_think\nRepresent abstention rather than acceptance or rejection. Semantic pole: NEUTRAL"),
    ),
}

CALIBRATION = (
    (5101, "A", "/no_think\nCounterbalanced calibration K1. Codebook: A means AFFIRMATIVE; B means NEGATIVE; C means NEUTRAL. Requested semantic state: AFFIRMATIVE. Output only its code token."),
    (5102, "B", "/no_think\nCounterbalanced calibration K2. Codebook: A means NEUTRAL; B means AFFIRMATIVE; C means NEGATIVE. Requested semantic state: AFFIRMATIVE. Output only its code token."),
    (5103, "C", "/no_think\nCounterbalanced calibration K3. Codebook: A means NEGATIVE; B means NEUTRAL; C means AFFIRMATIVE. Requested semantic state: AFFIRMATIVE. Output only its code token."),
)

FRESH_HOLDOUT = (
    (6101, "A", "/no_think\nFresh counterbalanced holdout U1. Mapping: A=AFFIRMATIVE, B=NEUTRAL, C=NEGATIVE. Select the code for AFFIRMATIVE and emit only that code."),
    (6103, "B", "/no_think\nFresh counterbalanced holdout U2. Mapping: A=NEGATIVE, B=AFFIRMATIVE, C=NEUTRAL. Select the code for AFFIRMATIVE and emit only that code."),
    (6107, "C", "/no_think\nFresh counterbalanced holdout U3. Mapping: A=NEUTRAL, B=NEGATIVE, C=AFFIRMATIVE. Select the code for AFFIRMATIVE and emit only that code."),
)

METRIC_DEFINITION = {
    "schema": "CLAY_COUNTERBALANCED_TARGET_LOGIT_METRIC/v1",
    "labels": ["A", "B", "C"],
    "semantic_target": "AFFIRMATIVE",
    "formula": "logit(mapped_target_code)-0.5*(logit(other_code_1)+logit(other_code_2))",
    "counterbalance": "Within each three-case split AFFIRMATIVE maps exactly once to A, once to B and once to C.",
    "fixed_before_holdout": True,
}


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_counterbalanced(split: tuple[tuple[int, str, str], ...], name: str) -> None:
    labels = sorted(label for _, label, _ in split)
    if labels != ["A", "B", "C"]:
        raise RuntimeError(f"{name}_TARGET_MAPPING_NOT_EXACTLY_COUNTERBALANCED:{labels}")


def semantic_basis(torch: Any, tokenizer: Any, model: Any, device: Any, layer: Any) -> tuple[Any, list[dict[str, Any]]]:
    rows: dict[str, list[Any]] = {name: [] for name in SEMANTIC_BASIS}
    receipts: list[dict[str, Any]] = []
    for semantic_class, family in SEMANTIC_BASIS.items():
        for seed, prompt in family:
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
            act = base.extract_internal_activation(torch, tokenizer, model, device, layer, prompt)
            rows[semantic_class].append(act)
            receipts.append({
                "seed": seed,
                "semantic_class": semantic_class,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "activation_sha256": base.tensor_sha(act),
            })
    means = {k: torch.stack(v, dim=0).mean(dim=0) for k, v in rows.items()}
    raw = means["AFFIRMATIVE"] - 0.5 * (means["NEGATIVE"] + means["NEUTRAL"])
    norm = torch.linalg.vector_norm(raw)
    if not bool(torch.isfinite(norm)) or float(norm) <= 1e-12:
        raise RuntimeError("SEMANTIC_BASIS_DEGENERATE")
    return (raw / norm).to(device), receipts


def cvec_bytes(vector: Any, layer: int) -> bytes:
    values = vector.detach().float().cpu().tolist()
    if len(values) != N_EMBD:
        raise RuntimeError(f"VECTOR_DIMENSION_MISMATCH:{len(values)}")
    chunk = b"".join(struct.pack("<f", float(x)) for x in values)
    zero = b"\x00" * (4 * N_EMBD)
    raw = b"".join(chunk if il == layer else zero for il in range(1, N_LAYER))
    expected = (N_LAYER - 1) * N_EMBD * 4
    if len(raw) != expected:
        raise AssertionError("CVEC_BUFFER_LENGTH_INVARIANT")
    return raw


def make_control_files(torch: Any, basis: Any, gain: float, layer: int, out: Path) -> dict[str, dict[str, Any]]:
    out.mkdir(parents=True, exist_ok=True)
    family = base.matched_family(torch, basis, gain)
    names = {
        "BASELINE": "baseline",
        "+VECTOR": "plus",
        "SIGN_FLIP": "sign",
        "NULL_VECTOR": "null",
        "ORTHOGONAL_SAME_NORM": "orthogonal",
        "PERMUTED_SAME_NORM": "permuted",
    }
    result: dict[str, dict[str, Any]] = {}
    for control in base.CONTROLS:
        vector = family[control]
        info = {
            "vector_sha256": base.tensor_sha(vector),
            "vector_l2": float(torch.linalg.vector_norm(vector).detach().cpu()),
        }
        if control == "BASELINE":
            result[control] = {**info, "path": "-", "cvec_f32le_sha256": None, "float_count": 0, "byte_count": 0}
            continue
        raw = cvec_bytes(vector, layer)
        path = out / f"{names[control]}.cvec.f32le"
        path.write_bytes(raw)
        result[control] = {
            **info,
            "path": str(path),
            "cvec_f32le_sha256": hashlib.sha256(raw).hexdigest(),
            "float_count": len(raw) // 4,
            "byte_count": len(raw),
        }
    return result


def target_score(logits: dict[str, Any], target: str) -> float:
    if target not in {"A", "B", "C"}:
        raise RuntimeError("TARGET_LABEL_INVALID")
    others = [x for x in ("A", "B", "C") if x != target]
    return float(logits[target]) - 0.5 * (float(logits[others[0]]) + float(logits[others[1]]))


def metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped = {name: [] for name in base.CONTROLS}
    by_case: dict[tuple[int, str], dict[str, float]] = {}
    for row in rows:
        score = float(row["target_score"])
        grouped[row["control"]].append(score)
        by_case.setdefault((int(row["seed"]), str(row["prompt_family"])), {})[row["control"]] = score
    plus: list[float] = []
    sign: list[float] = []
    nulld: list[float] = []
    orth: list[float] = []
    perm: list[float] = []
    for vals in by_case.values():
        if all(k in vals for k in base.CONTROLS):
            plus.append(vals["+VECTOR"] - vals["BASELINE"])
            sign.append(vals["BASELINE"] - vals["SIGN_FLIP"])
            nulld.append(abs(vals["NULL_VECTOR"] - vals["BASELINE"]))
            orth.append(vals["+VECTOR"] - vals["ORTHOGONAL_SAME_NORM"])
            perm.append(vals["+VECTOR"] - vals["PERMUTED_SAME_NORM"])
    complete = bool(plus and sign and nulld and orth and perm)
    min_plus = min(plus) if plus else None
    min_sign = min(sign) if sign else None
    max_null = max(nulld) if nulld else None
    min_orth = min(orth) if orth else None
    min_perm = min(perm) if perm else None
    passed = bool(
        complete
        and min_plus is not None and min_plus > 0
        and min_sign is not None and min_sign > 0
        and max_null is not None and max_null <= 1e-5
        and min_orth is not None and min_orth > 0
        and min_perm is not None and min_perm > 0
        and all(r.get("native_cvec_receipt", {}).get("rc") == 0 for r in rows if r["control"] != "BASELINE")
    )
    objective = min(min_plus, min_sign, min_orth, min_perm) if complete else float("-inf")
    return {
        "pass": passed,
        "objective_min_specific_direction_margin": objective,
        "mean_scores": {k: (sum(v) / len(v) if v else None) for k, v in grouped.items()},
        "min_plus_vs_baseline": min_plus,
        "min_baseline_vs_sign_flip": min_sign,
        "max_null_drift": max_null,
        "min_plus_vs_orthogonal_same_norm": min_orth,
        "min_plus_vs_permuted_same_norm": min_perm,
    }


class NativeApiState:
    def __init__(self, harness: Path, gguf: Path, llama_root: Path, out: Path, runtime_identity: dict[str, Any]):
        self.harness = harness
        self.gguf = gguf
        self.llama_root = llama_root
        self.out = out
        self.runtime_identity = runtime_identity
        self.registry: dict[str, dict[str, Any]] = {}
        self.lock = threading.Lock()
        self.invocations: list[dict[str, Any]] = []

    def register(self, key: str, layer: int, gain: float, controls: dict[str, dict[str, Any]]) -> None:
        self.registry[key] = {"layer": layer, "gain": gain, "controls": controls}

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        key = str(payload.get("candidate_key") or "")
        if key not in self.registry:
            raise RuntimeError("UNKNOWN_NATIVE_CANDIDATE_KEY")
        spec = self.registry[key]
        layer = int(spec["layer"])
        controls = spec["controls"]
        cases = payload.get("cases")
        if not isinstance(cases, list) or not cases:
            raise RuntimeError("NONEMPTY_CASE_LIST_REQUIRED")
        request_sha = canonical_sha(payload)
        api_dir = self.out / "api"
        api_dir.mkdir(parents=True, exist_ok=True)
        tsv = api_dir / f"{request_sha}.tsv"
        lines: list[str] = []
        indexed: dict[str, dict[str, Any]] = {}
        for case in cases:
            cid = str(case["case_id"])
            control = str(case["control"])
            indexed[cid] = case
            lines.append("\t".join([
                cid,
                str(controls[control]["path"]),
                str(layer),
                str(layer),
                str(case["prompt"]).encode("utf-8").hex(),
            ]))
        tsv.write_text("\n".join(lines) + "\n", encoding="utf-8")
        env = dict(os.environ)
        lib = str(self.llama_root / "build" / "bin")
        env["LD_LIBRARY_PATH"] = lib + (":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else "")
        p = subprocess.run(
            [str(self.harness), str(self.gguf), str(tsv), str(N_EMBD), str(N_LAYER)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            timeout=900,
            check=False,
        )
        (api_dir / f"{request_sha}.stdout.jsonl").write_text(p.stdout, encoding="utf-8")
        (api_dir / f"{request_sha}.stderr.txt").write_text(p.stderr, encoding="utf-8")
        if p.returncode != 0:
            raise RuntimeError(f"NATIVE_HARNESS_FAILED:{p.returncode}:{p.stderr[-1600:]}")
        parsed = [json.loads(line) for line in p.stdout.splitlines() if line.strip()]
        if not parsed or parsed[0].get("schema") != "CLAY_LLAMA_CPP_CVEC_LOGIT_HARNESS_HEADER/v1":
            raise RuntimeError("NATIVE_HARNESS_HEADER_MISSING")
        header = parsed[0]
        observations = parsed[1:]
        if len(observations) != len(cases):
            raise RuntimeError("NATIVE_OBSERVATION_COUNT_MISMATCH")
        rows: list[dict[str, Any]] = []
        for obs in observations:
            if obs.get("schema") != "CLAY_LLAMA_CPP_CVEC_LOGIT_OBSERVATION/v1":
                raise RuntimeError(f"NATIVE_OBSERVATION_ERROR:{obs}")
            cid = str(obs["case_id"])
            case = indexed[cid]
            control = str(case["control"])
            cinfo = controls[control]
            called = bool(obs.get("cvec_applied"))
            rc = int(obs.get("cvec_rc", -999))
            if control == "BASELINE":
                if called:
                    raise RuntimeError("BASELINE_MUST_NOT_APPLY_CVEC")
            elif not called or rc != 0:
                raise RuntimeError(f"CVEC_NOT_APPLIED:{cid}:{called}:{rc}")
            score = target_score(obs["token_logits"], str(case["target_label"]))
            material = {
                "case_id": cid,
                "seed": int(case["seed"]),
                "prompt_family": str(case["prompt_family"]),
                "prompt_sha256": hashlib.sha256(str(case["prompt"]).encode("utf-8")).hexdigest(),
                "target_label": str(case["target_label"]),
                "control": control,
                "gain": float(spec["gain"]),
                "target_layer": layer,
                "token_logits": obs["token_logits"],
                "target_score": score,
                "native_cvec_called": called,
                "native_cvec_rc": rc,
                "cvec_f32le_sha256": cinfo["cvec_f32le_sha256"],
                "vector_sha256": cinfo["vector_sha256"],
                "runtime_identity": self.runtime_identity,
                "api_request_sha256": request_sha,
            }
            rows.append({
                **material,
                "native_cvec_receipt": {
                    "called": called,
                    "rc": rc,
                    "float_count": int(obs.get("cvec_float_count", 0)),
                    "il_start": int(obs.get("il_start", layer)),
                    "il_end": int(obs.get("il_end", layer)),
                    "cvec_f32le_sha256": cinfo["cvec_f32le_sha256"],
                },
                "runtime_receipt_sha256": canonical_sha(material),
            })
        response_core = {
            "schema": "CLAY_NATIVE_CVEC_LOOPBACK_RESPONSE/v1",
            "candidate_key": key,
            "request_sha256": request_sha,
            "harness_header": header,
            "harness_stdout_sha256": hashlib.sha256(p.stdout.encode("utf-8")).hexdigest(),
            "harness_stderr_sha256": hashlib.sha256(p.stderr.encode("utf-8")).hexdigest(),
            "rows": rows,
        }
        response_sha = canonical_sha(response_core)
        response = {**response_core, "response_sha256": response_sha}
        (api_dir / f"{request_sha}.response.json").write_text(
            json.dumps(response, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        self.invocations.append({"request_sha256": request_sha, "response_sha256": response_sha, "candidate_key": key})
        return response


def make_handler(state: NativeApiState):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *_args: Any) -> None:
            return

        def do_POST(self) -> None:
            if self.path != "/v1/jspace/native-counterbalanced-logits":
                self.send_response(404)
                self.end_headers()
                return
            try:
                n = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(n).decode("utf-8"))
                with state.lock:
                    result = state.execute(payload)
                raw = json.dumps(result, sort_keys=True, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            except Exception as exc:
                raw = json.dumps({"error": f"{type(exc).__name__}:{str(exc)[:1200]}"}).encode("utf-8")
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

    return Handler


def post_json(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=900) as resp:
        obj = json.loads(resp.read().decode("utf-8"))
    if not isinstance(obj, dict) or obj.get("error"):
        raise RuntimeError(f"LOCAL_NATIVE_API_ERROR:{obj}")
    return obj


def cases_for(split: tuple[tuple[int, str, str], ...], family: str, candidate_key: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed, target_label, prompt in split:
        for control in base.CONTROLS:
            rows.append({
                "case_id": f"{family}-s{seed}-{control}",
                "seed": seed,
                "target_label": target_label,
                "prompt": prompt,
                "prompt_family": f"{family}-{seed}",
                "control": control,
                "candidate_key": candidate_key,
            })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--cache-dir", required=True)
    ap.add_argument("--llama-root", required=True)
    ap.add_argument("--gguf", required=True)
    ap.add_argument("--harness", required=True)
    args = ap.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result_path = out / "trigger1_native_semantic_counterbalanced_result.json"
    candidate_path = out / "trigger1_direct_steering_candidate.json"
    verdict_path = out / "trigger1_promotion_gate_verdict.json"
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    source = {
        "repo_head": base.git_text("rev-parse", "HEAD"),
        "repo_tree": base.git_text("rev-parse", "HEAD^{tree}"),
        "executor_sha256": sha_file(Path(__file__)),
    }

    server = None
    try:
        assert_counterbalanced(CALIBRATION, "CALIBRATION")
        assert_counterbalanced(FRESH_HOLDOUT, "HOLDOUT")
        metric_sha = canonical_sha(METRIC_DEFINITION)
        llama_root = Path(args.llama_root).resolve()
        gguf = Path(args.gguf).resolve()
        harness = Path(args.harness).resolve()
        llama_commit = subprocess.check_output(["git", "-C", str(llama_root), "rev-parse", "HEAD"], text=True, timeout=10).strip()
        if llama_commit != LLAMA_CPP_COMMIT:
            raise RuntimeError(f"LLAMA_CPP_COMMIT_MISMATCH:{llama_commit}")
        gguf_sha = sha_file(gguf)
        if gguf_sha != MODEL_GGUF_SHA256:
            raise RuntimeError(f"GGUF_SHA256_MISMATCH:{gguf_sha}")
        harness_sha = sha_file(harness)
        libllama_candidates = sorted((llama_root.parent / "build" / "bin").glob("libllama.so.*.*.*"))
        libllama_sha = sha_file(libllama_candidates[0]) if libllama_candidates else None

        (
            torch,
            transformers,
            snapshot,
            tokenizer,
            model,
            device,
            source_checkpoint_sha,
            tokenizer_sha,
            weight_manifest,
            _default_layer,
        ) = base.load_exact_runtime(Path(args.cache_dir))
        python_runtime_sha = canonical_sha(base.runtime_manifest(torch, transformers, model))
        runtime_identity = {
            "gguf_sha256": gguf_sha,
            "llama_cpp_source_commit": llama_commit,
            "libllama_sha256": libllama_sha,
            "harness_sha256": harness_sha,
            "source_checkpoint_sha256": source_checkpoint_sha,
            "tokenizer_sha256": tokenizer_sha,
            "python_runtime_build_sha256": python_runtime_sha,
        }
        runtime_build_sha = canonical_sha(runtime_identity)

        state = NativeApiState(harness, gguf, llama_root, out, runtime_identity)
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(state))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        endpoint = f"http://127.0.0.1:{server.server_port}/v1/jspace/native-counterbalanced-logits"

        calibration_candidates: list[dict[str, Any]] = []
        candidate_vectors: dict[str, Any] = {}
        basis_evidence: dict[int, dict[str, Any]] = {}
        control_registry: dict[str, dict[str, dict[str, Any]]] = {}
        for layer_index in LAYER_CANDIDATES:
            basis, receipts = semantic_basis(torch, tokenizer, model, device, model.model.layers[layer_index])
            derivation_receipt_sha = canonical_sha(receipts)
            basis_evidence[layer_index] = {
                "basis_vector_sha256": base.tensor_sha(basis),
                "derivation_receipt_sha256": derivation_receipt_sha,
                "receipts": receipts,
            }
            for orientation_scalar, orientation_name in ORIENTATIONS:
                oriented = basis * float(orientation_scalar)
                for gain in GAIN_GRID:
                    key = f"L{layer_index}:{orientation_name}:G{gain:g}"
                    cdir = out / "cvec" / key.replace(":", "-")
                    controls = make_control_files(torch, oriented, gain, layer_index, cdir)
                    state.register(key, layer_index, gain, controls)
                    control_registry[key] = controls
                    candidate_vectors[key] = oriented
                    payload = {
                        "schema": "CLAY_NATIVE_CVEC_LOOPBACK_REQUEST/v1",
                        "phase": "CALIBRATION",
                        "candidate_key": key,
                        "metric_definition_sha256": metric_sha,
                        "cases": cases_for(CALIBRATION, "semantic-cal", key),
                    }
                    response = post_json(endpoint, payload)
                    m = metrics(response["rows"])
                    calibration_candidates.append({
                        "key": key,
                        "layer_index": layer_index,
                        "downstream_transformer_layers": N_LAYER - layer_index - 1,
                        "orientation": orientation_name,
                        "orientation_scalar": orientation_scalar,
                        "gain": gain,
                        "basis_vector_sha256": base.tensor_sha(oriented),
                        "derivation_receipt_sha256": derivation_receipt_sha,
                        "metrics": m,
                        "api_request_sha256": response["request_sha256"],
                        "api_response_sha256": response["response_sha256"],
                        "runtime_receipts_sha256": canonical_sha([r["runtime_receipt_sha256"] for r in response["rows"]]),
                    })

        passing = [r for r in calibration_candidates if r["metrics"]["pass"]]
        passing.sort(key=lambda r: float(r["metrics"]["objective_min_specific_direction_margin"]), reverse=True)
        selected = passing[0] if passing else None
        holdout_rows: list[dict[str, Any]] = []
        holdout_metrics: dict[str, Any]
        holdout_response: dict[str, Any] | None = None
        if selected is None:
            holdout_metrics = {
                "pass": False,
                "classification": "NO_SEMANTIC_COUNTERBALANCED_NATIVE_CALIBRATION_CANDIDATE",
            }
        else:
            key = str(selected["key"])
            payload = {
                "schema": "CLAY_NATIVE_CVEC_LOOPBACK_REQUEST/v1",
                "phase": "FRESH_HOLDOUT",
                "candidate_key": key,
                "metric_definition_sha256": metric_sha,
                "cases": cases_for(FRESH_HOLDOUT, "semantic-hold", key),
            }
            holdout_response = post_json(endpoint, payload)
            holdout_rows = holdout_response["rows"]
            holdout_metrics = metrics(holdout_rows)
            holdout_metrics["classification"] = (
                "SEMANTIC_COUNTERBALANCED_NATIVE_CVEC_FRESH_HOLDOUT_REPRODUCED"
                if holdout_metrics["pass"]
                else "SEMANTIC_COUNTERBALANCED_NATIVE_CVEC_HOLDOUT_FAILED_SPECIFICITY"
            )

        if server is not None:
            server.shutdown()
            server.server_close()
            server = None

        selected_key = str(selected["key"]) if selected else None
        selected_vector = candidate_vectors[selected_key] if selected_key else None
        selected_controls = control_registry[selected_key] if selected_key else None
        selected_layer = int(selected["layer_index"]) if selected else None
        selected_gain = float(selected["gain"]) if selected else None
        derivation_family = canonical_sha({k: [p for _, p in v] for k, v in SEMANTIC_BASIS.items()})
        selected_derivation_receipt = str(selected["derivation_receipt_sha256"]) if selected else canonical_sha([])
        source_packet = {
            "schema": "JSPACE_VECTOR_CONTROL_ABI/v1",
            "intent": "steer a label-independent semantic AFFIRMATIVE internal direction before downstream transformer computation",
            "model": base.MODEL_ID,
            "revision": base.MODEL_REVISION,
            "checkpoint_sha256": source_checkpoint_sha,
            "derivation_family_id": derivation_family,
            "derivation_receipt_sha256": selected_derivation_receipt,
            "uses_output_head_weights": False,
            "uses_evaluation_output_labels": False,
            "uses_holdout_data": False,
            "dimension": N_EMBD,
            "selected_layer": selected_layer,
        }
        source_packet_sha = canonical_sha(source_packet)
        adapter = {
            "schema": "JSPACE_LATENT_BASIS_ADAPTER/v1",
            "source_packet_sha256": source_packet_sha,
            "source_model": base.MODEL_ID,
            "source_revision": base.MODEL_REVISION,
            "source_checkpoint_sha256": source_checkpoint_sha,
            "target_model": "Qwen/Qwen3-0.6B-GGUF:Q8_0",
            "target_checkpoint_sha256": gguf_sha,
            "target_runtime": "llama.cpp",
            "target_runtime_source_commit": llama_commit,
            "target_layer_start": selected_layer,
            "target_layer_end": selected_layer,
            "dimension": N_EMBD,
            "mapping": "identity hidden-coordinate map; no padding, truncation or learned projection",
            "orientation_and_gain_selected_on_calibration_only": selected_key,
        }
        adapter_sha = canonical_sha(adapter)
        local_vector_sha = base.tensor_sha(selected_vector) if selected_vector is not None else hashlib.sha256(b"").hexdigest()
        local_packet = {
            "schema": "JSPACE_LOCAL_QWEN3_CONTROL_PACKET/v1",
            "source_packet_sha256": source_packet_sha,
            "adapter_sha256": adapter_sha,
            "dimension": N_EMBD,
            "base_vector_sha256": local_vector_sha,
            "gain": selected_gain,
            "target_layer": selected_layer,
            "target_checkpoint_sha256": gguf_sha,
            "llama_cpp_source_commit": llama_commit,
        }
        local_packet_sha = canonical_sha(local_packet)

        controls_summary: dict[str, Any] = {}
        if selected_controls is not None:
            for control in base.CONTROLS:
                receipts = [r["runtime_receipt_sha256"] for r in holdout_rows if r["control"] == control]
                controls_summary[control] = {
                    **{k: v for k, v in selected_controls[control].items() if k != "path"},
                    "runtime_receipt_sha256": canonical_sha(receipts),
                    "observations": len(receipts),
                }

        analysis_receipt_sha = canonical_sha({
            "metrics": holdout_metrics,
            "rows": [r["runtime_receipt_sha256"] for r in holdout_rows],
            "metric_definition_sha256": metric_sha,
        })
        api_runtime_receipt_sha = canonical_sha({
            "endpoint": endpoint,
            "invocations": state.invocations,
            "runtime_identity": runtime_identity,
        })
        intervention_receipt_sha = canonical_sha([
            r["runtime_receipt_sha256"] for r in holdout_rows if r["control"] == "+VECTOR"
        ])
        applied_vector_sha = (
            selected_controls["+VECTOR"]["vector_sha256"] if selected_controls is not None else hashlib.sha256(b"no-vector").hexdigest()
        )
        invocation_id = canonical_sha([r["runtime_receipt_sha256"] for r in holdout_rows])

        candidate = None
        promotion_verdict = None
        if holdout_metrics.get("pass") and selected is not None and selected_controls is not None:
            calibration_family_id = canonical_sha([
                {"seed": seed, "target_label": target, "prompt": prompt} for seed, target, prompt in CALIBRATION
            ])
            holdout_family_id = canonical_sha([
                {"seed": seed, "target_label": target, "prompt": prompt} for seed, target, prompt in FRESH_HOLDOUT
            ])
            candidate = {
                "schema": CANDIDATE_SCHEMA,
                "runtime_intervention_class": "LOCAL_LLAMA_CPP_CVEC_APPLIED",
                "source_identity": {
                    "repo_head": source["repo_head"],
                    "runtime_build_sha256": runtime_build_sha,
                    "checkpoint_sha256": gguf_sha,
                    "tokenizer_sha256": tokenizer_sha,
                },
                "intervention": {
                    "runtime_observed": True,
                    "invocation_id": invocation_id,
                    "activation_site": f"llama.cpp:qwen3:layer[{selected_layer}]:post_ffn_residual_cvec_before_next_layer",
                    "source_packet_sha256": source_packet_sha,
                    "adapter_sha256": adapter_sha,
                    "local_vector_sha256": local_vector_sha,
                    "applied_vector_sha256": applied_vector_sha,
                    "runtime_intervention_receipt_sha256": intervention_receipt_sha,
                    "gain": selected_gain,
                    "layer_start": selected_layer,
                    "layer_end": selected_layer,
                    "downstream_transformer_layers": N_LAYER - selected_layer - 1,
                    "terminal_output_projection_shortcut": False,
                    "basis_constructed_without_output_head": True,
                },
                "controls": controls_summary,
                "calibration": {
                    "family_id": calibration_family_id,
                    "seeds": [s for s, _, _ in CALIBRATION],
                    "selected_gain": selected_gain,
                    "selected_layer": selected_layer,
                    "selected_orientation": selected["orientation"],
                    "counterbalanced_target_labels": [t for _, t, _ in CALIBRATION],
                },
                "holdout": {
                    "family_id": holdout_family_id,
                    "seeds": [s for s, _, _ in FRESH_HOLDOUT],
                    "reproducible_directional_effect": True,
                    "strongest_counterexample_recorded": True,
                    "analysis_receipt_sha256": analysis_receipt_sha,
                    "evaluation_independent_of_vector_derivation": True,
                    "metric_definition_sha256": metric_sha,
                    "metric_uses_output_tokens": True,
                    "label_mapping_counterbalanced": True,
                    "counterbalanced_target_labels": [t for _, t, _ in FRESH_HOLDOUT],
                },
                "vector_derivation": {
                    "method": "internal activation contrast AFFIRMATIVE - 0.5*(NEGATIVE+NEUTRAL), normalized; no output-head weights",
                    "uses_output_head_weights": False,
                    "uses_holdout_data": False,
                    "uses_evaluation_output_labels": False,
                    "derivation_family_id": derivation_family,
                    "derivation_receipt_sha256": selected_derivation_receipt,
                },
                "transport": {
                    "hosted_prompt_only": False,
                    "api_served": True,
                    "loopback_only": True,
                    "endpoint": endpoint,
                },
                "target": {
                    "relation": "ZERO_COST_API_SERVED_MODEL_RUNTIME",
                    "execution_surface": "LOCAL_LOOPBACK_API",
                    "zero_provider_billing": True,
                    "local_runtime_execution_receipt_sha256": api_runtime_receipt_sha,
                    "provider": "local",
                    "model_or_route": f"Qwen/Qwen3-0.6B-GGUF:Q8_0@{gguf_sha}/llama.cpp@{llama_commit}",
                },
            }
            candidate_path.write_text(json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
            gate = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "trigger1_jspace_promotion_gate.py"), "--candidate", str(candidate_path)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
                check=False,
            )
            if gate.returncode != 0:
                raise RuntimeError(f"PROMOTION_GATE_EXECUTION_FAILED:{gate.returncode}:{gate.stderr[-1200:]}")
            promotion_verdict = json.loads(gate.stdout)
            verdict_path.write_text(json.dumps(promotion_verdict, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

        owner_pass = bool(promotion_verdict and promotion_verdict.get("owner_trigger1_goal_credit_candidate") is True)
        result = {
            "schema": SCHEMA,
            "status": "PASS_OWNER_TRIGGER1_CANDIDATE" if owner_pass else ("PASS_MECHANISM_ONLY" if holdout_metrics.get("pass") else "SCIENTIFIC_NEGATIVE"),
            "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": source,
            "model": base.MODEL_ID,
            "model_revision": base.MODEL_REVISION,
            "source_checkpoint_sha256": source_checkpoint_sha,
            "source_weight_manifest": weight_manifest,
            "tokenizer_sha256": tokenizer_sha,
            "target_checkpoint_sha256": gguf_sha,
            "llama_cpp_source_commit": llama_commit,
            "native_harness_sha256": harness_sha,
            "runtime_identity": runtime_identity,
            "runtime_build_sha256": runtime_build_sha,
            "metric_definition": METRIC_DEFINITION,
            "metric_definition_sha256": metric_sha,
            "derivation_family_id": derivation_family,
            "basis_evidence": basis_evidence,
            "calibration_candidates": calibration_candidates,
            "selected_calibration_candidate": selected,
            "fresh_holdout": {
                "seeds": [s for s, _, _ in FRESH_HOLDOUT],
                "target_labels": [t for _, t, _ in FRESH_HOLDOUT],
                "family_sha256": canonical_sha([{"seed": s, "target": t, "prompt": p} for s, t, p in FRESH_HOLDOUT]),
                "rows": holdout_rows,
                "metrics": holdout_metrics,
                "api_request_sha256": holdout_response.get("request_sha256") if holdout_response else None,
                "api_response_sha256": holdout_response.get("response_sha256") if holdout_response else None,
            },
            "source_packet": source_packet,
            "source_packet_sha256": source_packet_sha,
            "adapter": adapter,
            "adapter_sha256": adapter_sha,
            "local_control_packet": local_packet,
            "local_control_packet_sha256": local_packet_sha,
            "controls": controls_summary,
            "loopback_endpoint": endpoint,
            "api_runtime_receipt_sha256": api_runtime_receipt_sha,
            "promotion_candidate_written": candidate is not None,
            "promotion_gate_verdict": promotion_verdict,
            "external_provider_credentials_read": False,
            "zero_provider_billing": True,
            "evidence_boundary": "Even an owner Trigger-1 candidate does not mint canonical credit, whole EntityOS/HCU, training, consciousness, or whole-product pass; the promotion gate itself is explicitly non-minting.",
        }
        result["result_sha256"] = canonical_sha(result)
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        return 0 if owner_pass else 2
    except Exception as exc:
        if server is not None:
            try:
                server.shutdown()
                server.server_close()
            except Exception:
                pass
        blocked = {
            "schema": SCHEMA,
            "status": "BLOCKED_SEMANTIC_COUNTERBALANCED_NATIVE_CVEC",
            "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": source,
            "reason": f"{type(exc).__name__}:{str(exc)[:2200]}",
            "external_provider_credentials_read": False,
            "zero_provider_billing": True,
        }
        blocked["result_sha256"] = canonical_sha(blocked)
        result_path.write_text(json.dumps(blocked, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

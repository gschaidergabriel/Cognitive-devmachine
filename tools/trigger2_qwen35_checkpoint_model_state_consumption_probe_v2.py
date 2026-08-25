#!/usr/bin/env python3
"""Trigger-2 Qwen3.5 checkpoint model-state consumption probe v2.

SOURCE/EVAL ONLY. This successor preserves useful v1 checkpoint/input evidence but
closes a narrower proof gap: manifest-bound shard paths being opened does not itself
prove the exact in-memory tensor state consumed by a forward pass (notably with mmap).

V2 adds a deterministic post-load model-state witness, independent safetensor tensor
reconciliation, explicit loader/backend identity, model-visible input identity, and a
single call binding. PASS is component evidence only: no checkpoint winner, training,
J-Space, HCU, or whole-EntityOS credit is minted.
"""
from __future__ import annotations

import argparse
import gc
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Mapping

SCHEMA = "CLAY_TRIGGER2_CHECKPOINT_MODEL_STATE_CONSUMPTION_ABI/v2"
CHILD_SCHEMA = "CLAY_TRIGGER2_CHECKPOINT_MODEL_STATE_CONSUMPTION_CHILD/v2"
DEFAULT_CANONICAL_PROMPT = "[USER]\nReturn exactly: identity-probe\n[ASSISTANT]\n"


class ProbeError(RuntimeError):
    pass


def _json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def _sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    h = sha256()
    with path.open("rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def _canonical_path(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _manifest_map(identity: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = identity.get("file_manifest")
    if not isinstance(rows, list) or not rows:
        raise ProbeError("IDENTITY_FILE_MANIFEST_REQUIRED")
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ProbeError("IDENTITY_FILE_MANIFEST_ROW_INVALID")
        rel, digest, size = row.get("path"), row.get("sha256"), row.get("size")
        if not isinstance(rel, str) or not rel:
            raise ProbeError("IDENTITY_FILE_MANIFEST_PATH_INVALID")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ProbeError(f"IDENTITY_FILE_MANIFEST_SHA256_INVALID:{rel}")
        if size is not None and (not isinstance(size, int) or size < 0):
            raise ProbeError(f"IDENTITY_FILE_MANIFEST_SIZE_INVALID:{rel}")
        if rel in out:
            raise ProbeError(f"IDENTITY_FILE_MANIFEST_DUPLICATE_PATH:{rel}")
        out[rel] = row
    return out


def _verify_manifest(local_dir: Path, identity: dict[str, Any]) -> tuple[bool, list[dict[str, Any]]]:
    mismatches: list[dict[str, Any]] = []
    for rel, row in sorted(_manifest_map(identity).items()):
        p = local_dir / rel
        if not p.is_file():
            mismatches.append({"path": rel, "failure": "MISSING"})
            continue
        actual_size, actual_sha = p.stat().st_size, _sha256_file(p)
        if row.get("size") is not None and actual_size != row.get("size"):
            mismatches.append({"path": rel, "failure": "SIZE_MISMATCH", "expected": row.get("size"), "actual": actual_size})
        if actual_sha != row.get("sha256"):
            mismatches.append({"path": rel, "failure": "SHA256_MISMATCH", "expected": row.get("sha256"), "actual": actual_sha})
    return not mismatches, mismatches


def _weight_shards(local_dir: Path, identity: dict[str, Any]) -> list[str]:
    manifest = _manifest_map(identity)
    shards: set[str] = set()
    index_files = [rel for rel in manifest if rel.endswith(".index.json") and ("safetensors" in rel or "pytorch_model" in rel)]
    for rel in index_files:
        p = local_dir / rel
        if not p.is_file():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ProbeError(f"WEIGHT_INDEX_JSON_INVALID:{rel}:{type(exc).__name__}") from exc
        weight_map = data.get("weight_map")
        if isinstance(weight_map, dict):
            for shard in weight_map.values():
                if isinstance(shard, str) and shard:
                    shards.add(shard)
    if not shards:
        shards = {rel for rel in manifest if rel.endswith((".safetensors", ".bin", ".pt", ".pth")) and not rel.endswith(".index.json")}
    if not shards:
        raise ProbeError("NO_WEIGHT_SHARDS_RESOLVED")
    unknown = sorted(shards - set(manifest))
    if unknown:
        raise ProbeError("WEIGHT_SHARD_NOT_MANIFEST_BOUND:" + ",".join(unknown))
    return sorted(shards)


def _tensor_identity(tensor: Any) -> dict[str, Any]:
    import torch
    t = tensor.detach().cpu().contiguous()
    raw = t.view(torch.uint8).numpy().tobytes(order="C")
    return {"dtype": str(t.dtype), "shape": [int(x) for x in t.shape], "numel": int(t.numel()), "raw_nbytes": len(raw), "raw_bytes_sha256": _sha256_bytes(raw)}


def _record_digest(record: Mapping[str, Any]) -> str:
    return _sha256_bytes(_json_bytes(dict(record)))


def _state_digest(records: Mapping[str, Mapping[str, Any]]) -> str:
    normalized = [{"name": name, **dict(records[name])} for name in sorted(records)]
    return _sha256_bytes(_json_bytes(normalized))


def _model_state_records(model: Any) -> dict[str, dict[str, Any]]:
    state = model.state_dict()
    records: dict[str, dict[str, Any]] = {}
    for name in sorted(state):
        value = state[name]
        if not hasattr(value, "detach"):
            raise ProbeError(f"MODEL_STATE_NON_TENSOR:{name}")
        records[name] = _tensor_identity(value)
    if not records:
        raise ProbeError("MODEL_STATE_EMPTY")
    return records


def _checkpoint_state_records(local_dir: Path, identity: dict[str, Any], backend: str) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    if backend not in {"mmap", "pread"}:
        raise ProbeError("UNSUPPORTED_SAFETENSORS_BACKEND")
    try:
        import safetensors
        from safetensors.torch import load_file
    except Exception as exc:
        raise ProbeError(f"SAFETENSORS_IMPORT_FAILED:{type(exc).__name__}:{exc}") from exc
    if "backend" not in inspect.signature(load_file).parameters:
        raise ProbeError("SAFETENSORS_BACKEND_PARAMETER_REQUIRED_FOR_V2:" + str(getattr(safetensors, "__version__", "UNKNOWN")))
    manifest = _manifest_map(identity)
    records: dict[str, dict[str, Any]] = {}
    shard_evidence: list[dict[str, Any]] = []
    for rel in _weight_shards(local_dir, identity):
        if not rel.endswith(".safetensors"):
            raise ProbeError(f"V2_REQUIRES_SAFETENSORS_SHARD:{rel}")
        tensors = load_file(str(local_dir / rel), device="cpu", backend=backend)
        keys: list[str] = []
        for name in sorted(tensors):
            if name in records:
                raise ProbeError(f"CHECKPOINT_DUPLICATE_TENSOR_KEY:{name}")
            records[name] = _tensor_identity(tensors[name])
            keys.append(name)
        shard_evidence.append({"path": rel, "manifest_sha256": manifest[rel]["sha256"], "backend": backend, "tensor_count": len(keys), "tensor_keyset_sha256": _sha256_bytes(_json_bytes(keys))})
        del tensors
        gc.collect()
    if not records:
        raise ProbeError("CHECKPOINT_TENSOR_STATE_EMPTY")
    return records, shard_evidence


def _loading_info_failures(loading_info: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    for key in ("missing_keys", "unexpected_keys", "mismatched_keys", "error_msgs"):
        value = loading_info.get(key, [])
        if value is None:
            value = []
        if not isinstance(value, (list, tuple)):
            failures.append(f"LOADING_INFO_{key.upper()}_INVALID")
        elif value:
            failures.append(f"LOADING_INFO_{key.upper()}_NONEMPTY:{len(value)}")
    return failures


def _reconcile_state_records(checkpoint: Mapping[str, Mapping[str, Any]], loaded: Mapping[str, Mapping[str, Any]], loading_info: Mapping[str, Any]) -> dict[str, Any]:
    failures = _loading_info_failures(loading_info)
    missing = sorted(set(checkpoint) - set(loaded))
    if missing:
        failures.append(f"CHECKPOINT_KEYS_MISSING_IN_LOADED_STATE:{len(missing)}")
    mismatches: list[dict[str, Any]] = []
    for name in sorted(set(checkpoint) & set(loaded)):
        expected, actual = dict(checkpoint[name]), dict(loaded[name])
        if expected != actual:
            mismatches.append({"name": name, "checkpoint_record_digest": _record_digest(expected), "loaded_record_digest": _record_digest(actual), "dtype_match": expected.get("dtype") == actual.get("dtype"), "shape_match": expected.get("shape") == actual.get("shape"), "raw_bytes_match": expected.get("raw_bytes_sha256") == actual.get("raw_bytes_sha256")})
    if mismatches:
        failures.append(f"CHECKPOINT_LOADED_TENSOR_MISMATCH:{len(mismatches)}")
    source_fingerprints: dict[tuple[Any, ...], list[str]] = {}
    for name, row in checkpoint.items():
        fp = (row.get("dtype"), tuple(row.get("shape", [])), row.get("raw_bytes_sha256"))
        source_fingerprints.setdefault(fp, []).append(name)
    aliases: list[dict[str, Any]] = []
    unexplained: list[str] = []
    for name in sorted(set(loaded) - set(checkpoint)):
        row = loaded[name]
        fp = (row.get("dtype"), tuple(row.get("shape", [])), row.get("raw_bytes_sha256"))
        sources = sorted(source_fingerprints.get(fp, []))
        if sources:
            aliases.append({"loaded_key": name, "byte_identical_to": sources})
        else:
            unexplained.append(name)
    if unexplained:
        failures.append(f"UNEXPLAINED_EXTRA_PERSISTENT_LOADED_STATE:{len(unexplained)}")
    return {"pass": not failures, "checkpoint_key_count": len(checkpoint), "loaded_state_key_count": len(loaded), "checkpoint_state_digest": _state_digest(checkpoint), "loaded_state_digest": _state_digest(loaded), "missing_checkpoint_keys": missing, "tensor_mismatches": mismatches, "byte_identical_extra_aliases": aliases, "unexplained_extra_loaded_keys": unexplained, "loading_info": {k: list(loading_info.get(k) or []) for k in ("missing_keys", "unexpected_keys", "mismatched_keys", "error_msgs")}, "failures": failures}


def _parse_strace_opened_paths(trace_text: str, local_dir: Path) -> list[str]:
    root = Path(os.path.abspath(os.path.normpath(str(local_dir.expanduser()))))
    found: set[str] = set()
    path_re = re.compile(r'(?:open|openat)\([^\n]*?"((?:\\.|[^"\\])*)"')
    for match in path_re.finditer(trace_text):
        try:
            decoded = bytes(match.group(1), "utf-8").decode("unicode_escape")
        except Exception:
            continue
        p = Path(decoded)
        if not p.is_absolute():
            continue
        cp = Path(os.path.abspath(os.path.normpath(str(p))))
        try:
            rel = cp.relative_to(root).as_posix()
        except ValueError:
            continue
        if (root / rel).is_file():
            found.add(rel)
    return sorted(found)


def _opened_manifest_evidence(local_dir: Path, identity: dict[str, Any], opened_rel_paths: Iterable[str]) -> dict[str, Any]:
    manifest = _manifest_map(identity)
    opened = sorted(set(opened_rel_paths))
    unknown = [rel for rel in opened if rel not in manifest]
    mismatches: list[dict[str, Any]] = []
    for rel in opened:
        if rel in manifest:
            actual, expected = _sha256_file(local_dir / rel), manifest[rel]["sha256"]
            if actual != expected:
                mismatches.append({"path": rel, "expected": expected, "actual": actual})
    required = _weight_shards(local_dir, identity)
    missing = sorted(set(required) - set(opened))
    return {"pass": not unknown and not mismatches and not missing, "opened_local_paths": opened, "unknown_opened_local_files": unknown, "opened_file_digest_mismatches": mismatches, "required_weight_shards": required, "missing_opened_weight_shards": missing, "scope": "CORROBORATING_OPENED_MANIFEST_BOUND_PATH_EVIDENCE_NOT_BYTE_CONSUMPTION_TRANSCRIPT"}


def _call_binding_digest(*, candidate_id: str, checkpoint_manifest_sha256: str, checkpoint_state_digest: str, loaded_state_digest: str, rendered_utf8_sha256: str, input_ids: Mapping[str, Any], attention_mask: Mapping[str, Any] | None, runtime: Mapping[str, Any], forward_output: Mapping[str, Any]) -> str:
    return _sha256_bytes(_json_bytes({"schema": "CLAY_TRIGGER2_MODEL_CALL_BINDING/v2", "candidate_id": candidate_id, "checkpoint_manifest_sha256": checkpoint_manifest_sha256, "checkpoint_state_digest": checkpoint_state_digest, "loaded_state_digest": loaded_state_digest, "rendered_utf8_sha256": rendered_utf8_sha256, "input_ids": dict(input_ids), "attention_mask": None if attention_mask is None else dict(attention_mask), "runtime": dict(runtime), "forward_output": dict(forward_output)}))


def _runtime_identity(*, torch_mod: Any, transformers_mod: Any, safetensors_mod: Any, model: Any, tokenizer: Any, disable_mmap: bool, checkpoint_backend: str) -> dict[str, Any]:
    first_param = next(model.parameters(), None)
    return {"python": sys.version.split()[0], "torch": str(getattr(torch_mod, "__version__", "UNKNOWN")), "transformers": str(getattr(transformers_mod, "__version__", "UNKNOWN")), "safetensors": str(getattr(safetensors_mod, "__version__", "UNKNOWN")), "platform": platform.platform(), "model_class": type(model).__name__, "tokenizer_class": type(tokenizer).__name__, "config_class": type(model.config).__name__, "parameter_dtype": str(first_param.dtype) if first_param is not None else None, "parameter_device": str(first_param.device) if first_param is not None else None, "transformers_disable_mmap": disable_mmap, "independent_checkpoint_read_backend": checkpoint_backend, "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE"), "TRANSFORMERS_OFFLINE": os.environ.get("TRANSFORMERS_OFFLINE")}


def _child_run(args: argparse.Namespace) -> int:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    local_dir, identity_path, out_path = _canonical_path(Path(args.local_dir)), _canonical_path(Path(args.identity_receipt)), _canonical_path(Path(args.child_output))
    credits = {"checkpoint_selection_credit": 0, "training_credit": 0, "causal_jspace_credit": 0, "whole_hcu_runtime_credit": 0, "whole_entityos_runtime_credit": 0}
    try:
        import torch, transformers, safetensors
        from transformers import AutoModelForCausalLM, AutoTokenizer
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
        if identity.get("candidate_id") != args.candidate_id:
            raise ProbeError("CANDIDATE_ID_MISMATCH")
        if identity.get("identity_complete") is not True:
            raise ProbeError("IDENTITY_RECEIPT_NOT_COMPLETE")
        tokenizer = AutoTokenizer.from_pretrained(str(local_dir), local_files_only=True, trust_remote_code=False)
        loaded_obj = AutoModelForCausalLM.from_pretrained(str(local_dir), local_files_only=True, trust_remote_code=False, low_cpu_mem_usage=False, output_loading_info=True, disable_mmap=args.disable_mmap)
        if not isinstance(loaded_obj, tuple) or len(loaded_obj) != 2:
            raise ProbeError("OUTPUT_LOADING_INFO_TUPLE_REQUIRED")
        model, loading_info = loaded_obj
        if not isinstance(loading_info, dict):
            raise ProbeError("LOADING_INFO_OBJECT_REQUIRED")
        model.eval()
        loaded_before = _model_state_records(model)
        checkpoint_records, shard_evidence = _checkpoint_state_records(local_dir, identity, args.checkpoint_backend)
        reconciliation = _reconcile_state_records(checkpoint_records, loaded_before, loading_info)
        if not reconciliation["pass"]:
            raise ProbeError("MANIFEST_TO_LOADED_STATE_RECONCILIATION_FAILED:" + "|".join(reconciliation["failures"]))
        messages = [{"role": "user", "content": "Return exactly: identity-probe"}]
        chat_template = getattr(tokenizer, "chat_template", None)
        chat_template_text = chat_template if isinstance(chat_template, str) and chat_template else None
        if args.render_mode == "native":
            if not chat_template_text:
                raise ProbeError("NATIVE_RENDER_REQUIRES_CHAT_TEMPLATE")
            rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            template_params = {"tokenize": False, "add_generation_prompt": True}
        elif args.render_mode == "canonical":
            rendered, template_params = args.canonical_prompt, None
        else:
            raise ProbeError("UNKNOWN_RENDER_MODE")
        rendered_bytes = rendered.encode("utf-8")
        encoded = tokenizer(rendered, return_tensors="pt", add_special_tokens=False)
        input_ids, attention_mask = encoded["input_ids"], encoded.get("attention_mask")
        iid = _tensor_identity(input_ids)
        amid = _tensor_identity(attention_mask) if attention_mask is not None else None
        runtime = _runtime_identity(torch_mod=torch, transformers_mod=transformers, safetensors_mod=safetensors, model=model, tokenizer=tokenizer, disable_mmap=args.disable_mmap, checkpoint_backend=args.checkpoint_backend)
        with torch.no_grad():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False)
        logits = outputs.logits
        last_logits = logits[:, -1, :].detach().cpu().contiguous()
        forward_output = {"full_logits_shape": [int(x) for x in logits.shape], "last_logits": _tensor_identity(last_logits), "top1_token_id": int(last_logits.argmax(dim=-1).item())}
        loaded_after = _model_state_records(model)
        before_digest, after_digest = _state_digest(loaded_before), _state_digest(loaded_after)
        if before_digest != after_digest:
            raise ProbeError("PERSISTENT_MODEL_STATE_MUTATED_DURING_FORWARD")
        call_digest = _call_binding_digest(candidate_id=args.candidate_id, checkpoint_manifest_sha256=str(identity.get("file_manifest_sha256")), checkpoint_state_digest=reconciliation["checkpoint_state_digest"], loaded_state_digest=before_digest, rendered_utf8_sha256=_sha256_bytes(rendered_bytes), input_ids=iid, attention_mask=amid, runtime=runtime, forward_output=forward_output)
        payload = {"schema": CHILD_SCHEMA, "pass": True, "candidate_id": args.candidate_id, "candidate_local_dir": str(local_dir), "identity_receipt_sha256": _sha256_file(identity_path), "checkpoint_manifest_sha256": identity.get("file_manifest_sha256"), "loader_policy": {"transformers_disable_mmap_requested": args.disable_mmap, "independent_checkpoint_read_backend": args.checkpoint_backend}, "loading_info": reconciliation["loading_info"], "checkpoint_shard_evidence": shard_evidence, "state_reconciliation": reconciliation, "post_load_state_before_forward_digest": before_digest, "post_forward_state_digest": after_digest, "persistent_state_stable_across_forward": True, "canonical_messages_sha256": _sha256_bytes(_json_bytes(messages)), "render_mode": args.render_mode, "resolved_chat_template": "PRESENT" if chat_template_text else "NO_TEMPLATE", "chat_template_text_sha256": _sha256_bytes(chat_template_text.encode("utf-8")) if chat_template_text else None, "apply_chat_template_parameters": template_params, "rendered_utf8_sha256": _sha256_bytes(rendered_bytes), "rendered_utf8_nbytes": len(rendered_bytes), "input_ids": iid, "attention_mask": amid, "forward_observed": True, "forward_output": forward_output, "runtime": runtime, "model_call_binding_sha256": call_digest, "model_state_consumption_component_eligible": True, "credit_boundary": credits}
    except Exception as exc:
        payload = {"schema": CHILD_SCHEMA, "pass": False, "candidate_id": args.candidate_id, "failure": f"{type(exc).__name__}:{exc}", "model_state_consumption_component_eligible": False, "credit_boundary": credits}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if payload.get("pass") else 2


def _parent_run(args: argparse.Namespace) -> int:
    local_dir, identity_path, output_path = _canonical_path(Path(args.local_dir)), _canonical_path(Path(args.identity_receipt)), _canonical_path(Path(args.output))
    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    result: dict[str, Any] = {"schema": SCHEMA, "pass": False, "candidate_id": args.candidate_id, "local_dir": str(local_dir), "identity_receipt": str(identity_path), "identity_receipt_sha256": _sha256_file(identity_path), "render_mode": args.render_mode, "model_loader_disable_mmap": args.disable_mmap, "independent_checkpoint_backend": args.checkpoint_backend, "evidence_scope": "COMPONENT_ONLY_NO_WINNER_NO_TRAINING_NO_JSPACE_PRODUCT_CREDIT", "credit_boundary": {"checkpoint_selection_credit": 0, "training_credit": 0, "causal_jspace_credit": 0, "whole_hcu_runtime_credit": 0, "whole_entityos_runtime_credit": 0}}
    try:
        if identity.get("candidate_id") != args.candidate_id:
            raise ProbeError("CANDIDATE_ID_MISMATCH")
        if identity.get("identity_complete") is not True:
            raise ProbeError("IDENTITY_RECEIPT_NOT_COMPLETE")
        manifest_ok, manifest_mismatches = _verify_manifest(local_dir, identity)
        result["preload_manifest_match"], result["preload_manifest_mismatches"] = manifest_ok, manifest_mismatches
        if not manifest_ok:
            raise ProbeError("PRELOAD_MANIFEST_MISMATCH")
        strace = shutil.which("strace")
        if not strace:
            raise ProbeError("STRACE_REQUIRED_TO_PRESERVE_V1_OPENED_SHARD_CORROBORATION")
        with tempfile.TemporaryDirectory(prefix="t2-qwen35-state-abi-v2-") as td:
            td_path = Path(td)
            trace_path, child_path = td_path / "strace.log", td_path / "child.json"
            cmd = [strace, "-f", "-e", "trace=open,openat", "-s", "4096", "-o", str(trace_path), sys.executable, str(Path(__file__).resolve()), "--child", "--candidate-id", args.candidate_id, "--local-dir", str(local_dir), "--identity-receipt", str(identity_path), "--child-output", str(child_path), "--render-mode", args.render_mode, "--canonical-prompt", args.canonical_prompt, "--checkpoint-backend", args.checkpoint_backend, "--disable-mmap" if args.disable_mmap else "--enable-mmap"]
            env = os.environ.copy(); env["HF_HUB_OFFLINE"] = "1"; env["TRANSFORMERS_OFFLINE"] = "1"
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, timeout=args.timeout_seconds)
            result["child_process"] = {"returncode": proc.returncode, "stderr_tail": proc.stderr[-2000:]}
            if not child_path.is_file():
                raise ProbeError("CHILD_RECEIPT_MISSING")
            child = json.loads(child_path.read_text(encoding="utf-8")); result["child"] = child
            if child.get("pass") is not True:
                raise ProbeError("CHILD_MODEL_STATE_CONSUMPTION_FAILED:" + str(child.get("failure")))
            opened = _parse_strace_opened_paths(trace_path.read_text(encoding="utf-8", errors="replace"), local_dir)
            opened_evidence = _opened_manifest_evidence(local_dir, identity, opened); result["opened_shard_corroboration"] = opened_evidence
            if not opened_evidence["pass"]:
                raise ProbeError("OPENED_SHARD_CORROBORATION_FAILED")
            post_ok, post_mismatches = _verify_manifest(local_dir, identity)
            result["postload_manifest_match"], result["postload_manifest_mismatches"] = post_ok, post_mismatches
            if not post_ok:
                raise ProbeError("POSTLOAD_MANIFEST_MUTATION_DETECTED")
            if child.get("model_state_consumption_component_eligible") is not True or child.get("persistent_state_stable_across_forward") is not True or not child.get("model_call_binding_sha256"):
                raise ProbeError("CHILD_V2_ACCEPTANCE_FIELDS_INCOMPLETE")
            result.update({"opened_manifest_bound_shards": True, "manifest_to_loaded_state_reconciled": True, "forward_bound_to_loaded_state_and_input": True, "selection_grade_consumed_model_state_component_eligible": True, "status": "PASS_COMPONENT_ONLY", "pass": True})
    except Exception as exc:
        result.update({"failure": f"{type(exc).__name__}:{exc}", "selection_grade_consumed_model_state_component_eligible": False, "status": "FAIL_OR_BLOCKED_COMPONENT_ONLY"})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result.get("pass") else 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate-id", required=True)
    p.add_argument("--local-dir", required=True)
    p.add_argument("--identity-receipt", required=True)
    p.add_argument("--output")
    p.add_argument("--child-output")
    p.add_argument("--render-mode", choices=["canonical", "native"], default="canonical")
    p.add_argument("--canonical-prompt", default=DEFAULT_CANONICAL_PROMPT)
    p.add_argument("--checkpoint-backend", choices=["pread", "mmap"], default="pread")
    g = p.add_mutually_exclusive_group(); g.add_argument("--disable-mmap", dest="disable_mmap", action="store_true"); g.add_argument("--enable-mmap", dest="disable_mmap", action="store_false")
    p.set_defaults(disable_mmap=True)
    p.add_argument("--timeout-seconds", type=int, default=900)
    p.add_argument("--child", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.child:
        if not args.child_output:
            raise SystemExit("--child-output required with --child")
        return _child_run(args)
    if not args.output:
        raise SystemExit("--output required in parent mode")
    return _parent_run(args)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Trigger-2 Qwen3.5 checkpoint/input identity ABI probe v1.

Selection-grade purpose only. This tool does not select a checkpoint, generate training
rows, or mint J-Space/training/HCU/EntityOS credit. Full PASS requires Linux strace
observation of the actual local files opened by the loader plus exact model-visible input
identity (rendered UTF-8 and token tensor dtype/shape/content).

The parent process launches itself in --child mode under strace. The child loads exactly
one frozen local checkpoint/tokenizer with local_files_only=True, renders one probe input,
and writes a compact child receipt. The parent parses open/openat events restricted to the
frozen local_dir, hashes observed files, compares them to the admitted checkpoint manifest,
and fails closed on ambiguity.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Iterable

SCHEMA = "CLAY_TRIGGER2_CHECKPOINT_INPUT_IDENTITY_ABI/v1"
CHILD_SCHEMA = "CLAY_TRIGGER2_CHECKPOINT_INPUT_IDENTITY_CHILD/v1"
DEFAULT_CANONICAL_PROMPT = "[USER]\nReturn exactly: identity-probe\n[ASSISTANT]\n"


class ProbeError(RuntimeError):
    pass


def _json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


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
        rel = row.get("path")
        digest = row.get("sha256")
        if not isinstance(rel, str) or not rel or not isinstance(digest, str) or len(digest) != 64:
            raise ProbeError("IDENTITY_FILE_MANIFEST_ROW_FIELDS_INVALID")
        if rel in out:
            raise ProbeError("IDENTITY_FILE_MANIFEST_DUPLICATE_PATH")
        out[rel] = row
    return out


def _verify_manifest(local_dir: Path, identity: dict[str, Any]) -> tuple[bool, list[dict[str, Any]]]:
    manifest = _manifest_map(identity)
    mismatches: list[dict[str, Any]] = []
    for rel, row in sorted(manifest.items()):
        p = local_dir / rel
        if not p.is_file():
            mismatches.append({"path": rel, "failure": "MISSING"})
            continue
        actual_size = p.stat().st_size
        actual_sha = _sha256_file(p)
        if row.get("size") is not None and actual_size != row.get("size"):
            mismatches.append({"path": rel, "failure": "SIZE_MISMATCH", "expected": row.get("size"), "actual": actual_size})
        if actual_sha != row.get("sha256"):
            mismatches.append({"path": rel, "failure": "SHA256_MISMATCH", "expected": row.get("sha256"), "actual": actual_sha})
    return not mismatches, mismatches


def _tensor_identity(tensor: Any) -> dict[str, Any]:
    """Bind tensor content/order/dtype/shape without relying on numpy dtype support."""
    import torch

    t = tensor.detach().cpu().contiguous()
    raw = t.view(torch.uint8).numpy().tobytes(order="C")
    dtype = str(t.dtype)
    shape = [int(x) for x in t.shape]
    envelope = b"TENSOR_IDENTITY_V1\0" + _json_bytes({"dtype": dtype, "shape": shape}) + b"\0" + raw
    return {
        "sha256": _sha256_bytes(envelope),
        "raw_bytes_sha256": _sha256_bytes(raw),
        "dtype": dtype,
        "shape": shape,
        "numel": int(t.numel()),
        "raw_nbytes": len(raw),
    }


def _relevant_weight_paths(local_dir: Path, identity: dict[str, Any]) -> set[str]:
    manifest = _manifest_map(identity)
    shards: set[str] = set()
    index_files = [rel for rel in manifest if rel.endswith(".index.json") and ("safetensors" in rel or "pytorch_model" in rel)]
    for rel in index_files:
        p = local_dir / rel
        if p.is_file():
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
        for rel in manifest:
            if rel.endswith((".safetensors", ".bin", ".pt", ".pth")):
                shards.add(rel)
    return shards


def _parse_strace_opened_paths(trace_text: str, local_dir: Path) -> list[str]:
    # IMPORTANT: use lexical absolute paths here, not Path.resolve(). Hugging Face
    # snapshot members are commonly symlinks into a sibling blobs/ directory. strace
    # records the pathname passed to open(2); resolving that symlink before the
    # containment check would incorrectly discard legitimate snapshot-member opens.
    root = Path(os.path.abspath(os.path.normpath(str(local_dir.expanduser()))))
    found: set[str] = set()
    # We accept only absolute paths lexically inside local_dir. Relative paths are
    # ignored rather than guessed from cwd; if a loader uses them, the probe fails
    # closed because required weight shards will remain unobserved.
    path_re = re.compile(r'(?:open|openat)\([^\n]*?"((?:\\.|[^"\\])*)"')
    for m in path_re.finditer(trace_text):
        encoded = m.group(1)
        try:
            decoded = bytes(encoded, "utf-8").decode("unicode_escape")
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


def _compare_consumed_to_manifest(
    local_dir: Path,
    identity: dict[str, Any],
    opened_rel_paths: Iterable[str],
) -> dict[str, Any]:
    manifest = _manifest_map(identity)
    opened = sorted(set(opened_rel_paths))
    unknown_opened = [rel for rel in opened if rel not in manifest]
    observed: list[dict[str, Any]] = []
    digest_mismatches: list[dict[str, Any]] = []
    for rel in opened:
        p = local_dir / rel
        actual = _sha256_file(p)
        row = manifest.get(rel)
        expected = None if row is None else row.get("sha256")
        observed.append({"path": rel, "sha256": actual, "expected_sha256": expected, "manifest_bound": row is not None})
        if row is not None and actual != expected:
            digest_mismatches.append({"path": rel, "expected": expected, "actual": actual})

    expected_weight_shards = sorted(_relevant_weight_paths(local_dir, identity))
    opened_weight_shards = sorted(set(expected_weight_shards) & set(opened))
    missing_weight_shards = sorted(set(expected_weight_shards) - set(opened))

    pass_ = not unknown_opened and not digest_mismatches and not missing_weight_shards and bool(expected_weight_shards)
    return {
        "pass": pass_,
        "observed_local_files": observed,
        "unknown_opened_local_files": unknown_opened,
        "digest_mismatches": digest_mismatches,
        "expected_weight_shards": expected_weight_shards,
        "opened_weight_shards": opened_weight_shards,
        "missing_weight_shards": missing_weight_shards,
    }


def _child_run(args: argparse.Namespace) -> int:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    local_dir = _canonical_path(Path(args.local_dir))
    out_path = Path(args.child_output)

    try:
        import torch
        import transformers
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(
            str(local_dir),
            local_files_only=True,
            trust_remote_code=False,
        )
        model = AutoModelForCausalLM.from_pretrained(
            str(local_dir),
            local_files_only=True,
            trust_remote_code=False,
            low_cpu_mem_usage=False,
        )
        model.eval()

        messages = [{"role": "user", "content": "Return exactly: identity-probe"}]
        messages_sha = _sha256_bytes(_json_bytes(messages))
        chat_template = getattr(tokenizer, "chat_template", None)
        chat_template_text = chat_template if isinstance(chat_template, str) and chat_template else None

        if args.render_mode == "native":
            if not chat_template_text:
                raise ProbeError("NATIVE_RENDER_REQUIRES_CHAT_TEMPLATE")
            rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            rendered_bytes = rendered.encode("utf-8")
            encoded = tokenizer(rendered, return_tensors="pt", add_special_tokens=False)
            apply_chat_template_parameters = {"tokenize": False, "add_generation_prompt": True}
        elif args.render_mode == "canonical":
            rendered = args.canonical_prompt
            rendered_bytes = rendered.encode("utf-8")
            encoded = tokenizer(rendered, return_tensors="pt", add_special_tokens=False)
            apply_chat_template_parameters = None
        else:
            raise ProbeError("UNKNOWN_RENDER_MODE")

        input_ids = encoded["input_ids"]
        attention_mask = encoded.get("attention_mask")
        with torch.no_grad():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False)
        logits = outputs.logits
        last_logits = logits[:, -1, :].detach().cpu().contiguous()
        top1 = int(last_logits.argmax(dim=-1).item())

        first_param = next(model.parameters(), None)
        text_config = model.config.get_text_config() if hasattr(model.config, "get_text_config") else model.config
        payload = {
            "schema": CHILD_SCHEMA,
            "pass": True,
            "candidate_local_dir": str(local_dir),
            "render_mode": args.render_mode,
            "loader": {
                "model_class": type(model).__name__,
                "tokenizer_class": type(tokenizer).__name__,
                "config_class": type(model.config).__name__,
                "text_model_type": getattr(text_config, "model_type", None),
                "local_files_only": True,
                "trust_remote_code": False,
                "low_cpu_mem_usage": False,
                "parameter_dtype": str(first_param.dtype) if first_param is not None else None,
                "parameter_device": str(first_param.device) if first_param is not None else None,
            },
            "canonical_messages_sha256": messages_sha,
            "resolved_chat_template": "PRESENT" if chat_template_text else "NO_TEMPLATE",
            "chat_template_text_sha256": _sha256_bytes(chat_template_text.encode("utf-8")) if chat_template_text else None,
            "apply_chat_template_parameters": apply_chat_template_parameters,
            "rendered_utf8_sha256": _sha256_bytes(rendered_bytes),
            "rendered_utf8_nbytes": len(rendered_bytes),
            "input_ids": _tensor_identity(input_ids),
            "attention_mask": _tensor_identity(attention_mask) if attention_mask is not None else None,
            "forward_observed": True,
            "forward_last_logits_shape": [int(x) for x in logits.shape],
            "forward_top1_token_id": top1,
            "runtime": {
                "python": sys.version.split()[0],
                "torch": getattr(torch, "__version__", "UNKNOWN"),
                "transformers": getattr(transformers, "__version__", "UNKNOWN"),
                "platform": sys.platform,
                "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE"),
                "TRANSFORMERS_OFFLINE": os.environ.get("TRANSFORMERS_OFFLINE"),
            },
            "credit_boundary": {
                "checkpoint_selection_credit": 0,
                "training_credit": 0,
                "causal_jspace_credit": 0,
                "whole_hcu_runtime_credit": 0,
                "whole_entityos_runtime_credit": 0,
            },
        }
    except Exception as exc:
        payload = {
            "schema": CHILD_SCHEMA,
            "pass": False,
            "failure": f"{type(exc).__name__}:{exc}",
            "credit_boundary": {
                "checkpoint_selection_credit": 0,
                "training_credit": 0,
                "causal_jspace_credit": 0,
                "whole_hcu_runtime_credit": 0,
                "whole_entityos_runtime_credit": 0,
            },
        }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if payload.get("pass") else 2


def _parent_run(args: argparse.Namespace) -> int:
    local_dir = _canonical_path(Path(args.local_dir))
    identity_path = _canonical_path(Path(args.identity_receipt))
    output_path = _canonical_path(Path(args.output))
    identity = json.loads(identity_path.read_text(encoding="utf-8"))

    result: dict[str, Any] = {
        "schema": SCHEMA,
        "pass": False,
        "candidate_id": args.candidate_id,
        "local_dir": str(local_dir),
        "identity_receipt": str(identity_path),
        "identity_receipt_sha256": _sha256_file(identity_path),
        "render_mode": args.render_mode,
        "consumption_capture": "LINUX_STRACE_OPEN_OPENAT_REQUIRED",
        "credit_boundary": {
            "checkpoint_selection_credit": 0,
            "training_credit": 0,
            "causal_jspace_credit": 0,
            "whole_hcu_runtime_credit": 0,
            "whole_entityos_runtime_credit": 0,
        },
    }

    try:
        if identity.get("candidate_id") != args.candidate_id:
            raise ProbeError("CANDIDATE_ID_MISMATCH")
        result["checkpoint_bundle_identity"] = {
            "candidate_id": identity.get("candidate_id"),
            "repo": identity.get("repo"),
            "requested_revision": identity.get("requested_revision"),
            "file_manifest_sha256": identity.get("file_manifest_sha256"),
            "config_json_sha256": identity.get("config_json_sha256"),
            "tokenizer_json_sha256": identity.get("tokenizer_json_sha256"),
            "tokenizer_config_json_sha256": identity.get("tokenizer_config_json_sha256"),
            "chat_template_jinja_sha256": identity.get("chat_template_jinja_sha256"),
        }
        if identity.get("identity_complete") is not True:
            raise ProbeError("IDENTITY_RECEIPT_NOT_COMPLETE")
        manifest_ok, manifest_mismatches = _verify_manifest(local_dir, identity)
        result["preload_manifest_match"] = manifest_ok
        result["preload_manifest_mismatches"] = manifest_mismatches
        if not manifest_ok:
            raise ProbeError("PRELOAD_MANIFEST_MISMATCH")

        strace = shutil.which("strace")
        if not strace:
            raise ProbeError("STRACE_REQUIRED_FOR_SELECTION_GRADE_CONSUMPTION_ATTESTATION")

        with tempfile.TemporaryDirectory(prefix="t2-qwen35-input-abi-") as td:
            td_path = Path(td)
            trace_path = td_path / "strace.log"
            child_path = td_path / "child.json"
            cmd = [
                strace,
                "-f",
                "-e",
                "trace=open,openat",
                "-s",
                "4096",
                "-o",
                str(trace_path),
                sys.executable,
                str(Path(__file__).resolve()),
                "--child",
                "--candidate-id",
                args.candidate_id,
                "--local-dir",
                str(local_dir),
                "--child-output",
                str(child_path),
                "--render-mode",
                args.render_mode,
                "--canonical-prompt",
                args.canonical_prompt,
            ]
            env = os.environ.copy()
            env["HF_HUB_OFFLINE"] = "1"
            env["TRANSFORMERS_OFFLINE"] = "1"
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, timeout=args.timeout_seconds)
            if not child_path.is_file():
                result["child_process"] = {"returncode": proc.returncode, "stderr_tail": proc.stderr[-2000:]}
                raise ProbeError("CHILD_RECEIPT_MISSING")
            child = json.loads(child_path.read_text(encoding="utf-8"))
            result["child"] = child
            result["child_process"] = {"returncode": proc.returncode, "stderr_tail": proc.stderr[-2000:]}
            if child.get("pass") is not True or child.get("forward_observed") is not True:
                raise ProbeError("CHILD_LOAD_RENDER_FORWARD_FAILED")

            trace_text = trace_path.read_text(encoding="utf-8", errors="replace")
            opened = _parse_strace_opened_paths(trace_text, local_dir)
            consumed = _compare_consumed_to_manifest(local_dir, identity, opened)
            result["consumed_identity"] = consumed
            result["opened_local_paths_count"] = len(opened)
            if not consumed.get("pass"):
                raise ProbeError("CONSUMED_IDENTITY_MISMATCH_OR_INCOMPLETE")

            post_ok, post_mismatches = _verify_manifest(local_dir, identity)
            result["postload_manifest_match"] = post_ok
            result["postload_manifest_mismatches"] = post_mismatches
            if not post_ok:
                raise ProbeError("POSTLOAD_MANIFEST_MUTATION_DETECTED")

            result["consumed_identity_match"] = True
            result["prompt_input_identity_complete"] = True
            result["selection_identity_abi_component_status"] = "PASS_COMPONENT_ONLY"
            result["pass"] = True
    except Exception as exc:
        result["failure"] = f"{type(exc).__name__}:{exc}"
        result["consumed_identity_match"] = False
        result["prompt_input_identity_complete"] = False
        result["selection_identity_abi_component_status"] = "FAIL_OR_BLOCKED_COMPONENT_ONLY"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result.get("pass") else 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate-id", required=True)
    p.add_argument("--local-dir", required=True)
    p.add_argument("--identity-receipt")
    p.add_argument("--output")
    p.add_argument("--render-mode", choices=["canonical", "native"], default="canonical")
    p.add_argument("--canonical-prompt", default=DEFAULT_CANONICAL_PROMPT)
    p.add_argument("--timeout-seconds", type=int, default=300)
    p.add_argument("--child", action="store_true")
    p.add_argument("--child-output")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.child:
        if not args.child_output:
            raise SystemExit("--child-output required with --child")
        return _child_run(args)
    if not args.identity_receipt or not args.output:
        raise SystemExit("--identity-receipt and --output required in parent mode")
    return _parent_run(args)


if __name__ == "__main__":
    raise SystemExit(main())

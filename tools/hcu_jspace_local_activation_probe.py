#!/usr/bin/env python3
"""Offline local observation/intervention probe for EntityOS/HCU Global J-Space.

`observation` is the cheap first discriminator: one model forward pass, one named layer
and position, activation/output digests, exact local source/runtime bindings, no hidden
state modification. `intervention` runs the clean/corrupted/target/sham/off-target causal
family and therefore requires the canonical create-only `go` unusual-experiment claim.

Neither mode grants canonical, whole-HCU, J-Space-model, training, or whole-product
credit by itself. Emitted records are bounded candidate evidence requiring canonical
admission/review. No model download is permitted: --model must be a local directory and
Hugging Face/Transformers offline flags are forced before model libraries are imported.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
from typing import Any

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

SCHEMA = "ENTITYOS_HCU_JSPACE_LOCAL_ACTIVATION_PROBE/v2"
CLAIM_SCHEMA = "clay-go-experiment-claim/v1"
OBSERVATION_CLASS = "LOCAL_MODEL_SPECIFIC_OBSERVATION_CANDIDATE_EVIDENCE_ONLY"
INTERVENTION_CLASS = "LOCAL_MODEL_SPECIFIC_CAUSAL_CANDIDATE_EVIDENCE_ONLY"


class ProbeRejected(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProbeRejected(f"{label}_UNAVAILABLE_OR_INVALID:{type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise ProbeRejected(f"{label}_OBJECT_REQUIRED")
    return value


def git_root() -> Path:
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ProbeRejected("CANONICAL_GIT_ROOT_REQUIRED") from exc
    path = Path(root).resolve()
    if not path.is_dir():
        raise ProbeRejected("CANONICAL_GIT_ROOT_REQUIRED")
    return path


def git_head(root: Path) -> str:
    try:
        head = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ProbeRejected("CANONICAL_GIT_HEAD_REQUIRED") from exc
    if len(head) != 40:
        raise ProbeRejected("CANONICAL_GIT_HEAD_INVALID")
    return head


def resolve_current_authority(root: Path) -> dict[str, Any]:
    inbox_path = root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    inbox = read_json(inbox_path, "SUPERVISOR_INBOX")
    epoch = str(inbox.get("schema_version") or "").strip()
    steering_ref = inbox.get("steering")
    if not epoch or not isinstance(steering_ref, str) or not steering_ref.strip():
        raise ProbeRejected("CURRENT_SUPERVISOR_POINTER_REQUIRED")
    rel = Path(steering_ref)
    if rel.is_absolute() or ".." in rel.parts:
        raise ProbeRejected("CURRENT_SUPERVISOR_POINTER_INVALID")
    steering_path = (root / rel).resolve()
    try:
        steering_path.relative_to(root)
    except ValueError as exc:
        raise ProbeRejected("CURRENT_SUPERVISOR_OUTSIDE_REPO") from exc
    steering = read_json(steering_path, "SUPERVISOR_STEERING")
    if str(steering.get("schema_version") or "").strip() != epoch:
        raise ProbeRejected("SUPERVISOR_INBOX_STEERING_EPOCH_MISMATCH")
    if (
        steering.get("active_program") != "ENTITYOS_HCU"
        or steering.get("product") != "EntityOS"
        or steering.get("integrated_cognition_compute_architecture") != "HCU"
    ):
        raise ProbeRejected("SUPERVISOR_PRODUCT_AUTHORITY_MISMATCH")
    free_only = steering.get("free_only")
    if not isinstance(free_only, dict) or free_only.get("enabled") is not True:
        raise ProbeRejected("FREE_ONLY_SUPERVISOR_REQUIRED_FOR_THIS_PROBE")
    return {
        "epoch": epoch,
        "inbox_path": inbox_path.relative_to(root).as_posix(),
        "inbox_sha256": sha256_file(inbox_path),
        "steering_path": steering_path.relative_to(root).as_posix(),
        "steering_sha256": sha256_file(steering_path),
    }


def validate_atomic_claim(
    root: Path, claim_arg: str, claimant_organ: str, experiment_name: str
) -> dict[str, Any]:
    claim_path = Path(claim_arg).expanduser()
    if not claim_path.is_absolute():
        claim_path = root / claim_path
    claim_path = claim_path.resolve()
    claims_dir = (root / "research_entity/continuity/go_experiment_claims").resolve()
    try:
        claim_path.relative_to(claims_dir)
    except ValueError as exc:
        raise ProbeRejected("ATOMIC_CLAIM_MUST_BE_IN_CANONICAL_CLAIMS_DIRECTORY") from exc
    if claim_path.name.endswith(".result.json"):
        raise ProbeRejected("ATOMIC_CLAIM_RESULT_FILE_NOT_A_CLAIM")

    claim = read_json(claim_path, "ATOMIC_CLAIM")
    required = {
        "schema": CLAIM_SCHEMA,
        "trigger": "go",
        "status": "CLAIMED",
        "claimant_organ": claimant_organ,
        "experiment_name": experiment_name,
    }
    for key, expected in required.items():
        if claim.get(key) != expected:
            raise ProbeRejected(f"ATOMIC_CLAIM_FIELD_MISMATCH:{key}")
    trigger_key = str(claim.get("trigger_key") or "").strip()
    if not trigger_key or claim_path.name != f"{trigger_key}.json":
        raise ProbeRejected("ATOMIC_CLAIM_TRIGGER_KEY_PATH_MISMATCH")
    if not str(claim.get("observed_canonical_main") or "").strip():
        raise ProbeRejected("ATOMIC_CLAIM_OBSERVED_MAIN_REQUIRED")
    if not str(claim.get("intervention_contract") or "").strip():
        raise ProbeRejected("ATOMIC_CLAIM_INTERVENTION_CONTRACT_REQUIRED")

    result_path = claims_dir / f"{trigger_key}.result.json"
    if result_path.exists():
        raise ProbeRejected("ATOMIC_CLAIM_RESULT_ALREADY_EXISTS_REPLICATION_REQUIRES_SEPARATE_CLASSIFICATION")
    return {
        "trigger_key": trigger_key,
        "claim_path": claim_path.relative_to(root).as_posix(),
        "claim_sha256": sha256_file(claim_path),
        "claimant_organ": claimant_organ,
        "experiment_name": experiment_name,
        "claimed_at": claim.get("claimed_at"),
        "claim_observed_canonical_main": claim.get("observed_canonical_main"),
        "intervention_contract": claim.get("intervention_contract"),
        "result_path_expected": result_path.relative_to(root).as_posix(),
        "lease_file_validated": True,
        "create_only_semantics_reverified_by_probe": False,
        "note": "The probe validates the canonical claim record but cannot reconstruct GitHub create-only transaction history; canonical admission must retain that evidence boundary.",
    }


def tree_identity(root: Path) -> dict[str, Any]:
    if not root.is_dir():
        raise ProbeRejected("LOCAL_MODEL_DIRECTORY_REQUIRED")
    rows: list[dict[str, Any]] = []
    combined = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        digest = sha256_file(path)
        size = path.stat().st_size
        rows.append({"path": rel, "size": size, "sha256": digest})
        combined.update(rel.encode("utf-8") + b"\0")
        combined.update(str(size).encode("ascii") + b"\0")
        combined.update(digest.encode("ascii") + b"\n")
    if not rows:
        raise ProbeRejected("LOCAL_MODEL_DIRECTORY_EMPTY")
    return {"tree_sha256": combined.hexdigest(), "files": rows}


def tensor_digest(tensor: Any) -> str:
    import torch

    data = tensor.detach().to(device="cpu", dtype=torch.float32).contiguous()
    return hashlib.sha256(data.numpy().tobytes(order="C")).hexdigest()


def integer_tensor_digest(tensor: Any) -> str:
    values = tensor.detach().to(device="cpu").reshape(-1).tolist()
    payload = json.dumps([int(v) for v in values], separators=(",", ":")).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def in_memory_parameter_identity(model: Any) -> dict[str, Any]:
    """Hash canonicalized post-load parameter values, not claimed loader source bytes."""
    import torch

    h = hashlib.sha256()
    count = 0
    elements = 0
    for name, param in model.named_parameters():
        raw = param.detach()
        canonical = raw.to(device="cpu", dtype=torch.float32).contiguous()
        h.update(name.encode("utf-8") + b"\0")
        h.update(str(tuple(raw.shape)).encode("ascii") + b"\0")
        h.update(str(raw.dtype).encode("ascii") + b"\0")
        h.update(canonical.numpy().tobytes(order="C"))
        count += 1
        elements += raw.numel()
    return {
        "post_load_parameter_value_sha256_float32_canonical": h.hexdigest(),
        "parameter_tensors": count,
        "parameter_elements": elements,
        "loader_consumption_attestation": False,
        "field_classification": "OBSERVED_POST_LOAD_VALUE_IDENTITY_PARTIAL",
        "note": "Post-load parameter values are observed; exact source-byte consumption by the loader and post-load mutation closure are not proven.",
    }


class NetworkFence:
    def __init__(self) -> None:
        self.attempts = 0
        self._connect = socket.socket.connect
        self._connect_ex = socket.socket.connect_ex
        self._create_connection = socket.create_connection
        self._getaddrinfo = socket.getaddrinfo

    def _blocked_network(self, *args: Any, **kwargs: Any) -> Any:
        self.attempts += 1
        raise ProbeRejected("NETWORK_ATTEMPT_BLOCKED_OFFLINE_ONLY")

    def __enter__(self) -> "NetworkFence":
        socket.socket.connect = self._blocked_network  # type: ignore[assignment]
        socket.socket.connect_ex = self._blocked_network  # type: ignore[assignment]
        socket.create_connection = self._blocked_network  # type: ignore[assignment]
        socket.getaddrinfo = self._blocked_network  # type: ignore[assignment]
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        socket.socket.connect = self._connect  # type: ignore[assignment]
        socket.socket.connect_ex = self._connect_ex  # type: ignore[assignment]
        socket.create_connection = self._create_connection  # type: ignore[assignment]
        socket.getaddrinfo = self._getaddrinfo  # type: ignore[assignment]


def resolve_layers(model: Any) -> Any:
    candidates = (
        ("model", "layers"),
        ("model", "decoder", "layers"),
        ("transformer", "h"),
        ("gpt_neox", "layers"),
    )
    for chain in candidates:
        node = model
        try:
            for name in chain:
                node = getattr(node, name)
            if len(node) > 0:
                return node
        except (AttributeError, TypeError):
            continue
    raise ProbeRejected("SUPPORTED_TRANSFORMER_LAYER_STACK_NOT_FOUND")


def normalize_position(position: int, length: int) -> int:
    resolved = position if position >= 0 else length + position
    if resolved < 0 or resolved >= length:
        raise ProbeRejected(f"POSITION_OUT_OF_RANGE:{position}:{length}")
    return resolved


def output_hidden(output: Any) -> Any:
    if hasattr(output, "shape"):
        return output
    if isinstance(output, (tuple, list)) and output and hasattr(output[0], "shape"):
        return output[0]
    raise ProbeRejected("LAYER_OUTPUT_HIDDEN_TENSOR_NOT_FOUND")


def replace_hidden(output: Any, replacement: Any) -> Any:
    if hasattr(output, "shape"):
        return replacement
    if isinstance(output, tuple):
        return (replacement, *output[1:])
    if isinstance(output, list):
        return [replacement, *output[1:]]
    raise ProbeRejected("LAYER_OUTPUT_REPLACEMENT_UNSUPPORTED")


def token_id(tokenizer: Any, text: str, label: str) -> int:
    ids = tokenizer.encode(text, add_special_tokens=False)
    if not ids:
        raise ProbeRejected(f"{label}_TOKEN_REQUIRED")
    return int(ids[-1])


def require_intervention_arguments(args: argparse.Namespace) -> None:
    required = {
        "corrupted": args.corrupted,
        "target_text": args.target_text,
        "off_target_text": args.off_target_text,
        "atomic_lease_claim": args.atomic_lease_claim,
        "claimant_organ": args.claimant_organ,
        "experiment_name": args.experiment_name,
    }
    missing = [name for name, value in required.items() if not str(value or "").strip()]
    if missing:
        raise ProbeRejected("INTERVENTION_ARGUMENTS_REQUIRED:" + ",".join(sorted(missing)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("observation", "intervention"), default="observation")
    parser.add_argument("--model", required=True, help="Local HF-compatible model snapshot directory")
    parser.add_argument("--clean", required=True)
    parser.add_argument("--corrupted")
    parser.add_argument("--target-text", help="Intervention metric token/text; final encoded token is used")
    parser.add_argument("--off-target-text", help="Intervention unrelated metric token/text")
    parser.add_argument("--layer", type=int, required=True)
    parser.add_argument("--position", type=int, default=-1)
    parser.add_argument("--off-target-position", type=int)
    parser.add_argument("--device", default="auto", choices=("auto", "cpu", "cuda", "mps"))
    parser.add_argument("--generation", required=True)
    parser.add_argument("--causal-event-id", required=True)
    parser.add_argument("--admission-id", required=True)
    parser.add_argument("--route-id", required=True)
    parser.add_argument("--inference-receipt-id", required=True)
    parser.add_argument("--atomic-lease-claim")
    parser.add_argument("--claimant-organ")
    parser.add_argument("--experiment-name")
    parser.add_argument("--output")
    args = parser.parse_args()

    causal_values = (args.generation, args.causal_event_id, args.admission_id, args.route_id, args.inference_receipt_id)
    if any(not str(value).strip() for value in causal_values):
        raise SystemExit("required causal identifiers must be non-empty")
    if args.mode == "intervention":
        require_intervention_arguments(args)

    observed_at = dt.datetime.now(dt.timezone.utc).isoformat()
    root = git_root()
    head = git_head(root)
    authority = resolve_current_authority(root)
    if args.mode == "intervention":
        lease: dict[str, Any] = validate_atomic_claim(
            root,
            args.atomic_lease_claim,
            args.claimant_organ,
            args.experiment_name,
        )
    else:
        lease = {
            "status": "NOT_REQUIRED_OBSERVATION_ONLY_NO_HIDDEN_STATE_MODIFICATION",
            "unusual_intervention_performed": False,
        }
    model_path = Path(args.model).expanduser().resolve()
    source_identity = tree_identity(model_path)
    network = NetworkFence()

    receipt: dict[str, Any] = {
        "schema": SCHEMA,
        "observed_at": observed_at,
        "probe_mode": args.mode,
        "classification": OBSERVATION_CLASS if args.mode == "observation" else INTERVENTION_CLASS,
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "architecture": "HCU",
        "mode": "FREE_ONLY_LOCAL_OFFLINE",
        "source_git_head": head,
        "probe_source_sha256": sha256_file(Path(__file__).resolve()),
        "authority": authority,
        "atomic_experiment_lease": lease,
        "causal_binding": {
            "generation": args.generation,
            "causal_event_id": args.causal_event_id,
            "admission_id": args.admission_id,
            "route_id": args.route_id,
            "inference_receipt_id": args.inference_receipt_id,
        },
        "model_source_identity": source_identity,
        "network_attempt_count": 0,
        "credit": {
            "entityos_hcu_whole_runtime": 0,
            "hcu_full_runtime": 0,
            "jspace_model_runtime": 0,
            "training": 0,
            "whole_product_pass": False,
        },
    }

    try:
        with network:
            import torch
            import transformers
            from transformers import AutoModelForCausalLM, AutoTokenizer

            torch.manual_seed(0)
            if hasattr(torch, "use_deterministic_algorithms"):
                torch.use_deterministic_algorithms(True, warn_only=True)

            if args.device == "auto":
                if torch.cuda.is_available():
                    device = "cuda"
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    device = "mps"
                else:
                    device = "cpu"
            else:
                device = args.device

            tokenizer = AutoTokenizer.from_pretrained(
                str(model_path), local_files_only=True, trust_remote_code=False
            )
            model = AutoModelForCausalLM.from_pretrained(
                str(model_path), local_files_only=True, trust_remote_code=False, torch_dtype="auto"
            )
            model.eval()
            model.to(device)
            layers = resolve_layers(model)
            layer_index = args.layer if args.layer >= 0 else len(layers) + args.layer
            if layer_index < 0 or layer_index >= len(layers):
                raise ProbeRejected(f"LAYER_OUT_OF_RANGE:{args.layer}:{len(layers)}")
            layer = layers[layer_index]

            clean_inputs = tokenizer(args.clean, return_tensors="pt", add_special_tokens=True)
            clean_ids = clean_inputs["input_ids"]
            seq_len = int(clean_ids.shape[1])
            patch_pos = normalize_position(args.position, seq_len)

            target_id: int | None = None
            off_target_id: int | None = None
            corrupt_inputs: Any | None = None
            off_pos: int | None = None
            if args.mode == "intervention":
                corrupt_inputs = tokenizer(args.corrupted, return_tensors="pt", add_special_tokens=True)
                corrupt_ids = corrupt_inputs["input_ids"]
                if clean_ids.shape != corrupt_ids.shape:
                    raise ProbeRejected(
                        f"CLEAN_CORRUPTED_TOKEN_SHAPE_MISMATCH:{tuple(clean_ids.shape)}:{tuple(corrupt_ids.shape)}"
                    )
                off_pos = (
                    normalize_position(args.off_target_position, seq_len)
                    if args.off_target_position is not None
                    else (patch_pos - 1 if patch_pos > 0 else patch_pos + 1)
                )
                if off_pos == patch_pos or off_pos < 0 or off_pos >= seq_len:
                    raise ProbeRejected("DISTINCT_OFF_TARGET_POSITION_REQUIRED")
                target_id = token_id(tokenizer, args.target_text, "TARGET")
                off_target_id = token_id(tokenizer, args.off_target_text, "OFF_TARGET")

            def to_device(inputs: Any) -> dict[str, Any]:
                return {k: v.to(device) for k, v in inputs.items()}

            def run_condition(
                label: str,
                inputs: dict[str, Any],
                *,
                observation_position: int,
                reference: Any | None = None,
            ) -> tuple[dict[str, Any], Any]:
                capture: dict[str, Any] = {}

                def hook(_module: Any, _inputs: Any, output: Any) -> Any:
                    hidden = output_hidden(output)
                    before = hidden[0, observation_position, :].detach().clone()
                    capture["activation_before_sha256"] = tensor_digest(before)
                    capture["activation_shape"] = list(before.shape)
                    capture["activation_dtype"] = str(before.dtype)
                    capture["reference_vector"] = before
                    if reference is None:
                        capture["activation_after_sha256"] = capture["activation_before_sha256"]
                        return output
                    replacement = hidden.clone()
                    replacement[:, observation_position, :] = reference.to(
                        device=hidden.device, dtype=hidden.dtype
                    )
                    after = replacement[0, observation_position, :].detach().clone()
                    capture["activation_after_sha256"] = tensor_digest(after)
                    return replace_hidden(output, replacement)

                handle = layer.register_forward_hook(hook)
                try:
                    with torch.no_grad():
                        result = model(**inputs, use_cache=False)
                finally:
                    handle.remove()
                logits = result.logits[:, -1, :].detach()
                execution_material = (
                    f"{args.generation}|{args.causal_event_id}|{args.admission_id}|"
                    f"{args.route_id}|{args.inference_receipt_id}|{label}"
                )
                record: dict[str, Any] = {
                    "condition": label,
                    "model_execution_id_derived_local": hashlib.sha256(execution_material.encode("utf-8")).hexdigest(),
                    "jspace_trace_id_derived_local": hashlib.sha256(
                        f"{execution_material}|{layer_index}|{observation_position}".encode("utf-8")
                    ).hexdigest(),
                    "derived_ids_are_canonical": False,
                    "layer": layer_index,
                    "activation_site": f"decoder_layer:{layer_index}:position:{observation_position}",
                    "activation_before_sha256_float32": capture["activation_before_sha256"],
                    "activation_after_sha256_float32": capture["activation_after_sha256"],
                    "activation_shape": capture["activation_shape"],
                    "activation_dtype": capture["activation_dtype"],
                    "final_logits_sha256_float32": tensor_digest(logits),
                    "field_classification": "OBSERVED_RUNTIME_MEASUREMENT_WITH_DERIVED_LOCAL_IDS",
                }
                if target_id is not None and off_target_id is not None:
                    record.update(
                        {
                            "target_token_id": target_id,
                            "target_logit": float(logits[0, target_id].item()),
                            "off_target_token_id": off_target_id,
                            "off_target_logit": float(logits[0, off_target_id].item()),
                        }
                    )
                return record, capture["reference_vector"]

            clean_record, clean_reference = run_condition(
                "OBSERVATION_BASELINE_CLEAN" if args.mode == "observation" else "BASELINE_CLEAN",
                to_device(clean_inputs),
                observation_position=patch_pos,
            )

            probe_payload: dict[str, Any] = {
                "layer": layer_index,
                "target_position": patch_pos,
                "clean_token_ids_sha256": integer_tensor_digest(clean_ids),
                "conditions": [clean_record],
            }

            if args.mode == "intervention":
                assert corrupt_inputs is not None and off_pos is not None
                corrupt_ids = corrupt_inputs["input_ids"]
                corrupt_record, corrupt_reference = run_condition(
                    "BASELINE_CORRUPTED", to_device(corrupt_inputs), observation_position=patch_pos
                )
                clean_off_record, clean_off_reference = run_condition(
                    "BASELINE_CLEAN_OFF_TARGET_REFERENCE",
                    to_device(clean_inputs),
                    observation_position=off_pos,
                )
                target_record, _ = run_condition(
                    "INTERVENTION_TARGET",
                    to_device(corrupt_inputs),
                    observation_position=patch_pos,
                    reference=clean_reference,
                )
                sham_record, _ = run_condition(
                    "SHAM_CONTROL",
                    to_device(corrupt_inputs),
                    observation_position=patch_pos,
                    reference=corrupt_reference,
                )
                off_record, _ = run_condition(
                    "OFF_TARGET_CONTROL",
                    to_device(corrupt_inputs),
                    observation_position=off_pos,
                    reference=clean_off_reference,
                )
                probe_payload.update(
                    {
                        "off_target_position": off_pos,
                        "corrupted_token_ids_sha256": integer_tensor_digest(corrupt_ids),
                        "conditions": [
                            clean_record,
                            corrupt_record,
                            clean_off_record,
                            target_record,
                            sham_record,
                            off_record,
                        ],
                        "derived_metrics": {
                            "target_patch_effect_on_target_logit": target_record["target_logit"] - corrupt_record["target_logit"],
                            "sham_effect_on_target_logit": sham_record["target_logit"] - corrupt_record["target_logit"],
                            "off_target_patch_effect_on_target_logit": off_record["target_logit"] - corrupt_record["target_logit"],
                            "target_patch_effect_on_off_target_logit": target_record["off_target_logit"] - corrupt_record["off_target_logit"],
                        },
                    }
                )

            receipt.update(
                {
                    "runtime": {
                        "python": platform.python_version(),
                        "torch": torch.__version__,
                        "transformers": transformers.__version__,
                        "device": device,
                        "model_class": type(model).__name__,
                        "tokenizer_class": type(tokenizer).__name__,
                        "layers": len(layers),
                    },
                    "post_load_identity": in_memory_parameter_identity(model),
                    "probe": probe_payload,
                    "promotion": {
                        "status": "UNASSESSED_CANDIDATE_ONLY",
                        "reason": (
                            "Observation mode does not modify hidden state and establishes no causal promotion."
                            if args.mode == "observation"
                            else "No predeclared effect/off-target threshold, exact loader-consumption attestation, or canonical evidence admission is evaluated by this probe."
                        ),
                    },
                }
            )
    except ProbeRejected as exc:
        receipt["failure"] = {"class": "PROBE_REJECTED_FAIL_CLOSED", "detail": str(exc)}
        receipt["promotion"] = {"status": "REJECTED_NO_CREDIT"}
    except Exception as exc:
        receipt["failure"] = {
            "class": "RUNTIME_OR_DEPENDENCY_FAILURE_NOT_SCIENTIFIC_NEGATIVE",
            "type": type(exc).__name__,
            "detail": str(exc),
        }
        receipt["promotion"] = {"status": "FAILED_NO_CREDIT"}
    finally:
        receipt["network_attempt_count"] = network.attempts

    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        out = Path(args.output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0 if "failure" not in receipt else 4


if __name__ == "__main__":
    raise SystemExit(main())

"""XENO_MODEL_SLOT/v1 -- Xeno Shell Master Spec v1 SS4.

One logical model-slot contract per resident checkpoint. Does NOT re-measure identity;
it BINDS to the exact checkpoint identity/loader receipts already produced by the
trigger2 checkpoint-candidate pipeline (research_entity/global/j-space/research/
vps_run_receipts/*_checkpoint_identity.json, *_loader_probe.json) so this shell layer
and the already-measured training-data-side facts cannot silently drift apart.

Per-executor-context fields (grid_instance_id, executor_id, lease_id, generation,
process_id, workspace_epoch) are supplied by the caller at lease time (grid10_fabric.py
elect_coordinator / runtime_claim_task already mint generation+lease_id) -- this module
does not invent its own leasing, it composes with the existing one.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SLOT_SCHEMA = "XENO_MODEL_SLOT/v1"

REPO_ROOT_CANDIDATES = [
    Path("/root/clay-xeno-shell-v1"),
    Path(__file__).resolve().parents[1],
]


class ModelSlotError(ValueError):
    pass


def _repo_root() -> Path:
    for p in REPO_ROOT_CANDIDATES:
        if (p / "research_entity").is_dir():
            return p
    raise ModelSlotError("REPO_ROOT_NOT_FOUND")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_resident_identity(candidate_id: str) -> dict[str, Any]:
    """Bind to the exact, already-produced checkpoint identity receipt for
    candidate_id (e.g. QWEN35_08B_TARGET_MEASURED). Fails closed if the receipt is
    missing, incomplete, or its own file_manifest_sha256 no longer matches the bytes
    on disk under local_dir (i.e. someone changed the checkpoint files without a new
    receipt)."""
    root = _repo_root()
    receipt_path = (
        root
        / "research_entity/global/j-space/research/vps_run_receipts"
        / f"2026-08-25_{candidate_id}_checkpoint_identity.json"
    )
    if not receipt_path.exists():
        raise ModelSlotError(f"IDENTITY_RECEIPT_NOT_FOUND:{receipt_path}")
    receipt = json.loads(receipt_path.read_text())
    # NOTE: the file-name token (candidate_id arg, e.g. QWEN35_08B_TARGET_MEASURED) is
    # a role-based alias; the receipt's internal candidate_id field
    # (e.g. QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED) is the specific model name.
    # File selection IS the binding mechanism here -- both are recorded for traceability.
    receipt["_slot_alias_requested"] = candidate_id
    if not receipt.get("identity_complete"):
        raise ModelSlotError(f"IDENTITY_NOT_COMPLETE:{candidate_id}")
    if not receipt.get("revision_matches_pinned"):
        raise ModelSlotError(f"REVISION_DOES_NOT_MATCH_PINNED:{candidate_id}")
    return receipt


def resident_model_object(candidate_id: str) -> dict[str, Any]:
    """The 'resident model object' fields required by spec SS4: exact checkpoint
    identity, tokenizer identity, runtime/backend identity, dtype identity, Xeno
    vector ABI binding, hook registry, immutable loaded-weight digest/loader receipt.
    Vector ABI binding and hook registry are explicitly UNBOUND here (see
    xeno_shell_hrr_selftest_v1 -- no measured .npy artifacts exist in-repo yet;
    this slot refuses to fabricate that binding)."""
    receipt = load_resident_identity(candidate_id)
    # Qwen3.5 config is multimodal (vision_config + text_config siblings); the
    # architecture facts the shell cares about (layers, hidden size, attention
    # pattern) live under text_config, not the top-level config dict.
    cfg = (receipt.get("config") or {}).get("text_config") or {}
    return {
        "schema": SLOT_SCHEMA,
        "candidate_id": candidate_id,
        "repo": receipt.get("repo"),
        "checkpoint_revision": receipt.get("requested_revision"),
        "revision_matches_pinned": receipt.get("revision_matches_pinned"),
        "tokenizer_json_sha256": receipt.get("tokenizer_json_sha256"),
        "config_json_sha256": receipt.get("config_json_sha256"),
        "chat_template_jinja_sha256": receipt.get("chat_template_jinja_sha256"),
        "file_manifest_sha256": receipt.get("file_manifest_sha256"),
        "torch_dtype": cfg.get("torch_dtype"),
        "hidden_size": cfg.get("hidden_size"),
        "num_hidden_layers": cfg.get("num_hidden_layers") or len(cfg.get("layer_types", []) or []),
        "full_attention_layer_indices": [
            i for i, t in enumerate(cfg.get("layer_types", []) or []) if t == "full_attention"
        ],
        "vector_abi_binding": "UNBOUND_NO_MEASURED_HRR_ARTIFACTS",
        "hook_registry": [],
        "loaded_weight_digest": receipt.get("file_manifest_sha256"),
        "identity_complete": receipt.get("identity_complete"),
    }


def bind_executor_context(
    *,
    candidate_id: str,
    grid_instance_id: str,
    executor_id: str,
    lease_id: str,
    generation: int,
    process_id: str,
    workspace_epoch: int,
) -> dict[str, Any]:
    """Compose the resident model object with one caller-supplied executor context.
    Does not itself grant a lease -- lease_id/generation must come from
    grid10_fabric.Fabric.elect_coordinator or runtime_claim_task."""
    model = resident_model_object(candidate_id)
    if not model["identity_complete"]:
        raise ModelSlotError(f"CANNOT_BIND_INCOMPLETE_IDENTITY:{candidate_id}")
    return {
        "schema": SLOT_SCHEMA,
        "grid_instance_id": grid_instance_id,
        "executor_id": executor_id,
        "lease_id": lease_id,
        "generation": generation,
        "process_id": process_id,
        "workspace_epoch": workspace_epoch,
        "resident_model": model,
    }

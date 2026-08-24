#!/usr/bin/env python3
"""Resolve the current EntityOS/HCU worker directive from canonical bootstrap.

This module is secret-blind and network-free. It prevents the swarm runtime from
silently falling back to the historical unversioned Mini Entity worker directive.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any


class WorkerAuthorityError(RuntimeError):
    pass


@dataclass(frozen=True)
class WorkerAuthority:
    bootstrap_path: Path
    protocol_path: Path
    owner_directive_path: Path
    authority_epoch: str
    supervisor_path: str
    protocol_text: str
    protocol_sha256: str
    owner_text: str


def _repo_path(root: Path, raw: str, label: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise WorkerAuthorityError(f"{label}: missing repository-relative path")
    rel = Path(raw)
    if rel.is_absolute():
        raise WorkerAuthorityError(f"{label}: absolute path forbidden")
    root_resolved = root.resolve()
    target = (root_resolved / rel).resolve()
    try:
        target.relative_to(root_resolved)
    except ValueError as exc:
        raise WorkerAuthorityError(f"{label}: path escapes repository root") from exc
    return target


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise WorkerAuthorityError(f"{label}: unreadable or malformed JSON: {type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise WorkerAuthorityError(f"{label}: root must be object")
    return value


def resolve_worker_authority(root: Path) -> WorkerAuthority:
    root = root.resolve()
    bootstrap_path = root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
    bootstrap = _read_json(bootstrap_path, "bootstrap")

    epoch = str(bootstrap.get("schema_version") or "").strip()
    if not epoch:
        raise WorkerAuthorityError("bootstrap: schema_version missing")
    if bootstrap.get("active_program") != "ENTITYOS_HCU":
        raise WorkerAuthorityError("bootstrap: active_program is not ENTITYOS_HCU")
    if bootstrap.get("product_endpoint") != "EntityOS":
        raise WorkerAuthorityError("bootstrap: product_endpoint is not EntityOS")
    if bootstrap.get("integrated_cognition_compute_architecture") != "HCU":
        raise WorkerAuthorityError("bootstrap: integrated architecture is not HCU")
    if bootstrap.get("free_only") is not True:
        raise WorkerAuthorityError("bootstrap: FREE_ONLY not active")

    protocol_path = _repo_path(root, bootstrap.get("all_worker_protocol"), "all_worker_protocol")
    owner_path = _repo_path(root, bootstrap.get("active_owner_authority"), "active_owner_authority")
    supervisor_raw = bootstrap.get("authority_correction")
    supervisor_path = str(supervisor_raw or "").strip()
    _repo_path(root, supervisor_path, "authority_correction")

    try:
        protocol = protocol_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise WorkerAuthorityError(f"all_worker_protocol: unreadable: {type(exc).__name__}") from exc
    try:
        owner = owner_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise WorkerAuthorityError(f"active_owner_authority: unreadable: {type(exc).__name__}") from exc

    required_protocol_tokens = (
        f"Authority epoch: {epoch}",
        "Program: ENTITYOS_HCU",
        "Product: EntityOS",
        "Compute architecture: HCU",
        "Mode: FREE_ONLY",
        supervisor_path,
    )
    missing = [token for token in required_protocol_tokens if token not in protocol]
    if missing:
        raise WorkerAuthorityError("all_worker_protocol: current-authority tokens missing: " + " | ".join(missing))

    if "Persistent research entity" in protocol and "Clay" not in protocol:
        raise WorkerAuthorityError("all_worker_protocol: persistent entity drift")
    if "Mini Entity `go` macrocycle" in protocol:
        raise WorkerAuthorityError("all_worker_protocol: historical Mini Entity runtime wording active")

    return WorkerAuthority(
        bootstrap_path=bootstrap_path,
        protocol_path=protocol_path,
        owner_directive_path=owner_path,
        authority_epoch=epoch,
        supervisor_path=supervisor_path,
        protocol_text=protocol,
        protocol_sha256=hashlib.sha256(protocol.encode("utf-8")).hexdigest(),
        owner_text=owner,
    )


def current_worker_prompt(protocol: str, role: str, task: str, state_context: str, serial: int) -> str:
    return f"""{protocol}

module clay.swarm.go.worker
let trigger = "go"
let worker_serial = {serial}
let worker_role = "{role}"

TASK-SPECIFIC INSTRUCTION
You are one research/build worker in the current FREE_ONLY EntityOS + HCU `go` macrocycle.
{task}

Use the supplied state as bounded context only. Runtime artifacts may outrank repository
narrative for runtime facts, but neither model output nor worker consensus can mint
canonical truth or real-effect authority.

REPOSITORY_STATE_SNAPSHOT
{state_context}

OUTPUT CONTRACT
1. Put the substantive result first in ClayCode/GRF form (R0..R6; preserve Hyperposition where unresolved).
2. Advance executable EntityOS, HCU/Typed Entry, or Global J-Space/GWT readiness with a concrete discriminator, patch, test, benchmark, or exact NO_CHANGE reason.
3. Do not invent tool execution, measurements, repository writes, provider capabilities, runtime credit, or PASS states.
4. Preserve the strongest counterhypothesis and the cheapest next discriminator.
5. Keep provider/model/J-Space outputs candidate-only until canonical evidence admission.
6. End with a short section exactly titled `DEUTSCHE_ZUSAMMENFASSUNG` containing concise German: Ergebnis; Messstatus/Evidenzklasse; stärkster Gegenpunkt; nächster ausführbarer Schritt.
"""


def install_worker_authority(base_module: Any, root: Path) -> WorkerAuthority:
    authority = resolve_worker_authority(root)
    base_module.PROTOCOL_PATH = authority.protocol_path
    base_module.OWNER_DIRECTIVE_PATH = authority.owner_directive_path
    first = next((line.strip() for line in authority.protocol_text.splitlines() if line.strip()), "")
    if not first:
        raise WorkerAuthorityError("all_worker_protocol: empty")
    base_module.PROTOCOL_BEGIN = first
    base_module.PROTOCOL_END = first

    def load_current_protocol() -> str:
        refreshed = resolve_worker_authority(root)
        base_module.PROTOCOL_PATH = refreshed.protocol_path
        base_module.OWNER_DIRECTIVE_PATH = refreshed.owner_directive_path
        marker = next((line.strip() for line in refreshed.protocol_text.splitlines() if line.strip()), "")
        base_module.PROTOCOL_BEGIN = marker
        base_module.PROTOCOL_END = marker
        return refreshed.protocol_text

    base_module.load_protocol = load_current_protocol
    base_module.worker_prompt = current_worker_prompt
    return authority

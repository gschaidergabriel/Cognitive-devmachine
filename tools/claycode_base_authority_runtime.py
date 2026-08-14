#!/usr/bin/env python3
"""Opaque host authority runtime candidate for ClayCode BASE.

The language may describe effects and capability references; execution authority remains
host-owned. A handle is accepted only when the exact live object instance is present in
the broker registry and its context binding is current. Serializable descriptors are
never bearer authority.

Candidate evidence only: this Python mechanism is not an OS sandbox and does not replace
APP-08 / Andreas Ubuntu authority-closure acceptance.
"""
from __future__ import annotations

import copy
import json
import random
import secrets
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any


class AuthorityDenied(RuntimeError):
    pass


@dataclass(frozen=True)
class EffectRequest:
    capability: str
    target: str
    operation: str
    origin: str
    basis_epoch: int
    selection_id: str
    closure_id: str
    value: int


class _CapabilityHandle:
    __slots__ = ("_runtime_id", "_handle_id", "_generation")

    def __init__(self, runtime_id: str, handle_id: str, generation: int):
        self._runtime_id = runtime_id
        self._handle_id = handle_id
        self._generation = generation

    def __copy__(self):
        # Deliberately produce a distinct object; registry identity will reject it.
        return _CapabilityHandle(self._runtime_id, self._handle_id, self._generation)

    def __deepcopy__(self, memo):
        return self.__copy__()


class HostAuthorityRuntime:
    def __init__(self):
        self._runtime_id = secrets.token_hex(16)
        self._generation = 1
        self._entries: dict[str, dict[str, Any]] = {}
        self.receipts: list[dict[str, Any]] = []

    @property
    def generation(self) -> int:
        return self._generation

    def issue(
        self,
        *,
        capability: str,
        target: str,
        operation: str,
        origin: str,
        basis_epoch: int,
        selection_id: str,
        closure_id: str,
        budget: int,
    ) -> _CapabilityHandle:
        if budget <= 0:
            raise ValueError("budget must be positive")
        hid = secrets.token_hex(16)
        handle = _CapabilityHandle(self._runtime_id, hid, self._generation)
        self._entries[hid] = {
            "handle": handle,
            "capability": capability,
            "target": target,
            "operation": operation,
            "origin": origin,
            "basis_epoch": int(basis_epoch),
            "selection_id": selection_id,
            "closure_id": closure_id,
            "remaining": int(budget),
            "revoked": False,
            "generation": self._generation,
        }
        return handle

    def descriptor(self, handle: _CapabilityHandle) -> dict[str, Any]:
        row = self._lookup_live(handle)
        return {
            "capability": row["capability"],
            "target": row["target"],
            "operation": row["operation"],
            "origin": row["origin"],
            "basis_epoch": row["basis_epoch"],
            "selection_id": row["selection_id"],
            "closure_id": row["closure_id"],
            "remaining": row["remaining"],
            "generation": row["generation"],
            "note": "DESCRIPTIVE_ONLY_NOT_BEARER_AUTHORITY",
        }

    def _lookup_live(self, handle: Any) -> dict[str, Any]:
        if not isinstance(handle, _CapabilityHandle):
            raise AuthorityDenied("NOT_OPAQUE_HANDLE")
        if handle._runtime_id != self._runtime_id:
            raise AuthorityDenied("FOREIGN_RUNTIME_HANDLE")
        row = self._entries.get(handle._handle_id)
        if row is None:
            raise AuthorityDenied("UNKNOWN_HANDLE")
        if row["handle"] is not handle:
            raise AuthorityDenied("COPIED_OR_FORGED_HANDLE")
        if handle._generation != self._generation or row["generation"] != self._generation:
            raise AuthorityDenied("STALE_RUNTIME_GENERATION")
        if row["revoked"]:
            raise AuthorityDenied("REVOKED")
        return row

    def revoke(self, handle: _CapabilityHandle) -> None:
        self._lookup_live(handle)["revoked"] = True

    def restart_epoch(self) -> None:
        # A restart/recovery boundary invalidates all bearer objects from the prior runtime.
        self._generation += 1
        self._entries = {}

    def authorize(self, handle: Any, request: EffectRequest) -> dict[str, Any]:
        row = self._lookup_live(handle)
        checks = {
            "capability": request.capability == row["capability"],
            "target": request.target == row["target"],
            "operation": request.operation == row["operation"],
            "origin": request.origin == row["origin"],
            "basis_epoch": request.basis_epoch == row["basis_epoch"],
            "selection_id": request.selection_id == row["selection_id"],
            "closure_id": request.closure_id == row["closure_id"],
            "budget": row["remaining"] > 0,
        }
        failed = [name for name, ok in checks.items() if not ok]
        if failed:
            raise AuthorityDenied("CONTEXT_MISMATCH:" + ",".join(failed))
        row["remaining"] -= 1
        receipt = {
            "capability": row["capability"],
            "target": row["target"],
            "operation": row["operation"],
            "origin": row["origin"],
            "basis_epoch": row["basis_epoch"],
            "selection_id": row["selection_id"],
            "closure_id": row["closure_id"],
            "runtime_generation": self._generation,
            "remaining": row["remaining"],
            "status": "AUTHORIZED",
        }
        self.receipts.append(receipt)
        return receipt


class AuthorityGateway:
    """Duck-typed effect gateway usable by the BASE effect interpreter/lowering."""
    def __init__(self, runtime: HostAuthorityRuntime, handles: dict[str, _CapabilityHandle], context: dict[str, Any]):
        self.runtime = runtime
        self.handles = dict(handles)
        self.context = dict(context)
        self.trace: list[list[Any]] = []

    def effect(self, effect: str, capability: str, value: int) -> int:
        if capability not in self.handles:
            raise AuthorityDenied("NO_HANDLE_FOR_CAPABILITY:" + capability)
        target = "effect://" + effect
        request = EffectRequest(
            capability=capability,
            target=target,
            operation=effect,
            origin=self.context["origin"],
            basis_epoch=self.context["basis_epoch"],
            selection_id=self.context["selection_id"],
            closure_id=self.context["closure_id"],
            value=value,
        )
        self.runtime.authorize(self.handles[capability], request)
        self.trace.append([effect, capability, value])
        if effect == "FS_READ": return value + 1000
        if effect == "FS_WRITE": return value
        if effect == "DB_WRITE": return value * 2
        if effect == "HTTP": return value + 7
        raise AuthorityDenied("UNSUPPORTED_EFFECT:" + effect)


def _issue(runtime: HostAuthorityRuntime, cap: str, effect: str, budget: int, context: dict[str, Any]):
    return runtime.issue(
        capability=cap,
        target="effect://" + effect,
        operation=effect,
        origin=context["origin"],
        basis_epoch=context["basis_epoch"],
        selection_id=context["selection_id"],
        closure_id=context["closure_id"],
        budget=budget,
    )


def self_test() -> dict[str, Any]:
    context = {"origin": "origin:trusted-fixture", "basis_epoch": 17, "selection_id": "sel:9", "closure_id": "closure:abc"}
    runtime = HostAuthorityRuntime()
    handle = _issue(runtime, "cap.fs.read", "FS_READ", 2, context)
    req = EffectRequest("cap.fs.read", "effect://FS_READ", "FS_READ", context["origin"], 17, context["selection_id"], context["closure_id"], 5)
    runtime.authorize(handle, req)
    runtime.authorize(handle, req)
    budget_rejected = False
    try:
        runtime.authorize(handle, req)
    except AuthorityDenied:
        budget_rejected = True

    runtime2 = HostAuthorityRuntime()
    h2 = _issue(runtime2, "cap.fs.read", "FS_READ", 10, context)
    descriptor = runtime2.descriptor(h2)
    structural_rejected = False
    try:
        runtime2.authorize(descriptor, req)
    except AuthorityDenied:
        structural_rejected = True
    copied_rejected = False
    try:
        runtime2.authorize(copy.copy(h2), req)
    except AuthorityDenied:
        copied_rejected = True
    forged_rejected = False
    try:
        fake = SimpleNamespace(_runtime_id=h2._runtime_id, _handle_id=h2._handle_id, _generation=h2._generation)
        runtime2.authorize(fake, req)
    except AuthorityDenied:
        forged_rejected = True

    rev = HostAuthorityRuntime()
    hr = _issue(rev, "cap.fs.read", "FS_READ", 10, context)
    rev.revoke(hr)
    revoked_rejected = False
    try:
        rev.authorize(hr, req)
    except AuthorityDenied:
        revoked_rejected = True

    restart = HostAuthorityRuntime()
    hs = _issue(restart, "cap.fs.read", "FS_READ", 10, context)
    restart.restart_epoch()
    stale_restart_rejected = False
    try:
        restart.authorize(hs, req)
    except AuthorityDenied:
        stale_restart_rejected = True

    mutation_runtime = HostAuthorityRuntime()
    hm = _issue(mutation_runtime, "cap.fs.read", "FS_READ", 20000, context)
    rng = random.Random(20260809)
    fields = ["capability", "target", "operation", "origin", "basis_epoch", "selection_id", "closure_id"]
    mutation_cases = 10000
    unauthorized_accepts = 0
    for i in range(mutation_cases):
        field = fields[i % len(fields)]
        data = {
            "capability": "cap.fs.read",
            "target": "effect://FS_READ",
            "operation": "FS_READ",
            "origin": context["origin"],
            "basis_epoch": context["basis_epoch"],
            "selection_id": context["selection_id"],
            "closure_id": context["closure_id"],
            "value": rng.randint(-1000, 1000),
        }
        if field == "basis_epoch": data[field] += 1
        else: data[field] = str(data[field]) + ":mut"
        try:
            mutation_runtime.authorize(hm, EffectRequest(**data))
            unauthorized_accepts += 1
        except AuthorityDenied:
            pass

    valid_runtime = HostAuthorityRuntime()
    hv = _issue(valid_runtime, "cap.fs.read", "FS_READ", 1000, context)
    valid_accepts = 0
    for i in range(1000):
        r = EffectRequest("cap.fs.read", "effect://FS_READ", "FS_READ", context["origin"], 17, context["selection_id"], context["closure_id"], i)
        valid_runtime.authorize(hv, r)
        valid_accepts += 1

    checks = {
        "budget_monotone_rejected": budget_rejected,
        "serialized_descriptor_rejected": structural_rejected,
        "copied_handle_rejected": copied_rejected,
        "structural_forgery_rejected": forged_rejected,
        "revoked_handle_rejected": revoked_rejected,
        "restart_stale_handle_rejected": stale_restart_rejected,
        "mutated_context_unauthorized_accepts_zero": unauthorized_accepts == 0,
        "valid_requests_preserved": valid_accepts == 1000,
    }
    if not all(checks.values()):
        raise AssertionError(checks)
    return {
        "schema_version": "1.0",
        "candidate": "claycode-base-authority-runtime-0.1",
        "pass": True,
        "checks": checks,
        "mutation_cases": mutation_cases,
        "unauthorized_accepts": unauthorized_accepts,
        "valid_accepts": valid_accepts,
        "counts_as_work_package_pass": False,
        "counts_as_target_acceptance": False,
        "scope_guard": "Python object-identity proxy for runtime authority invariants. Not an OS sandbox, foreign-process capability proof, or APP-08 target receipt.",
    }


def main() -> None:
    print(json.dumps(self_test(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

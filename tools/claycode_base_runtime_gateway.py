#!/usr/bin/env python3
"""ClayCode BASE Linux runtime capability/resource ABI candidate.

Implements an opaque host-rooted capability boundary, scoped file effects,
generation-bound resource handles, SQLite/process adapters, transactional effect
reserve/commit/rollback receipts, and versioned CAS identity.

Research/implementation candidate only. Local or GitHub-hosted execution is not the
Andreas Ubuntu target acceptance required by the BASE release gate.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class RuntimeFault(RuntimeError):
    pass


class CapabilityDenied(RuntimeFault):
    pass


class StaleResource(RuntimeFault):
    pass


class EffectStateError(RuntimeFault):
    pass


@dataclass(frozen=True)
class CapabilityHandle:
    _issuer: str
    _id: str
    kind: str
    scope: str
    generation: int


@dataclass(frozen=True)
class ResourceHandle:
    _issuer: str
    slot: int
    generation: int
    kind: str


@dataclass
class _Resource:
    kind: str
    generation: int
    value: Any
    live: bool = True


@dataclass
class _Effect:
    effect_id: str
    operation: str
    capability_id: str
    state: str
    input_hash: str
    output_hash: str | None = None


class VersionedCell:
    """Reference version-bound CAS cell; value equality is not resource identity."""

    def __init__(self, value: Any):
        self._value = value
        self._version = 0
        self._lock = threading.Lock()

    def read(self):
        with self._lock:
            return self._value, self._version

    def compare_exchange(self, expected_value, expected_version, new_value):
        with self._lock:
            if self._value != expected_value or self._version != expected_version:
                return False, (self._value, self._version)
            self._value = new_value
            self._version += 1
            return True, (self._value, self._version)


class RuntimeGateway:
    """Host-rooted capability/resource/effect ABI reference candidate.

    Capabilities are issuer-bound objects held by the runtime; serialized records or
    model-produced lookalikes never authorize effects. Resource handles are additionally
    generation-bound so slot reuse cannot make stale handles valid again.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._issuer = secrets.token_hex(16)
        self._caps: dict[str, CapabilityHandle] = {}
        self._cap_live: dict[str, bool] = {}
        self._resources: dict[int, _Resource] = {}
        self._slot_generation: dict[int, int] = {}
        self._next_slot = 0
        self._effects: dict[str, _Effect] = {}
        self.trace: list[dict[str, Any]] = []
        self._lock = threading.RLock()

    @staticmethod
    def _hash(obj: Any) -> str:
        payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()
        return hashlib.sha256(payload).hexdigest()

    def grant(self, kind: str, scope: str = "*") -> CapabilityHandle:
        with self._lock:
            hid = secrets.token_hex(16)
            handle = CapabilityHandle(self._issuer, hid, kind, scope, 0)
            self._caps[hid] = handle
            self._cap_live[hid] = True
            return handle

    def revoke(self, cap: CapabilityHandle) -> None:
        self._require_cap_object(cap)
        self._cap_live[cap._id] = False

    def _require_cap_object(
        self,
        cap: CapabilityHandle,
        kind: str | None = None,
        scope: str | None = None,
    ) -> CapabilityHandle:
        if not isinstance(cap, CapabilityHandle) or cap._issuer != self._issuer:
            raise CapabilityDenied("FOREIGN_OR_STRUCTURAL_CAPABILITY")
        original = self._caps.get(cap._id)
        if original is not cap or not self._cap_live.get(cap._id, False):
            raise CapabilityDenied("STALE_REVOKED_OR_COPIED_CAPABILITY")
        if kind is not None and cap.kind != kind:
            raise CapabilityDenied(f"CAPABILITY_KIND:{cap.kind}!={kind}")
        if scope is not None and cap.scope not in ("*", scope):
            raise CapabilityDenied(f"CAPABILITY_SCOPE:{cap.scope}!={scope}")
        return cap

    def _resolve_path(self, relative: str) -> Path:
        if os.path.isabs(relative):
            raise CapabilityDenied("ABSOLUTE_PATH_FORBIDDEN")
        path = (self.root / relative).resolve()
        try:
            path.relative_to(self.root)
        except ValueError as exc:
            raise CapabilityDenied("PATH_ESCAPE") from exc
        return path

    def reserve(
        self,
        operation: str,
        cap: CapabilityHandle,
        payload: Any,
        *,
        kind: str,
        scope: str = "*",
    ) -> str:
        self._require_cap_object(cap, kind, scope)
        effect_id = secrets.token_hex(16)
        self._effects[effect_id] = _Effect(
            effect_id,
            operation,
            cap._id,
            "RESERVED",
            self._hash(payload),
        )
        return effect_id

    def commit(self, effect_id: str, cap: CapabilityHandle, payload: Any, fn) -> Any:
        effect = self._effects.get(effect_id)
        if effect is None:
            raise EffectStateError("UNKNOWN_EFFECT")
        self._require_cap_object(cap)
        if effect.capability_id != cap._id:
            raise CapabilityDenied("EFFECT_CAPABILITY_MISMATCH")
        if effect.state != "RESERVED":
            raise EffectStateError(f"BAD_EFFECT_STATE:{effect.state}")
        if effect.input_hash != self._hash(payload):
            raise EffectStateError("EFFECT_INPUT_DRIFT")
        try:
            output = fn()
        except Exception:
            effect.state = "ROLLED_BACK"
            self.trace.append(
                {"effect_id": effect.effect_id, "operation": effect.operation, "state": effect.state}
            )
            raise
        effect.output_hash = self._hash(output)
        effect.state = "COMMITTED"
        self.trace.append(
            {
                "effect_id": effect.effect_id,
                "operation": effect.operation,
                "state": effect.state,
                "input_hash": effect.input_hash,
                "output_hash": effect.output_hash,
            }
        )
        return output

    def file_write_text(self, cap: CapabilityHandle, relative: str, text: str) -> int:
        path = self._resolve_path(relative)
        scope = "fs:" + str(path.parent.relative_to(self.root))
        effect_id = self.reserve(
            "file_write_text", cap, [relative, text], kind="fs.write", scope=scope
        )

        def operation():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            return len(text.encode())

        return self.commit(effect_id, cap, [relative, text], operation)

    def file_read_text(self, cap: CapabilityHandle, relative: str) -> str:
        path = self._resolve_path(relative)
        scope = "fs:" + str(path.parent.relative_to(self.root))
        effect_id = self.reserve("file_read_text", cap, [relative], kind="fs.read", scope=scope)
        return self.commit(effect_id, cap, [relative], lambda: path.read_text(encoding="utf-8"))

    def sqlite_open(self, cap: CapabilityHandle, relative: str) -> ResourceHandle:
        path = self._resolve_path(relative)
        scope = "db:" + str(path.relative_to(self.root))
        self._require_cap_object(cap, "db.open", scope)
        return self._allocate_resource("sqlite", sqlite3.connect(path))

    def sqlite_exec(
        self,
        cap: CapabilityHandle,
        handle: ResourceHandle,
        sql: str,
        params: tuple = (),
    ) -> list[tuple]:
        self._require_cap_object(cap, "db.exec")
        resource = self._resource(handle, "sqlite")
        payload = [handle.slot, handle.generation, sql, list(params)]
        effect_id = self.reserve("sqlite_exec", cap, payload, kind="db.exec")

        def operation():
            cursor = resource.value.execute(sql, params)
            rows = cursor.fetchall()
            resource.value.commit()
            return rows

        return self.commit(effect_id, cap, payload, operation)

    def process_run(self, cap: CapabilityHandle, argv: list[str]) -> dict[str, Any]:
        self._require_cap_object(cap, "process.run")
        if not argv:
            raise RuntimeFault("EMPTY_ARGV")
        effect_id = self.reserve("process_run", cap, argv, kind="process.run")

        def operation():
            process = subprocess.run(
                argv,
                cwd=self.root,
                text=True,
                capture_output=True,
                timeout=5,
                check=False,
            )
            return {
                "returncode": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
            }

        return self.commit(effect_id, cap, argv, operation)

    def _allocate_resource(self, kind: str, value: Any) -> ResourceHandle:
        with self._lock:
            free = next((slot for slot, resource in self._resources.items() if not resource.live), None)
            if free is None:
                slot = self._next_slot
                self._next_slot += 1
            else:
                slot = free
            generation = self._slot_generation.get(slot, -1) + 1
            self._slot_generation[slot] = generation
            self._resources[slot] = _Resource(kind, generation, value, True)
            return ResourceHandle(self._issuer, slot, generation, kind)

    def _resource(self, handle: ResourceHandle, kind: str | None = None) -> _Resource:
        if not isinstance(handle, ResourceHandle) or handle._issuer != self._issuer:
            raise StaleResource("FOREIGN_RESOURCE")
        resource = self._resources.get(handle.slot)
        if (
            resource is None
            or not resource.live
            or resource.generation != handle.generation
            or resource.kind != handle.kind
        ):
            raise StaleResource("STALE_RESOURCE")
        if kind and resource.kind != kind:
            raise StaleResource("RESOURCE_KIND")
        return resource

    def close(self, handle: ResourceHandle) -> None:
        resource = self._resource(handle)
        if hasattr(resource.value, "close"):
            resource.value.close()
        resource.live = False

    def receipt(self) -> dict[str, Any]:
        # Nonce/effect IDs belong to execution identity, not semantic outcome identity.
        semantic_trace = [{k: v for k, v in row.items() if k != "effect_id"} for row in self.trace]
        return {
            "trace": self.trace,
            "semantic_trace_hash": self._hash(semantic_trace),
            "execution_trace_hash": self._hash(self.trace),
        }

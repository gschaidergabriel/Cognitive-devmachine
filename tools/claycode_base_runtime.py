#!/usr/bin/env python3
"""ClayCode BASE Ubuntu host runtime candidate.

This module implements the external authority boundary for CC-WP-07/08/09.  It is
intentionally independent from model output: generated ClayCode may request an adapter,
but only a runtime-minted opaque capability handle authorizes host effects.

The implementation is conservative and stdlib-only so it can run unchanged on the
Ubuntu developer host and in hosted Ubuntu CI.  Hosted CI receipts are proxy evidence;
target-host promotion still requires the Andreas-PC receipt defined by the BASE gate.
"""
from __future__ import annotations

import concurrent.futures
import dataclasses
import hashlib
import json
import os
import secrets
import sqlite3
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Iterable

RUNTIME_VERSION = "claycode-base-runtime/0.1"
_CONSTRUCTOR_KEY = object()


class RuntimeFault(RuntimeError):
    """Base fail-closed runtime error."""


class CapabilityFault(RuntimeFault):
    pass


class ResourceFault(RuntimeFault):
    pass


class CASFault(RuntimeFault):
    pass


@dataclasses.dataclass(frozen=True)
class _CapabilityHandle:
    runtime_id: str
    capability_id: str
    kind: str
    epoch: int
    nonce: bytes = dataclasses.field(repr=False)
    _key: object = dataclasses.field(repr=False, compare=False, default=None)

    def __post_init__(self) -> None:
        if self._key is not _CONSTRUCTOR_KEY:
            raise CapabilityFault("CAPABILITY_HANDLE_NOT_RUNTIME_MINTED")

    def __reduce__(self):
        raise CapabilityFault("CAPABILITY_HANDLE_NOT_SERIALIZABLE")


@dataclasses.dataclass(frozen=True)
class ResourceRef:
    runtime_id: str
    resource_id: str
    kind: str
    generation: int


@dataclasses.dataclass(frozen=True)
class AdapterSpec:
    name: str
    capability_kind: str
    function: Callable[..., Any]


@dataclasses.dataclass
class VersionedCell:
    """Generation-tagged CAS cell; generation changes on every successful write.

    This deliberately makes A->B->A distinguishable and prevents an ABA-stale CAS from
    succeeding merely because the payload returned to an earlier value.
    """

    value: Any
    version: int = 0
    _lock: threading.Lock = dataclasses.field(default_factory=threading.Lock, repr=False)

    def snapshot(self) -> tuple[int, Any]:
        with self._lock:
            return self.version, self.value

    def compare_and_swap(self, expected_version: int, new_value: Any) -> tuple[bool, int, Any]:
        with self._lock:
            if self.version != expected_version:
                return False, self.version, self.value
            self.version += 1
            self.value = new_value
            return True, self.version, self.value


class ClayRuntime:
    def __init__(self, sandbox_root: str | os.PathLike[str]):
        self.runtime_id = uuid.uuid4().hex
        self._issuer_secret = secrets.token_bytes(32)
        self._epoch = 1
        self._sandbox_root = Path(sandbox_root).resolve()
        self._sandbox_root.mkdir(parents=True, exist_ok=True)
        self._capabilities: dict[str, _CapabilityHandle] = {}
        self._revoked: set[str] = set()
        self._resources: dict[str, ResourceRef] = {}
        self._resource_generation = 0
        self._adapters: dict[str, AdapterSpec] = {}
        self._trace_lock = threading.Lock()
        self._trace_seq = 0
        self._traces: list[dict[str, Any]] = []
        self._register_stdlib_adapters()

    @property
    def epoch(self) -> int:
        return self._epoch

    def rotate_epoch(self) -> int:
        """Invalidate every capability minted in an earlier authority epoch."""
        self._epoch += 1
        return self._epoch

    def mint_capability(self, kind: str) -> _CapabilityHandle:
        if kind not in {spec.capability_kind for spec in self._adapters.values()}:
            raise CapabilityFault(f"UNKNOWN_CAPABILITY_KIND:{kind}")
        cid = uuid.uuid4().hex
        nonce = hashlib.sha256(
            self._issuer_secret + self.runtime_id.encode() + cid.encode() + kind.encode() + str(self._epoch).encode()
        ).digest()
        handle = _CapabilityHandle(self.runtime_id, cid, kind, self._epoch, nonce, _CONSTRUCTOR_KEY)
        self._capabilities[cid] = handle
        return handle

    def revoke(self, handle: _CapabilityHandle) -> None:
        self._validate_handle(handle, expected_kind=None)
        self._revoked.add(handle.capability_id)

    def _validate_handle(self, handle: Any, expected_kind: str | None) -> _CapabilityHandle:
        if not isinstance(handle, _CapabilityHandle):
            raise CapabilityFault("CAPABILITY_TYPE_INVALID")
        if handle.runtime_id != self.runtime_id:
            raise CapabilityFault("CAPABILITY_WRONG_RUNTIME")
        registered = self._capabilities.get(handle.capability_id)
        if registered is None or registered is not handle:
            raise CapabilityFault("CAPABILITY_NOT_REGISTERED_IDENTITY")
        if handle.capability_id in self._revoked:
            raise CapabilityFault("CAPABILITY_REVOKED")
        if handle.epoch != self._epoch:
            raise CapabilityFault("CAPABILITY_STALE_EPOCH")
        expected_nonce = hashlib.sha256(
            self._issuer_secret
            + self.runtime_id.encode()
            + handle.capability_id.encode()
            + handle.kind.encode()
            + str(handle.epoch).encode()
        ).digest()
        if not secrets.compare_digest(expected_nonce, handle.nonce):
            raise CapabilityFault("CAPABILITY_NONCE_INVALID")
        if expected_kind is not None and handle.kind != expected_kind:
            raise CapabilityFault(f"CAPABILITY_KIND_MISMATCH:{handle.kind}!={expected_kind}")
        return handle

    def _safe_path(self, relative: str | os.PathLike[str]) -> Path:
        path = (self._sandbox_root / Path(relative)).resolve()
        try:
            path.relative_to(self._sandbox_root)
        except ValueError as exc:
            raise ResourceFault("SANDBOX_PATH_ESCAPE") from exc
        return path

    def _new_resource(self, kind: str) -> ResourceRef:
        self._resource_generation += 1
        ref = ResourceRef(self.runtime_id, uuid.uuid4().hex, kind, self._resource_generation)
        self._resources[ref.resource_id] = ref
        return ref

    def register_adapter(self, name: str, capability_kind: str, function: Callable[..., Any]) -> None:
        if name in self._adapters:
            raise RuntimeFault(f"DUPLICATE_ADAPTER:{name}")
        self._adapters[name] = AdapterSpec(name, capability_kind, function)

    def invoke(self, name: str, capability: Any, *args: Any, **kwargs: Any) -> Any:
        spec = self._adapters.get(name)
        if spec is None:
            raise RuntimeFault(f"UNKNOWN_ADAPTER:{name}")
        handle = self._validate_handle(capability, spec.capability_kind)
        started_ns = time.monotonic_ns()
        try:
            result = spec.function(*args, **kwargs)
            self._record_trace(name, handle, "PASS", started_ns, None)
            return result
        except Exception as exc:
            self._record_trace(name, handle, "FAULT", started_ns, type(exc).__name__)
            raise

    def _record_trace(self, name: str, handle: _CapabilityHandle, status: str, started_ns: int, error: str | None) -> None:
        with self._trace_lock:
            self._trace_seq += 1
            self._traces.append(
                {
                    "seq": self._trace_seq,
                    "adapter": name,
                    "capability_kind": handle.kind,
                    "capability_ref": hashlib.sha256(handle.capability_id.encode()).hexdigest()[:16],
                    "status": status,
                    "duration_ns": max(0, time.monotonic_ns() - started_ns),
                    "error": error,
                }
            )

    def trace_receipt(self) -> list[dict[str, Any]]:
        """Return public trace fields only; no capability nonce/issuer secret is exposed."""
        with self._trace_lock:
            return json.loads(json.dumps(self._traces))

    # ----- stdlib adapters -----
    def _register_stdlib_adapters(self) -> None:
        self.register_adapter("fs.write_text", "fs.write", self._fs_write_text)
        self.register_adapter("fs.read_text", "fs.read", self._fs_read_text)
        self.register_adapter("db.sqlite_transaction", "db.sqlite", self._sqlite_transaction)
        self.register_adapter("process.exec", "process.exec", self._process_exec)
        self.register_adapter("numerical.dot", "numerical.cpu", self._dot)
        self.register_adapter("async.map", "async.compute", self._async_map)

    def _fs_write_text(self, relative: str, text: str) -> dict[str, Any]:
        path = self._safe_path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        ref = self._new_resource("file")
        return {
            "resource": dataclasses.asdict(ref),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "bytes": len(text.encode("utf-8")),
        }

    def _fs_read_text(self, relative: str) -> dict[str, Any]:
        path = self._safe_path(relative)
        text = path.read_text(encoding="utf-8")
        return {"text": text, "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}

    def _sqlite_transaction(self, relative: str, statements: Iterable[tuple[str, tuple[Any, ...]]]) -> dict[str, Any]:
        path = self._safe_path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        rows: list[list[tuple[Any, ...]]] = []
        try:
            conn.execute("BEGIN IMMEDIATE")
            for sql, params in statements:
                cur = conn.execute(sql, tuple(params))
                rows.append(cur.fetchall() if cur.description else [])
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        ref = self._new_resource("sqlite")
        return {"resource": dataclasses.asdict(ref), "rows": rows}

    def _process_exec(self, argv: list[str], allowed_programs: Iterable[str]) -> dict[str, Any]:
        if not argv:
            raise ResourceFault("EMPTY_ARGV")
        allow = set(allowed_programs)
        program = Path(argv[0]).name
        if program not in allow:
            raise CapabilityFault(f"PROCESS_NOT_ALLOWLISTED:{program}")
        cp = subprocess.run(argv, cwd=self._sandbox_root, text=True, capture_output=True, timeout=10, check=False)
        return {
            "returncode": cp.returncode,
            "stdout": cp.stdout,
            "stderr": cp.stderr,
        }

    @staticmethod
    def _dot(left: list[float], right: list[float]) -> float:
        if len(left) != len(right):
            raise ResourceFault("DOT_LENGTH_MISMATCH")
        return float(sum(float(a) * float(b) for a, b in zip(left, right)))

    @staticmethod
    def _async_map(function: Callable[[Any], Any], values: list[Any], max_workers: int = 4) -> list[dict[str, Any]]:
        if max_workers < 1 or max_workers > 64:
            raise ResourceFault("BAD_WORKER_COUNT")
        indexed = list(enumerate(values))
        out: list[dict[str, Any]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(function, value): index for index, value in indexed}
            for future in concurrent.futures.as_completed(futures):
                index = futures[future]
                out.append({"index": index, "value": future.result()})
        # publication order is deterministic even though execution order is not.
        out.sort(key=lambda item: item["index"])
        return out


__all__ = [
    "ClayRuntime",
    "VersionedCell",
    "ResourceRef",
    "RuntimeFault",
    "CapabilityFault",
    "ResourceFault",
    "CASFault",
    "RUNTIME_VERSION",
]

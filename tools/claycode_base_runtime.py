#!/usr/bin/env python3
"""ClayCode BASE Ubuntu host runtime candidate.

Authority boundary for CC-WP-07/08/09. Generated/model-authored code may request an
effect, but only a runtime-minted opaque capability whose policy was fixed at mint time
can authorize it. Caller-supplied strings, allowlists, callables or descriptors never
become authority.

Hosted Ubuntu execution is proxy evidence; target-host promotion still requires the
Andreas Ubuntu developer-system receipt defined by the BASE gate.
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
from typing import Any, Callable, Iterable, Mapping

RUNTIME_VERSION = "claycode-base-runtime/0.2"
_CONSTRUCTOR_KEY = object()

class RuntimeFault(RuntimeError): pass
class CapabilityFault(RuntimeFault): pass
class ResourceFault(RuntimeFault): pass
class CASFault(RuntimeFault): pass

@dataclasses.dataclass(frozen=True)
class _CapabilityHandle:
    runtime_id: str
    capability_id: str
    kind: str
    epoch: int
    policy_hash: str
    nonce: bytes = dataclasses.field(repr=False)
    _key: object = dataclasses.field(repr=False, compare=False, default=None)
    def __post_init__(self):
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
    value: Any
    version: int = 0
    _lock: threading.Lock = dataclasses.field(default_factory=threading.Lock, repr=False)
    def snapshot(self):
        with self._lock: return self.version, self.value
    def compare_and_swap(self, expected_version: int, new_value: Any):
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
        self._policies: dict[str, dict[str, Any]] = {}
        self._revoked: set[str] = set()
        self._resources: dict[str, ResourceRef] = {}
        self._resource_generation = 0
        self._adapters: dict[str, AdapterSpec] = {}
        self._trace_lock = threading.Lock()
        self._trace_seq = 0
        self._traces: list[dict[str, Any]] = []
        self._register_stdlib_adapters()

    @property
    def epoch(self): return self._epoch

    def rotate_epoch(self):
        self._epoch += 1
        return self._epoch

    @staticmethod
    def _canonical_policy(policy: Mapping[str, Any] | None) -> tuple[dict[str, Any], str]:
        raw = dict(policy or {})
        try:
            encoded = json.dumps(raw, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
            normalized = json.loads(encoded)
        except Exception as exc:
            raise CapabilityFault("CAPABILITY_POLICY_NOT_CANONICAL_JSON") from exc
        return normalized, hashlib.sha256(encoded).hexdigest()

    def mint_capability(self, kind: str, policy: Mapping[str, Any] | None = None) -> _CapabilityHandle:
        if kind not in {x.capability_kind for x in self._adapters.values()}:
            raise CapabilityFault(f"UNKNOWN_CAPABILITY_KIND:{kind}")
        normalized, ph = self._canonical_policy(policy)
        self._validate_policy(kind, normalized)
        cid = uuid.uuid4().hex
        nonce = hashlib.sha256(self._issuer_secret + self.runtime_id.encode() + cid.encode() + kind.encode() + str(self._epoch).encode() + ph.encode()).digest()
        handle = _CapabilityHandle(self.runtime_id, cid, kind, self._epoch, ph, nonce, _CONSTRUCTOR_KEY)
        self._capabilities[cid] = handle
        self._policies[cid] = normalized
        return handle

    @staticmethod
    def _validate_policy(kind: str, policy: dict[str, Any]) -> None:
        if kind == "process.exec":
            programs = policy.get("programs")
            if not isinstance(programs, list) or not programs or not all(isinstance(x, str) and x and "/" not in x for x in programs):
                raise CapabilityFault("PROCESS_POLICY_REQUIRES_BASENAME_ALLOWLIST")
        elif kind == "async.compute":
            ops = policy.get("operations", ["identity", "square", "negate"])
            if not isinstance(ops, list) or any(x not in {"identity", "square", "negate"} for x in ops):
                raise CapabilityFault("ASYNC_POLICY_BAD_OPERATION")
        elif kind == "numerical.cpu":
            n = policy.get("max_vector", 1000000)
            if not isinstance(n, int) or n < 1 or n > 10000000:
                raise CapabilityFault("NUMERICAL_POLICY_BAD_LIMIT")
        elif kind in {"fs.read", "fs.write", "db.sqlite"}:
            prefix = policy.get("prefix", "")
            if not isinstance(prefix, str) or Path(prefix).is_absolute() or ".." in Path(prefix).parts:
                raise CapabilityFault("PATH_POLICY_BAD_PREFIX")

    def capability_descriptor(self, handle: _CapabilityHandle) -> dict[str, Any]:
        h, policy = self._validated(handle, None)
        return {"runtime_id": h.runtime_id, "capability_ref": hashlib.sha256(h.capability_id.encode()).hexdigest()[:16], "kind": h.kind, "epoch": h.epoch, "policy": json.loads(json.dumps(policy)), "authorizing": False}

    def revoke(self, handle: _CapabilityHandle):
        h, _ = self._validated(handle, None)
        self._revoked.add(h.capability_id)

    def _validated(self, handle: Any, expected_kind: str | None):
        if not isinstance(handle, _CapabilityHandle): raise CapabilityFault("CAPABILITY_TYPE_INVALID")
        if handle.runtime_id != self.runtime_id: raise CapabilityFault("CAPABILITY_WRONG_RUNTIME")
        registered = self._capabilities.get(handle.capability_id)
        if registered is None or registered is not handle: raise CapabilityFault("CAPABILITY_NOT_REGISTERED_IDENTITY")
        if handle.capability_id in self._revoked: raise CapabilityFault("CAPABILITY_REVOKED")
        if handle.epoch != self._epoch: raise CapabilityFault("CAPABILITY_STALE_EPOCH")
        policy = self._policies.get(handle.capability_id)
        if policy is None: raise CapabilityFault("CAPABILITY_POLICY_MISSING")
        _, ph = self._canonical_policy(policy)
        if ph != handle.policy_hash: raise CapabilityFault("CAPABILITY_POLICY_HASH_MISMATCH")
        expected_nonce = hashlib.sha256(self._issuer_secret + self.runtime_id.encode() + handle.capability_id.encode() + handle.kind.encode() + str(handle.epoch).encode() + ph.encode()).digest()
        if not secrets.compare_digest(expected_nonce, handle.nonce): raise CapabilityFault("CAPABILITY_NONCE_INVALID")
        if expected_kind is not None and handle.kind != expected_kind: raise CapabilityFault(f"CAPABILITY_KIND_MISMATCH:{handle.kind}!={expected_kind}")
        return handle, json.loads(json.dumps(policy))

    def _safe_path(self, relative: str | os.PathLike[str], policy: dict[str, Any]):
        prefix = Path(policy.get("prefix", ""))
        base = (self._sandbox_root / prefix).resolve()
        path = (base / Path(relative)).resolve()
        try: path.relative_to(base)
        except ValueError as exc: raise ResourceFault("SANDBOX_PATH_ESCAPE") from exc
        return path

    def _new_resource(self, kind: str):
        self._resource_generation += 1
        ref = ResourceRef(self.runtime_id, uuid.uuid4().hex, kind, self._resource_generation)
        self._resources[ref.resource_id] = ref
        return ref

    def register_adapter(self, name: str, capability_kind: str, function: Callable[..., Any]):
        if name in self._adapters: raise RuntimeFault(f"DUPLICATE_ADAPTER:{name}")
        self._adapters[name] = AdapterSpec(name, capability_kind, function)

    def invoke(self, name: str, capability: Any, *args: Any, **kwargs: Any):
        spec = self._adapters.get(name)
        if spec is None: raise RuntimeFault(f"UNKNOWN_ADAPTER:{name}")
        handle, policy = self._validated(capability, spec.capability_kind)
        started_ns = time.monotonic_ns()
        try:
            result = spec.function(policy, *args, **kwargs)
            self._record_trace(name, handle, "PASS", started_ns, None)
            return result
        except Exception as exc:
            self._record_trace(name, handle, "FAULT", started_ns, type(exc).__name__)
            raise

    def _record_trace(self, name, handle, status, started_ns, error):
        with self._trace_lock:
            self._trace_seq += 1
            self._traces.append({"seq": self._trace_seq, "adapter": name, "capability_kind": handle.kind, "capability_ref": hashlib.sha256(handle.capability_id.encode()).hexdigest()[:16], "policy_hash": handle.policy_hash[:16], "status": status, "duration_ns": max(0, time.monotonic_ns()-started_ns), "error": error})

    def trace_receipt(self):
        with self._trace_lock: return json.loads(json.dumps(self._traces))

    def _register_stdlib_adapters(self):
        self.register_adapter("fs.write_text", "fs.write", self._fs_write_text)
        self.register_adapter("fs.read_text", "fs.read", self._fs_read_text)
        self.register_adapter("db.sqlite_transaction", "db.sqlite", self._sqlite_transaction)
        self.register_adapter("process.exec", "process.exec", self._process_exec)
        self.register_adapter("numerical.dot", "numerical.cpu", self._dot)
        self.register_adapter("async.map", "async.compute", self._async_map)

    def _fs_write_text(self, policy, relative: str, text: str):
        path = self._safe_path(relative, policy)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        ref = self._new_resource("file")
        return {"resource": dataclasses.asdict(ref), "sha256": hashlib.sha256(text.encode()).hexdigest(), "bytes": len(text.encode())}

    def _fs_read_text(self, policy, relative: str):
        text = self._safe_path(relative, policy).read_text(encoding="utf-8")
        return {"text": text, "sha256": hashlib.sha256(text.encode()).hexdigest()}

    def _sqlite_transaction(self, policy, relative: str, statements: Iterable[tuple[str, tuple[Any, ...]]]):
        path = self._safe_path(relative, policy)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path); rows=[]
        try:
            conn.execute("BEGIN IMMEDIATE")
            for sql, params in statements:
                cur=conn.execute(sql, tuple(params)); rows.append(cur.fetchall() if cur.description else [])
            conn.commit()
        except Exception:
            conn.rollback(); raise
        finally: conn.close()
        return {"resource": dataclasses.asdict(self._new_resource("sqlite")), "rows": rows}

    def _process_exec(self, policy, argv: list[str]):
        if not argv: raise ResourceFault("EMPTY_ARGV")
        program=Path(argv[0]).name
        if program not in set(policy["programs"]): raise CapabilityFault(f"PROCESS_NOT_ALLOWLISTED:{program}")
        cp=subprocess.run(argv,cwd=self._sandbox_root,text=True,capture_output=True,timeout=10,check=False)
        return {"returncode":cp.returncode,"stdout":cp.stdout,"stderr":cp.stderr}

    @staticmethod
    def _dot(policy, left: list[float], right: list[float]):
        if len(left)!=len(right): raise ResourceFault("DOT_LENGTH_MISMATCH")
        if len(left)>int(policy.get("max_vector",1000000)): raise ResourceFault("DOT_RESOURCE_LIMIT")
        return float(sum(float(a)*float(b) for a,b in zip(left,right)))

    @staticmethod
    def _async_map(policy, operation: str, values: list[Any], max_workers: int=4):
        allowed=set(policy.get("operations",["identity","square","negate"]))
        if operation not in allowed: raise CapabilityFault(f"ASYNC_OPERATION_NOT_ALLOWED:{operation}")
        if max_workers<1 or max_workers>64: raise ResourceFault("BAD_WORKER_COUNT")
        funcs={"identity":lambda x:x,"square":lambda x:x*x,"negate":lambda x:-x}
        function=funcs[operation]
        out=[]
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures={pool.submit(function,v):i for i,v in enumerate(values)}
            for future in concurrent.futures.as_completed(futures): out.append({"index":futures[future],"value":future.result()})
        out.sort(key=lambda x:x["index"])
        return out

__all__=["ClayRuntime","VersionedCell","ResourceRef","RuntimeFault","CapabilityFault","ResourceFault","CASFault","RUNTIME_VERSION"]

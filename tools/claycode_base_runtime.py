#!/usr/bin/env python3
"""ClayCode BASE Ubuntu host runtime candidate.

Authority boundary for CC-WP-07/08/09. Generated/model-authored code may request an
effect, but only a runtime-minted opaque capability whose policy and optional causal
authority context were fixed at mint time can authorize it. Caller-supplied strings,
allowlists, callables, descriptors or model output never become authority.

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
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

RUNTIME_VERSION = "claycode-base-runtime/0.4"
_CONSTRUCTOR_KEY = object()
_ZERO_CONTEXT_HASH = hashlib.sha256(b"{}").hexdigest()

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
    context_hash: str
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

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class ClayRuntime:
    def __init__(self, sandbox_root: str | os.PathLike[str]):
        self.runtime_id = uuid.uuid4().hex
        self._issuer_secret = secrets.token_bytes(32)
        self._epoch = 1
        self._sandbox_root = Path(sandbox_root).resolve()
        self._sandbox_root.mkdir(parents=True, exist_ok=True)
        self._capabilities: dict[str, _CapabilityHandle] = {}
        self._policies: dict[str, dict[str, Any]] = {}
        self._contexts: dict[str, dict[str, Any]] = {}
        self._usage: dict[str, dict[str, int]] = {}
        self._usage_lock = threading.Lock()
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
    def _canonical_mapping(value: Mapping[str, Any] | None, error: str) -> tuple[dict[str, Any], str]:
        raw = dict(value or {})
        try:
            encoded = json.dumps(raw, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
            normalized = json.loads(encoded)
        except Exception as exc:
            raise CapabilityFault(error) from exc
        return normalized, hashlib.sha256(encoded).hexdigest()

    @classmethod
    def _canonical_policy(cls, policy: Mapping[str, Any] | None) -> tuple[dict[str, Any], str]:
        return cls._canonical_mapping(policy, "CAPABILITY_POLICY_NOT_CANONICAL_JSON")

    @classmethod
    def _canonical_context(cls, context: Mapping[str, Any] | None) -> tuple[dict[str, Any], str]:
        return cls._canonical_mapping(context, "AUTHORITY_CONTEXT_NOT_CANONICAL_JSON")

    @staticmethod
    def _sha256_fd(fd: int) -> str:
        h = hashlib.sha256()
        pos = os.lseek(fd, 0, os.SEEK_CUR)
        os.lseek(fd, 0, os.SEEK_SET)
        try:
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk: break
                h.update(chunk)
        finally:
            os.lseek(fd, pos, os.SEEK_SET)
        return h.hexdigest()

    @classmethod
    def _fingerprint_path(cls, path: Path) -> dict[str, Any]:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0))
        try:
            st = os.fstat(fd)
            return {"sha256": cls._sha256_fd(fd), "size": st.st_size, "mode": st.st_mode, "dev": st.st_dev, "ino": st.st_ino}
        finally:
            os.close(fd)

    @classmethod
    def _normalize_process_programs(cls, policy: Mapping[str, Any] | None) -> dict[str, Any]:
        raw = dict(policy or {})
        programs = raw.get("programs")
        if not isinstance(programs, list) or not programs:
            raise CapabilityFault("PROCESS_POLICY_REQUIRES_ABSOLUTE_EXECUTABLE_ALLOWLIST")
        canonical: list[str] = []
        fingerprints: dict[str, dict[str, Any]] = {}
        for entry in programs:
            if not isinstance(entry, str) or not entry:
                raise CapabilityFault("PROCESS_POLICY_REQUIRES_ABSOLUTE_EXECUTABLE_ALLOWLIST")
            supplied = Path(entry)
            if not supplied.is_absolute():
                raise CapabilityFault("PROCESS_POLICY_REQUIRES_ABSOLUTE_EXECUTABLE_ALLOWLIST")
            try:
                resolved = supplied.resolve(strict=True)
            except OSError as exc:
                raise CapabilityFault(f"PROCESS_POLICY_EXECUTABLE_MISSING:{entry}") from exc
            if not resolved.is_file() or not os.access(resolved, os.X_OK):
                raise CapabilityFault(f"PROCESS_POLICY_NOT_EXECUTABLE:{resolved}")
            r = str(resolved)
            canonical.append(r)
            fingerprints[r] = cls._fingerprint_path(resolved)
        raw["programs"] = sorted(set(canonical))
        raw["program_fingerprints"] = {k: fingerprints[k] for k in sorted(fingerprints)}
        raw.setdefault("child_capability_propagation", "NONE")
        return raw

    @staticmethod
    def _normalize_http_policy(policy: Mapping[str, Any] | None) -> dict[str, Any]:
        raw = dict(policy or {})
        origins = raw.get("origins")
        if not isinstance(origins, list) or not origins:
            raise CapabilityFault("HTTP_POLICY_REQUIRES_ORIGINS")
        normalized=[]
        for origin in origins:
            if not isinstance(origin,str): raise CapabilityFault("HTTP_POLICY_BAD_ORIGIN")
            u=urllib.parse.urlsplit(origin)
            if u.scheme not in {"http","https"} or not u.hostname or u.path not in {"","/"} or u.query or u.fragment:
                raise CapabilityFault("HTTP_POLICY_BAD_ORIGIN")
            port=u.port or (443 if u.scheme=="https" else 80)
            normalized.append(f"{u.scheme}://{u.hostname.lower()}:{port}")
        raw["origins"]=sorted(set(normalized))
        raw.setdefault("max_response_bytes", 1024 * 1024)
        return raw

    def mint_capability(self, kind: str, policy: Mapping[str, Any] | None = None, authority_context: Mapping[str, Any] | None = None) -> _CapabilityHandle:
        if kind not in {x.capability_kind for x in self._adapters.values()}:
            raise CapabilityFault(f"UNKNOWN_CAPABILITY_KIND:{kind}")
        if kind == "process.exec": policy = self._normalize_process_programs(policy)
        if kind == "net.http_get": policy = self._normalize_http_policy(policy)
        normalized, ph = self._canonical_policy(policy)
        context, ch = self._canonical_context(authority_context)
        self._validate_policy(kind, normalized)
        if normalized.get("require_context"):
            self._validate_required_context(context)
        cid = uuid.uuid4().hex
        nonce = hashlib.sha256(self._issuer_secret + self.runtime_id.encode() + cid.encode() + kind.encode() + str(self._epoch).encode() + ph.encode() + ch.encode()).digest()
        handle = _CapabilityHandle(self.runtime_id, cid, kind, self._epoch, ph, ch, nonce, _CONSTRUCTOR_KEY)
        self._capabilities[cid] = handle
        self._policies[cid] = normalized
        self._contexts[cid] = context
        self._usage[cid] = {"calls": 0, "units": 0}
        return handle

    @staticmethod
    def _validate_required_context(context: dict[str, Any]) -> None:
        required=("origin_hash","basis_hash","selection_hash","closure_hash")
        for key in required:
            value=context.get(key)
            if not isinstance(value,str) or len(value)!=64:
                raise CapabilityFault(f"AUTHORITY_CONTEXT_MISSING_OR_BAD:{key}")
            try: int(value,16)
            except ValueError as exc: raise CapabilityFault(f"AUTHORITY_CONTEXT_MISSING_OR_BAD:{key}") from exc

    @staticmethod
    def _validate_policy(kind: str, policy: dict[str, Any]) -> None:
        for key in ("max_calls","max_units"):
            if key in policy and (not isinstance(policy[key],int) or policy[key] < 1):
                raise CapabilityFault(f"CAPABILITY_POLICY_BAD_{key.upper()}")
        if "require_context" in policy and not isinstance(policy["require_context"], bool):
            raise CapabilityFault("CAPABILITY_POLICY_BAD_REQUIRE_CONTEXT")
        if kind == "process.exec":
            programs = policy.get("programs"); fps=policy.get("program_fingerprints")
            if not isinstance(programs, list) or not programs or not all(isinstance(x, str) and Path(x).is_absolute() for x in programs):
                raise CapabilityFault("PROCESS_POLICY_REQUIRES_ABSOLUTE_EXECUTABLE_ALLOWLIST")
            if not isinstance(fps,dict) or set(fps)!=set(programs): raise CapabilityFault("PROCESS_POLICY_FINGERPRINTS_REQUIRED")
            if policy.get("child_capability_propagation") != "NONE": raise CapabilityFault("PROCESS_CHILD_CAPABILITY_PROPAGATION_FORBIDDEN")
        elif kind == "async.compute":
            ops = policy.get("operations", ["identity", "square", "negate"])
            if not isinstance(ops, list) or any(x not in {"identity", "square", "negate"} for x in ops):
                raise CapabilityFault("ASYNC_POLICY_BAD_OPERATION")
        elif kind == "numerical.cpu":
            n = policy.get("max_vector", 1000000)
            if not isinstance(n, int) or n < 1 or n > 10000000: raise CapabilityFault("NUMERICAL_POLICY_BAD_LIMIT")
        elif kind in {"fs.read", "fs.write", "db.sqlite"}:
            prefix = policy.get("prefix", "")
            if not isinstance(prefix, str) or Path(prefix).is_absolute() or ".." in Path(prefix).parts: raise CapabilityFault("PATH_POLICY_BAD_PREFIX")
        elif kind == "net.http_get":
            origins=policy.get("origins"); limit=policy.get("max_response_bytes")
            if not isinstance(origins,list) or not origins: raise CapabilityFault("HTTP_POLICY_REQUIRES_ORIGINS")
            if not isinstance(limit,int) or limit<1 or limit>100*1024*1024: raise CapabilityFault("HTTP_POLICY_BAD_RESPONSE_LIMIT")

    def capability_descriptor(self, handle: _CapabilityHandle) -> dict[str, Any]:
        h, policy, context = self._validated(handle, None)
        return {"runtime_id": h.runtime_id, "capability_ref": hashlib.sha256(h.capability_id.encode()).hexdigest()[:16], "kind": h.kind, "epoch": h.epoch, "policy": json.loads(json.dumps(policy)), "authority_context": json.loads(json.dumps(context)), "context_hash": h.context_hash, "authorizing": False}

    def revoke(self, handle: _CapabilityHandle):
        h, _, _ = self._validated(handle, None)
        self._revoked.add(h.capability_id)

    def _validated(self, handle: Any, expected_kind: str | None):
        if not isinstance(handle, _CapabilityHandle): raise CapabilityFault("CAPABILITY_TYPE_INVALID")
        if handle.runtime_id != self.runtime_id: raise CapabilityFault("CAPABILITY_WRONG_RUNTIME")
        registered = self._capabilities.get(handle.capability_id)
        if registered is None or registered is not handle: raise CapabilityFault("CAPABILITY_NOT_REGISTERED_IDENTITY")
        if handle.capability_id in self._revoked: raise CapabilityFault("CAPABILITY_REVOKED")
        if handle.epoch != self._epoch: raise CapabilityFault("CAPABILITY_STALE_EPOCH")
        policy = self._policies.get(handle.capability_id); context=self._contexts.get(handle.capability_id)
        if policy is None: raise CapabilityFault("CAPABILITY_POLICY_MISSING")
        if context is None: raise CapabilityFault("AUTHORITY_CONTEXT_MISSING")
        _, ph = self._canonical_policy(policy); _, ch=self._canonical_context(context)
        if ph != handle.policy_hash: raise CapabilityFault("CAPABILITY_POLICY_HASH_MISMATCH")
        if ch != handle.context_hash: raise CapabilityFault("AUTHORITY_CONTEXT_HASH_MISMATCH")
        expected_nonce = hashlib.sha256(self._issuer_secret + self.runtime_id.encode() + handle.capability_id.encode() + handle.kind.encode() + str(handle.epoch).encode() + ph.encode() + ch.encode()).digest()
        if not secrets.compare_digest(expected_nonce, handle.nonce): raise CapabilityFault("CAPABILITY_NONCE_INVALID")
        if expected_kind is not None and handle.kind != expected_kind: raise CapabilityFault(f"CAPABILITY_KIND_MISMATCH:{handle.kind}!={expected_kind}")
        return handle, json.loads(json.dumps(policy)), json.loads(json.dumps(context))

    def _safe_path(self, relative: str | os.PathLike[str], policy: dict[str, Any]):
        prefix = Path(policy.get("prefix", "")); base=(self._sandbox_root/prefix).resolve(); path=(base/Path(relative)).resolve()
        try: path.relative_to(base)
        except ValueError as exc: raise ResourceFault("SANDBOX_PATH_ESCAPE") from exc
        return path

    def _new_resource(self, kind: str):
        self._resource_generation += 1
        ref=ResourceRef(self.runtime_id,uuid.uuid4().hex,kind,self._resource_generation); self._resources[ref.resource_id]=ref; return ref

    def register_adapter(self, name: str, capability_kind: str, function: Callable[..., Any]):
        if name in self._adapters: raise RuntimeFault(f"DUPLICATE_ADAPTER:{name}")
        self._adapters[name]=AdapterSpec(name,capability_kind,function)

    def _estimate_units(self, name: str, policy: dict[str, Any], args: tuple[Any,...]) -> int:
        try:
            if name == "fs.write_text": return len(str(args[1]).encode("utf-8"))
            if name == "fs.read_text":
                p=self._safe_path(args[0],policy); return max(1,p.stat().st_size) if p.exists() else 1
            if name == "db.sqlite_transaction": return max(1,len(list(args[1])))
            if name == "process.exec": return 1
            if name == "numerical.dot": return max(1,len(args[0]))
            if name == "async.map": return max(1,len(args[1]))
            if name == "net.http_get": return 1
        except Exception:
            return 1
        return 1

    def _charge(self, handle: _CapabilityHandle, policy: dict[str, Any], units: int) -> dict[str,int]:
        with self._usage_lock:
            usage=self._usage.setdefault(handle.capability_id,{"calls":0,"units":0})
            next_calls=usage["calls"]+1; next_units=usage["units"]+max(0,int(units))
            if "max_calls" in policy and next_calls>policy["max_calls"]: raise ResourceFault("CAPABILITY_CUMULATIVE_CALL_BUDGET")
            if "max_units" in policy and next_units>policy["max_units"]: raise ResourceFault("CAPABILITY_CUMULATIVE_RESOURCE_BUDGET")
            usage["calls"]=next_calls; usage["units"]=next_units
            return dict(usage)

    def usage_descriptor(self, handle: _CapabilityHandle) -> dict[str,Any]:
        h,_,_=self._validated(handle,None)
        with self._usage_lock: usage=dict(self._usage.get(h.capability_id,{"calls":0,"units":0}))
        return {"capability_ref":hashlib.sha256(h.capability_id.encode()).hexdigest()[:16],"usage":usage,"authorizing":False}

    def _invoke(self, name: str, capability: Any, supplied_context: Mapping[str,Any] | None, *args: Any, **kwargs: Any):
        spec=self._adapters.get(name)
        if spec is None: raise RuntimeFault(f"UNKNOWN_ADAPTER:{name}")
        handle,policy,bound_context=self._validated(capability,spec.capability_kind)
        if policy.get("require_context"):
            provided,provided_hash=self._canonical_context(supplied_context)
            self._validate_required_context(provided)
            if provided_hash!=handle.context_hash or provided!=bound_context: raise CapabilityFault("AUTHORITY_CONTEXT_BINDING_MISMATCH")
        elif supplied_context is not None:
            _,provided_hash=self._canonical_context(supplied_context)
            if handle.context_hash not in {_ZERO_CONTEXT_HASH,provided_hash}: raise CapabilityFault("AUTHORITY_CONTEXT_BINDING_MISMATCH")
        units=self._estimate_units(name,policy,args); usage=self._charge(handle,policy,units)
        started_ns=time.monotonic_ns()
        try:
            result=spec.function(policy,*args,**kwargs); self._record_trace(name,handle,"PASS",started_ns,None,usage); return result
        except Exception as exc:
            self._record_trace(name,handle,"FAULT",started_ns,type(exc).__name__,usage); raise

    def invoke(self, name: str, capability: Any, *args: Any, **kwargs: Any):
        return self._invoke(name,capability,None,*args,**kwargs)

    def invoke_bound(self, name: str, capability: Any, authority_context: Mapping[str,Any], *args: Any, **kwargs: Any):
        return self._invoke(name,capability,authority_context,*args,**kwargs)

    def _record_trace(self,name,handle,status,started_ns,error,usage):
        with self._trace_lock:
            self._trace_seq+=1; self._traces.append({"seq":self._trace_seq,"adapter":name,"capability_kind":handle.kind,"capability_ref":hashlib.sha256(handle.capability_id.encode()).hexdigest()[:16],"policy_hash":handle.policy_hash[:16],"context_hash":handle.context_hash[:16],"status":status,"duration_ns":max(0,time.monotonic_ns()-started_ns),"error":error,"cumulative_usage":usage})

    def trace_receipt(self):
        with self._trace_lock:return json.loads(json.dumps(self._traces))

    def _register_stdlib_adapters(self):
        self.register_adapter("fs.write_text","fs.write",self._fs_write_text)
        self.register_adapter("fs.read_text","fs.read",self._fs_read_text)
        self.register_adapter("db.sqlite_transaction","db.sqlite",self._sqlite_transaction)
        self.register_adapter("process.exec","process.exec",self._process_exec)
        self.register_adapter("numerical.dot","numerical.cpu",self._dot)
        self.register_adapter("async.map","async.compute",self._async_map)
        self.register_adapter("net.http_get","net.http_get",self._http_get)

    def _fs_write_text(self,policy,relative:str,text:str):
        path=self._safe_path(relative,policy); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text,encoding="utf-8")
        ref=self._new_resource("file"); return {"resource":dataclasses.asdict(ref),"sha256":hashlib.sha256(text.encode()).hexdigest(),"bytes":len(text.encode())}

    def _fs_read_text(self,policy,relative:str):
        text=self._safe_path(relative,policy).read_text(encoding="utf-8"); return {"text":text,"sha256":hashlib.sha256(text.encode()).hexdigest()}

    def _sqlite_transaction(self,policy,relative:str,statements:Iterable[tuple[str,tuple[Any,...]]]):
        path=self._safe_path(relative,policy); path.parent.mkdir(parents=True,exist_ok=True); conn=sqlite3.connect(path); rows=[]
        try:
            conn.execute("BEGIN IMMEDIATE")
            for sql,params in statements:
                cur=conn.execute(sql,tuple(params)); rows.append(cur.fetchall() if cur.description else [])
            conn.commit()
        except Exception: conn.rollback(); raise
        finally: conn.close()
        return {"resource":dataclasses.asdict(self._new_resource("sqlite")),"rows":rows}

    @classmethod
    def _verify_open_executable(cls, fd: int, expected: dict[str,Any]) -> None:
        st=os.fstat(fd); actual={"sha256":cls._sha256_fd(fd),"size":st.st_size,"mode":st.st_mode,"dev":st.st_dev,"ino":st.st_ino}
        if actual!=expected: raise CapabilityFault("PROCESS_EXECUTABLE_IDENTITY_CHANGED")

    def _process_exec(self,policy,argv:list[str]):
        if not argv: raise ResourceFault("EMPTY_ARGV")
        supplied=Path(argv[0])
        if not supplied.is_absolute(): raise CapabilityFault("PROCESS_EXEC_REQUIRES_ABSOLUTE_PATH")
        try: program=str(supplied.resolve(strict=True))
        except OSError as exc: raise ResourceFault(f"PROCESS_EXECUTABLE_MISSING:{argv[0]}") from exc
        if program not in set(policy["programs"]): raise CapabilityFault(f"PROCESS_NOT_ALLOWLISTED:{program}")
        fd=os.open(program,os.O_RDONLY)
        try:
            self._verify_open_executable(fd,policy["program_fingerprints"][program])
            pinned=f"/proc/self/fd/{fd}"
            child_env={k:v for k,v in os.environ.items() if not k.startswith("CLAYCODE_CAPABILITY_") and k not in {"CLAYCODE_AUTHORITY_CONTEXT","CLAYCODE_RUNTIME_SECRET"}}
            cp=subprocess.run([pinned,*argv[1:]],cwd=self._sandbox_root,text=True,capture_output=True,timeout=10,check=False,pass_fds=(fd,),close_fds=True,start_new_session=True,env=child_env)
            return {"returncode":cp.returncode,"stdout":cp.stdout,"stderr":cp.stderr,"executable_sha256":policy["program_fingerprints"][program]["sha256"],"child_capability_propagation":"NONE"}
        finally: os.close(fd)

    @staticmethod
    def _dot(policy,left:list[float],right:list[float]):
        if len(left)!=len(right): raise ResourceFault("DOT_LENGTH_MISMATCH")
        if len(left)>int(policy.get("max_vector",1000000)): raise ResourceFault("DOT_RESOURCE_LIMIT")
        return float(sum(float(a)*float(b) for a,b in zip(left,right)))

    @staticmethod
    def _async_map(policy,operation:str,values:list[Any],max_workers:int=4):
        allowed=set(policy.get("operations",["identity","square","negate"]))
        if operation not in allowed: raise CapabilityFault(f"ASYNC_OPERATION_NOT_ALLOWED:{operation}")
        if max_workers<1 or max_workers>64: raise ResourceFault("BAD_WORKER_COUNT")
        funcs={"identity":lambda x:x,"square":lambda x:x*x,"negate":lambda x:-x}; function=funcs[operation]; out=[]
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures={pool.submit(function,v):i for i,v in enumerate(values)}
            for future in concurrent.futures.as_completed(futures): out.append({"index":futures[future],"value":future.result()})
        out.sort(key=lambda x:x["index"]); return out

    @staticmethod
    def _origin(url: str) -> str:
        u=urllib.parse.urlsplit(url)
        if u.scheme not in {"http","https"} or not u.hostname: raise CapabilityFault("HTTP_URL_BAD_ORIGIN")
        port=u.port or (443 if u.scheme=="https" else 80)
        return f"{u.scheme}://{u.hostname.lower()}:{port}"

    def _http_get(self,policy,url:str):
        origin=self._origin(url)
        if origin not in set(policy["origins"]): raise CapabilityFault(f"HTTP_ORIGIN_NOT_ALLOWED:{origin}")
        limit=int(policy["max_response_bytes"]); opener=urllib.request.build_opener(_NoRedirect())
        req=urllib.request.Request(url,method="GET",headers={"User-Agent":"ClayCodeBaseRuntime/0.4"})
        try:
            with opener.open(req,timeout=10) as response:
                final=response.geturl()
                if self._origin(final)!=origin: raise CapabilityFault("HTTP_REDIRECT_ORIGIN_CHANGED")
                body=response.read(limit+1)
                if len(body)>limit: raise ResourceFault("HTTP_RESPONSE_LIMIT")
                return {"status":int(response.status),"body":body,"body_sha256":hashlib.sha256(body).hexdigest(),"final_url":final}
        except urllib.error.HTTPError as exc:
            if 300<=exc.code<400: raise CapabilityFault("HTTP_REDIRECT_FORBIDDEN") from exc
            raise

__all__=["ClayRuntime","VersionedCell","ResourceRef","RuntimeFault","CapabilityFault","ResourceFault","CASFault","RUNTIME_VERSION"]

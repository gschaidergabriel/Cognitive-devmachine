from __future__ import annotations

import hashlib
import hmac
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
import uvicorn
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from starlette.requests import Request
from starlette.responses import JSONResponse

VERSION = "0.1.0"

READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
MUTATING = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False)
EXTERNAL = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=True)

mcp = MCPServer(
    "clay-vps",
    title="Clay VPS",
    description="Controlled non-destructive Ubuntu VPS executor for Clay/Frank research, build, benchmark and Frank API communication.",
    instructions=(
        "Use this server for non-destructive VPS work only. Prefer read-only inspection first. "
        "Do not delete project/user data, rewrite git history, format disks, drop databases, or run destructive root actions. "
        "Mutations must be recoverable and audited. Frank API and MCP credentials are secrets and must never be returned."
    ),
    version=VERSION,
)


def _csv(name: str, default: str) -> list[str]:
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


def _roots() -> list[Path]:
    values = _csv("CLAY_MCP_ALLOWED_ROOTS", "/srv/clay-mcp/workspace,/srv/models,/opt/frank,/opt/clay")
    return [Path(x).expanduser().resolve(strict=False) for x in values]


def _state_dir() -> Path:
    p = Path(os.getenv("CLAY_MCP_STATE_DIR", "/var/lib/clay-vps-mcp"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def _resolve(path: str, *, exists: bool = False) -> Path:
    if "\x00" in path:
        raise ValueError("invalid path")
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = _roots()[0] / p
    p = p.resolve(strict=exists)
    for root in _roots():
        try:
            p.relative_to(root)
            return p
        except ValueError:
            pass
    raise PermissionError(f"path outside allowed roots: {p}")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _audit(action: str, payload: dict[str, Any], result: dict[str, Any]) -> None:
    rec = {
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "epoch": time.time(),
        "action": action,
        "payload": payload,
        "result": result,
        "uid": os.getuid(),
        "pid": os.getpid(),
    }
    with (_state_dir() / "audit.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")


def _allowed_executable(argv0: str) -> str:
    base = Path(argv0).name
    forbidden = {
        "rm", "rmdir", "shred", "wipefs", "mkfs", "mkfs.ext4", "mkfs.xfs", "fdisk", "sfdisk", "parted", "dd",
        "poweroff", "halt", "shutdown", "reboot", "userdel", "groupdel", "deluser", "delgroup", "dropdb",
    }
    if base in forbidden or base.startswith("mkfs."):
        raise PermissionError(f"destructive executable forbidden: {base}")
    defaults = (
        "git,python3,python,pytest,uv,cmake,make,ninja,gcc,g++,clang,clang++,cargo,rustc,node,npm,npx,"
        "llama-cli,llama-bench,llama-server,nvidia-smi,lspci,ls,cat,head,tail,grep,rg,find,stat,du,df,free,ps,"
        "sha256sum,jq,tar,unzip,huggingface-cli,hf"
    )
    allow = set(_csv("CLAY_MCP_ALLOWED_EXECUTABLES", defaults))
    if base not in allow:
        raise PermissionError(f"executable not allowlisted: {base}")
    exe = shutil.which(argv0) if "/" not in argv0 else str(Path(argv0))
    if not exe:
        raise FileNotFoundError(argv0)
    return exe


def _validate_argv(argv: list[str]) -> None:
    if not argv:
        raise ValueError("argv cannot be empty")
    base = Path(argv[0]).name
    joined = " ".join(argv[1:]).lower()
    if base == "git":
        forbidden = ["reset --hard", "clean -f", "clean -x", "push --force", "push -f", "branch -d", "branch -D".lower(), "checkout -f", "restore --staged --worktree"]
        if any(x.lower() in joined for x in forbidden):
            raise PermissionError("destructive git operation forbidden")
    if base in {"python", "python3"} and argv[1:2] == ["-c"]:
        raise PermissionError("python -c disabled; execute a reviewed script inside an allowed root")
    if base in {"node"} and argv[1:2] in (["-e"], ["--eval"]):
        raise PermissionError("node eval disabled")


def _env(extra: dict[str, str] | None) -> dict[str, str]:
    keep = {"PATH", "HOME", "USER", "LANG", "LC_ALL", "TZ", "CUDA_VISIBLE_DEVICES", "HF_HOME", "XDG_CACHE_HOME"}
    out = {k: v for k, v in os.environ.items() if k in keep}
    for k, v in (extra or {}).items():
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k):
            raise ValueError(f"invalid env key: {k}")
        if len(v) > 8192:
            raise ValueError(f"env value too long: {k}")
        out[k] = v
    return out


def _run(argv: list[str], cwd: str | None, timeout_seconds: int, env: dict[str, str] | None, max_output_chars: int) -> dict[str, Any]:
    _validate_argv(argv)
    exe = _allowed_executable(argv[0])
    max_timeout = int(os.getenv("CLAY_MCP_MAX_TIMEOUT", "7200"))
    if timeout_seconds < 1 or timeout_seconds > max_timeout:
        raise ValueError(f"timeout must be 1..{max_timeout}")
    workdir = _resolve(cwd or str(_roots()[0]), exists=True)
    started = time.monotonic()
    cp = subprocess.run(
        [exe, *argv[1:]], cwd=workdir, env=_env(env), stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace",
        timeout=timeout_seconds, check=False,
    )
    elapsed = round(time.monotonic() - started, 4)
    limit = max(1000, min(max_output_chars, 2_000_000))
    result = {
        "argv": [Path(exe).name, *argv[1:]], "cwd": str(workdir), "returncode": cp.returncode,
        "elapsed_seconds": elapsed, "stdout": cp.stdout[-limit:], "stderr": cp.stderr[-limit:],
        "stdout_truncated": len(cp.stdout) > limit, "stderr_truncated": len(cp.stderr) > limit,
    }
    _audit("run_command", {"argv": result["argv"], "cwd": str(workdir), "env_keys": sorted((env or {}).keys())}, {"returncode": cp.returncode, "elapsed_seconds": elapsed})
    return result


def _registry_path() -> Path:
    return _state_dir() / "processes.json"


def _load_registry() -> dict[str, Any]:
    try:
        return json.loads(_registry_path().read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_registry(reg: dict[str, Any]) -> None:
    tmp = _registry_path().with_suffix(".tmp")
    tmp.write_text(json.dumps(reg, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, _registry_path())


def _proc_start_ticks(pid: int) -> str | None:
    try:
        return Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").split()[21]
    except Exception:
        return None


@mcp.tool(annotations=READ_ONLY)
def ping() -> dict[str, Any]:
    """Return service identity and configured capability boundaries."""
    return {"ok": True, "service": "clay-vps", "version": VERSION, "hostname": platform.node(), "allowed_roots": [str(p) for p in _roots()]}


@mcp.tool(annotations=READ_ONLY)
def system_snapshot() -> dict[str, Any]:
    """Inspect operating system, load, CPU, memory, disks and NVIDIA GPU state."""
    mem: dict[str, str] = {}
    if Path("/proc/meminfo").exists():
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                mem[k] = v.strip()
    disks = []
    for root in _roots():
        probe = root if root.exists() else root.parent
        try:
            u = shutil.disk_usage(probe)
            disks.append({"root": str(root), "total": u.total, "used": u.used, "free": u.free})
        except Exception as exc:
            disks.append({"root": str(root), "error": str(exc)})
    gpu = None
    if shutil.which("nvidia-smi"):
        cp = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu", "--format=csv,noheader,nounits"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10, check=False)
        gpu = {"returncode": cp.returncode, "rows": [x.strip() for x in cp.stdout.splitlines() if x.strip()], "stderr": cp.stderr.strip()}
    return {"hostname": platform.node(), "platform": platform.platform(), "python": platform.python_version(), "cpu_count": os.cpu_count(), "loadavg": list(os.getloadavg()) if hasattr(os, "getloadavg") else None, "memory": mem, "disks": disks, "gpu": gpu}


@mcp.tool(annotations=READ_ONLY)
def list_directory(path: str, max_entries: int = 500) -> dict[str, Any]:
    """List an allowed directory."""
    d = _resolve(path, exists=True)
    if not d.is_dir():
        raise NotADirectoryError(str(d))
    rows = []
    for child in sorted(d.iterdir(), key=lambda p: p.name.lower())[: max(1, min(max_entries, 5000))]:
        st = child.stat()
        rows.append({"name": child.name, "path": str(child), "type": "dir" if child.is_dir() else "file" if child.is_file() else "other", "size": st.st_size, "mtime": st.st_mtime})
    return {"path": str(d), "entries": rows}


@mcp.tool(annotations=READ_ONLY)
def read_text_file(path: str, offset: int = 0, max_bytes: int = 200_000) -> dict[str, Any]:
    """Read a bounded UTF-8 text slice from an allowed file."""
    p = _resolve(path, exists=True)
    if not p.is_file():
        raise FileNotFoundError(str(p))
    max_bytes = max(1, min(max_bytes, int(os.getenv("CLAY_MCP_MAX_READ_BYTES", "1000000"))))
    with p.open("rb") as f:
        f.seek(offset)
        b = f.read(max_bytes)
    return {"path": str(p), "offset": offset, "bytes": len(b), "size": p.stat().st_size, "sha256": _sha256(p), "text": b.decode("utf-8", errors="replace")}


@mcp.tool(annotations=READ_ONLY)
def file_hash(path: str) -> dict[str, Any]:
    """Return SHA-256 and size for an allowed file."""
    p = _resolve(path, exists=True)
    return {"path": str(p), "sha256": _sha256(p), "size": p.stat().st_size}


@mcp.tool(annotations=READ_ONLY)
def find_files(root: str, pattern: str = "*", max_results: int = 500) -> dict[str, Any]:
    """Find files below an allowed root using a glob pattern such as '*.gguf'."""
    base = _resolve(root, exists=True)
    rows = []
    for p in base.rglob(pattern):
        if p.is_file():
            st = p.stat()
            rows.append({"path": str(p), "size": st.st_size, "mtime": st.st_mtime})
            if len(rows) >= max(1, min(max_results, 5000)):
                break
    return {"root": str(base), "pattern": pattern, "results": rows}


@mcp.tool(annotations=MUTATING)
def write_text_file(path: str, content: str, expected_sha256: str | None = None, create_only: bool = False) -> dict[str, Any]:
    """Create or recoverably replace a text file. Existing files require their current SHA-256 and are backed up first."""
    p = _resolve(path, exists=False)
    p.parent.mkdir(parents=True, exist_ok=True)
    prior_sha = None
    backup = None
    if p.exists():
        if create_only:
            raise FileExistsError(str(p))
        prior_sha = _sha256(p)
        if not expected_sha256 or not hmac.compare_digest(prior_sha, expected_sha256):
            raise PermissionError("existing-file update requires matching expected_sha256")
        backup_dir = _state_dir() / "backups" / time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / hashlib.sha256(str(p).encode()).hexdigest()
        shutil.copy2(p, backup)
    tmp = p.with_name(p.name + ".claytmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, p)
    result = {"path": str(p), "sha256": _sha256(p), "prior_sha256": prior_sha, "backup": str(backup) if backup else None}
    _audit("write_text_file", {"path": str(p), "create_only": create_only, "expected_sha256": expected_sha256}, result)
    return result


@mcp.tool(annotations=EXTERNAL)
def run_command(argv: list[str], cwd: str | None = None, timeout_seconds: int = 600, env: dict[str, str] | None = None, max_output_chars: int = 200_000) -> dict[str, Any]:
    """Run one allowlisted non-shell command in an allowed directory and capture stdout/stderr/exit status."""
    return _run(argv, cwd, timeout_seconds, env, max_output_chars)


@mcp.tool(annotations=EXTERNAL)
def start_process(argv: list[str], cwd: str | None = None, env: dict[str, str] | None = None, label: str | None = None) -> dict[str, Any]:
    """Start an allowlisted background process owned by this MCP service. Logs are retained for later inspection."""
    _validate_argv(argv)
    exe = _allowed_executable(argv[0])
    workdir = _resolve(cwd or str(_roots()[0]), exists=True)
    reg = _load_registry()
    proc_id = hashlib.sha256(f"{time.time_ns()}:{argv}:{workdir}".encode()).hexdigest()[:20]
    log_path = _state_dir() / "process_logs" / f"{proc_id}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = log_path.open("ab", buffering=0)
    proc = subprocess.Popen([exe, *argv[1:]], cwd=workdir, env=_env(env), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    rec = {"process_id": proc_id, "pid": proc.pid, "start_ticks": _proc_start_ticks(proc.pid), "argv": [Path(exe).name, *argv[1:]], "cwd": str(workdir), "log": str(log_path), "label": label, "started_at": time.time()}
    reg[proc_id] = rec
    _save_registry(reg)
    _audit("start_process", {"argv": rec["argv"], "cwd": rec["cwd"], "label": label}, {"process_id": proc_id, "pid": proc.pid})
    return rec


@mcp.tool(annotations=READ_ONLY)
def process_status(process_id: str) -> dict[str, Any]:
    """Inspect a process previously started through this MCP service."""
    rec = _load_registry().get(process_id)
    if not rec:
        raise KeyError(process_id)
    live_ticks = _proc_start_ticks(int(rec["pid"]))
    return {**rec, "running": live_ticks is not None and live_ticks == rec.get("start_ticks")}


@mcp.tool(annotations=READ_ONLY)
def process_logs(process_id: str, max_bytes: int = 200_000) -> dict[str, Any]:
    """Read the tail of logs for a process started through this MCP service."""
    rec = _load_registry().get(process_id)
    if not rec:
        raise KeyError(process_id)
    p = Path(rec["log"])
    if not p.exists():
        return {"process_id": process_id, "text": "", "bytes": 0}
    size = p.stat().st_size
    n = max(1, min(max_bytes, 2_000_000))
    with p.open("rb") as f:
        f.seek(max(0, size - n))
        b = f.read(n)
    return {"process_id": process_id, "running": _proc_start_ticks(int(rec["pid"])) == rec.get("start_ticks"), "bytes": len(b), "size": size, "text": b.decode("utf-8", errors="replace")}


@mcp.tool(annotations=MUTATING)
def stop_owned_process(process_id: str, grace_seconds: int = 10) -> dict[str, Any]:
    """Stop only a process that was started and registered by this MCP service."""
    reg = _load_registry()
    rec = reg.get(process_id)
    if not rec:
        raise KeyError(process_id)
    pid = int(rec["pid"])
    if _proc_start_ticks(pid) != rec.get("start_ticks"):
        return {"process_id": process_id, "stopped": False, "reason": "not_running_or_pid_reused"}
    os.killpg(pid, signal.SIGTERM)
    deadline = time.time() + max(1, min(grace_seconds, 60))
    while time.time() < deadline and _proc_start_ticks(pid) == rec.get("start_ticks"):
        time.sleep(0.1)
    running = _proc_start_ticks(pid) == rec.get("start_ticks")
    if running:
        os.killpg(pid, signal.SIGKILL)
    result = {"process_id": process_id, "stopped": True, "needed_sigkill": running}
    _audit("stop_owned_process", {"process_id": process_id}, result)
    return result


@mcp.tool(annotations=READ_ONLY)
def model_inventory(max_results: int = 300) -> dict[str, Any]:
    """Inventory GGUF and multimodal projector files under configured roots."""
    rows = []
    for root in _roots():
        if not root.exists():
            continue
        for pattern in ("*.gguf", "*mmproj*"):
            for p in root.rglob(pattern):
                if p.is_file():
                    st = p.stat()
                    rows.append({"path": str(p), "size": st.st_size, "mtime": st.st_mtime})
                    if len(rows) >= max_results:
                        return {"models": rows, "truncated": True}
    return {"models": rows, "truncated": False}


def _frank_base() -> str:
    base = os.getenv("FRANK_API_BASE_URL", "").strip()
    if not base:
        raise RuntimeError("FRANK_API_BASE_URL is not configured")
    parsed = urlparse(base)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("invalid FRANK_API_BASE_URL")
    return base.rstrip("/") + "/"


def _frank_headers() -> dict[str, str]:
    token = os.getenv("FRANK_API_TOKEN", "")
    if not token:
        raise RuntimeError("FRANK_API_TOKEN is not configured")
    header_name = os.getenv("FRANK_API_TOKEN_HEADER", "Authorization")
    prefix = os.getenv("FRANK_API_TOKEN_PREFIX", "Bearer ")
    return {header_name: f"{prefix}{token}", "Accept": "application/json"}


@mcp.tool(annotations=READ_ONLY)
def frank_health() -> dict[str, Any]:
    """Check the configured 24/7 Frank API health endpoint using the secret token without exposing it."""
    path = os.getenv("FRANK_API_HEALTH_PATH", "/health").lstrip("/")
    url = urljoin(_frank_base(), path)
    started = time.monotonic()
    with httpx.Client(timeout=15.0, follow_redirects=False) as client:
        r = client.get(url, headers=_frank_headers())
    return {"status_code": r.status_code, "elapsed_seconds": round(time.monotonic() - started, 4), "body": r.text[:100_000], "content_type": r.headers.get("content-type")}


@mcp.tool(annotations=EXTERNAL)
def frank_api_request(method: str, path: str, json_body: dict[str, Any] | list[Any] | None = None, timeout_seconds: int = 120) -> dict[str, Any]:
    """Communicate with Frank through its configured token. Only GET and POST to relative paths on FRANK_API_BASE_URL are permitted."""
    method = method.upper()
    if method not in {"GET", "POST"}:
        raise PermissionError("only GET and POST are allowed")
    if path.startswith("http://") or path.startswith("https://") or ".." in Path(path).parts:
        raise PermissionError("path must be relative to FRANK_API_BASE_URL")
    url = urljoin(_frank_base(), path.lstrip("/"))
    started = time.monotonic()
    with httpx.Client(timeout=max(1, min(timeout_seconds, 600)), follow_redirects=False) as client:
        r = client.request(method, url, headers=_frank_headers(), json=json_body if method == "POST" else None)
    result = {"status_code": r.status_code, "elapsed_seconds": round(time.monotonic() - started, 4), "content_type": r.headers.get("content-type"), "body": r.text[:500_000]}
    _audit("frank_api_request", {"method": method, "path": path, "has_json_body": json_body is not None}, {"status_code": r.status_code, "elapsed_seconds": result["elapsed_seconds"]})
    return result


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(_: Request) -> JSONResponse:
    return JSONResponse({"ok": True, "service": "clay-vps", "version": VERSION})


def _transport_security() -> TransportSecuritySettings:
    hosts = _csv("CLAY_MCP_ALLOWED_HOSTS", "127.0.0.1:*,localhost:*,[::1]:*")
    origins = _csv("CLAY_MCP_ALLOWED_ORIGINS", "http://127.0.0.1:*,http://localhost:*,http://[::1]:*")
    return TransportSecuritySettings(enable_dns_rebinding_protection=True, allowed_hosts=hosts, allowed_origins=origins)


class BearerTokenMiddleware:
    def __init__(self, app: Any):
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http" or scope.get("path") == "/healthz":
            await self.app(scope, receive, send)
            return
        expected = os.getenv("CLAY_MCP_TOKEN", "")
        if not expected:
            response = JSONResponse({"error": "CLAY_MCP_TOKEN_not_configured"}, status_code=503)
            await response(scope, receive, send)
            return
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        supplied = headers.get("authorization", "")
        wanted = f"Bearer {expected}"
        if not hmac.compare_digest(supplied, wanted):
            response = JSONResponse({"error": "unauthorized"}, status_code=401, headers={"WWW-Authenticate": "Bearer"})
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)


_base_app = mcp.streamable_http_app(
    stateless_http=True,
    json_response=True,
    host=os.getenv("CLAY_MCP_BIND", "127.0.0.1"),
    transport_security=_transport_security(),
)
app = BearerTokenMiddleware(_base_app)


def main() -> None:
    host = os.getenv("CLAY_MCP_BIND", "127.0.0.1")
    port = int(os.getenv("CLAY_MCP_PORT", "8765"))
    uvicorn.run(app, host=host, port=port, proxy_headers=True, forwarded_allow_ips=os.getenv("CLAY_MCP_FORWARDED_ALLOW_IPS", "127.0.0.1"))


if __name__ == "__main__":
    main()

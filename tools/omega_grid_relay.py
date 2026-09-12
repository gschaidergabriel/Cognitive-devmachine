#!/usr/bin/env python3
"""OMEGA GRID effect relay.

Runs outside the OMEGA sandbox with repository-scoped GitHub authority. It never
chooses the execution organ: GRID already bound ``organ_id``. The relay only verifies
that binding, applies the OMEGA/Frankenstein alignment guard, delivers the exact
idempotent command to the selected local FranKenstein bridge, waits for its receipt,
and returns correlated evidence to OMEGA.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any

REPO = os.getenv("GITHUB_REPOSITORY", "gschaidergabriel/clay-global-research-entity")
TOKEN = os.getenv("GITHUB_TOKEN", "")
API = "https://api.github.com"

ORGAN = {
    "host:ai-core-node": {
        "owner": "gabriel",
        "machine_id": "ai-core-node",
        "control": "chatgpt-local-ai-core-node-control",
        "results": "chatgpt-local-ai-core-node-results",
    },
    "host:andreas-maco": {
        "owner": "andreas",
        "machine_id": "andreas-maco",
        "control": "chatgpt-local-andreas-maco-control",
        "results": "chatgpt-local-andreas-maco-results",
    },
}

DELETE = [
    re.compile(r"(^|[;&|()]\s*)(sudo\s+)?(rm|rmdir|unlink|shred)(\s|$)", re.I),
    re.compile(r"\bgit\s+(rm|clean\b|branch\s+-[dD]\b|tag\s+-d\b)", re.I),
    re.compile(r"\bfind\b[^\n;&|]*\s-delete\b", re.I),
    re.compile(r"\b(delete\s+from|drop\s+(table|database|schema)|truncate\s+table)\b", re.I),
    re.compile(r"\b(apt|apt-get|dnf|yum)\s+(remove|autoremove|erase)\b", re.I),
    re.compile(r"\bpip(?:3)?\s+uninstall\b|\bnpm\s+uninstall\b", re.I),
]
FORMAT = [
    re.compile(r"(^|[;&|()]\s*)(sudo\s+)?(mkfs(?:\.[\w+.-]+)?|mke2fs|newfs|wipefs)(\s|$)", re.I),
    re.compile(r"\bdd\b[^\n]*\bof=/dev/", re.I),
]
PROTECTED_PATH = re.compile(
    r"(voice_action_guard\.py|ALIGNMENT_KERNEL\.md|effect_executor_interlock\.py|omega[/\\]alignment\.py)$",
    re.I,
)


def canonical(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(obj: Any) -> str:
    return hashlib.sha256(canonical(obj)).hexdigest()


def _request(method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, Any]:
    if not TOKEN:
        raise RuntimeError("GITHUB_TOKEN_MISSING")
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "omega-grid-relay/1",
            **({"Content-Type": "application/json"} if data else {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode()
            return int(resp.status), json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        try:
            body = json.loads(raw)
        except Exception:
            body = raw
        return int(exc.code), body


def get_file(branch: str, path: str) -> bytes | None:
    q = urllib.parse.quote(path, safe="/")
    status, body = _request("GET", f"/repos/{REPO}/contents/{q}?ref={urllib.parse.quote(branch)}")
    if status == 404:
        return None
    if status != 200 or not isinstance(body, dict):
        raise RuntimeError(f"GET_FILE_FAILED:{status}:{body}")
    return base64.b64decode(body["content"])


def put_new(branch: str, path: str, content: bytes, message: str) -> bool:
    q = urllib.parse.quote(path, safe="/")
    status, body = _request(
        "PUT",
        f"/repos/{REPO}/contents/{q}",
        {"message": message, "content": base64.b64encode(content).decode(), "branch": branch},
    )
    if status in (200, 201):
        return True
    # Existing idempotent command is not re-created or mutated.
    if status in (409, 422) and get_file(branch, path) is not None:
        return False
    raise RuntimeError(f"PUT_FILE_FAILED:{status}:{body}")


def wait_file(branch: str, path: str, timeout_s: float = 75.0) -> bytes | None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        value = get_file(branch, path)
        if value is not None:
            return value
        time.sleep(3)
    return None


def queue_vps(command_id: str, command: str, timeout_seconds: int = 60) -> None:
    payload = {
        "schema": "CLAY_VPS_COMMAND/v3",
        "command_id": command_id,
        "op": "exec",
        "cwd": "/workspace/omega_runtime/state",
        "timeout_seconds": timeout_seconds,
        "command": command,
    }
    put_new(
        "chatgpt-vps-control",
        f"vps_bridge/commands/{command_id}.json",
        json.dumps(payload, indent=2).encode() + b"\n",
        f"omega relay: queue {command_id}",
    )


def poll_pending() -> list[dict[str, Any]]:
    cid = "omega-relay-poll-" + uuid.uuid4().hex[:16]
    script = r'''python3 - <<'PY'
import json,pathlib
out=[]
for p in sorted(pathlib.Path('/workspace/omega_runtime/state/outbox').glob('*.json')):
    try:
        d=json.loads(p.read_text())
        if d.get('kind')=='GRID_EFFECT_INTENT': out.append(d)
    except Exception: pass
    if len(out)>=8: break
print(json.dumps({'pending':out},separators=(',',':')))
PY'''
    queue_vps(cid, script, 30)
    raw = wait_file("chatgpt-vps-results", f"vps_bridge/results/receipts/{cid}.json")
    if raw is None:
        return []
    receipt = json.loads(raw)
    if receipt.get("status") != "PASS":
        return []
    text = str(receipt.get("stdout_tail") or "").strip()
    try:
        parsed = json.loads(text)
    except Exception:
        return []
    return parsed.get("pending", []) if isinstance(parsed, dict) else []


def dangerous_exec(command: str) -> str | None:
    if any(p.search(command) for p in DELETE):
        return "DELETE_REMOVAL_DENIED"
    if any(p.search(command) for p in FORMAT):
        return "STORAGE_FORMAT_DENIED"
    if PROTECTED_PATH.search(command):
        return "ALIGNMENT_SELF_MUTATION_DENIED"
    return None


def build_local_command(effect: dict[str, Any]) -> tuple[str, dict[str, Any], str]:
    organ_id = str(effect["organ_id"])
    target = ORGAN[organ_id]
    task = effect.get("task") if isinstance(effect.get("task"), dict) else {}

    if task.get("requires_confirmation"):
        raise PermissionError("REQUIRE_CONFIRMATION")

    if task.get("task_id") == "background_host_scout":
        op = "status"
        args: dict[str, Any] = {}
    else:
        op = str(task.get("bridge_op") or "")
        args = task.get("bridge_args") if isinstance(task.get("bridge_args"), dict) else {}
        if op not in {"status", "exec", "read_file", "write_text", "screenshot"}:
            raise PermissionError("DEGRADE_TO_PROPOSAL")

    if op == "exec":
        command = str(args.get("command") or "")
        reason = dangerous_exec(command)
        if reason:
            raise PermissionError(reason)
    if op == "write_text":
        path = str(args.get("path") or "")
        if PROTECTED_PATH.search(path):
            raise PermissionError("ALIGNMENT_SELF_MUTATION_DENIED")

    cid = "omega-effect-" + re.sub(r"[^A-Za-z0-9_.-]", "-", str(effect["effect_id"]))[:100]
    cmd: dict[str, Any] = {
        "schema": "CLAY_LOCAL_COMMAND/v1",
        "command_id": cid,
        "op": op,
        "machine_id": target["machine_id"],
        "owner": target["owner"],
    }
    if op == "exec":
        cmd["command"] = str(args.get("command") or "")
        if args.get("cwd"):
            cmd["cwd"] = str(args["cwd"])
        cmd["timeout_seconds"] = min(3600, max(1, int(args.get("timeout_seconds", 120))))
    elif op == "read_file":
        cmd["path"] = str(args.get("path") or "")
    elif op == "write_text":
        cmd["path"] = str(args.get("path") or "")
        cmd["content"] = str(args.get("content") or "")
    elif op == "screenshot":
        cmd["name"] = str(args.get("name") or "omega-grid")
    return cid, cmd, op


def return_to_omega(effect: dict[str, Any], state: str, gate: dict[str, Any], local_receipt: dict[str, Any] | None) -> None:
    result = {
        "schema": "OMEGA_EFFECT_RETURN/v1",
        "effect_id": effect["effect_id"],
        "organ_id": effect["organ_id"],
        "request_sha256": effect["request_sha256"],
        "state": state,
        "gate": gate,
        "local_receipt": local_receipt,
        "returned_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    encoded = base64.b64encode(json.dumps(result, separators=(",", ":")).encode()).decode()
    cid = "omega-relay-return-" + re.sub(r"[^A-Za-z0-9_.-]", "-", str(effect["effect_id"]))[:80]
    script = f'''python3 - <<'PY'\nimport base64,json,pathlib,sqlite3\nr=json.loads(base64.b64decode("{encoded}"))\nroot=pathlib.Path('/workspace/omega_runtime/state')\n(root/'receipts').mkdir(exist_ok=True)\n(root/'receipts'/f"{{r['effect_id']}}.json").write_text(json.dumps(r,indent=2)+"\\n")\ncon=sqlite3.connect(root/'omega.sqlite3')\ncon.execute('update effect set state=? where id=?',(r['state'],r['effect_id']))\ncon.commit();con.close()\nfor p in (root/'outbox').glob('*.json'):\n    try:\n        d=json.loads(p.read_text())\n        if d.get('kind')=='GRID_EFFECT_INTENT' and d.get('payload',{{}}).get('effect_id')==r['effect_id']:\n            p.rename(p.with_suffix('.consumed'));break\n    except Exception: pass\nPY'''
    queue_vps(cid, script, 45)


def process(item: dict[str, Any]) -> None:
    effect = item.get("payload") if isinstance(item.get("payload"), dict) else {}
    required = {"effect_id", "organ_id", "task", "route", "authority", "request_sha256"}
    if not required.issubset(effect):
        return
    if effect["organ_id"] not in ORGAN:
        return
    if effect.get("authority") != "NOT_YET_GRANTED":
        return

    base = dict(effect)
    claimed = str(base.pop("request_sha256"))
    if digest(base) != claimed:
        gate = {"decision":"DENY","reason":"REQUEST_DIGEST_MISMATCH","decision_id":"gate_"+uuid.uuid4().hex,"authority_ref":"omega-grid-relay/v1"}
        return_to_omega(effect, "DENIED", gate, None)
        return

    try:
        cid, command, _op = build_local_command(effect)
    except PermissionError as exc:
        reason = str(exc)
        decision = "REQUIRE_CONFIRMATION" if reason == "REQUIRE_CONFIRMATION" else ("DEGRADE_TO_PROPOSAL" if reason == "DEGRADE_TO_PROPOSAL" else "DENY")
        gate = {"decision":decision,"reason":reason,"decision_id":"gate_"+uuid.uuid4().hex,"authority_ref":"omega-grid-relay/v1"}
        return_to_omega(effect, decision, gate, None)
        return

    target = ORGAN[effect["organ_id"]]
    gate = {
        "decision":"ALLOW",
        "reason":"EXACT_BOUND_REQUEST_ADMITTED",
        "decision_id":"gate_"+uuid.uuid4().hex,
        "authority_ref":"omega-grid-relay/v1",
        "effect_id":effect["effect_id"],
        "organ_id":effect["organ_id"],
        "request_sha256":claimed,
    }
    path = f"local_bridge/commands/{cid}.json"
    put_new(target["control"], path, json.dumps(command, indent=2).encode()+b"\n", f"omega effect: {effect['effect_id']}")
    raw = wait_file(target["results"], f"local_bridge/results/receipts/{cid}.json", 75)
    if raw is None:
        # Leave the intent pending. Same command id makes the next reconciliation idempotent.
        return
    receipt = json.loads(raw)
    state = "PASS" if receipt.get("status") == "PASS" else "UNKNOWN"
    return_to_omega(effect, state, gate, receipt)


def main() -> int:
    pending = poll_pending()
    for item in pending:
        try:
            process(item)
        except Exception as exc:
            print(f"relay-error:{type(exc).__name__}:{exc}", file=sys.stderr)
    print(json.dumps({"pending_seen": len(pending)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

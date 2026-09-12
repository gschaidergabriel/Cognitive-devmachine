#!/usr/bin/env python3
"""OMEGA GRID effect relay.

Routes exact GRID-bound effects to one real FranKenstein organ. The relay does not
choose the organ and cannot self-grant authority. It validates the request digest,
applies hard alignment fences, dispatches one idempotent Local-Bridge command, and
reconciles an exact receipt back into OMEGA.

Design invariant: a missing receipt is never a reason to replay an effect. Dispatch
and reconciliation are separate phases so a slow host cannot stall the whole relay.
"""
from __future__ import annotations

import argparse
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
DEFAULT_RECEIPT_WAIT_S = max(0.0, float(os.getenv("OMEGA_RECEIPT_WAIT_S", "0")))
DEFAULT_WATCH_INTERVAL_S = max(0.5, float(os.getenv("OMEGA_RELAY_INTERVAL_S", "2")))

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
    r"(voice_action_guard\.py|ALIGNMENT_KERNEL\.md|effect_executor_interlock\.py|omega[/\\]alignment\.py)(?:\s|$)",
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
            "User-Agent": "omega-grid-relay/2",
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
    """Create immutable command content.

    True means this call created it. False means the exact same bytes already exist.
    Same command id/path with different bytes is a hard conflict, never idempotency.
    """
    q = urllib.parse.quote(path, safe="/")
    status, body = _request(
        "PUT",
        f"/repos/{REPO}/contents/{q}",
        {"message": message, "content": base64.b64encode(content).decode(), "branch": branch},
    )
    if status in (200, 201):
        return True
    if status in (409, 422):
        current = get_file(branch, path)
        if current is not None:
            if current == content:
                return False
            raise RuntimeError("COMMAND_ID_CONFLICT")
    raise RuntimeError(f"PUT_FILE_FAILED:{status}:{body}")


def wait_file(branch: str, path: str, timeout_s: float) -> bytes | None:
    if timeout_s <= 0:
        return get_file(branch, path)
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        value = get_file(branch, path)
        if value is not None:
            return value
        time.sleep(min(1.0, max(0.1, timeout_s / 10.0)))
    return get_file(branch, path)


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
        json.dumps(payload, indent=2, sort_keys=True).encode() + b"\n",
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
        if d.get('kind')=='GRID_EFFECT_INTENT':
            d['_omega_outbox_name']=p.name
            out.append(d)
    except Exception:
        pass
    if len(out)>=16:
        break
print(json.dumps({'pending':out},separators=(',',':')))
PY'''
    queue_vps(cid, script, 30)
    raw = wait_file("chatgpt-vps-results", f"vps_bridge/results/receipts/{cid}.json", 30)
    if raw is None:
        raise RuntimeError("VPS_POLL_RECEIPT_TIMEOUT")
    receipt = json.loads(raw)
    if receipt.get("status") != "PASS" or receipt.get("command_id") != cid:
        raise RuntimeError("VPS_POLL_RECEIPT_INVALID")
    text = str(receipt.get("stdout_tail") or "").strip()
    parsed = json.loads(text)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("pending"), list):
        raise RuntimeError("VPS_POLL_PAYLOAD_INVALID")
    return parsed["pending"]


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


def gate_for(effect: dict[str, Any], decision: str, reason: str) -> dict[str, Any]:
    material = {
        "effect_id": effect.get("effect_id"),
        "organ_id": effect.get("organ_id"),
        "request_sha256": effect.get("request_sha256"),
        "decision": decision,
        "reason": reason,
        "authority_ref": "omega-grid-relay/v2",
    }
    return {
        "decision": decision,
        "reason": reason,
        "decision_id": "gate_" + digest(material)[:32],
        "authority_ref": "omega-grid-relay/v2",
        "effect_id": effect.get("effect_id"),
        "organ_id": effect.get("organ_id"),
        "request_sha256": effect.get("request_sha256"),
    }


def validate_local_receipt(receipt: dict[str, Any], cid: str, target: dict[str, str], op: str) -> str | None:
    if receipt.get("schema") != "CLAY_LOCAL_RECEIPT/v1":
        return "RECEIPT_SCHEMA_MISMATCH"
    if receipt.get("command_id") != cid:
        return "RECEIPT_COMMAND_ID_MISMATCH"
    if receipt.get("machine_id") != target["machine_id"]:
        return "RECEIPT_MACHINE_ID_MISMATCH"
    if receipt.get("owner") != target["owner"]:
        return "RECEIPT_OWNER_MISMATCH"
    if receipt.get("op") != op:
        return "RECEIPT_OP_MISMATCH"
    return None


def return_to_omega(effect: dict[str, Any], state: str, gate: dict[str, Any], local_receipt: dict[str, Any] | None, *, consume_intent: bool) -> None:
    result = {
        "schema": "OMEGA_EFFECT_RETURN/v2",
        "effect_id": effect["effect_id"],
        "organ_id": effect["organ_id"],
        "request_sha256": effect["request_sha256"],
        "state": state,
        "gate": gate,
        "local_receipt": local_receipt,
        "consume_intent": bool(consume_intent),
        "returned_at": (local_receipt or {}).get("finished_at"),
    }
    result_key = digest(result)[:16]
    encoded = base64.b64encode(json.dumps(result, separators=(",", ":"), sort_keys=True).encode()).decode()
    effect_key = re.sub(r"[^A-Za-z0-9_.-]", "-", str(effect["effect_id"]))[:70]
    cid = f"omega-relay-return-{effect_key}-{result_key}"
    consume = "True" if consume_intent else "False"
    script = f'''python3 - <<'PY'\nimport base64,json,pathlib,sqlite3\nr=json.loads(base64.b64decode("{encoded}"))\nroot=pathlib.Path('/workspace/omega_runtime/state')\n(root/'receipts').mkdir(exist_ok=True)\n(root/'receipts'/f"{{r['effect_id']}}.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\\n")\ncon=sqlite3.connect(root/'omega.sqlite3')\ncon.execute('update effect set state=? where id=?',(r['state'],r['effect_id']))\ncon.commit();con.close()\nif {consume}:\n    for p in (root/'outbox').glob('*.json'):\n        try:\n            d=json.loads(p.read_text())\n            if d.get('kind')=='GRID_EFFECT_INTENT' and d.get('payload',{{}}).get('effect_id')==r['effect_id']:\n                p.rename(p.with_suffix('.consumed'));break\n        except Exception:\n            pass\nPY'''
    queue_vps(cid, script, 45)


def _finalize_from_receipt(effect: dict[str, Any], cid: str, target: dict[str, str], op: str, raw: bytes) -> str:
    try:
        receipt = json.loads(raw)
    except Exception:
        gate = gate_for(effect, "DENY", "RECEIPT_JSON_INVALID")
        return_to_omega(effect, "UNKNOWN", gate, None, consume_intent=True)
        return "UNKNOWN:RECEIPT_JSON_INVALID"
    if not isinstance(receipt, dict):
        gate = gate_for(effect, "DENY", "RECEIPT_NOT_OBJECT")
        return_to_omega(effect, "UNKNOWN", gate, None, consume_intent=True)
        return "UNKNOWN:RECEIPT_NOT_OBJECT"
    mismatch = validate_local_receipt(receipt, cid, target, op)
    if mismatch:
        gate = gate_for(effect, "DENY", mismatch)
        return_to_omega(effect, "UNKNOWN", gate, receipt, consume_intent=True)
        return f"UNKNOWN:{mismatch}"
    gate = gate_for(effect, "ALLOW", "EXACT_BOUND_REQUEST_ADMITTED")
    state = "PASS" if receipt.get("status") == "PASS" else "UNKNOWN"
    return_to_omega(effect, state, gate, receipt, consume_intent=True)
    return state


def process(item: dict[str, Any], receipt_wait_s: float = DEFAULT_RECEIPT_WAIT_S) -> str:
    effect = item.get("payload") if isinstance(item.get("payload"), dict) else {}
    required = {"effect_id", "organ_id", "task", "route", "authority", "request_sha256"}
    missing = sorted(required.difference(effect))
    if missing:
        return "INVALID:MISSING:" + ",".join(missing)

    if effect["organ_id"] not in ORGAN:
        gate = gate_for(effect, "DENY", "UNKNOWN_ORGAN")
        return_to_omega(effect, "DENIED", gate, None, consume_intent=True)
        return "DENIED:UNKNOWN_ORGAN"
    if effect.get("authority") != "NOT_YET_GRANTED":
        gate = gate_for(effect, "DENY", "AUTHORITY_STATE_INVALID")
        return_to_omega(effect, "DENIED", gate, None, consume_intent=True)
        return "DENIED:AUTHORITY_STATE_INVALID"

    base = dict(effect)
    claimed = str(base.pop("request_sha256"))
    if digest(base) != claimed:
        gate = gate_for(effect, "DENY", "REQUEST_DIGEST_MISMATCH")
        return_to_omega(effect, "DENIED", gate, None, consume_intent=True)
        return "DENIED:REQUEST_DIGEST_MISMATCH"

    try:
        cid, command, op = build_local_command(effect)
    except PermissionError as exc:
        reason = str(exc)
        decision = "REQUIRE_CONFIRMATION" if reason == "REQUIRE_CONFIRMATION" else ("DEGRADE_TO_PROPOSAL" if reason == "DEGRADE_TO_PROPOSAL" else "DENY")
        gate = gate_for(effect, decision, reason)
        return_to_omega(effect, decision, gate, None, consume_intent=True)
        return f"{decision}:{reason}"

    target = ORGAN[effect["organ_id"]]
    receipt_path = f"local_bridge/results/receipts/{cid}.json"
    existing = get_file(target["results"], receipt_path)
    if existing is not None:
        return _finalize_from_receipt(effect, cid, target, op, existing)

    command_bytes = json.dumps(command, indent=2, sort_keys=True).encode() + b"\n"
    command_path = f"local_bridge/commands/{cid}.json"
    try:
        put_new(target["control"], command_path, command_bytes, f"omega effect: {effect['effect_id']}")
    except RuntimeError as exc:
        if str(exc) == "COMMAND_ID_CONFLICT":
            gate = gate_for(effect, "DENY", "COMMAND_ID_CONFLICT")
            return_to_omega(effect, "UNKNOWN", gate, None, consume_intent=True)
            return "UNKNOWN:COMMAND_ID_CONFLICT"
        raise

    raw = wait_file(target["results"], receipt_path, receipt_wait_s)
    if raw is not None:
        return _finalize_from_receipt(effect, cid, target, op, raw)

    gate = gate_for(effect, "ALLOW", "DISPATCHED_AWAITING_EXACT_RECEIPT")
    return_to_omega(effect, "PENDING", gate, None, consume_intent=False)
    return "PENDING"


def run_once(receipt_wait_s: float = DEFAULT_RECEIPT_WAIT_S) -> tuple[int, dict[str, Any]]:
    pending = poll_pending()
    counts: dict[str, int] = {}
    errors = 0
    for item in pending:
        try:
            outcome = process(item, receipt_wait_s=receipt_wait_s)
        except Exception as exc:
            errors += 1
            outcome = f"ERROR:{type(exc).__name__}:{exc}"
            print(f"relay-error:{type(exc).__name__}:{exc}", file=sys.stderr)
        key = outcome.split(":", 1)[0]
        counts[key] = counts.get(key, 0) + 1
    summary = {"pending_seen": len(pending), "outcomes": counts, "errors": errors}
    print(json.dumps(summary, sort_keys=True))
    return (0 if errors == 0 else 2), summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true", help="run the relay continuously")
    parser.add_argument("--interval", type=float, default=DEFAULT_WATCH_INTERVAL_S)
    parser.add_argument("--receipt-wait", type=float, default=DEFAULT_RECEIPT_WAIT_S)
    args = parser.parse_args(argv)

    if not args.watch:
        try:
            rc, _ = run_once(max(0.0, args.receipt_wait))
            return rc
        except Exception as exc:
            print(f"relay-fatal:{type(exc).__name__}:{exc}", file=sys.stderr)
            return 3

    interval = max(0.5, args.interval)
    worst_rc = 0
    while True:
        try:
            rc, _ = run_once(max(0.0, args.receipt_wait))
            worst_rc = max(worst_rc, rc)
        except KeyboardInterrupt:
            return worst_rc
        except Exception as exc:
            worst_rc = max(worst_rc, 3)
            print(f"relay-fatal:{type(exc).__name__}:{exc}", file=sys.stderr)
        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())

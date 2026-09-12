#!/usr/bin/env python3
"""OMEGA GRID effect relay.

Runs outside the OMEGA sandbox with repository-scoped GitHub authority. It never
chooses the execution organ: GRID already bound ``organ_id``. The relay only verifies
that binding, applies the OMEGA/Frankenstein alignment guard, delivers the exact
idempotent command to the selected local FranKenstein bridge, waits for its receipt,
and returns correlated evidence to OMEGA.

Security note: ``dangerous_exec`` is a fail-closed *pre-dispatch* guard for forbidden
command classes. It is not advertised as an OS/syscall sandbox. Execution success is
accepted only when the Local Bridge receipt is cryptographically correlated to the
exact command bytes and the exact machine/owner/op/command_id tuple.
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
    r"(voice_action_guard\.py|ALIGNMENT_KERNEL\.md|effect_executor_interlock\.py|"
    r"omega[/\\]alignment\.py|omega_grid_relay\.py|omega_chatgpt_mcp\.py)$",
    re.I,
)


class ReceiptVerificationError(RuntimeError):
    """Typed receipt rejection; a rejected receipt can never mint effect PASS."""

    def __init__(self, code: str, message: str | None = None):
        super().__init__(message or code)
        self.code = code
        self.message = message or code


def canonical(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(obj: Any) -> str:
    return hashlib.sha256(canonical(obj)).hexdigest()


def serialized_local_command(command: dict[str, Any]) -> bytes:
    """Return the exact bytes submitted to the Local Bridge command branch."""
    return json.dumps(command, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"


def command_sha256(command_bytes: bytes) -> str:
    return hashlib.sha256(command_bytes).hexdigest()


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
    """Pre-dispatch denylist for explicit destructive command classes.

    This is deliberately not called a kernel/syscall guarantee. A future host-level
    guard may add stronger enforcement, but this relay must never overclaim that
    regex inspection can police arbitrary shell indirection.
    """
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


def verify_local_receipt(
    target: dict[str, str],
    command: dict[str, Any],
    command_bytes: bytes,
    receipt: dict[str, Any],
    *,
    require_pass: bool = True,
) -> dict[str, Any]:
    """Bind a receipt to the exact dispatched bytes and execution subject.

    PASS is impossible unless all of these match: schema, machine_id, owner,
    command_id, op, command_sha256, status and exit_code. This prevents a stale,
    cross-host or same-ID/different-bytes receipt from being promoted.
    """
    if not isinstance(receipt, dict):
        raise ReceiptVerificationError("INVALID_RECEIPT_TYPE")
    if receipt.get("schema") != "CLAY_LOCAL_RECEIPT/v1":
        raise ReceiptVerificationError("RECEIPT_SCHEMA_MISMATCH")

    expected_machine = str(target["machine_id"]).strip().lower()
    expected_owner = str(target["owner"]).strip().lower()
    machine = str(receipt.get("machine_id") or "").strip().lower()
    owner = str(receipt.get("owner") or "").strip().lower()
    if machine != expected_machine or owner != expected_owner:
        raise ReceiptVerificationError(
            "RECEIPT_IDENTITY_MISMATCH",
            f"expected {expected_machine}/{expected_owner}, got {machine}/{owner}",
        )

    expected_command_id = str(command["command_id"])
    received_command_id = str(receipt.get("command_id") or "")
    if received_command_id != expected_command_id:
        raise ReceiptVerificationError(
            "RECEIPT_COMMAND_MISMATCH",
            f"expected {expected_command_id}, got {received_command_id or '<missing>'}",
        )

    expected_op = str(command["op"])
    received_op = str(receipt.get("op") or "")
    if received_op != expected_op:
        raise ReceiptVerificationError(
            "RECEIPT_OP_MISMATCH",
            f"expected {expected_op}, got {received_op or '<missing>'}",
        )

    expected_sha = command_sha256(command_bytes)
    received_sha = str(receipt.get("command_sha256") or "").lower()
    if received_sha != expected_sha:
        raise ReceiptVerificationError(
            "RECEIPT_COMMAND_DIGEST_MISMATCH",
            f"expected {expected_sha}, got {received_sha or '<missing>'}",
        )

    status = str(receipt.get("status") or "UNKNOWN").upper()
    if require_pass and status != "PASS":
        raise ReceiptVerificationError("RECEIPT_NOT_PASS", f"status={status}")

    if status == "PASS":
        try:
            exit_code = int(receipt.get("exit_code"))
        except (TypeError, ValueError):
            raise ReceiptVerificationError("RECEIPT_EXIT_CODE_MISSING") from None
        if exit_code != 0:
            raise ReceiptVerificationError("RECEIPT_EXIT_CODE_MISMATCH", f"exit_code={exit_code}")
        if receipt.get("errors"):
            raise ReceiptVerificationError("RECEIPT_ERRORS_PRESENT")

    return receipt


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


def _unknown_evidence(reason: str, raw: bytes | None = None, receipt: dict[str, Any] | None = None) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "schema": "OMEGA_RELAY_REJECTION/v1",
        "reason": reason,
    }
    if raw is not None:
        evidence["raw_receipt_sha256"] = hashlib.sha256(raw).hexdigest()
    if receipt is not None:
        evidence["receipt"] = receipt
    return evidence


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
        gate = {"decision":"DENY","reason":"REQUEST_DIGEST_MISMATCH","decision_id":"gate_"+uuid.uuid4().hex,"authority_ref":"omega-grid-relay/v2"}
        return_to_omega(effect, "DENIED", gate, None)
        return

    try:
        cid, command, _op = build_local_command(effect)
    except PermissionError as exc:
        reason = str(exc)
        decision = "REQUIRE_CONFIRMATION" if reason == "REQUIRE_CONFIRMATION" else ("DEGRADE_TO_PROPOSAL" if reason == "DEGRADE_TO_PROPOSAL" else "DENY")
        gate = {"decision":decision,"reason":reason,"decision_id":"gate_"+uuid.uuid4().hex,"authority_ref":"omega-grid-relay/v2"}
        return_to_omega(effect, decision, gate, None)
        return

    target = ORGAN[effect["organ_id"]]
    command_bytes = serialized_local_command(command)
    command_digest = command_sha256(command_bytes)
    gate = {
        "decision":"ALLOW",
        "reason":"EXACT_BOUND_REQUEST_ADMITTED",
        "decision_id":"gate_"+uuid.uuid4().hex,
        "authority_ref":"omega-grid-relay/v2",
        "effect_id":effect["effect_id"],
        "organ_id":effect["organ_id"],
        "machine_id":target["machine_id"],
        "owner":target["owner"],
        "command_id":cid,
        "command_sha256":command_digest,
        "request_sha256":claimed,
        "effect_guard":"PRE_DISPATCH_V1",
    }
    path = f"local_bridge/commands/{cid}.json"
    put_new(target["control"], path, command_bytes, f"omega effect: {effect['effect_id']}")
    raw = wait_file(target["results"], f"local_bridge/results/receipts/{cid}.json", 75)
    if raw is None:
        # UNKNOWN is terminal for automatic execution. Reconciliation may inspect the
        # immutable command/receipt later, but this relay never emits a second command.
        timeout_gate = dict(gate)
        timeout_gate["receipt_state"] = "RECEIPT_TIMEOUT_NO_REPLAY"
        return_to_omega(effect, "UNKNOWN", timeout_gate, _unknown_evidence("RECEIPT_TIMEOUT_NO_REPLAY"))
        return

    try:
        receipt = json.loads(raw)
    except Exception:
        bad_gate = dict(gate)
        bad_gate["receipt_state"] = "INVALID_RECEIPT_JSON"
        return_to_omega(effect, "UNKNOWN", bad_gate, _unknown_evidence("INVALID_RECEIPT_JSON", raw=raw))
        return

    try:
        verify_local_receipt(target, command, command_bytes, receipt, require_pass=True)
    except ReceiptVerificationError as exc:
        bad_gate = dict(gate)
        bad_gate["receipt_state"] = exc.code
        return_to_omega(effect, "UNKNOWN", bad_gate, _unknown_evidence(exc.code, raw=raw, receipt=receipt))
        return

    verified_gate = dict(gate)
    verified_gate["receipt_state"] = "EXACT_CORRELATED_PASS"
    return_to_omega(effect, "PASS", verified_gate, receipt)


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
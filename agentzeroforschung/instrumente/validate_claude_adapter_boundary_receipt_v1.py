#!/usr/bin/env python3
import hashlib
import json
import re
import sys
from pathlib import Path

SCHEMA = "CLAUDE_ADAPTER_BOUNDARY_RECEIPT/v1"
BOUNDARIES = ("tool_less", "ephemeral", "structured_output", "env_isolation")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")

class ReceiptError(ValueError):
    pass

def fail(msg):
    raise ReceiptError(msg)

def need(cond, msg):
    if not cond:
        fail(msg)

def is_nonplaceholder_hex(value, rx):
    if not isinstance(value, str) or not rx.fullmatch(value):
        return False
    return len(set(value)) > 1

def canonical_sha256(obj):
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()

def validate_common(common):
    need(isinstance(common, dict), "common must be object")
    need(is_nonplaceholder_hex(common.get("source_commit"), SHA40), "source_commit invalid/placeholder")
    need(is_nonplaceholder_hex(common.get("source_tree"), SHA40), "source_tree invalid/placeholder")
    need(common.get("dirty") is False, "dirty source not admissible")
    need(is_nonplaceholder_hex(common.get("claude_binary_sha256"), SHA256), "claude_binary_sha256 invalid/placeholder")
    need(isinstance(common.get("claude_version"), str) and common["claude_version"].strip(), "claude_version missing")
    need(is_nonplaceholder_hex(common.get("command_sha256"), SHA256), "command_sha256 invalid/placeholder")
    need(is_nonplaceholder_hex(common.get("input_sha256"), SHA256), "input_sha256 invalid/placeholder")
    need(isinstance(common.get("executor"), dict), "executor missing")
    ex = common["executor"]
    for key in ("os", "arch", "runtime"):
        need(isinstance(ex.get(key), str) and ex[key].strip(), f"executor.{key} missing")
    need(isinstance(common.get("started_at"), str) and common["started_at"].strip(), "started_at missing")
    need(isinstance(common.get("finished_at"), str) and common["finished_at"].strip(), "finished_at missing")
    return canonical_sha256(common)

def validate_boundary(name, b, common_digest):
    need(isinstance(b, dict), f"{name} must be object")
    need(b.get("schema") == name.upper() + "_RECEIPT/v1", f"{name} schema mismatch")
    need(b.get("common_identity_sha256") == common_digest, f"{name} common identity mismatch")
    need(b.get("measured") is True, f"{name} is not measured")
    need(b.get("status") == "PASS", f"{name} status is not PASS")
    need(is_nonplaceholder_hex(b.get("stdout_sha256"), SHA256), f"{name} stdout digest invalid")
    need(is_nonplaceholder_hex(b.get("stderr_sha256"), SHA256), f"{name} stderr digest invalid")

    if name == "tool_less":
        need(b.get("built_in_tools_enabled") is False, "built-in tools enabled")
        need(b.get("bash_enabled") is False, "bash enabled")
        need(b.get("mcp_servers") == [], "unexpected MCP server")
        need(b.get("tool_invocation_count") == 0, "tool invocation observed")
    elif name == "ephemeral":
        need(b.get("persistent_session_reused") is False, "persistent Claude session reused")
        need(b.get("prompt_history_written") is False, "prompt history written")
        need(b.get("auto_memory_written") is False, "auto memory written")
        need(b.get("temporary_home_created") is True, "temporary HOME not created")
        need(b.get("temporary_home_removed") is True, "temporary HOME not removed")
    elif name == "structured_output":
        need(b.get("parse_ok") is True, "structured parse failed")
        need(b.get("candidate_only") is True, "result not typed candidate-only")
        need(b.get("canonical_write_attempted") is False, "adapter attempted canonical write")
        need(is_nonplaceholder_hex(b.get("result_sha256"), SHA256), "result digest invalid")
        need(isinstance(b.get("result_schema"), str) and b["result_schema"].strip(), "result schema missing")
    elif name == "env_isolation":
        allowed = b.get("allowed_env_keys")
        observed = b.get("observed_child_env_keys")
        need(isinstance(allowed, list) and all(isinstance(x, str) for x in allowed), "allowed_env_keys invalid")
        need(isinstance(observed, list) and all(isinstance(x, str) for x in observed), "observed_child_env_keys invalid")
        need(len(allowed) == len(set(allowed)), "allowed_env_keys duplicate")
        need(len(observed) == len(set(observed)), "observed_child_env_keys duplicate")
        need(set(observed).issubset(set(allowed)), "child env exceeds allowlist")
        need(b.get("forbidden_key_count") == 0, "forbidden env key observed")
        need(b.get("secret_value_leak_count") == 0, "secret value leak observed")
        need(is_nonplaceholder_hex(b.get("environment_shape_sha256"), SHA256), "environment shape digest invalid")

def validate(doc):
    need(isinstance(doc, dict), "receipt must be object")
    need(doc.get("schema") == SCHEMA, "top-level schema mismatch")
    common = doc.get("common")
    common_digest = validate_common(common)
    need(doc.get("common_identity_sha256") == common_digest, "top-level common identity mismatch")
    boundaries = doc.get("boundaries")
    need(isinstance(boundaries, dict), "boundaries must be object")
    need(set(boundaries) == set(BOUNDARIES), "exact four boundary receipts required")
    for name in BOUNDARIES:
        validate_boundary(name, boundaries[name], common_digest)
    need(doc.get("aggregate_status") == "PASS", "aggregate_status must be PASS")
    need(doc.get("runtime_credit") == "CLAUDE_ADAPTER_BOUNDARY_ONLY", "runtime_credit scope mismatch")
    need(doc.get("whole_product_credit") == 0, "whole product credit must remain zero")
    return {"ok": True, "schema": SCHEMA, "common_identity_sha256": common_digest, "boundaries": list(BOUNDARIES)}

def main(argv):
    if len(argv) != 2:
        print("usage: validate_claude_adapter_boundary_receipt_v1.py RECEIPT.json", file=sys.stderr)
        return 2
    try:
        doc = json.loads(Path(argv[1]).read_text(encoding="utf-8"), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        result = validate(doc)
    except (OSError, json.JSONDecodeError, ValueError, ReceiptError) as e:
        print(json.dumps({"ok": False, "error": str(e)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

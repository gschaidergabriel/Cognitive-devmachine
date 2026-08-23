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
INVOCATION_ID = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")

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
    need(isinstance(common.get("invocation_id"), str) and INVOCATION_ID.fullmatch(common["invocation_id"]), "invocation_id invalid")
    need(isinstance(common.get("executor"), dict), "executor missing")
    ex = common["executor"]
    for key in ("os", "arch", "runtime"):
        need(isinstance(ex.get(key), str) and ex[key].strip(), f"executor.{key} missing")
    need(isinstance(common.get("started_at"), str) and common["started_at"].strip(), "started_at missing")
    need(isinstance(common.get("finished_at"), str) and common["finished_at"].strip(), "finished_at missing")
    return canonical_sha256(common)

def validate_boundary_shape(name, b, common_digest):
    need(isinstance(b, dict), f"{name} must be object")
    need(b.get("schema") == name.upper() + "_RECEIPT/v1", f"{name} schema mismatch")
    need(b.get("common_identity_sha256") == common_digest, f"{name} common identity mismatch")
    need(b.get("measured") is True, f"{name} is not measured")
    need(b.get("status") in {"PASS", "FAIL"}, f"{name} status invalid")
    need(is_nonplaceholder_hex(b.get("stdout_sha256"), SHA256), f"{name} stdout digest invalid")
    need(is_nonplaceholder_hex(b.get("stderr_sha256"), SHA256), f"{name} stderr digest invalid")

def boundary_violations(name, b):
    violations = []
    if name == "tool_less":
        need(isinstance(b.get("built_in_tools_enabled"), bool), "built_in_tools_enabled invalid")
        need(isinstance(b.get("bash_enabled"), bool), "bash_enabled invalid")
        need(isinstance(b.get("mcp_servers"), list) and all(isinstance(x, str) for x in b["mcp_servers"]), "mcp_servers invalid")
        need(isinstance(b.get("tool_invocation_count"), int) and not isinstance(b.get("tool_invocation_count"), bool) and b["tool_invocation_count"] >= 0, "tool_invocation_count invalid")
        if b["built_in_tools_enabled"]: violations.append("BUILT_IN_TOOLS_ENABLED")
        if b["bash_enabled"]: violations.append("BASH_ENABLED")
        if b["mcp_servers"]: violations.append("UNEXPECTED_MCP_SERVER")
        if b["tool_invocation_count"] != 0: violations.append("TOOL_INVOCATION_OBSERVED")
    elif name == "ephemeral":
        for key in ("persistent_session_reused", "prompt_history_written", "auto_memory_written", "temporary_home_created", "temporary_home_removed"):
            need(isinstance(b.get(key), bool), f"{key} invalid")
        if b["persistent_session_reused"]: violations.append("PERSISTENT_SESSION_REUSED")
        if b["prompt_history_written"]: violations.append("PROMPT_HISTORY_WRITTEN")
        if b["auto_memory_written"]: violations.append("AUTO_MEMORY_WRITTEN")
        if not b["temporary_home_created"]: violations.append("TEMPORARY_HOME_NOT_CREATED")
        if not b["temporary_home_removed"]: violations.append("TEMPORARY_HOME_NOT_REMOVED")
    elif name == "structured_output":
        for key in ("parse_ok", "candidate_only", "canonical_write_attempted"):
            need(isinstance(b.get(key), bool), f"{key} invalid")
        if b["parse_ok"]:
            need(is_nonplaceholder_hex(b.get("result_sha256"), SHA256), "result digest invalid")
            need(isinstance(b.get("result_schema"), str) and b["result_schema"].strip(), "result schema missing")
        if not b["parse_ok"]: violations.append("STRUCTURED_PARSE_FAILED")
        if not b["candidate_only"]: violations.append("RESULT_NOT_CANDIDATE_ONLY")
        if b["canonical_write_attempted"]: violations.append("CANONICAL_WRITE_ATTEMPTED")
    elif name == "env_isolation":
        allowed = b.get("allowed_env_keys")
        observed = b.get("observed_child_env_keys")
        need(isinstance(allowed, list) and all(isinstance(x, str) for x in allowed), "allowed_env_keys invalid")
        need(isinstance(observed, list) and all(isinstance(x, str) for x in observed), "observed_child_env_keys invalid")
        need(len(allowed) == len(set(allowed)), "allowed_env_keys duplicate")
        need(len(observed) == len(set(observed)), "observed_child_env_keys duplicate")
        need(isinstance(b.get("forbidden_key_count"), int) and not isinstance(b.get("forbidden_key_count"), bool) and b["forbidden_key_count"] >= 0, "forbidden_key_count invalid")
        need(isinstance(b.get("secret_value_leak_count"), int) and not isinstance(b.get("secret_value_leak_count"), bool) and b["secret_value_leak_count"] >= 0, "secret_value_leak_count invalid")
        need(is_nonplaceholder_hex(b.get("environment_shape_sha256"), SHA256), "environment shape digest invalid")
        if not set(observed).issubset(set(allowed)): violations.append("CHILD_ENV_EXCEEDS_ALLOWLIST")
        if b["forbidden_key_count"] != 0: violations.append("FORBIDDEN_ENV_KEY_OBSERVED")
        if b["secret_value_leak_count"] != 0: violations.append("SECRET_VALUE_LEAK_OBSERVED")
    return violations

def diagnose(doc):
    need(isinstance(doc, dict), "receipt must be object")
    need(doc.get("schema") == SCHEMA, "top-level schema mismatch")
    common = doc.get("common")
    common_digest = validate_common(common)
    need(doc.get("common_identity_sha256") == common_digest, "top-level common identity mismatch")
    boundaries = doc.get("boundaries")
    need(isinstance(boundaries, dict), "boundaries must be object")
    need(set(boundaries) == set(BOUNDARIES), "exact four boundary receipts required")
    details = {}
    failing = []
    invocation_stdout = None
    invocation_stderr = None
    for name in BOUNDARIES:
        b = boundaries[name]
        validate_boundary_shape(name, b, common_digest)
        if invocation_stdout is None:
            invocation_stdout = b["stdout_sha256"]
            invocation_stderr = b["stderr_sha256"]
        else:
            need(b["stdout_sha256"] == invocation_stdout, "cross-bound stdout digest mismatch")
            need(b["stderr_sha256"] == invocation_stderr, "cross-bound stderr digest mismatch")
        violations = boundary_violations(name, b)
        derived = "PASS" if not violations else "FAIL"
        need(b.get("status") == derived, f"{name} status does not match measured observations")
        details[name] = violations
        if violations:
            failing.append(name)
    aggregate = "PASS" if not failing else "FAIL"
    need(doc.get("aggregate_status") == aggregate, "aggregate_status does not match boundary observations")
    expected_credit = "CLAUDE_ADAPTER_BOUNDARY_ONLY" if aggregate == "PASS" else "ZERO"
    need(doc.get("runtime_credit") == expected_credit, "runtime_credit scope mismatch")
    need(doc.get("whole_product_credit") == 0, "whole product credit must remain zero")
    return {
        "ok": True,
        "schema": SCHEMA,
        "common_identity_sha256": common_digest,
        "aggregate_status": aggregate,
        "promotion_eligible": aggregate == "PASS",
        "failing_boundaries": failing,
        "violations": details,
    }

def validate(doc):
    result = diagnose(doc)
    need(result["aggregate_status"] == "PASS", "aggregate_status must be PASS")
    return {"ok": True, "schema": SCHEMA, "common_identity_sha256": result["common_identity_sha256"], "boundaries": list(BOUNDARIES)}

def main(argv):
    diagnostic = False
    args = list(argv[1:])
    if args and args[0] == "--diagnostic":
        diagnostic = True
        args.pop(0)
    if len(args) != 1:
        print("usage: validate_claude_adapter_boundary_receipt_v1.py [--diagnostic] RECEIPT.json", file=sys.stderr)
        return 2
    try:
        doc = json.loads(Path(args[0]).read_text(encoding="utf-8"), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        result = diagnose(doc) if diagnostic else validate(doc)
    except (OSError, json.JSONDecodeError, ValueError, ReceiptError) as e:
        print(json.dumps({"ok": False, "error": str(e)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
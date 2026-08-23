#!/usr/bin/env python3
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "CLAUDE_ADAPTER_BOUNDARY_RECEIPT/v2"
BOUNDARIES = ("tool_less", "ephemeral", "structured_output", "env_isolation")
PERSISTENCE_SCOPE_SCHEMA = "CLAUDE_USER_PERSISTENCE_SURFACE/v1"
PERSISTENCE_SCOPE_KINDS = ["auto_memory", "prompt_history", "transcripts"]
CANONICAL_ENV_ALLOWLIST = frozenset({
    "PATH", "HOME", "LANG", "LC_ALL", "TMPDIR",
    "SSL_CERT_FILE", "SSL_CERT_DIR", "NODE_EXTRA_CA_CERTS",
    "HTTP_PROXY", "HTTPS_PROXY",
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
    "DISABLE_AUTOUPDATER", "CLAUDE_CODE_SKIP_PROMPT_HISTORY",
    "CLAUDE_CODE_DISABLE_AUTO_MEMORY", "CLAUDE_CODE_DISABLE_CLAUDE_MDS",
})
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
    try:
        started = datetime.fromisoformat(common["started_at"].replace("Z", "+00:00"))
        finished = datetime.fromisoformat(common["finished_at"].replace("Z", "+00:00"))
    except ValueError:
        fail("started_at/finished_at must be ISO-8601 timestamps")
    need(started.tzinfo is not None and finished.tzinfo is not None, "started_at/finished_at must be timezone-aware")
    need(started.utcoffset() == timezone.utc.utcoffset(started), "started_at must be UTC")
    need(finished.utcoffset() == timezone.utc.utcoffset(finished), "finished_at must be UTC")
    need(finished >= started, "finished_at precedes started_at")
    return canonical_sha256(common)


def validate_boundary_shape(name, b, common_digest):
    need(isinstance(b, dict), f"{name} must be object")
    need(b.get("schema") == name.upper() + "_RECEIPT/v2", f"{name} schema mismatch")
    need(b.get("common_identity_sha256") == common_digest, f"{name} common identity mismatch")
    need(b.get("measured") is True, f"{name} is not measured")
    need(b.get("status") in {"PASS", "FAIL"}, f"{name} status invalid")
    need(is_nonplaceholder_hex(b.get("stdout_sha256"), SHA256), f"{name} stdout digest invalid")
    need(is_nonplaceholder_hex(b.get("stderr_sha256"), SHA256), f"{name} stderr digest invalid")


def _nonnegative_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def boundary_violations(name, b):
    violations = []
    if name == "tool_less":
        need(isinstance(b.get("built_in_tools_enabled"), bool), "built_in_tools_enabled invalid")
        need(isinstance(b.get("bash_enabled"), bool), "bash_enabled invalid")
        need(isinstance(b.get("mcp_servers"), list) and all(isinstance(x, str) for x in b["mcp_servers"]), "mcp_servers invalid")
        need(_nonnegative_int(b.get("tool_invocation_count")), "tool_invocation_count invalid")
        if b["built_in_tools_enabled"]: violations.append("BUILT_IN_TOOLS_ENABLED")
        if b["bash_enabled"]: violations.append("BASH_ENABLED")
        if b["mcp_servers"]: violations.append("UNEXPECTED_MCP_SERVER")
        if b["tool_invocation_count"] != 0: violations.append("TOOL_INVOCATION_OBSERVED")
    elif name == "ephemeral":
        bool_keys = (
            "persistent_session_reused", "no_session_persistence_requested",
            "prompt_history_suppressed", "auto_memory_disabled", "claude_mds_disabled",
            "auth_home_retained", "persistence_measurement_complete",
        )
        for key in bool_keys:
            need(isinstance(b.get(key), bool), f"{key} invalid")
        need(is_nonplaceholder_hex(b.get("home_identity_sha256"), SHA256), "home_identity_sha256 invalid")
        need(isinstance(b.get("persistence_scope_schema"), str), "persistence_scope_schema invalid")
        need(isinstance(b.get("persistence_scope_kinds"), list) and all(isinstance(x, str) for x in b["persistence_scope_kinds"]), "persistence_scope_kinds invalid")
        need(len(b["persistence_scope_kinds"]) == len(set(b["persistence_scope_kinds"])), "persistence_scope_kinds duplicate")
        need(is_nonplaceholder_hex(b.get("persistence_before_sha256"), SHA256), "persistence_before_sha256 invalid")
        need(is_nonplaceholder_hex(b.get("persistence_after_sha256"), SHA256), "persistence_after_sha256 invalid")
        for key in ("transcript_write_count", "prompt_history_write_count", "auto_memory_write_count"):
            need(_nonnegative_int(b.get(key)), f"{key} invalid")
        if b["persistent_session_reused"]: violations.append("PERSISTENT_SESSION_REUSED")
        if not b["no_session_persistence_requested"]: violations.append("NO_SESSION_PERSISTENCE_NOT_REQUESTED")
        if not b["prompt_history_suppressed"]: violations.append("PROMPT_HISTORY_NOT_SUPPRESSED")
        if not b["auto_memory_disabled"]: violations.append("AUTO_MEMORY_NOT_DISABLED")
        if not b["claude_mds_disabled"]: violations.append("CLAUDE_MDS_NOT_DISABLED")
        if not b["auth_home_retained"]: violations.append("AUTH_HOME_RETENTION_NOT_BOUND")
        if not b["persistence_measurement_complete"]: violations.append("PERSISTENCE_MEASUREMENT_INCOMPLETE")
        if b["persistence_scope_schema"] != PERSISTENCE_SCOPE_SCHEMA: violations.append("PERSISTENCE_SCOPE_SCHEMA_MISMATCH")
        if b["persistence_scope_kinds"] != PERSISTENCE_SCOPE_KINDS: violations.append("PERSISTENCE_SCOPE_INCOMPLETE")
        if b["persistence_before_sha256"] != b["persistence_after_sha256"]: violations.append("PERSISTENCE_SURFACE_CHANGED")
        if b["transcript_write_count"] != 0: violations.append("TRANSCRIPT_WRITE_OBSERVED")
        if b["prompt_history_write_count"] != 0: violations.append("PROMPT_HISTORY_WRITE_OBSERVED")
        if b["auto_memory_write_count"] != 0: violations.append("AUTO_MEMORY_WRITE_OBSERVED")
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
        need(set(allowed).issubset(CANONICAL_ENV_ALLOWLIST), "allowed_env_keys exceed canonical Claude child policy")
        need(_nonnegative_int(b.get("forbidden_key_count")), "forbidden_key_count invalid")
        need(_nonnegative_int(b.get("secret_value_leak_count")), "secret_value_leak_count invalid")
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
    stream_digests = {"stdout_sha256": set(), "stderr_sha256": set()}
    for name in BOUNDARIES:
        b = boundaries[name]
        validate_boundary_shape(name, b, common_digest)
        for stream_field in stream_digests:
            stream_digests[stream_field].add(b[stream_field])
        violations = boundary_violations(name, b)
        derived = "PASS" if not violations else "FAIL"
        need(b.get("status") == derived, f"{name} status does not match measured observations")
        details[name] = violations
        if violations:
            failing.append(name)
    for stream_field, digests in stream_digests.items():
        need(len(digests) == 1, f"boundary {stream_field} mismatch")
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
        print("usage: validate_claude_adapter_boundary_receipt_v2.py [--diagnostic] RECEIPT.json", file=sys.stderr)
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

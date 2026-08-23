#!/usr/bin/env python3
import hashlib
import json
import re
import sys
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


def need(condition, message):
    if not condition:
        raise ReceiptError(message)


def is_nonplaceholder_hex(value, pattern):
    return isinstance(value, str) and pattern.fullmatch(value) is not None and len(set(value)) > 1


def canonical_sha256(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def validate_common(common):
    need(isinstance(common, dict), "common must be object")
    need(is_nonplaceholder_hex(common.get("source_commit"), SHA40), "source_commit invalid/placeholder")
    need(is_nonplaceholder_hex(common.get("source_tree"), SHA40), "source_tree invalid/placeholder")
    need(common.get("dirty") is False, "dirty source not admissible")
    need(is_nonplaceholder_hex(common.get("claude_binary_sha256"), SHA256), "claude binary digest invalid")
    need(isinstance(common.get("claude_version"), str) and common["claude_version"].strip(), "claude version missing")
    need(is_nonplaceholder_hex(common.get("command_sha256"), SHA256), "command digest invalid")
    need(is_nonplaceholder_hex(common.get("input_sha256"), SHA256), "input digest invalid")
    executor = common.get("executor")
    need(isinstance(executor, dict), "executor missing")
    for key in ("os", "arch", "runtime"):
        need(isinstance(executor.get(key), str) and executor[key].strip(), f"executor.{key} missing")
    need(isinstance(common.get("started_at"), str) and common["started_at"].strip(), "started_at missing")
    need(isinstance(common.get("finished_at"), str) and common["finished_at"].strip(), "finished_at missing")
    return canonical_sha256(common)


def validate_base(name, boundary, common_digest):
    need(isinstance(boundary, dict), f"{name} must be object")
    need(boundary.get("schema") == name.upper() + "_RECEIPT/v2", f"{name} schema mismatch")
    need(boundary.get("common_identity_sha256") == common_digest, f"{name} common identity mismatch")
    need(boundary.get("measured") is True, f"{name} unmeasured")
    need(boundary.get("status") == "PASS", f"{name} status not PASS")
    need(is_nonplaceholder_hex(boundary.get("stdout_sha256"), SHA256), f"{name} stdout digest invalid")
    need(is_nonplaceholder_hex(boundary.get("stderr_sha256"), SHA256), f"{name} stderr digest invalid")


def validate_tool_less(boundary):
    need(boundary.get("built_in_tools_enabled") is False, "built-in tools enabled")
    need(boundary.get("bash_enabled") is False, "bash enabled")
    need(boundary.get("mcp_servers") == [], "unexpected MCP server")
    need(boundary.get("tool_invocation_count") == 0, "tool invocation observed")


def validate_ephemeral(boundary):
    need(boundary.get("persistent_session_reused") is False, "persistent session reused")
    need(boundary.get("no_session_persistence_requested") is True, "no-session-persistence not measured")
    need(boundary.get("prompt_history_suppressed") is True, "prompt history not suppressed")
    need(boundary.get("auto_memory_disabled") is True, "auto memory not disabled")
    need(boundary.get("claude_mds_disabled") is True, "CLAUDE.md memory inputs not disabled")
    need(boundary.get("auth_home_retained") is True, "retained auth HOME not acknowledged")
    need(is_nonplaceholder_hex(boundary.get("home_identity_sha256"), SHA256), "HOME identity digest invalid")
    need(boundary.get("persistence_measurement_complete") is True, "persistence measurement incomplete")
    need(boundary.get("persistence_scope_schema") == PERSISTENCE_SCOPE_SCHEMA, "persistence scope schema mismatch")
    need(boundary.get("persistence_scope_kinds") == PERSISTENCE_SCOPE_KINDS, "persistence scope kinds mismatch")
    before = boundary.get("persistence_before_sha256")
    after = boundary.get("persistence_after_sha256")
    need(is_nonplaceholder_hex(before, SHA256), "pre-run persistence digest invalid")
    need(is_nonplaceholder_hex(after, SHA256), "post-run persistence digest invalid")
    need(before == after, "Claude cognition persistence surface changed")
    need(boundary.get("transcript_write_count") == 0, "transcript write observed")
    need(boundary.get("prompt_history_write_count") == 0, "prompt-history write observed")
    need(boundary.get("auto_memory_write_count") == 0, "auto-memory write observed")


def validate_structured(boundary):
    need(boundary.get("parse_ok") is True, "structured parse failed")
    need(boundary.get("candidate_only") is True, "result not candidate-only")
    need(boundary.get("canonical_write_attempted") is False, "adapter attempted canonical write")
    need(is_nonplaceholder_hex(boundary.get("result_sha256"), SHA256), "result digest invalid")
    need(isinstance(boundary.get("result_schema"), str) and boundary["result_schema"].strip(), "result schema missing")


def validate_env(boundary):
    allowed = boundary.get("allowed_env_keys")
    observed = boundary.get("observed_child_env_keys")
    need(isinstance(allowed, list) and all(isinstance(x, str) for x in allowed), "allowed env invalid")
    need(isinstance(observed, list) and all(isinstance(x, str) for x in observed), "observed env invalid")
    need(len(allowed) == len(set(allowed)), "allowed env duplicate")
    need(len(observed) == len(set(observed)), "observed env duplicate")
    need(set(allowed).issubset(CANONICAL_ENV_ALLOWLIST), "allowed env exceeds canonical Claude child policy")
    need(set(observed).issubset(set(allowed)), "child env exceeds declared allowlist")
    need(boundary.get("forbidden_key_count") == 0, "forbidden env key observed")
    need(boundary.get("secret_value_leak_count") == 0, "secret value leak observed")
    need(is_nonplaceholder_hex(boundary.get("environment_shape_sha256"), SHA256), "environment shape digest invalid")


def validate(doc):
    need(isinstance(doc, dict), "receipt must be object")
    need(doc.get("schema") == SCHEMA, "top-level schema mismatch")
    common_digest = validate_common(doc.get("common"))
    need(doc.get("common_identity_sha256") == common_digest, "top-level common identity mismatch")
    boundaries = doc.get("boundaries")
    need(isinstance(boundaries, dict) and set(boundaries) == set(BOUNDARIES), "exact four boundaries required")
    for name in BOUNDARIES:
        boundary = boundaries[name]
        validate_base(name, boundary, common_digest)
        if name == "tool_less":
            validate_tool_less(boundary)
        elif name == "ephemeral":
            validate_ephemeral(boundary)
        elif name == "structured_output":
            validate_structured(boundary)
        else:
            validate_env(boundary)
    need(doc.get("aggregate_status") == "PASS", "aggregate status must be PASS")
    need(doc.get("runtime_credit") == "CLAUDE_ADAPTER_BOUNDARY_ONLY", "runtime credit scope mismatch")
    need(doc.get("whole_product_credit") == 0, "whole product credit must remain zero")
    return {"ok": True, "schema": SCHEMA, "common_identity_sha256": common_digest}


def main(argv):
    if len(argv) != 2:
        print("usage: validate_claude_adapter_boundary_receipt_v2.py RECEIPT.json", file=sys.stderr)
        return 2
    try:
        doc = json.loads(Path(argv[1]).read_text(encoding="utf-8"), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        print(json.dumps(validate(doc), sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, ValueError, ReceiptError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

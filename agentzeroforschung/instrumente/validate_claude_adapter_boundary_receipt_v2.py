#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "CLAUDE_ADAPTER_BOUNDARY_RECEIPT/v2"
BOUNDARIES = ("tool_less", "memory_authority", "structured_output", "env_isolation")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_OID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
HOME_MODES = {"PERSISTENT_AUTH_ONLY", "TEMPORARY"}
CANONICAL_AMBIENT_ENV_ALLOWLIST = frozenset({
    "PATH", "HOME", "LANG", "LC_ALL", "TMPDIR",
    "SSL_CERT_FILE", "SSL_CERT_DIR", "NODE_EXTRA_CA_CERTS",
    "HTTP_PROXY", "HTTPS_PROXY",
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
})
CANONICAL_GENERATED_POLICY_ENV = {
    "DISABLE_AUTOUPDATER": "1",
    "CLAUDE_CODE_SKIP_PROMPT_HISTORY": "1",
    "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
    "CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1",
}
REQUIRED_MEMORY_ENV = {
    key: CANONICAL_GENERATED_POLICY_ENV[key]
    for key in (
        "CLAUDE_CODE_SKIP_PROMPT_HISTORY",
        "CLAUDE_CODE_DISABLE_AUTO_MEMORY",
        "CLAUDE_CODE_DISABLE_CLAUDE_MDS",
    )
}


class ReceiptError(ValueError):
    pass


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ReceiptError(message)


def is_nonplaceholder_hex(value, rx) -> bool:
    return isinstance(value, str) and rx.fullmatch(value) is not None and len(set(value)) > 1


def canonical_sha256(obj) -> str:
    try:
        raw = json.dumps(
            obj,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ReceiptError(f"NONCANONICAL_JSON:{exc.__class__.__name__}") from exc
    return hashlib.sha256(raw).hexdigest()


def validate_common(common) -> str:
    need(isinstance(common, dict), "common must be object")
    need(is_nonplaceholder_hex(common.get("source_commit"), GIT_OID), "source_commit invalid/placeholder")
    need(is_nonplaceholder_hex(common.get("source_tree"), GIT_OID), "source_tree invalid/placeholder")
    need(common.get("dirty") is False, "dirty source not admissible")
    need(is_nonplaceholder_hex(common.get("claude_binary_sha256"), SHA256), "claude_binary_sha256 invalid/placeholder")
    need(isinstance(common.get("claude_version"), str) and common["claude_version"].strip(), "claude_version missing")
    need(is_nonplaceholder_hex(common.get("command_sha256"), SHA256), "command_sha256 invalid/placeholder")
    need(is_nonplaceholder_hex(common.get("input_sha256"), SHA256), "input_sha256 invalid/placeholder")
    executor = common.get("executor")
    need(isinstance(executor, dict), "executor missing")
    for key in ("os", "arch", "runtime"):
        need(isinstance(executor.get(key), str) and executor[key].strip(), f"executor.{key} missing")
    for key in ("started_at", "finished_at"):
        need(isinstance(common.get(key), str) and common[key].strip(), f"{key} missing")
    try:
        started = datetime.fromisoformat(common["started_at"].replace("Z", "+00:00"))
        finished = datetime.fromisoformat(common["finished_at"].replace("Z", "+00:00"))
    except ValueError:
        raise ReceiptError("started_at/finished_at must be ISO-8601 timestamps")
    need(started.tzinfo is not None and finished.tzinfo is not None, "started_at/finished_at must be timezone-aware")
    need(started.utcoffset() == timezone.utc.utcoffset(started), "started_at must be UTC")
    need(finished.utcoffset() == timezone.utc.utcoffset(finished), "finished_at must be UTC")
    need(finished >= started, "finished_at precedes started_at")
    return canonical_sha256(common)


def validate_boundary_shape(name: str, boundary, common_digest: str) -> None:
    need(isinstance(boundary, dict), f"{name} must be object")
    need(boundary.get("schema") == name.upper() + "_RECEIPT/v2", f"{name} schema mismatch")
    need(boundary.get("common_identity_sha256") == common_digest, f"{name} common identity mismatch")
    need(boundary.get("measured") is True, f"{name} is not measured")
    need(boundary.get("status") in {"PASS", "FAIL"}, f"{name} status invalid")
    need(is_nonplaceholder_hex(boundary.get("stdout_sha256"), SHA256), f"{name} stdout digest invalid")
    need(is_nonplaceholder_hex(boundary.get("stderr_sha256"), SHA256), f"{name} stderr digest invalid")


def boundary_violations(name: str, b) -> list[str]:
    violations: list[str] = []
    if name == "tool_less":
        for key in ("built_in_tools_enabled", "bash_enabled"):
            need(isinstance(b.get(key), bool), f"{key} invalid")
        need(isinstance(b.get("mcp_servers"), list) and all(isinstance(x, str) for x in b["mcp_servers"]), "mcp_servers invalid")
        count = b.get("tool_invocation_count")
        need(type(count) is int and count >= 0, "tool_invocation_count invalid")
        if b["built_in_tools_enabled"]:
            violations.append("BUILT_IN_TOOLS_ENABLED")
        if b["bash_enabled"]:
            violations.append("BASH_ENABLED")
        if b["mcp_servers"]:
            violations.append("UNEXPECTED_MCP_SERVER")
        if count:
            violations.append("TOOL_INVOCATION_OBSERVED")
    elif name == "memory_authority":
        for key in (
            "persistent_session_reused",
            "prompt_history_disabled",
            "auto_memory_disabled",
            "claude_md_memory_disabled",
        ):
            need(isinstance(b.get(key), bool), f"{key} invalid")
        need(b.get("home_mode") in HOME_MODES, "home_mode invalid")
        observed = b.get("observed_memory_env")
        need(isinstance(observed, dict), "observed_memory_env invalid")
        need(set(observed) == set(REQUIRED_MEMORY_ENV), "observed_memory_env keys mismatch")
        for key, expected in REQUIRED_MEMORY_ENV.items():
            need(observed.get(key) == expected, f"memory env fence missing:{key}")
        for key in ("memory_file_load_count", "memory_file_write_count"):
            value = b.get(key)
            need(type(value) is int and value >= 0, f"{key} invalid")
        if b["persistent_session_reused"]:
            violations.append("PERSISTENT_SESSION_REUSED")
        if not b["prompt_history_disabled"]:
            violations.append("PROMPT_HISTORY_ENABLED")
        if not b["auto_memory_disabled"]:
            violations.append("AUTO_MEMORY_ENABLED")
        if not b["claude_md_memory_disabled"]:
            violations.append("CLAUDE_MD_MEMORY_ENABLED")
        if b["memory_file_load_count"]:
            violations.append("MEMORY_FILE_LOADED")
        if b["memory_file_write_count"]:
            violations.append("MEMORY_FILE_WRITTEN")
    elif name == "structured_output":
        for key in ("parse_ok", "candidate_only", "canonical_write_attempted"):
            need(isinstance(b.get(key), bool), f"{key} invalid")
        if b["parse_ok"]:
            need(is_nonplaceholder_hex(b.get("result_sha256"), SHA256), "result digest invalid")
            need(isinstance(b.get("result_schema"), str) and b["result_schema"].strip(), "result schema missing")
        if not b["parse_ok"]:
            violations.append("STRUCTURED_PARSE_FAILED")
        if not b["candidate_only"]:
            violations.append("RESULT_NOT_CANDIDATE_ONLY")
        if b["canonical_write_attempted"]:
            violations.append("CANONICAL_WRITE_ATTEMPTED")
    elif name == "env_isolation":
        allowed = b.get("allowed_env_keys")
        observed = b.get("observed_child_env_keys")
        generated = b.get("generated_policy_env")
        need(isinstance(allowed, list) and all(isinstance(x, str) for x in allowed), "allowed_env_keys invalid")
        need(isinstance(observed, list) and all(isinstance(x, str) for x in observed), "observed_child_env_keys invalid")
        need(len(allowed) == len(set(allowed)), "allowed_env_keys duplicate")
        need(len(observed) == len(set(observed)), "observed_child_env_keys duplicate")
        need(set(allowed).issubset(CANONICAL_AMBIENT_ENV_ALLOWLIST), "allowed_env_keys exceed canonical Claude child policy")
        need(generated == CANONICAL_GENERATED_POLICY_ENV, "generated_policy_env differs from canonical Claude child policy")
        admitted = set(allowed) | set(CANONICAL_GENERATED_POLICY_ENV)
        if not set(observed).issubset(admitted):
            violations.append("CHILD_ENV_EXCEEDS_ADMITTED_KEYS")
        for key in ("forbidden_key_count", "secret_value_leak_count"):
            value = b.get(key)
            need(type(value) is int and value >= 0, f"{key} invalid")
        if b["forbidden_key_count"]:
            violations.append("FORBIDDEN_ENV_KEY_OBSERVED")
        if b["secret_value_leak_count"]:
            violations.append("SECRET_VALUE_LEAK_OBSERVED")
        need(is_nonplaceholder_hex(b.get("environment_shape_sha256"), SHA256), "environment shape digest invalid")
    return violations


def diagnose(doc) -> dict:
    need(isinstance(doc, dict), "receipt must be object")
    need(doc.get("schema") == SCHEMA, "top-level schema mismatch")
    common_digest = validate_common(doc.get("common"))
    need(doc.get("common_identity_sha256") == common_digest, "top-level common identity mismatch")
    boundaries = doc.get("boundaries")
    need(isinstance(boundaries, dict), "boundaries must be object")
    need(set(boundaries) == set(BOUNDARIES), "exact four v2 boundary receipts required")

    details = {}
    failing = []
    for name in BOUNDARIES:
        boundary = boundaries[name]
        validate_boundary_shape(name, boundary, common_digest)
        violations = boundary_violations(name, boundary)
        derived = "PASS" if not violations else "FAIL"
        need(boundary.get("status") == derived, f"{name} status does not match measured observations")
        details[name] = violations
        if violations:
            failing.append(name)

    aggregate = "PASS" if not failing else "FAIL"
    need(doc.get("aggregate_status") == aggregate, "aggregate_status does not match boundary observations")
    expected_credit = "CLAUDE_ADAPTER_BOUNDARY_ONLY" if aggregate == "PASS" else "ZERO"
    need(doc.get("runtime_credit") == expected_credit, "runtime_credit scope mismatch")
    need(doc.get("whole_product_credit") == 0, "whole product credit must remain zero")
    need(doc.get("v1_runtime_credit_accepted") is False, "v1 current runtime credit must be disabled")
    return {
        "ok": True,
        "schema": SCHEMA,
        "common_identity_sha256": common_digest,
        "aggregate_status": aggregate,
        "promotion_eligible": aggregate == "PASS",
        "failing_boundaries": failing,
        "violations": details,
    }


def validate(doc) -> dict:
    result = diagnose(doc)
    need(result["aggregate_status"] == "PASS", "aggregate_status must be PASS")
    return result


def main(argv: list[str]) -> int:
    diagnostic = False
    args = list(argv[1:])
    if args and args[0] == "--diagnostic":
        diagnostic = True
        args.pop(0)
    if len(args) != 1:
        print("usage: validate_claude_adapter_boundary_receipt_v2.py [--diagnostic] RECEIPT.json", file=sys.stderr)
        return 2
    try:
        doc = json.loads(
            Path(args[0]).read_text(encoding="utf-8"),
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
        )
        result = diagnose(doc) if diagnostic else validate(doc)
    except (OSError, json.JSONDecodeError, TypeError, ValueError, ReceiptError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

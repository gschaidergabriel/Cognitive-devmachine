#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SCHEMAS = {
    "tool_less": "TOOLLESS_RECEIPT/v1",
    "ephemeral": "EPHEMERAL_RECEIPT/v1",
    "structured_output": "STRUCTURED_OUTPUT_RECEIPT/v1",
    "env_isolation": "ENV_ISOLATION_RECEIPT/v1",
}


class ValidationError(ValueError):
    pass


def fail(code: str) -> None:
    raise ValidationError(code)


def req_obj(parent: dict, key: str) -> dict:
    value = parent.get(key)
    if not isinstance(value, dict):
        fail(f"MISSING_OBJECT:{key}")
    return value


def req_str(parent: dict, key: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        fail(f"MISSING_STRING:{key}")
    return value


def req_bool(parent: dict, key: str) -> bool:
    value = parent.get(key)
    if not isinstance(value, bool):
        fail(f"MISSING_BOOL:{key}")
    return value


def req_int(parent: dict, key: str, minimum: int = 0) -> int:
    value = parent.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        fail(f"INVALID_INT:{key}")
    return value


def req_sha(parent: dict, key: str, length: int = 64) -> str:
    value = req_str(parent, key)
    regex = HEX64 if length == 64 else HEX40
    if regex.fullmatch(value) is None:
        fail(f"INVALID_SHA{length}:{key}")
    if set(value) in ({"0"}, {"f"}):
        fail(f"PLACEHOLDER_SHA{length}:{key}")
    return value


def req_string_list(parent: dict, key: str) -> list[str]:
    value = parent.get(key)
    if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
        fail(f"INVALID_STRING_LIST:{key}")
    if value != sorted(set(value)):
        fail(f"NONCANONICAL_STRING_LIST:{key}")
    return value


def canonical_sha256(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class Binding:
    source_sha: str
    tree_sha: str
    dirty: bool
    dirty_diff_sha256: str | None
    test_run_id: str
    suite_digest: str
    executor_identity_sha256: str
    kernel: str
    claude_binary_sha256: str
    claude_version: str
    adapter_version: str
    adapter_sha256: str
    home_sha256: str
    environment_allowlist: tuple[str, ...]
    environment_sha256: str
    tool_mcp_config_sha256: str

    @property
    def digest(self) -> str:
        return canonical_sha256(self.__dict__)


def validate_common(data: dict) -> Binding:
    source = req_obj(data, "source")
    source_sha = req_sha(source, "commit_sha", 40)
    tree_sha = req_sha(source, "tree_sha", 40)
    dirty = req_bool(source, "dirty")
    dirty_diff_sha256 = req_sha(source, "dirty_diff_sha256") if dirty else None
    if not dirty and "dirty_diff_sha256" in source:
        fail("CLEAN_SOURCE_HAS_DIRTY_DIFF")

    run = req_obj(data, "run")
    test_run_id = req_str(run, "test_run_id")
    suite_digest = req_sha(run, "suite_digest")

    executor = req_obj(data, "executor")
    if req_str(executor, "host_class") != "UBUNTU":
        fail("EXECUTOR_NOT_UBUNTU")
    executor_identity_sha256 = req_sha(executor, "executor_identity_sha256")
    kernel = req_str(executor, "kernel")

    claude = req_obj(data, "claude")
    claude_binary_sha256 = req_sha(claude, "binary_sha256")
    claude_version = req_str(claude, "version")

    adapter = req_obj(data, "adapter")
    adapter_version = req_str(adapter, "version")
    adapter_sha256 = req_sha(adapter, "source_sha256")

    isolation = req_obj(data, "isolation")
    home_sha256 = req_sha(isolation, "home_sha256")
    allowlist = tuple(req_string_list(isolation, "environment_allowlist"))
    environment_sha256 = req_sha(isolation, "environment_sha256")
    tool_mcp_config_sha256 = req_sha(isolation, "tool_mcp_config_sha256")

    return Binding(
        source_sha,
        tree_sha,
        dirty,
        dirty_diff_sha256,
        test_run_id,
        suite_digest,
        executor_identity_sha256,
        kernel,
        claude_binary_sha256,
        claude_version,
        adapter_version,
        adapter_sha256,
        home_sha256,
        allowlist,
        environment_sha256,
        tool_mcp_config_sha256,
    )


def validate_toolless(data: dict) -> None:
    evidence = req_obj(data, "evidence")
    if req_string_list(evidence, "tools_admitted"):
        fail("TOOLS_ADMITTED")
    if req_string_list(evidence, "mcp_servers_admitted"):
        fail("MCP_SERVERS_ADMITTED")
    if req_int(evidence, "tool_call_count") != 0:
        fail("TOOL_CALL_OBSERVED")
    if not req_bool(evidence, "passed"):
        fail("TOOLLESS_NOT_PASSED")


def validate_ephemeral(data: dict) -> None:
    evidence = req_obj(data, "evidence")
    if req_str(evidence, "home_mode") != "TEMPORARY_EMPTY":
        fail("HOME_NOT_TEMPORARY_EMPTY")
    if req_int(evidence, "preexisting_state_count") != 0:
        fail("PREEXISTING_STATE_OBSERVED")
    if req_int(evidence, "postrun_persistent_artifact_count") != 0:
        fail("PERSISTENT_ARTIFACT_OBSERVED")
    if req_bool(evidence, "session_reuse"):
        fail("SESSION_REUSE_OBSERVED")
    if not req_bool(evidence, "passed"):
        fail("EPHEMERAL_NOT_PASSED")


def validate_structured(data: dict) -> None:
    evidence = req_obj(data, "evidence")
    req_sha(evidence, "parser_contract_sha256")
    req_sha(evidence, "raw_stdout_sha256")
    req_sha(evidence, "raw_stderr_sha256")
    req_sha(evidence, "accepted_result_sha256")
    if not req_bool(evidence, "malformed_probe_rejected"):
        fail("MALFORMED_OUTPUT_ACCEPTED")
    if not req_bool(evidence, "unstructured_probe_rejected"):
        fail("UNSTRUCTURED_OUTPUT_ACCEPTED")
    if not req_bool(evidence, "passed"):
        fail("STRUCTURED_OUTPUT_NOT_PASSED")


def validate_env(data: dict, binding: Binding) -> None:
    evidence = req_obj(data, "evidence")
    child_keys = set(req_string_list(evidence, "child_env_keys"))
    allowlist = set(binding.environment_allowlist)
    leaked = sorted(child_keys - allowlist)
    if leaked:
        fail("CHILD_ENV_OUTSIDE_ALLOWLIST:" + ",".join(leaked))
    if req_string_list(evidence, "ambient_secret_keys_seen"):
        fail("AMBIENT_SECRET_VISIBLE")
    if req_int(evidence, "ambient_probe_count", minimum=1) < 1:
        fail("NO_AMBIENT_PROBE")
    if req_int(evidence, "inherited_ambient_key_count") != 0:
        fail("AMBIENT_ENV_INHERITED")
    if not req_bool(evidence, "home_under_ephemeral_root"):
        fail("HOME_OUTSIDE_EPHEMERAL_ROOT")
    if not req_bool(evidence, "passed"):
        fail("ENV_ISOLATION_NOT_PASSED")


def validate_one(kind: str, data: dict) -> Binding:
    if data.get("schema") != SCHEMAS[kind]:
        fail(f"SCHEMA_MISMATCH:{kind}")
    binding = validate_common(data)
    if req_str(data, "binding_sha256") != binding.digest:
        fail(f"BINDING_DIGEST_MISMATCH:{kind}")
    if kind == "tool_less":
        validate_toolless(data)
    elif kind == "ephemeral":
        validate_ephemeral(data)
    elif kind == "structured_output":
        validate_structured(data)
    elif kind == "env_isolation":
        validate_env(data, binding)
    return binding


def validate_bundle(paths: dict[str, Path]) -> dict:
    bindings: dict[str, Binding] = {}
    for kind, path in paths.items():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"RECEIPT_READ_ERROR:{kind}:{type(exc).__name__}")
        if not isinstance(data, dict):
            fail(f"RECEIPT_NOT_OBJECT:{kind}")
        bindings[kind] = validate_one(kind, data)

    first = next(iter(bindings.values()))
    for kind, binding in bindings.items():
        if binding != first:
            fail(f"CROSS_RECEIPT_BINDING_MISMATCH:{kind}")

    return {
        "schema": "CLAUDE_CODE_ADAPTER_BOUNDARY_BUNDLE_VALIDATION/v1",
        "status": "PASS",
        "binding_sha256": first.digest,
        "subreceipts": {kind: SCHEMAS[kind] for kind in sorted(SCHEMAS)},
        "runtime_credit": "BOUNDARY_RECEIPT_ONLY",
        "whole_product_credit": "ZERO",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    for kind in SCHEMAS:
        parser.add_argument("--" + kind.replace("_", "-"), required=True, type=Path)
    args = parser.parse_args()
    paths = {kind: getattr(args, kind) for kind in SCHEMAS}
    try:
        result = validate_bundle(paths)
    except ValidationError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Bounded Daytona executor for Clay/ClayVerse research batches.

This is research execution tooling, not ClayVerse product/runtime code.
Credentials are read from Daytona's standard environment configuration and are never printed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def emit(event: str, **fields: object) -> None:
    safe = {"event": event, **fields}
    print(json.dumps(safe, sort_keys=True), flush=True)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--bundle", required=True, help="Local .tar/.tar.gz bundle to stage")
    p.add_argument("--bundle-sha256", required=True, help="Expected lowercase SHA-256")
    p.add_argument("--command", action="append", required=True, help="Command to run inside extracted bundle; repeatable")
    p.add_argument("--timeout", type=int, default=900, help="Per-command timeout seconds")
    p.add_argument("--ttl-minutes", type=int, default=30, help="Sandbox TTL safety bound")
    p.add_argument("--deny-network-after-stage", action="store_true", help="Block outbound traffic after upload/extract, before target commands")
    p.add_argument("--label", default="clayverse-batch", help="Non-secret run label")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    bundle = Path(args.bundle).resolve()
    if not bundle.is_file():
        raise SystemExit("bundle_missing")
    expected = args.bundle_sha256.strip().lower()
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        raise SystemExit("invalid_bundle_sha256")
    actual = sha256_file(bundle)
    if actual != expected:
        emit("local_bundle_hash_mismatch", expected=expected, actual=actual)
        return 2
    if not os.environ.get("DAYTONA_API_KEY") and not os.environ.get("DAYTONA_JWT_TOKEN"):
        raise SystemExit("daytona_credentials_missing")

    try:
        from daytona import Daytona
    except Exception as exc:  # pragma: no cover - runtime dependency gate
        emit("daytona_sdk_import_failed", error_type=type(exc).__name__)
        return 3

    daytona = Daytona()
    sandbox = None
    try:
        # Default SDK create() is intentionally used for maximum current-SDK compatibility.
        sandbox = daytona.create()
        sandbox_id = getattr(sandbox, "id", None)
        emit("sandbox_started", provider="daytona", sandbox_id=sandbox_id, label=args.label)
        try:
            sandbox.set_ttl(args.ttl_minutes)
        except Exception as exc:
            emit("ttl_set_failed", error_type=type(exc).__name__)
            return 4

        remote_bundle = "/tmp/clayverse_batch.tgz"
        sandbox.fs.upload_file(str(bundle), remote_bundle)
        verify = sandbox.process.exec(
            f"sha256sum {shlex.quote(remote_bundle)}",
            timeout=min(args.timeout, 120),
        )
        verify_stdout = getattr(getattr(verify, "artifacts", None), "stdout", None) or getattr(verify, "result", "")
        verify_code = int(getattr(verify, "exit_code", 1))
        observed_remote = str(verify_stdout).strip().split()[0] if str(verify_stdout).strip() else ""
        emit("remote_bundle_hash", exit_code=verify_code, expected=expected, observed=observed_remote)
        if verify_code != 0 or observed_remote != expected:
            return 5

        prep = sandbox.process.exec(
            "rm -rf /tmp/clayverse_batch && mkdir -p /tmp/clayverse_batch && tar -xf /tmp/clayverse_batch.tgz -C /tmp/clayverse_batch",
            timeout=min(args.timeout, 180),
        )
        if int(getattr(prep, "exit_code", 1)) != 0:
            emit("bundle_extract_failed", exit_code=int(getattr(prep, "exit_code", 1)))
            return 6

        if args.deny_network_after_stage:
            try:
                sandbox.update_network_settings(network_block_all=True)
                emit("network_policy", outbound="blocked")
            except Exception as exc:
                # Fail closed: requested isolation must not silently degrade.
                emit("network_policy_failed", error_type=type(exc).__name__)
                return 7

        for index, command in enumerate(args.command, start=1):
            result = sandbox.process.exec(command, cwd="/tmp/clayverse_batch", timeout=args.timeout)
            code = int(getattr(result, "exit_code", 1))
            stdout = getattr(getattr(result, "artifacts", None), "stdout", None) or getattr(result, "result", "")
            # Bound log volume; never print environment or credentials.
            text = str(stdout)
            if len(text) > 12000:
                text = text[:12000] + "\n...[truncated]"
            emit("command_result", index=index, exit_code=code, command_sha256=hashlib.sha256(command.encode()).hexdigest(), stdout=text)
            if code != 0:
                return 10 + index
        emit("batch_pass", commands=len(args.command), bundle_sha256=expected)
        return 0
    except Exception as exc:
        emit("provider_or_runtime_error", error_type=type(exc).__name__, message=str(exc)[:1000])
        return 90
    finally:
        if sandbox is not None:
            try:
                sandbox.stop(timeout=60)
                emit("sandbox_stopped", sandbox_id=getattr(sandbox, "id", None))
            except Exception as exc:
                emit("sandbox_stop_failed", error_type=type(exc).__name__)
            try:
                sandbox.delete(timeout=60, wait=True)
                emit("sandbox_deleted", sandbox_id=getattr(sandbox, "id", None))
            except Exception as exc:
                emit("sandbox_delete_failed", error_type=type(exc).__name__)


if __name__ == "__main__":
    sys.exit(main())

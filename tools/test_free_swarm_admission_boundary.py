#!/usr/bin/env python3
"""Deterministic FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1 verifier.

No external provider call is made. Negative cases install secret-access and
socket tripwires and prove that missing/malformed/stale/UNKNOWN/PAID/
SUBSCRIPTION admissions terminate before provider-key lookup and before
provider network I/O. A synthetic exact-FREE positive control uses a fake
urlopen response to prove the gate is not permanently closed.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any

import free_swarm_admission_gate as gate
import run_free_go_swarm as base
import run_24h_entityos_swarm as driver

ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR_SH = ROOT / "tools/run_24h_entityos_swarm_supervisor.sh"
FILES_UNDER_TEST = (
    ROOT / "tools/free_swarm_admission_gate.py",
    ROOT / "tools/run_free_go_swarm.py",
    ROOT / "tools/run_24h_entityos_swarm.py",
    SUPERVISOR_SH,
)
SECRET_NAMES = {
    "GROQ_API_KEY", "GROQ_API_KEYS", "MISTRAL_API_KEY", "MISTRAL_API_KEYS",
    "NVIDIA_API_KEY", "NVIDIA_API_KEYS", "NVIDIA_NIM_API_KEY", "NGC_API_KEY",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_text(*args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), *args], text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else "UNKNOWN"


def policy_for(
    cost_class: str = "UNKNOWN",
    *,
    include_provider: bool = True,
    schema: str = gate.ADMISSION_SCHEMA,
    policy_epoch: str = "8.67",
    admission_epoch: str | None = None,
    secret_lookup_allowed: bool | None = None,
    network_allowed: bool | None = None,
) -> dict[str, Any]:
    if admission_epoch is None:
        admission_epoch = policy_epoch
    if secret_lookup_allowed is None:
        secret_lookup_allowed = cost_class == "FREE"
    if network_allowed is None:
        network_allowed = cost_class == "FREE"
    free_only: dict[str, Any] = {
        "enabled": True,
        "provider_execution_requires_typed_explicit_free_classification": True,
        "provider_admissions": {},
    }
    if include_provider:
        free_only["provider_admissions"]["groq"] = {
            "schema": schema,
            "authority_epoch": admission_epoch,
            "provider": "groq",
            "admission_id": f"{admission_epoch}:groq:test",
            "cost_class": cost_class,
            "secret_lookup_allowed": secret_lookup_allowed,
            "network_allowed": network_allowed,
            "evidence_ref": "SYNTHETIC_TEST_ONLY",
        }
    return {"schema_version": policy_epoch, "free_only": free_only}


def write_policy(tmp: Path, obj: dict[str, Any]) -> Path:
    path = tmp / "SUPERVISOR_INBOX.json"
    path.write_text(json.dumps(obj, sort_keys=True) + "\n", encoding="utf-8")
    return path


class FakeResponse:
    status = 200
    headers: dict[str, str] = {}

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def read(self) -> bytes:
        return json.dumps({
            "choices": [{"message": {"content": "synthetic-positive-control"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }).encode("utf-8")


def run_negative_case(name: str, policy: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="clay-free-admission-") as td:
        policy_path = write_policy(Path(td), policy)
        old_policy_path = base.SUPERVISOR_PATH
        old_getenv = base.os.getenv
        old_urlopen = base.urllib.request.urlopen
        old_collect = driver.base.collect_keys
        old_fetch_catalog = driver.fetch_catalog
        counts = {"secret_lookup_count": 0, "network_attempt_count": 0}

        def poison_getenv(key: str, default: str | None = None) -> str | None:
            if key in SECRET_NAMES or any(key.startswith(n + "_") for n in SECRET_NAMES):
                counts["secret_lookup_count"] += 1
                raise AssertionError(f"provider secret touched before FREE admission: {key}")
            return old_getenv(key, default)

        def poison_urlopen(*args, **kwargs):
            counts["network_attempt_count"] += 1
            raise AssertionError("provider network touched before FREE admission")

        def poison_collect(*args, **kwargs):
            counts["secret_lookup_count"] += 1
            raise AssertionError("driver attempted credential collection before FREE admission")

        def poison_catalog(*args, **kwargs):
            counts["network_attempt_count"] += 1
            raise AssertionError("driver attempted catalog I/O before FREE admission")

        try:
            base.SUPERVISOR_PATH = policy_path
            base.os.getenv = poison_getenv
            base.urllib.request.urlopen = poison_urlopen

            decision = gate.resolve_provider_admission("groq", policy_path)
            assert not decision.allowed, (name, dataclasses.asdict(decision))

            keys = base.collect_keys(base.PROVIDERS[0])
            assert keys == [], (name, keys)
            status, _headers, payload = base.request_chat(
                base.PROVIDERS[0], "synthetic-never-used-key", "synthetic-model",
                "synthetic-prompt", 8, 0.01,
            )
            assert status == 0, (name, status, payload)
            assert isinstance(payload, dict)
            assert payload.get("classification") == "PROVIDER_ADMISSION_REVOKED_FAIL_CLOSED"

            # Independently prove discovery does not even enter its credential
            # or catalog functions for a blocked provider.
            driver.base.collect_keys = poison_collect
            driver.fetch_catalog = poison_catalog
            report = driver.discover_and_export(0.01)
            assert report["groq"]["source"] == "admission_blocked", (name, report["groq"])

            assert counts["secret_lookup_count"] == 0, (name, counts)
            assert counts["network_attempt_count"] == 0, (name, counts)
            return {
                "case": name,
                "verdict": "PASS",
                "reason": decision.reason,
                **counts,
            }
        finally:
            base.SUPERVISOR_PATH = old_policy_path
            base.os.getenv = old_getenv
            base.urllib.request.urlopen = old_urlopen
            driver.base.collect_keys = old_collect
            driver.fetch_catalog = old_fetch_catalog


def run_positive_control() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="clay-free-admission-positive-") as td:
        policy_path = write_policy(Path(td), policy_for("FREE"))
        old_policy_path = base.SUPERVISOR_PATH
        old_urlopen = base.urllib.request.urlopen
        counts = {"network_attempt_count": 0}

        def fake_urlopen(*args, **kwargs):
            counts["network_attempt_count"] += 1
            return FakeResponse()

        try:
            base.SUPERVISOR_PATH = policy_path
            base.urllib.request.urlopen = fake_urlopen
            decision = gate.resolve_provider_admission("groq", policy_path)
            assert decision.allowed, dataclasses.asdict(decision)
            status, _headers, payload = base.request_chat(
                base.PROVIDERS[0], "synthetic-key", "synthetic-model",
                "synthetic-prompt", 8, 0.01,
            )
            assert status == 200, (status, payload)
            assert counts["network_attempt_count"] == 1, counts
            return {
                "case": "EXACT_TYPED_FREE_POSITIVE_CONTROL",
                "verdict": "PASS",
                "reason": decision.reason,
                "network_attempt_count": counts["network_attempt_count"],
                "external_network_performed": False,
            }
        finally:
            base.SUPERVISOR_PATH = old_policy_path
            base.urllib.request.urlopen = old_urlopen


def verify_supervisor_shell() -> dict[str, Any]:
    text = SUPERVISOR_SH.read_text(encoding="utf-8")
    forbidden = (
        "load_all_secret_sources",
        "/run/secrets/clay_provider.env",
        "/artifacts/.clay_provider.env",
        "/cache/clay_provider.env",
        "research_entity/private/API_TOKENS.env",
        'source "$f"',
    )
    present = [item for item in forbidden if item in text]
    assert not present, present
    required = (
        "provider_is_admitted",
        "load_admitted_provider_secrets",
        "free_swarm_admission_gate.py",
        "clear_provider_secret_env",
    )
    missing = [item for item in required if item not in text]
    assert not missing, missing
    proc = subprocess.run(
        ["bash", "-n", str(SUPERVISOR_SH)], text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return {
        "case": "SUPERVISOR_SECRET_SOURCE_ORDER_AND_BASH_SYNTAX",
        "verdict": "PASS",
        "forbidden_generic_secret_sources_present": present,
        "bash_n_exit": proc.returncode,
    }


def run_all() -> dict[str, Any]:
    negative_cases = [
        ("PROVIDER_ADMISSION_MISSING", policy_for(include_provider=False)),
        ("UNKNOWN", policy_for("UNKNOWN")),
        ("PAID", policy_for("PAID")),
        ("SUBSCRIPTION", policy_for("SUBSCRIPTION")),
        ("STALE_AUTHORITY_EPOCH", policy_for("FREE", admission_epoch="8.66")),
        ("MALFORMED_SCHEMA", policy_for("FREE", schema="ENTITYOS_PROVIDER_ADMISSION/v0")),
        ("FREE_WITH_SECRET_LOOKUP_DENIED", policy_for("FREE", secret_lookup_allowed=False)),
        ("FREE_WITH_NETWORK_DENIED", policy_for("FREE", network_allowed=False)),
    ]
    results = [run_negative_case(name, policy) for name, policy in negative_cases]
    results.append(run_positive_control())
    results.append(verify_supervisor_shell())
    passed = all(item.get("verdict") == "PASS" for item in results)
    return {
        "schema": "FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1",
        "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "organ": "GPT-5.6 Sol test capsule",
        "scope": "DETERMINISTIC_SOURCE_MECHANISM_ONLY_NO_EXTERNAL_PROVIDER_IO",
        "repo_head": git_text("rev-parse", "HEAD"),
        "git_status": git_text("status", "--short") or "CLEAN",
        "source_sha256": {str(p.relative_to(ROOT)): sha256_file(p) for p in FILES_UNDER_TEST},
        "negative_cases_required": [name for name, _ in negative_cases],
        "results": results,
        "summary": {
            "tests": len(results),
            "passed": sum(item.get("verdict") == "PASS" for item in results),
            "failed": sum(item.get("verdict") != "PASS" for item in results),
            "secret_lookup_count_across_blocked_cases": sum(item.get("secret_lookup_count", 0) for item in results[:-2]),
            "network_attempt_count_across_blocked_cases": sum(item.get("network_attempt_count", 0) for item in results[:-2]),
            "external_provider_network_performed": False,
        },
        "verdict": "PASS" if passed else "FAIL",
        "credit": {
            "provider_runtime": 0,
            "entityos_whole_runtime": 0,
            "hcu_full_runtime": 0,
            "jspace_model_runtime": 0,
            "training": 0,
        },
        "evidence_limit": "Passing this capsule proves the local source/control boundary at the executed checkout only. It does not classify any real provider as FREE, expose a credential, perform provider I/O, prove VPS bridge health, or mint whole EntityOS/HCU/J-Space/training credit.",
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", default="", help="optional JSON receipt output path")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    try:
        receipt = run_all()
    except Exception as exc:
        receipt = {
            "schema": "FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1",
            "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "scope": "DETERMINISTIC_SOURCE_MECHANISM_ONLY_NO_EXTERNAL_PROVIDER_IO",
            "verdict": "FAIL",
            "error": f"{exc.__class__.__name__}:{exc}",
            "credit": {"provider_runtime": 0, "entityos_whole_runtime": 0, "hcu_full_runtime": 0, "jspace_model_runtime": 0, "training": 0},
        }
    payload = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt:
        path = Path(args.receipt)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if receipt.get("verdict") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

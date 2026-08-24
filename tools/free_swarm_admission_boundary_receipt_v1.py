#!/usr/bin/env python3
"""Deterministic FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1.

Mechanism test only: no real provider credential is read and no real provider socket is
opened. The harness exercises the production pre-key wrapper and the production pre-network
driver using synthetic local tripwires and a synthetic typed admission file.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Iterator

import free_provider_admission as admission
import run_24h_entityos_swarm_entry as entry

driver = entry.driver


class ExpectedNetworkTripwire(RuntimeError):
    pass


SYNTHETIC_EVIDENCE_SHA256 = hashlib.sha256(
    b"synthetic-local-free-provider-admission-boundary-evidence"
).hexdigest()


@contextmanager
def environment_snapshot() -> Iterator[None]:
    before = dict(os.environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(before)


@contextmanager
def no_quota_side_effect(*_args, **_kwargs):
    yield "synthetic-local-quota-slot"


def free_item(provider: str) -> dict:
    return {
        "cost_class": "FREE",
        "admitted": True,
        "cost_evidence": {
            "evidence_ref": f"synthetic-test-fixture:{provider}",
            "checked_at": "TEST_ONLY",
            "claim": "ZERO_MONETARY_COST_FOR_BOUND_PROVIDER_SCOPE",
            "scope": provider,
            "evidence_sha256": SYNTHETIC_EVIDENCE_SHA256,
        },
    }


def blocked_item(cost_class: str) -> dict:
    return {"cost_class": cost_class, "admitted": False}


def admission_document(
    *,
    binding: tuple[str, str],
    groq: dict | None = None,
    free_only: bool = True,
    source: str = admission.CONTROL_PLANE,
    stale_authority: bool = False,
) -> dict:
    return {
        "schema": admission.SCHEMA,
        "source": source,
        "free_only": free_only,
        "authority_epoch": "8.STALE" if stale_authority else binding[0],
        "supervisor_steering": binding[1],
        "providers": {} if groq is None else {"groq": groq},
    }


def write_doc(root: Path, payload: dict, name: str) -> Path:
    path = root / f"{name}.json"
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return path


def groq_spec():
    return next(spec for spec in driver.ALL_PROVIDER_SPECS if spec.name == "groq")


def run_case(
    name: str,
    root: Path,
    payload: dict | None,
    *,
    expect_allowed: bool,
) -> dict:
    counters = {"secret_lookup_count": 0, "network_attempt_count": 0}
    spec = groq_spec()
    real_collector = entry._ORIGINAL_COLLECT_KEYS
    real_entry_require = entry.require_provider_admitted
    real_driver_require = driver.require_provider_admitted
    real_request = driver._ORIGINAL_REQUEST_CHAT
    real_quota_slot = driver.quota_slot
    real_quota_observe = driver.quota_observe

    if payload is None:
        path = root / f"{name}-missing.json"
    else:
        path = write_doc(root, payload, name)

    def secret_tripwire(_spec):
        counters["secret_lookup_count"] += 1
        return ["synthetic-never-provider-key"]

    def network_tripwire(_spec, _key, _model, _prompt, _max_tokens, _timeout):
        counters["network_attempt_count"] += 1
        raise ExpectedNetworkTripwire("LOCAL_SOCKET_TRIPWIRE_REACHED")

    def bound_require(provider: str, **_kwargs) -> None:
        admission.require_provider_admitted(provider, path=path)

    entry._ORIGINAL_COLLECT_KEYS = secret_tripwire
    entry.require_provider_admitted = bound_require
    driver.require_provider_admitted = bound_require
    driver._ORIGINAL_REQUEST_CHAT = network_tripwire
    driver.quota_slot = no_quota_side_effect
    driver.quota_observe = lambda *_args, **_kwargs: None
    try:
        keys = driver.base.collect_keys(spec)
        secret_allowed = bool(keys)

        network_allowed = False
        try:
            driver.base.request_chat(
                spec,
                "synthetic-never-provider-key",
                "synthetic-model",
                "x",
                1,
                0.01,
            )
        except ExpectedNetworkTripwire:
            network_allowed = True
        except admission.ProviderAdmissionError:
            network_allowed = False

        observed_allowed = secret_allowed and network_allowed
        passed = observed_allowed is expect_allowed
        if expect_allowed:
            passed = passed and counters == {
                "secret_lookup_count": 1,
                "network_attempt_count": 1,
            }
        else:
            passed = passed and counters == {
                "secret_lookup_count": 0,
                "network_attempt_count": 0,
            }

        return {
            "case": name,
            "expected_allowed": expect_allowed,
            "observed_allowed": observed_allowed,
            **counters,
            "pass": passed,
        }
    finally:
        entry._ORIGINAL_COLLECT_KEYS = real_collector
        entry.require_provider_admitted = real_entry_require
        driver.require_provider_admitted = real_driver_require
        driver._ORIGINAL_REQUEST_CHAT = real_request
        driver.quota_slot = real_quota_slot
        driver.quota_observe = real_quota_observe


def main() -> int:
    binding = admission.active_supervisor_binding()
    with environment_snapshot(), tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cases = [
            run_case(
                "GLOBAL_FREE_ONLY_ADMISSION_MISSING",
                root,
                None,
                expect_allowed=False,
            ),
            run_case(
                "GLOBAL_FREE_ONLY_FALSE",
                root,
                admission_document(binding=binding, free_only=False),
                expect_allowed=False,
            ),
            run_case(
                "PROVIDER_ADMISSION_MISSING",
                root,
                admission_document(binding=binding),
                expect_allowed=False,
            ),
            run_case(
                "PROVIDER_COST_UNKNOWN",
                root,
                admission_document(binding=binding, groq=blocked_item("UNKNOWN")),
                expect_allowed=False,
            ),
            run_case(
                "PROVIDER_COST_PAID",
                root,
                admission_document(binding=binding, groq=blocked_item("PAID")),
                expect_allowed=False,
            ),
            run_case(
                "PROVIDER_COST_SUBSCRIPTION",
                root,
                admission_document(binding=binding, groq=blocked_item("SUBSCRIPTION")),
                expect_allowed=False,
            ),
            run_case(
                "WRONG_SOURCE",
                root,
                admission_document(
                    binding=binding,
                    groq=free_item("groq"),
                    source="ENV_ATTESTATION",
                ),
                expect_allowed=False,
            ),
            run_case(
                "STALE_AUTHORITY",
                root,
                admission_document(
                    binding=binding,
                    groq=free_item("groq"),
                    stale_authority=True,
                ),
                expect_allowed=False,
            ),
            run_case(
                "PROVIDER_COST_FREE_SYNTHETIC_MECHANISM_ONLY",
                root,
                admission_document(binding=binding, groq=free_item("groq")),
                expect_allowed=True,
            ),
        ]

    negative = [case for case in cases if not case["expected_allowed"]]
    positive = [case for case in cases if case["expected_allowed"]]
    passed = (
        all(case["pass"] for case in cases)
        and all(
            case["secret_lookup_count"] == 0
            and case["network_attempt_count"] == 0
            for case in negative
        )
        and len(positive) == 1
        and positive[0]["secret_lookup_count"] == 1
        and positive[0]["network_attempt_count"] == 1
    )
    receipt = {
        "schema": "FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1",
        "status": "PASS" if passed else "FAIL",
        "active_supervisor_binding": {
            "authority_epoch": binding[0],
            "supervisor_steering": binding[1],
        },
        "cases": cases,
        "negative_cases": len(negative),
        "positive_cases": len(positive),
        "real_provider_credentials_read": 0,
        "real_provider_network_attempts": 0,
        "synthetic_positive_case_only": True,
        "synthetic_positive_case_does_not_classify_real_provider_free": True,
        "production_prekey_entry_exercised": True,
        "test_process_function_injection_only": True,
        "tripwires": {
            "secret": "LOCAL_POST_ADMISSION_COLLECTOR_TRIPWIRE",
            "network": "LOCAL_PRE_SOCKET_PROVIDER_REQUEST_TRIPWIRE",
        },
        "scope": "FREE_ONLY_PROVIDER_ADMISSION_BOUNDARY_DETERMINISTIC_COMPONENT_ONLY",
        "provider_runtime_credit": 0,
        "whole_entityos_hcu_runtime_credit": 0,
        "unusual_experiment_count_added": 0,
    }
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

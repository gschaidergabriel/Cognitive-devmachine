#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import hashlib
import importlib
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import free_swarm_provider_admission as admission
import run_free_go_swarm as facade

LEGACY_FLAGS = {
    "CLAY_FREE_ONLY_ATTESTED":"1",
    "CLAY_GROQ_FREE_ATTESTED":"1",
    "CLAY_MISTRAL_FREE_ATTESTED":"1",
    "CLAY_NVIDIA_FREE_ATTESTED":"1",
}
PROVIDER_ENV_NAMES = set(sum((list(x) for x in admission.PROVIDER_SECRET_NAMES.values()), []))
PROVIDER_ENV_NAMES |= set(LEGACY_FLAGS)
PROVIDER_ENV_NAMES |= {"CLAY_PROVIDER_ADMISSION_FILE","CLAY_PROVIDER_SECRET_FILES"}


def payload(cost_class="FREE", admitted=True, *, global_free_only=True, include_provider=True):
    row = {
        "schema": admission.SCHEMA,
        "source": admission.SOURCE,
        "mode": admission.MODE,
        "decision_id": "test-decision",
        "generation": 7,
        "global_free_only": global_free_only,
        "providers": {},
    }
    if include_provider:
        row["providers"]["groq"] = {"cost_class": cost_class, "admitted": admitted, "reason": "test"}
    else:
        row["providers"]["mistral"] = {"cost_class": "UNKNOWN", "admitted": False, "reason": "placeholder"}
    return row


@contextlib.contextmanager
def clean_provider_env():
    old = {name: os.environ.get(name) for name in PROVIDER_ENV_NAMES}
    try:
        for name in PROVIDER_ENV_NAMES:
            os.environ.pop(name, None)
        yield
    finally:
        for name in PROVIDER_ENV_NAMES:
            os.environ.pop(name, None)
        for name, value in old.items():
            if value is not None:
                os.environ[name] = value


class BoundaryCaseRunner:
    def __init__(self):
        self.results=[]

    def run(self, name, admission_payload, expect_keys=False):
        with tempfile.TemporaryDirectory() as td, clean_provider_env():
            td=Path(td)
            secret=td/"provider.env"
            secret.write_text("GROQ_API_KEY=sentinel-secret\nMISTRAL_API_KEY=must-not-be-read\n",encoding="utf-8")
            os.environ.update(LEGACY_FLAGS)  # prove legacy flags cannot grant authority
            os.environ["CLAY_PROVIDER_SECRET_FILES"] = str(secret)
            if admission_payload is None:
                os.environ["CLAY_PROVIDER_ADMISSION_FILE"] = str(td/"missing.json")
            else:
                ap=td/"admission.json"
                ap.write_text(json.dumps(admission_payload),encoding="utf-8")
                os.environ["CLAY_PROVIDER_ADMISSION_FILE"] = str(ap)
            admission._CACHE_KEY = None
            admission._CACHE_VALUE = None
            admission.reset_metrics()
            socket_attempts=0
            real_connect=socket.socket.connect
            def blocked_connect(sock, address):
                nonlocal socket_attempts
                socket_attempts += 1
                admission.record_network_attempt()
                raise AssertionError(f"network reached boundary in {name}: {address}")
            socket.socket.connect=blocked_connect
            try:
                spec=next(x for x in facade.PROVIDERS if x.name=="groq")
                keys=facade.collect_keys(spec)
                # Model the unchanged 24h discovery control point: network is reachable
                # only if the admission-safe facade returns an admitted key.
                if keys and not expect_keys:
                    admission.record_network_attempt()
                metrics=admission.metrics_snapshot()
            finally:
                socket.socket.connect=real_connect
            observed={
                "case":name,
                "keys_returned":len(keys),
                "secret_lookup_count":metrics["secret_lookup_count"],
                "network_attempt_count":metrics["network_attempt_count"] + socket_attempts,
            }
            self.results.append(observed)
            if expect_keys:
                assert keys == ["sentinel-secret"], observed
                assert observed["secret_lookup_count"] > 0, observed
                assert observed["network_attempt_count"] == 0, observed
            else:
                assert keys == [], observed
                assert observed["secret_lookup_count"] == 0, observed
                assert observed["network_attempt_count"] == 0, observed
            return observed


class TestFreeSwarmAdmissionBoundary(unittest.TestCase):
    def test_required_negative_matrix(self):
        r=BoundaryCaseRunner()
        r.run("global_attestation_missing", payload(global_free_only=False))
        r.run("provider_admission_missing", payload(include_provider=False))
        r.run("unknown", payload("UNKNOWN", False))
        r.run("paid", payload("PAID", False))
        r.run("subscription", payload("SUBSCRIPTION", False))
        r.run("admission_file_missing", None)

    def test_non_free_admitted_contradiction_fails_closed(self):
        r=BoundaryCaseRunner()
        r.run("paid_admitted_contradiction", payload("PAID", True))

    def test_positive_free_unlocks_secret_lookup_only_after_admission(self):
        r=BoundaryCaseRunner()
        r.run("free_positive", payload("FREE", True), expect_keys=True)

    def test_supervisor_has_no_shell_secret_sourcing(self):
        text=(HERE/"run_24h_entityos_swarm_supervisor.sh").read_text(encoding="utf-8")
        self.assertNotIn("source \"$", text)
        self.assertNotIn("load_secret_file", text)
        self.assertNotIn("has_provider_key", text)
        self.assertLess(text.index("free_swarm_provider_admission.py"), text.index("run_24h_entityos_swarm.py"))

    def test_facade_checks_typed_admission_before_legacy_key_collection(self):
        text=(HERE/"run_free_go_swarm.py").read_text(encoding="utf-8")
        start=text.index("def collect_keys")
        end=text.index("\n\ndef ", start+5)
        body=text[start:end]
        self.assertLess(body.index("_typed_admission()"), body.index("_legacy.collect_keys(spec)"))
        self.assertIn("provider_is_admitted_free", body)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_receipt(results: list[dict]) -> dict:
    files=[
        HERE/"free_swarm_provider_admission.py",
        HERE/"run_free_go_swarm.py",
        HERE/"run_24h_entityos_swarm_supervisor.sh",
        HERE/"test_free_swarm_admission_boundary.py",
    ]
    negatives=[x for x in results if x["case"]!="free_positive"]
    return {
        "schema":"FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1",
        "observed_environment":"CHATGPT_LOCAL_CONTAINER_COMPONENT_TEST",
        "authority_epoch_target":"8.67",
        "scope":"FREE_SWARM_ADMISSION_BOUNDARY_COMPONENT_ONLY",
        "source_sha256":{str(p.relative_to(ROOT)):sha256(p) for p in files},
        "negative_acceptance":{
            "required":"secret_lookup_count=0 AND network_attempt_count=0",
            "pass":all(x["secret_lookup_count"]==0 and x["network_attempt_count"]==0 and x["keys_returned"]==0 for x in negatives),
            "cases":negatives,
        },
        "positive_control":next((x for x in results if x["case"]=="free_positive"),None),
        "legacy_env_attestation_is_authority":False,
        "shell_sources_secret_files":False,
        "whole_entityos_runtime_credit":0,
        "whole_hcu_runtime_credit":0,
        "provider_runtime_credit":0,
        "training_credit":0,
        "note":"Local component evidence only. No provider network call was made and no paid/provider execution credit is claimed.",
    }


def main() -> int:
    runner=BoundaryCaseRunner()
    cases=[
        ("global_attestation_missing",payload(global_free_only=False),False),
        ("provider_admission_missing",payload(include_provider=False),False),
        ("unknown",payload("UNKNOWN",False),False),
        ("paid",payload("PAID",False),False),
        ("subscription",payload("SUBSCRIPTION",False),False),
        ("admission_file_missing",None,False),
        ("paid_admitted_contradiction",payload("PAID",True),False),
        ("free_positive",payload("FREE",True),True),
    ]
    for name,p,positive in cases:
        runner.run(name,p,expect_keys=positive)
    receipt=build_receipt(runner.results)
    out=ROOT/"FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT.v1.json"
    out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0 if receipt["negative_acceptance"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

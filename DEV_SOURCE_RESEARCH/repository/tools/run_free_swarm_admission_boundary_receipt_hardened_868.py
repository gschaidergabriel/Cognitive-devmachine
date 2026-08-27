#!/usr/bin/env python3
"""Successor hardening for FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1.

This wrapper keeps the canonical v1 runner semantics while closing source-evidence
holes before the required exact-source runtime execution:

1. bind both the base runner and this hardening wrapper into the source manifest;
2. extend the child-process socket tripwire to DNS resolution via getaddrinfo(),
   connect_ex(), and unconnected datagram egress via sendto()/sendmsg() in addition
   to create_connection()/connect();
3. bind and execute the supervisor inherited-provider-environment fence regression,
   so the receipt cannot PASS without checking that the non-admitted credential
   clearing fence precedes every supervisor child-start path;
4. execute a fail-closed discovery regression proving the supervisor-8.68 mandatory
   blocked-case test methods remain present in the canonical receipt suite.

It still performs no external provider call and grants no provider/model/HCU/J-Space
or training credit by source presence alone.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import run_free_swarm_admission_boundary_receipt as base

ROOT = Path(__file__).resolve().parents[1]
SELF_REL = "tools/run_free_swarm_admission_boundary_receipt_hardened_868.py"
BASE_REL = "tools/run_free_swarm_admission_boundary_receipt.py"
TEST_REL = "tests/test_free_swarm_receipt_runner_hardening_868.py"
TEST_MODULE = "tests.test_free_swarm_receipt_runner_hardening_868"
INHERITED_ENV_TEST_REL = "tests/test_go_868_inherited_provider_secret_fence.py"
INHERITED_ENV_TEST_MODULE = "tests.test_go_868_inherited_provider_secret_fence"
REQUIRED_CASES_TEST_REL = "tests/test_free_swarm_receipt_required_cases_868.py"
REQUIRED_CASES_TEST_MODULE = "tests.test_free_swarm_receipt_required_cases_868"


def _hardened_bootstrap_text() -> str:
    return r'''import json
import os
from pathlib import Path
import socket
import sys
import unittest

log_path = Path(os.environ["CLAY_NETWORK_TRIPWIRE_LOG"])

def record(kind, target):
    try:
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"kind": kind, "target": repr(target)}, separators=(",", ":")) + "\n")
    finally:
        raise RuntimeError("CLAY_BOUNDARY_NETWORK_TRIPWIRE")

def guarded_connect(self, address):
    return record("socket.connect", address)

def guarded_connect_ex(self, address):
    return record("socket.connect_ex", address)

def guarded_create_connection(address, *args, **kwargs):
    return record("socket.create_connection", address)

def guarded_getaddrinfo(*args, **kwargs):
    target = args[:2] if args else kwargs
    return record("socket.getaddrinfo", target)

def guarded_sendto(self, data, *args, **kwargs):
    target = args[-1] if args else kwargs.get("address")
    return record("socket.sendto", target)

def guarded_sendmsg(self, buffers, *args, **kwargs):
    target = args[-1] if args else kwargs.get("address")
    return record("socket.sendmsg", target)

socket.socket.connect = guarded_connect
socket.socket.connect_ex = guarded_connect_ex
socket.create_connection = guarded_create_connection
socket.getaddrinfo = guarded_getaddrinfo
socket.socket.sendto = guarded_sendto
if hasattr(socket.socket, "sendmsg"):
    socket.socket.sendmsg = guarded_sendmsg
suite = unittest.defaultTestLoader.loadTestsFromNames(sys.argv[1:])
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
'''


def _install_hardening() -> None:
    if getattr(base, "_CLAY_868_RECEIPT_HARDENING_INSTALLED", False):
        return

    base.TEST_MODULES = tuple(dict.fromkeys((
        *base.TEST_MODULES,
        TEST_MODULE,
        INHERITED_ENV_TEST_MODULE,
        REQUIRED_CASES_TEST_MODULE,
    )))
    base.TEST_PATHS = tuple(dict.fromkeys((
        *base.TEST_PATHS,
        ROOT / TEST_REL,
        ROOT / INHERITED_ENV_TEST_REL,
        ROOT / REQUIRED_CASES_TEST_REL,
    )))
    base.SOURCE_PATHS = tuple(dict.fromkeys((
        *base.SOURCE_PATHS,
        BASE_REL,
        SELF_REL,
        TEST_REL,
        INHERITED_ENV_TEST_REL,
        REQUIRED_CASES_TEST_REL,
    )))
    base._bootstrap_text = _hardened_bootstrap_text

    original_write_receipt = base._write_receipt

    def write_receipt(path: Path | None, receipt: dict[str, Any]) -> None:
        source = receipt.setdefault("source", {})
        source["receipt_runner"] = SELF_REL
        source["receipt_runner_base"] = BASE_REL
        source["receipt_runner_hardening"] = {
            "authority_epoch": "8.68",
            "base_and_successor_manifest_bound": True,
            "required_case_discovery_test": REQUIRED_CASES_TEST_REL,
            "required_case_discovery_required_for_pass": True,
            "bootstrap_tripwires": [
                "socket.create_connection",
                "socket.getaddrinfo",
                "socket.socket.connect",
                "socket.socket.connect_ex",
                "socket.socket.sendto",
                "socket.socket.sendmsg_if_available",
            ],
            "inherited_provider_environment_fence_test": INHERITED_ENV_TEST_REL,
            "inherited_provider_environment_fence_required_for_pass": True,
        }
        fences = receipt.setdefault("fences", {})
        fences["supervisor_inherited_provider_environment_fence"] = (
            "ENFORCED_BY_TEST_GO_868_INHERITED_PROVIDER_SECRET_FENCE"
        )
        fences["supervisor_868_required_blocked_cases"] = (
            "ENFORCED_BY_TEST_FREE_SWARM_RECEIPT_REQUIRED_CASES_868"
        )
        original_write_receipt(path, receipt)

    base._write_receipt = write_receipt
    base._CLAY_868_RECEIPT_HARDENING_INSTALLED = True


_install_hardening()


if __name__ == "__main__":
    raise SystemExit(base.main())

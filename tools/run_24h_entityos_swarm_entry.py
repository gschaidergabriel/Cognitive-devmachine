#!/usr/bin/env python3
"""Admission-rechecking entrypoint for the canonical EntityOS/HCU FREE swarm.

The retained driver remains the implementation donor. This entrypoint revalidates
canonical typed FREE admission immediately before every model-chat and model-catalog
provider I/O so a mid-run authority revocation fails closed without touching network.
"""
from __future__ import annotations

import asyncio

import run_24h_entityos_swarm as driver
import run_free_go_swarm as base

_ORIGINAL_BOUNDED_CHAT = base.request_chat
_ORIGINAL_FETCH_CATALOG = driver.fetch_catalog


def admission_rechecking_chat(spec, key, model, prompt, max_tokens, timeout):
    if not base.provider_is_admitted_free(spec.name):
        return 403, {}, {
            "classification": "PROVIDER_ADMISSION_REVOKED_FAIL_CLOSED",
            "provider": spec.name,
            "network_attempted": False,
        }
    return _ORIGINAL_BOUNDED_CHAT(spec, key, model, prompt, max_tokens, timeout)


def admission_rechecking_catalog(provider: str, url: str, key: str, timeout: float):
    if not base.provider_is_admitted_free(provider):
        return []
    return _ORIGINAL_FETCH_CATALOG(provider, url, key, timeout)


base.request_chat = admission_rechecking_chat
driver.fetch_catalog = admission_rechecking_catalog


if __name__ == "__main__":
    raise SystemExit(asyncio.run(driver.main(driver.parse_args())))

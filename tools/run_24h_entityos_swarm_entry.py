#!/usr/bin/env python3
"""Production entry for the EntityOS/HCU FREE_ONLY swarm.

This module installs the final pre-key admission guard before delegating to
``run_24h_entityos_swarm``. Importing the underlying driver does not perform provider
network I/O; after this wrapper is installed every inherited ``collect_keys`` call must
revalidate typed admission before it may inspect provider credential environment values.

The underlying driver separately revalidates immediately before catalog/chat network I/O.
Together these two boundaries implement Supervisor 8.67's ordering:

    typed FREE admission -> credential lookup -> provider network

Legacy environment attestation flags remain downstream compatibility signals only.
"""
from __future__ import annotations

import asyncio

import run_24h_entityos_swarm as driver
from free_provider_admission import require_provider_admitted

_ORIGINAL_COLLECT_KEYS = driver.base.collect_keys


def typed_collect_keys(spec):
    require_provider_admitted(spec.name, path=driver.ADMISSION_FILE_DEFAULT)
    return _ORIGINAL_COLLECT_KEYS(spec)


# Install exactly once for both discovery and the inherited long-running worker loop.
driver.base.collect_keys = typed_collect_keys


def main() -> int:
    return asyncio.run(driver.main(driver.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())

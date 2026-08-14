#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import platform
import sqlite3
import sys
import time
import unittest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', required=True)
    args = ap.parse_args()

    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromName('test_semantic_access_v11'))
    suite.addTests(loader.loadTestsFromName('test_semantic_access_v11b_graph_gate'))
    tests = suite.countTestCases()

    started = time.perf_counter_ns()
    result = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000.0

    payload = {
        'schema_version': '1.0',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'pass': result.wasSuccessful(),
        'tests': tests,
        'tests_run': int(result.testsRun),
        'failures': len(result.failures),
        'errors': len(result.errors),
        'skipped': len(getattr(result, 'skipped', [])),
        'elapsed_ms': elapsed_ms,
        'source_commit': os.environ.get('SOURCE_SHA', 'UNKNOWN'),
        'github_run_id': os.environ.get('RUN_ID', 'UNKNOWN'),
        'runner': 'self-hosted Hostinger Ubuntu/Linux lane',
        'truth_class': 'VERIFIED_REMOTE_EXECUTION_EXACT_CLAY_CHECKOUT',
        'python': platform.python_version(),
        'sqlite': sqlite3.sqlite_version,
        'platform': platform.platform(),
        'machine': platform.machine(),
        'processor': platform.processor() or 'UNKNOWN',
        'scope': [
            'legacy U11 compatibility',
            'U11B verified-plan/latest-receipt/path-fingerprint gate',
            'graph/plan drift quarantine',
            'last-known-good preservation',
            'BEGIN IMMEDIATE contention fail-closed'
        ],
    }
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write('\n')
    print(json.dumps(payload, sort_keys=True))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())

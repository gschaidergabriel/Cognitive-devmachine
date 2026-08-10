#!/usr/bin/env python3
"""Narrow deterministic regression for WP14 exact-checkout freshness semantics."""
from __future__ import annotations

from claycode_base_wp14_strict_audit import release_commit_is_current


def main() -> int:
    cases = [
        ("abc123", "abc123", True, "exact_match"),
        ("abc123", "def456", False, "stale_or_foreign_release"),
        ("", "abc123", False, "missing_release_commit"),
        ("abc123", "", False, "missing_checkout_head"),
        ("", "", False, "both_missing"),
    ]
    failed = []
    for release_commit, checkout_head, expected, name in cases:
        observed = release_commit_is_current(release_commit, checkout_head)
        if observed is not expected:
            failed.append({"case": name, "expected": expected, "observed": observed})
    print({"pass": not failed, "cases": len(cases), "failures": failed})
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Canonical Clay GO collective-metrics entrypoint.

The historical v1 calculation is preserved as an internal implementation donor while
Supervisor 8.77 freshness, authority and monotonic-publication enforcement lives in
the adjacent freshness module. All callers keep this existing canonical path.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_IMPL_PATH = Path(__file__).with_name("go_collective_metrics_freshness_v1.py")
_SPEC = importlib.util.spec_from_file_location("clay_go_collective_metrics_freshness_v1", _IMPL_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("GO_COLLECTIVE_METRICS_FRESHNESS_V1_UNAVAILABLE")
_impl = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_impl)

for _name in dir(_impl):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_impl, _name)


def main() -> int:
    return _impl.main()


if __name__ == "__main__":
    raise SystemExit(main())

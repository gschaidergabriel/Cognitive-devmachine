#!/usr/bin/env python3
"""Piston/self-hosted code execution adapter for FRANK/RAE.

As of 2026-02-15 the hosted EMKC Piston API requires an authorization token. Set
PISTON_API_TOKEN for the hosted service, or set PISTON_API_URL to a self-hosted instance
(which may be used without a token). The hosted token is sent exactly in the
Authorization header, matching current piston_rs client behavior.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rae_secret_loader import SecretError, get_secret, secret_source  # noqa: E402

DEFAULT_BASE = "https://emkc.org/api/v2/piston"


def _configured_base() -> tuple[str, bool]:
    explicit = os.environ.get("PISTON_API_URL") or get_secret("PISTON_API_URL", required=False)
    return ((explicit or DEFAULT_BASE).rstrip("/"), bool(explicit))


def _headers() -> dict[str, str]:
    base, self_hosted = _configured_base()
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "FRANK-RAE/8.8 Piston adapter",
    }
    token = get_secret("PISTON_API_TOKEN", required=False)
    if token:
        headers["Authorization"] = token
    elif not self_hosted and base == DEFAULT_BASE:
        raise SecretError("Hosted Piston requires PISTON_API_TOKEN as of 2026-02-15; configure a token or PISTON_API_URL for self-hosted Piston")
    return headers


def _base() -> str:
    return _configured_base()[0]


def _request(path: str, method: str = "GET", body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(_base() + path, data=data, headers=_headers(), method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def runtimes() -> list:
    return _request("/runtimes")


def _runtime(language: str) -> dict:
    needle = language.lower()
    items = runtimes()
    candidates = [x for x in items if needle == str(x.get("language", "")).lower() or needle in [str(a).lower() for a in x.get("aliases") or []]]
    if not candidates:
        raise RuntimeError(f"Piston runtime not found: {language}")
    return candidates[-1]


def execute(code: str, language: str = "python", stdin: str = "") -> dict:
    rt = _runtime(language)
    payload = {"language": rt["language"], "version": rt["version"], "files": [{"name": "main", "content": code}], "stdin": stdin}
    d = _request("/execute", "POST", payload)
    return {"provider": "Piston", "tool": "piston_execute", "evidence_class": "runtime_experiment", "endpoint": _base(), "runtime": rt, "result": d}


def smoke_test() -> dict:
    d = execute("print('RAE_PISTON_OK')", "python")
    out = ((d.get("result") or {}).get("run") or {}).get("stdout") or ""
    if "RAE_PISTON_OK" not in out:
        raise RuntimeError("Piston smoke test failed")
    return {
        "schema_version": "1.0",
        "provider": "Piston",
        "tool": "piston_execute",
        "status": "RUNTIME_VERIFIED",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "endpoint": _base(),
        "credential_source": secret_source("PISTON_API_TOKEN"),
        "verification_class": "remote_python_execution",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code")
    ap.add_argument("--language", default="python")
    ap.add_argument("--stdin", default="")
    ap.add_argument("--list-runtimes", action="store_true")
    ap.add_argument("--smoke-test", action="store_true")
    a = ap.parse_args()
    if a.smoke_test:
        out = smoke_test()
    elif a.list_runtimes:
        out = runtimes()
    else:
        if a.code is None:
            ap.error("--code required")
        out = execute(a.code, a.language, a.stdin)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

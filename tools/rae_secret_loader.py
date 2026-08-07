#!/usr/bin/env python3
"""Credential loader for FRANK/RAE external tools.

Lookup priority:
1. process environment
2. designated private repository token store

The loader never prints secret values. Runtime secret managers can inject process
environment variables and therefore automatically take priority over the repo fallback.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_STORE = ROOT / "research_entity" / "private" / "API_TOKENS.env"
NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


class SecretError(RuntimeError):
    pass


def _parse_store(path: Path = PRIVATE_STORE) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise SecretError(f"Malformed credential-store line {lineno}")
        name, value = line.split("=", 1)
        name = name.strip()
        if not NAME_RE.fullmatch(name):
            raise SecretError(f"Invalid credential name on line {lineno}")
        values[name] = value.strip()
    return values


def get_secret(name: str, *, required: bool = True) -> str | None:
    if not NAME_RE.fullmatch(name):
        raise SecretError(f"Invalid credential name: {name!r}")
    env_value = os.environ.get(name)
    if env_value:
        return env_value
    value = _parse_store().get(name)
    if value:
        return value
    if required:
        raise SecretError(f"Credential {name} is not configured")
    return None


def secret_source(name: str) -> str | None:
    if os.environ.get(name):
        return "process_environment"
    if _parse_store().get(name):
        return "private_repo_token_store"
    return None


def status(names: Iterable[str]) -> dict[str, dict[str, object]]:
    return {
        name: {"configured": secret_source(name) is not None, "source": secret_source(name)}
        for name in names
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Check FRANK/RAE credential availability without revealing values")
    ap.add_argument("names", nargs="+", help="credential variable names")
    args = ap.parse_args()
    print(json.dumps(status(args.names), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

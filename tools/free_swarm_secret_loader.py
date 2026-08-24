#!/usr/bin/env python3
"""Provider-specific secret-file loader guarded by typed FREE admission.

Only simple KEY=VALUE dotenv syntax is accepted. Shell code is never sourced.
The admission predicate runs before any secret file is opened.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import shlex
from typing import Callable

from free_swarm_provider_admission import AdmissionError, load_admission, require_provider_free

_ALLOWED = {
    "groq": frozenset({"GROQ_API_KEY", "GROQ2_API_KEY", "GROQ3_API_KEY", "GROQ_API_KEYS"}),
    "mistral": frozenset({"MISTRAL_API_KEY", "MISTRAL2_API_KEY", "MISTRAL3_API_KEY", "MISTRAL_API_KEYS"}),
    "nvidia": frozenset({"NVIDIA_API_KEY", "NVIDIA_NIM_API_KEY", "NVIDIA2_API_KEY", "NVIDIA3_API_KEY", "NVIDIA_API_KEYS", "NGC_API_KEY"}),
}
_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _parse(text: str, allowed: frozenset[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key not in allowed or not _KEY_RE.match(key):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        out[key] = value
    return out


def load_provider_secret_files(
    admission_file: str,
    provider: str,
    paths: list[str],
    read_text: Callable[[Path], str] | None = None,
) -> dict[str, str]:
    doc = load_admission(admission_file)
    require_provider_free(doc, provider)  # MUST happen before any secret Path read.
    reader = read_text or (lambda p: p.read_text(encoding="utf-8", errors="strict"))
    values: dict[str, str] = {}
    for raw_path in paths:
        if not raw_path:
            continue
        p = Path(raw_path)
        if not p.is_file():
            continue
        values.update(_parse(reader(p), _ALLOWED[provider]))
    return values


def _main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--admission-file", required=True)
    ap.add_argument("--provider", required=True, choices=sorted(_ALLOWED))
    ap.add_argument("--file", action="append", default=[])
    args = ap.parse_args()
    try:
        values = load_provider_secret_files(args.admission_file, args.provider, args.file)
    except AdmissionError as exc:
        print(f"# ADMISSION_BLOCKED:{exc}")
        return 3
    for key in sorted(values):
        print(f"export {key}={shlex.quote(values[key])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

#!/usr/bin/env python3
"""Pre-write secret scanner for archive-assimilation artifacts.

Never emits matched secret material. Findings contain only category, path, line,
match length and a one-way SHA-256 fingerprint prefix.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

PATTERNS = [
    ("private_key_header", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("openai_or_openrouter_key", re.compile(r"\bsk-(?:or-v1-)?[A-Za-z0-9_-]{20,}\b")),
    ("groq_key", re.compile(r"\bgsk_[A-Za-z0-9_-]{20,}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("credential_assignment", re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|secret|password|passwd)\b"
        r"\s*[:=]\s*[\"']?([A-Za-z0-9_./+=:@-]{12,})"
    )),
]
TEXT_EXTS = {".txt", ".md", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".ini",
             ".cfg", ".conf", ".py", ".js", ".ts", ".tsx", ".jsx", ".sh", ".env",
             ".html", ".xml", ".csv"}

def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", "ignore")).hexdigest()[:16]

def scan_text(text: str, path: str = "<memory>") -> list[dict]:
    out, seen = [], set()
    for name, rx in PATTERNS:
        for m in rx.finditer(text):
            secret = m.group(1) if m.lastindex else m.group(0)
            key = (name, m.start(), m.end())
            if key in seen:
                continue
            seen.add(key)
            line = text.count("\n", 0, m.start()) + 1
            out.append({"category": name, "path": path, "line": line,
                        "match_length": len(secret), "fingerprint": _fingerprint(secret)})
    return out

def iter_files(inputs: list[str]):
    for raw in inputs:
        p = Path(raw)
        if p.is_file():
            yield p
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file() and (f.suffix.lower() in TEXT_EXTS or f.name.startswith(".")):
                    yield f

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    findings = []
    for p in iter_files(args.paths):
        try:
            text = p.read_text("utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        findings.extend(scan_text(text, str(p)))
    result = {"secret_material_detected": bool(findings), "findings": findings,
              "raw_secret_values_emitted": False}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for f in findings:
            print(f"{f['category']} {f['path']}:{f['line']} fp={f['fingerprint']} len={f['match_length']}")
    return 2 if findings else 0

if __name__ == "__main__":
    raise SystemExit(main())

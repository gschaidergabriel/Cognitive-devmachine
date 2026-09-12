#!/usr/bin/env python3
"""Read-only static comparison of the two observed local bridge daemons.

The tool does not import or execute either daemon. It hashes the exact files,
parses Python AST where possible, extracts operational string literals and
scores *presence of mechanisms* that matter for choosing a single writer.
Presence is not proof of correctness; the output is a forensics packet for the
next executable discriminator.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
from typing import Any

DEFAULTS = [
    Path("/home/ai-core-node/.local/share/clay-local-bridge/bin/daemon.py"),
    Path("/home/ai-core-node/.claude/star/local_bridge_daemon.py"),
]

KEYWORDS = {
    "branch_refs": ["chatgpt-local", "control", "results", "branch"],
    "idempotence": ["command_id", "command_sha", "sha256", "done", "executed", "duplicate"],
    "durable_state": ["sqlite", "sqlite3", "commit", "BEGIN IMMEDIATE", "WAL", "journal"],
    "locking": ["flock", "fcntl", "lockf", "FileLock", "lease", "mutex", "BEGIN IMMEDIATE"],
    "git_concurrency": ["fetch", "rebase", "merge-base", "fast-forward", "--force", "force-with-lease", "reset", "push"],
    "dirty_tree": ["status --porcelain", "git status", "clean", "stash", "untracked"],
    "effect_boundary": ["subprocess", "Popen", "check_call", "run(", "exec", "timeout"],
    "owner_machine": ["machine_id", "owner", "host", "hostname"],
    "secrets": ["redact", "secret", "token", "api_key", "password", "env"],
    "recovery": ["retry", "unknown", "crash", "recover", "resume", "pending", "failed"],
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def all_string_literals(tree: ast.AST) -> list[str]:
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append(node.value)
    return out


def called_names(tree: ast.AST) -> list[str]:
    out: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if isinstance(fn, ast.Name):
            out.add(fn.id)
        elif isinstance(fn, ast.Attribute):
            parts: list[str] = [fn.attr]
            v = fn.value
            while isinstance(v, ast.Attribute):
                parts.append(v.attr)
                v = v.value
            if isinstance(v, ast.Name):
                parts.append(v.id)
            out.add(".".join(reversed(parts)))
    return sorted(out)


def function_names(tree: ast.AST) -> list[str]:
    return sorted(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )


def operational_literals(strings: list[str]) -> list[str]:
    needles = (
        "git ", "sqlite", "chatgpt-", "command", "receipt", "result", "control",
        "done", "push", "fetch", "reset", "clean", "lock", "lease", "owner",
        "machine", "timeout", "stderr", "stdout",
    )
    rows: list[str] = []
    for s in strings:
        if any(n.lower() in s.lower() for n in needles):
            compact = re.sub(r"\s+", " ", s).strip()
            if compact and compact not in rows:
                rows.append(compact[:800])
    return rows[:200]


def mechanism_hits(text: str, strings: list[str], calls: list[str]) -> dict[str, list[str]]:
    corpus = "\n".join([text, *strings, *calls]).lower()
    result: dict[str, list[str]] = {}
    for group, words in KEYWORDS.items():
        hits = sorted({w for w in words if w.lower() in corpus})
        result[group] = hits
    return result


def suspicious_git_flags(strings: list[str]) -> list[str]:
    rows: list[str] = []
    for s in strings:
        low = s.lower()
        if "git" not in low and "push" not in low and "reset" not in low:
            continue
        if any(x in low for x in ("--force", " -f", "reset --hard", "clean -f")):
            rows.append(re.sub(r"\s+", " ", s).strip()[:800])
    return rows


def analyze(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    record: dict[str, Any] = {
        "path": str(path),
        "exists": True,
        "bytes": len(raw),
        "sha256": sha256(raw),
        "line_count": text.count("\n") + 1,
    }
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        record.update({
            "ast_ok": False,
            "syntax_error": {"line": exc.lineno, "offset": exc.offset, "msg": exc.msg},
        })
        strings: list[str] = []
        calls: list[str] = []
        funcs: list[str] = []
    else:
        strings = all_string_literals(tree)
        calls = called_names(tree)
        funcs = function_names(tree)
        record.update({
            "ast_ok": True,
            "functions": funcs,
            "calls": calls,
        })
    record["operational_literals"] = operational_literals(strings)
    record["mechanism_hits"] = mechanism_hits(text, strings, calls)
    record["suspicious_git_literals"] = suspicious_git_flags(strings)
    record["explicit_force_push_text"] = bool(re.search(r"push.{0,80}(--force|-f\b)", text, re.I | re.S))
    record["explicit_sqlite_text"] = "sqlite" in text.lower()
    record["explicit_file_lock_text"] = any(x in text.lower() for x in ("flock", "fcntl", "lockf", "filelock"))
    record["explicit_command_hash_text"] = bool(re.search(r"command.{0,40}(sha|hash)|sha.{0,40}command", text, re.I | re.S))
    record["explicit_machine_id_text"] = "machine_id" in text
    record["explicit_owner_text"] = bool(re.search(r"\bowner\b", text, re.I))
    return record


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", type=Path, nargs="*", default=DEFAULTS)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    rows: list[dict[str, Any]] = []
    for path in args.paths:
        p = path.expanduser().resolve()
        if not p.is_file():
            rows.append({"path": str(p), "exists": False})
        else:
            rows.append(analyze(p))

    report = {
        "schema": "CLAY_LOCAL_BRIDGE_STATIC_COMPARE/v1",
        "scope": "READ_ONLY_STATIC_NO_DAEMON_IMPORT_NO_EFFECT",
        "daemons": rows,
        "selection": "UNRESOLVED_REQUIRES_SEMANTIC_REVIEW_AND_EXECUTABLE_SINGLE_WRITER_TEST",
        "warning": "Mechanism presence is not proof that a mechanism is correct or active.",
    }
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        out = args.out.expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Deterministic Trigger-2 successor-dynamic training-ledger ancestry lint v1.

This component prevents a moving-main artifact from self-declaring an already superseded
training ledger as current. It resolves the newest ledger that existed in the candidate
commit's *parent ancestry* and compares that exact ancestry state with the candidate's
declared predecessor/current-ledger reference.

Scope: source/admission-lint component only. A PASS is only eligibility for later gates; it
mints no dataset, runtime, J-Space, HCU, EntityOS, canonical-truth, effect or training credit.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_SUCCESSOR_DYNAMIC_ANCESTRY_ADMISSION_LINT/v1"
LEDGER_SCHEMA_PREFIX = "CLAY_TRIGGER2_TRAINING_ARTIFACT_VERSION_LEDGER/v"
LEDGER_PATH_RE = re.compile(
    r"^research_entity/global/j-space/research/"
    r"\d{4}-\d{2}-\d{2}_TRIGGER2_TRAINING_ARTIFACT_VERSION_LEDGER_V(?P<version>\d+)_.*\.json$"
)
LEDGER_ID_RE = re.compile(r"^T2-LEDGER-V(?P<version>\d+)$")
CURRENT_SCOPE = "CURRENT_OR_ADMISSION"
DONOR_SCOPE = "DONOR_ONLY_HISTORICAL"
ALLOWED_SCOPES = {CURRENT_SCOPE, DONOR_SCOPE}


class LintError(RuntimeError):
    pass


@dataclass(frozen=True)
class Ledger:
    path: str
    version: int
    schema: str
    supersedes: str | None

    @property
    def ledger_id(self) -> str:
        return f"T2-LEDGER-V{self.version}"


def _run_git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise LintError("GIT_COMMAND_FAILED:" + args[0])
    return proc.stdout.strip()


def _repo_root(start: Path | None = None) -> Path:
    base = (start or Path.cwd()).resolve()
    root = _run_git(base, "rev-parse", "--show-toplevel")
    if not root:
        raise LintError("GIT_REPOSITORY_REQUIRED")
    return Path(root).resolve()


def _is_commit(root: Path, value: str) -> bool:
    proc = subprocess.run(
        ["git", "cat-file", "-e", value + "^{commit}"],
        cwd=root,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc.returncode == 0


def _single_parent(root: Path, commit: str) -> str:
    line = _run_git(root, "rev-list", "--parents", "-n", "1", commit)
    parts = line.split()
    if len(parts) != 2:
        raise LintError("CANDIDATE_COMMIT_REQUIRES_EXACTLY_ONE_PARENT")
    return parts[1]


def _tree(root: Path, commit: str) -> str:
    return _run_git(root, "rev-parse", commit + "^{tree}")


def _blob(root: Path, commit: str, path: str) -> str | None:
    proc = subprocess.run(
        ["git", "rev-parse", f"{commit}:{path}"],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if proc.returncode != 0:
        return None
    value = proc.stdout.strip()
    return value or None


def _json_at(root: Path, commit: str, path: str) -> Any:
    raw = _run_git(root, "show", f"{commit}:{path}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LintError("LEDGER_JSON_INVALID:" + path) from exc


def _ledger_paths(root: Path, commit: str) -> list[tuple[str, int]]:
    names = _run_git(root, "ls-tree", "-r", "--name-only", commit).splitlines()
    out: list[tuple[str, int]] = []
    for path in names:
        match = LEDGER_PATH_RE.match(path)
        if match:
            out.append((path, int(match.group("version"))))
    return sorted(out, key=lambda item: (item[1], item[0]))


def _normalize_ledger_ref(ref: Any, by_path: dict[str, Ledger], by_id: dict[str, Ledger]) -> str | None:
    if ref is None:
        return None
    if not isinstance(ref, str) or not ref:
        raise LintError("LEDGER_SUPERSEDES_REFERENCE_INVALID")
    if ref in by_path:
        return ref
    if ref in by_id:
        return by_id[ref].path
    basename = Path(ref).name
    matches = [path for path in by_path if Path(path).name == basename]
    if len(matches) == 1:
        return matches[0]
    raise LintError("LEDGER_SUPERSEDES_TARGET_NOT_REACHABLE:" + ref)


def resolve_parent_ledger(root: Path, parent_commit: str) -> tuple[Ledger, list[Ledger]]:
    ledgers: list[Ledger] = []
    for path, version in _ledger_paths(root, parent_commit):
        obj = _json_at(root, parent_commit, path)
        if not isinstance(obj, dict):
            raise LintError("LEDGER_OBJECT_REQUIRED:" + path)
        schema = obj.get("schema")
        if not isinstance(schema, str) or not schema.startswith(LEDGER_SCHEMA_PREFIX):
            raise LintError("LEDGER_SCHEMA_INVALID:" + path)
        ledgers.append(Ledger(path=path, version=version, schema=schema, supersedes=obj.get("supersedes")))
    if not ledgers:
        raise LintError("NO_REACHABLE_TRIGGER2_LEDGER")

    by_path = {ledger.path: ledger for ledger in ledgers}
    by_id = {ledger.ledger_id: ledger for ledger in ledgers}
    superseded_paths: set[str] = set()
    for ledger in ledgers:
        target = _normalize_ledger_ref(ledger.supersedes, by_path, by_id)
        if target is not None:
            if target == ledger.path:
                raise LintError("LEDGER_SELF_SUPERSESSION:" + ledger.path)
            superseded_paths.add(target)

    heads = [ledger for ledger in ledgers if ledger.path not in superseded_paths]
    if len(heads) != 1:
        raise LintError("AMBIGUOUS_REACHABLE_LEDGER_HEADS:" + str(len(heads)))
    return heads[0], ledgers


def _resolve_declared(ref: str, ledgers: list[Ledger]) -> Ledger | None:
    by_path = {ledger.path: ledger for ledger in ledgers}
    by_id = {ledger.ledger_id: ledger for ledger in ledgers}
    if ref in by_path:
        return by_path[ref]
    if ref in by_id:
        return by_id[ref]
    basename = Path(ref).name
    matches = [ledger for ledger in ledgers if Path(ledger.path).name == basename]
    return matches[0] if len(matches) == 1 else None


def lint(
    *,
    root: Path,
    candidate_commit: str,
    declared_ledger: str,
    scope: str,
    candidate_path: str | None = None,
) -> dict[str, Any]:
    failures: list[str] = []
    if scope not in ALLOWED_SCOPES:
        failures.append("SCOPE_INVALID")
    if not isinstance(declared_ledger, str) or not declared_ledger:
        failures.append("DECLARED_LEDGER_REQUIRED")
    if not _is_commit(root, candidate_commit):
        failures.append("CANDIDATE_COMMIT_NOT_FOUND")
    if failures:
        return _result(failures=failures)

    try:
        parent = _single_parent(root, candidate_commit)
        parent_tree = _tree(root, parent)
        candidate_tree = _tree(root, candidate_commit)
        newest, ledgers = resolve_parent_ledger(root, parent)
    except LintError as exc:
        return _result(failures=[str(exc)])

    candidate_blob = None
    if candidate_path is not None:
        candidate_blob = _blob(root, candidate_commit, candidate_path)
        if candidate_blob is None:
            failures.append("CANDIDATE_PATH_NOT_PRESENT_AT_COMMIT")

    declared = _resolve_declared(declared_ledger, ledgers)
    if declared is None:
        failures.append("DECLARED_LEDGER_NOT_REACHABLE_FROM_PARENT")

    stale = declared is not None and declared.path != newest.path
    if stale and scope == CURRENT_SCOPE:
        failures.append("STALE_ON_ARRIVAL_CURRENTNESS")

    if scope == DONOR_SCOPE:
        classification = "DONOR_ONLY_HISTORICAL_VALID_SCOPE" if declared is not None else "DONOR_ONLY_UNRESOLVED_LEDGER"
        eligible_next_gate = False
    elif stale:
        classification = "DONOR_ONLY_NEEDS_REENTRY"
        eligible_next_gate = False
    elif declared is not None:
        classification = "ELIGIBLE_FOR_NEXT_GATE_NOT_ADMITTED"
        eligible_next_gate = not failures
    else:
        classification = "BLOCKED"
        eligible_next_gate = False

    return _result(
        failures=failures,
        classification=classification,
        eligible_for_next_gate=eligible_next_gate,
        stale_on_arrival_currentness=bool(stale and scope == CURRENT_SCOPE),
        scope=scope,
        candidate_commit=candidate_commit,
        candidate_tree=candidate_tree,
        candidate_parent=parent,
        candidate_parent_tree=parent_tree,
        candidate_path=candidate_path,
        candidate_blob=candidate_blob,
        declared_ledger=declared_ledger,
        resolved_declared_ledger_path=declared.path if declared else None,
        resolved_parent_ledger_path=newest.path,
        resolved_parent_ledger_id=newest.ledger_id,
        resolved_parent_ledger_version=newest.version,
        reachable_ledger_count=len(ledgers),
    )


def _result(*, failures: list[str], **extra: Any) -> dict[str, Any]:
    failures = sorted(set(failures))
    out: dict[str, Any] = {
        "schema": SCHEMA,
        "pass": not failures,
        "failures": failures,
        "canonical_dataset_admission": False,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit_minted": False,
        "training_credit_minted": False,
    }
    out.update(extra)
    if failures:
        out.setdefault("classification", "BLOCKED")
        out.setdefault("eligible_for_next_gate", False)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-commit", required=True)
    parser.add_argument("--declared-ledger", required=True)
    parser.add_argument("--scope", choices=sorted(ALLOWED_SCOPES), default=CURRENT_SCOPE)
    parser.add_argument("--candidate-path")
    parser.add_argument("--repo-root")
    args = parser.parse_args()

    try:
        root = _repo_root(Path(args.repo_root) if args.repo_root else None)
        result = lint(
            root=root,
            candidate_commit=args.candidate_commit,
            declared_ledger=args.declared_ledger,
            scope=args.scope,
            candidate_path=args.candidate_path,
        )
    except LintError as exc:
        result = _result(failures=[str(exc)])
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("pass") else 2


if __name__ == "__main__":
    raise SystemExit(main())

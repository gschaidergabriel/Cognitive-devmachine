#!/usr/bin/env python3
"""Fail-closed lease/race guard for the EntityOS/HCU local J-Space activation probe.

This wrapper is the canonical execution ingress for unusual local activation interventions
until the underlying probe incorporates the same semantic-duplicate/race fence directly.

It does not create an experiment claim. The caller must already own the canonical create-only
claim. The wrapper validates canonical trigger-key syntax and performs the post-claim
legacy/noncanonical semantic-duplicate inspection required by
GO_EXPERIMENT_ATOMIC_LEASE_PROTOCOL.md before it can start the model intervention.

No provider credential or external provider network path is used here.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

GUARD_SCHEMA = "ENTITYOS_HCU_JSPACE_ACTIVATION_PROBE_LEASE_GUARD/v1"
CLAIM_SCHEMA = "clay-go-experiment-claim/v1"
CANON_RID_RE = re.compile(r"^rid_([0-9a-f]{64})$")
CANON_TS_RE = re.compile(r"^ts_(\d{8}T\d{12}Z)__p_([0-9a-f]{64})$")
LEGACY_DASHED_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2})-(\d{2})(?:-(\d{2}))?"
    r"([+-])(\d{2})-(\d{2})(?:__go)?__([0-9a-f]{12,64})$"
)
LEGACY_COMPACT_RE = re.compile(
    r"^(\d{8})T(\d{6})([+-])(\d{4})_([0-9a-f]{12,64})$"
)


class LeaseGuardRejected(RuntimeError):
    pass


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LeaseGuardRejected(f"{label}_UNAVAILABLE_OR_INVALID:{type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise LeaseGuardRejected(f"{label}_OBJECT_REQUIRED")
    return value


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_root() -> Path:
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise LeaseGuardRejected("CANONICAL_GIT_ROOT_REQUIRED") from exc
    path = Path(root).resolve()
    if not path.is_dir():
        raise LeaseGuardRejected("CANONICAL_GIT_ROOT_REQUIRED")
    return path


def git_head(root: Path) -> str:
    try:
        head = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise LeaseGuardRejected("CANONICAL_GIT_HEAD_REQUIRED") from exc
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise LeaseGuardRejected("CANONICAL_GIT_HEAD_INVALID")
    return head


def _parse_utc_stamp(stamp: str) -> dt.datetime:
    try:
        value = dt.datetime.strptime(stamp, "%Y%m%dT%H%M%S%fZ").replace(tzinfo=dt.timezone.utc)
    except ValueError as exc:
        raise LeaseGuardRejected("CANONICAL_TRIGGER_TIMESTAMP_INVALID") from exc
    if value.strftime("%Y%m%dT%H%M%S%fZ") != stamp:
        raise LeaseGuardRejected("CANONICAL_TRIGGER_TIMESTAMP_NONCANONICAL")
    return value


def parse_canonical_trigger_key(trigger_key: str) -> dict[str, str]:
    rid = CANON_RID_RE.fullmatch(trigger_key)
    if rid:
        return {"kind": "rid", "request_digest": rid.group(1)}
    ts = CANON_TS_RE.fullmatch(trigger_key)
    if ts:
        stamp, payload_digest = ts.groups()
        _parse_utc_stamp(stamp)
        return {"kind": "ts", "utc_stamp": stamp, "payload_digest": payload_digest}
    raise LeaseGuardRejected("CANONICAL_TRIGGER_KEY_REQUIRED")


def _to_utc_stamp(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
    sign: str,
    offset_hour: int,
    offset_minute: int,
) -> str:
    if offset_hour > 23 or offset_minute > 59:
        raise ValueError("invalid offset")
    offset_seconds = (offset_hour * 60 + offset_minute) * 60
    if sign == "-":
        offset_seconds *= -1
    tz = dt.timezone(dt.timedelta(seconds=offset_seconds))
    value = dt.datetime(year, month, day, hour, minute, second, tzinfo=tz)
    return value.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%S000000Z")


def parse_legacy_trigger_key(trigger_key: str) -> dict[str, str] | None:
    dashed = LEGACY_DASHED_RE.fullmatch(trigger_key)
    if dashed:
        (
            year, month, day, hour, minute, second, sign,
            offset_hour, offset_minute, payload_prefix
        ) = dashed.groups()
        try:
            stamp = _to_utc_stamp(
                int(year), int(month), int(day), int(hour), int(minute), int(second or "0"),
                sign, int(offset_hour), int(offset_minute)
            )
        except ValueError:
            return None
        return {"kind": "ts_legacy", "utc_stamp": stamp, "payload_prefix": payload_prefix}

    compact = LEGACY_COMPACT_RE.fullmatch(trigger_key)
    if compact:
        date_part, time_part, sign, offset_part, payload_prefix = compact.groups()
        try:
            stamp = _to_utc_stamp(
                int(date_part[0:4]), int(date_part[4:6]), int(date_part[6:8]),
                int(time_part[0:2]), int(time_part[2:4]), int(time_part[4:6]),
                sign, int(offset_part[0:2]), int(offset_part[2:4])
            )
        except ValueError:
            return None
        return {"kind": "ts_legacy", "utc_stamp": stamp, "payload_prefix": payload_prefix}
    return None


def _claim_trigger_key(path: Path) -> str | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict):
        return None
    key = value.get("trigger_key")
    return key if isinstance(key, str) and key else None


def _semantic_match(current: dict[str, str], candidate_key: str) -> bool:
    try:
        candidate = parse_canonical_trigger_key(candidate_key)
    except LeaseGuardRejected:
        candidate = None

    if candidate is not None:
        if current["kind"] == "rid":
            return candidate.get("kind") == "rid" and candidate.get("request_digest") == current["request_digest"]
        return (
            candidate.get("kind") == "ts"
            and candidate.get("utc_stamp") == current["utc_stamp"]
            and candidate.get("payload_digest") == current["payload_digest"]
        )

    legacy = parse_legacy_trigger_key(candidate_key)
    if legacy is None or current["kind"] != "ts":
        return False
    prefix = legacy["payload_prefix"]
    return (
        legacy["utc_stamp"] == current["utc_stamp"]
        and current["payload_digest"].startswith(prefix)
    )


def find_semantic_duplicate_claims(claims_dir: Path, current_claim_path: Path, trigger_key: str) -> list[str]:
    current = parse_canonical_trigger_key(trigger_key)
    duplicates: list[str] = []
    for candidate_path in sorted(claims_dir.glob("*.json")):
        resolved = candidate_path.resolve()
        if resolved == current_claim_path.resolve() or candidate_path.name.endswith(".result.json"):
            continue
        candidate_key = _claim_trigger_key(candidate_path) or candidate_path.stem
        if _semantic_match(current, candidate_key):
            duplicates.append(candidate_path.name)
    return duplicates


def validate_claim_and_race_fence(root: Path, claim_arg: str) -> dict[str, Any]:
    claims_dir = (root / "research_entity/continuity/go_experiment_claims").resolve()
    claim_path = Path(claim_arg).expanduser()
    if not claim_path.is_absolute():
        claim_path = root / claim_path
    claim_path = claim_path.resolve()
    try:
        claim_path.relative_to(claims_dir)
    except ValueError as exc:
        raise LeaseGuardRejected("ATOMIC_CLAIM_MUST_BE_IN_CANONICAL_CLAIMS_DIRECTORY") from exc
    if claim_path.name.endswith(".result.json"):
        raise LeaseGuardRejected("ATOMIC_CLAIM_RESULT_FILE_NOT_A_CLAIM")

    claim = _read_json(claim_path, "ATOMIC_CLAIM")
    if claim.get("schema") != CLAIM_SCHEMA or claim.get("trigger") != "go" or claim.get("status") != "CLAIMED":
        raise LeaseGuardRejected("ATOMIC_CLAIM_CORE_FIELDS_INVALID")
    trigger_key = claim.get("trigger_key")
    if not isinstance(trigger_key, str) or claim_path.name != f"{trigger_key}.json":
        raise LeaseGuardRejected("ATOMIC_CLAIM_TRIGGER_KEY_PATH_MISMATCH")
    identity = parse_canonical_trigger_key(trigger_key)

    duplicates = find_semantic_duplicate_claims(claims_dir, claim_path, trigger_key)
    if duplicates:
        raise LeaseGuardRejected(
            "EXPERIMENT_BUDGET_RACE_VIOLATION:" + ",".join(duplicates)
        )

    result_path = claims_dir / f"{trigger_key}.result.json"
    if result_path.exists():
        raise LeaseGuardRejected("ATOMIC_CLAIM_RESULT_ALREADY_EXISTS")

    return {
        "schema": GUARD_SCHEMA,
        "claim_path": claim_path.relative_to(root).as_posix(),
        "claim_sha256": _sha256_file(claim_path),
        "trigger_key": trigger_key,
        "trigger_identity": identity,
        "semantic_duplicate_count": 0,
        "result_path_expected": result_path.relative_to(root).as_posix(),
        "race_fence_passed": True,
        "create_only_transaction_history_reconstructed": False,
        "evidence_boundary": (
            "This guard validates the current canonical claim file and required post-claim "
            "semantic-duplicate fence. Canonical admission must separately preserve proof that "
            "the claim itself was created with GitHub create-only semantics."
        ),
    }


def _split_output_arg(argv: list[str]) -> tuple[list[str], str | None]:
    child: list[str] = []
    output: str | None = None
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--output":
            if i + 1 >= len(argv):
                raise LeaseGuardRejected("OUTPUT_ARGUMENT_VALUE_REQUIRED")
            output = argv[i + 1]
            i += 2
            continue
        if arg.startswith("--output="):
            output = arg.split("=", 1)[1]
            i += 1
            continue
        child.append(arg)
        i += 1
    return child, output


def _extract_claim_arg(argv: list[str]) -> str:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--atomic-lease-claim", required=True)
    ns, _ = parser.parse_known_args(argv)
    return ns.atomic_lease_claim


def main() -> int:
    argv = sys.argv[1:]
    root = git_root()
    head = git_head(root)
    claim_arg = _extract_claim_arg(argv)
    guard = validate_claim_and_race_fence(root, claim_arg)
    child_args, output_arg = _split_output_arg(argv)

    probe_path = root / "tools/hcu_jspace_local_activation_probe.py"
    if not probe_path.is_file():
        raise LeaseGuardRejected("UNDERLYING_ACTIVATION_PROBE_REQUIRED")
    guard.update(
        {
            "source_git_head": head,
            "guard_source_sha256": _sha256_file(Path(__file__).resolve()),
            "underlying_probe_sha256": _sha256_file(probe_path),
        }
    )

    proc = subprocess.run(
        [sys.executable, str(probe_path), *child_args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.stderr:
        sys.stderr.write(proc.stderr)

    try:
        receipt = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise LeaseGuardRejected(
            f"UNDERLYING_PROBE_NONJSON_RESULT:{proc.returncode}"
        ) from exc
    if not isinstance(receipt, dict):
        raise LeaseGuardRejected("UNDERLYING_PROBE_RECEIPT_OBJECT_REQUIRED")
    if receipt.get("source_git_head") != head:
        raise LeaseGuardRejected("UNDERLYING_PROBE_SOURCE_HEAD_MISMATCH")
    receipt["lease_runtime_fence"] = guard

    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if output_arg:
        out = Path(output_arg).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return proc.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LeaseGuardRejected as exc:
        sys.stderr.write(f"LEASE_GUARD_REJECTED:{exc}\n")
        raise SystemExit(5)

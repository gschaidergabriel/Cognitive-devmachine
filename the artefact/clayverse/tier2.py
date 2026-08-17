from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

TIER2_EXIT_CODE = 86
_FENCE_NAME = "tier2-replacement.json"
_SCHEMA = "clayverse.tier2-replacement/v1"
_POD_UID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_REASON = re.compile(r"^[a-z0-9_:-]{1,96}$")


class Tier2ReplacementBlocked(RuntimeError):
    """The current Pod sandbox may not reopen ClayVerse ingress."""


@dataclass(frozen=True)
class Tier2Fence:
    old_pod_uid: str
    reason: str
    entity_generation: int


def _state_root(state_root: str | Path) -> Path:
    root = Path(state_root)
    if not root.is_absolute():
        raise ValueError("ClayVerse state root must be absolute")
    return root


def _pod_uid(value: str) -> str:
    value = str(value or "").strip()
    if not _POD_UID.fullmatch(value):
        raise ValueError("CLAYVERSE_POD_UID is missing or invalid")
    return value


def _reason(value: str) -> str:
    value = str(value or "").strip()
    if not _REASON.fullmatch(value):
        raise ValueError("tier2 reason is missing or invalid")
    return value


def fence_path(state_root: str | Path) -> Path:
    return _state_root(state_root) / _FENCE_NAME


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def load_tier2_fence(state_root: str | Path) -> Tier2Fence | None:
    path = fence_path(state_root)
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return None
    if len(raw) > 4096:
        raise Tier2ReplacementBlocked("tier2 fence exceeds bound")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Tier2ReplacementBlocked("tier2 fence is malformed") from exc
    if not isinstance(payload, dict) or set(payload) != {
        "schema",
        "old_pod_uid",
        "reason",
        "entity_generation",
    }:
        raise Tier2ReplacementBlocked("tier2 fence shape is invalid")
    if payload.get("schema") != _SCHEMA:
        raise Tier2ReplacementBlocked("tier2 fence schema is unsupported")
    try:
        old_pod_uid = _pod_uid(payload["old_pod_uid"])
        reason = _reason(payload["reason"])
    except ValueError as exc:
        raise Tier2ReplacementBlocked("tier2 fence identity is invalid") from exc
    generation = payload["entity_generation"]
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
        raise Tier2ReplacementBlocked("tier2 fence generation is invalid")
    return Tier2Fence(old_pod_uid=old_pod_uid, reason=reason, entity_generation=generation)


def request_tier2_replacement(
    state_root: str | Path,
    *,
    current_pod_uid: str,
    reason: str,
    entity_generation: int,
) -> Tier2Fence:
    """Durably fence this Pod before asking deployment infrastructure to replace it."""
    root = _state_root(state_root)
    root.mkdir(parents=True, exist_ok=True)
    pod_uid = _pod_uid(current_pod_uid)
    reason = _reason(reason)
    if isinstance(entity_generation, bool) or not isinstance(entity_generation, int) or entity_generation < 1:
        raise ValueError("entity_generation must be a positive integer")

    fence = Tier2Fence(pod_uid, reason, entity_generation)
    payload = {
        "schema": _SCHEMA,
        "old_pod_uid": fence.old_pod_uid,
        "reason": fence.reason,
        "entity_generation": fence.entity_generation,
    }
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    tmp = root / f".{_FENCE_NAME}.{os.getpid()}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(tmp, flags, 0o600)
        try:
            os.write(fd, encoded)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(tmp, fence_path(root))
        _fsync_dir(root)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
    return fence


def assert_tier2_boot_allowed(state_root: str | Path, *, current_pod_uid: str) -> Tier2Fence | None:
    """Allow normal boot, or require a genuinely new Pod UID when a Tier-2 fence exists."""
    fence = load_tier2_fence(state_root)
    if fence is None:
        return None
    try:
        pod_uid = _pod_uid(current_pod_uid)
    except ValueError as exc:
        raise Tier2ReplacementBlocked("tier2 replacement cannot be attested without current Pod UID") from exc
    if pod_uid == fence.old_pod_uid:
        raise Tier2ReplacementBlocked("same Pod UID cannot satisfy Tier-2 replacement")
    return fence


def clear_tier2_fence_after_boot(
    state_root: str | Path,
    *,
    current_pod_uid: str,
    live_entity_generation: int,
) -> Tier2Fence | None:
    """Clear only after a new Pod boot has advanced the one global generation."""
    fence = load_tier2_fence(state_root)
    if fence is None:
        return None
    pod_uid = _pod_uid(current_pod_uid)
    if pod_uid == fence.old_pod_uid:
        raise Tier2ReplacementBlocked("same Pod UID cannot clear Tier-2 fence")
    if isinstance(live_entity_generation, bool) or not isinstance(live_entity_generation, int):
        raise Tier2ReplacementBlocked("live entity generation is invalid")
    if live_entity_generation <= fence.entity_generation:
        raise Tier2ReplacementBlocked("Tier-2 replacement did not advance global entity generation")
    path = fence_path(state_root)
    path.unlink()
    _fsync_dir(path.parent)
    return fence

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GENESIS_PATH = ROOT / "research_entity" / "ledgers" / "LEDGER_CHAIN_GENESIS.json"
CHAIN_VERSION = "RAE_LEDGER_CHAIN/v1"
CHAIN_FIELDS = ("chain_version", "chain_seq", "prev_hash", "entry_hash")


class LedgerChainError(RuntimeError):
    pass


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _compact_json(obj: dict[str, Any]) -> bytes:
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_chained_line(record: dict[str, Any]) -> bytes:
    return _compact_json(record) + b"\n"


def _entry_hash(prev_hash: str, record_without_entry_hash: dict[str, Any]) -> str:
    material = (
        CHAIN_VERSION.encode("ascii")
        + b"\0"
        + prev_hash.encode("ascii")
        + b"\0"
        + _compact_json(record_without_entry_hash)
    )
    return _sha256(material)


def load_genesis(genesis_path: Path = GENESIS_PATH) -> dict[str, Any]:
    try:
        doc = json.loads(genesis_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise LedgerChainError(f"cannot load genesis {genesis_path}: {exc}") from exc
    if doc.get("schema") != "RAE_LEDGER_CHAIN_GENESIS/v1":
        raise LedgerChainError("unsupported ledger-chain genesis schema")
    if doc.get("hash_algorithm") != "sha256":
        raise LedgerChainError("unsupported ledger-chain hash algorithm")
    if not isinstance(doc.get("ledgers"), dict):
        raise LedgerChainError("genesis ledgers map missing")
    return doc


def _ledger_key(path: Path, root: Path = ROOT) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError as exc:
        raise LedgerChainError(f"ledger outside repository root: {path}") from exc


def tracked_ledger_keys(genesis_path: Path = GENESIS_PATH) -> list[str]:
    return sorted(load_genesis(genesis_path)["ledgers"])


def _anchor_for(
    path: Path,
    *,
    genesis_path: Path = GENESIS_PATH,
    ledger_key: str | None = None,
) -> tuple[str, dict[str, Any]]:
    doc = load_genesis(genesis_path)
    key = ledger_key or _ledger_key(path)
    anchor = doc["ledgers"].get(key)
    if not isinstance(anchor, dict):
        raise LedgerChainError(f"ledger not anchored: {key}")
    return key, anchor


def verify_ledger(
    path: Path,
    *,
    genesis_path: Path = GENESIS_PATH,
    ledger_key: str | None = None,
) -> dict[str, Any]:
    path = Path(path)
    key, anchor = _anchor_for(path, genesis_path=genesis_path, ledger_key=ledger_key)
    data = path.read_bytes() if path.exists() else b""

    prefix_bytes = int(anchor["historical_byte_count"])
    prefix_lines = int(anchor["historical_line_count"])
    expected_prefix = str(anchor["historical_sha256"])

    if len(data) < prefix_bytes:
        raise LedgerChainError(
            f"{key}: historical prefix truncated: {len(data)} < {prefix_bytes} bytes"
        )

    prefix = data[:prefix_bytes]
    got_prefix = _sha256(prefix)
    if got_prefix != expected_prefix:
        raise LedgerChainError(
            f"{key}: historical prefix hash mismatch: {got_prefix} != {expected_prefix}"
        )
    if prefix.count(b"\n") != prefix_lines:
        raise LedgerChainError(
            f"{key}: historical line count mismatch: {prefix.count(b'\\n')} != {prefix_lines}"
        )
    if prefix_bytes and not prefix.endswith(b"\n"):
        raise LedgerChainError(f"{key}: historical prefix does not end on a line boundary")

    suffix = data[prefix_bytes:]
    prev_hash = expected_prefix
    appended = 0

    if suffix:
        raw_lines = suffix.splitlines(keepends=True)
        if any(not line.endswith(b"\n") for line in raw_lines):
            raise LedgerChainError(f"{key}: chained suffix contains unterminated line")
        for seq, raw in enumerate(raw_lines, 1):
            if not raw.strip():
                raise LedgerChainError(f"{key}: blank chained line at sequence {seq}")
            try:
                record = json.loads(raw.decode("utf-8"))
            except Exception as exc:
                raise LedgerChainError(f"{key}: invalid JSON at chained sequence {seq}: {exc}") from exc

            if record.get("chain_version") != CHAIN_VERSION:
                raise LedgerChainError(f"{key}: sequence {seq} has wrong chain_version")
            if record.get("chain_seq") != seq:
                raise LedgerChainError(
                    f"{key}: sequence mismatch: {record.get('chain_seq')} != {seq}"
                )
            if record.get("prev_hash") != prev_hash:
                raise LedgerChainError(
                    f"{key}: sequence {seq} prev_hash mismatch"
                )
            entry_hash = record.get("entry_hash")
            if not isinstance(entry_hash, str) or len(entry_hash) != 64:
                raise LedgerChainError(f"{key}: sequence {seq} missing valid entry_hash")

            payload = dict(record)
            payload.pop("entry_hash", None)
            expected_entry = _entry_hash(prev_hash, payload)
            if entry_hash != expected_entry:
                raise LedgerChainError(
                    f"{key}: sequence {seq} entry_hash mismatch"
                )

            canonical = canonical_chained_line(record)
            if raw != canonical:
                raise LedgerChainError(
                    f"{key}: sequence {seq} is not canonical byte serialization"
                )

            prev_hash = entry_hash
            appended = seq

    return {
        "ledger": key,
        "historical_line_count": prefix_lines,
        "historical_byte_count": prefix_bytes,
        "historical_sha256": expected_prefix,
        "appended_count": appended,
        "tail_hash": prev_hash,
        "ok": True,
    }


def prepare_chained_record(
    path: Path,
    obj: dict[str, Any],
    *,
    genesis_path: Path = GENESIS_PATH,
    ledger_key: str | None = None,
) -> dict[str, Any]:
    path = Path(path)
    key = ledger_key or _ledger_key(path)
    genesis = load_genesis(genesis_path)
    if key not in genesis["ledgers"]:
        return dict(obj)

    supplied = sorted(set(obj).intersection(CHAIN_FIELDS))
    if supplied:
        raise LedgerChainError(
            f"{key}: caller may not supply chain fields directly: {supplied}"
        )

    state = verify_ledger(path, genesis_path=genesis_path, ledger_key=key)
    record = dict(obj)
    record["chain_version"] = CHAIN_VERSION
    record["chain_seq"] = int(state["appended_count"]) + 1
    record["prev_hash"] = state["tail_hash"]
    record["entry_hash"] = _entry_hash(
        record["prev_hash"],
        {k: v for k, v in record.items() if k != "entry_hash"},
    )
    return record

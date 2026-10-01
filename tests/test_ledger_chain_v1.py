from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from rae_core.ledger_chain import (
    CHAIN_VERSION,
    LedgerChainError,
    canonical_chained_line,
    prepare_chained_record,
    verify_ledger,
)


ROOT = Path(__file__).resolve().parents[1]
TRACKED = [
    "research_entity/ledgers/CLAIMS.jsonl",
    "research_entity/ledgers/CLAIM_STATUS_EVENTS.jsonl",
    "research_entity/provenance/ARTIFACT_PROVENANCE.jsonl",
]


def _genesis(tmp_path: Path, key: str, data: bytes) -> Path:
    path = tmp_path / "GENESIS.json"
    doc = {
        "schema": "RAE_LEDGER_CHAIN_GENESIS/v1",
        "hash_algorithm": "sha256",
        "chain_version": CHAIN_VERSION,
        "ledgers": {
            key: {
                "historical_line_count": data.count(b"\n"),
                "historical_byte_count": len(data),
                "historical_sha256": hashlib.sha256(data).hexdigest(),
                "tail_line_sha256": hashlib.sha256(data.splitlines(keepends=True)[-1]).hexdigest(),
            }
        },
    }
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return path


def test_repository_ledgers_verify_at_genesis():
    for key in TRACKED:
        report = verify_ledger(ROOT / key)
        assert report["ok"] is True
        assert report["appended_count"] >= 0


def test_historical_edit_delete_reorder_fail(tmp_path: Path):
    key = "fixture.jsonl"
    rows = [
        b'{"id":"a","value":1}\n',
        b'{"id":"b","value":2}\n',
        b'{"id":"c","value":3}\n',
    ]
    original = b"".join(rows)
    ledger = tmp_path / key
    ledger.write_bytes(original)
    genesis = _genesis(tmp_path, key, original)
    assert verify_ledger(ledger, genesis_path=genesis, ledger_key=key)["ok"]

    mutations = [
        original.replace(b'"value":2', b'"value":9', 1),
        rows[0] + rows[2],
        rows[1] + rows[0] + rows[2],
    ]
    for mutated in mutations:
        ledger.write_bytes(mutated)
        with pytest.raises(LedgerChainError):
            verify_ledger(ledger, genesis_path=genesis, ledger_key=key)


def test_chained_append_and_semantic_or_byte_tamper_fail(tmp_path: Path):
    key = "fixture.jsonl"
    historical = b'{"id":"legacy"}\n'
    ledger = tmp_path / key
    ledger.write_bytes(historical)
    genesis = _genesis(tmp_path, key, historical)

    record = prepare_chained_record(
        ledger,
        {"id": "new", "value": 7},
        genesis_path=genesis,
        ledger_key=key,
    )
    assert record["chain_seq"] == 1
    assert record["prev_hash"] == hashlib.sha256(historical).hexdigest()
    ledger.write_bytes(historical + canonical_chained_line(record))
    report = verify_ledger(ledger, genesis_path=genesis, ledger_key=key)
    assert report["appended_count"] == 1
    assert report["tail_hash"] == record["entry_hash"]

    raw = ledger.read_bytes()
    ledger.write_bytes(raw.replace(b'"value":7', b'"value":8', 1))
    with pytest.raises(LedgerChainError):
        verify_ledger(ledger, genesis_path=genesis, ledger_key=key)

    ledger.write_bytes(historical + canonical_chained_line(record).replace(b',"value":7', b', "value":7', 1))
    with pytest.raises(LedgerChainError):
        verify_ledger(ledger, genesis_path=genesis, ledger_key=key)


def test_caller_cannot_mint_chain_fields(tmp_path: Path):
    key = "fixture.jsonl"
    historical = b'{"id":"legacy"}\n'
    ledger = tmp_path / key
    ledger.write_bytes(historical)
    genesis = _genesis(tmp_path, key, historical)
    with pytest.raises(LedgerChainError):
        prepare_chained_record(
            ledger,
            {"id": "bad", "prev_hash": "0" * 64},
            genesis_path=genesis,
            ledger_key=key,
        )


def test_schemas_declare_chain_fields():
    for name in ("claim.schema.json", "claim_status_event.schema.json", "provenance.schema.json"):
        schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
        props = schema["properties"]
        for field in ("chain_version", "chain_seq", "prev_hash", "entry_hash"):
            assert field in props

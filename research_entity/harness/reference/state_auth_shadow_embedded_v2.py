from __future__ import annotations

"""Compact embedded authenticated-state shadow candidate V2.

EXPERIMENTAL PHYSICAL MIGRATION ONLY.

This module is NOT activated by StateLedger and does not alter Clay semantic authority.
When explicitly instantiated it adds two physical acceleration columns to the existing
`state` table (`auth_bucket`, `auth_leaf_hash`) plus a 256-row bucket table and metadata.
StateLedger's canonical semantic_state_hash deliberately selects explicit semantic columns,
so these physical fields are outside the canonical semantic serialization.

Why this candidate exists:
V1 stores domain/key again in a separate per-key shadow table. V2 removes that duplication and
reuses authoritative row identity while retaining a rebuildable, incrementally maintainable,
tamper-detecting integrity root. Unused V2 columns can be ignored after rollback; promotion
would require an explicit migration/recovery contract before any target runtime adoption.
"""

from dataclasses import dataclass
import hashlib
import json
import sqlite3
from typing import Any

from .state_ledger import StateLedger, cjson
from .state_auth_shadow import (
    AuthShadowError,
    AuthShadowIntegrityError,
    AuthShadowVerification,
    _bucket_hash,
    _key_digest,
    _leaf_hash,
)

PROJECTION_VERSION = "AUTH_STATE_SHADOW_EMBEDDED_BUCKET256_V2"
ROOT_PREFIX = b"CLAY-AUTH-ROOT-EMBEDDED-V2\x00"

_BUCKET_SCHEMA = """
CREATE TABLE IF NOT EXISTS auth_shadow_v2_buckets(
  bucket INTEGER PRIMARY KEY CHECK(bucket>=0 AND bucket<256),
  bucket_hash BLOB NOT NULL,
  leaf_count INTEGER NOT NULL CHECK(leaf_count>=0),
  updated_epoch INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS auth_shadow_v2_meta(
  singleton_id INTEGER PRIMARY KEY CHECK(singleton_id=1),
  last_event_seq INTEGER NOT NULL CHECK(last_event_seq>=0),
  ledger_epoch INTEGER NOT NULL CHECK(ledger_epoch>=0),
  semantic_chain_hash TEXT NOT NULL,
  canonical_semantic_state_hash TEXT NOT NULL,
  domain_epochs_hash TEXT NOT NULL,
  root_hash TEXT NOT NULL,
  rebuild_count INTEGER NOT NULL CHECK(rebuild_count>=0),
  delta_refresh_count INTEGER NOT NULL CHECK(delta_refresh_count>=0),
  projection_version TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class EmbeddedAuthShadowReceiptV2:
    projection_version: str
    ledger_epoch: int
    last_event_seq: int
    semantic_chain_hash: str
    canonical_semantic_state_hash: str
    domain_epochs_hash: str
    root_hash: str
    authenticated_rows: int
    bucket_count: int
    rebuild_count: int
    delta_refresh_count: int
    verified_full: bool
    authority: str = "NON_AUTHORITATIVE_EXPERIMENTAL_PHYSICAL_INTEGRITY_SHADOW"


class EmbeddedAuthenticatedStateShadowV2:
    def __init__(self, ledger: StateLedger):
        self.ledger = ledger
        self.con = ledger.conn
        self._ensure_physical_columns()
        self.con.executescript(_BUCKET_SCHEMA)
        self.con.execute(
            "CREATE INDEX IF NOT EXISTS idx_state_auth_shadow_v2_bucket "
            "ON state(auth_bucket,domain,k)"
        )
        self.con.commit()

    def _ensure_physical_columns(self) -> None:
        columns = {str(r[1]) for r in self.con.execute("PRAGMA table_info(state)")}
        if "auth_bucket" not in columns:
            self.con.execute("ALTER TABLE state ADD COLUMN auth_bucket INTEGER")
        if "auth_leaf_hash" not in columns:
            self.con.execute("ALTER TABLE state ADD COLUMN auth_leaf_hash BLOB")

    def _meta(self):
        return self.con.execute(
            "SELECT * FROM auth_shadow_v2_meta WHERE singleton_id=1"
        ).fetchone()

    def _max_event_seq(self) -> int:
        return int(self.con.execute("SELECT COALESCE(MAX(seq),0) FROM events").fetchone()[0])

    def _domain_epochs_hash(self) -> str:
        deps = {
            str(r[0]): int(r[1])
            for r in self.con.execute("SELECT domain,epoch FROM domain_epochs ORDER BY domain")
        }
        return hashlib.sha256(cjson(deps).encode()).hexdigest()

    def _bucket_rows(self, bucket: int) -> list[tuple[bytes, bytes]]:
        rows: list[tuple[bytes, bytes]] = []
        for row in self.con.execute(
            "SELECT domain,k,auth_leaf_hash FROM state WHERE auth_bucket=?",
            (bucket,),
        ):
            if row["auth_leaf_hash"] is None:
                raise AuthShadowIntegrityError(
                    f"missing embedded leaf hash for {row['domain']}:{row['k']}"
                )
            rows.append((_key_digest(str(row["domain"]), str(row["k"])), bytes(row["auth_leaf_hash"])))
        rows.sort(key=lambda item: item[0])
        return rows

    def _root_from_buckets(self, *, ledger_epoch: int, semantic_chain_hash: str,
                           domain_epochs_hash: str) -> str:
        stored = {
            int(r[0]): bytes(r[1])
            for r in self.con.execute(
                "SELECT bucket,bucket_hash FROM auth_shadow_v2_buckets ORDER BY bucket"
            )
        }
        if len(stored) != 256:
            raise AuthShadowIntegrityError(f"expected 256 buckets, got {len(stored)}")
        hh = hashlib.sha256()
        hh.update(ROOT_PREFIX)
        hh.update(int(ledger_epoch).to_bytes(8, "big", signed=False))
        hh.update(bytes.fromhex(semantic_chain_hash))
        hh.update(bytes.fromhex(domain_epochs_hash))
        for bucket in range(256):
            hh.update(bytes([bucket]))
            hh.update(stored[bucket])
        return hh.hexdigest()

    def _recompute_bucket(self, bucket: int, *, updated_epoch: int) -> None:
        bucket_hash, leaf_count = _bucket_hash(self._bucket_rows(bucket))
        self.con.execute(
            """INSERT INTO auth_shadow_v2_buckets(bucket,bucket_hash,leaf_count,updated_epoch)
               VALUES(?,?,?,?)
               ON CONFLICT(bucket) DO UPDATE SET
                 bucket_hash=excluded.bucket_hash,
                 leaf_count=excluded.leaf_count,
                 updated_epoch=excluded.updated_epoch""",
            (bucket, bucket_hash, leaf_count, updated_epoch),
        )

    def _refresh_ref(self, domain: str, key: str, *, updated_epoch: int) -> int | None:
        row = self.con.execute(
            """SELECT domain,k,value_json,epistemic,status,domain_epoch,semantic_hash
               FROM state WHERE domain=? AND k=?""",
            (domain, key),
        ).fetchone()
        if row is None:
            # Current StateLedger preserves DELETE as a RETRACTED row; this branch exists for
            # future/foreign ledgers. Without the old physical bucket identity a hard-removed
            # row cannot be updated incrementally, so force a full rebuild rather than guess.
            return None
        key_digest = _key_digest(domain, key)
        bucket = key_digest[0]
        self.con.execute(
            "UPDATE state SET auth_bucket=?,auth_leaf_hash=? WHERE domain=? AND k=?",
            (bucket, _leaf_hash(row), domain, key),
        )
        return bucket

    def _write_meta(self, *, now: str, last_event_seq: int, rebuild_count: int,
                    delta_refresh_count: int) -> dict[str, Any]:
        chain = self.ledger._m("semantic_chain_hash")
        domain_hash = self._domain_epochs_hash()
        root = self._root_from_buckets(
            ledger_epoch=self.ledger.epoch,
            semantic_chain_hash=chain,
            domain_epochs_hash=domain_hash,
        )
        self.con.execute(
            """INSERT INTO auth_shadow_v2_meta
               (singleton_id,last_event_seq,ledger_epoch,semantic_chain_hash,
                canonical_semantic_state_hash,domain_epochs_hash,root_hash,rebuild_count,
                delta_refresh_count,projection_version,updated_at)
               VALUES(1,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(singleton_id) DO UPDATE SET
                 last_event_seq=excluded.last_event_seq,
                 ledger_epoch=excluded.ledger_epoch,
                 semantic_chain_hash=excluded.semantic_chain_hash,
                 canonical_semantic_state_hash=excluded.canonical_semantic_state_hash,
                 domain_epochs_hash=excluded.domain_epochs_hash,
                 root_hash=excluded.root_hash,
                 rebuild_count=excluded.rebuild_count,
                 delta_refresh_count=excluded.delta_refresh_count,
                 projection_version=excluded.projection_version,
                 updated_at=excluded.updated_at""",
            (
                last_event_seq,
                self.ledger.epoch,
                chain,
                self.ledger.semantic_state_hash,
                domain_hash,
                root,
                rebuild_count,
                delta_refresh_count,
                PROJECTION_VERSION,
                now,
            ),
        )
        return {"root_hash": root, "domain_epochs_hash": domain_hash}

    def full_rebuild(self, *, now: str) -> dict[str, Any]:
        self.con.execute("BEGIN IMMEDIATE")
        try:
            old = self._meta()
            rebuild_count = (int(old["rebuild_count"]) if old else 0) + 1
            delta_count = int(old["delta_refresh_count"]) if old else 0
            self.con.execute("UPDATE state SET auth_bucket=NULL,auth_leaf_hash=NULL")
            refs = list(self.con.execute("SELECT domain,k FROM state ORDER BY domain,k"))
            for row in refs:
                bucket = self._refresh_ref(
                    str(row["domain"]), str(row["k"]), updated_epoch=self.ledger.epoch
                )
                if bucket is None:
                    raise AuthShadowIntegrityError("row disappeared during rebuild")
            for bucket in range(256):
                self._recompute_bucket(bucket, updated_epoch=self.ledger.epoch)
            last_seq = self._max_event_seq()
            meta = self._write_meta(
                now=now,
                last_event_seq=last_seq,
                rebuild_count=rebuild_count,
                delta_refresh_count=delta_count,
            )
            self.con.commit()
            return {
                "mode": "FULL_REBUILD",
                "ledger_epoch": self.ledger.epoch,
                "last_event_seq": last_seq,
                "authenticated_rows": len(refs),
                "bucket_count": 256,
                **meta,
            }
        except Exception:
            self.con.rollback()
            raise

    def refresh(self, *, now: str) -> dict[str, Any]:
        meta = self._meta()
        if meta is None or str(meta["projection_version"]) != PROJECTION_VERSION:
            return self.full_rebuild(now=now)
        current_seq = self._max_event_seq()
        previous_seq = int(meta["last_event_seq"])
        if previous_seq > current_seq or int(meta["ledger_epoch"]) > self.ledger.epoch:
            return self.full_rebuild(now=now)
        if previous_seq == current_seq:
            if int(meta["ledger_epoch"]) != self.ledger.epoch:
                raise AuthShadowIntegrityError("ledger epoch changed without new authoritative event")
            if str(meta["canonical_semantic_state_hash"]) != self.ledger.semantic_state_hash:
                raise AuthShadowIntegrityError(
                    "canonical semantic state hash changed without new authoritative event"
                )
            return {
                "mode": "NO_CHANGE",
                "ledger_epoch": self.ledger.epoch,
                "last_event_seq": current_seq,
                "touched_refs": 0,
                "touched_buckets": 0,
                "root_hash": str(meta["root_hash"]),
            }

        events = list(self.con.execute(
            "SELECT seq,ops_json FROM events WHERE seq>? ORDER BY seq", (previous_seq,)
        ))
        touched: set[tuple[str, str]] = set()
        for event in events:
            try:
                ops = json.loads(event["ops_json"])
            except Exception as exc:
                raise AuthShadowIntegrityError(
                    f"unreadable event ops at seq={event['seq']}: {exc}"
                ) from exc
            for op in ops:
                domain = str(op.get("domain") or "")
                key = str(op.get("key") or "")
                if domain and key:
                    touched.add((domain, key))

        self.con.execute("BEGIN IMMEDIATE")
        try:
            touched_buckets: set[int] = set()
            for domain, key in sorted(touched):
                bucket = self._refresh_ref(
                    domain, key, updated_epoch=self.ledger.epoch
                )
                if bucket is None:
                    self.con.rollback()
                    return self.full_rebuild(now=now)
                touched_buckets.add(bucket)
            for bucket in sorted(touched_buckets):
                self._recompute_bucket(bucket, updated_epoch=self.ledger.epoch)
            out_meta = self._write_meta(
                now=now,
                last_event_seq=current_seq,
                rebuild_count=int(meta["rebuild_count"]),
                delta_refresh_count=int(meta["delta_refresh_count"]) + 1,
            )
            self.con.commit()
            return {
                "mode": "DELTA_REFRESH",
                "ledger_epoch": self.ledger.epoch,
                "last_event_seq": current_seq,
                "events_consumed": len(events),
                "touched_refs": len(touched),
                "touched_buckets": len(touched_buckets),
                **out_meta,
            }
        except Exception:
            self.con.rollback()
            raise

    def receipt(self, *, verified_full: bool = False) -> EmbeddedAuthShadowReceiptV2:
        meta = self._meta()
        if meta is None:
            raise AuthShadowError("embedded shadow not built")
        authenticated = int(self.con.execute(
            "SELECT COUNT(*) FROM state WHERE auth_bucket IS NOT NULL AND auth_leaf_hash IS NOT NULL"
        ).fetchone()[0])
        buckets = int(self.con.execute(
            "SELECT COUNT(*) FROM auth_shadow_v2_buckets"
        ).fetchone()[0])
        return EmbeddedAuthShadowReceiptV2(
            projection_version=str(meta["projection_version"]),
            ledger_epoch=int(meta["ledger_epoch"]),
            last_event_seq=int(meta["last_event_seq"]),
            semantic_chain_hash=str(meta["semantic_chain_hash"]),
            canonical_semantic_state_hash=str(meta["canonical_semantic_state_hash"]),
            domain_epochs_hash=str(meta["domain_epochs_hash"]),
            root_hash=str(meta["root_hash"]),
            authenticated_rows=authenticated,
            bucket_count=buckets,
            rebuild_count=int(meta["rebuild_count"]),
            delta_refresh_count=int(meta["delta_refresh_count"]),
            verified_full=bool(verified_full),
        )

    def verify_full(self) -> AuthShadowVerification:
        expected_by_bucket: dict[int, list[tuple[bytes, bytes]]] = {
            bucket: [] for bucket in range(256)
        }
        altered = 0
        missing = 0
        for row in self.con.execute(
            """SELECT domain,k,value_json,epistemic,status,domain_epoch,semantic_hash,
                      auth_bucket,auth_leaf_hash
               FROM state ORDER BY domain,k"""
        ):
            key_digest = _key_digest(str(row["domain"]), str(row["k"]))
            expected_leaf = _leaf_hash(row)
            if row["auth_bucket"] is None or row["auth_leaf_hash"] is None:
                missing += 1
                continue
            if int(row["auth_bucket"]) != key_digest[0] or bytes(row["auth_leaf_hash"]) != expected_leaf:
                altered += 1
            expected_by_bucket[key_digest[0]].append((key_digest, expected_leaf))

        stored_buckets = {
            int(r[0]): (bytes(r[1]), int(r[2]))
            for r in self.con.execute(
                "SELECT bucket,bucket_hash,leaf_count FROM auth_shadow_v2_buckets"
            )
        }
        expected_bucket_hashes: dict[int, bytes] = {}
        mismatched: list[int] = []
        for bucket in range(256):
            rows = sorted(expected_by_bucket[bucket], key=lambda item: item[0])
            expected_hash, expected_count = _bucket_hash(rows)
            expected_bucket_hashes[bucket] = expected_hash
            stored = stored_buckets.get(bucket)
            if stored is None or stored[0] != expected_hash or stored[1] != expected_count:
                mismatched.append(bucket)

        chain = self.ledger._m("semantic_chain_hash")
        domain_hash = self._domain_epochs_hash()
        hh = hashlib.sha256()
        hh.update(ROOT_PREFIX)
        hh.update(int(self.ledger.epoch).to_bytes(8, "big", signed=False))
        hh.update(bytes.fromhex(chain))
        hh.update(bytes.fromhex(domain_hash))
        for bucket in range(256):
            hh.update(bytes([bucket]))
            hh.update(expected_bucket_hashes[bucket])
        expected_root = hh.hexdigest()
        meta = self._meta()
        stored_root = str(meta["root_hash"]) if meta is not None else None
        meta_ok = bool(meta) and (
            int(meta["ledger_epoch"]) == self.ledger.epoch
            and int(meta["last_event_seq"]) == self._max_event_seq()
            and str(meta["semantic_chain_hash"]) == chain
            and str(meta["canonical_semantic_state_hash"]) == self.ledger.semantic_state_hash
            and str(meta["domain_epochs_hash"]) == domain_hash
            and str(meta["projection_version"]) == PROJECTION_VERSION
        )
        passed = meta_ok and missing == 0 and altered == 0 and not mismatched and stored_root == expected_root
        return AuthShadowVerification(
            passed=passed,
            ledger_epoch=self.ledger.epoch,
            expected_root_hash=expected_root,
            stored_root_hash=stored_root,
            mismatched_buckets=tuple(mismatched),
            missing_leaf_count=missing,
            extra_leaf_count=0,
            altered_leaf_count=altered,
        )

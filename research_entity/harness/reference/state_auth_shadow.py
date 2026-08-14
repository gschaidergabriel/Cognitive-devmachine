from __future__ import annotations

"""Rebuildable authenticated shadow over StateLedger state.

This candidate is deliberately NOT the canonical semantic_state_hash and grants no truth or
effect authority. It exists to test whether a small incrementally maintained integrity root can
make UnifiedDB projections cheaper to validate while retaining full rebuild/tamper detection.

The canonical StateLedger event/state semantics remain authoritative. This shadow consumes
only committed authoritative events, can be deleted/rebuilt, and must verify against the
ledger before any later architecture-promotion proposal.
"""

from dataclasses import dataclass
import hashlib
import json
import sqlite3
from typing import Any, Iterable

from .state_ledger import StateLedger, cjson

PROJECTION_VERSION = "AUTH_STATE_SHADOW_BUCKET256_V1"
LEAF_PREFIX = b"CLAY-AUTH-LEAF-V1\x00"
BUCKET_PREFIX = b"CLAY-AUTH-BUCKET-V1\x00"
ROOT_PREFIX = b"CLAY-AUTH-ROOT-V1\x00"
EMPTY_BUCKET_HASH = hashlib.sha256(b"CLAY-AUTH-BUCKET-V1:EMPTY").digest()

SCHEMA = """
CREATE TABLE IF NOT EXISTS auth_shadow_leaves(
  key_digest BLOB PRIMARY KEY,
  bucket INTEGER NOT NULL CHECK(bucket>=0 AND bucket<256),
  domain TEXT NOT NULL,
  k TEXT NOT NULL,
  leaf_hash BLOB NOT NULL,
  updated_epoch INTEGER NOT NULL,
  UNIQUE(domain,k)
);
CREATE INDEX IF NOT EXISTS idx_auth_shadow_leaves_bucket
  ON auth_shadow_leaves(bucket,key_digest);

CREATE TABLE IF NOT EXISTS auth_shadow_buckets(
  bucket INTEGER PRIMARY KEY CHECK(bucket>=0 AND bucket<256),
  bucket_hash BLOB NOT NULL,
  leaf_count INTEGER NOT NULL CHECK(leaf_count>=0),
  updated_epoch INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS auth_shadow_meta(
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


class AuthShadowError(RuntimeError):
    pass


class AuthShadowIntegrityError(AuthShadowError):
    pass


@dataclass(frozen=True)
class AuthShadowReceipt:
    projection_version: str
    ledger_epoch: int
    last_event_seq: int
    semantic_chain_hash: str
    canonical_semantic_state_hash: str
    domain_epochs_hash: str
    root_hash: str
    leaf_count: int
    bucket_count: int
    rebuild_count: int
    delta_refresh_count: int
    verified_full: bool
    authority: str = "NON_AUTHORITATIVE_REBUILDABLE_INTEGRITY_SHADOW"


@dataclass(frozen=True)
class AuthShadowVerification:
    passed: bool
    ledger_epoch: int
    expected_root_hash: str
    stored_root_hash: str | None
    mismatched_buckets: tuple[int, ...]
    missing_leaf_count: int
    extra_leaf_count: int
    altered_leaf_count: int
    authority: str = "VERIFICATION_ONLY_NO_EFFECT_AUTHORITY"


def _sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _put_len(hh: Any, data: bytes, width: int = 4) -> None:
    hh.update(len(data).to_bytes(width, "big"))
    hh.update(data)


def _key_digest(domain: str, key: str) -> bytes:
    return _sha(cjson([domain, key]).encode())


def _leaf_hash(row: sqlite3.Row) -> bytes:
    hh = hashlib.sha256()
    hh.update(LEAF_PREFIX)
    for value in (
        str(row["domain"]), str(row["k"]), str(row["epistemic"]), str(row["status"]),
        str(int(row["domain_epoch"])), str(row["semantic_hash"]),
    ):
        _put_len(hh, value.encode())
    raw_value = (row["value_json"] if row["value_json"] is not None else "null").encode()
    _put_len(hh, raw_value, width=8)
    return hh.digest()


def _bucket_hash(rows: Iterable[tuple[bytes, bytes]]) -> tuple[bytes, int]:
    hh = hashlib.sha256()
    hh.update(BUCKET_PREFIX)
    count = 0
    for key_digest, leaf_hash in rows:
        hh.update(key_digest)
        hh.update(leaf_hash)
        count += 1
    return hh.digest(), count


class AuthenticatedStateShadowV1:
    def __init__(self, ledger: StateLedger):
        self.ledger = ledger
        self.con = ledger.conn
        self.con.executescript(SCHEMA)
        self.con.commit()

    def _meta(self):
        return self.con.execute(
            "SELECT * FROM auth_shadow_meta WHERE singleton_id=1"
        ).fetchone()

    def _max_event_seq(self) -> int:
        return int(self.con.execute("SELECT COALESCE(MAX(seq),0) FROM events").fetchone()[0])

    def _domain_epochs_hash(self) -> str:
        deps = {
            str(r[0]): int(r[1])
            for r in self.con.execute("SELECT domain,epoch FROM domain_epochs ORDER BY domain")
        }
        return hashlib.sha256(cjson(deps).encode()).hexdigest()

    def _root_from_stored_buckets(self, *, ledger_epoch: int, semantic_chain_hash: str,
                                  domain_epochs_hash: str) -> str:
        rows = {
            int(r[0]): bytes(r[1])
            for r in self.con.execute(
                "SELECT bucket,bucket_hash FROM auth_shadow_buckets ORDER BY bucket"
            )
        }
        hh = hashlib.sha256()
        hh.update(ROOT_PREFIX)
        hh.update(int(ledger_epoch).to_bytes(8, "big", signed=False))
        hh.update(bytes.fromhex(semantic_chain_hash))
        hh.update(bytes.fromhex(domain_epochs_hash))
        for bucket in range(256):
            hh.update(bytes([bucket]))
            hh.update(rows.get(bucket, EMPTY_BUCKET_HASH))
        return hh.hexdigest()

    def _recompute_bucket(self, bucket: int, *, updated_epoch: int) -> None:
        rows = [
            (bytes(r[0]), bytes(r[1]))
            for r in self.con.execute(
                "SELECT key_digest,leaf_hash FROM auth_shadow_leaves "
                "WHERE bucket=? ORDER BY key_digest", (bucket,)
            )
        ]
        bucket_hash, leaf_count = _bucket_hash(rows)
        self.con.execute(
            """INSERT INTO auth_shadow_buckets(bucket,bucket_hash,leaf_count,updated_epoch)
               VALUES(?,?,?,?)
               ON CONFLICT(bucket) DO UPDATE SET
                 bucket_hash=excluded.bucket_hash,
                 leaf_count=excluded.leaf_count,
                 updated_epoch=excluded.updated_epoch""",
            (bucket, bucket_hash, leaf_count, updated_epoch),
        )

    def _upsert_ref(self, domain: str, key: str, *, updated_epoch: int) -> int:
        key_digest = _key_digest(domain, key)
        bucket = key_digest[0]
        row = self.con.execute(
            """SELECT domain,k,value_json,epistemic,status,domain_epoch,semantic_hash
               FROM state WHERE domain=? AND k=?""", (domain, key)
        ).fetchone()
        if row is None:
            self.con.execute("DELETE FROM auth_shadow_leaves WHERE key_digest=?", (key_digest,))
        else:
            self.con.execute(
                """INSERT INTO auth_shadow_leaves
                   (key_digest,bucket,domain,k,leaf_hash,updated_epoch)
                   VALUES(?,?,?,?,?,?)
                   ON CONFLICT(key_digest) DO UPDATE SET
                     bucket=excluded.bucket,
                     domain=excluded.domain,
                     k=excluded.k,
                     leaf_hash=excluded.leaf_hash,
                     updated_epoch=excluded.updated_epoch""",
                (key_digest, bucket, domain, key, _leaf_hash(row), updated_epoch),
            )
        return bucket

    def _write_meta(self, *, now: str, last_event_seq: int, rebuild_count: int,
                    delta_refresh_count: int) -> dict[str, Any]:
        chain = self.ledger._m("semantic_chain_hash")
        domain_hash = self._domain_epochs_hash()
        root = self._root_from_stored_buckets(
            ledger_epoch=self.ledger.epoch,
            semantic_chain_hash=chain,
            domain_epochs_hash=domain_hash,
        )
        self.con.execute(
            """INSERT INTO auth_shadow_meta
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
            (last_event_seq, self.ledger.epoch, chain, self.ledger.semantic_state_hash,
             domain_hash, root, rebuild_count, delta_refresh_count, PROJECTION_VERSION, now),
        )
        return {"root_hash": root, "domain_epochs_hash": domain_hash}

    def full_rebuild(self, *, now: str) -> dict[str, Any]:
        """Rebuild the entire non-authoritative shadow from current authoritative state."""
        self.con.execute("BEGIN IMMEDIATE")
        try:
            old = self._meta()
            rebuild_count = (int(old["rebuild_count"]) if old else 0) + 1
            delta_count = int(old["delta_refresh_count"]) if old else 0
            self.con.execute("DELETE FROM auth_shadow_leaves")
            self.con.execute("DELETE FROM auth_shadow_buckets")
            touched_buckets: set[int] = set()
            rows = list(self.con.execute("SELECT domain,k FROM state ORDER BY domain,k"))
            for row in rows:
                touched_buckets.add(self._upsert_ref(str(row["domain"]), str(row["k"]),
                                                     updated_epoch=self.ledger.epoch))
            for bucket in range(256):
                self._recompute_bucket(bucket, updated_epoch=self.ledger.epoch)
            last_seq = self._max_event_seq()
            meta = self._write_meta(
                now=now, last_event_seq=last_seq, rebuild_count=rebuild_count,
                delta_refresh_count=delta_count,
            )
            self.con.commit()
            return {
                "mode": "FULL_REBUILD",
                "ledger_epoch": self.ledger.epoch,
                "last_event_seq": last_seq,
                "leaf_count": len(rows),
                "bucket_count": 256,
                **meta,
            }
        except Exception:
            self.con.rollback()
            raise

    def refresh(self, *, now: str) -> dict[str, Any]:
        """Apply only refs touched by committed events since the last verified projection point."""
        meta = self._meta()
        if meta is None or str(meta["projection_version"]) != PROJECTION_VERSION:
            return self.full_rebuild(now=now)
        current_seq = self._max_event_seq()
        previous_seq = int(meta["last_event_seq"])
        if previous_seq > current_seq or int(meta["ledger_epoch"]) > self.ledger.epoch:
            return self.full_rebuild(now=now)
        if previous_seq == current_seq:
            if int(meta["ledger_epoch"]) != self.ledger.epoch:
                raise AuthShadowIntegrityError("ledger epoch changed without a new authoritative event")
            if str(meta["canonical_semantic_state_hash"]) != self.ledger.semantic_state_hash:
                raise AuthShadowIntegrityError(
                    "canonical semantic state hash changed without a new authoritative event"
                )
            return {
                "mode": "NO_CHANGE", "ledger_epoch": self.ledger.epoch,
                "last_event_seq": current_seq, "touched_refs": 0, "touched_buckets": 0,
                "root_hash": str(meta["root_hash"]),
            }

        events = list(self.con.execute(
            "SELECT seq,ops_json FROM events WHERE seq>? ORDER BY seq", (previous_seq,)
        ))
        touched: dict[tuple[str, str], int] = {}
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
                    touched[(domain, key)] = int(event["seq"])

        self.con.execute("BEGIN IMMEDIATE")
        try:
            touched_buckets: set[int] = set()
            for (domain, key), _event_seq in sorted(touched.items()):
                touched_buckets.add(self._upsert_ref(
                    domain, key, updated_epoch=self.ledger.epoch
                ))
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

    def receipt(self, *, verified_full: bool = False) -> AuthShadowReceipt:
        meta = self._meta()
        if meta is None:
            raise AuthShadowError("shadow not built")
        leaf_count = int(self.con.execute("SELECT COUNT(*) FROM auth_shadow_leaves").fetchone()[0])
        bucket_count = int(self.con.execute("SELECT COUNT(*) FROM auth_shadow_buckets").fetchone()[0])
        return AuthShadowReceipt(
            projection_version=str(meta["projection_version"]),
            ledger_epoch=int(meta["ledger_epoch"]),
            last_event_seq=int(meta["last_event_seq"]),
            semantic_chain_hash=str(meta["semantic_chain_hash"]),
            canonical_semantic_state_hash=str(meta["canonical_semantic_state_hash"]),
            domain_epochs_hash=str(meta["domain_epochs_hash"]),
            root_hash=str(meta["root_hash"]),
            leaf_count=leaf_count,
            bucket_count=bucket_count,
            rebuild_count=int(meta["rebuild_count"]),
            delta_refresh_count=int(meta["delta_refresh_count"]),
            verified_full=bool(verified_full),
        )

    def verify_full(self) -> AuthShadowVerification:
        """Independently reconstruct all leaves/buckets from StateLedger and compare the shadow."""
        expected_by_bucket: dict[int, list[tuple[bytes, bytes]]] = {
            bucket: [] for bucket in range(256)
        }
        expected_leaves: dict[bytes, bytes] = {}
        for row in self.con.execute(
            "SELECT domain,k,value_json,epistemic,status,domain_epoch,semantic_hash "
            "FROM state ORDER BY domain,k"
        ):
            key_digest = _key_digest(str(row["domain"]), str(row["k"]))
            leaf_hash = _leaf_hash(row)
            expected_leaves[key_digest] = leaf_hash
            expected_by_bucket[key_digest[0]].append((key_digest, leaf_hash))

        stored_leaves = {
            bytes(r[0]): bytes(r[1])
            for r in self.con.execute("SELECT key_digest,leaf_hash FROM auth_shadow_leaves")
        }
        missing = set(expected_leaves) - set(stored_leaves)
        extra = set(stored_leaves) - set(expected_leaves)
        altered = {
            key for key in set(expected_leaves) & set(stored_leaves)
            if expected_leaves[key] != stored_leaves[key]
        }

        stored_buckets = {
            int(r[0]): bytes(r[1])
            for r in self.con.execute("SELECT bucket,bucket_hash FROM auth_shadow_buckets")
        }
        expected_bucket_hashes: dict[int, bytes] = {}
        mismatched: list[int] = []
        for bucket in range(256):
            rows = sorted(expected_by_bucket[bucket], key=lambda item: item[0])
            bucket_hash, _count = _bucket_hash(rows)
            expected_bucket_hashes[bucket] = bucket_hash
            if stored_buckets.get(bucket) != bucket_hash:
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
        passed = (
            meta_ok and not missing and not extra and not altered and not mismatched
            and stored_root == expected_root
        )
        return AuthShadowVerification(
            passed=passed,
            ledger_epoch=self.ledger.epoch,
            expected_root_hash=expected_root,
            stored_root_hash=stored_root,
            mismatched_buckets=tuple(mismatched),
            missing_leaf_count=len(missing),
            extra_leaf_count=len(extra),
            altered_leaf_count=len(altered),
        )

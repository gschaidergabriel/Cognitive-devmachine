#!/usr/bin/env python3
"""Immutable Frankenstein-2 invocation -> canonical EntityOS effect reference binding.

This is a deterministic correlation primitive only. It does not execute effects,
mint canonical effect ids, classify outcomes, or replace EffectGate/EffectJournal.
It stores only a create-once reference from the existing Frankenstein-2
invocation_id to an effect_id already minted by the canonical effect authority.

The table lives beside the existing F2 effect lifecycle tables so same-session
overlapping calls cannot fall back to a mutable session-scoped effect pointer.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
import time


SCHEMA = "FRANKENSTEIN2_CANONICAL_EFFECT_BINDING/v1"


class CanonicalEffectBindingError(RuntimeError):
    pass


@dataclass(frozen=True)
class CanonicalEffectBinding:
    invocation_id: str
    canonical_effect_id: str
    authority_ref: str


class CanonicalEffectBindingStore:
    """Create-once 1:1 correlation index; never an effect/outcome authority."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._init_schema()

    def _con(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.path), isolation_level=None, timeout=10.0)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA busy_timeout=10000")
        con.execute("PRAGMA foreign_keys=ON")
        return con

    @staticmethod
    def _identity(value: str, label: str, *, max_len: int = 512) -> str:
        if not isinstance(value, str):
            raise CanonicalEffectBindingError(f"INVALID_{label}")
        value = value.strip()
        if not value or len(value) > max_len or "\x00" in value:
            raise CanonicalEffectBindingError(f"INVALID_{label}")
        return value

    def _init_schema(self) -> None:
        con = self._con()
        try:
            parent = con.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='effect_requests'"
            ).fetchone()
            if parent is None:
                raise CanonicalEffectBindingError("MISSING_EFFECT_LIFECYCLE_SCHEMA")
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS canonical_effect_bindings(
                  invocation_id TEXT PRIMARY KEY REFERENCES effect_requests(invocation_id),
                  canonical_effect_id TEXT NOT NULL UNIQUE,
                  authority_ref TEXT NOT NULL,
                  bound_ts REAL NOT NULL
                )
                """
            )
        finally:
            con.close()

    @staticmethod
    def _row_to_binding(row: sqlite3.Row) -> CanonicalEffectBinding:
        return CanonicalEffectBinding(
            invocation_id=row["invocation_id"],
            canonical_effect_id=row["canonical_effect_id"],
            authority_ref=row["authority_ref"],
        )

    def bind(
        self,
        invocation_id: str,
        *,
        canonical_effect_id: str,
        authority_ref: str,
        now_ts: float | None = None,
    ) -> CanonicalEffectBinding:
        """Bind one existing F2 invocation to exactly one canonical effect id.

        An exact duplicate is idempotent. Any attempt to rebind the invocation or
        reuse the canonical effect id for another invocation fails before mutation.
        """
        invocation_id = self._identity(invocation_id, "INVOCATION_ID", max_len=256)
        canonical_effect_id = self._identity(
            canonical_effect_id, "CANONICAL_EFFECT_ID", max_len=256
        )
        authority_ref = self._identity(authority_ref, "AUTHORITY_REF")
        ts = time.time() if now_ts is None else float(now_ts)

        con = self._con()
        try:
            con.execute("BEGIN IMMEDIATE")
            req = con.execute(
                "SELECT 1 FROM effect_requests WHERE invocation_id=?",
                (invocation_id,),
            ).fetchone()
            if req is None:
                raise CanonicalEffectBindingError("UNKNOWN_INVOCATION_ID")

            current = con.execute(
                "SELECT * FROM canonical_effect_bindings WHERE invocation_id=?",
                (invocation_id,),
            ).fetchone()
            if current is not None:
                binding = self._row_to_binding(current)
                if (
                    binding.canonical_effect_id == canonical_effect_id
                    and binding.authority_ref == authority_ref
                ):
                    con.execute("COMMIT")
                    return binding
                raise CanonicalEffectBindingError(
                    "INVOCATION_CANONICAL_EFFECT_REBIND_DENIED"
                )

            owner = con.execute(
                "SELECT invocation_id FROM canonical_effect_bindings "
                "WHERE canonical_effect_id=?",
                (canonical_effect_id,),
            ).fetchone()
            if owner is not None:
                raise CanonicalEffectBindingError(
                    "CANONICAL_EFFECT_ID_ALREADY_BOUND"
                )

            con.execute(
                "INSERT INTO canonical_effect_bindings"
                "(invocation_id,canonical_effect_id,authority_ref,bound_ts) "
                "VALUES(?,?,?,?)",
                (invocation_id, canonical_effect_id, authority_ref, ts),
            )
            con.execute("COMMIT")
            return CanonicalEffectBinding(
                invocation_id=invocation_id,
                canonical_effect_id=canonical_effect_id,
                authority_ref=authority_ref,
            )
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK")
            raise
        finally:
            con.close()

    def verify_observed_binding(
        self,
        *,
        target_invocation_id: str,
        observed_invocation_id: str,
        observed_effect_id: str,
        authority_ref: str,
    ) -> CanonicalEffectBinding:
        """Fail closed before result/completion use if call/effect authority cross-wire."""
        target_invocation_id = self._identity(
            target_invocation_id, "TARGET_INVOCATION_ID", max_len=256
        )
        observed_invocation_id = self._identity(
            observed_invocation_id, "OBSERVED_INVOCATION_ID", max_len=256
        )
        observed_effect_id = self._identity(
            observed_effect_id, "OBSERVED_EFFECT_ID", max_len=256
        )
        authority_ref = self._identity(authority_ref, "AUTHORITY_REF")

        if target_invocation_id != observed_invocation_id:
            raise CanonicalEffectBindingError(
                "OBSERVED_INVOCATION_ID_MISMATCH"
            )

        con = self._con()
        try:
            row = con.execute(
                "SELECT * FROM canonical_effect_bindings WHERE invocation_id=?",
                (target_invocation_id,),
            ).fetchone()
            if row is None:
                raise CanonicalEffectBindingError(
                    "CANONICAL_EFFECT_BINDING_MISSING"
                )
            binding = self._row_to_binding(row)
            if binding.canonical_effect_id != observed_effect_id:
                raise CanonicalEffectBindingError(
                    "CANONICAL_EFFECT_ID_MISMATCH"
                )
            if binding.authority_ref != authority_ref:
                raise CanonicalEffectBindingError(
                    "CANONICAL_EFFECT_AUTHORITY_MISMATCH"
                )
            return binding
        finally:
            con.close()

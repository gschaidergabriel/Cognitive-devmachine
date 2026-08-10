from __future__ import annotations

from dataclasses import dataclass
import re
import sqlite3
import time
import unicodedata

# Python's default Unicode character semantics are intentional here. The previous
# [a-z0-9] tokenizer dropped letters such as ä/ö/ü/ß and could collapse unrelated
# non-ASCII keys (for example Öl and Él) onto the same normalized key.
_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
NORMALIZER_VERSION = "unicode_nfkc_casefold_v1"


def norm(value: object) -> str:
    """Return the stable semantic-access key for multilingual text.

    NFKC removes compatibility-only representation differences, casefold gives
    language-aware caseless matching (for example German ß -> ss), and the token
    regex keeps Unicode letters/digits while excluding punctuation/underscores.
    """
    text = unicodedata.normalize("NFKC", str(value))
    return " ".join(match.group(0).casefold() for match in _TOKEN_RE.finditer(text))


@dataclass(frozen=True)
class CyclePin:
    cycle_id: str
    generation_id: str
    source_epoch: int
    graph_epoch: int
    derivation_hash: str


class CyclePinnedSemanticAccessV13:
    def __init__(self, con: sqlite3.Connection):
        self.con = con

    def pin(
        self,
        cycle_id: str,
        *,
        source_epoch: int,
        graph_epoch: int,
        pinned_at: str,
    ) -> CyclePin:
        row = self.con.execute(
            """SELECT g.generation_id,g.derivation_hash
               FROM semantic_access_head h
               JOIN semantic_access_generations g ON g.generation_id=h.generation_id
               WHERE h.head_key='CURRENT' AND g.status='CURRENT'
                 AND h.source_epoch=? AND h.graph_epoch=?
                 AND g.source_epoch=h.source_epoch AND g.graph_epoch=h.graph_epoch
                 AND g.derivation_hash=h.derivation_hash""",
            (source_epoch, graph_epoch),
        ).fetchone()
        if not row:
            raise RuntimeError("no coherent CURRENT generation for requested epochs")
        pin = CyclePin(cycle_id, row[0], source_epoch, graph_epoch, row[1])
        with self.con:
            self.con.execute(
                "INSERT INTO semantic_access_cycle_pins VALUES(?,?,?,?,?,'PINNED',?,NULL)",
                (
                    cycle_id,
                    pin.generation_id,
                    source_epoch,
                    graph_epoch,
                    pin.derivation_hash,
                    pinned_at,
                ),
            )
        return pin

    def query(self, pin: CyclePin, text: str, limit: int = 8):
        started = time.perf_counter_ns()
        if limit <= 0 or limit > 4096:
            raise ValueError("limit must be between 1 and 4096")
        normalized_key = norm(text)
        if not normalized_key:
            return (), time.perf_counter_ns() - started
        rows = self.con.execute(
            """SELECT target_record_id
               FROM semantic_access_flat_v13
               WHERE generation_id=? AND normalized_key=?
               ORDER BY path_rank,path_weight DESC,authority_rank DESC,target_record_id
               LIMIT ?""",
            (pin.generation_id, normalized_key, limit),
        ).fetchall()
        return tuple(row[0] for row in rows), time.perf_counter_ns() - started

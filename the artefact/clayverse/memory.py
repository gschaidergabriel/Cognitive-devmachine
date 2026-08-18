from __future__ import annotations
import hashlib
import json
import re
import time
import uuid
from .store import UnifiedDB

EXPLICIT = re.compile(r"(?im)^\s*(FACT|DECISION|TASK|COMMITMENT|PREFERENCE|OPEN|OPEN_QUESTION)\s*:\s*(.+?)\s*$")
EXPLICIT_LINE = re.compile(r"(?i)^\s*(FACT|DECISION|TASK|COMMITMENT|PREFERENCE|OPEN|OPEN_QUESTION)\s*:\s*(.+?)\s*$")
SEMANTIC_KINDS = {"fact", "decision", "task", "commitment", "preference", "open", "open_question"}
CONTROL_KINDS = {"source_archive", "compression_receipt", "compression_clearance"}

# Additive-only compression layer. `turns.content` is the append-only causal ledger and
# is NEVER rewritten by this module (see compact()) -- every effect, causal episode, and
# provenance chain points into turns, so a rewritten row would silently change a past
# other rows still reference. Each compression pass writes a NEW, separate row here
# instead, one per (turn_id, level), each naming its source turn id, its source digest,
# and what produced it. The original always remains reconstructable at turns.content.
# Name checked free against the 110 existing wiki.db tables before use (2026-08-18).
COMPRESSION_SCHEMA = """
CREATE TABLE IF NOT EXISTS turn_compressions(
    compression_id TEXT PRIMARY KEY,
    turn_id TEXT NOT NULL REFERENCES turns(turn_id),
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    level INTEGER NOT NULL,
    level_name TEXT NOT NULL,
    content TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    derived_from_turn_ids TEXT NOT NULL,
    extractor TEXT NOT NULL,
    prompt_version TEXT,
    created_at REAL NOT NULL,
    UNIQUE(turn_id, level)
);
CREATE INDEX IF NOT EXISTS idx_turn_compressions_turn ON turn_compressions(turn_id, level);
"""


class MemoryManager:
    """Progressive conversation compression with an extract-or-defer safety gate.

    The newest 20 turns remain full fidelity. A full-fidelity turn crosses the first
    compression boundary only when semantic coverage is demonstrably complete: either
    every non-empty line is an explicit durable marker, or a stronger extractor has
    issued a hash-bound compression clearance. Partial extraction is not enough. Once a
    turn has crossed that boundary it may age through later trace levels.

    Compression is additive, never destructive: turns.content is the append-only causal
    ledger and this class never rewrites it. Each pass appends a row to
    turn_compressions (one per turn_id x level, each naming its source turn id, source
    sha256, extractor, and timestamp); only the bookkeeping columns turns.fidelity and
    turns.compression_generation are updated to point at the current effective level.
    """

    LEVELS = (
        "full",
        "detailed_summary",
        "semantic_summary",
        "fact_decision_trace",
        "key_phrase",
        "minimum_trace",
    )

    def __init__(self, db: UnifiedDB, full_window=20):
        self.db = db
        self.full_window = full_window
        self.db.db.executescript(COMPRESSION_SCHEMA)

    def _write_compression_layer(self, row, level, text, *, extractor="ladder-v1", prompt_version="ladder-2026-08-18"):
        """Append a compression layer. Never touches turns.content; INSERT (or idempotent
        re-run) into turn_compressions only, keyed one row per (turn_id, level)."""
        compression_id = str(uuid.uuid4())
        self.db.db.execute(
            "INSERT INTO turn_compressions("
            "compression_id,turn_id,session_id,user_id,level,level_name,content,"
            "source_sha256,derived_from_turn_ids,extractor,prompt_version,created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(turn_id,level) DO UPDATE SET "
            "content=excluded.content,source_sha256=excluded.source_sha256,"
            "extractor=excluded.extractor,prompt_version=excluded.prompt_version,created_at=excluded.created_at",
            (
                compression_id,
                row["turn_id"],
                row["session_id"],
                row["user_id"],
                level,
                self.LEVELS[level],
                text,
                self._source_digest(row["content"]),
                json.dumps([row["turn_id"]]),
                extractor,
                prompt_version,
                time.time(),
            ),
        )
        return compression_id

    def _add_memory_once(self, kind, subject, value, source_turn_id, user_id, provenance):
        row = self.db.db.execute(
            "SELECT memory_id FROM durable_memory WHERE kind=? AND value=? AND source_turn_id=? AND user_id=? LIMIT 1",
            (kind, value, source_turn_id, user_id),
        ).fetchone()
        if row:
            return row[0]
        return self.db.add_memory(kind, subject, value, source_turn_id, user_id, provenance)

    def extract_explicit(self, turn_id, user_id, content):
        ids = []
        for kind, value in EXPLICIT.findall(content):
            ids.append(
                self._add_memory_once(
                    kind.lower(),
                    user_id,
                    value.strip(),
                    turn_id,
                    user_id,
                    {"extractor": "explicit-v3", "source": "precompression", "coverage": "line_explicit_only"},
                )
            )
        return ids

    @staticmethod
    def _source_digest(content):
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def _explicit_coverage_complete(content):
        lines = [line for line in content.splitlines() if line.strip()]
        return bool(lines) and all(EXPLICIT_LINE.fullmatch(line) for line in lines)

    def _semantic_count(self, turn_id):
        return int(
            self.db.db.execute(
                "SELECT COUNT(*) FROM durable_memory WHERE source_turn_id=? AND kind IN (%s)"
                % ",".join("?" for _ in SEMANTIC_KINDS),
                (turn_id, *sorted(SEMANTIC_KINDS)),
            ).fetchone()[0]
        )

    def record_semantic_clearance(self, turn_id, user_id, *, source_sha256, extractor):
        """Record complete semantic coverage from a stronger, external extractor.

        Clearance is accepted only while the exact full-fidelity source bytes still match
        the supplied digest. This prevents a stale extraction from authorizing deletion of
        different content.
        """
        row = self.db.db.execute("SELECT * FROM turns WHERE turn_id=? AND user_id=?", (turn_id, user_id)).fetchone()
        if not row or int(row["compression_generation"]) != 0:
            raise ValueError("semantic clearance requires the original full-fidelity turn")
        actual = self._source_digest(row["content"])
        if actual != source_sha256:
            raise ValueError("semantic clearance source digest mismatch")
        receipt = self.db.db.execute(
            "SELECT value FROM durable_memory WHERE kind='compression_receipt' AND source_turn_id=? LIMIT 1",
            (turn_id,),
        ).fetchone()
        if receipt and receipt["value"] != actual:
            raise ValueError("compression receipt source digest mismatch")
        return self._add_memory_once(
            "compression_clearance",
            row["session_id"],
            actual,
            turn_id,
            user_id,
            {"extractor": extractor, "coverage": "complete", "source_sha256": actual},
        )

    def _has_semantic_clearance(self, row):
        if self._explicit_coverage_complete(row["content"]):
            return True, "explicit_complete"
        digest = self._source_digest(row["content"])
        clearance = self.db.db.execute(
            "SELECT provenance FROM durable_memory WHERE kind='compression_clearance' AND source_turn_id=? AND user_id=? AND value=? LIMIT 1",
            (row["turn_id"], row["user_id"], digest),
        ).fetchone()
        if clearance:
            provenance = json.loads(clearance["provenance"])
            if provenance.get("coverage") == "complete" and provenance.get("source_sha256") == digest:
                return True, "semantic_clearance"
        return False, "incomplete_semantic_coverage"

    def _record_precompression_once(self, row, *, clearance, clearance_mode):
        self.extract_explicit(row["turn_id"], row["user_id"], row["content"])
        semantic_count = self._semantic_count(row["turn_id"])
        digest = self._source_digest(row["content"])
        existing = self.db.db.execute(
            "SELECT memory_id,provenance,value FROM durable_memory WHERE kind='compression_receipt' AND source_turn_id=? LIMIT 1",
            (row["turn_id"],),
        ).fetchone()
        provenance_update = {
            "archive": "sha256-precompression-v5-append-only",
            "lossless_source_retained": True,
            "lossless_source_location": "turns.content (never rewritten by compact())",
            "source_sha256": digest,
            "source_bytes": len(row["content"].encode("utf-8")),
            "source_words": len(row["content"].split()),
            "role": row["role"],
            "original_fidelity": row["fidelity"],
            "original_generation": int(row["compression_generation"]),
            "durable_extraction_count": semantic_count,
            "semantic_clearance": bool(clearance),
            "clearance_mode": clearance_mode,
            "status": "cleared" if clearance else "deferred_incomplete_semantic_coverage",
        }
        if existing:
            if existing["value"] != digest:
                raise ValueError("precompression source changed after receipt")
            self.db.db.execute(
                "UPDATE durable_memory SET provenance=? WHERE memory_id=?",
                (json.dumps(provenance_update, sort_keys=True), existing["memory_id"]),
            )
            return semantic_count
        self.db.add_memory(
            "compression_receipt",
            row["session_id"],
            digest,
            row["turn_id"],
            row["user_id"],
            provenance_update,
        )
        return semantic_count

    @staticmethod
    def _compress(text, level):
        words = text.split()
        if level <= 1:
            return " ".join(words[:80])
        if level == 2:
            return " ".join(words[:40])
        if level == 3:
            typed = EXPLICIT.findall(text)
            return " | ".join(f"{k}:{v.strip()}" for k, v in typed) if typed else " ".join(words[:20])
        if level == 4:
            return " ".join(words[:8])
        return " ".join(words[:2]) if words else ""

    def compact(self, session_id):
        rows = self.db.all_turns(session_id)
        n = len(rows)
        changed = 0
        compressed_turn_ids = []
        for i, row in enumerate(rows):
            age = n - i
            if age <= self.full_window:
                continue
            level = min(5, 1 + (age - self.full_window - 1) // 20)
            if row["compression_generation"] >= level:
                continue
            if int(row["compression_generation"]) == 0:
                clearance, clearance_mode = self._has_semantic_clearance(row)
                self._record_precompression_once(row, clearance=clearance, clearance_mode=clearance_mode)
                if not clearance:
                    continue
            # Additive only: the compressed text becomes a NEW row in turn_compressions,
            # derived fresh from row["content"] -- which is always the pristine original,
            # because this method no longer ever rewrites it. fidelity/compression_generation
            # on `turns` are a live "how compressed is the current view" pointer (the same
            # kind of mutable bookkeeping sessions.updated_at already is elsewhere in this
            # schema) -- turns.content itself is untouched.
            self._write_compression_layer(row, level, self._compress(row["content"], level))
            self.db.db.execute(
                "UPDATE turns SET fidelity=?, compression_generation=? WHERE turn_id=?",
                (self.LEVELS[level], level, row["turn_id"]),
            )
            compressed_turn_ids.append(row["turn_id"])
            changed += 1

        # Legacy full source archives are retired only after that exact turn crossed the
        # semantic-clearance gate. A deferred turn never loses its only recoverable source.
        # (In practice no code path in this repo ever writes a 'source_archive' durable_memory
        # row -- grepped 2026-08-18 -- so this DELETE is presently a no-op; left as-is, it is
        # not what step 1 was asked to touch.)
        if compressed_turn_ids:
            placeholders = ",".join("?" for _ in compressed_turn_ids)
            self.db.db.execute(
                f"DELETE FROM durable_memory WHERE kind='source_archive' AND source_turn_id IN ({placeholders})",
                tuple(compressed_turn_ids),
            )
        return changed

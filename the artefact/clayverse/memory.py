from __future__ import annotations
import hashlib
import re
from .store import UnifiedDB

EXPLICIT = re.compile(r"(?im)^\s*(FACT|DECISION|TASK|COMMITMENT|PREFERENCE|OPEN|OPEN_QUESTION)\s*:\s*(.+?)\s*$")
SEMANTIC_KINDS = {"fact", "decision", "task", "commitment", "preference", "open", "open_question"}


class MemoryManager:
    """Progressive conversation compression without a hidden full-text archive.

    The newest 20 turns remain full fidelity. Before any destructive compression this
    manager extracts deterministic durable markers and stores a non-reversible source
    receipt (SHA-256 + size metadata). The old conversation stream itself is then allowed
    to age down to a 1-2 word minimum trace.
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
            normalized_kind = kind.lower()
            ids.append(
                self._add_memory_once(
                    normalized_kind,
                    user_id,
                    value.strip(),
                    turn_id,
                    user_id,
                    {"extractor": "explicit-v2", "source": "precompression", "lossless_source_retained": False},
                )
            )
        return ids

    def _record_precompression_once(self, row):
        existing = self.db.db.execute(
            "SELECT memory_id FROM durable_memory WHERE kind='compression_receipt' AND source_turn_id=? LIMIT 1",
            (row["turn_id"],),
        ).fetchone()
        if existing:
            return existing[0]

        self.extract_explicit(row["turn_id"], row["user_id"], row["content"])
        raw = row["content"].encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        semantic_count = int(
            self.db.db.execute(
                "SELECT COUNT(*) FROM durable_memory WHERE source_turn_id=? AND kind IN (%s)"
                % ",".join("?" for _ in SEMANTIC_KINDS),
                (row["turn_id"], *sorted(SEMANTIC_KINDS)),
            ).fetchone()[0]
        )
        return self.db.add_memory(
            "compression_receipt",
            row["session_id"],
            digest,
            row["turn_id"],
            row["user_id"],
            {
                "archive": "sha256-precompression-v2",
                "lossless_source_retained": False,
                "source_sha256": digest,
                "source_bytes": len(raw),
                "source_words": len(row["content"].split()),
                "role": row["role"],
                "original_fidelity": row["fidelity"],
                "original_generation": int(row["compression_generation"]),
                "durable_extraction_count": semantic_count,
            },
        )

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
        for i, row in enumerate(rows):
            age = n - i
            if age <= self.full_window:
                continue
            level = min(5, 1 + (age - self.full_window - 1) // 20)
            if row["compression_generation"] >= level:
                continue
            self._record_precompression_once(row)
            self.db.db.execute(
                "UPDATE turns SET content=?, fidelity=?, compression_generation=? WHERE turn_id=?",
                (self._compress(row["content"], level), self.LEVELS[level], level, row["turn_id"]),
            )
            changed += 1

        # Candidate databases created by older artifact revisions may contain a complete
        # pre-compression transcript in source_archive. That would defeat the directive's
        # destructive conversation-stream compression. Receipts and extracted semantic
        # memories above are retained; the duplicate full-text archive is not.
        self.db.db.execute(
            "DELETE FROM durable_memory WHERE kind='source_archive' AND source_turn_id IN "
            "(SELECT turn_id FROM turns WHERE session_id=?)",
            (session_id,),
        )
        return changed

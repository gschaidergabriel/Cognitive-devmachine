from __future__ import annotations
import hashlib
import json
import re
from .store import UnifiedDB

EXPLICIT = re.compile(r"(?im)^\s*(FACT|DECISION|TASK|COMMITMENT|PREFERENCE|OPEN|OPEN_QUESTION)\s*:\s*(.+?)\s*$")
SEMANTIC_KINDS = {"fact", "decision", "task", "commitment", "preference", "open", "open_question"}


class MemoryManager:
    """Progressive conversation compression with an extract-or-defer safety gate.

    The newest 20 turns remain full fidelity. Older turns may be destructively
    compressed only after at least one durable semantic item has been extracted for
    that exact source turn. Untyped prose is therefore deferred rather than silently
    destroyed until a stronger semantic extractor records durable memory.
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

    def _semantic_count(self, turn_id):
        return int(
            self.db.db.execute(
                "SELECT COUNT(*) FROM durable_memory WHERE source_turn_id=? AND kind IN (%s)"
                % ",".join("?" for _ in SEMANTIC_KINDS),
                (turn_id, *sorted(SEMANTIC_KINDS)),
            ).fetchone()[0]
        )

    def _record_precompression_once(self, row):
        self.extract_explicit(row["turn_id"], row["user_id"], row["content"])
        semantic_count = self._semantic_count(row["turn_id"])
        existing = self.db.db.execute(
            "SELECT memory_id,provenance FROM durable_memory WHERE kind='compression_receipt' AND source_turn_id=? LIMIT 1",
            (row["turn_id"],),
        ).fetchone()
        if existing:
            provenance = json.loads(existing["provenance"])
            if int(provenance.get("durable_extraction_count", -1)) != semantic_count:
                provenance["durable_extraction_count"] = semantic_count
                provenance["status"] = "cleared" if semantic_count > 0 else "deferred_no_semantic_extraction"
                self.db.db.execute(
                    "UPDATE durable_memory SET provenance=? WHERE memory_id=?",
                    (json.dumps(provenance, sort_keys=True), existing["memory_id"]),
                )
            return semantic_count

        raw = row["content"].encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        self.db.add_memory(
            "compression_receipt",
            row["session_id"],
            digest,
            row["turn_id"],
            row["user_id"],
            {
                "archive": "sha256-precompression-v3",
                "lossless_source_retained": False,
                "source_sha256": digest,
                "source_bytes": len(raw),
                "source_words": len(row["content"].split()),
                "role": row["role"],
                "original_fidelity": row["fidelity"],
                "original_generation": int(row["compression_generation"]),
                "durable_extraction_count": semantic_count,
                "status": "cleared" if semantic_count > 0 else "deferred_no_semantic_extraction",
            },
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
            semantic_count = self._record_precompression_once(row)
            if semantic_count < 1:
                # Explicit-only extraction cannot prove that ordinary prose is disposable.
                # Keep source truth intact until a stronger extractor stores durable semantics.
                continue
            self.db.db.execute(
                "UPDATE turns SET content=?, fidelity=?, compression_generation=? WHERE turn_id=?",
                (self._compress(row["content"], level), self.LEVELS[level], level, row["turn_id"]),
            )
            compressed_turn_ids.append(row["turn_id"])
            changed += 1

        # Older artifact generations may have retained full source archives. Retire them
        # only after the corresponding turn has actually crossed the semantic-clearance
        # gate and been compressed; never delete the only recoverable copy of a deferred turn.
        if compressed_turn_ids:
            placeholders = ",".join("?" for _ in compressed_turn_ids)
            self.db.db.execute(
                f"DELETE FROM durable_memory WHERE kind='source_archive' AND source_turn_id IN ({placeholders})",
                tuple(compressed_turn_ids),
            )
        return changed

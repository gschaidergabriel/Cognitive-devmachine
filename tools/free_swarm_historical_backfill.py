#!/usr/bin/env python3
"""Historical replay/backfill for the EntityOS/HCU FREE swarm -> Evidence Forge funnel.

Purpose:
- scan *all* append-only workers.jsonl files incrementally, not just the newest tail;
- recover every explicit ARCHITECTURE_DELTA_JSON and batched historical extraction;
- preserve every successful historical worker output as a bounded extraction backlog;
- deduplicate execution-equivalent candidates while retaining append-only source provenance;
- drive historical chunks through repeated extraction passes until saturation.

No model/provider/network calls happen in this module. It only mutates the local Forge
SQLite database and therefore can run while external provider lanes are quarantined.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Any, Iterable

from free_swarm_delta_ingress import validate_delta

SINGLE_MARKER = "ARCHITECTURE_DELTA_JSON="
BATCH_MARKER = "ARCHITECTURE_DELTA_BATCH_JSON="
SCHEMA = "CLAY_FREE_SWARM_HISTORICAL_BACKFILL/v1"
PACKET_SCHEMA = "CLAY_HISTORICAL_DELTA_BACKFILL/v1"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
MAX_CHUNK_CHARS = 14_000
CHUNK_OVERLAP = 800
MAX_BATCH_DELTAS = 12
MIN_EXHAUSTIVE_ZERO_CONFIRMATIONS = 2
MAX_PASSES = 64

VOLATILE_VARIANT_KEYS = {
    "delta_id", "repair_of_candidate_hash", "repair_of_delta_id",
    "historical_source_event_id", "historical_chunk_id", "extraction_pass",
}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _json_values_after(text: str, marker: str, opener: str, closer: str) -> list[Any]:
    """Return every balanced JSON value following marker, not only the first."""
    out: list[Any] = []
    start_at = 0
    while True:
        pos = text.find(marker, start_at)
        if pos < 0:
            break
        start = text.find(opener, pos + len(marker))
        if start < 0:
            start_at = pos + len(marker)
            continue
        depth = 0
        in_str = False
        esc = False
        found_end = None
        for i in range(start, len(text)):
            c = text[i]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
                continue
            if c == '"':
                in_str = True
            elif c == opener:
                depth += 1
            elif c == closer:
                depth -= 1
                if depth == 0:
                    found_end = i + 1
                    break
        if found_end is None:
            start_at = start + 1
            continue
        try:
            out.append(json.loads(text[start:found_end]))
        except Exception:
            pass
        start_at = found_end
    return out


def explicit_deltas(text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (proposals, batch envelopes)."""
    proposals: list[dict[str, Any]] = []
    batches: list[dict[str, Any]] = []
    for obj in _json_values_after(text, SINGLE_MARKER, "{", "}"):
        if isinstance(obj, dict):
            proposals.append(obj)
    for envelope in _json_values_after(text, BATCH_MARKER, "{", "}"):
        if not isinstance(envelope, dict):
            continue
        batches.append(envelope)
        values = envelope.get("deltas")
        if not isinstance(values, list):
            continue
        for obj in values[:MAX_BATCH_DELTAS]:
            if isinstance(obj, dict):
                inherited = dict(obj)
                for key in ("historical_source_event_id", "historical_chunk_id", "extraction_pass"):
                    if key not in inherited and envelope.get(key) is not None:
                        inherited[key] = envelope.get(key)
                proposals.append(inherited)
    return proposals, batches


def _normalized_text(value: Any) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"\s+", " ", text)


def concept_identity(obj: dict[str, Any], repo_head: str) -> str:
    """Stable idea identity, intentionally independent of patch/test implementation details."""
    payload: dict[str, Any] = {}
    for key in ("hypothesis", "mechanism", "metric", "expected_direction", "falsifier", "risk"):
        if key in obj:
            payload[key] = _normalized_text(obj.get(key))
    targets = obj.get("target_files")
    payload["target_files"] = sorted(
        _normalized_text(x) for x in targets if isinstance(x, str)
    ) if isinstance(targets, list) else []
    payload["repo_head"] = repo_head or "UNBOUND"
    return sha_text(canonical(payload))


def variant_identity(obj: dict[str, Any], repo_head: str) -> str:
    """Execution-variant identity: same patch/tests at same source are one Forge candidate."""
    stable = {k: v for k, v in obj.items() if k not in VOLATILE_VARIANT_KEYS}
    stable["repo_head"] = repo_head or "UNBOUND"
    return sha_text(canonical(stable))


def source_event_identity(row: dict[str, Any], source_path: str, line_no: int, text_sha: str) -> str:
    payload = {
        "source_path": source_path,
        "line": line_no,
        "worker_id": row.get("worker_id"),
        "worker_serial": row.get("worker_serial"),
        "ts": row.get("ts"),
        "provider": row.get("provider"),
        "model": row.get("model"),
        "text_sha256": text_sha,
    }
    return sha_text(canonical(payload))


def actionability_score(text: str, role: str = "") -> float:
    low = text.lower()
    score = 0.0
    signals = [
        (SINGLE_MARKER.lower(), 0.45), (BATCH_MARKER.lower(), 0.45),
        ("patch", 0.08), ("diff", 0.08), ("test", 0.08),
        ("falsif", 0.08), ("benchmark", 0.08), ("hypothes", 0.06),
        ("race", 0.04), ("fail-closed", 0.04), ("invariant", 0.04),
    ]
    for needle, weight in signals:
        if needle in low:
            score += weight
    if re.search(r"(?m)^(?:--- a/|\+\+\+ b/|@@ -\d)", text):
        score += 0.18
    if re.search(r"(?m)\b(?:pytest|cargo test|go test|python3? -m pytest)\b", text):
        score += 0.12
    if role.upper() in {"ARCHITECT", "FALSIFIER", "CLAYCODE_FORGE", "RUNTIME", "SECURITY", "EXPERIMENT_DESIGN"}:
        score += 0.05
    if "no_delta" in low and score < 0.2:
        score -= 0.12
    return max(0.0, min(1.0, score))


def _chunks(text: str) -> Iterable[tuple[int, int, str]]:
    if not text:
        return
    if len(text) <= MAX_CHUNK_CHARS:
        yield 0, len(text), text
        return
    step = max(1, MAX_CHUNK_CHARS - CHUNK_OVERLAP)
    start = 0
    while start < len(text):
        end = min(len(text), start + MAX_CHUNK_CHARS)
        yield start, end, text[start:end]
        if end >= len(text):
            break
        start += step


def ensure_schema(con: sqlite3.Connection) -> None:
    """Additive migration only; historical Forge rows remain intact."""
    cols = {str(row[1]) for row in con.execute("PRAGMA table_info(candidates)")}
    additions = {
        "concept_id": "TEXT", "variant_id": "TEXT", "source_count": "INTEGER NOT NULL DEFAULT 1",
        "first_seen_at": "TEXT", "last_seen_at": "TEXT", "extraction_mode": "TEXT",
        "priority": "REAL NOT NULL DEFAULT 0",
    }
    for name, sql_type in additions.items():
        if name not in cols:
            con.execute(f"ALTER TABLE candidates ADD COLUMN {name} {sql_type}")
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS historical_outputs(
          source_event_id TEXT PRIMARY KEY, worker_sha TEXT NOT NULL, source_path TEXT NOT NULL,
          line_no INTEGER NOT NULL, provider TEXT, model TEXT, role TEXT, repo_head TEXT,
          text_sha256 TEXT NOT NULL, text_chars INTEGER NOT NULL, actionability REAL NOT NULL,
          explicit_proposals INTEGER NOT NULL DEFAULT 0, first_seen_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS historical_chunks(
          chunk_id TEXT PRIMARY KEY, source_event_id TEXT NOT NULL, chunk_index INTEGER NOT NULL,
          char_start INTEGER NOT NULL, char_end INTEGER NOT NULL, chunk_text TEXT NOT NULL,
          actionability REAL NOT NULL, state TEXT NOT NULL DEFAULT 'PENDING_EXTRACTION',
          extraction_passes INTEGER NOT NULL DEFAULT 0, consecutive_zero_novel INTEGER NOT NULL DEFAULT 0,
          last_novel_count INTEGER NOT NULL DEFAULT 0, last_extracted_at TEXT,
          UNIQUE(source_event_id,chunk_index)
        );
        CREATE TABLE IF NOT EXISTS candidate_sources(
          candidate_hash TEXT NOT NULL, source_event_id TEXT NOT NULL, chunk_id TEXT NOT NULL DEFAULT '',
          extractor_worker_sha TEXT NOT NULL DEFAULT '', extraction_mode TEXT NOT NULL, seen_at TEXT NOT NULL,
          PRIMARY KEY(candidate_hash,source_event_id,chunk_id,extractor_worker_sha,extraction_mode)
        );
        CREATE TABLE IF NOT EXISTS backfill_files(
          source_path TEXT PRIMARY KEY, inode INTEGER, byte_offset INTEGER NOT NULL DEFAULT 0,
          file_size INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL
        );
        """
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_historical_chunks_queue ON historical_chunks(state,actionability DESC,extraction_passes,chunk_index)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_candidates_variant ON candidates(variant_id)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_candidates_concept ON candidates(concept_id)")
    con.commit()
    _migrate_existing_candidates(con)


def _migrate_existing_candidates(con: sqlite3.Connection) -> None:
    rows = con.execute(
        "SELECT candidate_hash,proposal_json,COALESCE(repo_head,''),state,ready "
        "FROM candidates WHERE variant_id IS NULL OR concept_id IS NULL OR first_seen_at IS NULL"
    ).fetchall()
    for row in rows:
        try:
            obj = json.loads(row[1])
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue
        repo_head = str(row[2] or "").lower()
        cid = concept_identity(obj, repo_head)
        vid = variant_identity(obj, repo_head)
        stamp = now()
        con.execute(
            "UPDATE candidates SET concept_id=COALESCE(concept_id,?),variant_id=COALESCE(variant_id,?),"
            "first_seen_at=COALESCE(first_seen_at,ingested_at,?),last_seen_at=COALESCE(last_seen_at,ingested_at,?),"
            "extraction_mode=COALESCE(extraction_mode,'LEGACY_FORGE_ROW') WHERE candidate_hash=?",
            (cid, vid, stamp, stamp, row[0]),
        )
    dups = con.execute(
        "SELECT variant_id FROM candidates WHERE variant_id IS NOT NULL GROUP BY variant_id HAVING COUNT(*)>1"
    ).fetchall()
    for (vid,) in dups:
        group = con.execute(
            "SELECT candidate_hash,state,evaluated_at,ingested_at FROM candidates WHERE variant_id=? "
            "ORDER BY CASE WHEN evaluated_at IS NOT NULL THEN 0 ELSE 1 END, ingested_at, candidate_hash",
            (vid,),
        ).fetchall()
        if not group:
            continue
        canonical_hash = group[0][0]
        for candidate_hash, state, evaluated_at, _ in group[1:]:
            if evaluated_at is None and str(state).upper() in {"NEW", "NEEDS_IMPLEMENTATION"}:
                con.execute(
                    "UPDATE candidates SET state='DUPLICATE_SUPERSEDED',last_reason=? WHERE candidate_hash=?",
                    (f"same execution variant as {canonical_hash}", candidate_hash),
                )
    con.commit()


def _insert_candidate(con: sqlite3.Connection, *, obj: dict[str, Any], row: dict[str, Any], source_event_id: str, chunk_id: str, extraction_mode: str) -> tuple[bool, str]:
    valid, reasons = validate_delta(obj)
    if not valid:
        return False, "SCHEMA_INVALID:" + ",".join(reasons[:8])
    raw = canonical(obj)
    repo_head = str(row.get("repo_head_at_prompt") or "").strip().lower()
    if not COMMIT_RE.fullmatch(repo_head):
        repo_head = ""
    cid = concept_identity(obj, repo_head)
    vid = variant_identity(obj, repo_head)
    existing = con.execute(
        "SELECT candidate_hash FROM candidates WHERE variant_id=? ORDER BY evaluated_at IS NULL,ingested_at LIMIT 1",
        (vid,),
    ).fetchone()
    stamp = now()
    worker_sha = str(row.get("text_sha256") or sha_text(str(row.get("text") or "")))
    if existing:
        candidate_hash = str(existing[0])
        con.execute(
            "UPDATE candidates SET source_count=COALESCE(source_count,1)+1,last_seen_at=?,priority=MAX(COALESCE(priority,0),?) WHERE candidate_hash=?",
            (stamp, actionability_score(str(row.get("text") or ""), str(row.get("role") or "")), candidate_hash),
        )
        added = False
    else:
        candidate_hash = vid
        ready = bool(obj.get("ready_for_forge"))
        state = "NEW" if ready else "NEEDS_IMPLEMENTATION"
        con.execute(
            "INSERT INTO candidates(candidate_hash,delta_id,provider,model,role,worker_sha,repo_head,proposal_json,ready,state,ingested_at,concept_id,variant_id,source_count,first_seen_at,last_seen_at,extraction_mode,priority) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (candidate_hash, str(obj.get("delta_id") or candidate_hash[:16]), str(row.get("provider") or ""), str(row.get("model") or ""), str(row.get("role") or ""), worker_sha, repo_head, raw, int(ready), state, stamp, cid, vid, 1, stamp, stamp, extraction_mode, actionability_score(str(row.get("text") or ""), str(row.get("role") or ""))),
        )
        added = True
    con.execute(
        "INSERT OR IGNORE INTO candidate_sources(candidate_hash,source_event_id,chunk_id,extractor_worker_sha,extraction_mode,seen_at) VALUES(?,?,?,?,?,?)",
        (candidate_hash, source_event_id, chunk_id or "", worker_sha, extraction_mode, stamp),
    )
    return added, candidate_hash


def _batch_binding(con: sqlite3.Connection, value: dict[str, Any]) -> tuple[str, str, int] | None:
    """Resolve only the exact canonical chunk/source/next-pass binding."""
    chunk_id = str(value.get("historical_chunk_id") or "").strip()
    source_event_id = str(value.get("historical_source_event_id") or "").strip()
    try:
        extraction_pass = int(value.get("extraction_pass"))
    except (TypeError, ValueError):
        return None
    if not chunk_id or not source_event_id or extraction_pass <= 0:
        return None
    row = con.execute(
        "SELECT source_event_id,extraction_passes FROM historical_chunks WHERE chunk_id=?",
        (chunk_id,),
    ).fetchone()
    if not row or str(row[0]) != source_event_id:
        return None
    expected_pass = int(row[1] or 0) + 1
    if extraction_pass != expected_pass:
        return None
    return chunk_id, source_event_id, expected_pass


def _record_batch_progress(con: sqlite3.Connection, envelope: dict[str, Any], novel_count: int) -> None:
    """Advance extraction state only from an exact next-pass, bounded batch envelope.

    Saturation is deliberately conservative: only an explicitly exhaustive zero-novel
    pass contributes to the confirmation streak, and two consecutive confirmations are
    required. Non-exhaustive/missing signals and any novel result reset the streak. The
    finite pass ceiling is a visible stall state, never semantic saturation.
    """
    binding = _batch_binding(con, envelope)
    values = envelope.get("deltas")
    if binding is None or not isinstance(values, list) or len(values) > MAX_BATCH_DELTAS:
        return
    chunk_id, _, passes = binding
    row = con.execute(
        "SELECT consecutive_zero_novel FROM historical_chunks WHERE chunk_id=?",
        (chunk_id,),
    ).fetchone()
    if not row:
        return
    explicitly_exhaustive = envelope.get("exhaustive") is True
    zero = (
        int(row[0] or 0) + 1
        if explicitly_exhaustive and int(novel_count) == 0
        else 0
    )
    state = "PENDING_EXTRACTION"
    if zero >= MIN_EXHAUSTIVE_ZERO_CONFIRMATIONS:
        state = "SATURATED"
    elif passes >= MAX_PASSES:
        state = "MAX_PASSES_REACHED"
    con.execute(
        "UPDATE historical_chunks SET extraction_passes=?,consecutive_zero_novel=?,last_novel_count=?,last_extracted_at=?,state=? WHERE chunk_id=?",
        (passes, zero, int(novel_count), now(), state, chunk_id),
    )


def _ingest_worker_row(con: sqlite3.Connection, row: dict[str, Any], source_path: str, line_no: int) -> dict[str, int]:
    status = row.get("http_status")
    if not (isinstance(status, int) and 200 <= status < 300):
        return {"successful": 0, "candidates_added": 0, "chunks_added": 0, "batches": 0}
    text = str(row.get("text") or "")
    if not text:
        return {"successful": 0, "candidates_added": 0, "chunks_added": 0, "batches": 0}
    text_sha = str(row.get("text_sha256") or sha_text(text))
    event_id = source_event_identity(row, source_path, line_no, text_sha)
    proposals, batches = explicit_deltas(text)
    stamp = now()
    repo_head = str(row.get("repo_head_at_prompt") or "").strip().lower()
    if not COMMIT_RE.fullmatch(repo_head):
        repo_head = ""
    score = actionability_score(text, str(row.get("role") or ""))
    con.execute(
        "INSERT OR IGNORE INTO historical_outputs(source_event_id,worker_sha,source_path,line_no,provider,model,role,repo_head,text_sha256,text_chars,actionability,explicit_proposals,first_seen_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (event_id, text_sha, source_path, line_no, str(row.get("provider") or ""), str(row.get("model") or ""), str(row.get("role") or ""), repo_head, text_sha, len(text), score, len(proposals), stamp, stamp),
    )
    con.execute("UPDATE historical_outputs SET updated_at=?,explicit_proposals=MAX(explicit_proposals,?) WHERE source_event_id=?", (stamp, len(proposals), event_id))

    added = 0
    batch_novel: dict[str, int] = {}
    for obj in proposals:
        chunk_id = str(obj.get("historical_chunk_id") or "")
        if chunk_id and _batch_binding(con, obj) is None:
            # Model-generated causal references are input, never authority. A
            # foreign/stale/future pass cannot attach provenance or mint a candidate.
            continue
        mode = "HISTORICAL_BATCH" if chunk_id else "EXPLICIT_WORKER_DELTA"
        was_added, _ = _insert_candidate(con, obj=obj, row=row, source_event_id=event_id, chunk_id=chunk_id, extraction_mode=mode)
        added += int(was_added)
        if chunk_id:
            batch_novel[chunk_id] = batch_novel.get(chunk_id, 0) + int(was_added)
    for envelope in batches:
        chunk_id = str(envelope.get("historical_chunk_id") or "")
        _record_batch_progress(con, envelope, batch_novel.get(chunk_id, 0))

    chunks_added = 0
    if not batches:
        for idx, (start, end, chunk) in enumerate(_chunks(text)):
            chunk_id = sha_text(f"{event_id}:{idx}:{start}:{end}:{sha_text(chunk)}")
            before = con.total_changes
            con.execute(
                "INSERT OR IGNORE INTO historical_chunks(chunk_id,source_event_id,chunk_index,char_start,char_end,chunk_text,actionability,state) VALUES(?,?,?,?,?,?,?,?)",
                (chunk_id, event_id, idx, start, end, chunk, score, "PENDING_EXTRACTION"),
            )
            chunks_added += int(con.total_changes > before)
    return {"successful": 1, "candidates_added": added, "chunks_added": chunks_added, "batches": len(batches)}


def ingest_artifact_history(con: sqlite3.Connection, artifact_root: Path, *, max_new_lines: int = 50_000) -> dict[str, int]:
    """Incrementally backfill every workers.jsonl under artifact_root."""
    ensure_schema(con)
    totals = {"files_seen": 0, "lines_seen": 0, "successful_outputs": 0, "candidate_variants_added": 0, "chunks_added": 0, "batches_seen": 0}
    budget = max_new_lines
    paths = sorted(artifact_root.rglob("workers.jsonl")) if artifact_root.exists() else []
    for path in paths:
        if budget <= 0:
            break
        totals["files_seen"] += 1
        try:
            st = path.stat()
        except OSError:
            continue
        key = str(path)
        saved = con.execute("SELECT inode,byte_offset,file_size FROM backfill_files WHERE source_path=?", (key,)).fetchone()
        offset = int(saved[1] or 0) if saved else 0
        saved_inode = int(saved[0]) if saved and saved[0] is not None else None
        if saved and (saved_inode != int(st.st_ino) or int(st.st_size) < offset):
            offset = 0
        try:
            with path.open("rb") as fh:
                fh.seek(offset)
                local_line = 0
                while budget > 0:
                    pos = fh.tell()
                    raw = fh.readline()
                    if not raw:
                        break
                    if not raw.endswith(b"\n"):
                        fh.seek(pos)
                        break
                    offset = fh.tell()
                    budget -= 1
                    local_line += 1
                    totals["lines_seen"] += 1
                    try:
                        row = json.loads(raw.decode("utf-8", errors="replace"))
                    except Exception:
                        continue
                    if not isinstance(row, dict):
                        continue
                    stats = _ingest_worker_row(con, row, key, local_line)
                    totals["successful_outputs"] += stats["successful"]
                    totals["candidate_variants_added"] += stats["candidates_added"]
                    totals["chunks_added"] += stats["chunks_added"]
                    totals["batches_seen"] += stats["batches"]
        except OSError:
            continue
        con.execute(
            "INSERT INTO backfill_files(source_path,inode,byte_offset,file_size,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(source_path) DO UPDATE SET inode=excluded.inode,byte_offset=excluded.byte_offset,file_size=excluded.file_size,updated_at=excluded.updated_at",
            (key, int(st.st_ino), offset, int(st.st_size), now()),
        )
        con.commit()
    con.execute("UPDATE candidates SET state='NEEDS_IMPLEMENTATION',last_reason=COALESCE(last_reason,'historical non-ready candidate') WHERE ready=0 AND state='NEW'")
    con.commit()
    return totals


def backfill_metrics(con: sqlite3.Connection) -> dict[str, Any]:
    ensure_schema(con)
    states = {str(r[0]): int(r[1]) for r in con.execute("SELECT state,COUNT(*) FROM historical_chunks GROUP BY state")}
    outputs = int(con.execute("SELECT COUNT(*) FROM historical_outputs").fetchone()[0])
    chunks = int(con.execute("SELECT COUNT(*) FROM historical_chunks").fetchone()[0])
    source_links = int(con.execute("SELECT COUNT(*) FROM candidate_sources").fetchone()[0])
    concepts = int(con.execute("SELECT COUNT(DISTINCT concept_id) FROM candidates WHERE concept_id IS NOT NULL").fetchone()[0])
    variants = int(con.execute("SELECT COUNT(DISTINCT variant_id) FROM candidates WHERE variant_id IS NOT NULL").fetchone()[0])
    return {"schema": SCHEMA, "historical_outputs": outputs, "historical_chunks": chunks, "chunk_states": states, "candidate_source_links": source_links, "distinct_concepts": concepts, "distinct_execution_variants": variants, "pending_extraction": states.get("PENDING_EXTRACTION", 0)}


def load_backfill_packets(db_path: Path, *, limit: int = 128, max_chunk_chars: int = MAX_CHUNK_CHARS) -> list[dict[str, Any]]:
    if not db_path.exists():
        return []
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=0.5)
        con.row_factory = sqlite3.Row
        tables = {str(r[0]) for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "historical_chunks" not in tables:
            con.close()
            return []
        rows = con.execute(
            "SELECT c.*,o.provider,o.model,o.role,o.repo_head,o.text_sha256 FROM historical_chunks c JOIN historical_outputs o USING(source_event_id) WHERE c.state='PENDING_EXTRACTION' AND c.extraction_passes<? ORDER BY c.actionability DESC,c.extraction_passes ASC,c.chunk_index ASC LIMIT ?",
            (MAX_PASSES, max(1, int(limit))),
        ).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            known = [str(x[0]) for x in con.execute("SELECT DISTINCT ca.concept_id FROM candidate_sources cs JOIN candidates ca ON ca.candidate_hash=cs.candidate_hash WHERE cs.source_event_id=? AND ca.concept_id IS NOT NULL LIMIT 24", (row["source_event_id"],)).fetchall()]
            out.append({
                "schema": PACKET_SCHEMA, "historical_source_event_id": str(row["source_event_id"]),
                "historical_chunk_id": str(row["chunk_id"]), "chunk_index": int(row["chunk_index"]),
                "char_range": [int(row["char_start"]), int(row["char_end"])],
                "extraction_pass": int(row["extraction_passes"]) + 1, "max_passes": MAX_PASSES,
                "source_provider": str(row["provider"] or ""), "source_model": str(row["model"] or ""),
                "source_role": str(row["role"] or ""), "source_repo_head": str(row["repo_head"] or "") or None,
                "source_text_sha256": str(row["text_sha256"] or ""), "known_concept_ids": known,
                "chunk_text": str(row["chunk_text"] or "")[:max_chunk_chars],
                "authority": "NONCANONICAL_HISTORICAL_CANDIDATE_INPUT",
            })
        con.close()
        return out
    except Exception:
        return []

-- CLAY UnifiedDB V11 · OPTIONAL FTS5 CURRENT-SEMANTIC SEED INDEX
-- Apply only after capability verification confirms SQLite FTS5 support.
-- UnifiedDB semantic_records remains canonical truth. This virtual table is derived,
-- rebuildable retrieval acceleration only and never carries authority by itself.

PRAGMA foreign_keys=ON;
BEGIN IMMEDIATE;

CREATE VIRTUAL TABLE IF NOT EXISTS semantic_current_fts USING fts5(
  record_id UNINDEXED,
  record_kind,
  record_key,
  scope,
  payload_clay,
  tokenize='unicode61 remove_diacritics 2',
  prefix='2 3'
);

-- Idempotent rebuild of the derived index from canonical CURRENT state.
DELETE FROM semantic_current_fts;
INSERT INTO semantic_current_fts(
  rowid,record_id,record_kind,record_key,scope,payload_clay
)
SELECT
  rowid,record_id,record_kind,record_key,scope,payload_clay
FROM semantic_records
WHERE status='CURRENT'
  AND (valid_to IS NULL OR valid_to > CURRENT_TIMESTAMP);

DROP TRIGGER IF EXISTS semantic_records_fts_ai;
DROP TRIGGER IF EXISTS semantic_records_fts_ad;
DROP TRIGGER IF EXISTS semantic_records_fts_au;

CREATE TRIGGER semantic_records_fts_ai
AFTER INSERT ON semantic_records
BEGIN
  INSERT INTO semantic_current_fts(
    rowid,record_id,record_kind,record_key,scope,payload_clay
  )
  SELECT
    NEW.rowid,NEW.record_id,NEW.record_kind,NEW.record_key,NEW.scope,NEW.payload_clay
  WHERE NEW.status='CURRENT'
    AND (NEW.valid_to IS NULL OR NEW.valid_to > CURRENT_TIMESTAMP);
END;

CREATE TRIGGER semantic_records_fts_ad
AFTER DELETE ON semantic_records
BEGIN
  DELETE FROM semantic_current_fts WHERE rowid=OLD.rowid;
END;

-- One trigger body deliberately enforces delete-before-reinsert order. This avoids
-- depending on relative execution order between multiple AFTER UPDATE triggers.
CREATE TRIGGER semantic_records_fts_au
AFTER UPDATE ON semantic_records
BEGIN
  DELETE FROM semantic_current_fts WHERE rowid=OLD.rowid;
  INSERT INTO semantic_current_fts(
    rowid,record_id,record_kind,record_key,scope,payload_clay
  )
  SELECT
    NEW.rowid,NEW.record_id,NEW.record_kind,NEW.record_key,NEW.scope,NEW.payload_clay
  WHERE NEW.status='CURRENT'
    AND (NEW.valid_to IS NULL OR NEW.valid_to > CURRENT_TIMESTAMP);
END;

COMMIT;

-- Query pattern (runtime parameterizes/escapes MATCH text):
-- SELECT record_id,rank
-- FROM semantic_current_fts
-- WHERE semantic_current_fts MATCH ?
-- ORDER BY rank
-- LIMIT ?;
--
-- Optional weighted ranking when required:
-- ORDER BY bm25(semantic_current_fts,0.0,1.0,8.0,2.0,1.0)

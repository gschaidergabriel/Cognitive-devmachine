-- CLAY UnifiedDB V10 · SEMANTIC HISTORY CORRECTNESS
-- Purpose: remove the status-wide uniqueness defect that prevents >2 historical
-- versions of one semantic key while preserving exactly one CURRENT head.
-- This migration is intentionally schema-local and rollbackable from a pre-migration snapshot.

PRAGMA foreign_keys=ON;
BEGIN IMMEDIATE;

DROP VIEW IF EXISTS v_current_semantic_records;

CREATE TABLE semantic_records_v10(
  record_id TEXT PRIMARY KEY,
  record_kind TEXT NOT NULL,
  record_key TEXT NOT NULL,
  scope TEXT NOT NULL,
  epistemic_class TEXT NOT NULL,
  payload_clay TEXT NOT NULL,
  source_ref TEXT,
  source_hash TEXT,
  valid_from TEXT,
  valid_to TEXT,
  status TEXT NOT NULL,
  source_epoch INTEGER,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

INSERT INTO semantic_records_v10(
  record_id,record_kind,record_key,scope,epistemic_class,payload_clay,
  source_ref,source_hash,valid_from,valid_to,status,source_epoch,created_at,updated_at
)
SELECT
  record_id,record_kind,record_key,scope,epistemic_class,payload_clay,
  source_ref,source_hash,valid_from,valid_to,status,source_epoch,created_at,updated_at
FROM semantic_records;

DROP TABLE semantic_records;
ALTER TABLE semantic_records_v10 RENAME TO semantic_records;

-- Hot lookup over current semantic state.
CREATE INDEX idx_semantic_records_lookup
  ON semantic_records(record_kind,record_key,scope,status);

-- History/replay traversal must scale by semantic identity and epoch.
CREATE INDEX idx_semantic_records_history
  ON semantic_records(record_kind,record_key,scope,source_epoch DESC,updated_at DESC);

-- Exactly one CURRENT head per semantic identity, while allowing arbitrarily many
-- SUPERSEDED/RETIRED/etc historical rows.
CREATE UNIQUE INDEX uq_semantic_records_current
  ON semantic_records(record_kind,record_key,scope)
  WHERE status='CURRENT';

CREATE VIEW v_current_semantic_records AS
SELECT * FROM semantic_records
WHERE status='CURRENT' AND (valid_to IS NULL OR valid_to > CURRENT_TIMESTAMP);

COMMIT;

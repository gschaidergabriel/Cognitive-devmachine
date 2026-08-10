-- CLAY U10 CANDIDATE · EPOCH-COHERENT CONTEXT RETRIEVAL PROJECTION
-- Status: RESEARCH_CANDIDATE, not canonical/promotion.
-- UnifiedDB remains semantic authority; this is a rebuildable read projection.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS clay_semantic_bindings(
  logical_id TEXT PRIMARY KEY,
  record_id TEXT NOT NULL REFERENCES semantic_records(record_id) ON DELETE CASCADE,
  binding_class TEXT NOT NULL,
  source_epoch INTEGER,
  confidence REAL NOT NULL DEFAULT 1.0,
  source_ref TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_clay_semantic_binding_record ON clay_semantic_bindings(record_id);

CREATE TABLE IF NOT EXISTS clay_retrieval_policy(
  epistemic_class TEXT PRIMARY KEY,
  admissibility_rank INTEGER NOT NULL CHECK(admissibility_rank BETWEEN 0 AND 9),
  default_admit INTEGER NOT NULL CHECK(default_admit IN (0,1)),
  policy_note TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clay_current_semantic_projection(
  logical_id TEXT PRIMARY KEY,
  record_id TEXT NOT NULL UNIQUE,
  record_kind TEXT NOT NULL,
  record_key TEXT NOT NULL,
  scope TEXT NOT NULL,
  source_epoch INTEGER,
  epistemic_class TEXT NOT NULL,
  admissibility_rank INTEGER NOT NULL,
  valid_from TEXT,
  valid_to TEXT,
  projection_epoch INTEGER NOT NULL,
  policy_hash TEXT NOT NULL,
  source_hash TEXT,
  rebuilt_at TEXT NOT NULL
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_clay_current_projection_kind_key ON clay_current_semantic_projection(record_kind,record_key,scope);
CREATE INDEX IF NOT EXISTS idx_clay_current_projection_epoch ON clay_current_semantic_projection(projection_epoch,source_epoch);

CREATE TABLE IF NOT EXISTS clay_projection_rebuild_receipts(
  rebuild_receipt_id TEXT PRIMARY KEY,
  projection_kind TEXT NOT NULL,
  source_epoch INTEGER,
  projection_epoch INTEGER NOT NULL,
  as_of_time TEXT NOT NULL,
  policy_hash TEXT NOT NULL,
  input_rows INTEGER NOT NULL,
  output_rows INTEGER NOT NULL,
  rejected_rows INTEGER NOT NULL,
  duration_ms REAL NOT NULL,
  projection_hash TEXT NOT NULL,
  verification_clay TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_clay_projection_rebuild_epoch ON clay_projection_rebuild_receipts(projection_kind,projection_epoch DESC);

CREATE TABLE IF NOT EXISTS clay_context_query_receipts(
  context_query_id TEXT PRIMARY KEY,
  cycle_id TEXT,
  source_epoch INTEGER,
  graph_epoch INTEGER,
  projection_epoch INTEGER NOT NULL,
  mode TEXT NOT NULL CHECK(mode IN ('DIRECT','LOCAL_GRAPH','TEMPORAL','CONFLICT','MIXED')),
  seed_logical_id TEXT,
  relation_type TEXT,
  hop_limit INTEGER NOT NULL DEFAULT 0 CHECK(hop_limit BETWEEN 0 AND 32),
  query_intent_clay TEXT NOT NULL,
  policy_hash TEXT NOT NULL,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  duration_ms REAL,
  result_hash TEXT,
  status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clay_context_result_receipts(
  context_query_id TEXT NOT NULL REFERENCES clay_context_query_receipts(context_query_id) ON DELETE CASCADE,
  ordinal INTEGER NOT NULL,
  logical_id TEXT NOT NULL,
  record_id TEXT,
  path_clay TEXT NOT NULL DEFAULT '[]',
  evidence_clay TEXT NOT NULL DEFAULT '{}',
  admissibility_rank INTEGER NOT NULL,
  selected INTEGER NOT NULL CHECK(selected IN (0,1)),
  suppression_reason TEXT,
  PRIMARY KEY(context_query_id,ordinal)
);

CREATE VIEW IF NOT EXISTS v_clay_context_projection_health AS
SELECT p.projection_epoch,
       COUNT(*) AS projected_rows,
       MIN(p.source_epoch) AS min_source_epoch,
       MAX(p.source_epoch) AS max_source_epoch,
       MAX(p.rebuilt_at) AS rebuilt_at
FROM clay_current_semantic_projection p
GROUP BY p.projection_epoch;

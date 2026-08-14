-- CLAY U10 · SEMANTIC ACCESS FABRIC
-- Candidate migration. UnifiedDB remains semantic authority; this file adds only
-- provenance-bound semantic access keys, rebuildable hot projections and receipts.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS semantic_query_seeds(
  seed_version_id TEXT PRIMARY KEY,
  seed_id TEXT NOT NULL,
  normalized_key TEXT NOT NULL,
  logical_id TEXT NOT NULL,
  seed_class TEXT NOT NULL CHECK(seed_class IN ('CANONICAL','ALIAS','INTENT_SIGNATURE','MODEL_PROPOSED')),
  confidence REAL NOT NULL CHECK(confidence >= 0.0 AND confidence <= 1.0),
  provenance_clay TEXT NOT NULL,
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER,
  status TEXT NOT NULL CHECK(status IN ('CURRENT','SUPERSEDED','QUARANTINED','CANDIDATE')),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_semantic_query_seed_id_current
ON semantic_query_seeds(seed_id) WHERE status='CURRENT';

CREATE UNIQUE INDEX IF NOT EXISTS idx_semantic_query_key_current
ON semantic_query_seeds(normalized_key) WHERE status='CURRENT';

CREATE INDEX IF NOT EXISTS idx_semantic_query_seed_lookup
ON semantic_query_seeds(normalized_key,logical_id,confidence DESC,seed_id)
WHERE status='CURRENT';

CREATE TABLE IF NOT EXISTS semantic_access_projection(
  projection_version_id TEXT PRIMARY KEY,
  seed_id TEXT NOT NULL,
  target_record_id TEXT NOT NULL,
  target_logical_id TEXT NOT NULL,
  path_rank INTEGER NOT NULL CHECK(path_rank > 0),
  hop_count INTEGER NOT NULL CHECK(hop_count >= 0),
  path_weight REAL NOT NULL,
  authority_rank REAL NOT NULL DEFAULT 0.0,
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER NOT NULL,
  derivation_hash TEXT NOT NULL,
  path_clay TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('CURRENT','SUPERSEDED','QUARANTINED')),
  created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_semantic_access_unique_current
ON semantic_access_projection(seed_id,target_record_id)
WHERE status='CURRENT';

CREATE INDEX IF NOT EXISTS idx_semantic_access_hot
ON semantic_access_projection(seed_id,path_rank,path_weight DESC,authority_rank DESC,target_record_id)
WHERE status='CURRENT';

CREATE INDEX IF NOT EXISTS idx_semantic_access_target
ON semantic_access_projection(target_logical_id,graph_epoch DESC,seed_id)
WHERE status='CURRENT';

CREATE TABLE IF NOT EXISTS semantic_query_receipts_v10(
  query_receipt_id TEXT PRIMARY KEY,
  cycle_id TEXT,
  node_id TEXT,
  query_digest TEXT NOT NULL,
  seed_id TEXT,
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER NOT NULL,
  retrieval_mode TEXT NOT NULL CHECK(retrieval_mode IN ('SEMANTIC_SEED_FASTPATH','HYBRID_RRF_FALLBACK','LEXICAL_FALLBACK','MISS')),
  candidate_refs_clay TEXT NOT NULL,
  selected_refs_clay TEXT NOT NULL,
  suppressed_refs_clay TEXT NOT NULL,
  ranking_clay TEXT NOT NULL,
  admissibility_clay TEXT NOT NULL,
  latency_ns INTEGER,
  result_hash TEXT,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_semantic_query_receipts_v10_cycle
ON semantic_query_receipts_v10(cycle_id,created_at DESC);

CREATE VIEW IF NOT EXISTS v_current_semantic_query_seeds AS
SELECT * FROM semantic_query_seeds WHERE status='CURRENT';

CREATE VIEW IF NOT EXISTS v_current_semantic_access_projection AS
SELECT p.*
FROM semantic_access_projection p
JOIN semantic_query_seeds s ON s.seed_id=p.seed_id
WHERE p.status='CURRENT' AND s.status='CURRENT'
  AND p.source_epoch=s.source_epoch
  AND (s.graph_epoch IS NULL OR p.graph_epoch=s.graph_epoch);

-- Semantic safety:
-- * normalized_key/seed_id are access handles, not truth.
-- * MODEL_PROPOSED seeds may retrieve candidates but cannot promote authority.
-- * source_epoch/graph_epoch mismatch invalidates the fast path.
-- * projection is append-only/versioned and rebuildable from UnifiedDB + ClayGraph.

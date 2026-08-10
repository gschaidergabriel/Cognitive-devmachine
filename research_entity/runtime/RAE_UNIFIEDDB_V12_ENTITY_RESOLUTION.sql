-- CLAY U12 · EVIDENCE-BOUND ENTITY RESOLUTION
-- Candidate. Aliases are retrieval handles only; they never mint identity/truth/authority.
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS semantic_entity_aliases(
  alias_version_id TEXT PRIMARY KEY,
  alias_norm TEXT NOT NULL,
  logical_id TEXT NOT NULL,
  alias_class TEXT NOT NULL CHECK(alias_class IN ('CANONICAL','EXPLICIT','DOCUMENT_DERIVED','MODEL_PROPOSED')),
  confidence REAL NOT NULL CHECK(confidence>=0.0 AND confidence<=1.0),
  source_epoch INTEGER NOT NULL,
  provenance_clay TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('CURRENT','SUPERSEDED','QUARANTINED','CANDIDATE')),
  created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_entity_alias_current
ON semantic_entity_aliases(alias_norm,logical_id,alias_class) WHERE status='CURRENT';
CREATE INDEX IF NOT EXISTS idx_entity_alias_logical
ON semantic_entity_aliases(logical_id,source_epoch DESC,confidence DESC) WHERE status='CURRENT';
CREATE VIRTUAL TABLE IF NOT EXISTS semantic_entity_alias_fts USING fts5(
  alias_version_id UNINDEXED,alias_norm,logical_id UNINDEXED,tokenize='unicode61 remove_diacritics 2',prefix='2 3 4'
);
CREATE TABLE IF NOT EXISTS semantic_entity_resolution_receipts(
  receipt_id TEXT PRIMARY KEY,query_hash TEXT NOT NULL,source_epoch INTEGER NOT NULL,
  candidate_refs_clay TEXT NOT NULL,selected_logical_id TEXT,resolution_class TEXT NOT NULL
    CHECK(resolution_class IN ('EXACT_LOGICAL_ID','EVIDENCE_ALIAS','AMBIGUOUS','LOW_CONFIDENCE','MISS')),
  score_clay TEXT NOT NULL,latency_ns INTEGER,created_at TEXT NOT NULL
);

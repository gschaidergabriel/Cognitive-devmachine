-- CLAY U11 · COHERENT SEMANTIC ACCESS GENERATIONS
-- Candidate migration layered on U10. Prevents mixed projection generations while
-- preserving UnifiedDB semantic authority and rebuildable ClayGraph-derived access.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS semantic_access_generations(
  generation_id TEXT PRIMARY KEY,
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER NOT NULL,
  derivation_id TEXT NOT NULL,
  derivation_hash TEXT NOT NULL,
  seed_count INTEGER NOT NULL DEFAULT 0,
  path_count INTEGER NOT NULL DEFAULT 0,
  verification_clay TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL CHECK(status IN ('STAGING','VERIFIED','CURRENT','SUPERSEDED','QUARANTINED')),
  created_at TEXT NOT NULL,
  verified_at TEXT,
  published_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_semantic_access_generation_epoch
ON semantic_access_generations(source_epoch,graph_epoch,status,created_at DESC);

CREATE TABLE IF NOT EXISTS semantic_access_projection_v11(
  generation_id TEXT NOT NULL REFERENCES semantic_access_generations(generation_id) ON DELETE CASCADE,
  seed_id TEXT NOT NULL,
  target_record_id TEXT NOT NULL,
  target_logical_id TEXT NOT NULL,
  path_rank INTEGER NOT NULL CHECK(path_rank > 0),
  hop_count INTEGER NOT NULL CHECK(hop_count >= 0),
  path_weight REAL NOT NULL,
  authority_rank REAL NOT NULL DEFAULT 0.0,
  path_clay TEXT NOT NULL,
  PRIMARY KEY(generation_id,seed_id,target_record_id)
);
CREATE INDEX IF NOT EXISTS idx_semantic_access_v11_hot
ON semantic_access_projection_v11(generation_id,seed_id,path_rank,path_weight DESC,authority_rank DESC,target_record_id);
CREATE INDEX IF NOT EXISTS idx_semantic_access_v11_target
ON semantic_access_projection_v11(generation_id,target_logical_id,seed_id);

CREATE TABLE IF NOT EXISTS semantic_access_head(
  head_key TEXT PRIMARY KEY CHECK(head_key='CURRENT'),
  generation_id TEXT NOT NULL REFERENCES semantic_access_generations(generation_id),
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER NOT NULL,
  derivation_hash TEXT NOT NULL,
  published_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS semantic_access_generation_receipts(
  receipt_id TEXT PRIMARY KEY,
  generation_id TEXT NOT NULL REFERENCES semantic_access_generations(generation_id),
  receipt_class TEXT NOT NULL CHECK(receipt_class IN ('BUILD','VERIFY','PUBLISH','ROLLBACK','QUARANTINE')),
  evidence_clay TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_semantic_access_generation_receipt
ON semantic_access_generation_receipts(generation_id,created_at);

CREATE VIEW IF NOT EXISTS v_current_semantic_access_v11 AS
SELECT p.*,g.source_epoch,g.graph_epoch,g.derivation_hash
FROM semantic_access_head h
JOIN semantic_access_generations g ON g.generation_id=h.generation_id
JOIN semantic_access_projection_v11 p ON p.generation_id=g.generation_id
WHERE h.head_key='CURRENT' AND g.status='CURRENT'
  AND g.source_epoch=h.source_epoch AND g.graph_epoch=h.graph_epoch
  AND g.derivation_hash=h.derivation_hash;

-- Publication law:
-- 1. Build the entire generation under STAGING.
-- 2. Verify seed/path counts, graph/source epochs, derivation hash and required invariants.
-- 3. Mark generation VERIFIED.
-- 4. In ONE transaction: supersede previous CURRENT generation, mark new generation CURRENT,
--    and UPSERT semantic_access_head. Readers therefore see either old or new generation, never a mix.
-- 5. Empty/failed generations never replace the last-known-good head.

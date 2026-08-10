-- CLAYGRAPH V3 · MATERIALIZED SEMANTIC ACCESS PATHS
-- Derived/rebuildable topology only. Activation/accessibility never becomes truth.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS graph_semantic_access_paths(
  access_path_version_id TEXT PRIMARY KEY,
  seed_id TEXT NOT NULL,
  seed_logical_id TEXT NOT NULL,
  target_logical_id TEXT NOT NULL,
  graph_epoch INTEGER NOT NULL REFERENCES graph_epochs(graph_epoch),
  source_epoch INTEGER NOT NULL,
  path_rank INTEGER NOT NULL CHECK(path_rank > 0),
  hop_count INTEGER NOT NULL CHECK(hop_count >= 0),
  path_weight REAL NOT NULL,
  relation_signature TEXT NOT NULL,
  provenance_clay TEXT NOT NULL,
  admissibility_clay TEXT NOT NULL,
  derivation_hash TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('CURRENT','SUPERSEDED','QUARANTINED')),
  created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_graph_access_unique_current
ON graph_semantic_access_paths(seed_id,target_logical_id,graph_epoch)
WHERE status='CURRENT';

CREATE INDEX IF NOT EXISTS idx_graph_access_hot
ON graph_semantic_access_paths(seed_id,graph_epoch,path_rank,path_weight DESC,target_logical_id)
WHERE status='CURRENT';

CREATE INDEX IF NOT EXISTS idx_graph_access_target
ON graph_semantic_access_paths(target_logical_id,graph_epoch DESC,seed_id)
WHERE status='CURRENT';

CREATE TABLE IF NOT EXISTS graph_semantic_access_build_receipts(
  build_receipt_id TEXT PRIMARY KEY,
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER NOT NULL REFERENCES graph_epochs(graph_epoch),
  derivation_id TEXT NOT NULL,
  derivation_hash TEXT NOT NULL,
  seed_count INTEGER NOT NULL,
  path_count INTEGER NOT NULL,
  max_hops INTEGER NOT NULL,
  build_latency_ns INTEGER,
  source_refs_clay TEXT NOT NULL,
  rebuild_recipe_clay TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE VIEW IF NOT EXISTS v_current_graph_semantic_access_paths AS
SELECT p.*
FROM graph_semantic_access_paths p
JOIN (
  SELECT seed_id,target_logical_id,MAX(graph_epoch) ge
  FROM graph_semantic_access_paths
  WHERE status='CURRENT'
  GROUP BY seed_id,target_logical_id
) x
ON x.seed_id=p.seed_id AND x.target_logical_id=p.target_logical_id AND x.ge=p.graph_epoch
WHERE p.status='CURRENT';

-- Runtime rule: publish paths only after a coherent graph epoch is complete.
-- Invalidation rule: any relevant source/edge change queues rebuild; stale epoch => reject fast path.

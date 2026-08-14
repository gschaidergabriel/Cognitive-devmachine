-- CLAYGRAPH V4 · VERIFIED ACCESS PLANS
-- Candidate migration. Separates planning, verification and publication of rebuildable
-- semantic access paths. ClayGraph remains derived topology and never truth/authority.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS graph_semantic_access_plans(
  plan_id TEXT PRIMARY KEY,
  seed_id TEXT NOT NULL,
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER NOT NULL REFERENCES graph_epochs(graph_epoch),
  planner_id TEXT NOT NULL,
  planner_hash TEXT NOT NULL,
  topology_hash TEXT NOT NULL,
  max_hops INTEGER NOT NULL CHECK(max_hops >= 0),
  candidate_path_count INTEGER NOT NULL DEFAULT 0,
  selected_path_count INTEGER NOT NULL DEFAULT 0,
  counterevidence_path_count INTEGER NOT NULL DEFAULT 0,
  verification_clay TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL CHECK(status IN ('STAGING','VERIFIED','REJECTED','SUPERSEDED')),
  created_at TEXT NOT NULL,
  verified_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_graph_access_plan_epoch
ON graph_semantic_access_plans(graph_epoch,source_epoch,status,seed_id);

CREATE TABLE IF NOT EXISTS graph_semantic_access_plan_paths(
  plan_id TEXT NOT NULL REFERENCES graph_semantic_access_plans(plan_id) ON DELETE CASCADE,
  path_id TEXT NOT NULL,
  target_logical_id TEXT NOT NULL,
  path_rank INTEGER NOT NULL CHECK(path_rank > 0),
  hop_count INTEGER NOT NULL CHECK(hop_count >= 0),
  relation_signature TEXT NOT NULL,
  path_weight REAL NOT NULL,
  admissibility_clay TEXT NOT NULL,
  provenance_clay TEXT NOT NULL,
  counterevidence INTEGER NOT NULL DEFAULT 0 CHECK(counterevidence IN (0,1)),
  PRIMARY KEY(plan_id,path_id)
);
CREATE INDEX IF NOT EXISTS idx_graph_access_plan_path_hot
ON graph_semantic_access_plan_paths(plan_id,path_rank,path_weight DESC,target_logical_id);
CREATE INDEX IF NOT EXISTS idx_graph_access_plan_counter
ON graph_semantic_access_plan_paths(plan_id,counterevidence,path_rank);

CREATE TABLE IF NOT EXISTS graph_access_plan_verification_receipts(
  receipt_id TEXT PRIMARY KEY,
  plan_id TEXT NOT NULL REFERENCES graph_semantic_access_plans(plan_id),
  graph_epoch INTEGER NOT NULL,
  topology_hash TEXT NOT NULL,
  checked_path_count INTEGER NOT NULL,
  invalid_path_count INTEGER NOT NULL,
  stale_reference_count INTEGER NOT NULL,
  missing_counterevidence_count INTEGER NOT NULL,
  verification_clay TEXT NOT NULL,
  passed INTEGER NOT NULL CHECK(passed IN (0,1)),
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_graph_access_plan_verify
ON graph_access_plan_verification_receipts(plan_id,created_at DESC);

CREATE VIEW IF NOT EXISTS v_verified_graph_semantic_access_plans AS
SELECT p.*
FROM graph_semantic_access_plans p
JOIN graph_epochs g ON g.graph_epoch=p.graph_epoch
WHERE p.status='VERIFIED' AND g.source_epoch=p.source_epoch AND g.status='CURRENT';

-- Verification law:
-- * Planner output is candidate topology only.
-- * Verification checks every selected path against the exact graph epoch/topology hash.
-- * A plan with stale references or failed admissibility is REJECTED, never published.
-- * Counterevidence-path coverage is measured explicitly; rare negative/refuting paths may not
--   be silently displaced merely because a positive path has higher activation.
-- * Only a verified plan may feed a UnifiedDB U11 STAGING generation; U11 still performs its
--   own epoch/count/hash checks before the atomic generation-head swap.

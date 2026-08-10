-- CLAY U10 RESEARCH CANDIDATE · POSSIBILITY PREPROCESSOR
-- UnifiedDB remains canonical semantic truth. This migration stores recipes, epochs,
-- invalidation and receipts for a derived search-free/near-search-free hot-read layer.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS clay_possibility_recipes(
  recipe_id TEXT PRIMARY KEY,
  recipe_version TEXT NOT NULL,
  semantic_scope TEXT NOT NULL,
  horizon INTEGER NOT NULL,
  selector_clay TEXT NOT NULL,
  dependency_types_clay TEXT NOT NULL,
  admissibility_clay TEXT NOT NULL,
  ranking_clay TEXT NOT NULL,
  hyperposition_policy_clay TEXT NOT NULL,
  rebuild_recipe_clay TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('CANDIDATE','SHADOW','CURRENT','RETRACTED')),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clay_possibility_rule_members(
  recipe_id TEXT NOT NULL REFERENCES clay_possibility_recipes(recipe_id) ON DELETE CASCADE,
  possibility_id TEXT NOT NULL,
  semantic_ref TEXT NOT NULL,
  member_role TEXT NOT NULL,
  required INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY(recipe_id,possibility_id,semantic_ref,member_role)
);
CREATE INDEX IF NOT EXISTS idx_possibility_member_semantic
  ON clay_possibility_rule_members(semantic_ref,recipe_id,possibility_id);

CREATE TABLE IF NOT EXISTS clay_possibility_preprocessor_epochs(
  preprocessor_epoch INTEGER PRIMARY KEY,
  recipe_id TEXT NOT NULL REFERENCES clay_possibility_recipes(recipe_id),
  source_epoch INTEGER NOT NULL,
  parent_preprocessor_epoch INTEGER,
  dependency_hash TEXT NOT NULL,
  rule_hash TEXT NOT NULL,
  compiled_artifact_hash TEXT NOT NULL,
  compile_metadata_clay TEXT NOT NULL,
  published_at TEXT,
  status TEXT NOT NULL CHECK(status IN ('BUILDING','VALIDATED','CURRENT','SUPERSEDED','FAILED')),
  FOREIGN KEY(parent_preprocessor_epoch) REFERENCES clay_possibility_preprocessor_epochs(preprocessor_epoch)
);
CREATE INDEX IF NOT EXISTS idx_possibility_epoch_source
  ON clay_possibility_preprocessor_epochs(source_epoch,preprocessor_epoch DESC);

CREATE TABLE IF NOT EXISTS clay_possibility_delta_receipts(
  delta_receipt_id TEXT PRIMARY KEY,
  source_epoch INTEGER NOT NULL,
  from_preprocessor_epoch INTEGER,
  to_preprocessor_epoch INTEGER,
  delta_class TEXT NOT NULL CHECK(delta_class IN ('ADD_DEPENDENCY','REMOVE_DEPENDENCY','RULE_CHANGE','CAPABILITY_CHANGE','EVIDENCE_CHANGE','FULL_REBUILD')),
  changed_refs_clay TEXT NOT NULL,
  affected_refs_clay TEXT NOT NULL,
  algorithm_id TEXT NOT NULL,
  exactness_check_clay TEXT NOT NULL,
  latency_ms REAL,
  amplification_count INTEGER,
  evidence_refs_clay TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_possibility_delta_epoch
  ON clay_possibility_delta_receipts(source_epoch,created_at DESC);

CREATE TABLE IF NOT EXISTS clay_possibility_query_receipts(
  possibility_query_id TEXT PRIMARY KEY,
  cycle_id TEXT,
  source_epoch INTEGER NOT NULL,
  preprocessor_epoch INTEGER NOT NULL,
  graph_epoch INTEGER,
  cue_refs_clay TEXT NOT NULL,
  candidate_refs_clay TEXT NOT NULL,
  selected_refs_clay TEXT NOT NULL,
  suppressed_refs_clay TEXT NOT NULL DEFAULT '[]',
  conflict_refs_clay TEXT NOT NULL DEFAULT '[]',
  uncertainty_refs_clay TEXT NOT NULL DEFAULT '[]',
  selector_id TEXT NOT NULL,
  result_hash TEXT,
  latency_ms REAL,
  verification_clay TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(preprocessor_epoch) REFERENCES clay_possibility_preprocessor_epochs(preprocessor_epoch)
);
CREATE INDEX IF NOT EXISTS idx_possibility_query_cycle
  ON clay_possibility_query_receipts(cycle_id,created_at DESC);

CREATE TABLE IF NOT EXISTS clay_possibility_invalidation_queue(
  invalidation_id TEXT PRIMARY KEY,
  source_epoch INTEGER NOT NULL,
  changed_ref TEXT NOT NULL,
  invalidation_class TEXT NOT NULL,
  affected_recipe_ids_clay TEXT NOT NULL,
  affected_semantic_refs_clay TEXT NOT NULL,
  requested_at TEXT NOT NULL,
  processed_at TEXT,
  status TEXT NOT NULL CHECK(status IN ('OPEN','PROCESSING','DONE','FAILED','SUPERSEDED'))
);
CREATE INDEX IF NOT EXISTS idx_possibility_invalidation_open
  ON clay_possibility_invalidation_queue(status,source_epoch);

CREATE VIEW IF NOT EXISTS v_clay_current_possibility_preprocessor AS
SELECT p.* FROM clay_possibility_preprocessor_epochs p
JOIN (
  SELECT recipe_id,MAX(preprocessor_epoch) AS pe
  FROM clay_possibility_preprocessor_epochs
  WHERE status='CURRENT'
  GROUP BY recipe_id
) x ON x.recipe_id=p.recipe_id AND x.pe=p.preprocessor_epoch;

-- Runtime laws:
-- 1. canonical truth/provenance/authority remains in UnifiedDB source state;
-- 2. the preprocessor compiles prepared possibilities, never truth or effect authority;
-- 3. hot reads consume a coherent published source/preprocessor/graph epoch tuple;
-- 4. additions may use exact higher-order delta propagation when proven for the bounded horizon;
-- 5. removals/revocations fail closed to targeted recompute unless support-count proof preserves exactness;
-- 6. Hyperposition alternatives/conflicts are preserved as candidates, not destructively collapsed;
-- 7. every candidate may be rebuilt from canonical state + recipe; derived state is disposable.

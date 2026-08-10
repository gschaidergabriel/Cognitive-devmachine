-- CLAYGRAPH V3 RESEARCH CANDIDATE · POSSIBILITY PROJECTION
-- Derived/rebuildable topology for possibilities prepared by UnifiedDB V10 candidate.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS graph_possibility_projections(
  projection_id TEXT PRIMARY KEY,
  source_epoch INTEGER NOT NULL,
  preprocessor_epoch INTEGER NOT NULL,
  graph_epoch INTEGER NOT NULL REFERENCES graph_epochs(graph_epoch),
  context_key TEXT NOT NULL,
  cue_refs_clay TEXT NOT NULL,
  candidate_refs_clay TEXT NOT NULL,
  hyperposition_facets_clay TEXT NOT NULL DEFAULT '[]',
  conflict_refs_clay TEXT NOT NULL DEFAULT '[]',
  uncertainty_refs_clay TEXT NOT NULL DEFAULT '[]',
  projection_recipe_ref TEXT NOT NULL,
  selector_hash TEXT NOT NULL,
  derivation_hash TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('CANDIDATE','CURRENT','SUPPRESSED','STALE','RETRACTED')),
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_graph_possibility_context
  ON graph_possibility_projections(context_key,graph_epoch DESC,status);

CREATE TABLE IF NOT EXISTS graph_possibility_members(
  projection_id TEXT NOT NULL REFERENCES graph_possibility_projections(projection_id) ON DELETE CASCADE,
  possibility_ref TEXT NOT NULL,
  semantic_ref TEXT NOT NULL,
  member_role TEXT NOT NULL,
  rank_score REAL,
  admissibility_clay TEXT NOT NULL,
  evidence_refs_clay TEXT NOT NULL,
  PRIMARY KEY(projection_id,possibility_ref,semantic_ref,member_role)
);
CREATE INDEX IF NOT EXISTS idx_graph_possibility_member
  ON graph_possibility_members(semantic_ref,projection_id);

CREATE TABLE IF NOT EXISTS graph_possibility_selection_receipts(
  selection_receipt_id TEXT PRIMARY KEY,
  cycle_id TEXT,
  projection_id TEXT NOT NULL REFERENCES graph_possibility_projections(projection_id),
  selected_refs_clay TEXT NOT NULL,
  suppressed_refs_clay TEXT NOT NULL,
  ranking_clay TEXT NOT NULL,
  conflict_preservation_clay TEXT NOT NULL,
  authority_check_clay TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_graph_possibility_selection_cycle
  ON graph_possibility_selection_receipts(cycle_id,created_at DESC);

CREATE VIEW IF NOT EXISTS v_current_graph_possibility_projections AS
SELECT p.* FROM graph_possibility_projections p
JOIN (
  SELECT context_key,MAX(graph_epoch) ge
  FROM graph_possibility_projections
  WHERE status='CURRENT'
  GROUP BY context_key
) x ON x.context_key=p.context_key AND x.ge=p.graph_epoch;

-- Semantic boundaries:
-- possibility projection != canonical fact
-- possibility rank != truth
-- possibility reachability != effect authority
-- selected facet != deletion of nonselected Hyperposition facets
-- graph epoch must correspond to one coherent source/preprocessor epoch pair

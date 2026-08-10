-- CLAYGRAPH V3 CANDIDATE · BOUNDED CURRENT ADJACENCY + PATH RECEIPTS
-- Status: RESEARCH_CANDIDATE. ClayGraph remains derived/rebuildable and never truth authority.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS graph_relation_policies(
  relation_type TEXT PRIMARY KEY,
  traversal_class TEXT NOT NULL,
  max_hops INTEGER NOT NULL CHECK(max_hops BETWEEN 0 AND 32),
  min_confidence REAL NOT NULL CHECK(min_confidence BETWEEN 0.0 AND 1.0),
  min_admissibility_rank INTEGER NOT NULL CHECK(min_admissibility_rank BETWEEN 0 AND 9),
  directionality TEXT NOT NULL CHECK(directionality IN ('FORWARD','REVERSE','BIDIRECTIONAL')),
  policy_hash TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS graph_current_adjacency(
  source_logical_id TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  target_logical_id TEXT NOT NULL,
  graph_epoch INTEGER NOT NULL,
  source_epoch INTEGER NOT NULL,
  confidence REAL NOT NULL,
  admissibility_rank INTEGER NOT NULL,
  derivation_hash TEXT NOT NULL,
  rebuilt_at TEXT NOT NULL,
  PRIMARY KEY(source_logical_id,relation_type,target_logical_id)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_graph_current_adjacency_target ON graph_current_adjacency(target_logical_id,relation_type,source_logical_id);
CREATE INDEX IF NOT EXISTS idx_graph_current_adjacency_epoch ON graph_current_adjacency(graph_epoch,source_epoch);

CREATE TABLE IF NOT EXISTS graph_current_projection_receipts(
  projection_receipt_id TEXT PRIMARY KEY,
  graph_epoch INTEGER NOT NULL,
  source_epoch INTEGER NOT NULL,
  policy_hash TEXT NOT NULL,
  input_edges INTEGER NOT NULL,
  output_edges INTEGER NOT NULL,
  rejected_edges INTEGER NOT NULL,
  duration_ms REAL NOT NULL,
  projection_hash TEXT NOT NULL,
  verification_clay TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS graph_path_receipts(
  path_receipt_id TEXT PRIMARY KEY,
  context_query_id TEXT,
  graph_epoch INTEGER NOT NULL,
  source_epoch INTEGER NOT NULL,
  seed_logical_id TEXT NOT NULL,
  relation_type TEXT,
  hop_limit INTEGER NOT NULL,
  visited_count INTEGER NOT NULL,
  selected_logical_ids_clay TEXT NOT NULL,
  path_set_clay TEXT NOT NULL,
  bounded INTEGER NOT NULL CHECK(bounded IN (0,1)),
  policy_hash TEXT NOT NULL,
  duration_ms REAL NOT NULL,
  created_at TEXT NOT NULL
);

CREATE VIEW IF NOT EXISTS v_graph_current_projection_health AS
SELECT graph_epoch,source_epoch,COUNT(*) AS adjacency_edges,MAX(rebuilt_at) AS rebuilt_at
FROM graph_current_adjacency
GROUP BY graph_epoch,source_epoch;

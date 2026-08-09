PRAGMA foreign_keys=ON;

-- ClayGraph V2: derived relevance/topology substrate. Never semantic truth authority.

CREATE TABLE IF NOT EXISTS graph_hyperrelations(
  hyperrelation_version_id TEXT PRIMARY KEY,
  logical_hyperrelation_id TEXT NOT NULL,
  graph_epoch INTEGER NOT NULL REFERENCES graph_epochs(graph_epoch),
  relation_type TEXT NOT NULL,
  relation_class TEXT NOT NULL,
  weight REAL NOT NULL DEFAULT 0.0,
  confidence REAL,
  provenance_clay TEXT NOT NULL,
  admissibility_clay TEXT NOT NULL,
  causal_class TEXT,
  source_epoch INTEGER NOT NULL,
  derivation_hash TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_graph_hyperrel_logical ON graph_hyperrelations(logical_hyperrelation_id,graph_epoch DESC);
CREATE INDEX IF NOT EXISTS idx_graph_hyperrel_type ON graph_hyperrelations(relation_type,graph_epoch DESC);

CREATE TABLE IF NOT EXISTS graph_hyperrelation_members(
  hyperrelation_version_id TEXT NOT NULL REFERENCES graph_hyperrelations(hyperrelation_version_id) ON DELETE CASCADE,
  logical_id TEXT NOT NULL,
  role TEXT NOT NULL,
  ordinal INTEGER,
  member_scope TEXT,
  PRIMARY KEY(hyperrelation_version_id,logical_id,role)
);
CREATE INDEX IF NOT EXISTS idx_graph_hyper_member_logical ON graph_hyperrelation_members(logical_id);

CREATE TABLE IF NOT EXISTS graph_projection_receipts(
  projection_receipt_id TEXT PRIMARY KEY,
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER NOT NULL REFERENCES graph_epochs(graph_epoch),
  derivation_id TEXT NOT NULL,
  derivation_hash TEXT NOT NULL,
  selector_id TEXT,
  collection_semantics_clay TEXT NOT NULL,
  rebuild_recipe_clay TEXT NOT NULL,
  source_refs_clay TEXT NOT NULL,
  output_refs_clay TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_graph_projection_source_epoch ON graph_projection_receipts(source_epoch,graph_epoch DESC);

CREATE TABLE IF NOT EXISTS graph_selection_receipts(
  selection_receipt_id TEXT PRIMARY KEY,
  cycle_id TEXT,
  graph_epoch INTEGER NOT NULL REFERENCES graph_epochs(graph_epoch),
  source_epoch INTEGER NOT NULL,
  query_ref TEXT,
  candidate_refs_clay TEXT NOT NULL,
  selected_refs_clay TEXT NOT NULL,
  suppressed_refs_clay TEXT NOT NULL,
  selector_id TEXT NOT NULL,
  selector_hash TEXT NOT NULL,
  scoring_clay TEXT NOT NULL,
  admissibility_clay TEXT NOT NULL,
  evidence_refs_clay TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_graph_selection_cycle ON graph_selection_receipts(cycle_id,created_at DESC);

CREATE TABLE IF NOT EXISTS graph_receiver_receipts(
  receiver_receipt_id TEXT PRIMARY KEY,
  cycle_id TEXT,
  graph_epoch INTEGER NOT NULL REFERENCES graph_epochs(graph_epoch),
  candidate_ref TEXT NOT NULL,
  receiver_ref TEXT NOT NULL,
  delivered INTEGER NOT NULL DEFAULT 0,
  reconstructed INTEGER NOT NULL DEFAULT 0,
  used INTEGER NOT NULL DEFAULT 0,
  effect_ref TEXT,
  outcome_ref TEXT,
  reentered INTEGER NOT NULL DEFAULT 0,
  evidence_clay TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_graph_receiver_cycle ON graph_receiver_receipts(cycle_id,candidate_ref);

CREATE TABLE IF NOT EXISTS graph_invalidation_queue(
  invalidation_id TEXT PRIMARY KEY,
  source_epoch INTEGER NOT NULL,
  logical_ref TEXT NOT NULL,
  reason_class TEXT NOT NULL,
  dependency_closure_clay TEXT NOT NULL DEFAULT '[]',
  requested_at TEXT NOT NULL,
  processed_graph_epoch INTEGER,
  status TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_graph_invalidation_status ON graph_invalidation_queue(status,source_epoch);

CREATE VIEW IF NOT EXISTS v_latest_graph_hyperrelations AS
SELECT h.* FROM graph_hyperrelations h
JOIN (
  SELECT logical_hyperrelation_id, MAX(graph_epoch) ge
  FROM graph_hyperrelations
  GROUP BY logical_hyperrelation_id
) x ON x.logical_hyperrelation_id=h.logical_hyperrelation_id AND x.ge=h.graph_epoch
WHERE h.status='CURRENT';

-- Hard semantic boundaries are enforced by runtime/type layer:
-- activation/salience changes accessibility only;
-- MODEL_PROPOSED/derived relations do not authorize irreversible effects;
-- UnifiedDB source epoch/provenance remains semantic authority.

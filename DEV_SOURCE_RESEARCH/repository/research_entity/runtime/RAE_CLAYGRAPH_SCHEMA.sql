PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS meta(
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS graph_epochs(
  graph_epoch INTEGER PRIMARY KEY,
  source_epoch INTEGER NOT NULL,
  reason TEXT NOT NULL,
  created_at TEXT NOT NULL,
  status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS graph_nodes(
  node_version_id TEXT PRIMARY KEY,
  logical_id TEXT NOT NULL,
  graph_epoch INTEGER NOT NULL,
  node_kind TEXT NOT NULL,
  label TEXT,
  payload_clay TEXT NOT NULL,
  activation REAL NOT NULL DEFAULT 0.0,
  salience REAL NOT NULL DEFAULT 0.0,
  confidence REAL,
  source_ref TEXT,
  authority_class TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(graph_epoch) REFERENCES graph_epochs(graph_epoch)
);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_logical ON graph_nodes(logical_id,graph_epoch DESC);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_activation ON graph_nodes(graph_epoch,activation DESC);

CREATE TABLE IF NOT EXISTS graph_edges(
  edge_version_id TEXT PRIMARY KEY,
  logical_edge_id TEXT NOT NULL,
  graph_epoch INTEGER NOT NULL,
  source_logical_id TEXT NOT NULL,
  target_logical_id TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  weight REAL NOT NULL DEFAULT 0.0,
  confidence REAL,
  provenance_clay TEXT NOT NULL,
  admissibility_clay TEXT NOT NULL,
  causal_class TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(graph_epoch) REFERENCES graph_epochs(graph_epoch)
);
CREATE INDEX IF NOT EXISTS idx_graph_edges_source ON graph_edges(source_logical_id,graph_epoch DESC);
CREATE INDEX IF NOT EXISTS idx_graph_edges_target ON graph_edges(target_logical_id,graph_epoch DESC);

CREATE TABLE IF NOT EXISTS assemblies(
  assembly_id TEXT PRIMARY KEY,
  cycle_id TEXT,
  graph_epoch INTEGER NOT NULL,
  purpose TEXT NOT NULL,
  selected_nodes_clay TEXT NOT NULL,
  suppressed_nodes_clay TEXT NOT NULL,
  selection_reason_clay TEXT NOT NULL,
  context_hash TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activation_events(
  activation_event_id TEXT PRIMARY KEY,
  cycle_id TEXT,
  graph_epoch INTEGER NOT NULL,
  logical_id TEXT NOT NULL,
  activation_before REAL,
  activation_after REAL,
  cause_class TEXT NOT NULL,
  cause_ref TEXT,
  evidence_clay TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS graph_deltas(
  delta_id TEXT PRIMARY KEY,
  from_graph_epoch INTEGER,
  to_graph_epoch INTEGER NOT NULL,
  added_nodes_clay TEXT NOT NULL,
  retired_nodes_clay TEXT NOT NULL,
  added_edges_clay TEXT NOT NULL,
  retired_edges_clay TEXT NOT NULL,
  changed_activation_clay TEXT NOT NULL,
  source_epoch INTEGER NOT NULL,
  reason TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE VIEW IF NOT EXISTS v_latest_graph_nodes AS
SELECT n.* FROM graph_nodes n
JOIN (
  SELECT logical_id, MAX(graph_epoch) ge
  FROM graph_nodes
  GROUP BY logical_id
) x ON x.logical_id=n.logical_id AND x.ge=n.graph_epoch
WHERE n.status='CURRENT';

CREATE VIEW IF NOT EXISTS v_latest_graph_edges AS
SELECT e.* FROM graph_edges e
JOIN (
  SELECT logical_edge_id, MAX(graph_epoch) ge
  FROM graph_edges
  GROUP BY logical_edge_id
) x ON x.logical_edge_id=e.logical_edge_id AND x.ge=e.graph_epoch
WHERE e.status='CURRENT';

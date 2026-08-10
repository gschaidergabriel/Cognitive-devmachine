PRAGMA foreign_keys=ON;

-- ClayGraph V3 candidate: rebuildable latest-head projections for bounded hot reads.
-- Version logs + graph_epochs remain source-of-truth. Head tables are derived acceleration only.
-- Heads deliberately retain tombstones/non-CURRENT latest versions so out-of-order older arrivals
-- can never resurrect a logically retired edge/node.
-- Promotion gate: v_graph_projection_ambiguous_*_epochs must be empty and fast/legacy views must
-- compare equal on the target dataset before graph_current_projection_receipts.verified_equal=1.

CREATE INDEX IF NOT EXISTS idx_graph_nodes_logical_epoch_v3
  ON graph_nodes(logical_id, graph_epoch DESC);
CREATE INDEX IF NOT EXISTS idx_graph_edges_logical_epoch_v3
  ON graph_edges(logical_edge_id, graph_epoch DESC);

CREATE VIEW IF NOT EXISTS v_graph_projection_ambiguous_node_epochs AS
SELECT logical_id,graph_epoch,COUNT(*) AS version_count
FROM graph_nodes
GROUP BY logical_id,graph_epoch
HAVING COUNT(*)>1;

CREATE VIEW IF NOT EXISTS v_graph_projection_ambiguous_edge_epochs AS
SELECT logical_edge_id,graph_epoch,COUNT(*) AS version_count
FROM graph_edges
GROUP BY logical_edge_id,graph_epoch
HAVING COUNT(*)>1;

CREATE TABLE IF NOT EXISTS graph_head_nodes(
  logical_id TEXT PRIMARY KEY,
  node_version_id TEXT NOT NULL UNIQUE,
  graph_epoch INTEGER NOT NULL,
  source_epoch INTEGER NOT NULL,
  node_kind TEXT NOT NULL,
  label TEXT,
  payload_clay TEXT NOT NULL,
  activation REAL NOT NULL,
  salience REAL NOT NULL,
  confidence REAL,
  source_ref TEXT,
  authority_class TEXT NOT NULL,
  source_status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(graph_epoch) REFERENCES graph_epochs(graph_epoch)
);
CREATE INDEX IF NOT EXISTS idx_graph_head_nodes_current_activation
  ON graph_head_nodes(activation DESC, salience DESC, logical_id)
  WHERE source_status='CURRENT';
CREATE INDEX IF NOT EXISTS idx_graph_head_nodes_current_kind
  ON graph_head_nodes(node_kind, activation DESC, logical_id)
  WHERE source_status='CURRENT';

CREATE TABLE IF NOT EXISTS graph_head_edges(
  logical_edge_id TEXT PRIMARY KEY,
  edge_version_id TEXT NOT NULL UNIQUE,
  graph_epoch INTEGER NOT NULL,
  source_epoch INTEGER NOT NULL,
  source_logical_id TEXT NOT NULL,
  target_logical_id TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  weight REAL NOT NULL,
  confidence REAL,
  provenance_clay TEXT NOT NULL,
  admissibility_clay TEXT NOT NULL,
  causal_class TEXT,
  source_status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(graph_epoch) REFERENCES graph_epochs(graph_epoch)
);
CREATE INDEX IF NOT EXISTS idx_graph_head_edges_current_source
  ON graph_head_edges(source_logical_id, relation_type, target_logical_id, logical_edge_id)
  WHERE source_status='CURRENT';
CREATE INDEX IF NOT EXISTS idx_graph_head_edges_current_target
  ON graph_head_edges(target_logical_id, relation_type, source_logical_id, logical_edge_id)
  WHERE source_status='CURRENT';
CREATE INDEX IF NOT EXISTS idx_graph_head_edges_current_relation
  ON graph_head_edges(relation_type, weight DESC, logical_edge_id)
  WHERE source_status='CURRENT';

CREATE VIEW IF NOT EXISTS v_graph_current_nodes_fast AS
SELECT * FROM graph_head_nodes WHERE source_status='CURRENT';

CREATE VIEW IF NOT EXISTS v_graph_current_edges_fast AS
SELECT * FROM graph_head_edges WHERE source_status='CURRENT';

CREATE TABLE IF NOT EXISTS graph_current_projection_receipts(
  projection_id TEXT PRIMARY KEY,
  graph_epoch INTEGER NOT NULL,
  source_epoch INTEGER NOT NULL,
  projection_kind TEXT NOT NULL,
  derivation_hash TEXT NOT NULL,
  source_row_count INTEGER NOT NULL,
  head_row_count INTEGER NOT NULL,
  current_row_count INTEGER NOT NULL,
  verified_equal INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  FOREIGN KEY(graph_epoch) REFERENCES graph_epochs(graph_epoch)
);

CREATE TRIGGER IF NOT EXISTS trg_graph_nodes_head_upsert
AFTER INSERT ON graph_nodes
BEGIN
  INSERT INTO graph_head_nodes(
    logical_id,node_version_id,graph_epoch,source_epoch,node_kind,label,payload_clay,
    activation,salience,confidence,source_ref,authority_class,source_status,created_at
  )
  SELECT NEW.logical_id,NEW.node_version_id,NEW.graph_epoch,g.source_epoch,NEW.node_kind,NEW.label,
         NEW.payload_clay,NEW.activation,NEW.salience,NEW.confidence,NEW.source_ref,
         NEW.authority_class,NEW.status,NEW.created_at
  FROM graph_epochs g WHERE g.graph_epoch=NEW.graph_epoch
  ON CONFLICT(logical_id) DO UPDATE SET
    node_version_id=excluded.node_version_id,
    graph_epoch=excluded.graph_epoch,
    source_epoch=excluded.source_epoch,
    node_kind=excluded.node_kind,
    label=excluded.label,
    payload_clay=excluded.payload_clay,
    activation=excluded.activation,
    salience=excluded.salience,
    confidence=excluded.confidence,
    source_ref=excluded.source_ref,
    authority_class=excluded.authority_class,
    source_status=excluded.source_status,
    created_at=excluded.created_at
  WHERE excluded.graph_epoch > graph_head_nodes.graph_epoch
     OR (excluded.graph_epoch = graph_head_nodes.graph_epoch
         AND excluded.node_version_id > graph_head_nodes.node_version_id);
END;

CREATE TRIGGER IF NOT EXISTS trg_graph_edges_head_upsert
AFTER INSERT ON graph_edges
BEGIN
  INSERT INTO graph_head_edges(
    logical_edge_id,edge_version_id,graph_epoch,source_epoch,source_logical_id,target_logical_id,
    relation_type,weight,confidence,provenance_clay,admissibility_clay,causal_class,source_status,created_at
  )
  SELECT NEW.logical_edge_id,NEW.edge_version_id,NEW.graph_epoch,g.source_epoch,NEW.source_logical_id,
         NEW.target_logical_id,NEW.relation_type,NEW.weight,NEW.confidence,NEW.provenance_clay,
         NEW.admissibility_clay,NEW.causal_class,NEW.status,NEW.created_at
  FROM graph_epochs g WHERE g.graph_epoch=NEW.graph_epoch
  ON CONFLICT(logical_edge_id) DO UPDATE SET
    edge_version_id=excluded.edge_version_id,
    graph_epoch=excluded.graph_epoch,
    source_epoch=excluded.source_epoch,
    source_logical_id=excluded.source_logical_id,
    target_logical_id=excluded.target_logical_id,
    relation_type=excluded.relation_type,
    weight=excluded.weight,
    confidence=excluded.confidence,
    provenance_clay=excluded.provenance_clay,
    admissibility_clay=excluded.admissibility_clay,
    causal_class=excluded.causal_class,
    source_status=excluded.source_status,
    created_at=excluded.created_at
  WHERE excluded.graph_epoch > graph_head_edges.graph_epoch
     OR (excluded.graph_epoch = graph_head_edges.graph_epoch
         AND excluded.edge_version_id > graph_head_edges.edge_version_id);
END;

-- Rebuild recipe (transactional): clear head tables and repopulate latest version regardless status.
-- Runtime then verifies ambiguity views are empty and v_graph_current_*_fast == legacy
-- v_latest_graph_* before writing a verified projection receipt or admitting this migration.

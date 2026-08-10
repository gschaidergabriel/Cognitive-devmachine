-- CLAY ClayGraph V4 · EXPLICIT SEMANTIC <-> GRAPH BINDINGS
-- Candidate projection needed by hybrid retrieval. It avoids assuming that a
-- UnifiedDB semantic record_id is identical to a ClayGraph logical_id.
-- Bindings are derived/rebuildable, provenance-bound, and never truth authority.

PRAGMA foreign_keys=ON;
BEGIN IMMEDIATE;

CREATE TABLE IF NOT EXISTS graph_semantic_bindings(
  binding_version_id TEXT PRIMARY KEY,
  logical_binding_id TEXT NOT NULL,
  graph_epoch INTEGER NOT NULL REFERENCES graph_epochs(graph_epoch),
  source_epoch INTEGER NOT NULL,
  semantic_record_id TEXT NOT NULL,
  graph_logical_id TEXT NOT NULL,
  binding_class TEXT NOT NULL,
  confidence REAL,
  provenance_clay TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_graph_semantic_binding_logical
  ON graph_semantic_bindings(logical_binding_id,graph_epoch DESC);

CREATE INDEX IF NOT EXISTS idx_graph_semantic_binding_semantic_current
  ON graph_semantic_bindings(semantic_record_id,graph_epoch DESC,graph_logical_id)
  WHERE status='CURRENT';

CREATE INDEX IF NOT EXISTS idx_graph_semantic_binding_graph_current
  ON graph_semantic_bindings(graph_logical_id,graph_epoch DESC,semantic_record_id)
  WHERE status='CURRENT';

CREATE VIEW IF NOT EXISTS v_latest_graph_semantic_bindings AS
SELECT b.*
FROM graph_semantic_bindings b
WHERE b.status='CURRENT'
  AND NOT EXISTS (
    SELECT 1
    FROM graph_semantic_bindings newer
    WHERE newer.logical_binding_id=b.logical_binding_id
      AND newer.graph_epoch>b.graph_epoch
  );

COMMIT;

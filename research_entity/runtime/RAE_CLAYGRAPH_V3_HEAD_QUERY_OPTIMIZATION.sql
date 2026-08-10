-- CLAY ClayGraph V3 · HEAD QUERY OPTIMIZATION
-- Semantic goal: preserve the exact v_latest_graph_edges result set while making
-- neighborhood reads scale with the queried neighborhood instead of total history.
-- ClayGraph remains derived/rebuildable and never becomes truth/authority.

PRAGMA foreign_keys=ON;
BEGIN IMMEDIATE;

-- Missing in the base schema although the compatibility view is keyed by logical_edge_id.
CREATE INDEX IF NOT EXISTS idx_graph_edges_logical
  ON graph_edges(logical_edge_id,graph_epoch DESC);

-- Compact hot-state indexes. They are performance aids only; correctness is still
-- guarded by the NOT EXISTS newer-version test below.
CREATE INDEX IF NOT EXISTS idx_graph_edges_current_source
  ON graph_edges(source_logical_id,relation_type,weight DESC,target_logical_id)
  WHERE status='CURRENT';

CREATE INDEX IF NOT EXISTS idx_graph_edges_current_target
  ON graph_edges(target_logical_id,relation_type,weight DESC,source_logical_id)
  WHERE status='CURRENT';

DROP VIEW IF EXISTS v_latest_graph_edges;

-- Equivalent to: select MAX(graph_epoch) per logical_edge_id, then keep CURRENT.
-- Difference is physical execution: source/target predicates can be applied first,
-- followed by an indexed anti-probe for a newer version. No eager whole-graph GROUP BY.
CREATE VIEW v_latest_graph_edges AS
SELECT e.*
FROM graph_edges e
WHERE e.status='CURRENT'
  AND NOT EXISTS (
    SELECT 1
    FROM graph_edges newer
    WHERE newer.logical_edge_id=e.logical_edge_id
      AND newer.graph_epoch>e.graph_epoch
  );

-- Diagnostic only. Non-empty means writer/status maintenance left a stale CURRENT
-- row behind. The compatibility view remains correct even then, but publication/
-- recovery logic should repair or rebuild the derived graph.
CREATE VIEW IF NOT EXISTS v_graph_edge_stale_current_anomalies AS
SELECT c.logical_edge_id,
       c.edge_version_id AS stale_current_edge_version_id,
       c.graph_epoch AS stale_current_graph_epoch,
       MAX(n.graph_epoch) AS newer_graph_epoch
FROM graph_edges c
JOIN graph_edges n
  ON n.logical_edge_id=c.logical_edge_id
 AND n.graph_epoch>c.graph_epoch
WHERE c.status='CURRENT'
GROUP BY c.logical_edge_id,c.edge_version_id,c.graph_epoch;

COMMIT;

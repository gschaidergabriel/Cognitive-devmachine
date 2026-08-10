PRAGMA foreign_keys=ON;

-- ClayGraph V3 CURRENT hot-path candidate.
-- STATUS: CANDIDATE / SHADOW_ONLY until differential validation passes.
-- PURPOSE: keep append-only/versioned graph history while making CURRENT projection
--          index-addressable without GROUP BY + MAX(graph_epoch) on every hot read.
-- AUTHORITY: derived projection only; UnifiedDB source epoch/provenance remains semantic authority.
-- ROLLBACK: DROP the five cg_v3_* indexes and the two v_candidate_* views.
--
-- Promotion gate:
--   1. Existing graph history must have at most one status='CURRENT' row per logical id.
--   2. Candidate views must be set-equivalent to v_latest_graph_nodes/edges.
--   3. Rebuild/replay/lesion/recovery tests must preserve source_epoch/provenance semantics.
--   4. Measure read latency, write amplification, DB size and rebuild cost on Ubuntu.
--
-- NOTE: The UNIQUE partial indexes intentionally fail if historical CURRENT duplication exists.
--       Run this migration transactionally and ROLLBACK on any error.

BEGIN IMMEDIATE;

CREATE UNIQUE INDEX IF NOT EXISTS cg_v3_one_current_node
ON graph_nodes(logical_id)
WHERE status='CURRENT';

CREATE UNIQUE INDEX IF NOT EXISTS cg_v3_one_current_edge
ON graph_edges(logical_edge_id)
WHERE status='CURRENT';

CREATE INDEX IF NOT EXISTS cg_v3_current_node_activation
ON graph_nodes(activation DESC, logical_id)
WHERE status='CURRENT';

CREATE INDEX IF NOT EXISTS cg_v3_current_edge_source
ON graph_edges(source_logical_id, relation_type, weight DESC, target_logical_id)
WHERE status='CURRENT';

CREATE INDEX IF NOT EXISTS cg_v3_current_edge_target
ON graph_edges(target_logical_id, relation_type, weight DESC, source_logical_id)
WHERE status='CURRENT';

CREATE VIEW IF NOT EXISTS v_candidate_current_graph_nodes_v3 AS
SELECT * FROM graph_nodes WHERE status='CURRENT';

CREATE VIEW IF NOT EXISTS v_candidate_current_graph_edges_v3 AS
SELECT * FROM graph_edges WHERE status='CURRENT';

COMMIT;

-- SHADOW DIFFERENTIAL: both counts MUST be zero before replacing legacy views.
-- Node rows present in legacy current projection but absent from candidate:
-- SELECT COUNT(*) FROM (
--   SELECT node_version_id FROM v_latest_graph_nodes
--   EXCEPT
--   SELECT node_version_id FROM v_candidate_current_graph_nodes_v3
-- );
-- Node rows present in candidate but absent from legacy current projection:
-- SELECT COUNT(*) FROM (
--   SELECT node_version_id FROM v_candidate_current_graph_nodes_v3
--   EXCEPT
--   SELECT node_version_id FROM v_latest_graph_nodes
-- );
-- Repeat the same EXCEPT pair for edge_version_id over v_latest_graph_edges and
-- v_candidate_current_graph_edges_v3.
--
-- Recommended query-plan checks:
-- EXPLAIN QUERY PLAN SELECT * FROM v_candidate_current_graph_nodes_v3
--   WHERE logical_id=?;
-- EXPLAIN QUERY PLAN SELECT target_logical_id,relation_type,weight
--   FROM v_candidate_current_graph_edges_v3
--   WHERE source_logical_id=? ORDER BY weight DESC LIMIT 32;
-- EXPLAIN QUERY PLAN SELECT logical_id,activation
--   FROM v_candidate_current_graph_nodes_v3 ORDER BY activation DESC LIMIT 32;

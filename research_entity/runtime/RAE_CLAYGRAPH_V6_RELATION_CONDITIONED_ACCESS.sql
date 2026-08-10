-- ClayGraph V6 candidate: relation-conditioned bounded access over verified V3 heads.
--
-- Truth/authority invariants:
--   * graph_edges + graph_epochs remain version-log source of truth.
--   * graph_head_edges remains derived/rebuildable acceleration only.
--   * relation-conditioned selection is retrieval admission, never truth/effect authority.
--   * use only after V3 ambiguity/equality gates have admitted the head projection.
--
-- Accuracy motivation:
-- A single global weight Top-K can discard a semantically requested relation class at
-- high-degree nodes. V6 preserves the same total edge budget but lets a typed query relation
-- reserve a bounded prefix before filling the remaining slots from global strongest edges.
-- If no trustworthy typed relation exists, use the ordinary global bounded path.

PRAGMA foreign_keys=ON;

CREATE INDEX IF NOT EXISTS idx_graph_head_edges_current_source_weight_v6
  ON graph_head_edges(
    source_logical_id,
    weight DESC,
    target_logical_id,
    logical_edge_id
  )
  WHERE source_status='CURRENT';

CREATE INDEX IF NOT EXISTS idx_graph_head_edges_current_source_relation_weight_v6
  ON graph_head_edges(
    source_logical_id,
    relation_type,
    weight DESC,
    target_logical_id,
    logical_edge_id
  )
  WHERE source_status='CURRENT';

-- Parametric query recipe; runtime binds:
--   ?1 source_logical_id
--   ?2 typed relation_type
--   ?3 relation_reserve (0..total_budget)
--   ?4 total_budget
--
-- The requested relation consumes at most relation_reserve slots. Fallback then fills the
-- remaining budget with globally strongest CURRENT neighbors, excluding already admitted
-- logical edges. No full graph closure and no hidden authority transition occurs.
--
-- WITH requested AS (
--   SELECT logical_edge_id,edge_version_id,graph_epoch,source_epoch,
--          source_logical_id,target_logical_id,relation_type,weight,confidence,
--          provenance_clay,admissibility_clay,causal_class,source_status,created_at
--   FROM graph_head_edges INDEXED BY idx_graph_head_edges_current_source_relation_weight_v6
--   WHERE source_status='CURRENT'
--     AND source_logical_id=?1
--     AND relation_type=?2
--   ORDER BY weight DESC,target_logical_id ASC,logical_edge_id ASC
--   LIMIT ?3
-- ), fallback AS (
--   SELECT e.logical_edge_id,e.edge_version_id,e.graph_epoch,e.source_epoch,
--          e.source_logical_id,e.target_logical_id,e.relation_type,e.weight,e.confidence,
--          e.provenance_clay,e.admissibility_clay,e.causal_class,e.source_status,e.created_at
--   FROM graph_head_edges e INDEXED BY idx_graph_head_edges_current_source_weight_v6
--   WHERE e.source_status='CURRENT'
--     AND e.source_logical_id=?1
--     AND NOT EXISTS (
--       SELECT 1 FROM requested r WHERE r.logical_edge_id=e.logical_edge_id
--     )
--   ORDER BY e.weight DESC,e.target_logical_id ASC,e.logical_edge_id ASC
--   LIMIT max(0,?4-?3)
-- )
-- SELECT * FROM requested
-- UNION ALL
-- SELECT * FROM fallback
-- LIMIT ?4;

-- CLAY / UnifiedDB U16 candidate · LIVE FUSION RECEIPT PERSISTENCE
-- Status: RESEARCH_CANDIDATE_NOT_PROMOTED
--
-- Purpose: make stronger live networking observable and restart-safe without letting
-- transport delivery, graph relevance, or receipt presence mint truth/effect authority.
-- Semantic parent: CLAY_LIVE_FUSION_MESH_V2_CANDIDATE.clay v0.2-candidate.
-- Durable authority remains canonical Git/UnifiedDB state; this migration is additive
-- and rollbackable until real repo-worker replay + recovery evidence passes.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS clay_live_fusion_events(
  source TEXT NOT NULL,
  event_id TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  semantic_epoch INTEGER NOT NULL CHECK(semantic_epoch >= 0),
  work_spec_rev INTEGER CHECK(work_spec_rev IS NULL OR work_spec_rev >= 0),
  kind TEXT NOT NULL CHECK(kind IN ('NEW','REFINES','CONFIRMS','CONTRADICTS','SUPERSEDES','NO_MATERIAL_CHANGE')),
  payload_ref TEXT,
  evidence_class TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(source,event_id)
);

-- Exact replay may use INSERT OR IGNORE; same source+event id with changed content
-- is an identity conflict and must fail closed before the PK conflict can hide it.
CREATE TRIGGER IF NOT EXISTS trg_live_fusion_event_identity_conflict
BEFORE INSERT ON clay_live_fusion_events
WHEN EXISTS (
  SELECT 1 FROM clay_live_fusion_events e
  WHERE e.source=NEW.source AND e.event_id=NEW.event_id
    AND e.content_hash<>NEW.content_hash
)
BEGIN
  SELECT RAISE(ABORT,'LIVE_FUSION_IDENTITY_CONFLICT');
END;

CREATE TABLE IF NOT EXISTS clay_live_fusion_branch_projections(
  branch TEXT PRIMARY KEY,
  projection_epoch INTEGER NOT NULL CHECK(projection_epoch >= 0),
  projection_hash TEXT NOT NULL,
  completeness_state TEXT NOT NULL CHECK(completeness_state IN ('CURRENT','DEGRADED','UNKNOWN','STALE')),
  dependency_count INTEGER NOT NULL DEFAULT 0 CHECK(dependency_count >= 0),
  observed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clay_live_fusion_route_plans(
  route_plan_id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  event_id TEXT NOT NULL,
  mode TEXT NOT NULL CHECK(mode IN ('TARGETED_DELTA','DENSE_FANOUT','DIGEST_ONLY')),
  predicted_affected_fraction REAL,
  predicted_targeted_cost REAL,
  predicted_dense_cost REAL,
  predicted_repair_cost REAL,
  confidence REAL CHECK(confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),
  route_epoch INTEGER NOT NULL CHECK(route_epoch >= 0),
  reason_clay TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  FOREIGN KEY(source,event_id) REFERENCES clay_live_fusion_events(source,event_id)
);

CREATE TABLE IF NOT EXISTS clay_live_fusion_route_decisions(
  route_plan_id TEXT NOT NULL,
  target_branch TEXT NOT NULL,
  reason TEXT NOT NULL CHECK(reason IN ('DIRECT_SEMANTIC','DIRECT_WORK','CAUSAL_DEPENDENT','CONFLICT_INTERRUPT','ANTI_ENTROPY_REPAIR','DENSE_FANOUT','INDEX_ONLY')),
  payload_mode TEXT NOT NULL CHECK(payload_mode IN ('FULL_REF','DIGEST_ONLY','NONE')),
  urgency TEXT NOT NULL CHECK(urgency IN ('NEXT_SAFE_POINT','NEXT_CHECKPOINT','INDEX_ONLY')),
  projection_epoch INTEGER,
  projection_hash TEXT,
  created_at TEXT NOT NULL,
  PRIMARY KEY(route_plan_id,target_branch),
  FOREIGN KEY(route_plan_id) REFERENCES clay_live_fusion_route_plans(route_plan_id)
);

-- Targeted routing is allowed only against the exact CURRENT dependency projection
-- observed when the decision was made. Dense fanout remains the fail-broad fallback
-- when locality metadata is incomplete; it still cannot expand effect authority.
CREATE TRIGGER IF NOT EXISTS trg_live_fusion_targeted_projection_guard
BEFORE INSERT ON clay_live_fusion_route_decisions
WHEN (SELECT mode FROM clay_live_fusion_route_plans WHERE route_plan_id=NEW.route_plan_id)='TARGETED_DELTA'
  AND NOT EXISTS (
    SELECT 1 FROM clay_live_fusion_branch_projections p
    WHERE p.branch=NEW.target_branch
      AND p.completeness_state='CURRENT'
      AND p.projection_epoch=NEW.projection_epoch
      AND p.projection_hash=NEW.projection_hash
  )
BEGIN
  SELECT RAISE(ABORT,'LIVE_FUSION_STALE_OR_INCOMPLETE_PROJECTION');
END;

-- Seven durable causal-observability stages. These stages are intentionally stronger
-- than broker ACKs and weaker than epistemic promotion. Stage 7 is provenance-bound
-- re-entry receipt, not evidence that the re-entered content is true.
CREATE TABLE IF NOT EXISTS clay_live_fusion_receipt_events(
  source TEXT NOT NULL,
  event_id TEXT NOT NULL,
  target_branch TEXT NOT NULL,
  stage INTEGER NOT NULL CHECK(stage BETWEEN 1 AND 7),
  route_plan_id TEXT NOT NULL,
  receipt_hash TEXT NOT NULL,
  evidence_ref TEXT,
  truth_class TEXT NOT NULL DEFAULT 'RESEARCH_EVIDENCE',
  created_at TEXT NOT NULL,
  PRIMARY KEY(source,event_id,target_branch,stage),
  FOREIGN KEY(source,event_id) REFERENCES clay_live_fusion_events(source,event_id),
  FOREIGN KEY(route_plan_id,target_branch) REFERENCES clay_live_fusion_route_decisions(route_plan_id,target_branch)
);

CREATE TRIGGER IF NOT EXISTS trg_live_fusion_receipt_identity_conflict
BEFORE INSERT ON clay_live_fusion_receipt_events
WHEN EXISTS (
  SELECT 1 FROM clay_live_fusion_receipt_events r
  WHERE r.source=NEW.source AND r.event_id=NEW.event_id
    AND r.target_branch=NEW.target_branch AND r.stage=NEW.stage
    AND r.receipt_hash<>NEW.receipt_hash
)
BEGIN
  SELECT RAISE(ABORT,'LIVE_FUSION_RECEIPT_IDENTITY_CONFLICT');
END;

-- Exact duplicate receipts can be replayed with INSERT OR IGNORE. New receipts may
-- advance exactly one stage and may never skip/regress the causal-observability chain.
CREATE TRIGGER IF NOT EXISTS trg_live_fusion_receipt_monotonic
BEFORE INSERT ON clay_live_fusion_receipt_events
WHEN NOT EXISTS (
  SELECT 1 FROM clay_live_fusion_receipt_events r
  WHERE r.source=NEW.source AND r.event_id=NEW.event_id
    AND r.target_branch=NEW.target_branch AND r.stage=NEW.stage
    AND r.receipt_hash=NEW.receipt_hash
)
AND (
  (NEW.stage=1 AND EXISTS (
      SELECT 1 FROM clay_live_fusion_receipt_events r
      WHERE r.source=NEW.source AND r.event_id=NEW.event_id
        AND r.target_branch=NEW.target_branch
  ))
  OR
  (NEW.stage>1 AND COALESCE((
      SELECT MAX(r.stage) FROM clay_live_fusion_receipt_events r
      WHERE r.source=NEW.source AND r.event_id=NEW.event_id
        AND r.target_branch=NEW.target_branch
    ),0)<>NEW.stage-1)
)
BEGIN
  SELECT RAISE(ABORT,'LIVE_FUSION_RECEIPT_STAGE_GAP_OR_REGRESSION');
END;

CREATE TABLE IF NOT EXISTS clay_live_fusion_anti_entropy_checkpoints(
  branch TEXT NOT NULL,
  checkpoint_epoch INTEGER NOT NULL CHECK(checkpoint_epoch >= 0),
  local_projection_hash TEXT NOT NULL,
  source_projection_hash TEXT NOT NULL,
  digest_hash TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('MATCH','GAP','REPAIRING','REPAIRED','DEGRADED')),
  missing_refs_clay TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  PRIMARY KEY(branch,checkpoint_epoch)
);

CREATE VIEW IF NOT EXISTS v_clay_live_fusion_current_receipt_stage AS
SELECT r.source,r.event_id,r.target_branch,MAX(r.stage) AS stage,
       CASE MAX(r.stage)
         WHEN 1 THEN 'DELIVERED'
         WHEN 2 THEN 'RECONSTRUCTED'
         WHEN 3 THEN 'PLAN_REVALIDATED'
         WHEN 4 THEN 'USED'
         WHEN 5 THEN 'LOCAL_EFFECT'
         WHEN 6 THEN 'VERIFIED_OUTCOME'
         WHEN 7 THEN 'REENTRY'
       END AS stage_name
FROM clay_live_fusion_receipt_events r
GROUP BY r.source,r.event_id,r.target_branch;

CREATE VIEW IF NOT EXISTS v_clay_live_fusion_latest_anti_entropy AS
WITH ranked AS (
  SELECT a.*,ROW_NUMBER() OVER(PARTITION BY branch ORDER BY checkpoint_epoch DESC,created_at DESC) AS rn
  FROM clay_live_fusion_anti_entropy_checkpoints a
)
SELECT branch,checkpoint_epoch,local_projection_hash,source_projection_hash,digest_hash,state,missing_refs_clay,created_at
FROM ranked WHERE rn=1;

-- U16 candidate invariants:
-- 1. source+event identity conflict fails closed; exact replay can be idempotent.
-- 2. TARGETED_DELTA requires exact CURRENT branch projection epoch/hash.
-- 3. DENSE_FANOUT remains available when dependency locality is uncertain/dense.
-- 4. delivery -> reconstruction -> plan revalidation -> use -> local effect -> verified
--    outcome -> re-entry is persistent and monotone; no stage implies truth/causal credit.
-- 5. anti-entropy gaps/degraded state are first-class durable evidence, not hidden misses.
-- 6. broker/network acceleration is outside semantic authority and can be killed/replayed.
-- 7. promotion requires real repo-worker replay, fault injection, recovery and resource data.

PRAGMA foreign_keys=ON;

-- UnifiedDB V10 candidate: Omnisource live-fusion intake and mandatory research re-entry.
-- Clay/ClayCode records remain semantic authority; this SQL is persistence/projection runtime only.
-- V10 remains TESTING and is not part of the promoted UnifiedDB stack.

CREATE TABLE IF NOT EXISTS clay_omnisource_observations(
  observation_id TEXT PRIMARY KEY,
  source_class TEXT NOT NULL CHECK(source_class IN (
    'REPO_STATE','WORK_EVENT','WORKER_RESULT','RUNTIME_RECEIPT','BENCHMARK_ROW',
    'TEST_FAILURE','NEGATIVE_RESULT','USER_DIRECTIVE','USER_OBSERVATION','UPLOADED_SOURCE',
    'EXTERNAL_PRIMARY','EXTERNAL_OFFICIAL','EXTERNAL_TECHNICAL','PROVIDER_CAPABILITY',
    'FRANK_TELEMETRY','UNIFIEDDB_DELTA','CLAYGRAPH_DELTA','EXPERIMENT_OUTPUT',
    'OTHER_PROVENANCE_BOUND'
  )),
  source_ref TEXT NOT NULL,
  source_actor TEXT,
  source_time TEXT,
  observed_at TEXT NOT NULL,
  semantic_epoch INTEGER,
  epoch_state TEXT NOT NULL DEFAULT 'CURRENT'
    CHECK(epoch_state IN ('CURRENT','STALE','UNKNOWN','QUARANTINED')),
  semantic_identity TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  raw_payload_ref TEXT NOT NULL,
  provenance_hash TEXT NOT NULL,
  verification_state TEXT NOT NULL DEFAULT 'VERIFIED'
    CHECK(verification_state IN ('VERIFIED','UNVERIFIED','QUARANTINED')),
  promotion_eligible INTEGER NOT NULL DEFAULT 1 CHECK(promotion_eligible IN (0,1)),
  work_id TEXT,
  work_spec_rev INTEGER,
  work_revision_state TEXT NOT NULL DEFAULT 'NOT_APPLICABLE'
    CHECK(work_revision_state IN ('CURRENT','STALE','UNKNOWN','NOT_APPLICABLE')),
  current_work_credit_eligible INTEGER NOT NULL DEFAULT 0 CHECK(current_work_credit_eligible IN (0,1)),
  bound_repo_head TEXT,
  bound_component_hashes_clay TEXT NOT NULL DEFAULT '[]',
  execution_started_at TEXT,
  freshness REAL,
  confidence REAL,
  created_by TEXT NOT NULL,
  CHECK (
    (work_revision_state='NOT_APPLICABLE' AND work_id IS NULL AND work_spec_rev IS NULL AND current_work_credit_eligible=0)
    OR
    (work_revision_state<>'NOT_APPLICABLE' AND work_id IS NOT NULL)
  )
);
CREATE INDEX IF NOT EXISTS idx_omni_identity_epoch
  ON clay_omnisource_observations(semantic_identity,semantic_epoch DESC,observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_omni_content
  ON clay_omnisource_observations(content_hash);
CREATE INDEX IF NOT EXISTS idx_omni_source
  ON clay_omnisource_observations(source_class,observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_omni_work_revision
  ON clay_omnisource_observations(work_id,work_spec_rev,observed_at DESC);

CREATE TRIGGER IF NOT EXISTS trg_omni_no_stale_promotion_insert
BEFORE INSERT ON clay_omnisource_observations
WHEN (NEW.epoch_state IN ('STALE','UNKNOWN','QUARANTINED')
      OR NEW.verification_state IN ('UNVERIFIED','QUARANTINED'))
     AND NEW.promotion_eligible <> 0
BEGIN
  SELECT RAISE(ABORT,'stale/unverified observation cannot be promotion eligible');
END;

CREATE TRIGGER IF NOT EXISTS trg_omni_no_stale_promotion_update
BEFORE UPDATE OF epoch_state,verification_state,promotion_eligible ON clay_omnisource_observations
WHEN (NEW.epoch_state IN ('STALE','UNKNOWN','QUARANTINED')
      OR NEW.verification_state IN ('UNVERIFIED','QUARANTINED'))
     AND NEW.promotion_eligible <> 0
BEGIN
  SELECT RAISE(ABORT,'stale/unverified observation cannot be promotion eligible');
END;

-- A technically successful execution can still be stale with respect to the current work contract.
-- Preserve it as evidence, but block current-work completion/promotion credit.
CREATE TRIGGER IF NOT EXISTS trg_omni_no_stale_work_credit_insert
BEFORE INSERT ON clay_omnisource_observations
WHEN NEW.work_revision_state IN ('STALE','UNKNOWN')
     AND NEW.current_work_credit_eligible <> 0
BEGIN
  SELECT RAISE(ABORT,'stale/unknown work revision cannot receive current-work credit');
END;

CREATE TRIGGER IF NOT EXISTS trg_omni_no_stale_work_credit_update
BEFORE UPDATE OF work_revision_state,current_work_credit_eligible ON clay_omnisource_observations
WHEN NEW.work_revision_state IN ('STALE','UNKNOWN')
     AND NEW.current_work_credit_eligible <> 0
BEGIN
  SELECT RAISE(ABORT,'stale/unknown work revision cannot receive current-work credit');
END;

CREATE TRIGGER IF NOT EXISTS trg_omni_current_work_credit_requires_binding_insert
BEFORE INSERT ON clay_omnisource_observations
WHEN NEW.current_work_credit_eligible=1
 AND (
   NEW.work_revision_state<>'CURRENT'
   OR NEW.work_id IS NULL
   OR NEW.work_spec_rev IS NULL
   OR NEW.bound_repo_head IS NULL
   OR NEW.execution_started_at IS NULL
   OR NEW.bound_component_hashes_clay='[]'
 )
BEGIN
  SELECT RAISE(ABORT,'current-work credit requires current revision, repo head, start time and component hashes');
END;

CREATE TRIGGER IF NOT EXISTS trg_omni_current_work_credit_requires_binding_update
BEFORE UPDATE OF current_work_credit_eligible,work_revision_state,work_id,work_spec_rev,bound_repo_head,bound_component_hashes_clay,execution_started_at
ON clay_omnisource_observations
WHEN NEW.current_work_credit_eligible=1
 AND (
   NEW.work_revision_state<>'CURRENT'
   OR NEW.work_id IS NULL
   OR NEW.work_spec_rev IS NULL
   OR NEW.bound_repo_head IS NULL
   OR NEW.execution_started_at IS NULL
   OR NEW.bound_component_hashes_clay='[]'
 )
BEGIN
  SELECT RAISE(ABORT,'current-work credit requires current revision, repo head, start time and component hashes');
END;

CREATE TABLE IF NOT EXISTS clay_fusion_assessments(
  assessment_id TEXT PRIMARY KEY,
  observation_id TEXT NOT NULL REFERENCES clay_omnisource_observations(observation_id) ON DELETE CASCADE,
  compared_against_epoch INTEGER,
  novelty_class TEXT NOT NULL CHECK(novelty_class IN (
    'NEW','REFINES','CONFIRMS','CONTRADICTS','SUPERSEDES','NO_MATERIAL_CHANGE','DUPLICATE'
  )),
  materiality REAL NOT NULL CHECK(materiality>=0.0 AND materiality<=1.0),
  uncertainty REAL NOT NULL CHECK(uncertainty>=0.0 AND uncertainty<=1.0),
  affected_claims_clay TEXT NOT NULL DEFAULT '[]',
  affected_hypotheses_clay TEXT NOT NULL DEFAULT '[]',
  affected_work_clay TEXT NOT NULL DEFAULT '[]',
  affected_components_clay TEXT NOT NULL DEFAULT '[]',
  evidence_for_clay TEXT NOT NULL DEFAULT '[]',
  evidence_against_clay TEXT NOT NULL DEFAULT '[]',
  strongest_counterhypothesis_ref TEXT,
  semantic_delta_ref TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(observation_id)
);
CREATE INDEX IF NOT EXISTS idx_fusion_novelty
  ON clay_fusion_assessments(novelty_class,created_at DESC);

CREATE TABLE IF NOT EXISTS clay_research_reentry_receipts(
  receipt_id TEXT PRIMARY KEY,
  observation_id TEXT NOT NULL REFERENCES clay_omnisource_observations(observation_id),
  assessment_id TEXT NOT NULL REFERENCES clay_fusion_assessments(assessment_id),
  fused_epoch INTEGER NOT NULL,
  work_id TEXT,
  work_spec_rev INTEGER,
  work_revision_state TEXT NOT NULL DEFAULT 'NOT_APPLICABLE'
    CHECK(work_revision_state IN ('CURRENT','STALE','UNKNOWN','NOT_APPLICABLE')),
  current_work_credit_eligible INTEGER NOT NULL DEFAULT 0 CHECK(current_work_credit_eligible IN (0,1)),
  bound_repo_head TEXT,
  bound_component_hashes_clay TEXT NOT NULL DEFAULT '[]',
  evidence_updates_clay TEXT NOT NULL DEFAULT '[]',
  claim_updates_clay TEXT NOT NULL DEFAULT '[]',
  hypothesis_updates_clay TEXT NOT NULL DEFAULT '[]',
  counterhypothesis_updates_clay TEXT NOT NULL DEFAULT '[]',
  experiment_updates_clay TEXT NOT NULL DEFAULT '[]',
  work_updates_clay TEXT NOT NULL DEFAULT '[]',
  architecture_delta_candidates_clay TEXT NOT NULL DEFAULT '[]',
  test_obligations_clay TEXT NOT NULL DEFAULT '[]',
  negative_results_clay TEXT NOT NULL DEFAULT '[]',
  branch_feedback_targets_clay TEXT NOT NULL DEFAULT '[]',
  no_change_reason_clay TEXT,
  next_falsifier_clay TEXT,
  rollback_or_recovery_impact_clay TEXT,
  closure_state TEXT NOT NULL CHECK(closure_state IN ('OPEN','PARTIAL','CLOSED','FAILED')),
  completed_at TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(assessment_id),
  CHECK (
    current_work_credit_eligible=0
    OR (
      work_revision_state='CURRENT'
      AND work_id IS NOT NULL
      AND work_spec_rev IS NOT NULL
      AND bound_repo_head IS NOT NULL
      AND bound_component_hashes_clay<>'[]'
    )
  )
);
CREATE INDEX IF NOT EXISTS idx_reentry_state
  ON clay_research_reentry_receipts(closure_state,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reentry_work_revision
  ON clay_research_reentry_receipts(work_id,work_spec_rev,created_at DESC);

CREATE TABLE IF NOT EXISTS clay_reentry_branch_receipts(
  receipt_id TEXT NOT NULL REFERENCES clay_research_reentry_receipts(receipt_id) ON DELETE CASCADE,
  branch_ref TEXT NOT NULL,
  route_reason TEXT NOT NULL,
  delivered INTEGER NOT NULL DEFAULT 0 CHECK(delivered IN (0,1)),
  reconstructed INTEGER NOT NULL DEFAULT 0 CHECK(reconstructed IN (0,1)),
  plan_revalidated INTEGER NOT NULL DEFAULT 0 CHECK(plan_revalidated IN (0,1)),
  used INTEGER NOT NULL DEFAULT 0 CHECK(used IN (0,1)),
  local_effect INTEGER NOT NULL DEFAULT 0 CHECK(local_effect IN (0,1)),
  interrupted_before_effect INTEGER NOT NULL DEFAULT 0 CHECK(interrupted_before_effect IN (0,1)),
  ack_epoch INTEGER,
  dependency_projection_hash TEXT,
  observed_at TEXT NOT NULL,
  PRIMARY KEY(receipt_id,branch_ref)
);
CREATE INDEX IF NOT EXISTS idx_reentry_branch_ack
  ON clay_reentry_branch_receipts(branch_ref,ack_epoch DESC);

CREATE TABLE IF NOT EXISTS clay_reentry_checkpoints(
  checkpoint_id TEXT PRIMARY KEY,
  semantic_epoch INTEGER NOT NULL,
  source_projection_hash TEXT NOT NULL,
  dependency_projection_hash TEXT NOT NULL,
  last_observation_id TEXT,
  last_reentry_receipt_id TEXT,
  health_state TEXT NOT NULL CHECK(health_state IN ('HEALTHY','DEGRADED','FAILED','RECOVERING','QUARANTINED','UNKNOWN')),
  created_at TEXT NOT NULL
);

CREATE VIEW IF NOT EXISTS v_clay_omnisource_pending_assessment AS
SELECT o.*
FROM clay_omnisource_observations o
LEFT JOIN clay_fusion_assessments a USING(observation_id)
WHERE a.observation_id IS NULL;

CREATE VIEW IF NOT EXISTS v_clay_material_reentry_pending AS
SELECT a.*,o.source_class,o.semantic_identity,o.semantic_epoch,
       o.work_id,o.work_spec_rev,o.work_revision_state,o.current_work_credit_eligible
FROM clay_fusion_assessments a
JOIN clay_omnisource_observations o USING(observation_id)
LEFT JOIN clay_research_reentry_receipts r USING(assessment_id)
WHERE a.materiality>=0.5
  AND a.novelty_class NOT IN ('NO_MATERIAL_CHANGE','DUPLICATE')
  AND o.promotion_eligible=1
  AND (r.receipt_id IS NULL OR r.closure_state<>'CLOSED');

CREATE VIEW IF NOT EXISTS v_clay_duplicate_content_provenance AS
SELECT content_hash,COUNT(*) AS observation_count,
       COUNT(DISTINCT provenance_hash) AS distinct_provenance_count
FROM clay_omnisource_observations
GROUP BY content_hash
HAVING COUNT(*)>1;

CREATE VIEW IF NOT EXISTS v_clay_stale_work_evidence AS
SELECT o.observation_id,o.source_class,o.source_ref,o.work_id,o.work_spec_rev,
       o.work_revision_state,o.current_work_credit_eligible,o.bound_repo_head,
       o.bound_component_hashes_clay,o.execution_started_at,o.observed_at
FROM clay_omnisource_observations o
WHERE o.work_revision_state IN ('STALE','UNKNOWN');

-- Producer-declared CURRENT binding. This is only a candidate projection and must never be
-- consumed as authoritative current-work completion credit by itself.
CREATE VIEW IF NOT EXISTS v_clay_current_work_credit_receipts AS
SELECT r.*
FROM clay_research_reentry_receipts r
WHERE r.current_work_credit_eligible=1
  AND r.work_revision_state='CURRENT';

-- Authoritative cross-check against the V9 dynamic-work current revision projection.
-- V9 remains the work-spec authority; V10 does not duplicate or replace it.
CREATE VIEW IF NOT EXISTS v_clay_authoritative_current_work_credit_receipts AS
SELECT r.*
FROM clay_research_reentry_receipts r
JOIN v_clay_current_work_specs w
  ON w.work_id=r.work_id AND w.spec_rev=r.work_spec_rev
WHERE r.current_work_credit_eligible=1
  AND r.work_revision_state='CURRENT';

CREATE VIEW IF NOT EXISTS v_clay_work_credit_revision_mismatches AS
SELECT r.receipt_id,r.work_id,r.work_spec_rev AS receipt_spec_rev,
       w.spec_rev AS current_spec_rev,r.bound_repo_head,r.bound_component_hashes_clay,
       r.closure_state,r.created_at
FROM clay_research_reentry_receipts r
LEFT JOIN v_clay_current_work_specs w ON w.work_id=r.work_id
WHERE r.current_work_credit_eligible=1
  AND (w.work_id IS NULL OR w.spec_rev<>r.work_spec_rev);

CREATE VIEW IF NOT EXISTS v_clay_reentry_branch_closure AS
SELECT r.receipt_id,
       COUNT(b.branch_ref) AS branch_count,
       SUM(CASE WHEN b.delivered=1 THEN 1 ELSE 0 END) AS delivered_count,
       SUM(CASE WHEN b.reconstructed=1 THEN 1 ELSE 0 END) AS reconstructed_count,
       SUM(CASE WHEN b.plan_revalidated=1 THEN 1 ELSE 0 END) AS plan_revalidated_count,
       SUM(CASE WHEN b.used=1 THEN 1 ELSE 0 END) AS used_count,
       SUM(CASE WHEN b.local_effect=1 THEN 1 ELSE 0 END) AS local_effect_count
FROM clay_research_reentry_receipts r
LEFT JOIN clay_reentry_branch_receipts b USING(receipt_id)
GROUP BY r.receipt_id;

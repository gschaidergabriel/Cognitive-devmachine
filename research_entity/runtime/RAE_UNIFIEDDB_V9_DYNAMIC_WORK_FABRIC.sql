-- CLAY U9 · SYSTEM POSSIBILITY TABLE + REVISIONED DYNAMIC WORK FABRIC
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS clay_system_resource_observations(
  observation_id TEXT PRIMARY KEY,
  resource_id TEXT NOT NULL,
  resource_class TEXT NOT NULL,
  label TEXT NOT NULL,
  host_or_surface TEXT,
  provider TEXT,
  details_clay TEXT NOT NULL DEFAULT '{}',
  authority_clay TEXT NOT NULL DEFAULT '{}',
  availability_state TEXT NOT NULL CHECK(availability_state IN ('AVAILABLE','UNAVAILABLE','STALE','UNKNOWN','DEGRADED')),
  evidence_class TEXT NOT NULL,
  evidence_ref TEXT,
  observed_at TEXT NOT NULL,
  freshness_seconds INTEGER NOT NULL DEFAULT 900,
  writer_node TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_clay_resource_obs ON clay_system_resource_observations(resource_id,observed_at DESC);

CREATE TABLE IF NOT EXISTS clay_capability_observations(
  observation_id TEXT PRIMARY KEY,
  capability_instance_id TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  capability_key TEXT NOT NULL,
  capability_class TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('CAN_NOW','CAN_DELEGATE','CANNOT_NOW','UNKNOWN','STALE')),
  modalities_clay TEXT NOT NULL DEFAULT '[]',
  execution_scope_clay TEXT NOT NULL DEFAULT '{}',
  authority_scope_clay TEXT NOT NULL DEFAULT '{}',
  cost_clay TEXT NOT NULL DEFAULT '{}',
  latency_clay TEXT NOT NULL DEFAULT '{}',
  privacy_clay TEXT NOT NULL DEFAULT '{}',
  trials INTEGER NOT NULL DEFAULT 0,
  successes INTEGER NOT NULL DEFAULT 0,
  confidence REAL NOT NULL,
  evidence_clay TEXT NOT NULL DEFAULT '{}',
  observed_at TEXT NOT NULL,
  freshness_seconds INTEGER NOT NULL DEFAULT 900,
  writer_node TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_clay_cap_obs ON clay_capability_observations(capability_instance_id,observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_clay_cap_key ON clay_capability_observations(capability_key,observed_at DESC);

CREATE TABLE IF NOT EXISTS clay_work_items(
  work_id TEXT PRIMARY KEY,
  goal_ref TEXT NOT NULL,
  origin_class TEXT NOT NULL,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  terminal_status TEXT,
  terminal_at TEXT
);

CREATE TABLE IF NOT EXISTS clay_work_spec_revisions(
  work_id TEXT NOT NULL REFERENCES clay_work_items(work_id) ON DELETE CASCADE,
  spec_rev INTEGER NOT NULL,
  parent_rev INTEGER,
  title TEXT NOT NULL,
  work_clay TEXT NOT NULL,
  reason_clay TEXT NOT NULL DEFAULT '{}',
  completion_clay TEXT NOT NULL,
  evidence_need_clay TEXT NOT NULL DEFAULT '[]',
  executor_policy_clay TEXT NOT NULL DEFAULT '{}',
  required_capabilities_clay TEXT NOT NULL DEFAULT '[]',
  write_scope_clay TEXT NOT NULL DEFAULT '[]',
  dependency_clay TEXT NOT NULL DEFAULT '[]',
  invalidation_clay TEXT NOT NULL DEFAULT '[]',
  base_priority REAL NOT NULL DEFAULT 0.5,
  expected_impact REAL NOT NULL DEFAULT 0.5,
  urgency REAL NOT NULL DEFAULT 0.0,
  information_gain REAL NOT NULL DEFAULT 0.0,
  status TEXT NOT NULL CHECK(status IN ('PROPOSED','READY','DEFERRED','BLOCKED','SUPERSEDED','CANCELLED')),
  source_ref TEXT,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(work_id,spec_rev)
);

CREATE TABLE IF NOT EXISTS clay_work_dependencies(
  work_id TEXT NOT NULL,
  depends_on_work_id TEXT NOT NULL,
  dependency_class TEXT NOT NULL,
  condition_clay TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  PRIMARY KEY(work_id,depends_on_work_id,dependency_class),
  FOREIGN KEY(work_id) REFERENCES clay_work_items(work_id),
  FOREIGN KEY(depends_on_work_id) REFERENCES clay_work_items(work_id)
);

CREATE TABLE IF NOT EXISTS clay_work_scheduler_receipts(
  scheduler_receipt_id TEXT PRIMARY KEY,
  work_id TEXT NOT NULL REFERENCES clay_work_items(work_id),
  spec_rev INTEGER NOT NULL,
  scheduler_node TEXT NOT NULL,
  goal_fit REAL NOT NULL,
  capability_fit REAL NOT NULL,
  availability_fit REAL NOT NULL,
  dependency_pressure REAL NOT NULL,
  urgency REAL NOT NULL,
  information_gain REAL NOT NULL,
  collision_risk REAL NOT NULL,
  cost_pressure REAL NOT NULL,
  stale_pressure REAL NOT NULL,
  priority_score REAL NOT NULL,
  eligibility_state TEXT NOT NULL CHECK(eligibility_state IN ('ELIGIBLE','BLOCKED','DEFER','STALE','CANCEL')),
  selected_executor TEXT,
  possibility_snapshot_clay TEXT NOT NULL,
  reason_clay TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(work_id,spec_rev) REFERENCES clay_work_spec_revisions(work_id,spec_rev)
);
CREATE INDEX IF NOT EXISTS idx_clay_sched_work ON clay_work_scheduler_receipts(work_id,created_at DESC);

CREATE TABLE IF NOT EXISTS clay_work_leases(
  lease_id TEXT PRIMARY KEY,
  work_id TEXT NOT NULL REFERENCES clay_work_items(work_id),
  spec_rev INTEGER NOT NULL,
  executor_node TEXT NOT NULL,
  lease_token TEXT NOT NULL UNIQUE,
  claimed_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('CLAIMED','RUNNING','RELEASED','EXPIRED','COMPLETE','ABORTED')),
  FOREIGN KEY(work_id,spec_rev) REFERENCES clay_work_spec_revisions(work_id,spec_rev)
);
CREATE INDEX IF NOT EXISTS idx_clay_lease_work ON clay_work_leases(work_id,claimed_at DESC);

CREATE TABLE IF NOT EXISTS clay_execution_receipts(
  execution_receipt_id TEXT PRIMARY KEY,
  work_id TEXT REFERENCES clay_work_items(work_id),
  spec_rev INTEGER,
  executor_node TEXT NOT NULL,
  executor_class TEXT NOT NULL,
  machine_ref TEXT,
  action_clay TEXT NOT NULL,
  observed_effect_clay TEXT NOT NULL,
  verification_clay TEXT NOT NULL,
  evidence_refs_clay TEXT NOT NULL DEFAULT '[]',
  truth_class TEXT NOT NULL CHECK(truth_class IN ('LOCAL_EXECUTION_PRIMARY','REMOTE_EXECUTION_RECEIPT','RESEARCH_EVIDENCE','SIMULATION_ONLY','UNVERIFIED')),
  success INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_clay_exec_work ON clay_execution_receipts(work_id,created_at DESC);

CREATE TABLE IF NOT EXISTS clay_implementation_maps(
  map_id TEXT PRIMARY KEY,
  source_turn_ref TEXT,
  subject_clay TEXT NOT NULL,
  possibility_snapshot_clay TEXT NOT NULL,
  recommended_path_clay TEXT NOT NULL,
  generated_work_ids_clay TEXT NOT NULL DEFAULT '[]',
  explanation_clay TEXT NOT NULL,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE VIEW IF NOT EXISTS v_clay_current_resources AS
WITH ranked AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY resource_id ORDER BY observed_at DESC,observation_id DESC) rn
 FROM clay_system_resource_observations
)
SELECT *,CASE WHEN datetime(observed_at,'+'||freshness_seconds||' seconds') < CURRENT_TIMESTAMP THEN 'STALE' ELSE availability_state END AS effective_availability
FROM ranked WHERE rn=1;

CREATE VIEW IF NOT EXISTS v_clay_current_capabilities AS
WITH ranked AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY capability_instance_id ORDER BY observed_at DESC,observation_id DESC) rn
 FROM clay_capability_observations
)
SELECT *,CASE WHEN datetime(observed_at,'+'||freshness_seconds||' seconds') < CURRENT_TIMESTAMP THEN 'STALE' ELSE state END AS effective_state
FROM ranked WHERE rn=1;

-- This is the single current system-possibility projection requested by the owner.
CREATE VIEW IF NOT EXISTS v_clay_system_possibility_table AS
SELECT r.resource_id,r.resource_class,r.label,r.host_or_surface,r.provider,r.details_clay,r.authority_clay,
       r.effective_availability,r.evidence_class,r.evidence_ref,r.observed_at AS resource_observed_at,
       c.capability_instance_id,c.capability_key,c.capability_class,c.effective_state AS capability_state,
       c.modalities_clay,c.execution_scope_clay,c.authority_scope_clay,c.cost_clay,c.latency_clay,c.privacy_clay,
       c.trials,c.successes,c.confidence,c.evidence_clay,c.observed_at AS capability_observed_at
FROM v_clay_current_resources r
LEFT JOIN v_clay_current_capabilities c ON c.resource_id=r.resource_id;

CREATE VIEW IF NOT EXISTS v_clay_current_work_specs AS
WITH ranked AS (
 SELECT s.*,ROW_NUMBER() OVER(PARTITION BY work_id ORDER BY spec_rev DESC) rn
 FROM clay_work_spec_revisions s
)
SELECT r.* FROM ranked r JOIN clay_work_items w USING(work_id)
WHERE r.rn=1 AND w.terminal_status IS NULL;

CREATE VIEW IF NOT EXISTS v_clay_current_scheduler AS
WITH ranked AS (
 SELECT s.*,ROW_NUMBER() OVER(PARTITION BY work_id ORDER BY created_at DESC,scheduler_receipt_id DESC) rn
 FROM clay_work_scheduler_receipts s
)
SELECT * FROM ranked WHERE rn=1;

CREATE VIEW IF NOT EXISTS v_clay_dynamic_work_queue AS
SELECT w.work_id,w.goal_ref,s.spec_rev,s.title,s.work_clay,s.completion_clay,s.required_capabilities_clay,
       s.executor_policy_clay,s.dependency_clay,s.invalidation_clay,s.status AS spec_status,
       q.priority_score,q.eligibility_state,q.selected_executor,q.possibility_snapshot_clay,q.reason_clay,
       s.created_at AS spec_created_at,q.created_at AS scheduled_at
FROM clay_work_items w
JOIN v_clay_current_work_specs s USING(work_id)
LEFT JOIN v_clay_current_scheduler q USING(work_id)
WHERE s.status NOT IN ('SUPERSEDED','CANCELLED')
ORDER BY COALESCE(q.priority_score,s.base_priority) DESC,s.created_at;

CREATE VIEW IF NOT EXISTS v_clay_local_operational_truth AS
SELECT * FROM clay_execution_receipts WHERE truth_class='LOCAL_EXECUTION_PRIMARY';

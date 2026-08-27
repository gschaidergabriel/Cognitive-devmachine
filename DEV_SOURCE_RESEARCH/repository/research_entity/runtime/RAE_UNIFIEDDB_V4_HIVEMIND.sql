PRAGMA foreign_keys=ON;

-- RAE v4: provider-agnostic hive/self/world/prospection/slow-plasticity substrate.
-- GitHub/event ledgers remain the cross-provider durable spine; this SQLite is a fast
-- local materialization of the same persistent Research Entity.

CREATE TABLE IF NOT EXISTS hive_organs(
  node_id TEXT PRIMARY KEY,
  actor_id TEXT NOT NULL,
  provider TEXT NOT NULL,
  model TEXT,
  organ_role TEXT NOT NULL,
  session_id TEXT,
  capabilities_clay TEXT NOT NULL DEFAULT '{}',
  limitations_clay TEXT NOT NULL DEFAULT '{}',
  authority_clay TEXT NOT NULL DEFAULT '{}',
  lifecycle_state TEXT NOT NULL,
  joined_at TEXT NOT NULL,
  last_pulse_at TEXT NOT NULL,
  freshness_limit_s INTEGER NOT NULL DEFAULT 900,
  last_state_epoch INTEGER,
  last_graph_epoch INTEGER
);

CREATE TABLE IF NOT EXISTS hive_handoffs(
  handoff_id TEXT PRIMARY KEY,
  work_ref TEXT,
  from_node_id TEXT NOT NULL,
  to_actor_id TEXT,
  to_node_id TEXT,
  summary_clay TEXT NOT NULL,
  evidence_refs_clay TEXT NOT NULL DEFAULT '[]',
  unresolved_clay TEXT NOT NULL DEFAULT '[]',
  requested_next_clay TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  consumed_at TEXT,
  consumed_by_node_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_hive_handoff_target ON hive_handoffs(to_actor_id,status,created_at DESC);

CREATE TABLE IF NOT EXISTS rae_world_records(
  record_id TEXT PRIMARY KEY,
  region TEXT NOT NULL,
  semantic_key TEXT NOT NULL,
  payload_clay TEXT NOT NULL,
  epistemic_class TEXT NOT NULL,
  evidence_refs_clay TEXT NOT NULL DEFAULT '[]',
  parent_refs_clay TEXT NOT NULL DEFAULT '[]',
  valid_from TEXT,
  valid_to TEXT,
  observed_at TEXT NOT NULL,
  confidence REAL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rae_world_current ON rae_world_records(region,semantic_key,status,valid_to);

CREATE TABLE IF NOT EXISTS rae_self_observations(
  observation_id TEXT PRIMARY KEY,
  organ_id TEXT NOT NULL,
  organ_class TEXT NOT NULL,
  state_clay TEXT NOT NULL,
  capabilities_clay TEXT NOT NULL DEFAULT '[]',
  limitations_clay TEXT NOT NULL DEFAULT '[]',
  authority_clay TEXT NOT NULL DEFAULT '[]',
  health TEXT NOT NULL,
  current_work_ref TEXT,
  last_effect_ref TEXT,
  observed_at TEXT NOT NULL,
  freshness_limit_s INTEGER NOT NULL,
  confidence REAL NOT NULL,
  evidence_refs_clay TEXT NOT NULL DEFAULT '[]'
);
CREATE INDEX IF NOT EXISTS idx_rae_self_obs ON rae_self_observations(organ_id,observed_at DESC);

CREATE TABLE IF NOT EXISTS rae_prospective_states(
  prospective_id TEXT PRIMARY KEY,
  current_refs_clay TEXT NOT NULL,
  intervention_clay TEXT,
  predicted_clay TEXT NOT NULL,
  assumptions_clay TEXT NOT NULL DEFAULT '[]',
  horizon TEXT NOT NULL,
  probability REAL,
  confidence REAL,
  falsifiers_clay TEXT NOT NULL DEFAULT '[]',
  invalidators_clay TEXT NOT NULL DEFAULT '[]',
  evidence_refs_clay TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  resolved_at TEXT,
  outcome_ref TEXT
);

CREATE TABLE IF NOT EXISTS rae_causal_credit(
  credit_id TEXT PRIMARY KEY,
  outcome_ref TEXT NOT NULL,
  target_ref TEXT NOT NULL,
  credit_class TEXT NOT NULL,
  weight REAL NOT NULL,
  evidence_refs_clay TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rae_usage_episodes(
  episode_id TEXT PRIMARY KEY,
  cycle_id TEXT,
  node_id TEXT NOT NULL,
  task_shape TEXT,
  selected_refs_clay TEXT NOT NULL DEFAULT '[]',
  suppressed_refs_clay TEXT NOT NULL DEFAULT '[]',
  retrieval_receipts_clay TEXT NOT NULL DEFAULT '[]',
  decision_clay TEXT,
  expected_clay TEXT NOT NULL DEFAULT '[]',
  observed_outcome_clay TEXT NOT NULL DEFAULT '[]',
  friction_clay TEXT NOT NULL DEFAULT '[]',
  correction_clay TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rae_plasticity_signals(
  signal_id TEXT PRIMARY KEY,
  episode_id TEXT NOT NULL,
  target_kind TEXT NOT NULL,
  target_key TEXT NOT NULL,
  direction REAL NOT NULL,
  magnitude REAL NOT NULL,
  confidence REAL NOT NULL,
  evidence_class TEXT NOT NULL,
  rationale_clay TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(episode_id) REFERENCES rae_usage_episodes(episode_id)
);
CREATE INDEX IF NOT EXISTS idx_plasticity_target ON rae_plasticity_signals(target_kind,target_key,status,created_at DESC);

CREATE TABLE IF NOT EXISTS rae_adaptive_parameters(
  parameter_key TEXT PRIMARY KEY,
  value REAL NOT NULL,
  min_value REAL NOT NULL,
  max_value REAL NOT NULL,
  max_step_per_episode REAL NOT NULL,
  max_step_per_day REAL NOT NULL,
  evidence_floor REAL NOT NULL,
  update_count INTEGER NOT NULL DEFAULT 0,
  last_updated_at TEXT,
  provenance_clay TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS rae_mutation_candidates(
  mutation_id TEXT PRIMARY KEY,
  target_scope TEXT NOT NULL,
  hypothesis_clay TEXT NOT NULL,
  predicted_effect_clay TEXT NOT NULL,
  evidence_refs_clay TEXT NOT NULL DEFAULT '[]',
  accumulated_support REAL NOT NULL DEFAULT 0.0,
  baseline_snapshot_ref TEXT,
  shadow_result_ref TEXT,
  replay_result_ref TEXT,
  recovery_result_ref TEXT,
  rollback_ref TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

INSERT OR IGNORE INTO rae_adaptive_parameters VALUES
 ('retrieval.recency_weight',0.20,0.05,0.45,0.0025,0.02,0.70,0,NULL,'{}'),
 ('retrieval.evidence_weight',0.35,0.15,0.60,0.0025,0.02,0.70,0,NULL,'{}'),
 ('retrieval.negative_result_weight',0.25,0.10,0.50,0.0025,0.02,0.75,0,NULL,'{}'),
 ('workspace.novelty_weight',0.15,0.05,0.35,0.0020,0.015,0.72,0,NULL,'{}'),
 ('workspace.info_gain_weight',0.25,0.10,0.50,0.0020,0.015,0.72,0,NULL,'{}'),
 ('handoff.unresolved_priority',0.30,0.10,0.60,0.0025,0.02,0.70,0,NULL,'{}');

CREATE VIEW IF NOT EXISTS v_current_hive_organs AS
SELECT * FROM hive_organs
WHERE lifecycle_state IN ('ACTIVE_CURRENT_SESSION','ACTIVE','IDLE');

CREATE VIEW IF NOT EXISTS v_open_hive_handoffs AS
SELECT * FROM hive_handoffs WHERE status='OPEN';

CREATE VIEW IF NOT EXISTS v_current_rae_world AS
SELECT * FROM rae_world_records
WHERE status='CURRENT' AND (valid_to IS NULL OR valid_to > CURRENT_TIMESTAMP);

CREATE VIEW IF NOT EXISTS v_pending_mutations AS
SELECT * FROM rae_mutation_candidates
WHERE status IN ('PROPOSED','ACCUMULATING','SHADOWING','READY');

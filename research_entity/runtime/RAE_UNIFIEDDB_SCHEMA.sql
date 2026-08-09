PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS meta(
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS research_entities(
  entity_id TEXT PRIMARY KEY,
  entity_kind TEXT NOT NULL,
  label TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS actor_nodes(
  node_id TEXT PRIMARY KEY,
  actor_id TEXT NOT NULL,
  provider TEXT,
  model TEXT,
  runtime_class TEXT,
  lifecycle_state TEXT NOT NULL,
  session_id TEXT,
  capabilities_clay TEXT NOT NULL DEFAULT '{}',
  authority_clay TEXT NOT NULL DEFAULT '{}',
  joined_at TEXT NOT NULL,
  last_verified_at TEXT NOT NULL,
  session_epoch INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS state_epochs(
  epoch INTEGER PRIMARY KEY,
  parent_epoch INTEGER,
  tx_id TEXT,
  root_hash TEXT NOT NULL,
  committed_at TEXT NOT NULL,
  writer_node TEXT,
  FOREIGN KEY(parent_epoch) REFERENCES state_epochs(epoch)
);

CREATE TABLE IF NOT EXISTS semantic_transactions(
  tx_id TEXT PRIMARY KEY,
  idempotency_key TEXT NOT NULL UNIQUE,
  writer_node TEXT NOT NULL,
  base_epoch INTEGER NOT NULL,
  proposed_at TEXT NOT NULL,
  committed_at TEXT,
  status TEXT NOT NULL,
  authority_scope TEXT NOT NULL,
  intent_clay TEXT NOT NULL,
  source_ref TEXT,
  receipt_hash TEXT
);

CREATE TABLE IF NOT EXISTS transaction_ops(
  tx_id TEXT NOT NULL REFERENCES semantic_transactions(tx_id) ON DELETE CASCADE,
  op_no INTEGER NOT NULL,
  op_kind TEXT NOT NULL,
  target_kind TEXT NOT NULL,
  target_key TEXT NOT NULL,
  precondition_clay TEXT,
  payload_clay TEXT NOT NULL,
  PRIMARY KEY(tx_id,op_no)
);

CREATE TABLE IF NOT EXISTS semantic_records(
  record_id TEXT PRIMARY KEY,
  record_kind TEXT NOT NULL,
  record_key TEXT NOT NULL,
  scope TEXT NOT NULL,
  epistemic_class TEXT NOT NULL,
  payload_clay TEXT NOT NULL,
  source_ref TEXT,
  source_hash TEXT,
  valid_from TEXT,
  valid_to TEXT,
  status TEXT NOT NULL,
  source_epoch INTEGER,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(record_kind,record_key,scope,status)
);
CREATE INDEX IF NOT EXISTS idx_semantic_records_lookup ON semantic_records(record_kind,record_key,scope,status);

CREATE TABLE IF NOT EXISTS prompt_cycles(
  cycle_id TEXT PRIMARY KEY,
  node_id TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  input_digest TEXT,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  status TEXT NOT NULL,
  state_epoch_begin INTEGER,
  graph_epoch_begin INTEGER,
  state_epoch_end INTEGER,
  graph_epoch_end INTEGER,
  home_room_id TEXT,
  trigger_word TEXT
);
CREATE INDEX IF NOT EXISTS idx_prompt_cycles_node ON prompt_cycles(node_id,started_at DESC);

CREATE TABLE IF NOT EXISTS state_injections(
  injection_id TEXT PRIMARY KEY,
  cycle_id TEXT,
  node_id TEXT NOT NULL,
  event_name TEXT NOT NULL,
  capsule_hash TEXT NOT NULL,
  source_epoch INTEGER,
  graph_epoch INTEGER,
  bounded_content_clay TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS query_receipts(
  query_id TEXT PRIMARY KEY,
  cycle_id TEXT,
  node_id TEXT,
  query_kind TEXT NOT NULL,
  intent_clay TEXT NOT NULL,
  source_epoch INTEGER,
  graph_epoch INTEGER,
  planner_clay TEXT NOT NULL,
  result_refs_clay TEXT NOT NULL,
  admissibility_clay TEXT NOT NULL,
  result_hash TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS world_state(
  world_key TEXT PRIMARY KEY,
  payload_clay TEXT NOT NULL,
  epistemic_class TEXT NOT NULL,
  source_ref TEXT,
  source_hash TEXT,
  valid_from TEXT,
  valid_to TEXT,
  status TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS self_state(
  self_key TEXT PRIMARY KEY,
  payload_clay TEXT NOT NULL,
  evidence_class TEXT NOT NULL,
  source_ref TEXT,
  status TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS research_focus_state(
  focus_key TEXT PRIMARY KEY,
  payload_clay TEXT NOT NULL,
  priority REAL,
  confidence REAL,
  source_ref TEXT,
  status TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS room_state_refs(
  room_id TEXT PRIMARY KEY,
  room_state_ref TEXT NOT NULL,
  room_state_hash TEXT,
  active_worker_count INTEGER,
  last_pulse_at TEXT,
  status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_refs(
  evidence_id TEXT PRIMARY KEY,
  source_ref TEXT NOT NULL,
  evidence_class TEXT NOT NULL,
  ancestry_family TEXT,
  content_hash TEXT,
  observed_at TEXT NOT NULL,
  valid_from TEXT,
  valid_to TEXT,
  status TEXT NOT NULL,
  notes_clay TEXT
);

CREATE TABLE IF NOT EXISTS claim_refs(
  claim_id TEXT PRIMARY KEY,
  status TEXT NOT NULL,
  scope TEXT,
  proposition TEXT,
  source_ref TEXT,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pilot_interactions(
  interaction_id TEXT PRIMARY KEY,
  pilot_user_id TEXT NOT NULL,
  source_repo TEXT NOT NULL,
  source_interaction_ref TEXT NOT NULL,
  started_at TEXT,
  ended_at TEXT,
  provider_path_clay TEXT NOT NULL DEFAULT '[]',
  task_class TEXT,
  outcome_class TEXT,
  user_effort_score REAL,
  privacy_class TEXT NOT NULL,
  source_hash TEXT,
  status TEXT NOT NULL,
  ingested_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pilot_harness_events(
  event_id TEXT PRIMARY KEY,
  interaction_id TEXT REFERENCES pilot_interactions(interaction_id),
  event_time TEXT NOT NULL,
  event_type TEXT NOT NULL,
  node_id TEXT,
  state_epoch INTEGER,
  graph_epoch INTEGER,
  event_ref TEXT,
  payload_clay TEXT NOT NULL,
  privacy_class TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pilot_events_interaction ON pilot_harness_events(interaction_id,event_time);

CREATE TABLE IF NOT EXISTS misunderstanding_cases(
  case_id TEXT PRIMARY KEY,
  interaction_id TEXT REFERENCES pilot_interactions(interaction_id),
  detected_at TEXT NOT NULL,
  failure_classes_clay TEXT NOT NULL,
  user_correction_ref TEXT,
  expected_or_intended_clay TEXT,
  observed_behavior_clay TEXT NOT NULL,
  state_epoch_before INTEGER,
  state_epoch_after INTEGER,
  graph_epoch INTEGER,
  node_path_clay TEXT NOT NULL,
  query_receipts_clay TEXT NOT NULL,
  graph_refs_clay TEXT NOT NULL,
  tool_effect_refs_clay TEXT NOT NULL,
  candidate_causes_clay TEXT NOT NULL,
  selected_cause_clay TEXT,
  confidence REAL,
  repair_target TEXT,
  regression_fixture_ref TEXT,
  candidate_fix_ref TEXT,
  shadow_result_ref TEXT,
  live_verification_ref TEXT,
  promotion_scope TEXT,
  status TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_misunderstanding_status ON misunderstanding_cases(status,detected_at DESC);

CREATE TABLE IF NOT EXISTS success_patterns(
  pattern_id TEXT PRIMARY KEY,
  interaction_id TEXT REFERENCES pilot_interactions(interaction_id),
  pattern_class TEXT NOT NULL,
  mechanism_clay TEXT NOT NULL,
  generalization_scope TEXT,
  evidence_clay TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS repair_experiments(
  repair_id TEXT PRIMARY KEY,
  case_id TEXT REFERENCES misunderstanding_cases(case_id),
  target_component TEXT NOT NULL,
  hypothesis_clay TEXT NOT NULL,
  intervention_clay TEXT NOT NULL,
  baseline_ref TEXT,
  replay_result_ref TEXT,
  shadow_result_ref TEXT,
  live_result_ref TEXT,
  outcome_class TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS snapshots(
  snapshot_id TEXT PRIMARY KEY,
  unified_epoch INTEGER,
  graph_epoch INTEGER,
  unified_sha256 TEXT,
  graph_sha256 TEXT,
  transaction_cursor TEXT,
  canonical_revision INTEGER,
  canonical_state_hash TEXT,
  created_at TEXT NOT NULL,
  recovery_test_state TEXT NOT NULL DEFAULT 'UNTESTED'
);

CREATE VIEW IF NOT EXISTS v_open_misunderstandings AS
SELECT * FROM misunderstanding_cases WHERE status IN ('OPEN','REPRODUCED','FIX_CANDIDATE','SHADOW_TESTING');

CREATE VIEW IF NOT EXISTS v_active_actor_nodes AS
SELECT * FROM actor_nodes WHERE lifecycle_state IN ('ACTIVE','ACTIVE_CURRENT_SESSION','IDLE');

CREATE VIEW IF NOT EXISTS v_current_semantic_records AS
SELECT * FROM semantic_records WHERE status='CURRENT' AND (valid_to IS NULL OR valid_to > CURRENT_TIMESTAMP);

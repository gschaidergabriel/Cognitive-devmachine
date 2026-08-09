PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS pilot_usecases(
  usecase_id TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  scope TEXT NOT NULL,
  task_family TEXT NOT NULL,
  goal_refs_clay TEXT NOT NULL DEFAULT '[]',
  tool_classes_clay TEXT NOT NULL DEFAULT '[]',
  provider_paths_clay TEXT NOT NULL DEFAULT '[]',
  first_seen TEXT NOT NULL,
  last_seen TEXT NOT NULL,
  frequency_window TEXT,
  explicit_importance REAL,
  importance_confidence REAL NOT NULL DEFAULT 0.0,
  current_capability_fit REAL,
  generalization_hypothesis TEXT,
  status TEXT NOT NULL,
  parent_usecase_refs_clay TEXT NOT NULL DEFAULT '[]',
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pilot_usecases_family ON pilot_usecases(task_family,status,last_seen DESC);

CREATE TABLE IF NOT EXISTS usecase_interaction_refs(
  usecase_id TEXT NOT NULL REFERENCES pilot_usecases(usecase_id) ON DELETE CASCADE,
  interaction_id TEXT NOT NULL REFERENCES pilot_interactions(interaction_id) ON DELETE CASCADE,
  assignment_confidence REAL NOT NULL,
  evidence_ref TEXT,
  created_at TEXT NOT NULL,
  PRIMARY KEY(usecase_id,interaction_id)
);

CREATE TABLE IF NOT EXISTS usecase_importance_observations(
  observation_id TEXT PRIMARY KEY,
  usecase_id TEXT NOT NULL REFERENCES pilot_usecases(usecase_id) ON DELETE CASCADE,
  interaction_id TEXT REFERENCES pilot_interactions(interaction_id),
  observed_at TEXT NOT NULL,
  component TEXT NOT NULL,
  value REAL,
  confidence REAL NOT NULL,
  evidence_class TEXT NOT NULL,
  evidence_ref TEXT,
  evidence_clay TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_usecase_importance_component ON usecase_importance_observations(usecase_id,component,observed_at DESC);

CREATE TABLE IF NOT EXISTS usecase_capability_gaps(
  gap_id TEXT PRIMARY KEY,
  usecase_id TEXT NOT NULL REFERENCES pilot_usecases(usecase_id) ON DELETE CASCADE,
  capability_class TEXT NOT NULL,
  required_level REAL,
  observed_fit REAL,
  friction_clay TEXT NOT NULL,
  failure_case_refs_clay TEXT NOT NULL DEFAULT '[]',
  opportunity_refs_clay TEXT NOT NULL DEFAULT '[]',
  confidence REAL NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_usecase_gap_status ON usecase_capability_gaps(usecase_id,status,confidence DESC);

CREATE TABLE IF NOT EXISTS usecase_outcome_observations(
  observation_id TEXT PRIMARY KEY,
  usecase_id TEXT NOT NULL REFERENCES pilot_usecases(usecase_id) ON DELETE CASCADE,
  interaction_id TEXT REFERENCES pilot_interactions(interaction_id),
  observed_at TEXT NOT NULL,
  outcome_class TEXT NOT NULL,
  success_value REAL,
  user_effort REAL,
  correction_count INTEGER,
  reuse_signal REAL,
  bypass_signal REAL,
  evidence_ref TEXT,
  evidence_clay TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS usecase_promotion_decisions(
  decision_id TEXT PRIMARY KEY,
  usecase_id TEXT NOT NULL REFERENCES pilot_usecases(usecase_id) ON DELETE CASCADE,
  decided_at TEXT NOT NULL,
  decision_class TEXT NOT NULL,
  rationale_clay TEXT NOT NULL,
  evidence_refs_clay TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  status TEXT NOT NULL
);

CREATE VIEW IF NOT EXISTS v_active_pilot_usecases AS
SELECT * FROM pilot_usecases WHERE status IN ('CANDIDATE','ACTIVE','VALIDATED');

CREATE VIEW IF NOT EXISTS v_open_usecase_gaps AS
SELECT * FROM usecase_capability_gaps WHERE status IN ('OPEN','VALIDATED','TESTING');

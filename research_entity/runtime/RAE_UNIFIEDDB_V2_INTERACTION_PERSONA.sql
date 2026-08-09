PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS interaction_quality_observations(
  observation_id TEXT PRIMARY KEY,
  interaction_id TEXT REFERENCES pilot_interactions(interaction_id),
  observed_at TEXT NOT NULL,
  dimension TEXT NOT NULL,
  direction TEXT NOT NULL,
  magnitude REAL,
  confidence REAL NOT NULL,
  evidence_ref TEXT,
  evidence_clay TEXT NOT NULL,
  user_benefit_clay TEXT,
  autonomy_guard_state TEXT NOT NULL DEFAULT 'PASS',
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_interaction_quality_dimension ON interaction_quality_observations(dimension,observed_at DESC);

CREATE TABLE IF NOT EXISTS persona_consistency_observations(
  observation_id TEXT PRIMARY KEY,
  interaction_id TEXT REFERENCES pilot_interactions(interaction_id),
  observed_at TEXT NOT NULL,
  dimension TEXT NOT NULL,
  declared_state_ref TEXT,
  observed_behavior_clay TEXT NOT NULL,
  consistency_class TEXT NOT NULL,
  confidence REAL NOT NULL,
  node_path_clay TEXT NOT NULL,
  evidence_ref TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_persona_consistency_dimension ON persona_consistency_observations(dimension,observed_at DESC);

CREATE TABLE IF NOT EXISTS interaction_persona_cases(
  case_id TEXT PRIMARY KEY,
  interaction_id TEXT REFERENCES pilot_interactions(interaction_id),
  detected_at TEXT NOT NULL,
  case_classes_clay TEXT NOT NULL,
  quality_dimensions_clay TEXT NOT NULL,
  persona_dimensions_clay TEXT NOT NULL,
  observed_behavior_clay TEXT NOT NULL,
  expected_or_preferred_clay TEXT,
  candidate_causes_clay TEXT NOT NULL,
  selected_cause_clay TEXT,
  confidence REAL,
  repair_target TEXT,
  regression_fixture_ref TEXT,
  candidate_fix_ref TEXT,
  shadow_result_ref TEXT,
  live_verification_ref TEXT,
  promotion_scope TEXT,
  autonomy_guard_state TEXT NOT NULL DEFAULT 'PASS',
  status TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_interaction_persona_cases_status ON interaction_persona_cases(status,detected_at DESC);

CREATE TABLE IF NOT EXISTS persona_revisions(
  revision_id TEXT PRIMARY KEY,
  parent_revision_id TEXT,
  changed_at TEXT NOT NULL,
  changed_by_actor TEXT NOT NULL,
  change_scope TEXT NOT NULL,
  before_state_ref TEXT,
  after_state_ref TEXT NOT NULL,
  hypothesis_ref TEXT,
  evidence_refs_clay TEXT NOT NULL,
  rollback_ref TEXT,
  status TEXT NOT NULL
);

CREATE VIEW IF NOT EXISTS v_open_interaction_persona_cases AS
SELECT * FROM interaction_persona_cases
WHERE status IN ('OPEN','REPRODUCED','FIX_CANDIDATE','SHADOW_TESTING');

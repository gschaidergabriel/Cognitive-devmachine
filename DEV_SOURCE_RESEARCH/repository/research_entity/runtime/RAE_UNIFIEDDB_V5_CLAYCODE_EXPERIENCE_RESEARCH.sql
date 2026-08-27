PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS rae_experience_observations(
  observation_id TEXT PRIMARY KEY,
  episode_id TEXT,
  cycle_id TEXT,
  node_id TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  signal_class TEXT NOT NULL,
  task_shape TEXT,
  direction TEXT NOT NULL,
  magnitude REAL NOT NULL,
  confidence REAL NOT NULL,
  user_or_system_evidence_clay TEXT NOT NULL,
  suspected_layer TEXT,
  symptom_clay TEXT NOT NULL,
  preferred_property_clay TEXT,
  evidence_refs_clay TEXT NOT NULL DEFAULT '[]',
  token_cost_estimate REAL,
  latency_cost_ms REAL,
  repair_cost_estimate REAL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rae_experience_signal ON rae_experience_observations(signal_class,status,observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_rae_experience_layer ON rae_experience_observations(suspected_layer,status,observed_at DESC);

CREATE TABLE IF NOT EXISTS claycode_research_candidates(
  candidate_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  candidate_class TEXT NOT NULL,
  target_layer TEXT NOT NULL,
  pattern_key TEXT NOT NULL,
  supporting_observation_ids_clay TEXT NOT NULL,
  supporting_count INTEGER NOT NULL,
  positive_count INTEGER NOT NULL,
  negative_count INTEGER NOT NULL,
  mean_confidence REAL NOT NULL,
  accumulated_impact REAL NOT NULL,
  hypothesis_clay TEXT NOT NULL,
  counterhypothesis_clay TEXT NOT NULL,
  predicted_gain_clay TEXT NOT NULL,
  falsifier_clay TEXT NOT NULL,
  benchmark_plan_clay TEXT NOT NULL,
  current_best_mechanism_clay TEXT,
  status TEXT NOT NULL,
  promotion_gate TEXT NOT NULL,
  UNIQUE(pattern_key,status)
);
CREATE INDEX IF NOT EXISTS idx_claycode_research_priority ON claycode_research_candidates(status,accumulated_impact DESC,supporting_count DESC);

CREATE TABLE IF NOT EXISTS claycode_research_experiments(
  experiment_id TEXT PRIMARY KEY,
  candidate_id TEXT NOT NULL REFERENCES claycode_research_candidates(candidate_id) ON DELETE CASCADE,
  preregistered_at TEXT NOT NULL,
  baseline_ref TEXT,
  treatment_ref TEXT,
  matched_budget_rule_clay TEXT NOT NULL,
  metrics_clay TEXT NOT NULL,
  result_clay TEXT,
  outcome_class TEXT,
  evidence_refs_clay TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL,
  completed_at TEXT
);

CREATE TABLE IF NOT EXISTS claycode_experience_promotions(
  promotion_id TEXT PRIMARY KEY,
  candidate_id TEXT NOT NULL REFERENCES claycode_research_candidates(candidate_id),
  experiment_id TEXT REFERENCES claycode_research_experiments(experiment_id),
  promoted_at TEXT NOT NULL,
  target_scope TEXT NOT NULL,
  delta_ref TEXT NOT NULL,
  rollback_ref TEXT,
  causal_receipt_clay TEXT NOT NULL,
  status TEXT NOT NULL
);

CREATE VIEW IF NOT EXISTS v_claycode_experience_research_queue AS
SELECT * FROM claycode_research_candidates
WHERE status IN ('OPEN','ACCUMULATING','READY_FOR_EXPERIMENT','EXPERIMENTING')
ORDER BY accumulated_impact DESC,supporting_count DESC,updated_at DESC;

CREATE VIEW IF NOT EXISTS v_unrouted_rae_experience AS
SELECT * FROM rae_experience_observations
WHERE status='OPEN'
ORDER BY magnitude*confidence DESC,observed_at DESC;

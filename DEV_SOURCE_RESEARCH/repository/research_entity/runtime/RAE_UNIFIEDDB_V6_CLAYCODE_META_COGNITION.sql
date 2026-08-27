PRAGMA foreign_keys=ON;

-- Observable explicit-cognition / operation traces -> ClayCode research.
-- Hidden provider chain-of-thought is never collected or required.

CREATE TABLE IF NOT EXISTS claycode_meta_observations(
  observation_id TEXT PRIMARY KEY,
  cycle_id TEXT,
  node_id TEXT NOT NULL,
  actor_id TEXT,
  event_class TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  trace_class TEXT NOT NULL,
  trace_shape_clay TEXT NOT NULL,
  state_refs_clay TEXT NOT NULL DEFAULT '[]',
  operation_refs_clay TEXT NOT NULL DEFAULT '[]',
  outcome_refs_clay TEXT NOT NULL DEFAULT '[]',
  detected_properties_clay TEXT NOT NULL DEFAULT '[]',
  suspected_claycode_layers_clay TEXT NOT NULL DEFAULT '[]',
  candidate_primitives_clay TEXT NOT NULL DEFAULT '[]',
  token_cost_estimate REAL,
  latency_cost_ms REAL,
  evidence_class TEXT NOT NULL,
  confidence REAL NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cc_meta_obs_event ON claycode_meta_observations(event_class,status,observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_cc_meta_obs_trace ON claycode_meta_observations(trace_class,status,observed_at DESC);

CREATE TABLE IF NOT EXISTS claycode_meta_patterns(
  pattern_id TEXT PRIMARY KEY,
  pattern_key TEXT NOT NULL,
  target_layer TEXT NOT NULL,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  observation_ids_clay TEXT NOT NULL,
  count_total INTEGER NOT NULL,
  count_positive INTEGER NOT NULL,
  count_negative INTEGER NOT NULL,
  count_friction INTEGER NOT NULL,
  accumulated_weight REAL NOT NULL,
  hypothesis_clay TEXT NOT NULL,
  counterhypothesis_clay TEXT NOT NULL,
  candidate_language_delta_clay TEXT NOT NULL,
  predicted_effect_clay TEXT NOT NULL,
  falsifier_clay TEXT NOT NULL,
  benchmark_plan_clay TEXT NOT NULL,
  status TEXT NOT NULL,
  UNIQUE(pattern_key,status)
);
CREATE INDEX IF NOT EXISTS idx_cc_meta_pattern_priority ON claycode_meta_patterns(status,accumulated_weight DESC,count_total DESC,last_seen_at DESC);

CREATE TABLE IF NOT EXISTS claycode_meta_derivation_receipts(
  receipt_id TEXT PRIMARY KEY,
  observation_id TEXT NOT NULL REFERENCES claycode_meta_observations(observation_id),
  pattern_id TEXT REFERENCES claycode_meta_patterns(pattern_id),
  derived_at TEXT NOT NULL,
  derivation_version TEXT NOT NULL,
  rule_hits_clay TEXT NOT NULL,
  conclusion_clay TEXT NOT NULL,
  uncertainty_clay TEXT NOT NULL,
  status TEXT NOT NULL
);

CREATE VIEW IF NOT EXISTS v_open_claycode_meta_observations AS
SELECT * FROM claycode_meta_observations WHERE status='OPEN' ORDER BY observed_at;

CREATE VIEW IF NOT EXISTS v_claycode_meta_research_queue AS
SELECT * FROM claycode_meta_patterns
WHERE status IN ('ACCUMULATING','READY_FOR_EXPERIMENT','EXPERIMENTING')
ORDER BY accumulated_weight DESC,count_total DESC,last_seen_at DESC;

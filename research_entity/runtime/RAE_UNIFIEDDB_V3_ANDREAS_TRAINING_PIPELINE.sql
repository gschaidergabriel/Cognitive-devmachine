PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS andreas_research_candidates(
  candidate_id TEXT PRIMARY KEY,
  source_ref TEXT NOT NULL,
  source_class TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  valid_from TEXT,
  valid_to TEXT,
  entity_resolution_score REAL NOT NULL,
  confidence REAL NOT NULL,
  recurrence REAL NOT NULL,
  task_importance REAL NOT NULL,
  correction_cost REAL NOT NULL,
  outcome_impact REAL NOT NULL,
  future_utility REAL NOT NULL,
  generalizability REAL NOT NULL,
  novelty REAL NOT NULL,
  mechanics_fraction REAL NOT NULL,
  deterministic_score REAL NOT NULL,
  verifiability_score REAL NOT NULL,
  privacy_class TEXT NOT NULL,
  sensitivity_class TEXT NOT NULL,
  staleness REAL NOT NULL,
  usecase_label TEXT,
  cognitive_pattern TEXT,
  payload_clay TEXT NOT NULL,
  evidence_clay TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_andreas_candidates_status ON andreas_research_candidates(status,observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_andreas_candidates_usecase ON andreas_research_candidates(usecase_label,novelty DESC);

CREATE TABLE IF NOT EXISTS andreas_candidate_routes(
  route_id TEXT PRIMARY KEY,
  candidate_id TEXT NOT NULL REFERENCES andreas_research_candidates(candidate_id) ON DELETE CASCADE,
  destination TEXT NOT NULL,
  weight REAL NOT NULL,
  priority REAL NOT NULL,
  rationale_clay TEXT NOT NULL,
  status TEXT NOT NULL,
  generated_at TEXT NOT NULL,
  UNIQUE(candidate_id,destination,status)
);
CREATE INDEX IF NOT EXISTS idx_andreas_routes_destination ON andreas_candidate_routes(destination,status,priority DESC);

CREATE TABLE IF NOT EXISTS andreas_usecase_observations(
  observation_id TEXT PRIMARY KEY,
  candidate_id TEXT NOT NULL REFERENCES andreas_research_candidates(candidate_id) ON DELETE CASCADE,
  detected_at TEXT NOT NULL,
  usecase_class TEXT NOT NULL,
  novelty REAL NOT NULL,
  evidence_clay TEXT NOT NULL,
  status TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_andreas_usecase_class ON andreas_usecase_observations(usecase_class,status,novelty DESC);

CREATE TABLE IF NOT EXISTS needle_offload_candidates(
  offload_id TEXT PRIMARY KEY,
  candidate_id TEXT NOT NULL REFERENCES andreas_research_candidates(candidate_id) ON DELETE CASCADE,
  mechanics_fraction REAL NOT NULL,
  deterministic_score REAL NOT NULL,
  verifiability_score REAL NOT NULL,
  adapter_scope TEXT,
  semantic_residual_clay TEXT NOT NULL,
  priority REAL NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(candidate_id,status)
);
CREATE INDEX IF NOT EXISTS idx_needle_offload_status ON needle_offload_candidates(status,priority DESC);

CREATE TABLE IF NOT EXISTS andreas_training_case_specs(
  case_id TEXT PRIMARY KEY,
  candidate_id TEXT NOT NULL REFERENCES andreas_research_candidates(candidate_id) ON DELETE CASCADE,
  variant_type TEXT NOT NULL,
  cognitive_pattern TEXT,
  source_state_clay TEXT NOT NULL,
  target_dimensions_clay TEXT NOT NULL,
  personalization_clay TEXT NOT NULL,
  transfer_constraints_clay TEXT NOT NULL,
  weight REAL NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_andreas_training_cases ON andreas_training_case_specs(variant_type,status,weight DESC);

CREATE TABLE IF NOT EXISTS andreas_training_manifests(
  manifest_id TEXT PRIMARY KEY,
  policy_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  min_weight REAL NOT NULL,
  candidate_count INTEGER NOT NULL,
  model_training_count INTEGER NOT NULL,
  runtime_memory_count INTEGER NOT NULL,
  regression_count INTEGER NOT NULL,
  needle_count INTEGER NOT NULL,
  unknown_usecase_count INTEGER NOT NULL,
  manifest_clay TEXT NOT NULL,
  status TEXT NOT NULL
);

CREATE VIEW IF NOT EXISTS v_andreas_model_training_queue AS
SELECT c.*, r.weight, r.priority, r.rationale_clay
FROM andreas_research_candidates c
JOIN andreas_candidate_routes r ON r.candidate_id=c.candidate_id
WHERE c.status='CURRENT' AND r.destination='MODEL_TRAINING' AND r.status='CURRENT';

CREATE VIEW IF NOT EXISTS v_andreas_runtime_memory_queue AS
SELECT c.*, r.weight, r.priority, r.rationale_clay
FROM andreas_research_candidates c
JOIN andreas_candidate_routes r ON r.candidate_id=c.candidate_id
WHERE c.status='CURRENT' AND r.destination='ANDREAS_UNIFIEDDB' AND r.status='CURRENT';

CREATE VIEW IF NOT EXISTS v_andreas_unknown_usecases AS
SELECT c.*, u.usecase_class, u.novelty AS detected_novelty
FROM andreas_research_candidates c
JOIN andreas_usecase_observations u ON u.candidate_id=c.candidate_id
WHERE c.status='CURRENT' AND u.usecase_class='UNKNOWN/EMERGING_USECASE' AND u.status='OPEN';

CREATE VIEW IF NOT EXISTS v_needle_offload_queue AS
SELECT c.candidate_id,c.source_ref,c.usecase_label,n.*
FROM needle_offload_candidates n
JOIN andreas_research_candidates c ON c.candidate_id=n.candidate_id
WHERE c.status='CURRENT' AND n.status='OPEN';

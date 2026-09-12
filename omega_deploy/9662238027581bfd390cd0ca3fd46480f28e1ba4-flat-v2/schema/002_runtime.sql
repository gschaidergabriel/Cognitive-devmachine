PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS effect_intent(
  effect_id TEXT PRIMARY KEY,
  frame_id TEXT,
  organ_id TEXT NOT NULL,
  owner_id TEXT,
  machine_id TEXT,
  request_digest TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  authority_state TEXT NOT NULL,
  dispatch_state TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS effect_intent_state ON effect_intent(dispatch_state,updated_at);

CREATE TABLE IF NOT EXISTS organ_telemetry(
  organ_id TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  owner_id TEXT,
  machine_id TEXT,
  health TEXT NOT NULL,
  cpu_load REAL,
  ram_load REAL,
  gpu_load REAL,
  payload_json TEXT NOT NULL,
  content_digest TEXT NOT NULL,
  PRIMARY KEY(organ_id,observed_at,content_digest)
);
CREATE INDEX IF NOT EXISTS organ_telemetry_latest ON organ_telemetry(organ_id,observed_at DESC);

CREATE TABLE IF NOT EXISTS relay_ledger(
  effect_id TEXT PRIMARY KEY,
  organ_id TEXT NOT NULL,
  command_id TEXT,
  state TEXT NOT NULL,
  attempt_count INTEGER NOT NULL DEFAULT 0,
  command_digest TEXT,
  receipt_digest TEXT,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS worker_run(
  worker_run_id TEXT PRIMARY KEY,
  provider TEXT,
  model TEXT,
  role TEXT,
  admission_ref TEXT,
  input_digest TEXT NOT NULL,
  output_digest TEXT,
  state TEXT NOT NULL,
  canonical_credit_minted INTEGER NOT NULL DEFAULT 0 CHECK(canonical_credit_minted IN(0,1)),
  started_at TEXT NOT NULL,
  finished_at TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS world_projection_checkpoint(
  checkpoint_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  source_observation_count INTEGER NOT NULL,
  source_claim_count INTEGER NOT NULL,
  projection_digest TEXT NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS policy_decision(
  decision_id TEXT PRIMARY KEY,
  effect_id TEXT NOT NULL,
  binding_id TEXT NOT NULL,
  authority_ref TEXT NOT NULL,
  decision TEXT NOT NULL,
  reason TEXT NOT NULL,
  request_digest TEXT NOT NULL,
  organ_id TEXT NOT NULL,
  owner_id TEXT,
  machine_id TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS policy_decision_effect ON policy_decision(effect_id,created_at DESC);

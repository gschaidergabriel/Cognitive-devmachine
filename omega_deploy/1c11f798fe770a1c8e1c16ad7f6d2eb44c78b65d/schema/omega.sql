PRAGMA foreign_keys=ON;
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS source_subject(
  source_id TEXT PRIMARY KEY,
  source_kind TEXT NOT NULL,
  canonical_name TEXT NOT NULL,
  owner_id TEXT,
  machine_id TEXT,
  installation_id TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS observation(
  observation_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES source_subject(source_id),
  subject_id TEXT NOT NULL,
  owner_id TEXT,
  machine_id TEXT,
  installation_id TEXT,
  runtime_epoch_id TEXT,
  source_repo TEXT,
  source_commit TEXT,
  source_path TEXT,
  receipt_id TEXT,
  raw_locator TEXT,
  observed_at TEXT NOT NULL,
  ingested_at TEXT NOT NULL,
  evidence_class TEXT NOT NULL,
  authority_rank INTEGER NOT NULL DEFAULT 0,
  confidence REAL CHECK(confidence IS NULL OR confidence BETWEEN 0.0 AND 1.0),
  content_digest TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  UNIQUE(source_id,subject_id,runtime_epoch_id,content_digest,observed_at)
);
CREATE INDEX IF NOT EXISTS observation_subject_time ON observation(subject_id,observed_at DESC);
CREATE INDEX IF NOT EXISTS observation_source_time ON observation(source_id,observed_at DESC);
CREATE INDEX IF NOT EXISTS observation_machine_time ON observation(machine_id,observed_at DESC);

CREATE TABLE IF NOT EXISTS claim(
  claim_id TEXT PRIMARY KEY,
  subject_id TEXT NOT NULL,
  predicate TEXT NOT NULL,
  object_json TEXT NOT NULL,
  status TEXT NOT NULL,
  evidence_class TEXT NOT NULL,
  authority_rank INTEGER NOT NULL DEFAULT 0,
  confidence REAL,
  current INTEGER NOT NULL DEFAULT 1 CHECK(current IN(0,1)),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claim_evidence(
  claim_id TEXT NOT NULL REFERENCES claim(claim_id) ON DELETE CASCADE,
  observation_id TEXT NOT NULL REFERENCES observation(observation_id) ON DELETE CASCADE,
  relation TEXT NOT NULL,
  PRIMARY KEY(claim_id,observation_id,relation)
);

CREATE TABLE IF NOT EXISTS world_entity(
  entity_id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,
  canonical_name TEXT NOT NULL,
  properties_json TEXT NOT NULL DEFAULT '{}',
  confidence REAL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS world_relation(
  relation_id TEXT PRIMARY KEY,
  subject_entity_id TEXT NOT NULL REFERENCES world_entity(entity_id),
  predicate TEXT NOT NULL,
  object_entity_id TEXT NOT NULL REFERENCES world_entity(entity_id),
  confidence REAL,
  evidence_claim_id TEXT REFERENCES claim(claim_id),
  valid_from TEXT,
  valid_to TEXT,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cognition_epoch(
  epoch_id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  predecessor_epoch_id TEXT REFERENCES cognition_epoch(epoch_id),
  reason TEXT NOT NULL,
  status TEXT NOT NULL,
  state_digest TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cognition_frame(
  frame_id TEXT PRIMARY KEY,
  epoch_id TEXT NOT NULL REFERENCES cognition_epoch(epoch_id),
  predecessor_frame_id TEXT REFERENCES cognition_frame(frame_id),
  created_at TEXT NOT NULL,
  trigger_kind TEXT NOT NULL,
  context_digest TEXT NOT NULL,
  selected_proposal_id TEXT,
  broadcast_json TEXT,
  state_digest TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS proposal(
  proposal_id TEXT PRIMARY KEY,
  frame_id TEXT NOT NULL REFERENCES cognition_frame(frame_id) ON DELETE CASCADE,
  cell_id TEXT NOT NULL,
  worker_kind TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  score REAL,
  selected INTEGER NOT NULL DEFAULT 0 CHECK(selected IN(0,1)),
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS task(
  task_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  state TEXT NOT NULL,
  assigned_organ TEXT,
  priority INTEGER NOT NULL DEFAULT 0,
  lease_owner TEXT,
  lease_expires_at TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS effect_receipt(
  effect_id TEXT PRIMARY KEY,
  subject_id TEXT NOT NULL,
  owner_id TEXT,
  machine_id TEXT,
  runtime_epoch_id TEXT,
  action_kind TEXT NOT NULL,
  request_digest TEXT NOT NULL,
  result_digest TEXT,
  status TEXT NOT NULL,
  requested_at TEXT NOT NULL,
  completed_at TEXT,
  receipt_locator TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS improvement_candidate(
  candidate_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  proposer TEXT NOT NULL,
  target TEXT NOT NULL,
  hypothesis TEXT NOT NULL,
  patch_locator TEXT,
  state TEXT NOT NULL,
  baseline_json TEXT NOT NULL DEFAULT '{}',
  test_json TEXT NOT NULL DEFAULT '{}',
  falsifier_json TEXT NOT NULL DEFAULT '{}',
  shadow_json TEXT NOT NULL DEFAULT '{}',
  promotion_receipt TEXT
);

CREATE TABLE IF NOT EXISTS bridge_message(
  message_id TEXT PRIMARY KEY,
  direction TEXT NOT NULL CHECK(direction IN('IN','OUT')),
  sender TEXT NOT NULL,
  recipient TEXT NOT NULL,
  kind TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  consumed_at TEXT,
  correlation_id TEXT
);

CREATE TABLE IF NOT EXISTS reentry_snapshot(
  snapshot_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  human_context_json TEXT NOT NULL,
  source_heads_json TEXT NOT NULL,
  host_state_json TEXT NOT NULL,
  open_conflicts_json TEXT NOT NULL,
  open_tasks_json TEXT NOT NULL,
  state_digest TEXT NOT NULL
);

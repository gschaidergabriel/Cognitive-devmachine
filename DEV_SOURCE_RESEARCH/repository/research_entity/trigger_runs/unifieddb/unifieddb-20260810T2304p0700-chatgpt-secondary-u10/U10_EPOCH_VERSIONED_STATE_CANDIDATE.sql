-- Candidate U10: additive, reversible epoch-versioned authoritative state layer.
-- Status: CANDIDATE_NOT_PROMOTED. Do not replace current tables until target-VPS replay/recovery gates pass.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS u10_tx_commits(
  tx_id TEXT PRIMARY KEY REFERENCES semantic_transactions(tx_id) ON DELETE CASCADE,
  committed_epoch INTEGER NOT NULL UNIQUE REFERENCES state_epochs(epoch),
  execution_id TEXT,
  lease_epoch INTEGER,
  commit_root_hash TEXT NOT NULL,
  committed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS u10_record_versions(
  record_kind TEXT NOT NULL,
  record_key TEXT NOT NULL,
  scope TEXT NOT NULL,
  version_epoch INTEGER NOT NULL REFERENCES state_epochs(epoch),
  payload_clay TEXT NOT NULL,
  epistemic_class TEXT NOT NULL,
  source_ref TEXT,
  source_hash TEXT,
  valid_from TEXT,
  valid_to TEXT,
  tombstone INTEGER NOT NULL DEFAULT 0 CHECK(tombstone IN (0,1)),
  PRIMARY KEY(record_kind,record_key,scope,version_epoch)
);
CREATE INDEX IF NOT EXISTS idx_u10_record_versions_lookup
ON u10_record_versions(record_kind,record_key,scope,version_epoch DESC);

CREATE TABLE IF NOT EXISTS u10_record_heads(
  record_kind TEXT NOT NULL,
  record_key TEXT NOT NULL,
  scope TEXT NOT NULL,
  head_epoch INTEGER NOT NULL,
  PRIMARY KEY(record_kind,record_key,scope),
  FOREIGN KEY(record_kind,record_key,scope,head_epoch)
    REFERENCES u10_record_versions(record_kind,record_key,scope,version_epoch)
);

CREATE TABLE IF NOT EXISTS u10_projection_epochs(
  projection_name TEXT PRIMARY KEY,
  projection_epoch INTEGER NOT NULL,
  source_state_epoch INTEGER NOT NULL REFERENCES state_epochs(epoch),
  projection_root_hash TEXT,
  readiness TEXT NOT NULL CHECK(readiness IN ('READY','LAGGING','REBUILDING','FAILED','UNKNOWN')),
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS u10_projection_outbox(
  outbox_id TEXT PRIMARY KEY,
  source_state_epoch INTEGER NOT NULL REFERENCES state_epochs(epoch),
  projection_name TEXT NOT NULL,
  event_kind TEXT NOT NULL,
  payload_ref TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('PENDING','APPLIED','FAILED','QUARANTINED')),
  attempts INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  applied_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_u10_projection_outbox
ON u10_projection_outbox(projection_name,status,source_state_epoch);

CREATE TABLE IF NOT EXISTS u10_selection_receipts(
  selection_id TEXT PRIMARY KEY,
  query_id TEXT REFERENCES query_receipts(query_id),
  state_epoch INTEGER NOT NULL REFERENCES state_epochs(epoch),
  projection_name TEXT,
  projection_source_epoch INTEGER,
  planner_clay TEXT NOT NULL,
  candidate_refs_clay TEXT NOT NULL,
  candidate_set_hash TEXT NOT NULL,
  selected_refs_clay TEXT NOT NULL,
  selection_hash TEXT NOT NULL,
  admissibility_clay TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS u10_reentry_receipts(
  reentry_id TEXT PRIMARY KEY,
  state_epoch INTEGER NOT NULL REFERENCES state_epochs(epoch),
  episode_id TEXT NOT NULL,
  signal_id TEXT NOT NULL,
  causal_id TEXT NOT NULL,
  verified_outcome_ref TEXT NOT NULL,
  causal_credit_ref TEXT NOT NULL,
  admitted_delta_ref TEXT NOT NULL,
  receipt_hash TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS u10_recovery_checkpoints(
  checkpoint_id TEXT PRIMARY KEY,
  state_epoch INTEGER NOT NULL REFERENCES state_epochs(epoch),
  db_snapshot_ref TEXT NOT NULL,
  db_sha256 TEXT NOT NULL,
  integrity_check TEXT NOT NULL,
  foreign_key_check TEXT NOT NULL,
  restore_test_state TEXT NOT NULL CHECK(restore_test_state IN ('UNTESTED','PASS','FAIL')),
  created_at TEXT NOT NULL
);

CREATE VIEW IF NOT EXISTS v_u10_current_records AS
SELECT v.* FROM u10_record_heads h
JOIN u10_record_versions v
  ON v.record_kind=h.record_kind
 AND v.record_key=h.record_key
 AND v.scope=h.scope
 AND v.version_epoch=h.head_epoch
WHERE v.tombstone=0;

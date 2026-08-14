-- U11 PCAMF candidate: proof-carrying causal receipts + derived associative fields.
-- Additive candidate only. Promotion requires exact-source target-VPS evidence.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS u11_receipt_registry(
  receipt_id TEXT PRIMARY KEY,
  receipt_kind TEXT NOT NULL CHECK(receipt_kind IN ('GWT_USE','EFFECT_ATTEMPT','VERIFIED_OUTCOME','CAUSAL_CREDIT','ADMITTED_DELTA','REENTRY','TERMINAL_DONE','DONE_NO_LEARNING')),
  state_epoch INTEGER NOT NULL REFERENCES state_epochs(epoch),
  execution_id TEXT NOT NULL,
  lease_epoch INTEGER NOT NULL,
  payload_hash TEXT NOT NULL,
  source_ref TEXT,
  verified INTEGER NOT NULL CHECK(verified IN (0,1)),
  created_at TEXT NOT NULL,
  UNIQUE(receipt_kind, execution_id, lease_epoch, payload_hash)
);
CREATE INDEX IF NOT EXISTS idx_u11_receipt_exec ON u11_receipt_registry(execution_id,lease_epoch,state_epoch,receipt_kind);

CREATE TABLE IF NOT EXISTS u11_receipt_edges(
  child_receipt_id TEXT NOT NULL REFERENCES u11_receipt_registry(receipt_id) ON DELETE CASCADE,
  parent_receipt_id TEXT NOT NULL REFERENCES u11_receipt_registry(receipt_id),
  edge_kind TEXT NOT NULL CHECK(edge_kind IN ('USES','ATTEMPTS','VERIFIES','CREDITS','ADMITS','REENTERS','CLOSES')),
  PRIMARY KEY(child_receipt_id,parent_receipt_id,edge_kind),
  CHECK(child_receipt_id <> parent_receipt_id)
);

CREATE TABLE IF NOT EXISTS u11_terminal_receipts(
  terminal_receipt_id TEXT PRIMARY KEY REFERENCES u11_receipt_registry(receipt_id),
  execution_id TEXT NOT NULL,
  lease_epoch INTEGER NOT NULL,
  state_epoch INTEGER NOT NULL REFERENCES state_epochs(epoch),
  chain_root_hash TEXT NOT NULL,
  terminal_class TEXT NOT NULL CHECK(terminal_class IN ('DONE','DONE_NO_LEARNING')),
  closure_validator_version TEXT NOT NULL,
  closed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS u11_associative_fields(
  field_id TEXT PRIMARY KEY,
  field_kind TEXT NOT NULL CHECK(field_kind IN ('PKM','ANN','HOPFIELD','HDC_VSA','MODEL_NATIVE','OTHER')),
  source_state_epoch INTEGER NOT NULL REFERENCES state_epochs(epoch),
  build_hash TEXT NOT NULL,
  model_or_index_hash TEXT NOT NULL,
  admissibility_clay TEXT NOT NULL,
  calibration_clay TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('SHADOW','READY','LAGGING','REBUILDING','FAILED','QUARANTINED','REJECTED')),
  authoritative INTEGER NOT NULL DEFAULT 0 CHECK(authoritative=0),
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS u11_selection_proofs(
  selection_id TEXT PRIMARY KEY,
  query_id TEXT,
  field_id TEXT REFERENCES u11_associative_fields(field_id),
  state_epoch INTEGER NOT NULL REFERENCES state_epochs(epoch),
  field_source_epoch INTEGER,
  route_class TEXT NOT NULL,
  candidate_set_hash TEXT NOT NULL,
  selected_canonical_refs_clay TEXT NOT NULL,
  canonical_rebind_hash TEXT,
  rebind_status TEXT NOT NULL CHECK(rebind_status IN ('BOUND','ABSTAIN','FALLBACK','REJECTED')),
  planner_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS u11_projection_delta_outbox(
  delta_id TEXT PRIMARY KEY,
  source_state_epoch INTEGER NOT NULL REFERENCES state_epochs(epoch),
  projection_name TEXT NOT NULL,
  delta_kind TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  payload_ref TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('PENDING','APPLIED','FAILED','QUARANTINED')),
  created_at TEXT NOT NULL,
  applied_at TEXT
);

CREATE TABLE IF NOT EXISTS u11_projection_registry(
  projection_name TEXT PRIMARY KEY,
  source_state_epoch INTEGER NOT NULL REFERENCES state_epochs(epoch),
  projection_root_hash TEXT NOT NULL,
  build_hash TEXT NOT NULL,
  readiness TEXT NOT NULL CHECK(readiness IN ('READY','LAGGING','REBUILDING','FAILED','UNKNOWN')),
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS u11_authenticated_epoch_checkpoints(
  checkpoint_id TEXT PRIMARY KEY,
  state_epoch INTEGER NOT NULL REFERENCES state_epochs(epoch),
  tree_size INTEGER NOT NULL,
  merkle_root_hash TEXT NOT NULL,
  prior_checkpoint_id TEXT REFERENCES u11_authenticated_epoch_checkpoints(checkpoint_id),
  canonical_root_hash TEXT NOT NULL,
  proof_scheme TEXT NOT NULL,
  created_at TEXT NOT NULL
);

-- SQL FKs/NOT NULL do not prove full causal closure.
-- TERMINAL_DONE insertion must be mediated by a deterministic ClayCode/runtime closure validator
-- that verifies exact receipt kinds, edges, current execution_id, current lease_epoch,
-- verified outcome, admitted/no-learning path, and state epoch.

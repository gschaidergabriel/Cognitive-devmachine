-- CLAY U12 · FRANK DATABASE PULSE STATE PLANE
-- Research candidate implementing the owner-fixed FRANK Database Pulse boundary.
-- UnifiedDB remains semantic/provenance authority. Pulse state is endogenous runtime
-- bookkeeping and never mints truth or external effect authority.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS frank_database_pulse_state(
  singleton_id INTEGER PRIMARY KEY CHECK(singleton_id=1),
  entity_id TEXT NOT NULL,
  lineage_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('PULSING','PAUSED','DEGRADED','QUARANTINED','STOPPED')),
  pulse_count INTEGER NOT NULL DEFAULT 0 CHECK(pulse_count >= 0),
  state_transition_count INTEGER NOT NULL DEFAULT 0 CHECK(state_transition_count >= 0),
  entity_epoch INTEGER NOT NULL DEFAULT 0 CHECK(entity_epoch >= 0),
  last_applied_delta_seq INTEGER NOT NULL DEFAULT 0 CHECK(last_applied_delta_seq >= 0),
  source_epoch INTEGER NOT NULL DEFAULT 0 CHECK(source_epoch >= 0),
  graph_epoch INTEGER NOT NULL DEFAULT 0 CHECK(graph_epoch >= 0),
  semantic_generation_id TEXT,
  state_clay TEXT NOT NULL DEFAULT '{}',
  state_hash TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS frank_database_pulse_delta_queue(
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  delta_id TEXT NOT NULL UNIQUE,
  changed_ref TEXT NOT NULL,
  reason_class TEXT NOT NULL,
  payload_clay TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  source_epoch INTEGER NOT NULL CHECK(source_epoch >= 0),
  graph_epoch INTEGER CHECK(graph_epoch IS NULL OR graph_epoch >= 0),
  admitted_at TEXT NOT NULL,
  applied_pulse_id TEXT
);
-- The cognition hot path should touch only unapplied deltas. This deliberately mirrors
-- SQLite's supported partial-index pattern rather than indexing cold historical rows.
CREATE INDEX IF NOT EXISTS idx_frank_pulse_delta_unapplied
ON frank_database_pulse_delta_queue(seq,source_epoch,graph_epoch)
WHERE applied_pulse_id IS NULL;

CREATE TABLE IF NOT EXISTS frank_database_pulse_receipts(
  pulse_id TEXT PRIMARY KEY,
  pulse_index INTEGER NOT NULL UNIQUE CHECK(pulse_index > 0),
  pre_state_hash TEXT NOT NULL,
  post_state_hash TEXT NOT NULL,
  applied_delta_count INTEGER NOT NULL CHECK(applied_delta_count >= 0),
  backlog_after INTEGER NOT NULL CHECK(backlog_after >= 0),
  model_call_count INTEGER NOT NULL DEFAULT 0 CHECK(model_call_count >= 0),
  tool_call_count INTEGER NOT NULL DEFAULT 0 CHECK(tool_call_count >= 0),
  effect_count INTEGER NOT NULL DEFAULT 0 CHECK(effect_count >= 0),
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER NOT NULL,
  semantic_generation_id TEXT,
  receipt_clay TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_frank_pulse_receipts_index
ON frank_database_pulse_receipts(pulse_index DESC);

CREATE TABLE IF NOT EXISTS frank_database_pulse_checkpoints(
  checkpoint_id TEXT PRIMARY KEY,
  pulse_id TEXT,
  pulse_index INTEGER NOT NULL CHECK(pulse_index >= 0),
  snapshot_clay TEXT NOT NULL,
  state_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_frank_pulse_checkpoint_latest
ON frank_database_pulse_checkpoints(pulse_index DESC,created_at DESC);

CREATE VIEW IF NOT EXISTS v_frank_database_pulse_health AS
SELECT s.*,
  (SELECT COUNT(*) FROM frank_database_pulse_delta_queue q WHERE q.applied_pulse_id IS NULL) AS backlog_count,
  (SELECT MAX(pulse_index) FROM frank_database_pulse_receipts) AS latest_receipt_index
FROM frank_database_pulse_state s WHERE singleton_id=1;

-- U12 Pulse invariants:
-- 1. pulse_count, state_transition_count, model/tool/effect counts are distinct observables;
-- 2. a valid pulse MAY have model_call_count=0;
-- 3. only bounded unapplied deltas are consumed on the hot path; no global census is required;
-- 4. payload and state hashes are verified before transition; corruption fails closed;
-- 5. state mutation + delta acknowledgement + receipt + checkpoint commit atomically;
-- 6. semantic access generation is usable only when its source/graph epochs are coherent;
-- 7. stale semantic access is dropped, never silently reused as current truth;
-- 8. U10 possibility invalidations are append-only side effects inside the same transaction;
-- 9. checkpoints are last-known-good recovery candidates and must verify before restoration;
-- 10. Pulse output/state never grants external effect authority.

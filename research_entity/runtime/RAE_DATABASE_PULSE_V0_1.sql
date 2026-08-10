-- CLAY / FRANK DATABASE PULSE v0.1 CANDIDATE
-- Layers on the U10 possibility compiler. UnifiedDB remains semantic/provenance authority.
-- This schema stores only change-completeness receipts and pulse execution receipts.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS database_pulse_change_manifests(
  manifest_id TEXT PRIMARY KEY,
  parent_source_epoch INTEGER NOT NULL,
  source_epoch INTEGER NOT NULL,
  parent_graph_epoch INTEGER NOT NULL,
  graph_epoch INTEGER NOT NULL,
  changed_refs_clay TEXT NOT NULL DEFAULT '[]',
  affected_anchor_refs_clay TEXT NOT NULL DEFAULT '[]',
  complete INTEGER NOT NULL CHECK(complete IN (0,1)),
  provenance_clay TEXT NOT NULL DEFAULT '{}',
  manifest_hash TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('CANDIDATE','VERIFIED','QUARANTINED','SUPERSEDED')),
  created_at TEXT NOT NULL,
  CHECK(source_epoch >= parent_source_epoch),
  CHECK(graph_epoch >= 0 AND parent_graph_epoch >= 0)
);
CREATE INDEX IF NOT EXISTS idx_database_pulse_manifest_basis
ON database_pulse_change_manifests(
  parent_source_epoch,source_epoch,parent_graph_epoch,graph_epoch,status,complete,created_at DESC
);

CREATE TABLE IF NOT EXISTS database_pulse_cycles(
  pulse_id TEXT PRIMARY KEY,
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER NOT NULL,
  previous_field_epoch INTEGER,
  change_manifest_id TEXT,
  shadow_field_epoch INTEGER,
  state TEXT NOT NULL CHECK(state IN ('PLANNED','RUNNING','VERIFIED','PUBLISHED','NOOP','FAILED','QUARANTINED')),
  plan_class TEXT NOT NULL CHECK(plan_class IN ('NOOP','FACET_ONLY','WITNESS_REPAIR','ANCHOR_RECOMPILE','FIELD_REBUILD','FAIL_CLOSED')),
  invalidation_count INTEGER NOT NULL DEFAULT 0 CHECK(invalidation_count >= 0),
  changed_refs_clay TEXT NOT NULL DEFAULT '[]',
  affected_anchors_clay TEXT NOT NULL DEFAULT '[]',
  semantic_plan_hash TEXT NOT NULL,
  model_call_count INTEGER NOT NULL DEFAULT 0 CHECK(model_call_count >= 0),
  tool_call_count INTEGER NOT NULL DEFAULT 0 CHECK(tool_call_count >= 0),
  state_transition_count INTEGER NOT NULL DEFAULT 0 CHECK(state_transition_count >= 0),
  graph_change_count INTEGER NOT NULL DEFAULT 0 CHECK(graph_change_count >= 0),
  hypothesis_count INTEGER NOT NULL DEFAULT 0 CHECK(hypothesis_count >= 0),
  memory_update_count INTEGER NOT NULL DEFAULT 0 CHECK(memory_update_count >= 0),
  reentry_count INTEGER NOT NULL DEFAULT 0 CHECK(reentry_count >= 0),
  effect_count INTEGER NOT NULL DEFAULT 0 CHECK(effect_count >= 0),
  started_at TEXT NOT NULL,
  completed_at TEXT,
  latency_ns INTEGER,
  receipt_hash TEXT,
  evidence_clay TEXT NOT NULL DEFAULT '{}',
  FOREIGN KEY(change_manifest_id) REFERENCES database_pulse_change_manifests(manifest_id)
);
CREATE INDEX IF NOT EXISTS idx_database_pulse_cycles_basis
ON database_pulse_cycles(source_epoch,graph_epoch,started_at DESC);
CREATE INDEX IF NOT EXISTS idx_database_pulse_cycles_state
ON database_pulse_cycles(state,started_at DESC);

CREATE VIEW IF NOT EXISTS v_database_pulse_latest AS
SELECT * FROM database_pulse_cycles ORDER BY rowid DESC LIMIT 1;

-- Pulse invariants:
-- 1. DATABASE PULSE != LLM inference loop. Maintenance pulses SHOULD normally have model_call_count=0.
-- 2. Pulse output is derived context/access state, never truth or effect authority.
-- 3. A scoped cross-epoch repair requires a VERIFIED complete change manifest.
-- 4. Without a complete manifest, cross-epoch dirty work escalates to FIELD_REBUILD.
-- 5. Unexplained epoch drift with neither invalidation nor manifest fails closed.
-- 6. Shadow possibility fields remain BUILDING until verification succeeds.
-- 7. Publication is compare-and-swap against previous_field_epoch; a moved head quarantines the stale shadow.
-- 8. Empty/broken shadows never replace last-known-good CURRENT state.
-- 9. Invalidation rows become DONE only after successful publication.
-- 10. Pulse semantic receipt hashes exclude wall-clock latency so matched replays remain comparable.

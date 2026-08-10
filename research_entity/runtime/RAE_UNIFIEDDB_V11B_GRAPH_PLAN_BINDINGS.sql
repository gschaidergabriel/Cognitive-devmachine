-- CLAY U11B CANDIDATE · GRAPH PLAN BINDINGS
-- Durable provenance bridge between a coherent UnifiedDB semantic-access generation
-- and the exact ClayGraph V4 plans/verification receipts that authorized its path set.
-- No binding grants truth/effect authority; it only makes the derivation gate replayable.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS semantic_access_generation_plan_bindings(
  generation_id TEXT NOT NULL REFERENCES semantic_access_generations(generation_id) ON DELETE CASCADE,
  plan_id TEXT NOT NULL,
  verification_receipt_id TEXT NOT NULL,
  plan_paths_hash TEXT NOT NULL,
  seed_id TEXT NOT NULL,
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER NOT NULL,
  topology_hash TEXT NOT NULL,
  bound_at TEXT NOT NULL,
  PRIMARY KEY(generation_id,plan_id)
);

CREATE INDEX IF NOT EXISTS idx_semantic_access_generation_plan_binding_plan
ON semantic_access_generation_plan_bindings(plan_id,generation_id);

CREATE INDEX IF NOT EXISTS idx_semantic_access_generation_plan_binding_epoch
ON semantic_access_generation_plan_bindings(source_epoch,graph_epoch,generation_id);

-- Integrated admission law when ClayGraph V4 is present:
-- * every U11 generation path is covered by a bound VERIFIED plan for the same seed;
-- * ONLY the newest verification receipt for a plan is admissible, and it must pass with
--   zero invalid/stale/missing-counterevidence counts;
-- * a deterministic hash of the complete stored plan-path rows is bound at stage time and
--   rechecked at verify/publish so post-receipt path mutation cannot inherit old verification;
-- * plan/source/graph epochs and topology hash match the receipt and current graph epoch;
-- * stage/verify/publish own the write-serialization boundary and revalidate before mutation/publish;
-- * stale bindings quarantine the candidate generation;
-- * last-known-good semantic_access_head is never replaced by a stale generation.

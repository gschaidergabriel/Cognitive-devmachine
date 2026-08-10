-- CLAY U11B CANDIDATE · GRAPH PLAN BINDINGS
-- Durable provenance bridge between a coherent UnifiedDB semantic-access generation
-- and the ClayGraph V4 plans/verification receipts that authorized its path set.
-- No binding grants truth/effect authority; it only makes the derivation gate replayable.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS semantic_access_generation_plan_bindings(
  generation_id TEXT NOT NULL REFERENCES semantic_access_generations(generation_id) ON DELETE CASCADE,
  plan_id TEXT NOT NULL,
  verification_receipt_id TEXT NOT NULL,
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

-- Admission law when ClayGraph V4 is present:
-- * every U11 generation path must be covered by a bound VERIFIED plan for the same seed;
-- * every bound plan must have a passed verification receipt with zero invalid/stale/missing-counterevidence counts;
-- * plan/source/graph epochs and topology hash must match the receipt and current graph epoch;
-- * verify and publish re-check the bindings; stale bindings quarantine the generation;
-- * last-known-good semantic_access_head is never replaced by a stale generation.

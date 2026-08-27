-- CLAY U13 · CYCLE-PINNED FLAT SEMANTIC ACCESS
-- Candidate layered on U10/U11. One Clay/Frank cycle pins one immutable verified generation;
-- hot reads then avoid rechecking the mutable head on every lookup.
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS semantic_access_flat_v13(
  generation_id TEXT NOT NULL REFERENCES semantic_access_generations(generation_id) ON DELETE CASCADE,
  normalized_key TEXT NOT NULL,
  target_record_id TEXT NOT NULL,
  target_logical_id TEXT NOT NULL,
  path_rank INTEGER NOT NULL CHECK(path_rank>0),
  path_weight REAL NOT NULL,
  authority_rank REAL NOT NULL,
  path_clay TEXT NOT NULL,
  PRIMARY KEY(generation_id,normalized_key,path_rank,target_record_id)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_semantic_access_flat_target_v13
ON semantic_access_flat_v13(generation_id,target_logical_id,normalized_key);

CREATE TABLE IF NOT EXISTS semantic_access_cycle_pins(
  cycle_id TEXT PRIMARY KEY,
  generation_id TEXT NOT NULL REFERENCES semantic_access_generations(generation_id),
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER NOT NULL,
  derivation_hash TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('PINNED','RELEASED','ABORTED')),
  pinned_at TEXT NOT NULL,
  released_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_semantic_access_cycle_generation_v13
ON semantic_access_cycle_pins(generation_id,status,pinned_at);

-- Snapshot law:
-- * pin only a CURRENT verified head with exact requested source/graph epochs.
-- * within a cycle the generation is immutable; a concurrent head swap becomes visible only
--   to the next pin. This gives replayable snapshot semantics and removes per-query head joins.
-- * cycle pin is context/retrieval authority only, never effect authority.

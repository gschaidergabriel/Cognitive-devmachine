-- CLAY U12 · SEGMENTED SEMANTIC ACCESS PULSE GENERATIONS
-- CANDIDATE ONLY.
--
-- UnifiedDB/StateLedger remains semantic/truth authority. These tables are disposable,
-- rebuildable access projections. ClayGraph activation/path rank never mints truth,
-- evidence status or effect authority.
--
-- U12 addresses U11 full-generation write amplification by making each seed's access
-- neighborhood an immutable content-addressed segment. A coherent generation is a small
-- seed->segment map. Local, impact-complete pulses create segments only for affected seeds,
-- reuse unaffected segments, verify the complete generation map, and atomically flip one
-- head. Unknown/broad topology changes must fall back to a full rebuild.

PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS access_segment(
  segment_id TEXT PRIMARY KEY,
  seed_id TEXT NOT NULL,
  segment_hash TEXT NOT NULL,
  path_count INTEGER NOT NULL CHECK(path_count > 0),
  created_ns INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_access_segment_seed
ON access_segment(seed_id,created_ns DESC);

CREATE TABLE IF NOT EXISTS access_segment_path(
  segment_id TEXT NOT NULL REFERENCES access_segment(segment_id) ON DELETE CASCADE,
  target_record_id TEXT NOT NULL,
  target_logical_id TEXT NOT NULL,
  path_rank INTEGER NOT NULL CHECK(path_rank > 0),
  hop_count INTEGER NOT NULL CHECK(hop_count >= 0),
  path_weight REAL NOT NULL,
  authority_rank REAL NOT NULL,
  path_clay TEXT NOT NULL,
  PRIMARY KEY(segment_id,target_record_id)
);
CREATE INDEX IF NOT EXISTS idx_access_segment_path_rank
ON access_segment_path(segment_id,path_rank,path_weight DESC,authority_rank DESC,target_record_id);

-- Reverse dependency index is the safety-critical pulse selector. It must contain every
-- logical identity whose change can invalidate the segment. Incomplete closure is not
-- permission to guess: caller must mark impact_complete=false and force full rebuild.
CREATE TABLE IF NOT EXISTS access_segment_dependency(
  segment_id TEXT NOT NULL REFERENCES access_segment(segment_id) ON DELETE CASCADE,
  dependency_logical_id TEXT NOT NULL,
  PRIMARY KEY(segment_id,dependency_logical_id)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_access_segment_dependency_reverse
ON access_segment_dependency(dependency_logical_id,segment_id);

CREATE TABLE IF NOT EXISTS access_generation(
  generation_id TEXT PRIMARY KEY,
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER NOT NULL,
  generation_hash TEXT NOT NULL,
  seed_count INTEGER NOT NULL CHECK(seed_count > 0),
  status TEXT NOT NULL CHECK(status IN('STAGING','VERIFIED','CURRENT','SUPERSEDED','QUARANTINED')),
  created_ns INTEGER NOT NULL,
  published_ns INTEGER
);
CREATE INDEX IF NOT EXISTS idx_access_generation_epoch
ON access_generation(source_epoch,graph_epoch,status,created_ns DESC);

CREATE TABLE IF NOT EXISTS access_generation_seed(
  generation_id TEXT NOT NULL REFERENCES access_generation(generation_id) ON DELETE CASCADE,
  seed_id TEXT NOT NULL,
  segment_id TEXT NOT NULL REFERENCES access_segment(segment_id),
  PRIMARY KEY(generation_id,seed_id)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_access_generation_segment
ON access_generation_seed(generation_id,segment_id);

CREATE TABLE IF NOT EXISTS access_head(
  head_key TEXT PRIMARY KEY CHECK(head_key='CURRENT'),
  generation_id TEXT NOT NULL REFERENCES access_generation(generation_id),
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER NOT NULL,
  generation_hash TEXT NOT NULL,
  published_ns INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS access_pulse_receipt(
  event_id TEXT PRIMARY KEY,
  generation_id TEXT NOT NULL REFERENCES access_generation(generation_id),
  receipt_json TEXT NOT NULL,
  created_ns INTEGER NOT NULL
);

-- U12 publication / recovery law:
-- 1. Build new immutable segments only after dependency closure is declared complete.
-- 2. If impact is incomplete, change expands unknown topology, or affected fraction exceeds
--    the measured threshold, execute FULL_FALLBACK.
-- 3. Create STAGING generation + complete seed->segment map.
-- 4. Verify map count, seed/segment identity, non-empty segment paths and generation hash.
-- 5. In ONE transaction: VERIFIED -> supersede old CURRENT -> new CURRENT -> flip access_head.
-- 6. Any exception rolls back the whole transaction; last-known-good head remains current.
-- 7. Generation hash commits to the full seed->immutable-segment map. Deep path replay/hash
--    remains a slower audit/benchmark, not a mandatory per-pulse global scan.
-- 8. Segments/generations are derived. GC may remove unreferenced SUPERSEDED material only
--    after replay/rollback retention policy allows it.

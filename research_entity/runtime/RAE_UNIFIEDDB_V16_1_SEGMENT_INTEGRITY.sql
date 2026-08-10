-- CLAY UNIFIEDDB V16.1 · SEGMENT INTEGRITY GUARD
-- Extension over the V16 segmented Pulse-maintenance candidate (historical runtime filenames
-- still contain v12). UnifiedDB/StateLedger remains semantic truth authority.
--
-- Problem closed here: V16 segment IDs are content-addressed, but SQLite rows backing an already
-- published segment can still be mutated after creation. In particular, deleting a reverse
-- dependency can hide a future impact. V16.1 records the original complete segment manifest and
-- marks the projection DIRTY on any mutation of a segment used by the CURRENT generation.
-- Reads then fail closed; the next maintenance pulse must full-rebuild before CLEAN is restored.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS access_segment_manifest_v16_1(
  segment_id TEXT PRIMARY KEY REFERENCES access_segment(segment_id) ON DELETE CASCADE,
  manifest_json TEXT NOT NULL,
  manifest_hash TEXT NOT NULL,
  created_ns INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS access_projection_integrity_v16_1(
  singleton_id INTEGER PRIMARY KEY CHECK(singleton_id=1),
  status TEXT NOT NULL CHECK(status IN ('CLEAN','DIRTY')),
  dirty_segment_id TEXT,
  dirty_reason TEXT,
  mutation_count INTEGER NOT NULL DEFAULT 0 CHECK(mutation_count>=0),
  updated_ns INTEGER NOT NULL
);
INSERT OR IGNORE INTO access_projection_integrity_v16_1
VALUES(1,'CLEAN',NULL,NULL,0,0);

CREATE TABLE IF NOT EXISTS access_integrity_repair_receipt_v16_1(
  event_id TEXT PRIMARY KEY,
  dirty_segment_id TEXT,
  dirty_reason TEXT,
  repaired_generation_id TEXT NOT NULL,
  repair_mode TEXT NOT NULL CHECK(repair_mode='FULL_FALLBACK'),
  receipt_json TEXT NOT NULL,
  created_ns INTEGER NOT NULL
);

-- A newly-created immutable segment is populated before it is referenced by CURRENT, so those
-- legitimate INSERTs do not trip the guard. Mutations after publication do.
CREATE TRIGGER IF NOT EXISTS trg_v16_1_path_insert_dirty
AFTER INSERT ON access_segment_path
WHEN EXISTS(
  SELECT 1 FROM access_head h JOIN access_generation_seed gs ON gs.generation_id=h.generation_id
  WHERE h.head_key='CURRENT' AND gs.segment_id=NEW.segment_id
)
BEGIN
  UPDATE access_projection_integrity_v16_1
  SET status='DIRTY',dirty_segment_id=NEW.segment_id,dirty_reason='PATH_INSERT_AFTER_PUBLISH',
      mutation_count=mutation_count+1,updated_ns=CAST(strftime('%s','now') AS INTEGER)*1000000000
  WHERE singleton_id=1;
END;

CREATE TRIGGER IF NOT EXISTS trg_v16_1_path_update_dirty
AFTER UPDATE ON access_segment_path
WHEN EXISTS(
  SELECT 1 FROM access_head h JOIN access_generation_seed gs ON gs.generation_id=h.generation_id
  WHERE h.head_key='CURRENT' AND gs.segment_id=NEW.segment_id
)
BEGIN
  UPDATE access_projection_integrity_v16_1
  SET status='DIRTY',dirty_segment_id=NEW.segment_id,dirty_reason='PATH_UPDATE_AFTER_PUBLISH',
      mutation_count=mutation_count+1,updated_ns=CAST(strftime('%s','now') AS INTEGER)*1000000000
  WHERE singleton_id=1;
END;

CREATE TRIGGER IF NOT EXISTS trg_v16_1_path_delete_dirty
AFTER DELETE ON access_segment_path
WHEN EXISTS(
  SELECT 1 FROM access_head h JOIN access_generation_seed gs ON gs.generation_id=h.generation_id
  WHERE h.head_key='CURRENT' AND gs.segment_id=OLD.segment_id
)
BEGIN
  UPDATE access_projection_integrity_v16_1
  SET status='DIRTY',dirty_segment_id=OLD.segment_id,dirty_reason='PATH_DELETE_AFTER_PUBLISH',
      mutation_count=mutation_count+1,updated_ns=CAST(strftime('%s','now') AS INTEGER)*1000000000
  WHERE singleton_id=1;
END;

CREATE TRIGGER IF NOT EXISTS trg_v16_1_dependency_insert_dirty
AFTER INSERT ON access_segment_dependency
WHEN EXISTS(
  SELECT 1 FROM access_head h JOIN access_generation_seed gs ON gs.generation_id=h.generation_id
  WHERE h.head_key='CURRENT' AND gs.segment_id=NEW.segment_id
)
BEGIN
  UPDATE access_projection_integrity_v16_1
  SET status='DIRTY',dirty_segment_id=NEW.segment_id,dirty_reason='DEPENDENCY_INSERT_AFTER_PUBLISH',
      mutation_count=mutation_count+1,updated_ns=CAST(strftime('%s','now') AS INTEGER)*1000000000
  WHERE singleton_id=1;
END;

CREATE TRIGGER IF NOT EXISTS trg_v16_1_dependency_update_dirty
AFTER UPDATE ON access_segment_dependency
WHEN EXISTS(
  SELECT 1 FROM access_head h JOIN access_generation_seed gs ON gs.generation_id=h.generation_id
  WHERE h.head_key='CURRENT' AND gs.segment_id=NEW.segment_id
)
BEGIN
  UPDATE access_projection_integrity_v16_1
  SET status='DIRTY',dirty_segment_id=NEW.segment_id,dirty_reason='DEPENDENCY_UPDATE_AFTER_PUBLISH',
      mutation_count=mutation_count+1,updated_ns=CAST(strftime('%s','now') AS INTEGER)*1000000000
  WHERE singleton_id=1;
END;

CREATE TRIGGER IF NOT EXISTS trg_v16_1_dependency_delete_dirty
AFTER DELETE ON access_segment_dependency
WHEN EXISTS(
  SELECT 1 FROM access_head h JOIN access_generation_seed gs ON gs.generation_id=h.generation_id
  WHERE h.head_key='CURRENT' AND gs.segment_id=OLD.segment_id
)
BEGIN
  UPDATE access_projection_integrity_v16_1
  SET status='DIRTY',dirty_segment_id=OLD.segment_id,dirty_reason='DEPENDENCY_DELETE_AFTER_PUBLISH',
      mutation_count=mutation_count+1,updated_ns=CAST(strftime('%s','now') AS INTEGER)*1000000000
  WHERE singleton_id=1;
END;

CREATE TRIGGER IF NOT EXISTS trg_v16_1_segment_update_dirty
AFTER UPDATE ON access_segment
WHEN EXISTS(
  SELECT 1 FROM access_head h JOIN access_generation_seed gs ON gs.generation_id=h.generation_id
  WHERE h.head_key='CURRENT' AND gs.segment_id=NEW.segment_id
)
BEGIN
  UPDATE access_projection_integrity_v16_1
  SET status='DIRTY',dirty_segment_id=NEW.segment_id,dirty_reason='SEGMENT_HEADER_UPDATE_AFTER_PUBLISH',
      mutation_count=mutation_count+1,updated_ns=CAST(strftime('%s','now') AS INTEGER)*1000000000
  WHERE singleton_id=1;
END;

CREATE TRIGGER IF NOT EXISTS trg_v16_1_generation_map_update_dirty
AFTER UPDATE ON access_generation_seed
WHEN EXISTS(
  SELECT 1 FROM access_head h WHERE h.head_key='CURRENT' AND h.generation_id=NEW.generation_id
)
BEGIN
  UPDATE access_projection_integrity_v16_1
  SET status='DIRTY',dirty_segment_id=NEW.segment_id,dirty_reason='CURRENT_GENERATION_MAP_UPDATE',
      mutation_count=mutation_count+1,updated_ns=CAST(strftime('%s','now') AS INTEGER)*1000000000
  WHERE singleton_id=1;
END;

CREATE TRIGGER IF NOT EXISTS trg_v16_1_generation_map_delete_dirty
AFTER DELETE ON access_generation_seed
WHEN EXISTS(
  SELECT 1 FROM access_head h WHERE h.head_key='CURRENT' AND h.generation_id=OLD.generation_id
)
BEGIN
  UPDATE access_projection_integrity_v16_1
  SET status='DIRTY',dirty_segment_id=OLD.segment_id,dirty_reason='CURRENT_GENERATION_MAP_DELETE',
      mutation_count=mutation_count+1,updated_ns=CAST(strftime('%s','now') AS INTEGER)*1000000000
  WHERE singleton_id=1;
END;

-- V16.1 laws:
-- 1. Manifest hash must equal the original V16 content hash.
-- 2. Query of a DIRTY projection fails closed before returning ranked paths.
-- 3. Incremental maintenance is forbidden while DIRTY; only a verified FULL_FALLBACK may CLEAN it.
-- 4. Existing segments are reused only after manifest/path/dependency verification.
-- 5. Corrupt content-address collisions are repaired into a new physical segment identity while
--    retaining the same semantic manifest hash; the corrupt referenced segment is never reused.
-- 6. Integrity status is projection health only; it never grants semantic truth/effect authority.

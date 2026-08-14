-- CLAY UNIFIEDDB · SPM-S1 INTEGRITY TRIPWIRE
-- Additive fail-closed health layer for UNIFIEDDB_SEGMENTED_PULSE_MAINTENANCE_S1.
-- UnifiedDB/StateLedger remains semantic truth authority; this is projection health only.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS spm_s1_integrity_state(
  singleton_id INTEGER PRIMARY KEY CHECK(singleton_id=1),
  status TEXT NOT NULL CHECK(status IN ('CLEAN','DIRTY')),
  dirty_segment_id TEXT,
  dirty_reason TEXT,
  mutation_count INTEGER NOT NULL DEFAULT 0 CHECK(mutation_count>=0),
  updated_ns INTEGER NOT NULL
);
INSERT OR IGNORE INTO spm_s1_integrity_state VALUES(1,'CLEAN',NULL,NULL,0,0);

CREATE TABLE IF NOT EXISTS spm_s1_integrity_repair_receipt(
  event_id TEXT PRIMARY KEY,
  dirty_segment_id TEXT,
  dirty_reason TEXT,
  repaired_generation_id TEXT NOT NULL,
  repair_mode TEXT NOT NULL CHECK(repair_mode='FULL_FALLBACK'),
  audit_json TEXT NOT NULL,
  created_ns INTEGER NOT NULL
);

-- Legitimate SPM-S1 segment construction happens before the new segment is in access_head's
-- CURRENT generation. Therefore INSERT triggers below stay quiet during normal copy-on-write
-- publication and fire only for post-publication mutation of CURRENT material.
CREATE TRIGGER IF NOT EXISTS trg_spm_s1_path_insert_dirty
AFTER INSERT ON access_segment_path
WHEN EXISTS(
  SELECT 1 FROM access_head h JOIN access_generation_seed gs ON gs.generation_id=h.generation_id
  WHERE h.head_key='CURRENT' AND gs.segment_id=NEW.segment_id
)
BEGIN
  UPDATE spm_s1_integrity_state SET status='DIRTY',dirty_segment_id=NEW.segment_id,
    dirty_reason='PATH_INSERT_AFTER_PUBLISH',mutation_count=mutation_count+1,
    updated_ns=CAST(strftime('%s','now') AS INTEGER)*1000000000 WHERE singleton_id=1;
END;

CREATE TRIGGER IF NOT EXISTS trg_spm_s1_path_update_dirty
AFTER UPDATE ON access_segment_path
WHEN EXISTS(
  SELECT 1 FROM access_head h JOIN access_generation_seed gs ON gs.generation_id=h.generation_id
  WHERE h.head_key='CURRENT' AND gs.segment_id=OLD.segment_id
) OR EXISTS(
  SELECT 1 FROM access_head h JOIN access_generation_seed gs ON gs.generation_id=h.generation_id
  WHERE h.head_key='CURRENT' AND gs.segment_id=NEW.segment_id
)
BEGIN
  UPDATE spm_s1_integrity_state SET status='DIRTY',
    dirty_segment_id=CASE WHEN EXISTS(
      SELECT 1 FROM access_head h JOIN access_generation_seed gs ON gs.generation_id=h.generation_id
      WHERE h.head_key='CURRENT' AND gs.segment_id=OLD.segment_id
    ) THEN OLD.segment_id ELSE NEW.segment_id END,
    dirty_reason='PATH_UPDATE_AFTER_PUBLISH',mutation_count=mutation_count+1,
    updated_ns=CAST(strftime('%s','now') AS INTEGER)*1000000000 WHERE singleton_id=1;
END;

CREATE TRIGGER IF NOT EXISTS trg_spm_s1_path_delete_dirty
AFTER DELETE ON access_segment_path
WHEN EXISTS(
  SELECT 1 FROM access_head h JOIN access_generation_seed gs ON gs.generation_id=h.generation_id
  WHERE h.head_key='CURRENT' AND gs.segment_id=OLD.segment_id
)
BEGIN
  UPDATE spm_s1_integrity_state SET status='DIRTY',dirty_segment_id=OLD.segment_id,
    dirty_reason='PATH_DELETE_AFTER_PUBLISH',mutation_count=mutation_count+1,
    updated_ns=CAST(strftime('%s','now') AS INTEGER)*1000000000 WHERE singleton_id=1;
END;

CREATE TRIGGER IF NOT EXISTS trg_spm_s1_dependency_insert_dirty
AFTER INSERT ON access_segment_dependency
WHEN EXISTS(
  SELECT 1 FROM access_head h JOIN access_generation_seed gs ON gs.generation_id=h.generation_id
  WHERE h.head_key='CURRENT' AND gs.segment_id=NEW.segment_id
)
BEGIN
  UPDATE spm_s1_integrity_state SET status='DIRTY',dirty_segment_id=NEW.segment_id,
    dirty_reason='DEPENDENCY_INSERT_AFTER_PUBLISH',mutation_count=mutation_count+1,
    updated_ns=CAST(strftime('%s','now') AS INTEGER)*1000000000 WHERE singleton_id=1;
END;

CREATE TRIGGER IF NOT EXISTS trg_spm_s1_dependency_update_dirty
AFTER UPDATE ON access_segment_dependency
WHEN EXISTS(
  SELECT 1 FROM access_head h JOIN access_generation_seed gs ON gs.generation_id=h.generation_id
  WHERE h.head_key='CURRENT' AND gs.segment_id=OLD.segment_id
) OR EXISTS(
  SELECT 1 FROM access_head h JOIN access_generation_seed gs ON gs.generation_id=h.generation_id
  WHERE h.head_key='CURRENT' AND gs.segment_id=NEW.segment_id
)
BEGIN
  UPDATE spm_s1_integrity_state SET status='DIRTY',
    dirty_segment_id=CASE WHEN EXISTS(
      SELECT 1 FROM access_head h JOIN access_generation_seed gs ON gs.generation_id=h.generation_id
      WHERE h.head_key='CURRENT' AND gs.segment_id=OLD.segment_id
    ) THEN OLD.segment_id ELSE NEW.segment_id END,
    dirty_reason='DEPENDENCY_UPDATE_AFTER_PUBLISH',mutation_count=mutation_count+1,
    updated_ns=CAST(strftime('%s','now') AS INTEGER)*1000000000 WHERE singleton_id=1;
END;

CREATE TRIGGER IF NOT EXISTS trg_spm_s1_dependency_delete_dirty
AFTER DELETE ON access_segment_dependency
WHEN EXISTS(
  SELECT 1 FROM access_head h JOIN access_generation_seed gs ON gs.generation_id=h.generation_id
  WHERE h.head_key='CURRENT' AND gs.segment_id=OLD.segment_id
)
BEGIN
  UPDATE spm_s1_integrity_state SET status='DIRTY',dirty_segment_id=OLD.segment_id,
    dirty_reason='DEPENDENCY_DELETE_AFTER_PUBLISH',mutation_count=mutation_count+1,
    updated_ns=CAST(strftime('%s','now') AS INTEGER)*1000000000 WHERE singleton_id=1;
END;

CREATE TRIGGER IF NOT EXISTS trg_spm_s1_segment_header_update_dirty
AFTER UPDATE ON access_segment
WHEN EXISTS(
  SELECT 1 FROM access_head h JOIN access_generation_seed gs ON gs.generation_id=h.generation_id
  WHERE h.head_key='CURRENT' AND gs.segment_id=OLD.segment_id
) OR EXISTS(
  SELECT 1 FROM access_head h JOIN access_generation_seed gs ON gs.generation_id=h.generation_id
  WHERE h.head_key='CURRENT' AND gs.segment_id=NEW.segment_id
)
BEGIN
  UPDATE spm_s1_integrity_state SET status='DIRTY',
    dirty_segment_id=CASE WHEN EXISTS(
      SELECT 1 FROM access_head h JOIN access_generation_seed gs ON gs.generation_id=h.generation_id
      WHERE h.head_key='CURRENT' AND gs.segment_id=OLD.segment_id
    ) THEN OLD.segment_id ELSE NEW.segment_id END,
    dirty_reason='SEGMENT_HEADER_UPDATE_AFTER_PUBLISH',mutation_count=mutation_count+1,
    updated_ns=CAST(strftime('%s','now') AS INTEGER)*1000000000 WHERE singleton_id=1;
END;

CREATE TRIGGER IF NOT EXISTS trg_spm_s1_generation_map_insert_dirty
AFTER INSERT ON access_generation_seed
WHEN EXISTS(
  SELECT 1 FROM access_head h WHERE h.head_key='CURRENT' AND h.generation_id=NEW.generation_id
)
BEGIN
  UPDATE spm_s1_integrity_state SET status='DIRTY',dirty_segment_id=NEW.segment_id,
    dirty_reason='CURRENT_GENERATION_MAP_INSERT',mutation_count=mutation_count+1,
    updated_ns=CAST(strftime('%s','now') AS INTEGER)*1000000000 WHERE singleton_id=1;
END;

CREATE TRIGGER IF NOT EXISTS trg_spm_s1_generation_map_update_dirty
AFTER UPDATE ON access_generation_seed
WHEN EXISTS(
  SELECT 1 FROM access_head h WHERE h.head_key='CURRENT' AND h.generation_id=OLD.generation_id
) OR EXISTS(
  SELECT 1 FROM access_head h WHERE h.head_key='CURRENT' AND h.generation_id=NEW.generation_id
)
BEGIN
  UPDATE spm_s1_integrity_state SET status='DIRTY',
    dirty_segment_id=CASE WHEN EXISTS(
      SELECT 1 FROM access_head h WHERE h.head_key='CURRENT' AND h.generation_id=OLD.generation_id
    ) THEN OLD.segment_id ELSE NEW.segment_id END,
    dirty_reason='CURRENT_GENERATION_MAP_UPDATE',mutation_count=mutation_count+1,
    updated_ns=CAST(strftime('%s','now') AS INTEGER)*1000000000 WHERE singleton_id=1;
END;

CREATE TRIGGER IF NOT EXISTS trg_spm_s1_generation_map_delete_dirty
AFTER DELETE ON access_generation_seed
WHEN EXISTS(
  SELECT 1 FROM access_head h WHERE h.head_key='CURRENT' AND h.generation_id=OLD.generation_id
)
BEGIN
  UPDATE spm_s1_integrity_state SET status='DIRTY',dirty_segment_id=OLD.segment_id,
    dirty_reason='CURRENT_GENERATION_MAP_DELETE',mutation_count=mutation_count+1,
    updated_ns=CAST(strftime('%s','now') AS INTEGER)*1000000000 WHERE singleton_id=1;
END;

-- Operational law:
-- CLEAN + impact-complete bounded change -> normal SPM-S1 incremental path.
-- Any post-publication CURRENT mutation -> DIRTY in the same SQLite transaction.
-- UPDATE guards observe both OLD and NEW membership so key moves away from CURRENT cannot evade.
-- DIRTY -> no model-facing access read; incremental maintenance forbidden.
-- Recovery -> authoritative full recompute, restore hash-consistent segment rows, publish
-- FULL_FALLBACK, run SPM-S1 deep audit, write repair receipt, then and only then CLEAN.

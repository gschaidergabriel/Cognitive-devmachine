-- MINIUNIFIEDDB_COGNITION_SCHEMA/v1
-- Append-only cognition-object and binding layer inside the SAME MiniUnifiedDB.
-- This schema never grants semantic truth or real-effect authority.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS cognition_objects(
  object_digest TEXT PRIMARY KEY
    CHECK(length(object_digest)=64 AND object_digest NOT GLOB '*[^0-9a-f]*'),
  object_kind TEXT NOT NULL CHECK(length(object_kind) BETWEEN 1 AND 96),
  schema_version TEXT NOT NULL CHECK(length(schema_version) BETWEEN 1 AND 96),
  object_json TEXT NOT NULL,
  object_sha256 TEXT NOT NULL
    CHECK(length(object_sha256)=64 AND object_sha256 NOT GLOB '*[^0-9a-f]*'),
  provenance_json TEXT NOT NULL,
  provenance_sha256 TEXT NOT NULL
    CHECK(length(provenance_sha256)=64 AND provenance_sha256 NOT GLOB '*[^0-9a-f]*'),
  created_generation INTEGER NOT NULL CHECK(created_generation >= 0),
  created_causal_id TEXT NOT NULL CHECK(length(created_causal_id) BETWEEN 1 AND 256),
  created_at TEXT NOT NULL CHECK(length(created_at) BETWEEN 1 AND 64),
  truth_authority INTEGER NOT NULL DEFAULT 0 CHECK(truth_authority = 0),
  effect_authority INTEGER NOT NULL DEFAULT 0 CHECK(effect_authority = 0),
  CHECK(object_digest = object_sha256)
);

CREATE TABLE IF NOT EXISTS cognition_bindings(
  binding_name TEXT NOT NULL CHECK(length(binding_name) BETWEEN 1 AND 192),
  entity_generation INTEGER NOT NULL CHECK(entity_generation >= 0),
  object_digest TEXT NOT NULL,
  semantic_class TEXT NOT NULL CHECK(length(semantic_class) BETWEEN 1 AND 96),
  causal_id TEXT NOT NULL CHECK(length(causal_id) BETWEEN 1 AND 256),
  workspace_digest TEXT
    CHECK(workspace_digest IS NULL OR
          (length(workspace_digest)=64 AND workspace_digest NOT GLOB '*[^0-9a-f]*')),
  profile_id TEXT,
  profile_sha256 TEXT
    CHECK(profile_sha256 IS NULL OR
          (length(profile_sha256)=64 AND profile_sha256 NOT GLOB '*[^0-9a-f]*')),
  receipt_digest TEXT NOT NULL
    CHECK(length(receipt_digest)=64 AND receipt_digest NOT GLOB '*[^0-9a-f]*'),
  status TEXT NOT NULL
    CHECK(status IN ('ACTIVE','CANDIDATE','MEASURED','ABSTAINED','RETIRED')),
  bound_at TEXT NOT NULL CHECK(length(bound_at) BETWEEN 1 AND 64),
  truth_authority INTEGER NOT NULL DEFAULT 0 CHECK(truth_authority = 0),
  effect_authority INTEGER NOT NULL DEFAULT 0 CHECK(effect_authority = 0),
  PRIMARY KEY(binding_name, entity_generation),
  FOREIGN KEY(object_digest) REFERENCES cognition_objects(object_digest) ON DELETE RESTRICT,
  CHECK((profile_id IS NULL AND profile_sha256 IS NULL) OR
        (profile_id IS NOT NULL AND profile_sha256 IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS cognition_objects_kind_generation_idx
  ON cognition_objects(object_kind, created_generation);
CREATE INDEX IF NOT EXISTS cognition_bindings_object_idx
  ON cognition_bindings(object_digest);
CREATE INDEX IF NOT EXISTS cognition_bindings_generation_idx
  ON cognition_bindings(entity_generation, binding_name);

CREATE TRIGGER IF NOT EXISTS cognition_objects_live_generation_insert
BEFORE INSERT ON cognition_objects
BEGIN
  SELECT CASE
    WHEN COALESCE((SELECT generation FROM entity_state WHERE id=1), -1) < 0
      THEN RAISE(ABORT, 'COGNITION_ENTITY_STATE_MISSING')
    WHEN NEW.created_generation > (SELECT generation FROM entity_state WHERE id=1)
      THEN RAISE(ABORT, 'COGNITION_OBJECT_FUTURE_GENERATION')
  END;
END;

CREATE TRIGGER IF NOT EXISTS cognition_objects_immutable_update
BEFORE UPDATE ON cognition_objects
BEGIN
  SELECT RAISE(ABORT, 'COGNITION_OBJECT_IMMUTABLE');
END;

CREATE TRIGGER IF NOT EXISTS cognition_objects_immutable_delete
BEFORE DELETE ON cognition_objects
BEGIN
  SELECT RAISE(ABORT, 'COGNITION_OBJECT_IMMUTABLE');
END;

CREATE TRIGGER IF NOT EXISTS cognition_bindings_live_generation_insert
BEFORE INSERT ON cognition_bindings
BEGIN
  SELECT CASE
    WHEN COALESCE((SELECT generation FROM entity_state WHERE id=1), -1) < 0
      THEN RAISE(ABORT, 'COGNITION_ENTITY_STATE_MISSING')
    WHEN NEW.entity_generation != (SELECT generation FROM entity_state WHERE id=1)
      THEN RAISE(ABORT, 'COGNITION_BINDING_STALE_GENERATION')
    WHEN COALESCE((SELECT created_generation FROM cognition_objects
                   WHERE object_digest=NEW.object_digest), -1) < 0
      THEN RAISE(ABORT, 'COGNITION_OBJECT_MISSING')
    WHEN (SELECT created_generation FROM cognition_objects
          WHERE object_digest=NEW.object_digest) > NEW.entity_generation
      THEN RAISE(ABORT, 'COGNITION_OBJECT_FROM_FUTURE')
  END;
END;

CREATE TRIGGER IF NOT EXISTS cognition_bindings_append_only_update
BEFORE UPDATE ON cognition_bindings
BEGIN
  SELECT RAISE(ABORT, 'COGNITION_BINDING_APPEND_ONLY');
END;

CREATE TRIGGER IF NOT EXISTS cognition_bindings_append_only_delete
BEFORE DELETE ON cognition_bindings
BEGIN
  SELECT RAISE(ABORT, 'COGNITION_BINDING_APPEND_ONLY');
END;

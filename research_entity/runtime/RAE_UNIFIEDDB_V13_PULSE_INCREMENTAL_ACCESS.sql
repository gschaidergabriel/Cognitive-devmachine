-- CLAY U13 · PULSE-CERTIFIED INCREMENTAL SEMANTIC ACCESS
-- Candidate layered on U10 semantic seeds + U11 immutable generation paths + U12 Database Pulse.
-- Goal: avoid invalidating/rebuilding every semantic-access path merely because an unrelated
-- UnifiedDB source epoch advanced. UnifiedDB remains truth authority; U13 remains disposable.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS semantic_access_seed_dependencies_v13(
  generation_id TEXT NOT NULL REFERENCES semantic_access_generations(generation_id) ON DELETE CASCADE,
  seed_id TEXT NOT NULL,
  dependency_ref TEXT NOT NULL,
  dependency_kind TEXT NOT NULL,
  dependency_version_hash TEXT,
  proof_eligible INTEGER NOT NULL DEFAULT 0 CHECK(proof_eligible IN (0,1)),
  PRIMARY KEY(generation_id,seed_id,dependency_ref)
);
CREATE INDEX IF NOT EXISTS idx_semantic_access_seed_dep_v13_ref
ON semantic_access_seed_dependencies_v13(dependency_ref,seed_id,generation_id);

CREATE TABLE IF NOT EXISTS semantic_access_seed_heads_v13(
  seed_id TEXT PRIMARY KEY,
  generation_id TEXT NOT NULL REFERENCES semantic_access_generations(generation_id),
  dependency_capture TEXT NOT NULL CHECK(dependency_capture IN ('COMPLETE','PARTIAL')),
  status TEXT NOT NULL CHECK(status IN ('CURRENT','STALE','QUARANTINED')),
  installed_source_epoch INTEGER NOT NULL,
  installed_graph_epoch INTEGER NOT NULL,
  installed_by_pulse_id TEXT,
  invalidated_by_pulse_id TEXT,
  invalidated_delta_id TEXT,
  head_hash TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_semantic_access_seed_heads_v13_status
ON semantic_access_seed_heads_v13(status,seed_id);

CREATE TABLE IF NOT EXISTS semantic_access_seed_invalidations_v13(
  invalidation_id TEXT PRIMARY KEY,
  pulse_id TEXT NOT NULL,
  delta_id TEXT NOT NULL,
  changed_ref TEXT NOT NULL,
  reason_class TEXT NOT NULL,
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER,
  seed_id TEXT NOT NULL,
  previous_generation_id TEXT NOT NULL,
  invalidation_class TEXT NOT NULL CHECK(invalidation_class IN ('EXACT_DEPENDENCY','PARTIAL_CAPTURE','GLOBAL_BARRIER')),
  delta_admitted_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_semantic_access_seed_invalid_v13_seed
ON semantic_access_seed_invalidations_v13(seed_id,source_epoch DESC,graph_epoch DESC);

CREATE TABLE IF NOT EXISTS semantic_access_seed_promotions_v13(
  promotion_id TEXT PRIMARY KEY,
  seed_id TEXT NOT NULL,
  generation_id TEXT NOT NULL,
  pulse_id TEXT,
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER NOT NULL,
  dependency_capture TEXT NOT NULL,
  head_hash TEXT NOT NULL,
  receipt_clay TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_semantic_access_seed_promotions_v13_seed
ON semantic_access_seed_promotions_v13(seed_id,source_epoch DESC,graph_epoch DESC);

-- The existing U12 Pulse marks each admitted delta applied inside the SAME transaction as the
-- state/receipt/checkpoint. This trigger therefore invalidates affected U13 read heads atomically.
-- Global barriers can be encoded either by typed changed_ref prefixes or by reason_class, so a
-- malformed/non-canonical ref cannot accidentally preserve a semantically stale head.
CREATE TRIGGER IF NOT EXISTS trg_pulse_invalidate_semantic_access_v13
AFTER UPDATE OF applied_pulse_id ON frank_database_pulse_delta_queue
WHEN OLD.applied_pulse_id IS NULL AND NEW.applied_pulse_id IS NOT NULL
BEGIN
  INSERT OR IGNORE INTO semantic_access_seed_invalidations_v13(
    invalidation_id,pulse_id,delta_id,changed_ref,reason_class,source_epoch,graph_epoch,
    seed_id,previous_generation_id,invalidation_class,delta_admitted_at
  )
  SELECT
    'u13:' || NEW.delta_id || ':' || h.seed_id,
    NEW.applied_pulse_id,NEW.delta_id,NEW.changed_ref,NEW.reason_class,NEW.source_epoch,NEW.graph_epoch,
    h.seed_id,h.generation_id,
    CASE
      WHEN NEW.changed_ref GLOB 'GLOBAL:*' OR NEW.changed_ref GLOB 'POLICY:*'
        OR NEW.changed_ref GLOB 'COMPILER:*' OR NEW.changed_ref GLOB 'GRAPH_SCHEMA:*'
        OR NEW.changed_ref GLOB 'AUTHORITY_SCHEMA:*'
        OR UPPER(NEW.reason_class) IN (
          'GLOBAL_BARRIER','POLICY_CHANGE','COMPILER_CHANGE','GRAPH_SCHEMA_CHANGE',
          'AUTHORITY_SCHEMA_CHANGE','DERIVATION_CHANGE'
        ) THEN 'GLOBAL_BARRIER'
      WHEN h.dependency_capture='PARTIAL' THEN 'PARTIAL_CAPTURE'
      ELSE 'EXACT_DEPENDENCY'
    END,
    NEW.admitted_at
  FROM semantic_access_seed_heads_v13 h
  WHERE h.status='CURRENT' AND (
    h.dependency_capture='PARTIAL'
    OR NEW.changed_ref GLOB 'GLOBAL:*' OR NEW.changed_ref GLOB 'POLICY:*'
    OR NEW.changed_ref GLOB 'COMPILER:*' OR NEW.changed_ref GLOB 'GRAPH_SCHEMA:*'
    OR NEW.changed_ref GLOB 'AUTHORITY_SCHEMA:*'
    OR UPPER(NEW.reason_class) IN (
      'GLOBAL_BARRIER','POLICY_CHANGE','COMPILER_CHANGE','GRAPH_SCHEMA_CHANGE',
      'AUTHORITY_SCHEMA_CHANGE','DERIVATION_CHANGE'
    )
    OR EXISTS(
      SELECT 1 FROM semantic_access_seed_dependencies_v13 d
      WHERE d.generation_id=h.generation_id AND d.seed_id=h.seed_id
        AND d.dependency_ref=NEW.changed_ref
    )
  );

  UPDATE semantic_access_seed_heads_v13
  SET status='STALE',invalidated_by_pulse_id=NEW.applied_pulse_id,
      invalidated_delta_id=NEW.delta_id,updated_at=NEW.admitted_at
  WHERE seed_id IN (
    SELECT seed_id FROM semantic_access_seed_invalidations_v13 WHERE delta_id=NEW.delta_id
  ) AND status='CURRENT';
END;

CREATE VIEW IF NOT EXISTS v_current_semantic_access_v13 AS
SELECT h.seed_id,h.generation_id,p.target_record_id,p.target_logical_id,p.path_rank,p.hop_count,
       p.path_weight,p.authority_rank,p.path_clay,g.source_epoch AS built_source_epoch,
       g.graph_epoch AS built_graph_epoch,g.derivation_hash,h.dependency_capture,
       s.source_epoch AS pulse_source_epoch,s.graph_epoch AS pulse_graph_epoch,s.pulse_count
FROM frank_database_pulse_state s
JOIN semantic_access_seed_heads_v13 h ON h.status='CURRENT'
JOIN semantic_access_generations g ON g.generation_id=h.generation_id
  AND g.status IN ('VERIFIED','CURRENT','SUPERSEDED')
JOIN semantic_access_projection_v11 p
  ON p.generation_id=h.generation_id AND p.seed_id=h.seed_id
WHERE s.singleton_id=1 AND s.status IN ('PULSING','PAUSED','DEGRADED')
  AND h.installed_source_epoch<=s.source_epoch AND h.installed_graph_epoch<=s.graph_epoch;

-- U13 laws:
-- 1. U12 Pulse is the ONLY liveness/cognition-cycle authority; U13 adds no second Pulse.
-- 2. U13 reuses U11 immutable path rows; it does not create another path truth store.
-- 3. COMPLETE heads survive unrelated global epoch increments iff no admitted Pulse delta matches
--    one of their declared dependencies. PARTIAL heads conservatively stale on every applied delta.
-- 4. Global policy/compiler/schema/derivation barriers stale all heads by ref OR reason class.
-- 5. Invalidation is coupled to U12 delta acknowledgement and rolls back with a failed Pulse.
-- 6. STALE heads never appear in the hot view; callers must fall back/rebuild.
-- 7. A seed-generation promotion is valid only after explicit runtime verification against the
--    current U12 Pulse source/graph epochs, dependency certificate and non-empty U11 membership.
-- 8. Rank/reachability remain non-authoritative context; proof/effect authority is unchanged.
-- 9. Invalidation receipt time is the source delta admission time; U12 pulse_id binds execution.

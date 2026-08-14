-- CLAY U10 · POSSIBILITY PREPROCESSOR / STANDING POSSIBILITY ARRANGEMENTS
-- Research candidate. UnifiedDB remains canonical semantic state; ClayGraph remains derived topology.
-- The hot cognitive path reads already prepared packets and never promotes activation to truth/authority.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS possibility_candidates(
  candidate_version_id TEXT PRIMARY KEY,
  candidate_id TEXT NOT NULL,
  family_id TEXT NOT NULL,
  context_signature TEXT NOT NULL,
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER,
  candidate_kind TEXT NOT NULL,
  semantic_refs_clay TEXT NOT NULL DEFAULT '[]',
  graph_refs_clay TEXT NOT NULL DEFAULT '[]',
  hyperposition_refs_clay TEXT NOT NULL DEFAULT '[]',
  evidence_refs_clay TEXT NOT NULL DEFAULT '[]',
  conflict_refs_clay TEXT NOT NULL DEFAULT '[]',
  uncertainty_refs_clay TEXT NOT NULL DEFAULT '[]',
  authority_refs_clay TEXT NOT NULL DEFAULT '[]',
  dependency_refs_clay TEXT NOT NULL DEFAULT '[]',
  utility REAL NOT NULL DEFAULT 0.0,
  coherence REAL NOT NULL DEFAULT 0.0,
  urgency REAL NOT NULL DEFAULT 0.0,
  evidence_score REAL NOT NULL DEFAULT 0.0,
  risk REAL NOT NULL DEFAULT 0.0,
  cost REAL NOT NULL DEFAULT 0.0,
  provenance_clay TEXT NOT NULL,
  derivation_hash TEXT NOT NULL,
  valid_until TEXT,
  status TEXT NOT NULL CHECK(status IN ('CURRENT','STALE','SUPPRESSED','REVOKED','CANDIDATE')),
  materialized_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_possibility_candidate_sig
ON possibility_candidates(context_signature,status,source_epoch DESC,graph_epoch DESC);
CREATE INDEX IF NOT EXISTS idx_possibility_candidate_logical
ON possibility_candidates(candidate_id,source_epoch DESC,graph_epoch DESC,status);
CREATE INDEX IF NOT EXISTS idx_possibility_candidate_family
ON possibility_candidates(context_signature,family_id,status,source_epoch DESC,graph_epoch DESC);

CREATE TABLE IF NOT EXISTS possibility_candidate_members(
  candidate_version_id TEXT NOT NULL REFERENCES possibility_candidates(candidate_version_id) ON DELETE CASCADE,
  member_ref TEXT NOT NULL,
  member_role TEXT NOT NULL,
  dependency_class TEXT NOT NULL,
  PRIMARY KEY(candidate_version_id,member_ref,member_role,dependency_class)
);
CREATE INDEX IF NOT EXISTS idx_possibility_candidate_member
ON possibility_candidate_members(member_ref,dependency_class,candidate_version_id);

CREATE TABLE IF NOT EXISTS possibility_packets(
  packet_id TEXT PRIMARY KEY,
  context_signature TEXT NOT NULL,
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER,
  selector_id TEXT NOT NULL,
  selector_hash TEXT NOT NULL,
  top_k INTEGER NOT NULL,
  candidate_refs_clay TEXT NOT NULL,
  suppressed_refs_clay TEXT NOT NULL DEFAULT '[]',
  conflict_refs_clay TEXT NOT NULL DEFAULT '[]',
  uncertainty_refs_clay TEXT NOT NULL DEFAULT '[]',
  authority_refs_clay TEXT NOT NULL DEFAULT '[]',
  next_intents_clay TEXT NOT NULL DEFAULT '[]',
  packet_clay TEXT NOT NULL,
  packet_hash TEXT NOT NULL,
  candidate_count INTEGER NOT NULL,
  family_count INTEGER NOT NULL DEFAULT 0,
  valid_until TEXT,
  status TEXT NOT NULL CHECK(status IN ('CURRENT','STALE','SUPERSEDED','INVALID')),
  materialized_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_possibility_packet_hot
ON possibility_packets(context_signature,status,source_epoch DESC,graph_epoch DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_possibility_packet_one_current
ON possibility_packets(context_signature) WHERE status='CURRENT';

CREATE TABLE IF NOT EXISTS possibility_packet_dependencies(
  packet_id TEXT NOT NULL REFERENCES possibility_packets(packet_id) ON DELETE CASCADE,
  member_ref TEXT NOT NULL,
  dependency_class TEXT NOT NULL,
  PRIMARY KEY(packet_id,member_ref,dependency_class)
);
CREATE INDEX IF NOT EXISTS idx_possibility_packet_dependency
ON possibility_packet_dependencies(member_ref,dependency_class,packet_id);

CREATE TABLE IF NOT EXISTS possibility_packet_invalidations(
  invalidation_id TEXT PRIMARY KEY,
  changed_ref TEXT NOT NULL,
  source_epoch INTEGER NOT NULL,
  affected_signatures_clay TEXT NOT NULL DEFAULT '[]',
  reason_class TEXT NOT NULL,
  requested_at TEXT NOT NULL,
  processed_at TEXT,
  status TEXT NOT NULL CHECK(status IN ('OPEN','PROCESSING','COMPLETE','FAILED'))
);
CREATE INDEX IF NOT EXISTS idx_possibility_invalidation_open
ON possibility_packet_invalidations(status,source_epoch);

CREATE TABLE IF NOT EXISTS possibility_materialization_policies(
  policy_id TEXT PRIMARY KEY,
  context_family TEXT NOT NULL,
  query_shape_class TEXT NOT NULL,
  materialization_mode TEXT NOT NULL CHECK(materialization_mode IN ('STANDING','HYBRID','LAZY')),
  read_rate_ema REAL,
  update_rate_ema REAL,
  lazy_query_ms REAL,
  packet_query_ms REAL,
  maintenance_ms REAL,
  storage_penalty_ms REAL NOT NULL DEFAULT 0.0,
  expected_net_benefit_ms_per_window REAL,
  fallback_recipe_clay TEXT NOT NULL DEFAULT '{}',
  evidence_refs_clay TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_possibility_policy_family
ON possibility_materialization_policies(context_family,status,updated_at DESC);

CREATE TABLE IF NOT EXISTS possibility_compile_receipts(
  receipt_id TEXT PRIMARY KEY,
  context_signature TEXT,
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER,
  selector_hash TEXT NOT NULL,
  candidate_count INTEGER NOT NULL,
  selected_count INTEGER NOT NULL,
  compile_latency_ms REAL,
  update_scope_count INTEGER,
  packet_hash TEXT,
  verification_class TEXT NOT NULL,
  evidence_refs_clay TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL
);

CREATE VIEW IF NOT EXISTS v_current_possibility_packets AS
WITH ranked AS (
  SELECT p.*,
         ROW_NUMBER() OVER(
           PARTITION BY context_signature
           ORDER BY source_epoch DESC, COALESCE(graph_epoch,-1) DESC, materialized_at DESC, packet_id DESC
         ) AS rn
  FROM possibility_packets p
  WHERE status='CURRENT' AND (valid_until IS NULL OR julianday(valid_until) > julianday('now'))
)
SELECT * FROM ranked WHERE rn=1;

CREATE VIEW IF NOT EXISTS v_current_possibility_candidates AS
SELECT * FROM possibility_candidates
WHERE status='CURRENT' AND (valid_until IS NULL OR julianday(valid_until) > julianday('now'));

-- Runtime invariants:
-- 1. hot read = canonical cue/signature -> current packet; no eager whole-memory scan or whole-graph rebuild;
-- 2. packets are derived/model-facing products and never outrank UnifiedDB evidence/provenance;
-- 3. ClayGraph activation/relation may affect accessibility/score only, never truth or effect authority;
-- 4. Hyperposition alternatives/conflicts remain represented in candidate/packet refs; selection is not deletion;
-- 5. writes/re-entry invalidate only packets whose dependency members intersect the changed semantic closure;
-- 6. stale/mixed epochs fail closed to the previous coherent packet or explicit cold fallback;
-- 7. cold fallback retrieval remains allowed for missing/unknown/exploratory contexts;
-- 8. promotion requires differential equivalence to full recompute plus latency/accuracy/update-amplification evidence;
-- 9. standing materialization is adaptive: hot/cheap-to-maintain contexts may be STANDING; cold/high-maintenance contexts remain LAZY/HYBRID;
-- 10. top-k is family-factorized: multiple bindings of one possibility family cannot crowd out distinct alternatives;
-- 11. expired candidates are excluded before packet selection; freshness is parsed as time, never inferred from string order or semantic similarity.

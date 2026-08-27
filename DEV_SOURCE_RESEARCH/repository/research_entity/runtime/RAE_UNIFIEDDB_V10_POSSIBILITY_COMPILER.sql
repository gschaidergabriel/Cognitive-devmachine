-- CLAY U10 · INCREMENTAL POSSIBILITY COMPILER / PREPROCESSOR
--
-- Design law: UnifiedDB remains semantic/provenance authority.  This migration adds
-- rebuildable compiled read products so the hot cognition path consumes a bounded
-- current possibility field instead of performing global combinatorial search.
-- ClayGraph activation/reachability proposes accessibility only; it never promotes
-- truth or effect authority.
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS clay_possibility_compiler_specs(
  compiler_id TEXT PRIMARY KEY,
  compiler_version TEXT NOT NULL,
  max_depth INTEGER NOT NULL CHECK(max_depth >= 0),
  max_witnesses_per_candidate INTEGER NOT NULL CHECK(max_witnesses_per_candidate > 0),
  max_path_states INTEGER NOT NULL CHECK(max_path_states > 0),
  selector_clay TEXT NOT NULL,
  score_policy_clay TEXT NOT NULL,
  facet_schema_clay TEXT NOT NULL,
  invalidation_policy_clay TEXT NOT NULL,
  policy_hash TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('CANDIDATE','CURRENT','SUPERSEDED','REFUTED')),
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clay_possibility_field_epochs(
  field_epoch INTEGER PRIMARY KEY,
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER NOT NULL,
  compiler_id TEXT NOT NULL REFERENCES clay_possibility_compiler_specs(compiler_id),
  input_hash TEXT NOT NULL,
  field_hash TEXT,
  status TEXT NOT NULL CHECK(status IN ('BUILDING','CURRENT','STALE','SUPERSEDED','FAILED')),
  built_at TEXT NOT NULL,
  completed_at TEXT,
  build_metadata_clay TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_poss_field_epoch_current
  ON clay_possibility_field_epochs(status,source_epoch DESC,graph_epoch DESC);

CREATE TABLE IF NOT EXISTS clay_possibility_ordinals(
  candidate_ref TEXT PRIMARY KEY,
  ordinal INTEGER NOT NULL UNIQUE CHECK(ordinal >= 0),
  first_source_epoch INTEGER NOT NULL,
  retired_source_epoch INTEGER,
  status TEXT NOT NULL CHECK(status IN ('CURRENT','RETIRED'))
);

CREATE TABLE IF NOT EXISTS clay_possibility_anchor_fields(
  field_id TEXT PRIMARY KEY,
  field_epoch INTEGER NOT NULL REFERENCES clay_possibility_field_epochs(field_epoch) ON DELETE CASCADE,
  anchor_ref TEXT NOT NULL,
  anchor_kind TEXT,
  candidate_count INTEGER NOT NULL,
  truncated INTEGER NOT NULL DEFAULT 0 CHECK(truncated IN (0,1)),
  compile_ms REAL,
  input_hash TEXT NOT NULL,
  output_hash TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('CURRENT','STALE','FAILED','SUPERSEDED')),
  created_at TEXT NOT NULL,
  UNIQUE(field_epoch,anchor_ref)
);
CREATE INDEX IF NOT EXISTS idx_poss_anchor_latest
  ON clay_possibility_anchor_fields(anchor_ref,field_epoch DESC,status);

CREATE TABLE IF NOT EXISTS clay_possibility_field_members(
  field_id TEXT NOT NULL REFERENCES clay_possibility_anchor_fields(field_id) ON DELETE CASCADE,
  candidate_ref TEXT NOT NULL,
  candidate_ordinal INTEGER NOT NULL,
  rank INTEGER NOT NULL CHECK(rank >= 0),
  score REAL NOT NULL,
  best_path_score REAL NOT NULL,
  derivation_count INTEGER NOT NULL DEFAULT 1 CHECK(derivation_count > 0),
  witness_truncated INTEGER NOT NULL DEFAULT 0 CHECK(witness_truncated IN (0,1)),
  evidence_refs_clay TEXT NOT NULL DEFAULT '[]',
  provenance_clay TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY(field_id,candidate_ref),
  FOREIGN KEY(candidate_ref) REFERENCES clay_possibility_ordinals(candidate_ref),
  FOREIGN KEY(candidate_ordinal) REFERENCES clay_possibility_ordinals(ordinal)
);
CREATE INDEX IF NOT EXISTS idx_poss_member_rank
  ON clay_possibility_field_members(field_id,rank);
CREATE INDEX IF NOT EXISTS idx_poss_member_candidate
  ON clay_possibility_field_members(candidate_ref,field_id);

-- Hyperposition-safe bounded derivation witnesses.  Multiple still-admissible paths
-- survive until projection.  If witness_truncated=1 and a stored witness is invalidated,
-- the safe repair is ANCHOR_RECOMPILE rather than pretending an unseen alternative.
CREATE TABLE IF NOT EXISTS clay_possibility_witnesses(
  witness_id TEXT PRIMARY KEY,
  field_id TEXT NOT NULL,
  candidate_ref TEXT NOT NULL,
  witness_rank INTEGER NOT NULL CHECK(witness_rank >= 0),
  path_score REAL NOT NULL,
  path_refs_clay TEXT NOT NULL,
  relation_refs_clay TEXT NOT NULL DEFAULT '[]',
  path_hash TEXT NOT NULL,
  provenance_clay TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL CHECK(status IN ('CURRENT','INVALIDATED','SUPERSEDED')),
  created_at TEXT NOT NULL,
  UNIQUE(field_id,candidate_ref,witness_rank),
  FOREIGN KEY(field_id,candidate_ref)
    REFERENCES clay_possibility_field_members(field_id,candidate_ref) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_poss_witness_path_hash
  ON clay_possibility_witnesses(path_hash,status);

-- Facets are dynamic constraints (availability, authority, modality, privacy, cost tier,
-- freshness class, etc.).  A runtime may materialize membership as a dense bitset,
-- Roaring bitmap, or another measured encoding.  The encoding is explicitly typed and
-- rebuildable; the source observations remain authoritative.
CREATE TABLE IF NOT EXISTS clay_possibility_facets(
  facet_id TEXT PRIMARY KEY,
  field_epoch INTEGER NOT NULL REFERENCES clay_possibility_field_epochs(field_epoch) ON DELETE CASCADE,
  facet_key TEXT NOT NULL,
  facet_value TEXT NOT NULL,
  encoding TEXT NOT NULL CHECK(encoding IN ('DENSE_BITSET_LE','ROARING32','SORTED_U32','NONE')),
  membership_blob BLOB,
  member_count INTEGER NOT NULL,
  ordinal_highwater INTEGER NOT NULL DEFAULT 0,
  source_hash TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('CURRENT','STALE','SUPERSEDED')),
  created_at TEXT NOT NULL,
  UNIQUE(field_epoch,facet_key,facet_value)
);
CREATE INDEX IF NOT EXISTS idx_poss_facet_lookup
  ON clay_possibility_facets(field_epoch,facet_key,facet_value,status);

CREATE TABLE IF NOT EXISTS clay_possibility_invalidation_queue(
  invalidation_id TEXT PRIMARY KEY,
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER,
  changed_ref TEXT NOT NULL,
  reason_class TEXT NOT NULL,
  affected_anchor_refs_clay TEXT NOT NULL DEFAULT '[]',
  repair_mode TEXT NOT NULL CHECK(repair_mode IN ('FACET_ONLY','WITNESS_REPAIR','ANCHOR_RECOMPILE','FIELD_REBUILD')),
  evidence_refs_clay TEXT NOT NULL DEFAULT '[]',
  requested_at TEXT NOT NULL,
  processed_at TEXT,
  status TEXT NOT NULL CHECK(status IN ('OPEN','PROCESSING','DONE','FAILED'))
);
CREATE INDEX IF NOT EXISTS idx_poss_invalidation_open
  ON clay_possibility_invalidation_queue(status,source_epoch);

CREATE TABLE IF NOT EXISTS clay_possibility_query_receipts(
  query_receipt_id TEXT PRIMARY KEY,
  cycle_id TEXT,
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER NOT NULL,
  field_epoch INTEGER NOT NULL,
  anchor_ref TEXT NOT NULL,
  facet_query_clay TEXT NOT NULL,
  selected_refs_clay TEXT NOT NULL,
  suppressed_count INTEGER NOT NULL DEFAULT 0,
  selector_hash TEXT NOT NULL,
  latency_us INTEGER,
  fallback_class TEXT NOT NULL CHECK(fallback_class IN ('COMPILED_FIELD','RECURSIVE_SQL','RAW_SCAN','NO_RESULT')),
  exactness_check_clay TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  FOREIGN KEY(field_epoch) REFERENCES clay_possibility_field_epochs(field_epoch)
);
CREATE INDEX IF NOT EXISTS idx_poss_query_cycle
  ON clay_possibility_query_receipts(cycle_id,created_at DESC);

CREATE VIEW IF NOT EXISTS v_clay_current_possibility_field_epoch AS
SELECT e.* FROM clay_possibility_field_epochs e
WHERE e.status='CURRENT'
ORDER BY e.source_epoch DESC,e.graph_epoch DESC,e.field_epoch DESC
LIMIT 1;

CREATE VIEW IF NOT EXISTS v_clay_current_possibility_anchor_fields AS
SELECT f.* FROM clay_possibility_anchor_fields f
JOIN v_clay_current_possibility_field_epoch e ON e.field_epoch=f.field_epoch
WHERE f.status='CURRENT';

CREATE VIEW IF NOT EXISTS v_clay_compiled_possibility_candidates AS
SELECT f.field_epoch,f.anchor_ref,m.candidate_ref,m.candidate_ordinal,m.rank,m.score,
       m.best_path_score,m.derivation_count,m.witness_truncated,m.evidence_refs_clay,m.provenance_clay
FROM v_clay_current_possibility_anchor_fields f
JOIN clay_possibility_field_members m ON m.field_id=f.field_id;

-- U10 invariants:
-- 1. compiled possibility != truth and != effect authority;
-- 2. compiled fields are rebuildable from UnifiedDB + ClayGraph epochs and provenance;
-- 3. hot retrieval must not perform eager global combinatorial closure when a valid field exists;
-- 4. dynamic constraints are applied as facets after structural possibility compilation;
-- 5. alternative derivation witnesses are preserved up to a bounded budget;
-- 6. witness truncation forces conservative anchor recompilation on relevant invalidation;
-- 7. mixed source/graph/field epochs are rejected by runtime;
-- 8. recursive SQL/raw scan remains an explicit measurable fallback, never a silent semantic divergence;
-- 9. BUILDING epochs are shadow-state; last-known-good CURRENT remains readable until atomic promotion.

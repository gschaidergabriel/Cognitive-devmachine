-- CLAYGRAPH V4 CANDIDATE · STRICT SEMANTIC ACCESS HEADS
-- Purpose: prevent stale semantic-path resurrection while making strict latest-version reads bounded.
-- Authority: derived/rebuildable topology only. UnifiedDB + version logs remain semantic authority.
PRAGMA foreign_keys=ON;

-- V3's historical compatibility view chooses MAX(graph_epoch) only among CURRENT rows.
-- That can resurrect an older CURRENT path after a newer version is QUARANTINED/SUPERSEDED.
-- Strict semantics select the newest version first, then apply status.
CREATE VIEW IF NOT EXISTS v_current_graph_semantic_access_paths_strict AS
SELECT p.*
FROM graph_semantic_access_paths p
JOIN (
  SELECT seed_id,target_logical_id,MAX(graph_epoch) AS ge
  FROM graph_semantic_access_paths
  GROUP BY seed_id,target_logical_id
) x
ON x.seed_id=p.seed_id
AND x.target_logical_id=p.target_logical_id
AND x.ge=p.graph_epoch
WHERE p.status='CURRENT';

-- Same-epoch multiple versions have no safe total order in the V3 contract.
-- They therefore block projection promotion instead of being silently adjudicated.
CREATE VIEW IF NOT EXISTS v_graph_semantic_access_ambiguous_epochs AS
SELECT seed_id,target_logical_id,graph_epoch,COUNT(*) AS version_count
FROM graph_semantic_access_paths
GROUP BY seed_id,target_logical_id,graph_epoch
HAVING COUNT(*)>1;

-- Rebuildable latest-version head. Tombstones/non-CURRENT latest versions are retained
-- so a stale older CURRENT path cannot reappear through the fast view.
CREATE TABLE IF NOT EXISTS graph_semantic_access_heads(
  seed_id TEXT NOT NULL,
  target_logical_id TEXT NOT NULL,
  access_path_version_id TEXT NOT NULL,
  seed_logical_id TEXT NOT NULL,
  graph_epoch INTEGER NOT NULL,
  source_epoch INTEGER NOT NULL,
  path_rank INTEGER NOT NULL CHECK(path_rank > 0),
  hop_count INTEGER NOT NULL CHECK(hop_count >= 0),
  path_weight REAL NOT NULL,
  relation_signature TEXT NOT NULL,
  provenance_clay TEXT NOT NULL,
  admissibility_clay TEXT NOT NULL,
  derivation_hash TEXT NOT NULL,
  source_status TEXT NOT NULL CHECK(source_status IN ('CURRENT','SUPERSEDED','QUARANTINED')),
  created_at TEXT NOT NULL,
  PRIMARY KEY(seed_id,target_logical_id),
  FOREIGN KEY(graph_epoch) REFERENCES graph_epochs(graph_epoch)
);

-- access_path_version_id is already globally unique in the authoritative source log.
-- Re-enforcing that uniqueness in the rebuildable head adds a B-tree/write cost without
-- increasing semantic safety; the head can only be admitted after source/head verification.
CREATE INDEX IF NOT EXISTS idx_graph_semantic_access_heads_hot
ON graph_semantic_access_heads(seed_id,path_rank,path_weight DESC,target_logical_id)
WHERE source_status='CURRENT';

CREATE INDEX IF NOT EXISTS idx_graph_semantic_access_heads_target
ON graph_semantic_access_heads(target_logical_id,graph_epoch DESC,seed_id)
WHERE source_status='CURRENT';

CREATE VIEW IF NOT EXISTS v_current_graph_semantic_access_paths_fast AS
SELECT * FROM graph_semantic_access_heads WHERE source_status='CURRENT';

CREATE TABLE IF NOT EXISTS graph_semantic_access_head_receipts(
  projection_id TEXT PRIMARY KEY,
  graph_epoch INTEGER NOT NULL,
  source_epoch INTEGER NOT NULL,
  source_row_count INTEGER NOT NULL,
  head_row_count INTEGER NOT NULL,
  strict_current_row_count INTEGER NOT NULL,
  fast_current_row_count INTEGER NOT NULL,
  ambiguity_count INTEGER NOT NULL,
  stale_resurrection_count INTEGER NOT NULL,
  verified_equal INTEGER NOT NULL DEFAULT 0,
  benchmark_ref TEXT,
  derivation_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(graph_epoch) REFERENCES graph_epochs(graph_epoch)
);

CREATE TRIGGER IF NOT EXISTS trg_graph_semantic_access_head_upsert
AFTER INSERT ON graph_semantic_access_paths
BEGIN
  INSERT INTO graph_semantic_access_heads(
    seed_id,target_logical_id,access_path_version_id,seed_logical_id,graph_epoch,source_epoch,
    path_rank,hop_count,path_weight,relation_signature,provenance_clay,admissibility_clay,
    derivation_hash,source_status,created_at
  ) VALUES(
    NEW.seed_id,NEW.target_logical_id,NEW.access_path_version_id,NEW.seed_logical_id,NEW.graph_epoch,NEW.source_epoch,
    NEW.path_rank,NEW.hop_count,NEW.path_weight,NEW.relation_signature,NEW.provenance_clay,NEW.admissibility_clay,
    NEW.derivation_hash,NEW.status,NEW.created_at
  )
  ON CONFLICT(seed_id,target_logical_id) DO UPDATE SET
    access_path_version_id=excluded.access_path_version_id,
    seed_logical_id=excluded.seed_logical_id,
    graph_epoch=excluded.graph_epoch,
    source_epoch=excluded.source_epoch,
    path_rank=excluded.path_rank,
    hop_count=excluded.hop_count,
    path_weight=excluded.path_weight,
    relation_signature=excluded.relation_signature,
    provenance_clay=excluded.provenance_clay,
    admissibility_clay=excluded.admissibility_clay,
    derivation_hash=excluded.derivation_hash,
    source_status=excluded.source_status,
    created_at=excluded.created_at
  WHERE excluded.graph_epoch > graph_semantic_access_heads.graph_epoch
     OR (excluded.graph_epoch = graph_semantic_access_heads.graph_epoch
         AND excluded.access_path_version_id > graph_semantic_access_heads.access_path_version_id);
END;

-- PROMOTION GATE (all mandatory):
-- 1. v_graph_semantic_access_ambiguous_epochs is empty on the target dataset.
-- 2. Rebuild graph_semantic_access_heads transactionally from the newest version per
--    (seed_id,target_logical_id), retaining non-CURRENT latest versions as tombstones.
-- 3. v_current_graph_semantic_access_paths_fast == v_current_graph_semantic_access_paths_strict
--    by full row identity/hash under matched graph/source epochs.
-- 4. A newer QUARANTINED/SUPERSEDED version must suppress an older CURRENT version.
-- 5. Write graph_semantic_access_head_receipts.verified_equal=1 only after 1-4 pass.
-- 6. Activation/accessibility remains non-authoritative; no graph head can mint truth/effect authority.

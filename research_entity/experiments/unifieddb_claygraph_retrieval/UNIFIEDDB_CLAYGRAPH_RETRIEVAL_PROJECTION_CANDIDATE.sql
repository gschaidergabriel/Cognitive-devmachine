-- CANDIDATE ONLY. Disposable/rebuildable retrieval projection.
-- UnifiedDB/StateLedger remains canonical; ClayGraph remains derived and non-authoritative.
-- Schema v2 adds deterministic per-source neighbor rank so runtime graph traversal has a
-- real work bound rather than an output-only LIMIT. All graph edges remain stored; rank is
-- an acceleration/admission projection, never evidence strength or truth.
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS retrieval_projection_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS udb_retrieval_documents(
  record_id TEXT PRIMARY KEY,
  logical_id TEXT NOT NULL,
  record_kind TEXT NOT NULL,
  record_key TEXT NOT NULL,
  scope TEXT NOT NULL,
  epistemic_class TEXT NOT NULL,
  status TEXT NOT NULL,
  source_epoch INTEGER NOT NULL,
  title TEXT NOT NULL DEFAULT '',
  body TEXT NOT NULL,
  tags TEXT NOT NULL DEFAULT '',
  source_hash TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_udb_retrieval_current ON udb_retrieval_documents(status,scope,record_kind);
CREATE INDEX IF NOT EXISTS idx_udb_retrieval_logical ON udb_retrieval_documents(logical_id,status);
CREATE VIRTUAL TABLE IF NOT EXISTS udb_retrieval_fts USING fts5(
  record_id UNINDEXED,logical_id UNINDEXED,title,body,tags,
  tokenize='unicode61 remove_diacritics 2',prefix='2 3 4'
);
CREATE TABLE IF NOT EXISTS claygraph_neighbor_cache(
  source_logical_id TEXT NOT NULL,
  target_logical_id TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  weight REAL NOT NULL,
  confidence REAL,
  graph_epoch INTEGER NOT NULL,
  source_epoch INTEGER NOT NULL,
  causal_class TEXT,
  provenance_clay TEXT NOT NULL DEFAULT '{}',
  admissibility_clay TEXT NOT NULL DEFAULT '{}',
  source_rank INTEGER NOT NULL DEFAULT 2147483647,
  PRIMARY KEY(source_logical_id,target_logical_id,relation_type,graph_epoch)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_claygraph_neighbor_source_epoch
  ON claygraph_neighbor_cache(source_logical_id,graph_epoch DESC,source_rank,weight DESC,target_logical_id);
CREATE INDEX IF NOT EXISTS idx_claygraph_neighbor_target_epoch
  ON claygraph_neighbor_cache(target_logical_id,graph_epoch DESC,weight DESC,source_logical_id);

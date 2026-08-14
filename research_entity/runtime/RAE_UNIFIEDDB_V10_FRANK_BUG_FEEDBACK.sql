-- CLAY U10 · Frank explicit bug feedback intake
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS clay_frank_bug_reports(
  bug_id TEXT PRIMARY KEY,
  source_repository TEXT NOT NULL,
  source_path TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  previous_andreas_input TEXT NOT NULL,
  previous_frank_output TEXT NOT NULL,
  session_ref TEXT,
  source_cycle_id TEXT,
  source_frank_epoch INTEGER,
  source_frank_repo_head TEXT,
  redaction_applied INTEGER NOT NULL DEFAULT 0 CHECK(redaction_applied IN (0,1)),
  research_state TEXT NOT NULL DEFAULT 'NEW' CHECK(research_state IN ('NEW','CLAIMED','TRIAGED','RESOLVED','REJECTED')),
  ingested_at TEXT NOT NULL,
  UNIQUE(source_repository,source_path)
);
CREATE INDEX IF NOT EXISTS idx_clay_frank_bug_state ON clay_frank_bug_reports(research_state,ingested_at DESC);

CREATE TABLE IF NOT EXISTS clay_frank_bug_ingest_receipts(
  receipt_id TEXT PRIMARY KEY,
  bug_id TEXT NOT NULL REFERENCES clay_frank_bug_reports(bug_id),
  source_path TEXT NOT NULL,
  source_payload_hash TEXT NOT NULL,
  work_id TEXT,
  ingest_state TEXT NOT NULL CHECK(ingest_state IN ('INGESTED','DUPLICATE','REJECTED_HASH','INVALID')),
  evidence_clay TEXT NOT NULL,
  created_at TEXT NOT NULL
);

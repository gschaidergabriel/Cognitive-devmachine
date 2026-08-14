PRAGMA foreign_keys=ON;

-- Research candidate only. Starts SHADOW; not promoted to canonical runtime migration.
CREATE TABLE IF NOT EXISTS frank_continuity_policy(
  policy_key TEXT PRIMARY KEY CHECK(policy_key='self.root/continuity'),
  enforcement_state TEXT NOT NULL CHECK(enforcement_state IN ('SHADOW','ENFORCE','DISABLED')),
  required_external_anchor INTEGER NOT NULL CHECK(required_external_anchor IN (0,1)),
  updated_at TEXT NOT NULL
);
INSERT OR IGNORE INTO frank_continuity_policy(policy_key,enforcement_state,required_external_anchor,updated_at)
VALUES('self.root/continuity','SHADOW',1,CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS frank_state_lineages(
  lineage_id TEXT PRIMARY KEY,
  parent_lineage_id TEXT REFERENCES frank_state_lineages(lineage_id),
  lineage_generation INTEGER NOT NULL CHECK(lineage_generation>=1),
  head_epoch INTEGER NOT NULL CHECK(head_epoch>=0),
  head_root_hash TEXT NOT NULL,
  parent_head_hash TEXT,
  external_anchor_generation INTEGER NOT NULL CHECK(external_anchor_generation>=0),
  external_anchor_ref TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('CANDIDATE','ADMITTED_CURRENT','RECOVERY_CANDIDATE','SUPERSEDED','QUARANTINED','REVOKED')),
  source_ref TEXT,
  created_at TEXT NOT NULL,
  admitted_at TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_frank_one_admitted_lineage
ON frank_state_lineages(status) WHERE status='ADMITTED_CURRENT';
CREATE UNIQUE INDEX IF NOT EXISTS ux_frank_lineage_generation
ON frank_state_lineages(lineage_generation);

CREATE TABLE IF NOT EXISTS frank_external_anchor_receipts(
  anchor_receipt_id TEXT PRIMARY KEY,
  anchor_ref TEXT NOT NULL,
  observed_generation INTEGER NOT NULL CHECK(observed_generation>=0),
  observed_digest TEXT NOT NULL,
  verification_state TEXT NOT NULL CHECK(verification_state IN ('VERIFIED','FAILED','UNKNOWN','STALE')),
  failure_domain_clay TEXT NOT NULL DEFAULT '{}',
  evidence_ref TEXT,
  observed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS frank_execution_fence(
  lease_key TEXT PRIMARY KEY CHECK(lease_key='self.root/global-execution'),
  lease_state TEXT NOT NULL CHECK(lease_state IN ('IDLE','ACTIVE','RELEASING','RECOVERING')),
  lease_epoch INTEGER NOT NULL CHECK(lease_epoch>=0),
  execution_id TEXT,
  lineage_id TEXT NOT NULL REFERENCES frank_state_lineages(lineage_id),
  lineage_generation INTEGER NOT NULL,
  external_anchor_generation INTEGER NOT NULL,
  holder_session_ref_hash TEXT,
  holder_client_ref_hash TEXT,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS semantic_transaction_execution_bindings(
  tx_id TEXT PRIMARY KEY REFERENCES semantic_transactions(tx_id) ON DELETE RESTRICT,
  lease_key TEXT NOT NULL,
  lease_epoch INTEGER NOT NULL,
  execution_id TEXT NOT NULL,
  lineage_id TEXT NOT NULL REFERENCES frank_state_lineages(lineage_id),
  lineage_generation INTEGER NOT NULL,
  external_anchor_generation INTEGER NOT NULL,
  session_ref_hash TEXT NOT NULL,
  client_ref_hash TEXT NOT NULL,
  binding_hash TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS frank_continuity_commits(
  commit_id TEXT PRIMARY KEY,
  tx_id TEXT NOT NULL UNIQUE REFERENCES semantic_transactions(tx_id) ON DELETE RESTRICT,
  lineage_id TEXT NOT NULL REFERENCES frank_state_lineages(lineage_id),
  lineage_generation INTEGER NOT NULL,
  parent_epoch INTEGER NOT NULL,
  new_epoch INTEGER NOT NULL UNIQUE,
  parent_root_hash TEXT NOT NULL,
  new_root_hash TEXT NOT NULL,
  lease_epoch INTEGER NOT NULL,
  execution_id TEXT NOT NULL,
  external_anchor_generation INTEGER NOT NULL,
  commit_hash TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  FOREIGN KEY(new_epoch) REFERENCES state_epochs(epoch) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS snapshot_lineage_bindings(
  snapshot_id TEXT PRIMARY KEY REFERENCES snapshots(snapshot_id) ON DELETE RESTRICT,
  lineage_id TEXT NOT NULL REFERENCES frank_state_lineages(lineage_id),
  lineage_generation INTEGER NOT NULL,
  external_anchor_generation INTEGER NOT NULL,
  head_epoch INTEGER NOT NULL,
  head_root_hash TEXT NOT NULL,
  binding_hash TEXT NOT NULL UNIQUE,
  verification_state TEXT NOT NULL CHECK(verification_state IN ('UNTESTED','VERIFIED','FAILED','STALE')),
  created_at TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS trg_frank_lineage_no_head_rewind
BEFORE UPDATE OF head_epoch,head_root_hash,lineage_generation,external_anchor_generation ON frank_state_lineages
WHEN (SELECT enforcement_state FROM frank_continuity_policy WHERE policy_key='self.root/continuity')='ENFORCE'
BEGIN
  SELECT CASE WHEN NEW.lineage_generation!=OLD.lineage_generation THEN RAISE(ABORT,'FRANK_LINEAGE_GENERATION_IMMUTABLE') END;
  SELECT CASE WHEN NEW.head_epoch<OLD.head_epoch THEN RAISE(ABORT,'FRANK_LINEAGE_HEAD_REWIND') END;
  SELECT CASE WHEN NEW.external_anchor_generation<OLD.external_anchor_generation THEN RAISE(ABORT,'FRANK_EXTERNAL_ANCHOR_REWIND') END;
END;

CREATE TRIGGER IF NOT EXISTS trg_frank_execution_fence_monotonic
BEFORE UPDATE OF lease_epoch,execution_id,lineage_id,lineage_generation,external_anchor_generation ON frank_execution_fence
WHEN (SELECT enforcement_state FROM frank_continuity_policy WHERE policy_key='self.root/continuity')='ENFORCE'
BEGIN
  SELECT CASE WHEN NEW.lease_epoch<OLD.lease_epoch THEN RAISE(ABORT,'FRANK_STALE_LEASE_EPOCH') END;
  SELECT CASE WHEN NEW.execution_id IS NOT OLD.execution_id AND NEW.lease_epoch<=OLD.lease_epoch THEN RAISE(ABORT,'FRANK_EXECUTION_CHANGE_REQUIRES_NEW_EPOCH') END;
  SELECT CASE WHEN NEW.external_anchor_generation<OLD.external_anchor_generation THEN RAISE(ABORT,'FRANK_EXECUTION_ANCHOR_REWIND') END;
END;

CREATE TRIGGER IF NOT EXISTS trg_frank_tx_binding_matches_current_execution
BEFORE INSERT ON semantic_transaction_execution_bindings
WHEN (SELECT enforcement_state FROM frank_continuity_policy WHERE policy_key='self.root/continuity')='ENFORCE'
BEGIN
  SELECT CASE WHEN NOT EXISTS(
    SELECT 1 FROM frank_execution_fence f
    JOIN frank_state_lineages l ON l.lineage_id=f.lineage_id
    WHERE f.lease_key=NEW.lease_key AND f.lease_state='ACTIVE'
      AND f.lease_epoch=NEW.lease_epoch AND f.execution_id=NEW.execution_id
      AND f.lineage_id=NEW.lineage_id AND f.lineage_generation=NEW.lineage_generation
      AND f.external_anchor_generation=NEW.external_anchor_generation
      AND f.holder_session_ref_hash=NEW.session_ref_hash
      AND f.holder_client_ref_hash=NEW.client_ref_hash
      AND l.status='ADMITTED_CURRENT'
  ) THEN RAISE(ABORT,'FRANK_TX_BINDING_STALE_EXECUTION') END;
END;

CREATE TRIGGER IF NOT EXISTS trg_frank_tx_binding_immutable_update
BEFORE UPDATE ON semantic_transaction_execution_bindings
WHEN (SELECT enforcement_state FROM frank_continuity_policy WHERE policy_key='self.root/continuity')='ENFORCE'
BEGIN SELECT RAISE(ABORT,'FRANK_TX_BINDING_IMMUTABLE'); END;

CREATE TRIGGER IF NOT EXISTS trg_frank_continuity_commit_guard
BEFORE INSERT ON frank_continuity_commits
WHEN (SELECT enforcement_state FROM frank_continuity_policy WHERE policy_key='self.root/continuity')='ENFORCE'
BEGIN
  SELECT CASE WHEN NEW.new_epoch!=NEW.parent_epoch+1 THEN RAISE(ABORT,'FRANK_NONCONTIGUOUS_STATE_EPOCH') END;
  SELECT CASE WHEN NOT EXISTS(
    SELECT 1 FROM frank_state_lineages l
    WHERE l.lineage_id=NEW.lineage_id AND l.status='ADMITTED_CURRENT'
      AND l.lineage_generation=NEW.lineage_generation
      AND l.head_epoch=NEW.parent_epoch AND l.head_root_hash=NEW.parent_root_hash
      AND l.external_anchor_generation<=NEW.external_anchor_generation
  ) THEN RAISE(ABORT,'FRANK_LINEAGE_PARENT_MISMATCH') END;
  SELECT CASE WHEN NOT EXISTS(
    SELECT 1 FROM frank_execution_fence f
    WHERE f.lease_key='self.root/global-execution' AND f.lease_state='ACTIVE'
      AND f.lease_epoch=NEW.lease_epoch AND f.execution_id=NEW.execution_id
      AND f.lineage_id=NEW.lineage_id AND f.lineage_generation=NEW.lineage_generation
      AND f.external_anchor_generation=NEW.external_anchor_generation
  ) THEN RAISE(ABORT,'FRANK_CONTINUITY_STALE_EXECUTION') END;
  SELECT CASE WHEN NOT EXISTS(
    SELECT 1 FROM semantic_transaction_execution_bindings b
    WHERE b.tx_id=NEW.tx_id AND b.lease_epoch=NEW.lease_epoch AND b.execution_id=NEW.execution_id
      AND b.lineage_id=NEW.lineage_id AND b.lineage_generation=NEW.lineage_generation
      AND b.external_anchor_generation=NEW.external_anchor_generation
  ) THEN RAISE(ABORT,'FRANK_CONTINUITY_TX_UNBOUND') END;
  SELECT CASE WHEN NOT EXISTS(
    SELECT 1 FROM semantic_transactions t
    WHERE t.tx_id=NEW.tx_id AND t.base_epoch=NEW.parent_epoch AND t.status!='COMMITTED'
  ) THEN RAISE(ABORT,'FRANK_CONTINUITY_TX_BASE_MISMATCH') END;
END;

CREATE TRIGGER IF NOT EXISTS trg_frank_continuity_advance_lineage
AFTER INSERT ON frank_continuity_commits
WHEN (SELECT enforcement_state FROM frank_continuity_policy WHERE policy_key='self.root/continuity')='ENFORCE'
BEGIN
  UPDATE frank_state_lineages
  SET head_epoch=NEW.new_epoch,head_root_hash=NEW.new_root_hash,external_anchor_generation=NEW.external_anchor_generation
  WHERE lineage_id=NEW.lineage_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_frank_state_epoch_requires_continuity
BEFORE INSERT ON state_epochs
WHEN (SELECT enforcement_state FROM frank_continuity_policy WHERE policy_key='self.root/continuity')='ENFORCE'
BEGIN
  SELECT CASE WHEN NOT EXISTS(
    SELECT 1 FROM frank_continuity_commits c
    WHERE c.new_epoch=NEW.epoch AND c.parent_epoch IS NEW.parent_epoch AND c.new_root_hash=NEW.root_hash
  ) THEN RAISE(ABORT,'FRANK_STATE_EPOCH_WITHOUT_CONTINUITY_COMMIT') END;
END;

CREATE VIEW IF NOT EXISTS v_frank_current_continuity AS
SELECT p.enforcement_state,p.required_external_anchor,
       l.lineage_id,l.lineage_generation,l.head_epoch,l.head_root_hash,
       l.external_anchor_generation,l.external_anchor_ref,
       f.lease_state,f.lease_epoch,f.execution_id,
       f.holder_session_ref_hash,f.holder_client_ref_hash,f.updated_at AS fence_updated_at
FROM frank_continuity_policy p
LEFT JOIN frank_state_lineages l ON l.status='ADMITTED_CURRENT'
LEFT JOIN frank_execution_fence f ON f.lineage_id=l.lineage_id
WHERE p.policy_key='self.root/continuity';

-- IMPORTANT: the external floor must be verified by code outside this rollback domain.
-- A receipt row inside UnifiedDB is provenance only; it cannot prove that UnifiedDB itself was not rewound.

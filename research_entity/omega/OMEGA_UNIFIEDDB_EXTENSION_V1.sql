-- OMEGA federation extension for EntityOS unified.db
-- Additive schema. Does not replace existing EntityOS identity/GRID/effect tables.
PRAGMA foreign_keys=ON;
BEGIN IMMEDIATE;

CREATE TABLE IF NOT EXISTS omega_source (
    source_id TEXT PRIMARY KEY,
    source_kind TEXT NOT NULL,
    canonical_uri TEXT NOT NULL,
    machine_id TEXT,
    owner TEXT,
    entity_id TEXT,
    installation_id TEXT,
    state_root_id TEXT,
    authority_tier INTEGER NOT NULL DEFAULT 100,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE','STALE','SUSPENDED','REVOKED','UNKNOWN')),
    discovered_at TEXT NOT NULL,
    last_observed_at TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_omega_source_uri ON omega_source(canonical_uri);

CREATE TABLE IF NOT EXISTS omega_repo_head (
    source_id TEXT NOT NULL REFERENCES omega_source(source_id),
    repository_full_name TEXT NOT NULL,
    repo_ref TEXT NOT NULL,
    commit_sha TEXT NOT NULL,
    tree_sha TEXT,
    observed_at TEXT NOT NULL,
    receipt_id TEXT,
    PRIMARY KEY(repository_full_name, repo_ref, commit_sha)
);

CREATE TABLE IF NOT EXISTS omega_ingest_batch (
    ingest_batch_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES omega_source(source_id),
    opened_at TEXT NOT NULL,
    closed_at TEXT,
    status TEXT NOT NULL CHECK(status IN ('OPEN','COMMITTED','PARTIAL','FAILED')),
    source_snapshot_digest TEXT,
    observation_count INTEGER NOT NULL DEFAULT 0,
    object_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    error_json TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS omega_object (
    object_sha256 TEXT PRIMARY KEY,
    byte_length INTEGER NOT NULL,
    media_type TEXT,
    codec TEXT,
    compressed_sha256 TEXT,
    compressed_length INTEGER,
    storage_uri TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS omega_observation (
    observation_id TEXT PRIMARY KEY,
    ingest_batch_id TEXT NOT NULL REFERENCES omega_ingest_batch(ingest_batch_id),
    source_id TEXT NOT NULL REFERENCES omega_source(source_id),
    source_repo TEXT,
    repo_ref TEXT,
    commit_sha TEXT,
    machine_id TEXT,
    owner TEXT,
    entity_id TEXT,
    installation_id TEXT,
    state_root_id TEXT,
    runtime_epoch_id TEXT,
    source_db TEXT,
    source_table TEXT,
    source_pk TEXT,
    receipt_id TEXT,
    observed_at TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    epistemic_class TEXT NOT NULL CHECK(epistemic_class IN ('OBSERVED','REPORTED','INFERRED','GENERATED_CACHE')),
    content_sha256 TEXT NOT NULL,
    object_sha256 TEXT REFERENCES omega_object(object_sha256),
    authority_ref TEXT,
    authority_digest TEXT,
    confidence REAL CHECK(confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),
    status TEXT NOT NULL DEFAULT 'VALID' CHECK(status IN ('VALID','STALE','CONFLICTED','REVOKED','INVALID')),
    payload_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS ix_omega_obs_source_time ON omega_observation(source_id, observed_at);
CREATE INDEX IF NOT EXISTS ix_omega_obs_machine_epoch ON omega_observation(machine_id, runtime_epoch_id);
CREATE INDEX IF NOT EXISTS ix_omega_obs_content ON omega_observation(content_sha256);

CREATE TABLE IF NOT EXISTS omega_alias (
    namespace TEXT NOT NULL,
    alias TEXT NOT NULL,
    canonical_kind TEXT NOT NULL,
    canonical_id TEXT NOT NULL,
    source_observation_id TEXT REFERENCES omega_observation(observation_id),
    confidence REAL NOT NULL DEFAULT 1.0 CHECK(confidence >= 0.0 AND confidence <= 1.0),
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE','DISPUTED','REVOKED')),
    PRIMARY KEY(namespace, alias, canonical_kind, canonical_id)
);

CREATE TABLE IF NOT EXISTS omega_claim (
    claim_id TEXT PRIMARY KEY,
    subject_key TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object_json TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('CANDIDATE','CURRENT','CONFLICTED','SUPERSEDED','REJECTED','UNKNOWN')),
    authority_tier INTEGER NOT NULL DEFAULT 100,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_omega_claim_sp ON omega_claim(subject_key, predicate, status);

CREATE TABLE IF NOT EXISTS omega_claim_evidence (
    claim_id TEXT NOT NULL REFERENCES omega_claim(claim_id),
    observation_id TEXT NOT NULL REFERENCES omega_observation(observation_id),
    relation TEXT NOT NULL CHECK(relation IN ('SUPPORTS','CONTRADICTS','QUALIFIES','SUPERSEDES')),
    PRIMARY KEY(claim_id, observation_id, relation)
);

CREATE TABLE IF NOT EXISTS omega_conflict (
    conflict_id TEXT PRIMARY KEY,
    subject_key TEXT NOT NULL,
    predicate TEXT NOT NULL,
    left_claim_id TEXT REFERENCES omega_claim(claim_id),
    right_claim_id TEXT REFERENCES omega_claim(claim_id),
    detected_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('OPEN','RESOLVED','ACCEPTED_AMBIGUITY')),
    resolution_json TEXT
);

CREATE TABLE IF NOT EXISTS omega_actor (
    actor_id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    owner_scope TEXT,
    aliases_json TEXT NOT NULL DEFAULT '[]',
    attestation_method TEXT,
    last_attested_at TEXT,
    attestation_receipt_id TEXT,
    status TEXT NOT NULL DEFAULT 'UNKNOWN' CHECK(status IN ('ACTIVE','SUSPENDED','REVOKED','UNKNOWN')),
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS omega_capability_grant (
    grant_id TEXT PRIMARY KEY,
    actor_id TEXT NOT NULL REFERENCES omega_actor(actor_id),
    capability TEXT NOT NULL,
    target_scope TEXT NOT NULL,
    decision TEXT NOT NULL CHECK(decision IN ('ALLOWED','LOCAL_ONLY','DENIED','UNKNOWN')),
    authority_ref TEXT NOT NULL,
    authority_digest TEXT,
    valid_from TEXT NOT NULL,
    valid_until TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE','SUPERSEDED','REVOKED'))
);

CREATE TABLE IF NOT EXISTS omega_worker_claim (
    worker_claim_id TEXT PRIMARY KEY,
    worker_id TEXT NOT NULL,
    boundary_key TEXT NOT NULL,
    claim_kind TEXT NOT NULL,
    acquired_at TEXT NOT NULL,
    expires_at TEXT,
    status TEXT NOT NULL CHECK(status IN ('ACTIVE','RELEASED','EXPIRED','CONFLICTED')),
    packet_sha256 TEXT,
    authority_ref TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_omega_worker_active_boundary
    ON omega_worker_claim(boundary_key)
    WHERE status='ACTIVE';

CREATE TABLE IF NOT EXISTS omega_world_entity (
    world_entity_id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    current_json TEXT NOT NULL DEFAULT '{}',
    source_claim_id TEXT REFERENCES omega_claim(claim_id),
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS omega_world_relation (
    world_relation_id TEXT PRIMARY KEY,
    cause_entity_id TEXT NOT NULL REFERENCES omega_world_entity(world_entity_id),
    effect_entity_id TEXT NOT NULL REFERENCES omega_world_entity(world_entity_id),
    relation_type TEXT NOT NULL,
    confidence REAL NOT NULL CHECK(confidence >= 0.0 AND confidence <= 1.0),
    observation_count INTEGER NOT NULL DEFAULT 0,
    source_observation_id TEXT REFERENCES omega_observation(observation_id),
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE','LEGACY','INVALIDATED','DISPUTED')),
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS omega_world_projection (
    projection_id TEXT PRIMARY KEY,
    projection_kind TEXT NOT NULL,
    basis_digest TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'CURRENT' CHECK(status IN ('CURRENT','STALE','SUPERSEDED','INVALID'))
);

CREATE TABLE IF NOT EXISTS omega_summary_cache (
    cache_key TEXT PRIMARY KEY,
    basis_digest TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    expires_at TEXT,
    payload_text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'CURRENT' CHECK(status IN ('CURRENT','STALE','INVALID'))
);

COMMIT;

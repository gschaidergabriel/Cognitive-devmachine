# KMP-UDB-U12-MATERIALIZATION-PAIR-CERTIFICATE-20260811

packet_id: `KMP-UDB-U12-MATERIALIZATION-PAIR-CERTIFICATE-20260811`
domains: `unifieddb, claygraph, frank, recovery, harness`
epistemic_class: `CURRENT_REPOSITORY_GAP_PLUS_IMPLEMENTED_CANDIDATE_PENDING_TARGET_EXECUTION`
status_hint: `OPEN_TARGET_VPS_AND_BOOTSTRAP_GATED`
origin_actor: `chatgpt-secondary`
provider: `OpenAI`
model: `GPT-5.6 Sol`
canonical_parent: `r2:04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
trigger: `unifieddb`
invoked_alias: `unifiedb`
program: `FRANK_V0_1`
work_package: `F-V01-04-UNIFIEDDB-STATE-CONTINUITY`

## Coordination / non-duplication

This packet is a post-run delta to the already-completed concurrent run:

`research_entity/trigger_runs/unifieddb/unifieddb-20260811T0417p0700-chatgpt-secondary-state-continuity/`

That parent run owns the semantic-lineage/execution-binding/external-recovery-floor/WAL-safety lane. U12 does not duplicate those candidates and does not alter their HOLD status.

U12 addresses a separate executable gap found in current target source: `runtime/state/apply_current_schema.py` explicitly states that UnifiedDB and ClayGraph are two physical SQLite databases, cross-file atomicity is not claimed, and interrupted/divergent materializations must fail closed. Before U12, normal `open_pair()` only required both files to exist and did not enforce the stated cross-file materialization truth gate.

## Hypothesis

A deterministic `MaterializationPairCertificate` bound to the exact ordered schema-source bytes for both physical databases can reject physically healthy but semantically mismatched UnifiedDB/ClayGraph pairs without pretending to provide cross-file atomic commit.

Certificate identity:

- protocol = `FRANK_MATERIALIZATION_PAIR_V1`;
- physical role = `UNIFIEDDB` or `CLAYGRAPH`;
- own ordered schema-chain SHA-256;
- shared pair SHA-256 binding protocol + both chain digests;
- lifecycle state = `UPDATING` or `CURRENT`.

Migration invalidates any pre-existing certificate to `UPDATING` before one-sided DDL work. It stamps `CURRENT` only after both schema chains complete and both SQLite integrity + foreign-key checks pass. Normal open verifies exact protocol/role/chain/pair/state and rejects absence or mismatch.

## Strongest counterhypothesis

Strict missing-certificate rejection can create an availability regression on an existing valid production pair that predates U12. Since current canonical materializations do not yet carry the certificate, merging enforcement before a Research-Entity-authorized one-time certification/migration path is proven would intentionally fail closed and could prevent normal state opening. Therefore target test success alone is insufficient for promotion.

A second counterhypothesis is that exact schema-source byte binding is too sensitive to semantically irrelevant source changes. If that causes unnecessary outages, the successor should bind a canonical schema/IR digest rather than weakening pair verification.

## Implemented target candidate

Repository: `gschaidergabriel/Dr.-Unterweger`

Branch: `chatgpt/unifieddb-u12-materialization-pair-gate-20260811`

Draft PR: `#282`

Head observed after CI-trigger push: `cb6a559e6aa3ec8845f7e24c0cf3909b7becd35f`

Changed surfaces:

- `runtime/state/apply_current_schema.py`
- `tests/unifieddb_u12_materialization_pair_gate.py`
- `.github/workflows/unifieddb-u12-materialization-pair-vps.yml`

No canonical Frank state is mutated by the candidate workflow.

## Falsifier

The disposable exact-current-schema test requires all four negative controls to remain physically healthy (`PRAGMA integrity_check == ok` on both files) while normal pair open rejects them:

1. shared pair digest divergence;
2. persisted `UPDATING` state representing interrupted one-sided materialization;
3. ClayGraph schema-chain digest divergence while shared pair metadata is otherwise present;
4. missing certificate protocol field / legacy partial certificate.

After restoring the exact certificate, normal pair open and certificate verification must succeed. The test also measures 100 normal `open_pair()` operations and reports p50/p95/p99/min/max/mean latency.

## Current execution truth

Target self-hosted workflow definition is committed, but no PR-triggered workflow receipt for the U12 head was observable through the GitHub connector at packet creation time.

Therefore:

`TARGET_VPS_RESULT = UNKNOWN_PENDING`

Do not infer PASS from workflow existence, branch creation, local source review, or absence of a visible failure.

## Relation to current storage safety

The existing target WAL-reset release guard remains independent and stronger for its scope. It must not be duplicated or weakened. U12 only handles pair-materialization identity/coherency. A pair with a valid U12 certificate still fails release if the physical SQLite WAL safety gate is unresolved.

## Promotion gates

U12 may advance beyond candidate only if all hold:

1. exact self-hosted Linux/X64 workflow passes on fresh ancestry;
2. negative controls reject while physical integrity remains `ok`;
3. measured pair-open overhead is acceptable;
4. a safe one-time certificate bootstrap/migration path is demonstrated against an existing current pair;
5. crash between Graph and Unified migration/stamping phases leaves subsequent normal open fail-closed and recovery deterministic;
6. rollback removes enforcement or restores last-known-good code/state without discarding evidence;
7. concurrent repository overlap is rechecked before merge;
8. existing WAL/storage and semantic-lineage gates remain independently satisfied.

## Architecture consequence

Keep the current physical split:

- UnifiedDB = authoritative semantic/logical state plane;
- ClayGraph = derived/rebuildable topology;
- cross-file atomicity = NOT CLAIMED;
- cross-file compatibility = explicit machine-verifiable admission gate;
- physical integrity = necessary but not sufficient for semantic pair admission.

This strengthens the parent run's `KEEP_DERIVED` ClayGraph decision without turning ClayGraph into truth authority or forcing physical consolidation.

## Re-entry

- `unifieddb`: add pair-materialization compatibility as a recovery/boot acceptance obligation.
- `claygraph`: publish/verify source materialization identity separately from activation/salience.
- `frank`: normal state open must not silently combine divergent physical state planes.
- `harness`: add interrupted pair migration + stale/missing certificate + recovery cases.
- `recovery`: certificate bootstrap and crash-window recovery must be tested before promotion.

No canonical migration, merge, whole-Frank acceptance, paid/final training, or self.root/Frank Harness mutation is authorized by this packet.

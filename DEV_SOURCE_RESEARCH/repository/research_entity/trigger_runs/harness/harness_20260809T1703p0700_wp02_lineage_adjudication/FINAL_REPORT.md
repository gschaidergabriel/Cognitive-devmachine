# Harness H-WP-02 Lineage Adjudication

Run: `harness_20260809T1703p0700_wp02_lineage_adjudication`
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Result

H-WP-02 has meaningful executable progress but currently contains two incompatible StateLedger lineages. Neither should be promoted unchanged.

- Lineage A: `research_entity/harness/reference_state_ledger.py`
- Lineage B: `research_entity/harness/reference/state_ledger.py`

The live-fusion receipt correctly identified this as a promotion blocker. This run narrowed the conflict with an exact repository differential probe plus a live-baseline compatibility audit.

## Exact differential finding

GitHub Actions `ubuntu-latest` / Python 3.12 executed `research_entity/harness/tests/wp02_lineage_differential.py` against both current repository modules. The output is preserved in `CI_DIFFERENTIAL_OUTPUT.json` and the exact execution receipt in `CI_EXECUTION_RECEIPT.json`.

1. Same final semantic state reached through different event grouping/history:
   - A semantic root: equal.
   - B `semantic_state_hash`: unequal.
2. Explicit typed-set permutation/dedup:
   - A root: unequal.
   - B `semantic_state_hash`: equal.
3. Idempotency payload collision with identical idempotency key + event id but changed semantic value:
   - A returns `IDEMPOTENT_REPLAY`; stored value remains the original value.
   - B raises `IdempotencyConflict`; stored value remains the original value.
4. Capability surface:
   - A has full verify + snapshot restore, no domain epochs.
   - B has domain epochs, no full verify or snapshot restore.

Interpretation: A has the cleaner history-independent current-content identity and stronger verification/recovery surface. B has the stronger typed canonicalization, domain epochs and idempotency conflict discipline. B currently overloads `semantic_state_hash` with epoch/history identity; A under-specifies typed collections/domain epochs and can silently classify a changed semantic payload as replay when the key/event-id pair is reused.

## Static implementation differences

### A strengths

- semantic state root excludes event id, timestamp, writer and provenance packaging;
- full event-chain/state verification;
- explicit snapshot export/restore;
- provenance-explicit synthetic recovery event.

### A gaps

- no typed `$kind=set` normalization;
- no domain epochs;
- no explicit CURRENT/RETRACTED/SUPERSEDED/QUARANTINED state-status surface;
- idempotent replay does not verify semantic payload/provenance equality after matching idempotency key + event id.

### B strengths

- typed set vs ordered collection canonicalization;
- domain epochs;
- separate semantic event, semantic chain, execution chain and trace-root concepts;
- semantic/provenance/source idempotency fingerprint;
- retract/supersede status semantics.

### B gaps

- `semantic_state_hash` depends on global epoch, domain epochs and semantic history chain, so equal current semantic content can hash differently solely because event grouping/history differs;
- no full verify method over current ledger/event/state chains;
- no snapshot restore method;
- execution-attempt/retry identity needs an explicit contract independent of semantic idempotency.

## Live frankv0.1 baseline compatibility

The current reference baseline is the accessible `gschaidergabriel/Dr.-Unterweger` repository, observed at commit `d916b98fb65dc62fbf3275d6a48dc52c2bfc2612` during this run.

Its repository semantic materializer advances a transaction/epoch root from prior root + source head + source content hash + idempotency + operations. H1 therefore cannot silently replace that observable identity. A corrected H1 ledger should retain it as a compatibility/version identity or document an explicit tested divergence.

## Adjudication

`MERGE_REQUIRED_NO_LINEAGE_SELECTED`

Recommended identity stack:

1. `baseline_transaction_root_hash`
   - preserve imported frankv0.1 observable transaction/epoch identity during H1 compatibility work.
2. `semantic_content_hash`
   - canonical current semantic content only;
   - independent of provenance, execution, event grouping and historical path;
   - typed collection/status semantics included.
3. `state_version_hash`
   - bind semantic-content hash to global/domain epochs plus semantic history/version identity.
4. `trace_root_hash`
   - bind state-version identity to provenance/source/execution/attempt chain.

This separates the questions “is the current meaning the same?”, “is this the same version/history?” and “is this the same execution trace?” instead of forcing one hash to answer all three.

## Merge requirements before H-WP-02 completion

- keep B typed canonicalization and domain epochs;
- keep B semantic/provenance/execution identity separation;
- import A full verification and snapshot restore;
- strengthen idempotency so semantic/provenance/source mismatch fails closed;
- model repeated execution attempts/retries as separate trace receipts rather than semantic-idempotency mutation;
- add expected-domain/read-set conflict guards for consequential commits;
- include timing/schedule/retry/recurrence metadata in execution receipts without allowing those signals to widen authority;
- retain the live-baseline transaction root as compatibility state until a tested divergence is approved.

## Execution boundary

Exact current-repository execution on GitHub Ubuntu CI is now complete and confirms the adjudication. This is stronger than the initial source-mirror probe but is still not target-developer-host or live-frank-baseline differential evidence.

Therefore:

- H-WP-02: still incomplete;
- H1 Reference Harness: still blocked/not PASS;
- exact GitHub Ubuntu differential: PASS;
- actual Ubuntu developer-host execution: pending;
- live frankv0.1 golden-corpus differential: pending;
- crash/recovery matrix: pending;
- no canonical scientific promotion;
- no paid/final training authorization.

## Next highest-information test

Build one merged candidate H1 oracle ledger from the evidenced invariants, then run:

- exact captured frankv0.1 transaction fixtures;
- same final state / different transaction grouping;
- set/order canonicalization;
- stale global vs domain/read-set epoch writers;
- idempotency payload collision;
- crash between mutation/receipt/epoch publication;
- checkpoint restore;
- dynamic Run ClayGraph binding;
- schedule/retry timing receipts;
- exact execution on the actual Ubuntu developer host.

Only after those results should the H-WP-02 oracle contract be frozen.

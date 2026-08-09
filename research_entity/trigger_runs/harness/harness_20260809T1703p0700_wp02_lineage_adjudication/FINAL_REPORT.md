# Harness H-WP-02 Lineage Adjudication

Run: `harness_20260809T1703p0700_wp02_lineage_adjudication`
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Result

H-WP-02 has meaningful executable progress but currently contains two incompatible StateLedger lineages. Neither should be promoted unchanged.

- Lineage A: `research_entity/harness/reference_state_ledger.py`
- Lineage B: `research_entity/harness/reference/state_ledger.py`

The current live-fusion receipt correctly identified this as a promotion blocker. This run narrows the conflict with a discriminating differential probe and a baseline compatibility audit.

## Differential finding

A source-mirror execution over the current formulas produced:

1. Same final semantic state reached through different event grouping/history:
   - A semantic root: equal.
   - B `semantic_state_hash`: unequal.
2. Explicit typed-set permutation/dedup:
   - A root: unequal.
   - B `semantic_state_hash`: equal.
3. Ordinary ordered-sequence permutation:
   - both detect semantic change.

Interpretation: A has the cleaner history-independent current-content identity. B has the stronger typed canonicalization and version/trace machinery. B currently overloads `semantic_state_hash` with epoch/history identity; A under-specifies typed collections/domain epochs and has a weaker idempotency collision check.

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
- idempotent replay accepts the same idempotency key + event id without verifying that the semantic payload/provenance is unchanged.

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

The current reference baseline is the accessible `gschaidergabriel/Dr.-Unterweger` repository, observed at commit `d916b98fb65dc62fbf3275d6a48dc52c2bfc2612` in this run.

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

This separates the questions "is the current meaning the same?", "is this the same version/history?" and "is this the same execution trace?" instead of forcing one hash to answer all three.

## Merge requirements before H-WP-02 completion

- keep B typed canonicalization and domain epochs;
- keep B semantic/provenance/execution identity separation;
- import A full verification and snapshot restore;
- strengthen idempotency so semantic/provenance/source mismatch fails closed;
- model repeated execution attempts/retries as separate trace receipts rather than semantic-idempotency mutation;
- add expected-domain/read-set conflict guards for consequential commits;
- include timing/schedule/retry/recurrence metadata in execution receipts without allowing those signals to widen authority;
- retain the live-baseline transaction root as compatibility state until a tested divergence is approved.

## Built artifact

`research_entity/harness/tests/wp02_lineage_differential.py`

This test imports and executes both current repository modules against the same small golden corpus. It is intentionally a differential observation test, not a lineage preference test.

## Execution boundary

This hosted ChatGPT worker cannot check out/execute the connected repository as a local process. A source-mirror mechanism probe was executed successfully here, but the new repository differential test itself remains `PENDING_EXACT_REPO_EXECUTION` on the Ubuntu/repo executor.

Therefore:

- H-WP-02: still incomplete;
- H1 Reference Harness: still blocked/not PASS;
- no canonical scientific promotion;
- no LoRA authorization.

## Next highest-information test

Execute `research_entity/harness/tests/wp02_lineage_differential.py` on the Ubuntu developer host, then extend the corpus to:

- exact captured frankv0.1 transaction fixtures;
- same final state / different transaction grouping;
- set/order canonicalization;
- stale global vs domain-epoch writers;
- idempotency payload collision;
- crash between mutation/receipt/epoch publication;
- checkpoint restore;
- dynamic Run ClayGraph binding;
- schedule/retry timing receipts.

Only after those results should one merged H1 oracle contract be frozen.

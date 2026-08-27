# KMP-UDB-V17-DUAL-LINE-CAUSAL-CLOSURE-20260811

packet_id: `KMP-UDB-V17-DUAL-LINE-CAUSAL-CLOSURE-20260811`
domains: `unifieddb, frank, gwt, harness, claycode, effect_authority, recovery`
epistemic_class: `CURRENT_TARGET_VPS_NEGATIVE_EVIDENCE_PLUS_REPOSITORY_ARCHITECTURE_ADJUDICATION`
status_hint: `OPEN_BLOCKING_PROMOTION`
origin_actor: `chatgpt-secondary`
provider: `OpenAI`
model: `GPT-5.6 Sol`
canonical_parent: `r2:04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
trigger: `unifieddb`
program: `FRANK_V0_1`
subject: `self.root / human-surface Frank v0.1`

## Atomic finding

The target repository currently contains two materially different V17 effect re-entry lines. They must be reconciled before any strong `provenance-bound re-entry/DONE` promotion claim.

1. The actively exercised `UNIFIEDDB_V17_EFFECT_REENTRY_DONE_CANDIDATE.sql` + `effect_terminal_runtime_v17_candidate.py` line binds effect id, attempt id and verified outcome hash, but stores episode/signal/causal/delta support identities as free symbols and does not structurally require a current V15/V16 execution.
2. A separate richer `UNIFIEDDB_V17_PROVENANCE_BOUND_EFFECT_COMPLETION.sql` + `UNIFIEDDB_V17_1_CAUSAL_ADMISSION_CLOSURE_CANDIDATE.sql` line adds exact execution/lease, provider outcome, GWT-use, prediction-outcome, causal-credit, semantic-delta and optional snapshot closure.
3. The richer V17.1 line has a target-VPS workflow definition but no persisted `runtime/vps_unifieddb/frank_effect_reentry_v17_1_causal_admission_v1/LATEST.json` receipt was observable on current main during this adjudication. Therefore it is candidate evidence, not a validated replacement.

## Direct falsification evidence

Current target-VPS negative receipt `f649ce7ab8249c9dbc61ad7018804204ade53cb5` confirms the active V17 line can accept fabricated episode/signal/causal/delta identifiers and reach terminal DONE while V15 presence remains IDLE epoch 0, V16 execution remains unbound, and canonical GWT/causal/delta support rows are absent. Its own verifier reports DONE_VALID and recovery COMPLETE.

This falsifies any interpretation of the active V17 result as full causal/provenance closure. The narrower verified claim that remains supported is: exact effect attempt + verified effect outcome can be bound into the candidate terminal chain. It does not prove that the re-entry support identities are real, causally related, or owned by the current self.root execution.

## Existing stronger candidate

`UNIFIEDDB_V17_1_CAUSAL_ADMISSION_CLOSURE_CANDIDATE.sql` already encodes the important relational closure obligations and should be treated as the primary consolidation source rather than reinvented as a third V17 family. Its guards require:

- exact current V15/V16 execution and lease epoch;
- exact verified effect/provider outcome identity;
- receiver receipt with `used=1` and `local_effect=1` for the same attention episode/effect;
- verified prediction outcome carrying the same provider receipt;
- non-`CORRELATED_ONLY` causal credit targeting the same effect and same GWT cycle;
- explicit semantic-delta admission at a canonical state epoch;
- re-entry authority receipt and optional snapshot/epoch match;
- current execution again at terminalization.

## Counterhypothesis

The richer V17.1 candidate may still be too strict, incomplete, or stale relative to the current effect-provider path. In particular an explicit typed `NO_LEARNING` effect completion may not require a semantic-delta admission, while it still must require real current execution and real causal/GWT support sufficient for truthful re-entry. Therefore simply promoting V17.1 unchanged is not justified.

## Required reconciliation experiment

Build one successor of the active V17 line, not a third parallel architecture, by porting only the independently justified V17.1 closure constraints into the currently exercised provider/effect path. Run a differential matrix on the accepted target VPS:

- valid current execution + real same-cycle GWT use + verified provider outcome + direct causal credit + admitted delta -> ACCEPT;
- valid current execution + explicit typed NO_LEARNING + real same-cycle GWT/effect-use receipt and verified outcome -> ACCEPT only if the no-learning contract explicitly waives delta/credit and the verifier records that waiver;
- fabricated episode/signal/causal/delta -> REJECT;
- V15 IDLE / V16 unbound -> REJECT;
- stale lease epoch / successor execution -> REJECT;
- cross-spliced but individually valid GWT, prediction, credit, delta or snapshot rows -> REJECT;
- rollback/restart between OUTCOME_SUCCEEDED, REENTERED and DONE -> deterministic fail-closed recovery;
- verify SQLite integrity/FK, p50/p95/p99 latency, RSS, transaction/write amplification and exact source/blob hashes.

The old active-V17 positive integration must be relabeled as `EFFECT_OUTCOME_BINDING_PASS`, not `FULL_CAUSAL_REENTRY_CLOSURE_PASS`, until this discriminator passes.

## Cross-branch feedback

- `frank`: do not count active V17 terminal PASS as proof of complete provenance-bound self.root re-entry.
- `gwt`: require actual receiver-use/effect receipts, not free episode/signal labels.
- `claycode`: encode `LEARNING` versus `NO_LEARNING` terminal semantics explicitly so storage gates do not infer authority from nullable strings.
- `harness`: add fabricated-support, cross-splice, stale-execution and crash/restart cases to the direct Frank v0.1 gate.
- `unifieddb`: consolidate the two V17 families; keep the richer V17.1 line as source evidence, but do not promote without exact-current target-VPS receipt.

## Promotion boundary

`OPEN_BLOCKING_PROMOTION`.

No canonical migration or whole-Frank acceptance change is authorized by this packet. The next promotion requires exact-current target-VPS differential evidence on one consolidated V17 successor plus crash/restart/replay evidence. Training authorization is unchanged.
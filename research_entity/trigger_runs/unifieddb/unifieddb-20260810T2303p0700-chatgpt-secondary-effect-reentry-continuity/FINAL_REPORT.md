# UnifiedDB — Effect/Re-entry/Terminal Continuity Run

Run: `unifieddb-20260810T2303p0700-chatgpt-secondary-effect-reentry-continuity`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol / temporary Clay research worker  
Program: `FRANK_V0_1`  
Primary component: `F-V01-04-UNIFIEDDB-STATE-CONTINUITY`  
Adjacent component: `F-V01-09-EFFECT-AUTHORITY`

## Executive result

This run produced a concrete target-VPS result, not only architecture prose.

The baseline V14 lifecycle is not a valid terminal causal closure mechanism: an empty/unbound re-entry can be accepted and `REENTERED` is treated as complete without an explicit `DONE` receipt. That negative baseline was already confirmed on the accepted Hostinger Ubuntu self-hosted runner.

An additive V17 candidate was then hardened so that the local lifecycle layer binds the exact canonical effect, attempt and verified outcome, disables legacy arbitrary re-entry, keeps `REENTERED` nonterminal until a separate `DONE` receipt, survives a restart between re-entry and DONE, rejects duplicate DONE, and rolls back without damaging V14/V16. The corrected candidate passed that bounded target-VPS differential.

That success did **not** justify promotion. A second target-VPS discriminator proved that the simple V17 candidate can still accept fabricated GWT/causal/delta support identities and terminalize while V15 presence remains IDLE and V16 execution context is unbound.

The run then tested the richer V17 schema. Its foreign keys and row-existence checks still do not establish one causal chain. On the accepted target VPS, valid-but-unrelated rows were cross-spliced: the causal credit referred to an unrelated **unverified** prediction outcome, the semantic record was merely an unrelated `CURRENT` record, and the support snapshot hash had no structural target. The re-entry and terminal `DONE` were nevertheless admitted while SQLite integrity and foreign-key checks remained clean.

**Core finding:** database referential integrity is necessary but not sufficient for cognitive causal integrity. UnifiedDB must encode the *relation between evidence objects*, not merely the existence of each object.

## Target-VPS evidence

1. `FRANK-V01-EFFECT-REENTRY-GAP-31406627821`
   - V14 empty/unbound re-entry accepted.
   - `REENTERED` treated as complete.
   - no explicit DONE state.
   - wall shadow 0.12 s; max RSS 23,936 KiB.

2. `FRANK-V01-V17-SCHEMA-GAP-31407772002`
   - initial V17 accepted re-entry binding on RESERVED.
   - accepted terminal DONE on RESERVED.
   - accepted wrong attempt/outcome binding.
   - wall shadow 0.15 s; max RSS 24,064 KiB.

3. `FRANK-V01-EFFECT-REENTRY-DONE-V17-CANDIDATE-31408227242`
   - corrected local V17 layer passed exact attempt/outcome binding checks.
   - legacy unbound re-entry disabled.
   - `REENTERED != COMPLETE` before DONE.
   - restart between re-entry and DONE recovered as nonterminal.
   - duplicate DONE rejected.
   - additive rollback preserved V14/V16 and removed candidate tables.
   - candidate remained noncanonical and performed no external provider effect.
   - wall shadow 0.14 s; max RSS 24,320 KiB.

4. `FRANK-V01-V17-SUPPORT-BINDING-GAP-31408220117`
   - simple V17 accepted fabricated episode/signal/causal/delta identities.
   - accepted DONE while V15 presence was IDLE epoch 0.
   - accepted DONE without V16 execution context.
   - its own verifier still called the chain valid/complete.
   - wall shadow 0.12 s; max RSS 24,320 KiB.

5. `FRANK-V01-V17-RELATIONAL-CROSS-SPLICE-GAP-31408872635`
   - richer V17 accepted a cross-spliced support set.
   - causal credit pointed to an unrelated unverified prediction outcome.
   - semantic record was CURRENT but unrelated to the effect causal chain.
   - support snapshot hash had no structural target.
   - terminal DONE was accepted.
   - `PRAGMA integrity_check` and foreign-key checks remained clean.
   - wall shadow 0.15 s; max RSS 24,360 KiB.

No external provider-side effect was performed in these experiments.

## Hypothesis adjudication

| ID | Hypothesis | Result |
|---|---|---|
| H1 | V14 already closes verified outcome -> provenance-bound re-entry -> terminal completion | **REFUTED on target VPS** |
| H2 | additive exact attempt/outcome binding + explicit DONE repairs the local lifecycle gap without rebuilding V14 | **SUPPORTED as candidate sublayer on target VPS** |
| H3 | simple V17 also binds current execution and canonical GWT/causal/delta support | **REFUTED on target VPS** |
| H4 | richer V17 FK/support checks establish one causal chain | **REFUTED on target VPS** |

The strongest counterhypothesis for H4 was that existing `outcome_ref`, `target_key` and foreign-key existence checks were enough. The cross-splice discriminator falsified that counterhypothesis.

## Architecture decision

**Do not add either V17 variant to the canonical migration chain.**

Retain the useful local mechanisms discovered by the passing candidate differential:

- exact `effect_id + attempt_id + verified outcome_hash` binding;
- legacy unbound re-entry fail-closed;
- nonterminal `REENTERED`;
- explicit durable `DONE` receipt;
- duplicate-DONE rejection;
- restart distinction between `REENTRY_PENDING` and `COMPLETE`;
- additive/reversible migration surface.

But the next candidate must close the entire causal relation structurally:

`current execution generation`
`-> exact effect reservation/attempt`
`-> verified provider outcome`
`-> exact GWT attention episode`
`-> receiver reconstructed + used + local_effect receipt`
`-> verified causal-credit outcome derived from that same effect/GWT chain`
`-> exact admitted semantic delta OR explicit typed no-learning receipt`
`-> real support snapshot/receipt identity`
`-> provenance-bound re-entry`
`-> DONE receipt`

The crucial change is that these must be **joined by shared causal identities**, not independently checked for row existence.

## Store architecture

The preferred direction remains a logically unified, Clay-native authoritative state plane with measured physical separation:

- authoritative SQLite/UnifiedDB: identity, epochs, effect state, event history, execution fences, GWT-use receipts, causal/admission receipts, recovery metadata;
- ClayGraph: derived/rebuildable topology and query acceleration only;
- vector/activation/ranking indexes: derived salience/retrieval surfaces only;
- provider state: physically external and independently verified, with provenance/hash/receipt identity persisted in UnifiedDB.

Physical all-in-one consolidation remains `HOLD`: this subcycle produced no measurement showing that broader consolidation beats the extra common-mode/recovery risk.

## External research consequence

Official SQLite documentation supports keeping this repair additive while it is experimental: SQLite deliberately exposes limited direct `ALTER TABLE` operations, and more complex schema changes generally require a new-table/copy/drop/rename procedure; foreign-key behavior can also affect rename/drop operations. The project therefore avoids rebuilding the V14 parent table merely to test a new invariant. This is a reversible engineering choice, not a claim that additive side tables are universally superior.

SQLite transactional/foreign-key integrity is also deliberately treated as a lower layer than Frank causal integrity. The cross-splice result demonstrates why a normal database integrity pass cannot be used as a cognitive-causal acceptance test.

## Mandatory dimensions

- Semantic correctness: local V17 sublayer PASS; full causal closure FAIL.
- Temporal/provenance correctness: full closure FAIL under cross-splice.
- Selection integrity: FAIL for terminal causal authority under cross-splice.
- Replay/restart: partial PASS for restart between re-entry and DONE; hard-crash matrix still open.
- Transaction/effect atomicity: partial candidate evidence; exact full-chain atomicity remains open.
- Migration/rollback: simple additive candidate rollback PASS; canonical migration remains blocked.
- p50/p95/p99: not measured; only single-run wall shadows exist.
- write/read amplification: not measured.
- storage amplification: not measured.
- concurrency/lock contention: not measured.
- hard-crash recovery/rebuild time: not measured.
- graph/vector/FTS retrieval quality: not applicable to this bounded terminalization subcycle.
- IPC/serialization savings of physical consolidation: not measured.
- model token/context cost: not measured.

Unknown values remain UNKNOWN; the single-run wall times are not reported as latency distributions.

## Next discriminating work

1. Add explicit support-relation receipts/keys so causal credit must point to a **verified** outcome belonging to the same effect/GWT-use chain.
2. Bind admitted semantic delta to that exact causal credit/re-entry admission; represent no-learning explicitly and separately.
3. Replace free `support_snapshot_hash` authority with an FK/receipt-backed snapshot identity, or remove it from terminal authority.
4. Bind terminalization to immutable V15/V16 execution generation and stale-writer fencing.
5. Rerun the exact cross-splice attack and require rejection while a truthful chain still passes.
6. Run hard-crash cutpoints at outcome -> support-binding -> re-entry -> DONE and verify no false COMPLETE/duplicate provider effect.
7. Run concurrent terminalization/idempotency/lock tests and measure p50/p95/p99, resource and amplification distributions against V14/V16.
8. Only after those pass, consider canonical migration; then rerun current-source end-to-end provider uncertainty/reconciliation and final effect-authority acceptance.

## Promotion

`NO_PROMOTION` for full V17 / UnifiedDB effect closure.

The run does promote one narrower scientific result: **exact attempt/outcome binding + explicit nonterminal re-entry + terminal DONE is a useful local mechanism, but it is insufficient unless the whole causal-support relation is structurally closed.**

Frank v0.1 acceptance is not claimed. Training was not started or authorized by this run.

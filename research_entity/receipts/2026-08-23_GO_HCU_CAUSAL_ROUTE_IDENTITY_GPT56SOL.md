# GO Receipt — HCU causal route identity

Date: 2026-08-23  
Organ: ChatGPT GPT-5.6 Sol temporary Clay organ  
Trigger: `go`  
Claim scope: source/mechanism + isolated component regression only; no HCU/EntityOS runtime acceptance.

## Authority refresh

- Fast bootstrap supplied to the session was treated as cache only.
- Research `main` initially observed at `2178d9b0a062636231ff0e3c533417c2268a7a96` and advanced during this run to `2fb3953956f35bc12f75d0b231fad603a278d037`.
- Newer authority resolves the active program to EntityOS with HCU as the integrated cognition/compute architecture; Xeno/XCU/Mini Entity names are compatibility/research aliases where migration is not yet safe.
- Canonical state/evidence remains deterministic and EffectGate/EffectJournal remains the real-effect boundary.

## Frontier selected

Draft PR #1263 (`hcu: reactive provider-independent world-model substrate`) contained the live HCU reactive router candidate. The current-main supervisor identified a causal identity gap: a route digest derived only from generation and routing output could alias materially different input events whenever both events selected the same lanes/projection.

The PR was also substantially behind current `main`, so no merge/promotion credit was granted.

## Exactly one unusual experiment

Counterexample: construct two materially different `HCU_REACTIVE_EVENT/v1` inputs whose novelty values differ but which cross the same thresholds and select the same route.

Prediction under the old formula:
- identical route result + generation -> identical `decision_sha256` despite different causal events.

Prediction under causal event binding:
- canonical event digests differ;
- route decision digests differ;
- exact replay of the same event remains stable.

Observed mechanism result:
- old formula produced the same route lanes and the same decision digest for the two events;
- event-bound formula separated the event and route identities while preserving deterministic replay.

This supports the supervisor counterhypothesis that routing-output identity alone is insufficient for causal replay/audit.

## Parallel fusion / no stale overwrite

During the run PR #1263 advanced concurrently. The router acquired `HCU_CAUSAL_ROUTE_IDENTITY/v1` with canonical `event_sha256` bound into the route digest, and the test suite acquired `test_distinct_events_with_same_route_do_not_alias_decision_identity`.

A stale attempt to update the same test file was rejected by GitHub with HTTP 409 because the blob SHA had changed. The write was not forced. The new content was refreshed instead, avoiding a parallel overwrite.

Observed PR head after fusion: `ca1d222a735d1ce20b701c208b5d175db14fc059`.

## Isolated regression reproduction

Using the retrieved current router and test content from that PR head in an isolated Python execution surface:

- `py_compile`: exit 0;
- reactive-router unit suite: 8/8 PASS, exit 0;
- same event with reversed mapping key order remained deterministic;
- distinct events selecting the same route produced distinct `event_sha256` and `decision_sha256`.

Execution caveat: Python startup emitted an unrelated `artifact_tool` spreadsheet-runtime warmup timeout. The HCU compile and unittest processes nevertheless completed with exit 0. This does not provide exact packaged-HCU runtime evidence.

A scoped evidence comment was also written to PR #1263 as issue comment id `5387060158`.

## Remaining blocker

The HCU package still has no positive bound local checkpoint/tokenizer/runtime capability record. The current contracts explicitly require exact checkpoint/tokenizer/runtime identity before HCU promotion. Therefore the next safe step is not to invent an engine name inside the route digest.

Required next sequence:

1. define a positive fail-closed local HCU engine capability/admission record;
2. bind exact checkpoint, tokenizer, runtime/build identity and admitted engine class;
3. have scheduler/route resolution consume that record;
4. bind canonical resolved engine identity/class together with event identity and routing result into the causal route/inference receipt;
5. require downstream inference to echo event + route + engine identity;
6. rebase/fuse PR #1263 onto current `main` before any merge/promotion;
7. rerun exact authorized-isolated acceptance after rebase.

## Explicit non-claims

No credit is granted here for:
- exact bundled ~0.8B runtime;
- provider-free HCU boot;
- HCU runtime fit or throughput;
- Global J-Space causal use;
- controllable emergence;
- target VPS performance;
- whole EntityOS acceptance.

Together API remains forbidden. No VPS/self-hosted/production-host test was used.

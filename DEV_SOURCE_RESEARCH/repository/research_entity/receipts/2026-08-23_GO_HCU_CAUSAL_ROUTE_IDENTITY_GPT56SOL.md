# GO Receipt — HCU causal route identity + serializer-profile binding

Date: 2026-08-23  
Organ: ChatGPT GPT-5.6 Sol temporary Clay organ  
Trigger: `go`  
Claim scope: source/mechanism + isolated component regression only; no HCU/EntityOS runtime acceptance.

## Authority refresh

- The session bootstrap was treated as cache only and current GitHub authority was refreshed before material claims.
- Authority converged during this run from older ClayVerse/Xeno-facing cache/state to the current law: **EntityOS is the sole product/system identity and HCU is the sole integrated cognition/compute architecture**. Xeno/XCU/Mini Entity/MicroEntity remain compatibility, research-alias, path, hash, receipt, or historical-provenance names only where exact migration requires them.
- Canonical durable state/evidence remains outside model cognition; EffectGate/EffectJournal remain the only real-effect authority.
- Current build/test/experiment/runtime credit remains authorized-isolated-sandbox-only. VPS/self-hosted/production-host testing, Together, and paid fallback remain forbidden under current authority.

## Frontier selected

Draft PR #1263 (`hcu: reactive provider-independent world-model substrate`) was the strongest nonduplicate HCU route/Entry candidate.

Initial source counterhypothesis: a route digest derived from routing output + generation could alias materially different causal events when both events selected the same lanes/projection.

During the same macro-cycle the branch and supervisor advanced concurrently through:

- immutable causal event digest binding;
- positive fail-closed internal-provider/engine admission;
- exact engine artifact SHA-256 plus independently supplied admitted-artifact registry;
- router-policy digest;
- engine-identity digest;
- route identity bound to event + policy + engine + deterministic route result;
- downstream inference echo checks;
- Typed Entry Fabric source/tests preserving ingress/causal/admission identity into `HCU_REACTIVE_EVENT/v1`.

No parallel second router was created.

## Exactly one unusual experiment

The one unusual experiment for this user-triggered `go` was the same-route causal-alias stress:

- construct two materially different `HCU_REACTIVE_EVENT/v1` inputs;
- choose values that cross the same thresholds and therefore select the same route;
- compare the old route-only identity formula with causal-event-bound identity.

Observed mechanism result:

- old formula produced the same route lanes and the same decision digest for the two distinct events;
- event-bound identity produced distinct event and route digests;
- exact replay remained stable.

This supports the supervisor counterhypothesis that routing-output identity alone is insufficient for causal replay/audit.

Later artifact-rotation, serializer-echo, and other checks in this run are regression-only follow-ups and are not additional unusual experiments.

## Parallel coordination / stale-write behavior

Multiple concurrent updates landed on PR #1263 while this run was active.

- An early stale test-file update was rejected by GitHub with HTTP 409 and was not forced.
- A later serializer-profile update was also rejected with HTTP 409 after the router changed concurrently and was not forced.
- After refresh, a serializer patch based on an older full-file snapshot temporarily omitted a newly added independent engine-artifact registry. This regression was detected immediately by comparing the current tests with the prior exact router and was repaired before final evidence.

Repair commits on the draft branch:

- `4eadd47eb944f86d6659b02dcb283661b0876bd1` — restore independent engine-artifact registry while binding serializer profile;
- `dc079f3062b2e5d6614360611c3845e1bea50c75` — regression coverage for serializer + exact engine receipt binding.

## Serializer / cross-language identity finding

The current router uses Python `json.dumps(... sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)` for hash input serialization.

RFC 8785 JCS provides an invariant JSON representation for cryptographic hashing/signing using I-JSON constraints, ECMAScript primitive serialization, and deterministic property sorting. Therefore Python-local deterministic serialization must not silently be promoted to heterogeneous Entry-Fabric identity proof.

The branch now binds the explicit implementation-scoped profile:

`HCU_PYTHON_JSON_DUMPS_SORT_KEYS_UTF8/v1`

into:

- event identity envelope;
- router policy;
- engine identity;
- route decision;
- `RouteDecision` receipt;
- downstream inference echo validation.

This is a fail-closed provenance improvement, **not** a JCS implementation and not cross-language acceptance. A future admitted RFC 8785 JCS or explicitly versioned typed equivalent must use a distinct profile and independent compatibility evidence.

## Isolated component regression

Exact branch head used for the final reconstructed component regression at that point:

`dc079f3062b2e5d6614360611c3845e1bea50c75`

Using the exact router/test content written at that head in an isolated Python execution surface:

- `py_compile`: exit 0;
- reactive-router suite: **18/18 PASS**, exit 0;
- independent engine-artifact registry mismatch fails closed;
- missing admitted-artifact registry fails closed for model activation;
- distinct events selecting the same route remain distinct;
- admitted engine artifact rotation changes engine/route identity without changing causal event identity;
- inference receipt must echo event + route + exact engine + serializer profile;
- wrong serializer profile fails closed.

Execution caveat: Python startup emitted an unrelated `artifact_tool` spreadsheet-runtime warmup timeout. The HCU compile and unittest processes themselves completed with exit 0. This does not establish packaged-HCU or whole-EntityOS runtime acceptance.

## Other durable deltas in this go

- PR #1263 received a scoped evidence comment (issue comment id `5387060158`).
- `the artefact/README.md` was corrected on `main` from stale Xeno-facing work-selection language to current EntityOS/HCU authority while preserving compatibility names where required.
- `research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md` was corrected on `main` so future visible status routing no longer reintroduces Xeno/XCU as current product/architecture authority.

## Remaining gates

1. Keep PR #1263 Draft and zero whole-runtime credit until exact current-head authorized-isolated execution is available.
2. Admit a true heterogeneous Typed Entry canonicalization profile: RFC 8785 JCS or an explicitly versioned typed equivalent; prove identical digest generation from independent admitted implementations before cross-language identity is claimed.
3. Bind real local ~0.8B checkpoint + tokenizer + runtime/build bytes to the admitted HCU engine artifact identity, not merely a placeholder digest.
4. Bind the actual downstream inference receipt producer, not only the assertion contract.
5. Rebase/fuse the draft candidate against current `main` before merge/promotion.
6. Rebuild and digest-bind the compatibility package snapshot from the exact settled head.
7. Then measure script-only hit rate, selective-inference savings, GRID10/COGSIM10, and only later bounded WM_TEST/NESTED_SIM under measured discriminators.

## Explicit non-claims

No credit is granted here for:

- exact bundled/local ~0.8B runtime;
- provider-free HCU boot/runtime continuity;
- HCU throughput, capacity, or target-hardware fit;
- cross-language Entry identity;
- Global J-Space causal use;
- controllable emergence;
- target VPS performance;
- whole EntityOS acceptance.

Source/component/historical PASS does not imply EntityOS/HCU runtime PASS.

# GO — Live Fusion Strong Mesh V1.4 Shadow Candidate — 2026-08-10

Status: RESEARCH_CANDIDATE_NOT_PROMOTED  
Actor: chatgpt-secondary / OpenAI / GPT-5.6 Sol  
Parent: PR #156 Live fusion re-entry V1.3 candidate, branch observed advancing during this run; V1.4 branch was finally forked from parent head `2f7d34545cdd86b2c289f5b7697633b5d7814d6f`  
Goal: Frank v0.1 voll lauffähig auf Andreas Ubuntu developer system

## Fresh-state correction

The run initially found two gaps in an older PR #156 head: missing `affected_work/affected_claims` runtime routing and ACK being conflated with semantic resolution. Before durable write, the PR head was re-read and had advanced. V1.3 already repaired both issues. Those planned changes were therefore discarded rather than duplicated.

Remaining V1.3 routing gap: the protocol asks ClayGraph to project semantic dependencies, but runtime routing still activates only from exact branch/key/work/claim overlap. In addition, every nonzero branch overlap becomes an active checkpoint delivery even when impact and urgency are very low. This leaves two complementary risks:

1. hidden cross-branch causal dependencies can remain `INDEX_ONLY` unless the producer already knows the exact affected work/claim/key;
2. same-branch low-signal chatter can still create active delivery load.

## Hypothesis / counterhypothesis

H1: a current, provenance-bound derived dependency projection used only for shadow routing can recover hidden causal reach while permitting low-signal branch-only chatter to remain index-only.

H0 / strongest counterhypothesis: dependency expansion adds false-positive edges, stale topology and delivery amplification; exact V1.3 routing is safer and the apparent rescue is fixture overfitting.

Therefore V1.4 is shadow-only. No candidate route changes V1.3 delivery or effect authority.

## External live research delta

- GoAgent (arXiv:2603.19677, 2026) models task-relevant groups explicitly and uses a conditional information bottleneck to reduce redundant communication/noise. This supports testing causal reach and compression together rather than maximizing edge count.
- Autonomous Topology Mutation (arXiv:2607.20488, 2026) gates runtime topology changes with capability/state invariants and shadow-before-live validation. This directly supports keeping V1.4 routing non-live until measured.
- MCP 2026-07-28 makes requests self-describing and header-routable rather than depending on hidden transport session state. For Clay this is implementation-pattern evidence for explicit routing metadata, not an architecture truth claim.

External sources are design evidence only; they do not promote V1.4.

## Candidate

Added `StrongMeshShadowRouter` layered on V1.3. It consumes a disposable `DependencyProjection` bound to worker id, graph epoch, state hash and provenance. Current dependency key/work/claim overlap can upgrade otherwise invisible routes. Stale projections cannot upgrade. Low-impact + low-urgency + non-conflicting branch-only overlap may be shadow-demoted to `INDEX_ONLY`.

The candidate emits `ShadowRouteDecision` containing exact base and candidate route classes, relevance, direct/dependency matches, projection identity and change class. It never writes live V1.3 routing state.

## Local deterministic tests

Command: `python3 -m unittest -v test_live_fusion_strong_mesh_v14.py`

Result: 11/11 PASS.

Coverage includes direct-work preservation, low-signal branch-only demotion, high-impact preservation, cross-branch dependency rescue, stale-projection fail-conservative behavior, worker mismatch fail-closed, historical-only no-upgrade, high-impact hidden dependency interrupt, observable shadow summary, the false-current-dependency containment control, and the mandatory OOB lesion/rescue.

The local test harness reconstructed the exact V1.3 scoring formula observed at parent head `668cedc5b8d89df1a77e40bc0aac916986d5f7eb`; compare showed the final fork head added V1.3 tests/workflow/protocol only and did not change `live_fusion_reentry_v13.py`. Full exact-parent import remains a CI gate.

## Strongest counterhypothesis result — false dependency

A deliberately wrong but `current=true` dependency projection can produce a candidate false-positive interrupt. This is an expected negative result, not hidden: dependency membership alone is not truth. The V1.4 safety result is containment: the exact V1.3 route remains `INDEX_ONLY`, the candidate route is shadow-only, and `ShadowRouteDecision.authority` is explicitly `SHADOW_ROUTING_ONLY_NO_TRUTH_OR_EFFECT_AUTHORITY`.

This means real false-dependency rate and shadow precision must be measured before any live admission. A current timestamp/epoch alone is insufficient evidence that an edge is causally useful.

## Synthetic matched routing fixture

48 event/worker pairs, 8 deltas x 6 workers, frozen adjudicated required-active and required-interrupt pairs. Evidence class: `SYNTHETIC_MECHANISM_ONLY`.

| Metric | V1.3 exact overlap | V1.4 shadow |
|---|---:|---:|
| Required active recall | 6/11 = 54.5% | 11/11 = 100% |
| Active precision | 6/8 = 75% | 11/11 = 100% |
| Required interrupt recall | 2/6 = 33.3% | 6/6 = 100% |
| Interrupt precision | 2/2 = 100% | 6/6 = 100% |
| Extra active deliveries | 2 | 0 |
| Dependency reach upgrades | n/a | 5 |
| Low-signal demotions | n/a | 2 |

These numbers are intentionally not generalized beyond the fixture and do not include the separate adversarial false-edge control.

## Exactly one GO out-of-box experiment

`OOB_HIDDEN_DEPENDENCY_LESION_RESCUE`:
- lesion every direct branch/key/work/claim match for a high-impact conflict;
- V1.3 exact overlap -> `INDEX_ONLY`;
- restore only one current derived work dependency;
- V1.4 shadow -> `INTERRUPT_NEXT_SAFE_POINT`;
- PASS locally.

Interpretation: a derived dependency edge can recover a deliberately hidden route. It does not prove real-corpus benefit; false-dependency and stale-topology controls remain mandatory.

## Architecture delta

Candidate only:

`LiveFusionDelta -> V1.3 causal transport` remains unchanged.

Add shadow path:

`current UnifiedDB + current ClayGraph + worker subscription -> epoch-bound DependencyProjection -> V1.4 ShadowRouteDecision -> matched validation -> optional later live admission`

The design strengthens semantic connectivity without making the physical/active mesh denser by default.

## Promotion blockers

- exact parent V1.3 import/test on CI;
- current active-worker dependency projection from real UnifiedDB/ClayGraph;
- real corpus of missed/irrelevant worker re-entry cases;
- real false-dependency rate / precision control;
- active delivery amplification and p50/p95/p99 latency/resource measurements;
- parent crash/restart/replay invariants preserved;
- Hostinger Ubuntu receipt;
- rollback and no critical recall regression.

No Frank Harness mutation, no canonical architecture promotion, no target-hardware acceptance and no training authorization are claimed.

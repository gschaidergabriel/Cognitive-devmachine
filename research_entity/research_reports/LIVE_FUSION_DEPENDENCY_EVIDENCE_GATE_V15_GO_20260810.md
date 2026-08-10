# Live Fusion Dependency Evidence Gate V15 — GO research candidate

Date: 2026-08-10
Actor: chatgpt-secondary / OpenAI / GPT-5.6 Sol
Role: temporary Research Entity worker; not Frank
Base main at branch creation: `4599c82b525fd9af987328d666dfc250239d54bf`
Canonical parent: revision 2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
Status: CANDIDATE_NOT_PROMOTED / SHADOW_ONLY

## Why this delta exists

The current live-fusion lineage already has three useful but unpromoted pieces: PR #156 causal re-entry/ACK/resolution, PR #165 work lease/fencing, and PR #166 dependency-aware strong-mesh shadow routing. Latest Hypofusion R5 additionally requires completeness-gated adaptive routing, anti-entropy and explicit false-dependency controls.

The remaining narrow failure mode is that `projection_current=true` does not imply that a dependency edge is causally trustworthy. A current associative/heuristic ClayGraph relation can be useful for visibility while still being wrong. If every such edge may upgrade a high-impact hidden conflict to `INTERRUPT_NEXT_SAFE_POINT`, stronger networking can amplify false interrupts and synchronize workers around a false premise.

V15 therefore adds a shadow-only evidence gate after the parent routing proposal. It does not create another transport or truth plane.

## Candidate rule

- direct parent routes are preserved;
- stale or worker-mismatched dependency projections cannot upgrade routing;
- dependency-only interrupt requires at least one current hard witness: `DECLARED_WORK_DEPENDENCY`, `VERIFIED_CAUSAL`, `REPLAY_CONFIRMED`, or `AUTHORITATIVE_REFERENCE`;
- soft/unknown dependency evidence may keep a high-impact event visible at `NEXT_CHECKPOINT` and request reconciliation, but cannot by itself mint blocking power;
- verified reconciliation may later promote a soft witness to hard;
- all outputs remain coordination/shadow evidence only, never truth or effect authority.

## Executed local mechanism tests

Command:

`python3 -m unittest -v test_live_fusion_dependency_evidence_gate_v15.py`

Result: **10/10 PASS** in the local Linux tool environment.

Covered falsifiers include soft-edge false interrupt, hard causal witness, declared work dependency, stale hard witness, stale projection, direct-route preservation, worker mismatch, non-blocking checkpoint verification, summary observability, and the out-of-box false-edge lesion/rescue experiment.

Evidence class: `LOCAL_DEVELOPMENT_MECHANISM_TEST`; this is not committed-byte Ubuntu/Hostinger or Andreas target evidence.

## Synthetic false-edge stress

Command:

`python3 benchmark_live_fusion_dependency_evidence_gate_v15.py`

Frozen parameters: seed 20260810, N=100000, true edge rate 0.50, hard witness conditional on true edge 0.80, soft witness conditional on true edge 0.15, soft false edge 0.05.

Observed on this synthetic mechanism fixture:

- parent-style strong dependency interrupt: 50,247 interrupts; 2,560 false interrupts; interrupt precision 0.94905; interrupt recall vs true edges 0.94901;
- V15 evidence gate: 40,271 interrupts; 0 false interrupts; 9,976 checkpoint verifications; interrupt precision 1.0; immediate interrupt recall vs true edges 0.80143.

Interpretation: the gate can eliminate this fixture's soft-edge false interrupts, but it deliberately moves unresolved true dependencies out of immediate blocking and into checkpoint verification. The lower immediate interrupt recall is a real cost, not a win to hide. Real replay must decide whether reconciliation latency and missed-immediate-block risk are acceptable.

Evidence class: `SYNTHETIC_MECHANISM_ONLY`. No generalized performance or safety claim is made.

## Exactly one deliberately unusual experiment

`OOB_FALSE_EDGE_LESION_RESCUE`

Inject a plausible current associative dependency for a high-impact hidden contradiction. The parent route proposes an interrupt; V15 caps it to `NEXT_CHECKPOINT`. Add only a replay-confirmed causal witness; V15 then restores `INTERRUPT_NEXT_SAFE_POINT`.

Result: PASS locally. This tests whether stronger connectivity can remain useful without treating graph association itself as authority.

## External live-knowledge fusion

Fresh 2026 design evidence supports the direction but does not promote it:

- GoAgent (arXiv:2603.19677): task/group-specific communication topology plus an information bottleneck rather than indiscriminate all-to-all communication;
- Autonomous Topology Mutation (arXiv:2607.20488): shadow-before-live topology validation with state/capability invariants;
- MCP 2026-07-28 protocol update: explicit self-describing routing metadata/state handles;
- Enzyme (arXiv:2603.27775): cost-based selection among refresh strategies rather than one universal incremental mode.

These are analogies/design evidence only. Clay promotion still requires repository/runtime measurements.

## Strongest counterhypothesis

The evidence gate may be too conservative. Soft dependencies can be correct before a hard witness exists; capping them to a checkpoint may delay interruption long enough for a worker to perform a stale effect. If anti-entropy/reconciliation is slower than the effect window, V15 may reduce false interrupts while increasing false non-interrupts.

## Highest-information next test

Run the already-required converged real-repository Ubuntu fault matrix on current work/claim/dependency events:

1. compare broadcast, tag/direct, PR166-style dependency routing, and V15 evidence-gated routing;
2. inject missing, stale and false edges plus dual-view ClayGraph/UnifiedDB disagreement;
3. replay duplicates and causal reorder;
4. crash/restart transport, reconciliation and lease/fencing state;
5. measure relevant-recipient recall, permanent miss rate after repair, false interrupt rate, false non-interrupt rate, verification latency, active-delivery amplification, p50/p95/p99 latency, CPU/RAM/I/O/network and recovery;
6. require zero permanent high-impact missed recipients after repair before any promotion.

## Branch feedback

- `clayresearch`: add false-dependency trust tier to completeness-gated live-fusion falsification.
- `frank`: no Harness authority change; hidden dependency interruptions must be provenance/evidence gated.
- `gwt`: preserve delivered/reconstructed/used/effect distinctions; associative reach does not equal causal uptake.
- `emergenz`: measure false synchronization/overcoupling from poisoned or heuristic dependency edges.
- `claycode`: eventual typed representation must distinguish projection freshness from dependency evidence class.
- `hyperposition`: preserve uncertain dependency alternatives until reconciliation instead of collapsing them to one blocking route.
- `claygraph`: expose edge provenance/evidence class separately from activation/currentness.
- `unifieddb`: persist witness identity, provenance, epoch and reconciliation outcome without creating a second truth store.
- `harness`: add false-edge and false-non-interrupt arms to the real-replay/Ubuntu fault matrix.

## Decision

Architecture promotion: NONE.
Canonical promotion: NONE.
Frank Harness mutation: NONE.
Candidate action: KEEP TESTING as an orthogonal shadow gate on the current live-fusion lineage.
Rollback: remove/disable the V15 adjudication layer; parent routing behavior is untouched.

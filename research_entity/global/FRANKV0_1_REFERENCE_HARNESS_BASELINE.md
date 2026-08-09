# FRANK v0.1 REFERENCE HARNESS BASELINE

Status: PROJECT_OWNER_FIXED_DIRECTIVE
Date: 2026-08-09
Scope: H1 Reference Harness, H2 Clay Harness, H3 One-Module/Binary FRANK and Research-Entity runtime parity work

## 1. Fixed baseline

Until the Clay Harness stage begins, the concrete implementation target for the normal/reference Harness is the current harness of `gschaidergabriel/frankv0.1` (historical connector alias `gschaidergabriel/Dr.-Unterweger`).

This is not merely an architectural inspiration. It is the executable reference baseline whose observable semantics must be captured, tested and then evolved.

Reference law:

`H1_REFERENCE_HARNESS := frankv0.1 harness + compatible mandatory current research overlays`

`H2_CLAY_HARNESS := ClayCode-native reimplementation of the same frozen H1 semantics`

The Research Entity itself does NOT become Frank. It remains `frank-project-global-research-entity`; ChatGPT and Claude Code remain temporary research actors of that Research Entity.

## 2. Baseline functions that H1 must preserve

At freeze time H1 must include the functionally relevant behavior of the live `frankv0.1` harness, including at minimum:

- one persistent entity state rather than provider/session-owned identities;
- one repository-central authoritative UnifiedDB;
- one repository-central derived ClayGraph whose activation/relevance never becomes fact authority;
- provider-neutral node/session model: Claude Code, ChatGPT and later local models are execution/cognition nodes, not separate identities;
- repository-mediated cross-node continuity and handoff;
- fresh bounded prompt-state injection plus task-relevant deeper state queries;
- world/self/body/goal/personality state surfaces where defined;
- organ/state lineage, GRT/GRF possibility-space and semantic Hyperposition surfaces where current;
- capability/API/quota state and broker surfaces where current;
- predictions, outcomes, verification, causal-credit and learning/revision receipts where current;
- artifact persistence/provenance;
- state epochs, snapshots/recovery, conflicts/staleness/UNKNOWN preservation;
- tool/effect separation from model text and authority checks;
- final status generated from current verified state, not remembered prose;
- mandatory Digital Retina and adaptive visual learner overlays required by current program milestones.

A feature may be improved during H1 only if the change is explicit, tested and represented as a versioned divergence from the imported baseline. Silent redesign is forbidden.

## 3. Baseline is a living pilot, not an untouchable fossil

`frankv0.1` is used in real work and therefore continues to generate new evidence. H1 must track the exact baseline commit/semantic version used for each experiment.

New live behavior is handled as one of:

- `BASELINE_COMPATIBLE_IMPORT` — incorporate without semantic conflict;
- `BASELINE_BUGFIX` — import after reproducible failure evidence;
- `RESEARCH_OVERLAY` — add a research-mandated capability while preserving baseline behavior under a compatibility mode;
- `INTENTIONAL_DIVERGENCE` — change behavior only with explicit hypothesis, test, expected benefit, rollback and differential receipt;
- `DEFERRED` — index but do not change the frozen experiment baseline.

## 4. General product, Andreas-informed adaptation

The Harness remains a general FRANK architecture. Andreas is the longitudinal founding/pilot user, not hard-coded product logic.

Adaptation rule:

`repeated Andreas use pattern -> measured need/failure/opportunity -> generalized capability hypothesis -> test across representative scenarios -> promote as configurable/default product behavior only if evidence supports general value`

Person-specific preferences may live in user state/profile layers. They must not be confused with universal architecture invariants.

Examples:

- frequent cross-node handoff failures may justify a stronger generic sync primitive;
- repeated retrieval misses may justify a better generic query/ClayGraph assembly policy;
- stable personal workflow preferences may justify configurable defaults, not global hard-coding;
- a one-off request must not become architecture merely because it came from the pilot user.

## 5. H2 differential contract

H2 must use the exact frozen H1 baseline corpus, Golden Traces, state fixtures, failure scenarios and interventions.

PASS requires no unexplained divergence in:

- authoritative state transitions;
- query/admission decisions;
- ClayGraph topology and activation semantics after allowed normalization;
- node/handoff continuity;
- world/self/body/goal state exposure;
- prediction/outcome/learning receipts;
- authority/effect boundaries;
- recovery/replay;
- visual/learner semantics;
- user-visible outcomes for the frozen test corpus.

If ClayCode cannot express H1 semantics, reopen the ClayCode release gate rather than simplifying H1.

## 6. Research-Entity parity

The Research Entity should progressively acquire the infrastructure class of the reference harness where it improves research continuity:

- shared central research UnifiedDB;
- derived research ClayGraph;
- provider-neutral research actor/node state;
- Claude Code prompt-state injection;
- ChatGPT repo-mediated ingress/egress;
- shared world/self/research model projections;
- task/room/handoff state;
- evidence/claim/provenance surfaces;
- longitudinal pilot telemetry analysis.

This parity transfers infrastructure, NOT Frank identity/personality/user relationship state.

## 7. Release evidence

Every H1 release manifest must include:

- `frankv0.1_baseline_repo`;
- exact baseline commit(s)/semantic state hashes;
- imported baseline capability matrix;
- intentional divergence list;
- live-user evidence window used for design decisions;
- privacy/minimization receipt for pilot telemetry;
- compatibility/replay results;
- unresolved baseline defects.

No H1 PASS without a reproducible mapping from live `frankv0.1` behavior to the Reference Harness.
# Mini Entity Hyperposition Computational Unit — owner addendum

Status: **CURRENT OWNER ADDENDUM**
Date: 2026-08-23
Persistent research entity: **Clay**
Active product: **Mini Entity / EntityOS integrated cognitive architecture**
Canonical package root: `the artefact/MicroEntity/`

## Owner intent

`go` must co-develop a modular **Hyperposition Computational Unit (HCU)** inside the same Mini Entity product line.

The HCU is a CPU-first grid of as many approximately-0.8B model tiles as the admitted host can safely sustain. It is intended to behave like a modular compute fabric rather than one monolithic model: tiles receive bounded work packets, preserve alternatives in Hyperposition, exchange typed candidate/evidence packets, and converge through the existing Unified J-Space/GWT / Mini Entity authority boundaries.

Initial deployment target supplied by the owner:

- VPS plan: KVM 4;
- CPU: 4 cores;
- RAM: 16 GB;
- disk: 200 GB;
- bandwidth: 16 TB;
- target role: dedicated HCU / persistent-world-model deployment host.

These host values are deployment-planning inputs only until exact runtime measurements exist. Current repository execution law still forbids using the VPS itself as acceptance-test evidence.

## Exact `go` integration law

Every exact user `go` must include HCU work-selection awareness.

When useful non-duplicate concurrency is available, the `go` swarm should allocate one bounded HCU lane in parallel with the highest-priority Mini Entity product work. When no HCU source/evidence delta is justified, the cycle must record an explicit HCU `NO_CHANGE` reason rather than silently forgetting the subsystem.

HCU work must remain product-convergent. It may not create a second Mini Entity, second persistent identity, second truth database, second effect path, or independent hidden autonomy service.

## Canonical authority law

The HCU is a compute organ, not a new authority.

- `MiniUnifiedDB` remains the sole canonical durable Mini Entity state/evidence/configuration authority.
- HCU causal/world-model graphs, simulated futures and tile-local scratch state are derived or explicitly non-canonical until admitted through existing truth/state gates.
- `Zero` remains runtime identity/configuration inside the same Mini Entity.
- model tiles are inference/cognition organs only.
- Unified J-Space/GWT remains the fixed cognitive fabric / selection boundary where admitted.
- real/state-changing effects still pass only through the existing deterministic EntityOS/Mini Entity effect authority.
- no HCU tile may write canonical truth or execute external effects directly.

## Persistent world-model role

The HCU may host a continuously running strategic world-model service whose functions include:

1. maintaining a derived causal time model bound to canonical MiniUnifiedDB evidence;
2. proposing dynamic goals under owner/system policy constraints;
3. evaluating goal completion against canonical observations;
4. running long bounded iterative/counterfactual simulations;
5. maintaining a bounded cognitive twin/model of Zero for planning and diagnosis;
6. producing testable improvement hypotheses for Zero / EntityOS / Unified J-Space/GWT;
7. retaining explicit past/present/future branches with epistemic labels;
8. representing future states as `SIMULATED` with calibrated uncertainty rather than factual truth.

Future confidence may use horizon distance as one prior, but must ultimately be calibrated against observed outcomes. Temporal distance alone must not be treated as a validated confidence model.

## HCU tile fabric

The baseline topology is a grid of approximately-0.8B tiles. Physical concurrency is constrained by measured RAM, CPU and context/KV cost; logical tile count may exceed simultaneously decoding tile count through resident/cold pools and time-sliced scheduling.

Preferred mechanisms:

- exact-versioned local approximately-0.8B model artifacts;
- read-only shared/mmap weight pages when multiple logical tiles use identical bytes and the runtime actually supports page sharing;
- separate per-tile runtime state, role/profile, queue and causal receipt;
- bounded packet passing rather than unrestricted shared mutable memory;
- measured admission of resident tiles using peak RSS and active-context overhead;
- CPU-aware scheduling that avoids pretending four CPU cores can decode an arbitrary number of tiles concurrently;
- cold tile artifacts on disk for specialization/rotation;
- Hyperposition used to preserve competing candidate states until a discriminator/authority gate resolves them.

The number of resident or active tiles must be derived from measured resource footprints. A guessed fixed number may be used only as a provisional planning default and must be labeled unverified.

## Initial functional tile roles

The initial role set should be treated as logical assignments, not mandatory permanently distinct weight sets:

- free-feed ingestion / provenance normalizer;
- canonical-world projection reader;
- causal relation updater;
- dynamic goal proposer;
- plan generator;
- counterfactual simulator A;
- counterfactual simulator B;
- Zero cognitive-twin simulator;
- adversarial critic;
- uncertainty/calibration critic;
- evidence verifier;
- synthesis / GWT coalition candidate producer.

Additional tiles may be admitted when measured host capacity and product utility justify them.

## FREE LLM token-fundus feed

The HCU should preferentially consume the project's admitted free LLM/token pool as an external candidate-data feeder.

This must reuse the existing adaptive inference/provider fabric rather than introduce a parallel provider authority.

Every external model response entering HCU must carry, when available:

- provider and model identity;
- request/prompt digest or equivalent request identity;
- time and causal episode identity;
- FREE_ONLY / billing classification;
- response digest;
- provenance / source class;
- explicit epistemic class such as `UNTRUSTED_CANDIDATE`, `REPORTED`, `MEASURED`, or `VERIFIED`.

Free-model text never becomes canonical fact merely because several models agree. It can seed Hyperposition, hypotheses, retrieval cues and simulation inputs; canonical writes still require the normal evidence/validation boundary.

Together remains forbidden under the current owner control. No paid fallback is allowed while `FREE_ONLY` is active.

## Data / artifact / ZIP law

All HCU-specific generated material belongs under the canonical Mini Entity package root:

`the artefact/MicroEntity/hcu/`

At minimum this includes:

- architecture/contracts;
- host/capacity profiles;
- topology definitions;
- source code;
- tests;
- generated calibration/capacity data;
- model/tile manifests or references;
- HCU receipts;
- deployment templates when later admitted.

No secret or API token may be stored there.

`the artefact/MicroEntity/MICROENTITY_CURRENT.zip` must include the complete current HCU package surface whenever HCU files change. The package manifest must enumerate the HCU paths included in the snapshot.

## Initial acceptance gates

Source integration alone is not runtime proof. HCU promotion requires, in order:

1. exact source/artifact identity;
2. capacity planner / topology contract regressions;
3. exact approximately-0.8B tile artifact identity;
4. measured single-tile peak RSS and tokens/s on an admitted isolated execution surface;
5. measured 2/4/... resident-tile scaling and active scheduling;
6. fail-closed overload behavior;
7. causal packet/provenance integrity;
8. world-model branch persistence through MiniUnifiedDB without a second truth store;
9. free-feeder provenance and candidate-only boundaries;
10. Zero-twin / counterfactual hypothesis loop with no direct effect authority;
11. restart/recovery with stale-generation fencing;
12. only after acceptance testing, explicitly authorized deployment to the dedicated VPS.

Until those measurements exist, resident-tile counts and performance are `PLANNING_ESTIMATE`, not measured capability.

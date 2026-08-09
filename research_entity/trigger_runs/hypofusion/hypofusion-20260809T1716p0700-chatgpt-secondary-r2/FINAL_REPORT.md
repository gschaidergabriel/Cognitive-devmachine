# HYPOFUSION R2 — Adversarial Hypothesis Screening + Whole-Mesh Fusion 2

Run: `hypofusion-20260809T1716p0700-chatgpt-secondary-r2`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Promotion: **NONE**

## Executive result

This Hypofusion does **not** justify another architecture expansion. It pushes the current programme toward stricter executable boundaries and several simpler external mechanism candidates.

Eight transformed hypotheses were created because external comparison materially changed their mechanism, boundary or next test:

1. **standard-first numeric identity** rather than assuming a custom Clay canonicalizer;
2. **dual compiler trust**: provenance ancestry + independent semantic oracle;
3. **opaque lifetime contract** with implementation mechanism left open;
4. **loop stability controller** rather than monotonic recurrence-depth assumptions;
5. **reducer-first higher-order representation** rather than native hyperrelations by default;
6. **scoped commit freshness** rather than one global effect epoch;
7. **dual replay lanes**: deterministic staged replay + outside-in nondeterministic faulting;
8. **BASE witness first**: executable cross-branch conformance before more surface-language redesign.

The dominant meta-result is:

> **Keep semantic distinctions rich, but make every expensive or exotic mechanism earn its place against the strongest simpler external alternative.**

## What changed most

### 1. ClayCode compiler trust is now a two-proof problem

Current worker evidence already refuted the idea that a self-consistent provenance/hash chain proves semantic preservation: deliberately wrong but internally consistent lowerings passed chain integrity. External verified-compiler work independently treats source/target behavior preservation as a separate correctness property.

Therefore BASE evidence should keep both:

- ancestry/provenance integrity: source -> parser -> AST -> typed IR -> semantic identity -> lowering -> artifact -> execution receipt;
- an independent semantic/reference/translation-validation oracle.

Neither substitutes for the other.

### 2. Numeric identity should be standard-first

The new ClayCode cross-runtime probe found host-native JSON numeric divergence and exact-integer loss. RFC 8785 already provides a mature canonicalization model for an IEEE-754/I-JSON domain, including explicit behavior for non-finite values and long integers outside that domain.

Fusion result: do not invent Clay-specific numeric formatting until the admitted Clay numeric domain proves JCS-compatible semantics insufficient. Exact `Int`, signed-zero and special-value policy must be explicit at the type/canonical-IR/lowering boundary.

### 3. Resource lifetime is real, but generation tags are not privileged

The local ABA probe strongly demonstrates the failure mode of raw reusable slot identity under forced reuse. WebAssembly Component Model/Wasmtime supplies an independent typed `own`/`borrow` handle family.

Fusion result: require **opaque current-lifetime resource identity**. Generation counters, backend-native resource handles and non-reusing identifiers remain competing mechanisms.

### 4. FRANK's loop-of-loops survives, but only as a controlled dynamical system

The integrated ClayResearch hypothesis that FRANK is better modeled as interacting multi-timescale recurrent loops remains plausible. Current external looped-LM work supplies a serious counterboundary: additional recurrence can improve performance up to a point and then collapse.

Fusion result: recurrence depth/gain is an intervention variable. The architecture needs explicit stop/stall/overcoupling criteria and matched-compute comparisons against shallow/fixed recurrence. This is not an argument against FRANK's loop mechanics; it is a requirement to measure their stability envelope.

### 5. Hyperposition becomes reducer-first

The internal relation work already showed that unlabeled pairwise reductions can lose role-bearing semantics. But 2026 peer-reviewed work demonstrates exact pairwise reductions for a nontrivial class of hypergraph dynamics, and current theory work challenges universal expressivity claims for hypergraphs.

Fusion result: explicit n-ary/hyperrelation representation stays available, but it must beat the best typed graph/factor/state-machine reduction on semantic/intervention/replay equivalence or measurable cost. `higher-order interaction != mandatory hyperedge`.

### 6. Shared semantic epochs and effect freshness are different problems

Shared epochs remain a useful candidate for coherent UDB/ClayGraph/GWT/Hyperposition reads and replay. A fresh Harness worker, however, found that global-epoch equality at effect commit safely rejected unsafe changes but also falsely aborted safe work under unrelated churn, while a scoped dependency/capability/resource check avoided both in the constructed model.

Fusion result:

- use coherent semantic epochs for snapshot/read/replay identity where they help;
- revalidate **scoped decision dependencies** at effect commit;
- never infer commit authority from model output, Needle routing, GWT selection, ClayGraph activation, recurrence or emergence state.

### 7. Exactly-once external effects remain unproven

Local idempotency ledgers and serialized transactions can classify retries/concurrency, but a local `PREPARED` record cannot generally distinguish crash-before-effect from crash-after-effect without remote cooperation.

Fusion result: external effects need remote idempotency/deduplication, transactional coupling, queryable/reconcilable remote identity, or a typed `UNCERTAIN` recovery result. Do not promote a local ledger into an exactly-once guarantee.

### 8. Replay needs two lanes

Current Harness work supports content-addressed staged TurnTrace replay and environment fingerprints. Independent reliability-engineering precedents pair deterministic simulation with real/outside-in fault injection.

Fusion result: H1/H2/H3 validation should pair:

- deterministic staged semantic replay for reproducibility/localization;
- outside-in nondeterministic faulting for failure classes hidden by the simulator/model.

## Current-stage implication

The `BASE_CLAYCODE_RELEASE` gate should become more execution-heavy, not more speculative.

Highest-information order:

1. Build one minimal executable semantic witness for every registered branch through the **real** BASE parser/type/effect/lowering/runtime chain.
2. Run a wrong-but-self-consistent lowering mutation suite against a distinct reference evaluator/semantic oracle.
3. Run numeric canonicalization/roundtrip across selected backends using RFC8785-compatible behavior as the baseline where applicable.
4. Run real FFI lifetime/ABA tests across files, processes, sockets/HTTP and DB handles on the Ubuntu developer target.
5. Freeze ambiguous legacy G9 semantics explicitly; fail closed before authoritative freeze rather than guessing intent from source formatting.
6. Preserve later-stage H1/H2/H3 work as blocked prerequisites; do not skip the staged programme.

## Whole-mesh feedback

All nine currently registered scientific branches received explicit feedback in `BRANCH_FEEDBACK_MANIFEST.json`:

- `clayresearch`: refine toward standard-first/reducer-first/scoped-freshness/dual-replay tests;
- `frank`: preserve recurrence but add stability envelope and non-authority boundary;
- `gwt`: keep system vs model-internal workspace distinct and causally test uptake/re-entry;
- `emergenz`: no promotion; strengthen intervention/multiscale/transfer controls;
- `claycode`: highest-priority execution delta; compile real cross-branch witnesses;
- `hyperposition`: reducer-first and bounded propagation;
- `claygraph`: keep provenance/conflict/activation separation without intrinsic hypergraph claims;
- `unifieddb`: logical unification survives, physical/incremental choices remain benchmarked;
- `harness`: staged deterministic replay + outside-in fault lane + scoped commit freshness.

## Negative results preserved

- cryptographic/provenance continuity is **not sufficient** for semantic-preserving lowering in the tested class;
- raw reusable runtime slot identity is unsafe under forced ABA reuse in the constructed model;
- host-native JSON number serialization is unsafe semantic-hash material for the tested cross-runtime edge corpus;
- G9 V3 contains focused grammar/source self-consistency counterexamples;
- three legacy G9 rule lines remain semantically ambiguous and must not be auto-normalized before authoritative freeze;
- one global epoch at effect commit can cause false aborts under unrelated churn in the current synthetic oracle;
- local effect state does not establish exactly-once external side effects;
- universal native-hyperrelation necessity is not defensible against exact reduction counterexamples.

## Completion boundary

All nine mandatory Hypofusion run artifacts were written. External searches covered every major mechanism cluster represented by the current integrated matrix and fresh worker deltas. Counterhypotheses were paired with discriminating tests and every registered branch received feedback.

One product/tool limitation remains: the current GitHub connector cannot recursively enumerate repository directories/tree. The run therefore inherits the previous Hypofusion's 99-record mapping, explicitly enumerates the current 60-hypothesis integrated matrix plus recent worker deltas, and marks any otherwise-unreachable historical hypothesis records as `INACCESSIBLE` rather than pretending exhaustive tree visibility.

No new target-host experiment was executed by this Hypofusion itself. No canonical revision or scientific claim was promoted.

**Operational completion before final live-worker reread: 96%.**
# ClayCode Run — Resource Lifetime / FFI Ownership

Run ID: `claycode_20260809T1607p0700_chatgpt_secondary_resource_lifetime`  
Trigger: `claycode`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2` / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` / `IN_PROGRESS`  
Promotion: **NONE**  
Protocol completion: **LOCAL_RESEARCH_DELTA_COMPLETE; OFFICIAL PREFLIGHT/CHECKER PENDING**

## Executive synthesis

This run deliberately avoided duplicating concurrent ClayCode work on grammar self-conformance, relation namespaces, semantic publication and the Ubuntu effect/capability boundary. It targeted the next unresolved compiler/runtime layer: lifetime semantics for opaque FFI/resources crossing ClayCode, async code and host adapters.

The current G9 V3 semantic candidate has `ResourceRef`, `CapabilityToken` and `EffectIntent`, but does not state an explicit owned/borrowed/moved/dropped resource-lifetime contract. The BASE workspace still leaves typed IR, type/effect checking, runtime ABI/FFI, concurrency/memory and conformance packages open.

A small executable reference checker was therefore built around an explicit `ResourceHandle<T>` state machine. Against seven targeted traces it produced the expected result in 7/7 cases: two valid traces passed and five unsafe traces were rejected. The unsafe set covered double-drop, drop while borrowed, borrow escape, use-after-move by the old owner and nominal resource-kind confusion.

The result supports an **OPEN canonical-IR/runtime lifetime candidate**, not a promoted new surface syntax. Ownership/lifetime remains explicitly orthogonal to capability/effect authority: owning a resource handle never self-authorizes an external effect, and host revalidation remains mandatory.

## Concurrent-work assimilation

A fresh reread after a GitHub 409 conflict found a parallel ClayCode run at the same stage that independently identified grammar self-conformance as an immediate BASE blocker and produced a minimal grammar-repair candidate. This resource-lifetime run does not supersede or duplicate that result. The two deltas are complementary:

- parser/grammar self-conformance is required before broad compiler release;
- FFI/runtime resource lifetime is a downstream typed-IR/runtime invariant that must be integrated once the parser/type pipeline is real.

The 409 itself was handled by rereading current remote state rather than forcing an overwrite, preserving the project's collision/revalidation rule.

## Fusion 1 — internal evidence

### FRANK

FRANK C9 separates presence, admissibility, selection and authority. Its effect path uses non-authoritative `EffectIntent`, opaque host-minted permits, release-time revalidation, no-ambient-authority foreign-code execution and child-effect closure.

ClayCode implication: `ResourceHandle` must not collapse into `CapabilityToken` or `EffectPermit`. Handle lifetime controls whether a referenced host resource instance remains valid for use; separate authority checks decide whether an effect is allowed.

### Clay / current stage

The current staged program is `BASE_CLAYCODE_RELEASE`. The release policy is compile/runtime first and semantic redesign only when an executable counterexample forces it. The lifetime experiment therefore proposes the smallest semantic addition consistent with observed failures and keeps first-class source syntax unresolved.

### ClayGraph

ClayGraph V2 preserves graph/source epochs, typed hyperrelation roles and separate projection/selection/receiver receipts. Activation/salience is derived relevance, not truth or authority.

ClayCode implication: a graph may refer to resource identities or resource-related causal paths, but graph activation must never create, revive, transfer, drop or authorize a live runtime handle.

### UnifiedDB

UnifiedDB V9 already represents resource observations, capability instances, freshness, revisioned work, leases and execution receipts.

ClayCode implication: stable resource identity and lifetime/effect receipts can be linked into shared semantic state, but a persisted observation is not proof that an in-process borrowed handle is still live. Runtime lifetime state must remain bound to the actual executing resource instance and its current generation/scope.

### GWT / Hyperposition / Emergenz

The GWT contract distinguishes selection, delivery, reconstruction, uptake, causal use, effect, outcome and re-entry. Hyperposition keeps semantic, active, coordination and physical topology separate. Resource lifetime belongs to the runtime/causal-use/effect-lowering boundary; it must not become workspace authority or an emergence score.

No emergence claim is made from this result. Correct lifetime handling primarily reduces execution/replay confounds in later causal experiments.

### Harness

H1/H2/H3 remain downstream of BASE. Eventually the same owned/borrowed/drop traces should be included in H1/H2 differential replay so ClayCode lowering cannot silently change resource lifetime or effect semantics.

## Executable experiment

Artifact: `EXECUTABLE_RESEARCH_RECEIPT.json`

Prototype semantic state:

`OWNED | BORROWED | MOVED | DROPPED`

Tested operations:

- allocate/new resource;
- move ownership;
- borrow with bounded scope;
- use owned resource;
- use borrowed resource;
- end borrow;
- drop;
- nominal resource-kind check.

Results:

1. valid borrow -> end borrow -> drop: PASS
2. double drop: REJECT
3. drop while borrowed: REJECT
4. borrowed handle used after scope exit: REJECT
5. old owner uses after move: REJECT
6. resource kind mismatch: REJECT
7. valid move -> new owner use -> drop: PASS

The deliberately naive comparison proxy treated a generic `ResourceRef` as sufficient and therefore accepted all five unsafe negative traces. This proxy is a constructed discriminator, not a claim about the unfinished current ClayCode compiler.

## External independent evidence / Fusion 2

Primary WebAssembly Component Model specifications independently use lifetime-bearing resource types with distinct owned and borrowed handles. Owned handles represent transferable ownership; borrowed handles are temporary loans. Current concurrency design also treats outstanding loans as runtime state and can reject/drop-trap when lifetime constraints are violated across asynchronous activity.

This independently supports the need for explicit lifetime semantics somewhere in ClayCode's typed IR/runtime/lowering. It does **not** establish that ClayCode must copy WIT syntax, use the Component Model as its only backend, or expose `own<T>` / `borrow<T>` directly in the human/model-facing surface.

## Hypotheses

### H-CC-RL-001 — explicit lifetime state

Supported by current prototype, not promoted.

ClayCode needs explicit canonical IR/runtime lifetime state for opaque FFI resources so ownership transfer, borrowing, drop and nominal resource identity are checked before host lowering.

Counterhypothesis: generic `ResourceRef` plus adapter-local conventions can provide equivalent safety/replay/diagnostics with lower complexity.

Falsifier: a matched generic-reference implementation reaches equivalent rejection coverage, deterministic replay and cross-FFI correctness without hidden adapter semantics.

### H-CC-RL-002 — no mandatory new surface syntax

OPEN.

The lifetime contract may remain canonical IR/runtime semantics without adding first-class `own<T>` / `borrow<T>` syntax to G9.

Falsifier: real parser/compiler/application trials show IR-only lifetime tracking causes ambiguous source diagnostics, unsafe lowering or excessive repair/annotation cost.

### H-CC-RL-003 — ownership != authority

Supported architecture invariant.

Owning a live resource handle never self-authorizes an external effect. Capability/effect authority stays external and independently revalidated.

### H-CC-RL-004 — async borrow scope

Supported by prototype plus independent Component Model analogue, not promoted.

Async/FFI borrowing needs static or dynamic scope enforcement so owners cannot drop while loans remain active and borrowed references cannot escape their valid task/call lifetime.

## Goodman anti-echo review

FRANK C9's typed/no-ambient-authority FFI direction was not accepted merely because ClayCode already agrees with it. Shared FRANK↔ClayCode ancestry was collapsed. Independent evidence came from the current executable lifetime counterexamples and the WebAssembly Component Model resource/concurrency specifications.

Verdict: **REFINED**.

The evidence supports explicit resource-lifetime semantics as a canonical IR/runtime candidate. It does not support a mandatory new surface syntax, a completed Ubuntu implementation, or any collapse of resource ownership into effect authority.

## Negative results and limits

- A naive generic-reference lowering is unsafe for the five targeted lifetime failures.
- No evidence yet shows first-class `own/borrow` surface syntax is required.
- No Ubuntu developer-system execution occurred in this run; target-runtime correctness/performance remains OPEN.
- The official repository `research_interconnect_preflight.py` and `goodman_filter_check.py` could not be executed from this ChatGPT tool surface because no usable repository checkout was available. Manual manifests remain fail-closed and do not count as official PASS.
- The current prototype is a reference semantic checker, not the finished ClayCode parser/typechecker/compiler/runtime.

## Cross-branch feedback

- **FRANK:** preserve separate lifetime and authority domains; add lifetime/drop/borrow receipts at the tool/FFI boundary when implemented.
- **ClayGraph:** resource association/activation never creates or revives runtime handles; graph refs may point to identity/receipts only.
- **UnifiedDB:** persist stable identities and receipts where useful, but do not infer a live borrow/ownership state from stale persisted observations.
- **GWT:** lifetime failure should appear as causal-use/effect failure receipt, never as workspace authority.
- **Hyperposition:** ownership transfer/borrowing is an explicit physical/runtime topology transition with semantic identity continuity, not semantic colocation.
- **Emergenz:** use lifetime correctness as experimental-control hygiene; no emergence promotion.
- **Harness:** add lifetime traces to later H1/H2 differential conformance.
- **Clayresearch:** retain as one BASE compiler/runtime candidate, not a cross-project truth promotion.

## BASE-stage impact

Affected work packages:

- `CC-WP-03-IR-TYPES`
- `CC-WP-04-TYPE-EFFECT`
- `CC-WP-07-RUNTIME-ABI-FFI`
- `CC-WP-09-CONCURRENCY-MEMORY`
- `CC-WP-11-FUZZ-CONFORMANCE`

No package is marked complete. No application proof is promoted. BASE remains `NOT_PASS`.

## Next discriminating experiment

Highest-information continuation:

1. integrate `ResourceHandle` state into the real ClayCode evaluator/type/effect/FFI slice after parser self-conformance is available;
2. compile the same positive/negative lifetime corpus through at least one real host ABI;
3. add async stress/property tests for nested borrows, cancellation, error unwinding, move/drop races and generation reuse;
4. compare two source-language strategies under matched tests: IR-only inferred lifetime semantics vs explicit first-class `own/borrow` syntax;
5. differential-test against WebAssembly Component Model/WIT or an equivalent reference backend;
6. replicate final claims on the Ubuntu developer-system target before BASE promotion.

Promotion criterion: preserve the five safety invariants plus valid-program behavior with bounded diagnostics/runtime cost and no authority conflation.

## Durable artifacts

- `RESOURCE_LIFETIME_CANDIDATE.clay`
- `EXECUTABLE_RESEARCH_RECEIPT.json`
- `INTERCONNECT_MANIFEST.json`
- `HYPOTHESIS_MATRIX.json`
- `FRANK_CLAYCODE_GOODMAN_REVIEW.json`
- `NEGATIVE_RESULTS.json`
- `TOOL_EXECUTION_MANIFEST.json`
- center event `20260809T1607p0700_claycode_resource_lifetime_delta.json`
- `FINAL_REPORT.md`

## Final research delta

**Supported local candidate:** explicit owned/borrowed/moved/dropped resource-lifetime semantics belong in ClayCode's canonical IR/runtime/FFI contract unless a simpler matched implementation falsifies the need.

**Not promoted:** surface syntax, Ubuntu backend choice, compiler completion, BASE package completion.

**Preserved invariant:** resource lifetime/ownership is not capability/effect authority.

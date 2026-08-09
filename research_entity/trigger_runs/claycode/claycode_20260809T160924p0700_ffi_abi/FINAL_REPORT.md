# ClayCode Run — FFI/ABI Resource Identity and Lifetime Discriminator

Run: `claycode_20260809T160924p0700_ffi_abi`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Selected partition: `CC-WP-07-RUNTIME-ABI-FFI`

## Executive synthesis

This run did not redesign ClayCode globally. It targeted one still-open BASE compiler/runtime boundary that was not occupied by the current parser, relation-surface, control-flow, ClayGraph/UnifiedDB or capability-fuzz workers: host FFI resource identity and lifetime.

The current G9 candidate already has a strong authority separation (`CapabilityToken`, `EffectIntent`, external commit gateway) but the language surface does not yet make an FFI resource's runtime lifetime/ownership identity explicit. A local executable counterexample shows that a naive lowerer that lets a capability designate only a reusable numeric resource slot is unsafe under drop+reuse: an old handle/capability can resolve to a new resource, including a different resource type. The same slot-only model has no machine-enforceable temporary-borrow boundary.

A bounded candidate using typed resource identity plus generation/lifetime semantics rejected all planted stale/cross-type/capability-alias/borrow-after-return cases while preserving valid operations in the tested corpus.

This supports a **refinement**, not a canonical syntax promotion:

> ClayCode BASE FFI lowering should bind capability designation to a lifetime-bound typed resource identity and enforce owned/borrowed or an equivalent lifetime discipline. The exact representation is still OPEN.

`CC-WP-07` remains OPEN. No BASE-stage percentage is awarded by this run.

## Research-center coordination

The worker joined the current ClayCode federation before claiming work and selected only the FFI/ABI resource-lifetime partition. It explicitly reused, rather than duplicated, concurrent work on:

- parser/canonicalizer conformance;
- strict relation/predicate surface;
- control-flow precedence;
- ClayGraph/UnifiedDB semantic boundaries;
- existing capability forgery/scope fuzzing.

JOIN and CLAIM receipts are in the ClayCode room event stream.

## Fusion 1 — current internal evidence

### ClayCode G9

G9 already separates semantic intent from execution authority and defines `CapabilityToken.designates: ResourceRef`. This is retained. The unresolved question is what identity a `ResourceRef` must preserve when lowered across a host ABI that allocates, drops, borrows and reuses runtime resources.

### FRANK

The newest fused FRANK target overlay keeps P10 effect authority external to model output, requires host-minted effect permission/revalidation and forbids ambient OS authority. P12 also preserves authority/untrusted-code boundaries even if later deployment boundaries collapse. These are shared FRANK/ClayCode lineage and therefore were not counted as independent proof.

### ClayGraph

ClayGraph V2 explicitly keeps graph activation/relevance non-authoritative and records source/graph epochs and projection/selection receipts. Therefore a graph-level resource association may aid routing or replay, but it must never substitute for live host-resource authority/lifetime validation.

### UnifiedDB

UnifiedDB V9 already distinguishes persistent resource observations, capability instances, authority scope and execution receipts. The FFI finding suggests keeping stable semantic resource identity distinct from ephemeral runtime handle/lifetime identity instead of overloading one reusable host slot as both.

### GWT / Emergenz / Hyperposition

No emergence claim is made. A stale FFI alias would be a causal confounder: an intervention/effect could silently hit a different physical resource while higher-level receipts still reference the old semantic intention. GWT/effect traces should therefore preserve the effective host-resource identity used at execution. Hyperposition's distinction between semantic and physical execution topology also argues against collapsing resource identity into a single ambiguous reference.

### Harness

H-WP-10 effect authority remains OPEN. The new discriminator is a candidate future Harness fixture: drop a resource, force slot reuse, replay the old capability/handle, test cross-type reuse, and test borrow escape. The Harness should accept any implementation that passes these invariants, not require this run's exact five-field representation.

## External research

Evidence class: primary official standard/documentation; independent design analogue, not proof that ClayCode must copy WebAssembly.

1. WebAssembly Component Model WIT reference — resources are typed non-copy entities passed by handles; WIT distinguishes owned resources from borrowed resources, with borrows scoped to the duration of a call.  
   Source: https://component-model.bytecodealliance.org/design/wit.html

2. WASI documentation — WASI applications operate in a capability-based sandbox and begin without ambient authority; the host explicitly grants capabilities.  
   Source: https://wasi.dev/

The independent lesson is architectural, not syntactic: host resources need opaque/type-safe lifetime handling and capabilities should remain host-granted authority, separate from textual/model intent.

## Executable experiment

Artifact: `ffi_resource_identity_probe.py`  
Receipt: `EXECUTABLE_RESEARCH_RECEIPT.json`

Two host-resource-table models were compared over 20,000 deterministic allocation/drop/reuse cases.

### Naive slot-only identity

Observed:

- stale handle accepted after slot reuse: `20,000 / 20,000`;
- stale capability designation retargeted to reused slot: `20,000 / 20,000`;
- cross-type stale alias accepted: `10,000 / 20,000`;
- simulated borrow remained usable after call boundary: `20,000 / 20,000`.

### Typed generation/lifetime identity

Observed:

- stale handle accepted: `0`;
- stale capability-resource alias accepted: `0`;
- cross-type stale alias accepted: `0`;
- borrow-after-return accepted: `0`;
- valid operations accepted: `40,000` checks.

Execution surface: local Python sandbox. E2B was not exposed in this ChatGPT tool surface. This is not Ubuntu-native or production-compiler evidence.

## Hypotheses and counterhypotheses

### H-CC-FFI-001 — stale resource alias

If a capability designates only a reusable slot/resource number, drop+reuse can retarget old authority to a new resource.

Status: `SUPPORTED_LOCAL_SYNTHETIC`.

Counterhypothesis: the runtime uses globally unique/non-reused identities or independently version-checks every lookup, making explicit generation unnecessary.

Falsifier: a concrete slot-reusing lowerer that rejects all stale aliases without any equivalent lifetime/version identity.

### H-CC-FFI-002 — temporary borrow boundary

Temporary FFI loans need machine-checkable lifetime/ownership semantics or an equivalent mechanism.

Status: `SUPPORTED_LOCAL_PLUS_EXTERNAL_ANALOGUE`.

Counterhypothesis: ClayCode never exposes borrow semantics, or each backend statically proves non-escape before lowering.

### H-CC-FFI-003 — representation remains open

The requirement should be semantic (`lifetime-bound typed resource identity`), not prematurely fixed to `{instance, slot, generation, mode}`.

Status: `OPEN`.

A runtime with opaque globally unique handles and equivalent lifetime enforcement may be simpler and equally safe.

## Goodman anti-echo review

Verdict: `REFINED`.

The FRANK/ClayCode external-authority rule survives independent checks, but the FFI boundary needs a stronger resource-identity contract. Independent support came from the new executable stale-handle test and official WebAssembly/WASI resource/capability designs. The exact candidate representation is not independently established and therefore is not promoted.

Full review: `FRANK_CLAYCODE_GOODMAN_REVIEW.json`.

## Negative results

### NR-CC-FFI-001

Reusable numeric slot identity alone fails the tested stale-resource/authority model. Preserve this as a regression case.

### NR-CC-PREFLIGHT-001 — research tooling

The current `tools/research_interconnect_preflight.py` still hard-codes the old integrated branch name `clay` in its fail-closed priority sets, while the current trigger registry names that integrated branch `clayresearch`. Its registry-set equality guard is therefore stale after the rename.

This run does not claim a successful preflight. `INTERCONNECT_MANIFEST.json` was materialized manually from verified current GitHub inputs and the tooling contradiction is preserved for repair. This is a governance/tooling negative result, not a ClayCode scientific claim.

The Goodman checker was likewise not falsely claimed as executed because this ChatGPT surface has connector access rather than a full repository checkout/runtime.

## Branch feedback

- **ClayCode:** keep G9 capability/effect separation; add an OPEN FFI requirement for lifetime-safe typed resource designation or equivalent.
- **FRANK:** P10 effect permits should revalidate the effective runtime resource identity at release/commit, not only a reusable slot-like reference.
- **Harness:** add stale-handle, slot-reuse, cross-type-reuse and borrow-escape effect-authority fixtures.
- **UnifiedDB:** preserve stable semantic resource IDs separately from ephemeral runtime-handle generation/lifetime data where needed for replay and receipts.
- **ClayGraph:** resource associations remain routing/provenance metadata, never live authority.
- **GWT:** effect/outcome receipts should carry the effective resource identity actually used by the host.
- **Hyperposition:** stale aliasing is a physical-topology/replay divergence, not a semantic equivalence.
- **Emergenz:** treat resource aliasing as a causal confounder in intervention experiments; no emergence promotion.
- **Clayresearch:** no global architecture change; retain the external authority boundary and feed the FFI regression into BASE/Harness work.

## Architecture implication

The smallest justified delta is:

`CapabilityToken.designates ResourceRef`

must, at an FFI effect boundary, resolve to a resource identity whose lifetime cannot silently alias another live resource. That may be implemented by generation-tagged handles, globally unique opaque handles, backend-native owned/borrowed handles, or another mechanism that passes the same invariants.

This preserves ClayCode's design principle: semantic expressibility is not execution authority, and lowering must not erase authority-critical identity.

## Next discriminating experiment

Implement the same interface contract in two real lowerings on the Ubuntu target, preferably:

1. a native Linux host-resource adapter; and
2. a WebAssembly Component/WASI adapter or another independent backend.

Run the same stale-handle/borrow/cross-type corpus plus crash/restart, async, cancellation and replay cases. Compare explicit generation-tagged IDs against opaque globally unique IDs for:

- semantic preservation;
- stale-resource rejection;
- borrow/cancellation correctness;
- replay determinism;
- capability scope correctness;
- latency/memory overhead;
- diagnostic/repair cost.

Only then decide the canonical IR representation and consider progress on `CC-WP-07`.

## Final research delta

**Accepted as local negative result:** slot-only FFI resource identity is unsafe under deliberate slot reuse in the tested model.

**Accepted as refined requirement:** FFI capability/resource lowering needs lifetime-bound typed identity or an equivalent proven mechanism.

**Not accepted:** the exact five-field candidate as canonical ClayCode syntax/IR.

**Program stage:** remains `BASE_CLAYCODE_RELEASE`; `CC-WP-07` remains OPEN and no strict stage progress is awarded.

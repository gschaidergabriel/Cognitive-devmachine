# ClayCode Trigger Run — Resource Lifetime / Epoch / Borrow / Type

Run: `claycode_20260809T1709p0700_chatgpt_resource_lifetime_epoch`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Stage: `BASE_CLAYCODE_RELEASE`  
Promotion: **NONE**

## Question

Can current ClayCode G9 semantics realize safe host-resource lifetimes through compiler/runtime/FFI lowering, or does a bounded database/resource slice force new ClayCode core syntax or a new DB-specific primitive?

## Current internal basis

- G9 V3 already separates `CapabilityToken`, `ResourceRef`, `EffectIntent`, concrete adapter lowering and external effect lifecycle.
- BASE acceptance requires a runtime ABI, typed host FFI, explicit resource/memory semantics and executable application receipts, while enforcing the project rule `less change, more compile`.
- ClayGraph V2 explicitly keeps graph projection/relevance separate from semantic/effect authority and binds projections to graph/source epochs.
- UnifiedDB V9 separately records physical/system resources, capability observations, freshness, leases and execution receipts; current semantic state is not identical to a live resource instance.
- Current FRANK loop-of-loops material requires typed recurrent/effect state while preserving authority boundaries and Ubuntu-only v0.1 execution scope.
- Current mesh feedback preserves the BASE frontend/compiler closure blocker: runtime evidence does not bypass parser/compiler completion.
- Repository search in this hosted run did not locate `FRANK_ARCHITECTURE.claycode.json`; current FRANK directive/mesh material was used provisionally and the absence was recorded rather than fabricated.

## External primary-source research

The WebAssembly Component Model provides a useful independent comparison rather than a design mandate:

- component resources are abstract lifetime-bearing types represented indirectly by handles;
- `own` and `borrow` are distinct handle modes;
- resource handles are mediated through per-instance tables rather than copied resource values;
- resource types are generative/type-distinct;
- runtime rules enforce drop/borrow conditions, including async lend/borrow accounting.

This supports testing resource lifetime as a typed runtime/ABI concern rather than assuming every resource domain needs new source-language syntax.

## Executable experiment

A generic ClayCode-like canonical resource object was lowered to a generated Python guest running in a **separate process**. The guest could request resource operations only through an inherited Unix-socket broker owned by the host process. The broker tracked:

- opaque host-issued handle identity;
- resource type;
- current resource/capability epoch;
- closed/open state;
- active borrows.

An independent pure state-machine oracle evaluated the same requests.

### Randomized differential result

- seed: `202608091706`
- randomized operations: **20,000**
- broker/oracle mismatches: **0**
- guest exit: **0**
- source hash: `8170cf06dfdb8a2204eb5f653e09aa22d04d029d990a310cd02be332c895daf6`
- generated guest hash: `5698e4fa10a6688c58aae5664f76dc87b73a1427fb38a6043bf590891dab8e3a`

Representative rejected cases included unknown/forged handles, wrong resource type, stale epoch, double close, invalid borrow and owner-close while borrowed.

### Discriminating ablations

Three deliberately weakened implementations produced immediate executable counterexamples:

1. remove epoch/freshness check -> stale handle use becomes accepted;
2. remove active-borrow close check -> owner close becomes accepted while a borrow remains live;
3. remove resource type check -> a DB handle can be used as a file handle.

Therefore opaque handle naming alone is insufficient in this tested slice. Lifetime/freshness/type semantics must survive lowering by either static proof, runtime enforcement, target-backend guarantees, or a verified combination.

## Goodman anti-echo result

Verdict: **REFINED**.

The FRANK/ClayCode separation between computation and external effect/resource authority has independent support from the Component Model resource design and this executable proxy, but the result does **not** justify a new DB-specific ClayCode primitive. The evidence instead favors a backend-neutral typed resource-lowering contract under CC-WP-07.

Important refinement: capability authorization epoch and resource lifetime/generation epoch should not be silently collapsed into one concept. They may correlate in some backends, but target execution must determine when revocation invalidates a live resource versus only future effects.

## Parallel-worker relation

A concurrent ClayCode worker started `claycode_20260809T1708p0700_chatgpt_resource_handle_aba`, focused on stale-handle slot-reuse ABA. This run is complementary: it covers capability/resource freshness, borrow lifetime and cross-type misuse. Shared repository ancestry and temporal overlap mean convergence, **not independent replication**.

## ClayGraph / UnifiedDB findings

### ClayGraph

No graph schema change is justified. Host-resource lifetime/generation must remain distinct from graph epoch/root/projection identity. A graph projection can reference a resource-related concept, but graph activation or relevance must not be treated as proof that a host handle is live/current.

### UnifiedDB

No storage consolidation or schema promotion is justified. V9 already separates resource observations, capability observations, freshness and execution receipts. A future ClayCode runtime adapter should bind a live handle instance to these semantic/provenance records without equating the records themselves with the handle.

## Branch feedback

- `clayresearch`: support `less change, more compile` for this bounded slice.
- `frank`: refine future resource/effect contracts; no target-runtime promotion.
- `gwt`: no change; selection/use/reentry do not establish live host-resource validity.
- `emergenz`: no change; this is runtime safety evidence, not emergence evidence.
- `claycode`: define/test backend-neutral typed resource lowering in CC-WP-07 and fuzz it in CC-WP-11; no syntax/core change.
- `hyperposition`: no change; alternatives do not establish resource validity.
- `claygraph`: keep graph epoch separate from resource generation/lifetime.
- `unifieddb`: keep semantic identity/capability observation separate from live handle instance.
- `harness`: later differential tests should include stale/unknown/wrong-type handles, active-borrow close, cancellation/drop, ABA reuse and capability-state change.

## Negative results / boundaries

- No evidence that a DB-specific ClayCode core primitive is needed for this slice.
- No evidence that graph identity can substitute for runtime resource identity.
- No evidence that logical UnifiedDB resource records can substitute for a live host handle.
- No production sandbox/no-ambient-authority claim: guest Python remained an ordinary local process and the broker constrained only the tested resource path.
- No Ubuntu developer-host, H1, H2 or live-FRANK execution claim.
- No work package is marked complete from this local proxy run.

## Next highest-information test

Freeze a backend-neutral `ResourceHandle` lowering contract without changing source syntax, then compile it to the selected Ubuntu-native and/or WASM/WASI path and differentially test:

- generative resource type identity;
- own/borrow transfer and drop;
- stale/ABA handle reuse;
- cancellation and async borrow lifetime;
- capability revocation versus resource lifetime;
- absent/forged/wrong-type handles;
- semantic-hash and execution-receipt preservation.

Only a real compiler/application counterexample should reopen ClayCode core semantics.

## Run decision

`RESEARCH_DELTA = COMMITTED`  
`SCIENTIFIC_PROMOTION = NONE`  
`CLAYCODE_CORE_CHANGE = NO`  
`ROUTE = CC-WP-07 + CC-WP-11`  
`BASE_GATE = NOT_PASS`

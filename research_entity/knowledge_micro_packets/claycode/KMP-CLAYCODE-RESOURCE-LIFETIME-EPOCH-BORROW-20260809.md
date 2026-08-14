# KMP-CLAYCODE-RESOURCE-LIFETIME-EPOCH-BORROW-20260809

packet_id: KMP-CLAYCODE-RESOURCE-LIFETIME-EPOCH-BORROW-20260809
domains: [claycode, frank, unifieddb, claygraph, harness]
epistemic_class: LOCAL_PROXY_EXECUTABLE_RESEARCH_PLUS_PRIMARY_SPEC_COMPARISON
status_hint: OPEN_SUPPORTED_NOT_PROMOTED
origin_actor: chatgpt-secondary
provider: OpenAI
model: GPT-5.6 Sol
run_id: claycode_20260809T1709p0700_chatgpt_resource_lifetime_epoch
canonical_parent: r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346

## Atomic finding

A generic typed host-resource lifetime contract implemented as external runtime/FFI enforcement matched an independent oracle across 20,000 randomized operations with zero mismatches. Removing epoch/freshness, active-borrow close, or resource-type checks produced immediate executable safety counterexamples.

This bounded slice does not justify a DB-specific ClayCode core primitive. The current best route is a backend-neutral typed ResourceHandle lowering contract under CC-WP-07, with conformance/fuzz coverage under CC-WP-11.

## Boundaries

The test used a local Python guest/broker proxy, not the Ubuntu developer host and not a production sandbox. It does not prove no-ambient-authority, full FRANK safety, or that every target backend needs duplicate runtime checks when equivalent guarantees are independently verified.

Graph epoch/projection identity, UnifiedDB semantic/resource records, capability authorization freshness and live host-resource lifetime must remain distinct unless target evidence establishes a safe mapping.

## Falsifier / next test

Compile the frozen resource contract to the selected Ubuntu-native and/or WASM/WASI backend and differentially test generative type identity, own/borrow transfer, stale/ABA reuse, async cancellation/drop, capability revocation, forged/wrong-type denial and receipt/hash preservation.

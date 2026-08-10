# ClayCode Run — WP03 Typed Canonical IR Normalization

Run ID: `20260810T2014p0700-chatgpt-secondary-wp03-irnorm`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: revision 2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`

## Current-state decision

Current release state remains:

- `CC-WP-01-SPEC-FREEZE = PASS`
- `CC-WP-02-PARSER-CANON = PASS`
- `CC-WP-03-IR-TYPES = OPEN`
- `CLAYCODE_RELEASE_GATE = NOT_PASS`

This run does not reopen the BASE semantic freeze. It converts the next blocker into a narrower implementation hypothesis: place a typed canonical IR identity/normalization layer after the existing V18 parser/frontend and before the type/effect checker.

## Hypothesis and strongest counterhypothesis

Hypothesis: WP03 can close without new ClayCode surface syntax by materializing the existing G9/V18 records, sum-like symbolic types, collections, refs, epochs and authority structures into typed canonical IR, and by normalizing only constructs whose declared type semantics are unordered.

Strongest counterhypothesis: at least one mandatory self.root/GWT/Hyperposition/UnifiedDB/ClayGraph fixture requires a new core semantic primitive or an untyped escape hatch. A production fixture that fails typed lowering after the minimal implementation is the falsifier and would reopen the language question under the semantic-freeze law.

## Executable result

A current V18-compatible candidate was built for owner-fixed proactive agency, open-web authority separation, semantic/runtime identity, GWT measurement receipts and Hyperposition relations. It parsed with the existing BASE-D V18 grammar/frontend.

The executable discriminator reproduced a concrete WP03 gap in the current frontend identity:

- record field reorder produces different current frontend `semantic_hash` values;
- set literal reorder produces different current frontend `semantic_hash` values;
- a typed normalization layer makes each pair equal when the construct is explicitly unordered;
- ordered/list/effect sequences are not proposed for normalization.

Observed discriminator values:

- record frontend hashes: `d681797685ac3d8ec75b16e132461468937f648fa4a496db5eafd7a53be97aec` vs `653bea94dd6c4d8706d60199870ae0dbe4d9d7bef0c77e4f42de796f101027be`;
- record typed-normalized hash: `d57a37686572ba05902e428df8959db723d08bd722f9facf2c111fe49f325d1e` for both;
- set frontend hashes: `25e535bae8a92b50859e4d7f9ea615cc1cf42f37b0dfc269769133bb7ee88749` vs `8fcd8bffa931a82b217c7886a9b38c9b3b046b449b892a67569309d1caa0cba1`;
- set typed-normalized hash: `10e6166f45162ffe4094e97f92a69d2040e23e754b9653c893a1c38e1daa14fb` for both.

The local typed constraint probe accepted 7/7 positive fixtures, rejected 7/7 deliberate negative mutations and rejected 2000/2000 seeded open-web authority-escalation mutations.

Scope guard: this is a local/proxy executable research discriminator, not target-VPS production acceptance. Local strict LALR evidence was also not claimed because `interegular` was unavailable in the local execution environment. WP03 therefore remains OPEN.

## ClayGraph finding

Current ClayGraph separates logical node/edge identity, graph epoch, activation/salience, authority class and provenance. WP03 should preserve this separation in canonical types: semantic identity must not be confused with graph-version identity, and activation/relevance must not become truth or effect authority.

## UnifiedDB finding

Current UnifiedDB exposes state epochs, semantic transactions, idempotency keys, semantic records, query receipts, evidence references and snapshots. This strengthens the requirement for typed separation of semantic identity from state/runtime version identity and for provenance/epoch-bearing transaction and replay types. It does not force one physical storage model into ClayCode.

## GWT / Hyperposition finding

Representative `MeasurementReceipt` and `HyperRelation` structures are expressible under the current V18 syntax. The production schemas remain unresolved until the typed IR/checker and later H1/H2 differential readouts execute them. Structural parseability is evidence of expressibility only, not completion.

## Independent Goodman check

The FRANK/ClayCode capability-authority assumption received an independent implementation check against current official WebAssembly/WASI design. WASI uses capability-based sandboxing without ambient authority by default, and WIT resources expose resource handles with owned/borrowed semantics. This supports keeping descriptive `CapabilityToken` semantics distinct from the runtime bearer: the latter should lower to an opaque/owned/borrowed resource handle rather than copyable authority text.

This does not force WASI as the only backend. It informs WP07 runtime/FFI realization and preserves the existing rule that textual capability names never confer authority.

Current WASI 0.3 also provides native async primitives; that is a useful later WP09 implementation candidate, not evidence for changing WP03 surface semantics.

## Architecture delta candidate

Insert:

`V18 source -> parser/canonical frontend AST -> TYPED CANONICAL IR -> type/effect checker -> evaluator/lowering`

Typed canonical IR requirements from this run:

1. Normalize record-field order only where record semantic identity is order-insensitive.
2. Normalize/deduplicate `Set<T>` elements by typed semantic identity.
3. Preserve order for `Ordered<T>`, lists, effect sequences, preference sequences and any type whose semantics declare order significant.
4. Keep `semantic_hash` for typed executable meaning separate from exact provenance/contract/source identity.
5. Represent semantic identity separately from runtime version/state epoch where stale/ABA/replay behavior depends on version identity.
6. Keep descriptive capability data separate from opaque runtime bearer/resource handles.
7. Keep Web evidence authority fixed as untrusted/no-instruction/no-effect authority through typed checking.
8. Carry GWT measurement/intervention and Hyperposition relation/topology identities as typed structures with epoch/provenance links.

No grammar delta is proposed.

## Test obligations

Before WP03 can PASS:

- implement the typed canonical IR in the production toolchain;
- add positive/negative typed corpus for current G9/Dialect plus owner-fixed Agency/Web fixtures;
- add GWT/Hyperposition/ClayGraph/UnifiedDB representative fixtures;
- add semantic-hash metamorphic tests for unordered record fields and sets;
- add negative tests proving ordered/list/effect order is never accidentally normalized;
- add semantic-id vs runtime-version/epoch stale-identity tests;
- add forged/stale/revoked capability identity tests across the WP03/WP04 boundary;
- run the production implementation on the accepted Hostinger Ubuntu target VPS and preserve exact source/toolchain/runtime receipts;
- compile real self.root/Frank/adaptive-state fixtures without an untyped escape hatch.

## Goodman disposition

- Agency/Web expressibility: `REFINED` — current syntax is sufficient in the tested slice, but a typed semantic normalization layer is required.
- Capability bearer separation: `SUPPORTED` as implementation direction by independent official capability/resource design; target-runtime closure is still pending.
- GWT/Hyperposition production type closure: `UNRESOLVED` until production differential evidence exists.

## Re-entry / next frontier

Research delta: `SUPPORTED_IMPLEMENTATION_DIRECTION`, not package promotion.

Immediate next falsifier: implement the minimal typed canonical IR behind V18 and run its positive/negative/metamorphic corpus against current G9/Dialect plus owner-fixed self.root Agency/Web, GWT, Hyperposition, ClayGraph and UnifiedDB fixtures. If that closes without escape hatches, run the exact committed implementation on the target VPS and only then consider a WP03 PASS receipt.

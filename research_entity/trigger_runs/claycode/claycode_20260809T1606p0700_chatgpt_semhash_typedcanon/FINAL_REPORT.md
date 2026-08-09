# ClayCode Trigger Run — Type-Directed Canonical IR / Semantic Hash

Run: `claycode_20260809T1606p0700_chatgpt_semhash_typedcanon`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Promotion: **none — run-local research delta only**

## Executive result

This run isolates a canonical-identity problem that is distinct from the concurrent full-G9 parser-closure and control-flow/precedence lanes.

The executable result is that **canonicalization must be type-directed**. A serializer that sorts/deduplicates every collection-like structure can erase real ClayCode meaning. In the run-local oracle, a schema-blind canonicalizer produced the same hash for the forward and reversed ordered `external_effect` lifecycle. The typed candidate did not.

Observed:

- equivalent declared/generic relation surfaces shared one `semantic_hash` while exact surface/provenance instances retained distinct contract identity;
- **20,000/20,000** explicit `Set` permutation/duplicate variants preserved semantic hash;
- **20,000/20,000** `Ordered` lifecycle mutations changed semantic hash;
- a ClayGraph-style role/ordinal reordering changed semantic hash;
- ordinary dictionary key order did not change semantic hash;
- **50,000/50,000** semantic relation mutations changed semantic hash.

A concurrent HTTP lowering result then supplied an independent compiler-identity counterexample: fresh capability-token identity embedded in generated code changed target hashes across otherwise equivalent fresh builds. This run added a 10,000-instance discriminator:

- embedded runtime authority identity -> **10,000 distinct artifact hashes**;
- stable generated artifact with runtime capability handle -> **1 artifact hash**;
- the same 10,000 concrete authority instances remained distinguishable as **10,000 deployment/execution identities**.

The resulting OPEN identity contract is:

`semantic_hash != artifact_hash != contract_hash != deployment/execution identity`

No new FRANK-specific cognitive primitive is justified and no CURRENT ClayCode generation is promoted.

## New negative results

### N-CC-SCHEMABLIND-CANON-003

Schema-blind collection canonicalization is unsafe. It may collapse order-sensitive lifecycle, role, path, effect or replay semantics. Canonicalization must preserve order by default and normalize order/duplicates only for fields whose typed IR explicitly defines set semantics.

### N-CC-RUNTIME-AUTHORITY-ARTIFACT-HASH-004

Per-run capability/resource authority must not silently contaminate stable generated-artifact identity. Runtime authority belongs in host/deployment/execution binding and receipts unless a program explicitly makes that authority instance part of its source semantics.

## Relation to concurrent ClayCode work

Current federation state was reread before this run committed.

- Union types are already repaired in the checked-in G9 grammar and are not counted as a current blocker.
- The full-G9 worker reports 61/86 CURRENT top-level chunks accepted by the current executable grammar proxy and 25/86 failing. Its normalization candidate reaches 86/86 but is explicitly not yet selected as the source-surface winner.
- The control-flow/precedence worker independently shows that parser closure alone is insufficient: eager conditional normalization can execute unselected effects and flat operator grouping materially changes results.
- Generic quoted RelationId and declared relation surfaces remain OPEN competing/compatible reader surfaces over a possible shared typed Relation IR.

This run adds the missing identity constraint for comparing those surfaces: alternatives may be called semantically equivalent only after they lower into the same **typed** canonical IR and produce the same semantic hash without erasing ordered/higher-order structure.

## Cross-branch fusion

### FRANK

The fused FRANK target requires causal/semantic/authority distinctions, replay identity and atomic semantic publication to survive representation changes. Type-directed canonical identity is compatible with those constraints; surface equality alone is not evidence of architectural equivalence.

### ClayGraph

ClayGraph V2 represents hyperrelations with explicit member roles and optional ordinals. Those fields constrain canonicalization: a convenient parser relation representation must not sort away role/order semantics or flatten n-ary structure into a binary identity.

### UnifiedDB

UnifiedDB depends on revisioned state, transaction/work identity and receipts. Semantic hashes can support replay/deduplication only if canonicalization preserves the typed distinctions on which those transitions depend.

### GWT / Emergenz

Hash equality is representation identity evidence, not evidence of workspace use, causal outcome, re-entry or emergence. Existing intervention/readout requirements remain unchanged.

### Hyperposition

Higher-order relations, role bindings and topology identities are direct counterconstraints against schema-blind collection normalization. Pairwise/binary reader conveniences must not erase higher-order identity.

### Harness

The active state-ledger/replay work makes this a near-term H1/H2 requirement: Reference and Clay Harness traces need deterministic typed identity, while H2 differential tests must reject cases where different ordered/effect semantics accidentally receive the same canonical hash.

### Clay / Ubuntu target

The current v0.1 target is Andreas' Ubuntu Linux developer system. Runtime authority-instance binding therefore belongs in the Ubuntu host capability/effect layer and execution receipts, not in stable semantic identity merely because a host token exists.

## External triangulation

MLIR independently demonstrates that a common IR can have generic and custom/readable textual forms. RFC 8949 independently demonstrates that deterministic encoding requires explicit deterministic rules rather than relying on incidental serializer behavior. These are architecture analogues only; the ClayCode conclusion rests on the executable project-specific counterexamples above.

## Goodman anti-echo

The FRANK requirement was not promoted merely because ClayCode and FRANK agree. Shared ancestry was collapsed. Independent evidence came from:

- the run-local Set/Ordered/role hash oracle;
- the run-local authority/artifact/deployment discriminator;
- the concurrent HTTP target-hash counterexample;
- external compiler/serialization patterns used only as triangulation.

Verdict: `REFINED`. Production parser/typed-IR/Ubuntu replay evidence remains required.

## Hypotheses

- `H-CC-TYPED-CANON-011` — OPEN, supported by executable micro-oracle: canonicalization should be driven by explicit type semantics.
- `H-CC-DUAL-SURFACE-HASH-012` — OPEN: equivalent generic/infix reader surfaces may share semantic identity while retaining distinct source/provenance identity.
- `H-CC-AUTHORITY-INSTANCE-SEPARATION-013` — OPEN, supported by local discriminator plus concurrent HTTP counterexample: per-run authority identity should be separated from stable artifact identity.

## Coordination / limitations

The current ClayCode federation contract was observed. `CURRENT_DYNAMIC_WORK.clay` is absent from the repository export, so full live UnifiedDB federation state could not be verified. The run therefore records degraded repo-native coordination rather than a federation PASS.

A GitHub 409 occurred on the first durable write because another worker advanced the repository. The write was not forced; the new head was reread, concurrent work was assimilated, and only then were append-only run artifacts written.

The official `research_interconnect_preflight.py` could not be executed because this hosted ChatGPT execution surface has no repository checkout. The manual interconnect manifest is fail-closed and does not claim official preflight PASS. E2B is repository-marked runtime-verified but is not exposed as a callable tool here, so local execution was used and no fresh E2B evidence is claimed.

## BASE implication

`CC-WP-02-PARSER-CANON`, `CC-WP-03-IR-TYPES`, `CC-WP-07-RUNTIME-ABI-FFI` and `CC-WP-11-FUZZ-CONFORMANCE` remain OPEN.

The next production compiler requirement is now sharper:

1. parse the complete admitted G9+dialect corpus;
2. lower every surface candidate to a typed canonical AST/IR;
3. mark collection/role/path semantics explicitly as Set/Ordered/etc.;
4. compute semantic identity from typed IR, not raw syntax;
5. keep exact source/provenance contract identity separately;
6. keep runtime capability/resource instance identity in deployment/execution receipts;
7. differential-test parse -> IR -> print -> parse -> evaluate/replay across N/S/D surfaces and H1/H2 traces.

Only after those tests should a source-surface policy or BASE parser/canonicalizer package be promoted.

## Research delta

Durable delta committed by this run:

- type-directed canonicalization executable evidence;
- schema-blind canonicalization negative result;
- semantic/contract/artifact/deployment identity separation candidate;
- runtime-authority artifact-hash negative result;
- 20k Set + 20k Ordered + 50k semantic-mutation hash tests;
- 10k authority-instance artifact/deployment discriminator;
- Goodman review, 9-branch interconnect, tool manifest and center/work handoff;
- no canonical/current-stack/BASE promotion.

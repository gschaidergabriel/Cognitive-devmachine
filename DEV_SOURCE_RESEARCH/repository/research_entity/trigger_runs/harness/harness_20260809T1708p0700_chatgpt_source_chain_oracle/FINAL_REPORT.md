# Harness Run — SourceChainEvidence v1

Run: `harness_20260809T1708p0700_chatgpt_source_chain_oracle`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Scientific promotion: **NONE**  
Stage progress credit: **NONE**

## Result

A narrow executable Harness validator was added for the new BASE source-chain evidence requirement that emerged from current ClayCode negative results and live Fusion feedback.

The validator requires an explicit evidence chain:

`source -> parse -> typed_ir -> lowering -> execution -> replay`

and rejects silent discontinuities in artifact ancestry, parser admission, semantic identity, type/effect contract identity, lowering contract identity, execution receipts and replay state.

It also directly regressionizes the two current negative results:

- `N-CC-SOURCE-CHAIN-BYPASS-007`: a named-cycle fixture cannot be counted as production compiler evidence when the referenced grammar does not admit that header form.
- `N-CC-EMIT-RETURN-SEMANTIC-LEAK-008`: lowering `emit` to terminating host-language `return` is rejected unless source semantics explicitly declare `emit` terminating.

## Why this was selected

The current staged program remains at `BASE_CLAYCODE_RELEASE`; H1/H2/H3 are blocked downstream. A sibling Harness worker had already implemented the broader TurnTraceEnvelope validator and another sibling had claimed the Needle boundary. The live Fusion then introduced a stricter source-chain gate not present in the TurnTraceEnvelope code. This run therefore took a non-overlapping BASE evidence sublane rather than duplicating state-ledger, trace-envelope or Needle work.

## Mesh grounding

The run uses the current whole-mesh live Fusion refresh as compact nine-branch coverage, then cross-reads newer Harness, ClayCode and ClayResearch overlays. `INTERCONNECT_MANIFEST.json` records the exact branch effects.

The strongest post-baseline inputs were:

- Harness TurnTraceEnvelope v1 plus its local synthetic execution receipt;
- ClayCode source-chain negative evidence and 20,000-case emit-termination discriminator;
- ClayCode cross-runtime numeric canonicalization probe;
- ClayResearch CTK convergence requirement for an executable parse-to-replay conformance chain.

## Build artifacts

- `research_entity/harness/source_chain_oracle_v1.py`
- `research_entity/harness/test_source_chain_oracle_v1.py`

The Oracle is intentionally separate from the existing TurnTraceEnvelope module so the fresh sibling artifact is not overwritten and the new evidence layer can be integrated explicitly later.

## Executed tests

Exact committed logic was exercised locally in the hosted Linux sandbox.

- Unit regressions: **8/8 PASS**.
- Targeted invalid mutation sweep: **5,000/5,000 invalid cases rejected**.
- Differential false-equivalence sweep: **5,000 cases, 0 false equivalents** when final state matched but lowering-contract identity differed.

These are `LOCAL_SYNTHETIC_EXECUTION_NOT_TARGET_UBUNTU`. They do not prove production ClayCode parser/compiler/runtime correctness and do not count as live FRANK evidence.

## New executable constraint

For BASE/H2 evidence, matching final behavior/state is insufficient. A candidate must retain comparable semantic identity across the production compiler chain. In particular, H2 differential validation should compare at least:

- admitted source semantic identity;
- grammar/parser identity;
- canonical typed-IR semantic identity;
- type/effect contract identity;
- lowering contract identity and explicit semantic-delta status;
- target execution receipt/state identity;
- replay receipt/state identity.

The recent numeric-canonicalization finding adds a related requirement: the semantic hashes used in this chain must themselves rely on explicit typed canonicalization, not host-native JSON number formatting.

## Negative/limitation results

1. This worker could not clone GitHub directly into the container because outbound DNS/network access was unavailable. Canonical repository access and writes therefore used the connected GitHub connector.
2. SourceChainEvidence v1 validates supplied external artifact hashes but does not fetch/re-hash every referenced artifact byte itself. A production receipt collector must bind these fields to actual bytes.
3. The production ClayCode parser/compiler/runtime does not yet have a released BASE chain in the current program workspace, so the new Oracle cannot yet execute a real production source-to-runtime witness.
4. No execution occurred on Andreas' exact Ubuntu developer system.
5. No BASE, H1, H2 or H3 PASS is claimed.

## Branch feedback

`BRANCH_FEEDBACK_MANIFEST.json` records explicit feedback for every registered branch. Material change is limited to ClayCode/Harness evidence requirements; architecture/scientific claims in FRANK, GWT, Emergenz, Hyperposition, ClayGraph and UnifiedDB remain unchanged.

## Next discriminating action

As soon as the production ClayCode BASE parser/canonicalizer/type-effect/lowering/runtime path exists, wire this Oracle into its receipt collector and execute the named-cycle and emit-termination regressions end-to-end on the Ubuntu target. If production semantics legitimately differ, the difference must be explicit, content-addressed and receipted rather than hidden in lowering.

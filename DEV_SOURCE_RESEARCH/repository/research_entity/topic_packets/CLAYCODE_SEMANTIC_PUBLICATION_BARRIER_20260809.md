# Topic Packet — ClayCode Semantic Publication Barrier

**status:** OPEN / BASE acceptance candidate  
**origin run:** `claycode-20260809T1603p0700-chatgpt-semantic-publication`  
**canonical parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Compact synthesis

ClayCode does not currently need a dedicated transaction/publication keyword to represent the tested FRANK/UnifiedDB/ClayGraph coherence boundary. A standard typed IR/runtime contract is the smaller current target:

`SemanticPublicationReceipt + PublishedSemanticEpoch`

The contract separates:

1. committed canonical UnifiedDB state epoch;
2. derived ClayGraph epoch bound to that exact source epoch;
3. reader-visible CURRENT publication that advances only after projection/retraction closure and validation.

A local executable semantic oracle passed 12/12 fixed adversarial cases and 20,000 mutation rounds without a mixed-reader-epoch or graph-derived authority violation. This is representability/falsification evidence only, not production compiler or split-store durability evidence.

## Constituent micro-packet

- `research_entity/knowledge_micro_packets/claycode/KMP-CLAYCODE-SEMANTIC-PUBLICATION-BARRIER-20260809.md`

## Preserved negative result

`NR-CC-NEW-PUBLISH-SYNTAX-20260809`: adding a new language keyword now is not justified. The counterhypothesis remains live: the real BASE type/effect checker or a physically split deployment may expose an unrepresentable partial-publication state.

## Mesh links

ClayCode BASE · FRANK P10/P11 · UnifiedDB transaction/epoch plane · ClayGraph projection epochs · Harness crash/replay differential · Clay Semantic Coupling Fabric.

GWT, Hyperposition and Emergenz receive `NO_CHANGE` on mechanism: their existing readouts/alternatives/evidence must simply reference the coherent published epoch tuple.

## Highest-information next test

Freeze the receipt types in production canonical IR, compile them through the real BASE parser/type-effect checker/runtime, then inject crashes before/after state commit, during/after graph rebuild, and before/after publication across physically separate canonical and derived stores. Require deterministic replay, no mixed CURRENT, no incomplete retractions, stable hashes and no authority amplification.
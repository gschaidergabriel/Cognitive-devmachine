# KMP — CC11 MRSC × E2B: Triple-Bound Identity Candidate

**Upstream:** CC-RC1.6 Certified Multi-Rail Semantic Compiler (CC11)  
**New executable evidence:** E2B ClayCode-Lab v0.1/v0.2  
**Receipt:** `research_entity/runtime/executable_research_receipts/claycode-e2b-20260808T2034p0700.json`  
**Status:** OPEN refinement candidate; no promotion

## Why this changes CC11

CC11 already discovered that a critical projection receipt must bind both:

1. canonical source/input identity; and
2. exact emitted reader-view identity.

Its `ProjectionReceiptV2` therefore prevents a reader payload from changing while a source-only receipt remains valid.

The first real E2B compiler loop now splits CC11's item (1) into two distinct identities:

- **canonical semantic identity** — are the executable semantics equivalent?
- **canonical contract-instance/provenance identity** — is this the exact committed Proposal/Adequacy/ancestry instance?

ClayCode-Lab v0.1 exposed the failure: one hash treated reordering/duplicate set-like constraints as semantic changes.
ClayCode-Lab v0.2 repaired this by adding `semantic_hash` while retaining provenance-bound `contract_hash`.

## New CC11 candidate: Triple-Bound Projection Receipt

For critical P1 -> P2 reader projections, test replacing the conceptual two-way binding:

`canonical_input_hash + projected_view_hash`

with explicit three-way identity:

`canonical_semantic_hash + canonical_contract_hash + projected_view_hash`

plus CC11's existing:
- schema/compiler/reader identity;
- role-binding hash;
- basis epochs;
- loss declaration;
- required-semantics coverage;
- validation refs.

### Intended semantics

- `canonical_semantic_hash` answers: **same executable meaning?**
- `canonical_contract_hash` answers: **same committed source/provenance instance?**
- `projected_view_hash` answers: **same bytes/symbols actually delivered to the reader?**

None substitutes for the others.

## Hypothesis H-CC11-E2B-001

A triple-bound receipt can reduce false inequality of semantically equivalent canonical inputs without weakening replay/provenance integrity or emitted-view integrity.

### Falsifier

Construct transformations across:
- reorder/duplicate operations declared `SET`;
- explicitly ordered operations;
- source/provenance mutation with same semantic meaning;
- semantic mutation with same superficial source shape;
- projected-view mutation;
- stale basis/epoch;
- role/class swap.

The candidate fails if any of these occur:
- semantically different canonical inputs collide on semantic hash;
- provenance-distinct instances become indistinguishable where ancestry is required;
- view mutation passes without view-hash change;
- ordered semantics are incorrectly normalized as sets;
- semantic equivalence checking costs outweigh its use on hot paths without a tiered strategy.

## Compiler-design consequence

Collection semantics must become typed compiler metadata, not inferred from Python list usage:

- `SET<T>` — order-insensitive, duplicate-idempotent;
- `ORDERED<T>` — order is semantic;
- `MULTISET<T>` — multiplicity semantic, order not;
- future `WEIGHTED<T>` / priority structures — explicit weights/priorities semantic.

Only `SET` may use the v0.2 normalization rule demonstrated in E2B.

## Mesh consequences

- **ClayGraph:** semantic relation identity vs provenance/event-instance identity should be separate keys when relation operands are canonically set-like; ordered/n-ary role bindings remain role-sensitive.
- **FRANK:** Reader/View Compiler receipts should carry semantic equality and exact ancestry separately before projection/view binding.
- **Hyperposition:** identity/firebreak checks must declare comparison axis (`semantic`, `instance/provenance`, `view`, `basis/epoch`).
- **GWT/Emergenz:** matched arms may pin semantic identity while deliberately varying provenance/view identity, or vice versa, rather than bundling them.

## Next E2B experiment

Implement typed collection kinds in ClayCode-Lab and run mutation/property tests over all three identities. Then integrate the passing rules into a CC-RC1.6 MRSC reference compiler rather than treating the lab surface as production syntax.

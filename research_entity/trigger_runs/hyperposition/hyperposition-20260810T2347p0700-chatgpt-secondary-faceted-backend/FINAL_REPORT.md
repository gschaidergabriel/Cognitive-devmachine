# Hyperposition — Faceted Backend / Higher-Order Reduction Run

Run: `hyperposition-20260810T2347p0700-chatgpt-secondary-faceted-backend`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: revision 2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program target: Frank v0.1 / `self.root` on accepted target VPS  
Evidence class: local executable falsifier + current repo contracts + primary external research. Not target-VPS acceptance evidence.

## Question

Can Hyperposition preserve unresolved alternatives and true n-ary semantic identity while allowing the physical runtime to use a simpler pairwise backend when that backend is demonstrably equivalent?

## Hypothesis H-HP-FACET-1

Keep an n-ary `HyperpositionRelation` as semantic identity and make physical representation a verified lowering choice. Candidate backends:

- `PAIRWISE_ONLY` only if reduction error is exactly zero under the declared visible variables;
- `LATENT_FACTOR_STAR` as a finite-domain equivalence fallback;
- `NATIVE_NARY` when runtime support/cost makes it preferable.

Semantic topology hash, active topology hash and physical topology hash remain distinct.

## Strongest counterhypotheses

1. **C1: pairwise-only over the original variables is always enough.**
2. **C2: if n-ary semantics matter, a physically native hyperedge runtime is mandatory.**
3. **C3: PID/PEID can serve as the universal irreducibility gate.**

## Executable falsifier

`hyperposition_backend_v1.py` was executed locally under CPython 3.13.5 on Linux x86_64.

### XOR relation

Visible variables `(a,b,c)` with `c = a XOR b` define four valid tuples.

An exhaustive search over all `16^3 = 4096` conjunctions of hard pairwise relations on `(a,b)`, `(a,c)`, `(b,c)` found:

- exact pairwise models: **0**;
- best pairwise visible-state error: **2 states**;
- native n-ary valid states: **4**;
- lesion of the n-ary constraint: **8 visible states**;
- rescue: **4 visible states**;
- context clamp `a=1`: **2 visible states**.

Result: C1 is refuted for this relation under matched original visible variables.

### Hidden-factor lowering

For any tested finite relation, create a latent factor `H` whose states correspond to admitted n-ary tuples and pairwise compatibility edges `H--Xi` binding each visible coordinate.

Randomized differential test:

- seed: `0xC1A7`;
- trials: **1000**;
- arity: **3..6**;
- per-variable domain size: **2..4**;
- maximum Cartesian size tested: **4096**;
- maximum admitted relation size tested: **2329**;
- projection mismatches native n-ary vs latent-star: **0**.

Local microbenchmark on this verifier showed similar projection cost for these small Python representations; these numbers are not deployment evidence.

Result: C2 is refuted for the tested finite unweighted relation class. Physical n-ary storage is not semantically mandatory if the lowering carries an explicit projection-equivalence receipt and retains the original semantic relation identity.

## External evidence / counterevidence

- Bacchus & van Beek, *On the Conversion between Non-Binary and Binary Constraint Satisfaction Problems* (AAAI 1998), and Dubois, *Formally Verified Transformation of Non-binary Constraints into Binary Constraints* (2020), independently support the existence of equivalent hidden-variable binary encodings for finite non-binary CSPs.
- Bian, Zhou & Bi, *Beyond Pairwise Interactions: Unveiling the Role of Higher-Order Interactions via Stepwise Reduction* (arXiv:2411.05685), reports that higher-order structure is useful in some networks and negligible in others. This supports a measured backend/reduction decision rather than universal hyperedge promotion.
- Lyu, Clark & Raviv, *Multivariate Partial Information Decomposition: Constructions, Inconsistencies, and Alternative Measures* (arXiv:2508.05530), gives counterexamples/impossibility results for broad multivariate PID lattice decompositions. Therefore PID/PEID remains an optional estimator/readout, not a release or irreducibility gate.
- Chen, Erwig & Walkingshaw, *A Calculus for Variational Programming* (ECOOP 2016), provides independent precedent for explicit typed variation/alternatives without forcing immediate selection.
- `egg` equality saturation is useful for compactly maintaining **equivalent** program alternatives, but equivalence classes are not a substitute for epistemically conflicting/non-equivalent Hyperposition alternatives.

## Architecture delta — HP-FACETED-BACKEND-V1

### Semantic plane

Preserve:

- `HyperpositionAlternativeSet`;
- `HyperpositionRelation` with role-ordered n-ary semantic identity;
- context and compatibility/exclusion state;
- evidence/provenance/uncertainty;
- GWT epoch/WorkspaceEpisode cross-links.

### Physical/lowering plane

Add `HyperpositionLoweringPlan` with:

- semantic hash;
- physical hash;
- backend identity;
- visible and latent variables;
- pairwise-reduction error;
- equivalence verification receipt;
- rollback.

### Backend selector law

`PAIRWISE_ONLY` is legal only when measured reduction error is zero.  
`LATENT_FACTOR_STAR` is legal only after projection equivalence.  
`NATIVE_NARY` remains a cost/performance option, not semantic authority.

Backend selection must compare latency, memory, contention, recovery complexity and incremental invalidation cost. Semantic identity never changes merely because physical lowering changes.

## Hyperposition readout delta

Primary irreducibility evidence becomes a vector, not a score:

- exact pairwise reduction error;
- intervention-response mismatch;
- state/replay divergence;
- lesion loss;
- rescue recovery;
- optional information-synergy estimator with estimator/version/limitations;
- semantic/active/physical topology hashes;
- cost shadow.

PID/PEID is demoted from any implicit universal role to `OPTIONAL_ESTIMATOR` until estimator-specific validity is established.

## ClayGraph feedback

Current ClayGraph V2 already stores logical hyperrelation identity, typed members/roles, graph epoch and projection receipts. The new requirement is to keep the semantic hyperrelation identity stable when a physical/backend projection introduces latent factor nodes. Derived graph topology may expose the factor-star physical plan, but may not replace the logical hyperrelation or mint truth/authority.

## UnifiedDB feedback

UnifiedDB semantic records/epochs/transactions are sufficient as a logical persistence surface for the candidate. Store the semantic relation and lowering plan as separate typed records linked by epoch/hash/receipt. Do not infer that one physical database or one graph representation is required.

## ClayCode feedback

No executable counterexample was found that requires reopening `CLAYCODE_BASE_SEMANTIC_FREEZE_V1`.

The frozen G9 substrate already has `Set`, `Ordered`, `Hyperrelation`, `GraphDelta.hyperrelations`, `Conflict`, `Unknown`, hashes, evidence refs and projection receipts. Therefore the next move is implementation, not language redesign:

1. WP03 TypedIR: add typed Hyperposition alternative/relation/lowering/readout nodes using existing semantic primitives.
2. WP04 Type/effect: enforce semantic-hash preservation and forbid backend/readout from minting truth or effect authority.
3. WP06 Lowering: implement native-nary and hidden-factor-star backends behind one semantic relation identity.
4. WP11 Fuzz/conformance: property-test projection equivalence, clamp/lesion/rescue, stale epoch rejection and rollback.

## Status of hypotheses

- H-HP-FACET-1: **SUPPORTED AS CANDIDATE**, local finite-domain evidence only.
- C1 pairwise-only original variables universal: **REFUTED** by XOR exhaustive search.
- C2 physically native n-ary backend mandatory: **REFUTED FOR TESTED FINITE RELATIONS** by latent-star differential fuzz.
- C3 PID as universal gate: **CHALLENGED / NOT ADOPTED** by current multivariate PID counterevidence.

## Next falsifier

Run the exact current ClayCode frontend -> TypedIR -> lowering chain on the candidate source, then execute both `NATIVE_NARY` and `LATENT_FACTOR_STAR` on the accepted Ubuntu target VPS with matched fixtures. Require:

- zero semantic projection mismatch;
- stable semantic hash across backend changes;
- explicit physical hash change;
- lesion/rescue equivalence;
- stale epoch rejection;
- crash/restart replay;
- latency/RAM/CPU/storage/DB metadata;
- a corpus including sparse/dense, weighted/probabilistic and continuous-boundary counterexamples.

Until that passes, this is a research/implementation candidate, not a promoted runtime architecture.

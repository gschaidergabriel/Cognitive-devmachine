# Hyperposition H1 Experiments

## EXP-HYP-H1-NARY-001 — Pairwise information-equivalence counterexample

**Class:** executable synthetic/formal counterexample  
**Runtime:** local Python sandbox  
**Question:** Can role-pair projections always reconstruct a ternary relation?

Constructed two ternary Boolean relations:

- `R_even = {(a,b,c) | a XOR b XOR c = 0}`
- `R_odd  = {(a,b,c) | a XOR b XOR c = 1}`

Each relation has four tuples. For each role pair `(1,2)`, `(1,3)`, `(2,3)`, both relations project to the same complete set `{00,01,10,11}`. Therefore all pairwise projections are identical while the full ternary relations are disjoint.

**Result:** pairwise role projections are not sufficient in general to preserve n-ary grouping/higher-order information. A relation-instance representation (native hyperedge or role-aware reified node) is required when this information matters.

**Boundary:** this does not prove native hypergraph storage is necessary. It proves only that a representation retaining relation-instance identity/roles is necessary for this class.

## EXP-HYP-H1-CASCADE-002 — Tail change-amplification proxy

**Class:** executable synthetic proxy  
**Runtime:** local Python sandbox  
**Seed:** 42  
**Graph:** 50,000-node DAG, 150,532 dependency edges (~3.01 parents/node), mixed local/global parent selection.  
**Intervention:** choose seed nodes; each touched dependency propagates consequential invalidation with probability `p`.  
**Metrics:** affected node fraction and incremental work fraction versus full traversal `(N+E)`.

Selected 30-trial results:

| p | seeds | mean affected | p95 affected | mean incremental work/full |
|---:|---:|---:|---:|---:|
| 0.30 | 100 | 1.37% | 2.58% | 1.33% |
| 0.40 | 100 | 9.62% | 19.29% | 8.72% |
| 0.50 | 100 | 37.61% | 52.08% | 34.38% |
| 0.50 | 1 | 1.97% | 19.75% | 1.65% |
| 0.50 | 1000 | 55.64% | 60.44% | 54.01% |

**Result:** the same mean regime can hide large cascade tails; with one seed at `p=0.5`, mean affected fraction was ~1.97% while q95 was ~19.75%. Incremental work remained lower than a full traversal in this toy, but the margin collapses as affected fraction rises.

**Implication:** `R_delta` should not be a single mean scalar. FRANK should record at least affected-state fraction distribution, q95/q99 cascade size, touched-edge work, recovery time and rebuild crossover.

**Boundary:** Python graph topology and propagation rules are synthetic and not calibrated to live FRANK.

## EXP-HYP-H1-TOOL-003 — Execution-surface verification

- GitHub connector: successful internal canonical reads and external implementation inspection.
- Local sandbox: successful executable experiments above.
- Native web: successful scholarly/primary-source fallback.
- Direct repository clone/network shell: failed (`Could not resolve host: github.com`), confirming provider scripts cannot be assumed executable from this sandbox.
- E2B: canonical registry marks credential not persisted for this runtime path; not used.

# ATOMIC FINAL REPORT — Executable Contract Tomography (ECT)

## Result
This run did **not** extend the previous CJC causal-order family. Fresh current-head evidence moved the highest-leverage target to ClayCode WP04, where the mesh reports 27 exact target+arity obligations and zero execution without an independently justified exact `CallContract`.

Selected possibility: **ATOMIC-CANDIDATE-ECT-001 / Executable Contract Tomography**. ECT keeps a finite declared contract domain as unresolved Hyperposition and reduces it only through sandbox/static verifier witnesses bound to current `self.root`, runtime identity and semantic epoch. It explicitly forbids contract inference from names, paths, role resemblance or model confidence. A singleton is still not admitted until a final exact verifier PASS. The resulting `CallContractWitness` carries no effect authority.

## External collision
Broad novelty was refuted. CEGIS/OGIS, syntax-guided synthesis, synthesis modulo black-box oracles and active automata learning are established. Proof-carrying actions and IFC are also prior art. ECT is therefore only a **NOVEL_COMBINATION_CANDIDATE** in the narrow ClayCode/self.root/CallContract setting, not a world-first claim.

## Executable proxy
A synthetic finite-domain Python reference harness was executed locally. It models arities 0..5, 8 argument types, 8 return types and 6 effect classes, with current/stale identity/epoch and sandbox gates.

50,000 randomized contracts:
- FIELD_VALUE_WITNESS exact recovery: 1.0; query p50 5, p95 8, p99 8, max 8.
- FIELD_ONLY_WITNESS exact recovery: 1.0; query p50 15, p95 29, p99 34, max 45.
- blind lexicographic finite-search rank proxy: p50 2,646; p95 1,114,491.
- random-without-replacement rank proxy: p50 2,660; p95 1,101,987.
- six explicit negative tests passed: stale epoch, wrong native self, unsafe effect probe, weak Boolean-only diagnostic and authority non-minting among them.

These numbers are **synthetic query-complexity evidence**, not real Frank runtime performance. Blind-search figures are computed ranks, not millions of executed calls.

## Counterevidence / boundary
The strongest conventional baseline wins decisively whenever available: authenticated exact static metadata requires one read. ECT is justified only for obligations lacking such metadata. More importantly, field-value performance assumes a trusted verifier that can produce semantically distinguishing diagnostics. With Boolean-only mismatch, ECT intentionally refuses to infer hidden semantics and stays UNKNOWN. If the real callable domain is incomplete/open-ended or the verifier is not sound enough for exact elimination, ECT cannot promote a contract.

## Decision
**NO ARCHITECTURE PROMOTION.** Status: `SUPPORTED_SYNTHETIC_PROXY_RETEST`.

The next discriminator is concrete and current: census the 27 WP04 obligations for exact authenticated metadata; apply ECT only to the unresolved remainder; test on the accepted Hostinger target/static verifier with stale identity, epoch, witness corruption, unsafe-effect and crash/recovery controls; compare against the smallest conventional exact resolver. If real diagnostics do not provide trustworthy distinguishing witnesses, record ECT as `NO BENEFIT / REFUTED FOR WP04` rather than weakening the exact-call gate.

## Late concurrency refresh
Before durable write, the research head advanced. Concurrent `SCF-001` is researching cross-module semantic minting/laundering, while ClayCode V18 repaired frontend `contract_hash` binding and registry-v3 mesh handling. The current cutoff explicitly states that WP03/WP04 were not promoted and the Needle CallContract discriminator remains negative gap evidence. ECT therefore continues only as a complementary unresolved-CallContract recovery possibility; it does not overwrite SCF or V18 work.

# GO FINAL SYNTHESIS — CAS-safe swarm pivot from WP03 duplication to WP04 evidence frontier

Run: `go-20260810T2032p0700-chatgpt-secondary-cas-wp04-frontier`  
Actor: `chatgpt-secondary / OpenAI / GPT-5.6 Sol`  
Status: `MATERIAL_RESEARCH_AND_COORDINATION_DELTA_COMMITTED / NO_PACKAGE_OR_ARCHITECTURE_PROMOTION`

## 1. What changed

This GO invocation began at the current ClayCode BASE critical path and initially found that the generic `tools/claycode_base_typed_ir.py` path still defaulted to V7/reparse behavior while WP02 had accepted a V18 frontend and explicitly required a receipt-bound FrontendArtifact -> TypedIR no-reparse next falsifier.

A minimal content-verified no-reparse bridge and exactly one bounded local experiment were prepared. Before mainline effect, CAS rejected the prepared commit as non-fast-forward because concurrent workers had advanced main. Refresh showed that another worker had already committed a stronger receipt-bound V18 bridge and explicit no-reparse/tamper validation. The duplicate code was therefore not forced or remerged.

This is a positive swarm result: stale-write prevention worked, duplicate implementation was suppressed, and shared state changed the plan before effect.

## 2. Exactly one out-of-box experiment

`GO-OOB-PROVENANCE-ISOTOPE-20260810` was this macrocycle's sole deliberately unusual experiment.

In a local proxy contract model:

- identical canonical AST with different source provenance preserved one semantic identity;
- grammar binding mismatch failed closed;
- canonical AST tampering failed closed.

The experiment passed inside its bounded model. It is not target-VPS acceptance and, after concurrent bridge discovery, is classified as same-ancestry convergent evidence rather than independent replication. No second OOB experiment was run in this macrocycle.

## 3. Live target-VPS fusion

Fresh swarm evidence provided real target-VPS runs in `gschaidergabriel/Dr.-Unterweger`.

Workflow `31392402946`, job `agency-web-core`, ran on runner `clay`, machine `digital-retina`, with exact content-address checks for the selected V18 compiler stack. Its tested typed-state scope passed: 10 closed sum types, 10 required records, 63 rule/invariant semantics, zero binding ambiguities, Agency/ResearchQuestion/Experiment state-identity checks PASS, web-authority separation PASS, no untyped escape in required records, zero implicit execution, effect/truth authority NONE. The receipt itself says WP03 remains `OPEN_PENDING_FULL_DIRECTIVE_FIDELITY_AND_DOWNSTREAM_CONSUMPTION`; therefore no WP03 package PASS is claimed here.

Workflow `31392404848`, job `call-constraints`, also succeeded on the same target runner. It measured 27 exact target+arity call identities, 59 type-equality constraints in 37 components, zero exact declared matches, 26 unresolved signatures, one effect-boundary missing-signature obligation, zero execution-admitted calls, rejected fuzzy/suffix resolution and signature invention, and produced an 18-signature theoretical component-cover plan. The strongest current WP04 result is therefore a negative one: do not manufacture concrete CallContracts from names, caller constraints or apparent behavior.

## 4. Source-network deepening

Current G9, DialectRegistry, Reward successor and historical Project-Frankenstein NAcc lineage were checked for independently justified high-leverage signatures.

They provide useful role/type/lineage evidence but do not declare the missing concrete global signatures. In particular, the DialectRegistry declares `Verifiable.verify(receipt:ReceiptRef)->Verification`, but that is not evidence that the distinct global `verify/5` and `verify/1` call sites share that contract. Likewise, Reward successor call sites establish causal role but not full callable type signatures.

PR #178 already contains a versioned `CallContract` / `CallContractObligation` schema that can represent `UNRESOLVED_SIGNATURE` fail-closed. A new schema would be duplicate work.

## 5. Fresh external fusion

Current official MLIR material supports an extensible typed IR with operation/type-specific semantics and verification, including the fact that order is semantic only where the corresponding construct says so. Current WIT material distinguishes owned and borrowed resource handles. Current Wasmtime release/security evidence also shows why a mature sandbox backend cannot be assumed to replace Clay's deterministic effect-authority layer: an affected WASI `path_open(TRUNCATE)` host-permission bypass was patched in May 2026.

Disposition: keep Clay semantic/type/effect authority backend-neutral; use MLIR/WIT/WASI as lowering/runtime candidates, not semantic authority. No new ClayCode surface syntax is justified by this evidence.

## 6. Work-state repair

The old `WORK-CLAYCODE-BASE14-CLOSE-20260809` was formally stale: it used `FRANK_V0_1_ANDREAS_PC`, preferred Andreas' local Ubuntu host and contained an invalidator that fires when that machine ceases to be the v0.1 target. Current owner-fixed semantics place self.root on the accepted Hostinger target VPS.

This GO run therefore:

1. append-only cancelled the stale work;
2. created `WORK-CLAYCODE-BASE14-TARGET-VPS-20260810` with goal `SELF_ROOT_V0_1_TARGET_VPS_API`;
3. revised it after fresh WP03/WP04 target-VPS receipts so already-covered scope is not blindly repeated;
4. revised it again after a concurrent borrow/re-entry GO result added a candidate lifecycle differential for stale/revoked/reconstructed/revalidated bearer state.

The lifecycle refinement is only a test obligation. It does not change current Clay semantics or effect authority.

## 7. q23 / mesh reentry

q23 receives the reusable typed evidence boundary: visual/web instruction-like content should use the same untrusted evidence + epoch/provenance + no-authority semantics instead of creating modality-specific authority. q23's Qwen/vision-feature target-VPS resource inventory remains unresolved and nonblocking while BASE is the critical path.

Branch feedback was routed to claycode, harness, frank, gwt, UnifiedDB, ClayGraph, q23 and atomic. No branch received release credit from research volume.

## 8. Current frontier

The current repository workspace still records only:

- CC-WP-01 PASS;
- CC-WP-02 PASS;
- CC-WP-03 OPEN;
- CC-WP-04..14 OPEN;
- BASE release gate NOT_PASS.

Therefore this GO run adds **zero new package PASS credit**.

Highest-value next actions are:

1. close only the remaining WP03 full-directive-fidelity/downstream-consumption obligations not already covered by workflow 31392402946;
2. for WP04, locate or explicitly author versioned callable interfaces only when semantically justified, then remeasure the exact 37-component constraint graph; unresolved calls remain fail-closed;
3. once effect/runtime bindings exist, run target-VPS currentness/lifetime differentials for stale/revoked/reconstructed/revalidated capability/resource states;
4. continue WP05..WP14 only by their dependency/receipt gates;
5. keep q23 vision-feature work concurrent only when spare capacity does not displace BASE.

No Frank/self.root Harness mutation was authorized or performed. No paid/final training was authorized or attempted.

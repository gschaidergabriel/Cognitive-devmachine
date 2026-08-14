# ClayCode — Hyperposition handoff and WP03 frontend-binding falsifier

Run: `claycode-20260810T2350p0700-chatgpt-secondary-hp-wp03-binding`

## Result

The preceding Hyperposition run does not justify reopening ClayCode BASE semantics. Current G9 already expresses contextual facets, Hyperposition, stable higher-order relation identity, typed roles, graph deltas and ordinary record/class forms sufficient for the new bounded-irreducibility readout candidate.

The material ClayCode finding is instead an implementation-boundary defect candidate in CC-WP-03:

- production `claycode_base_frontend.py` defaults to the accepted V18 grammar;
- the current `claycode_base_typed_ir.py` defaults to V7;
- `compile_sources` reparses source through the grammar selected by TypedIR;
- the accepted WP02 receipt explicitly names the next falsifier as a receipt-bound V18 FrontendArtifact -> TypedIR bridge without silent reparse and with expected-surface/grammar binding fail-closed.

This means the current WP03 entry path can diverge from the exact frontend artifact whose parser/canonical semantics already earned WP02 PASS. No WP03 failure is promoted until execution on the accepted target VPS, but the source-level mismatch is sufficiently direct to define the next blocker test.

## Hyperposition -> ClayCode architecture decision

Do not add a new Hyperposition syntax primitive now.

Represent the research candidate with existing records/classes and preserve these distinctions in TypedIR/runtime:

`Hyperposition state != selected projection`

`n-ary semantic relation != mandatory physical hyperedge`

`semantic topology != active topology != coordination topology != physical topology`

`higher-order relation != hypercomputation`

`bounded reduction loss != truth`

The new readout measures relation/context preservation against explicit comparator classes and budgets rather than asserting absolute irreducibility.

## ClayGraph / UnifiedDB implications

ClayGraph V2 already provides a strong physical counterexample to the claim that n-ary semantics require an exotic storage primitive: it stores a stable logical hyperrelation row plus member/role rows and projection/selection receipts. This is compatible with the Hyperposition result that pairwise physical incidence can preserve n-ary semantic identity when the relation object itself is retained.

UnifiedDB remains the epoch/transaction/provenance-bound semantic state plane. Hyperposition readout payloads and relation identities may be persisted there without turning ClayGraph activation or topology into truth/authority.

## GWT / Emergenz implications

GWT and Hyperposition should share episode/state epochs. GWT measures selection/broadcast/reconstruction/use/outcome/re-entry; Hyperposition measures which contextual/relation topology enabled or altered those outcomes. Emergence claims remain intervention-sensitive and vector-valued; no single synergy, graph-density or recurrence score is sufficient.

## Goodman review

The Frank/Hyperposition demand for higher-order semantics is `REFINED`: preserve relation/context identity, but do not force a new physical topology or language syntax.

Absolute higher-order irreducibility is `REFUTED` by the finite auxiliary-state comparator in the synthetic discriminator.

The claim that the current G9 surface cannot express the candidate readout is `REFUTED` at local compatibility level.

The claim that WP03 may independently reparse source after receipt-bound WP02 acceptance is `REFUTED` by the explicit WP02 next-falsifier contract plus current source mismatch.

## Executable artifact

`WP03_FRONTEND_BINDING_FALSIFIER.py` was committed. It checks:

- frontend default is the accepted V18 grammar;
- TypedIR default matches the production frontend rather than selecting an independent grammar;
- frontend artifact surface remains `BASE_D_V18_REWARD_RELATIONS`;
- record declaration identity survives TypedIR;
- a `class` declaration such as `ReductionComparator` is not silently lost from TypedIR declaration identity.

An attempt to clone fresh current main and run this exact artifact in the local container failed before code execution because DNS could not resolve GitHub. This is recorded as `BLOCKED_TRANSPORT`, not PASS or FAIL.

## Minimal repair direction after target confirmation

1. Make the production TypedIR bridge consume the receipt-bound FrontendArtifact rather than silently reparse source with an independent grammar default.
2. Validate frontend surface, grammar SHA and frontend semantic identity fail-closed before TypedIR admission.
3. Preserve `class/type` declaration identity in TypedIR, or explicitly prove/test a narrower intended representation.
4. Rerun deterministic identity, stale-grammar, surface-mismatch, grammar-hash-mismatch and class-declaration tests on accepted Hostinger Ubuntu.
5. Only after those pass, proceed to WP04 type/effect semantics; do not reopen the language freeze for this issue.

## Disposition

`NO_SEMANTIC_CHANGE` for Hyperposition.

`WP03_BLOCKER_CANDIDATE` for frontend-artifact binding/class identity.

`NO_PROGRESS_PROMOTION` until exact target-VPS execution.

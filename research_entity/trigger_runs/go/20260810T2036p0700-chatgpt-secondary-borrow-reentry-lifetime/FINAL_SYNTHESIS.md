# GO FINAL SYNTHESIS — borrow/re-entry lifetime and receipt-aware currentness

Run: `20260810T2036p0700-chatgpt-secondary-borrow-reentry-lifetime`  
Actor: `chatgpt-secondary / OpenAI / GPT-5.6 Sol`  
Status: `MATERIAL_RESEARCH_DELTA_COMMITTED / NO_PACKAGE_OR_ARCHITECTURE_PROMOTION`

## Global routing result

The live swarm changed during this invocation. The old Andreas-PC BASE14 work was cancelled as stale and replaced by `WORK-CLAYCODE-BASE14-TARGET-VPS-20260810`. Concurrent PRs already own WP03 structural TypedIR, CycleRegionIR, binding, WP04 call contracts/constraints and nested-path implementation, so this run deliberately did not create a parallel production patch.

Current live evidence leaves WP03 open despite a target-VPS typed-state PASS measurement, and WP04 retains a hard negative result: unresolved production call signatures must not be invented from names, caller constraints or apparent behavior.

Q23 VSTG-1 reentry was consumed. Its remaining joined visual-feature/effect/outcome target-VPS question stays open and does not delay BASE.

## Fresh external mechanism evidence

WebAssembly Component Model provides a useful counterexample to either extreme. WIT distinguishes owned and borrowed resource handles statically, but the component runtime still enforces handle uniqueness/drop/lifetime rules; async borrowing uses runtime lend/borrow accounting. Scala 3 capture checking and recent capability-classifier/revocable-capability work show that significant capability/effect/lifetime information can also be carried statically.

Fusion: the current ClayCode direction remains strongest as a hybrid boundary: nominal/typed semantic and capability descriptors in WP03, static effect/capture constraints in WP04 where expressible, and residual runtime checks for dynamic bearer possession, current resource/lease epoch, revocation and restart/re-entry facts.

No new ClayCode surface syntax is justified by this evidence.

## Exactly one out-of-box experiment

`BORROW_REENTRY_LIFETIME_ABLATION_V1` was the sole unusual experiment of this GO macrocycle.

240,000 deterministic synthetic lifecycle cases, seed `20260810`, were distributed equally across valid, stale resource epoch, stale lease epoch, revoked, serialized reconstruction, returned task, wrong context, dropped, verified resource rebound and verified lease renewal classes.

Observed inside the defined mechanism model:

- `SCOPE_ONLY`: 96,000 false accepts, false-accept rate 57.14% over invalid cases, zero false denies. False accepts were exactly stale-resource, stale-lease, revoked and serialized-reconstruction classes.
- `RIGID_DYNAMIC_EPOCH`: zero false accepts but 48,000 false denies, rejecting both positively revalidated rebound/renewal classes; false-deny rate 66.67% over valid cases.
- `RECEIPT_AWARE_DYNAMIC`: zero false accepts and zero false denies in this synthetic model.

This is not an empirical security rate and not target-VPS acceptance. The ground-truth model explicitly contains revalidation semantics, so the result is a mechanism sanity check: it exposes the opposite blind spots of lexical-only and rigid raw-epoch policies.

## New test obligation

Candidate only: when resource or lease identity legitimately changes, continuity should be accepted only through independently verified revalidation/renewal evidence bound to the intended semantic contract/resource identity and old/new currentness identities. Serialized/descriptive equality must never reconstruct bearer authority.

Strongest counterhypothesis: unconditional rejection on any epoch/lease mismatch is simpler and may dominate once the real false-denial cost and revalidation attack surface are measured.

Next falsifier: run exact target-VPS lifecycle fixtures for valid/stale/revoked/reconstructed/rebound/renewed capability states against the current WP04/runtime lane; measure false accept, false denial, restart/replay equivalence and resource cost. If receipt-aware revalidation does not beat rigid mismatch rejection end-to-end, reject this refinement.

## Disposition

- `WP03`: no promotion.
- `WP04`: no promotion; add lifecycle/revalidation differential only.
- `BASE_CLAYCODE_RELEASE`: no promotion.
- `Q23`: VSTG indexed/reused; open joined visual/effect/outcome receipt remains later work.
- `Frank/self.root Harness`: not mutated.
- Paid/final training: not authorized, not attempted.

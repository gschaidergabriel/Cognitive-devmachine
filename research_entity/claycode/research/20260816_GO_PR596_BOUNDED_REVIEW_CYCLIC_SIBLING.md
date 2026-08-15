# GO 2026-08-16 — PR #596 bounded review + cyclic-sibling quarantine

## Active framing

- Active program: `CLAYVERSE_CLAY_MACHINE_ONLY`.
- This is Clay Machine / ClayCode compiler-runtime work.
- Legacy FRANK/self.root names in inherited paths are compatibility evidence only, not the active project goal.
- Trigger: exact `go`.
- Worker: temporary Clay research/build worker, GPT-5.6 Sol.
- Research parent before write: `ce6e66e9e1fddff471a012882350ddd3f9f9e7cf`.
- Product repo: `gschaidergabriel/Dr.-Unterweger`.
- Product main observed unchanged: `7fbcb5f64798d919859dc0b664ab5f29559f9d5a`.
- Reviewed candidate: PR #596, exact head `c75d5a1dd787be60d6785fbadc0de68606a3ba85`.

## R0 — observed reality

PR #596 is open and review-gated. The current candidate replaces recursive TypeRef canonicalization/equality/diagnostic rendering with explicit work stacks while preserving the inherited WP04 rule that a parameterized nominal head is not itself alias-resolved; only its parameters are canonicalized. Existing exact-head evidence reports 8/8 fixed depth-4096 TypeRef checks and a broader current-main regression envelope.

No submitted PR review existed before this cycle.

## R1 — retained hypothesis

The candidate removes Python call-stack dependence from the productive TypeRef operations without widening ClayCode generic/host/member semantics and without altering alias-cycle fail-closed behavior.

## R3 — strongest counter-reality

A cycle confined to one structural child could contaminate alias provenance or result-stack assembly and incorrectly poison a healthy sibling, even if simple sibling sharing and single-child structural cycles already pass.

## Exactly one bounded unusual experiment

Experiment: `CYCLIC_SIBLING_QUARANTINE`.

Construction:

- `A -> Pair<B, C>`
- `B -> A` (cycle confined to the left child)
- `C -> Int` (healthy right child)

Prediction if the candidate mechanism is correct:

- canonical result is `Pair<<TYPE_ERROR>, Int>`;
- exactly one `TYPE_ALIAS_CYCLE` is emitted;
- the healthy right sibling remains `Int`.

Prediction if the counter-reality is correct:

- the right sibling is poisoned, omitted, or misassembled; or
- multiple/spurious cycle diagnostics appear.

Observed in a bounded executable reconstruction of the exact `_canonical` algorithm from PR #596 head:

- result: `Pair<<TYPE_ERROR>, Int>`;
- diagnostics: exactly one `TYPE_ALIAS_CYCLE` reaching `A`;
- measured elapsed time: about `0.013 ms` on the local sandbox run;
- outcome: PASS / counter-reality not observed.

No second unusual experiment was executed in this macro-cycle.

## Review result

No blocking semantic defect was found in the reviewed TypeRef integration.

Retained boundaries:

- no generic TypeRef semantics selected;
- no host/member defaulting;
- no effect/execution authority minted;
- no Clay Machine completion claim;
- same account/model/project ancestry is not independent semantic replication.

Residual caveat: this review does not prove that every other TypeRef consumer elsewhere in the repository avoids recursive dataclass equality/stringification. It only supports the reviewed productive checker path and bounded regression envelope.

A COMMENT review was submitted on PR #596 at exact head `c75d5a1dd787be60d6785fbadc0de68606a3ba85`; GitHub review id `4944760579`. It intentionally does not claim independent-person approval.

## Primary external boundary

Official Python documentation states that the recursion limit exists to prevent interpreter/C-stack overflow and that setting it too high can crash the process. Official dataclasses documentation states that generated equality compares fields structurally. These facts support removing host recursion from finite ClayCode TypeRef processing instead of treating a raised recursion limit as the semantic fix.

## Collapse

Outcome: `RETAIN / SUPPORTED_REVIEW_CANDIDATE`.

Not promoted:

- PR #596 is not canonical main merely because this review found no blocker;
- ClayCode compiler/runtime is not complete;
- Clay Machine VM / ClayOS is not complete.

## Next discriminator

1. Normal canonical merge decision for PR #596 under project policy.
2. If merged, bind post-merge canonical-main bytes/receipts before promotion.
3. Then resume the current high-information Clay Machine frontier: classify the 429 unresolved Call names / 464 occurrences and 22 MethodChain/member segments from canonical corpus authority without host/default inference or exclusion-based manufactured coverage.

Rollback: this research delta is documentary only; product bytes were not changed by this cycle.
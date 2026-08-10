# FRANK RUN — H-WP-10 destructive-effect contract closure candidate

Run: `frank-20260810T2031p0700-chatgpt-secondary-hwp10-destructive-guards`  
Trigger: `frank`  
Actor: `chatgpt-secondary / OpenAI / GPT-5.6 Sol`  
Persistent entity: `Clay`  
Research subject: `self.root`, human surface `Frank`  
Status: `MATERIAL_HARNESS_DELTA_CANDIDATE / NO_RELEASE_PROMOTION`

## Fresh-state finding

The run first selected the CC-WP-03 FrontendArtifact -> TypedIR no-reparse gap, but a fresh-main reread showed that concurrent workers had already implemented a stronger receipt-bound bridge plus residual-semantics preservation. The planned duplicate write was aborted under the project `stale plan -> STOP/REPLAN` rule.

The next non-overlapping executable discriminator was in H1 effect authority. The owner-fixed directive requires:

- `DESTRUCTIVE.DELETE_ACCOUNT -> REQUIRE_CONFIRMATION + explicit_target + irreversibility_warning`
- `DESTRUCTIVE.MASS_DELETE -> REQUIRE_CONFIRMATION + exact_scope + count_preview + rollback_state`

The current reference implementation instead required only `explicit_target` for DELETE_ACCOUNT and allowed `MASS_DELETE` when `exact_scope + count_preview + (rollback_available or no_backup_disclosed)` held. That is an executable contract mismatch, not merely missing documentation.

## Candidate delta

Branch: `frank/hwp10-destructive-guards-20260810`  
Draft PR: `#182`  
Patch head at PR creation lineage: `8d0056e32ee45e8faa150ceca44f93621e647b2c`

Changes:

1. Add policy-relevant `irreversibility_warning` and `rollback_state_known` request state. These fields are automatically included in the existing deterministic request hash.
2. DELETE_ACCOUNT now fails closed unless both explicit target and irreversibility warning are present.
3. MASS_DELETE now fails closed unless exact scope, count preview and resolved rollback state are present.
4. Add two regression tests. Existing ordinary read/reversible write/external communication direct-execution tests are unchanged.

No model, translator, GWT, ClayGraph, peer or visual signal receives effect authority from this patch.

## Executed evidence

Evidence class: `LOCAL_DETERMINISTIC_FIXTURE`, not target-VPS acceptance.

Reconstructed current reference component plus the existing 17-test suite and the two new contract tests were executed locally:

`19/19 PASS`

The first PR-triggered `Research Entity Identity Guard` run failed before any workflow step materialized. GitHub returned an empty step list and no retrievable job log. This is therefore retained as `CI_CONTROL_PLANE_FAILURE_OR_UNKNOWN`, not as a code/test failure. A separate PR workflow was still queued at the observation point. No Hostinger/target-VPS PASS is claimed.

## Hypothesis / counterhypothesis

Hypothesis: explicitly representing the two owner-required guard facts closes the H1 contract mismatch without increasing ordinary-operation friction or widening effect authority.

Strongest counterhypothesis: the new booleans are still too lossy; production H1 may require typed `IrreversibilityState` and `RollbackState` identities rather than boolean summaries, especially for restart/replay and confirmation-hash stability. If typed state is required, this patch is a useful fail-closed interim discriminator but not the final representation.

## Architecture fidelity

`UNKNOWN` for promotion. Local contract fidelity improves for the two tested destructive subtypes, but H-WP-10 remains OPEN and no target-VPS or H2 differential evidence exists.

## Required next falsifier

Run the exact PR bytes on the accepted Hostinger Ubuntu lane and extend the test to durable confirmation/nonce consumption, crash/restart, duplicate handling and reservation -> permit -> commit -> verified outcome -> provenance-bound re-entry. Then repeat the two destructive guards through the H2 ClayCode equivalent. Any boolean-state ambiguity that changes admissibility after replay must reopen the representation to typed state rather than weakening the fixed directive.

## Branch impacts

- H-WP-10 EFFECT-AUTHORITY: direct executable candidate.
- H-WP-13 RECOVERY: durable one-shot confirmation/replay remains a blocker.
- H-WP-14 FUZZ-ADVERSARIAL: add destructive-guard mutation and missing-state fuzz cases.
- H2 Clay Harness: require semantic/differential equivalence for the two guard facts.
- ClayCode CC-WP-04 TYPE-EFFECT: keep effect-authority facts typed/non-mintable; do not treat content freedom, model confidence or salience as authority.

No H1/BASE release promotion. No training authorization. No self.root Harness self-mutation authority.

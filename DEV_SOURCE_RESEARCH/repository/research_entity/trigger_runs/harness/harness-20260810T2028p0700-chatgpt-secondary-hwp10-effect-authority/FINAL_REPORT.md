# Harness H-WP-10 — Effect Authority Adversarial Replication

Run: `harness-20260810T2028p0700-chatgpt-secondary-hwp10-effect-authority`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Evidence: local deterministic component execution + adversarial sibling-candidate replication  
Release authority: none; H1 remains NOT_PASS

## Result

The run began as an independent implementation lane for H-WP-10 after the visible workspace showed H-WP-10 OPEN and only H-WP-02 actively claimed. During durable write-back, a concurrent sibling implementation appeared. The run therefore stopped blind overwrite, refreshed live repository state and converted itself into an adversarial replication lane.

A sibling candidate at `research_entity/harness/reference_effect_authority.py` had a recorded 12/12 local acceptance PASS. Five additional authority-invariant tests were applied against that exact candidate semantics. Result: **0/5 pass, 5/5 fail**.

Material counterexamples:

1. `SELF_PROPOSAL_ONLY` can obtain `ALLOW` for `PRIVILEGED_CHANGE` by setting `preauthorized_exact_change=true`.
2. An `AUTHENTICATED_USER`-labelled request with `authenticated=false` can obtain the same privileged direct allow.
3. `SELF_PROPOSAL_ONLY` can construct a matching confirmation receipt that authorizes a credential/security effect.
4. `SELF_PROPOSAL_ONLY` can construct a matching confirmation receipt that authorizes a financial/legal commitment.
5. Confirmation request identity does not bind policy-relevant guard state; distinct destructive guard states can share one request hash.

These violate the owner-fixed effect-authority boundary. The current sibling candidate must not be promoted from its 12/12 local acceptance receipt.

## Concurrent implementation comparison

A second concurrently-created candidate exists at `research_entity/harness/reference/effect_authority.py`. Its implementation binds policy-relevant request fields into confirmation identity and explicitly requires authenticated-user authority on privileged preauthorization/confirmation application, so it is safer on the five discovered counterexamples. It is not promoted here: DELETE_ACCOUNT irreversibility-warning semantics, MASS_DELETE rollback semantics, and restart-persistent one-shot confirmation consumption still require contract review/integration evidence.

## Architecture decision

`H-WP-10 = NOT_PASS / REPAIR_REQUIRED`

Do not choose between the duplicate implementations by chronology or worker authority. Canonicalize by executable contract coverage:

- all owner-fixed acceptance cases;
- EA-CEX-01..05 adversarial regressions;
- exact policy-relevant request identity;
- independently validated authority source;
- persistent confirmation consumption/idempotency through H-WP-02;
- crash/restart and duplicate-effect tests;
- full H1 effect commit/outcome/re-entry trace;
- target-VPS execution;
- H2 ClayCode differential equivalence later.

## Cross-branch impact

Harness release audit must retain H1 `NOT_PASS`. Frank must preserve proposal/authority separation. ClayCode must encode typed authority source and one-shot request-bound confirmation without an escape hatch. UnifiedDB/state ledger must preserve consumption state across restart. ClayGraph must represent proposal/salience paths as non-authoritative and expose forbidden authority edges as validation failures.

## H-WP-17 compatibility

The concurrently completed H-WP-17 target-contract gate already reports the 2026-08-09 H1 freeze stale and explicitly keeps H1/H2 `NOT_PASS`; therefore this counterexample does not contradict that H-WP-17 component result. It deepens the same no-promotion conclusion with an executable authority defect.

## Durable artifacts

- `CLAIM.json`
- `INTERCONNECT_MANIFEST.json`
- `ADVERSARIAL_COUNTEREXAMPLE_REPORT.json`
- `AFFECTED_BRANCH_FEEDBACK.json`
- `RUN_CLAYGRAPH.json`
- this report

## Next falsifier

Canonicalize one H1 effect-authority candidate, add EA-CEX-01..05 as permanent regression tests, bind nonce consumption to canonical state/replay, run the full acceptance/adversarial/restart suite, then execute the exact component/full-turn path on the accepted target VPS. A PASS is not allowed before those receipts exist.

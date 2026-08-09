# GO Actions scheduler skip discriminator — 2026-08-10 06:44 +07

Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Entity role: temporary Clay Research Entity worker; NOT Frank  
Trigger: exact `go`  
Mission: `Frank v0.1 voll lauffähig auf Andreas PC`  
Fresh main before experiment: `a42097ed41e69b5968d451d3b6e560cf5adf6557`  
Fresh main before durable write: `1f98115ca8101f5255b42f745e202887f101e11f`

## Why this experiment

Current shared evidence had two superficially similar Clay Actions failures: GitHub-hosted jobs completed failure with zero visible steps, while a Clay `runs-on: self-hosted` probe stayed queued even though the Hostinger machine demonstrably executes self-hosted jobs in `gschaidergabriel/Dr.-Unterweger`.

Fresh official GitHub documentation materially narrows interpretation:
- repository-level self-hosted runners are dedicated to one repository;
- organization-level runners can serve multiple organization repositories subject to access policy;
- self-hosted runner execution itself is free of GitHub Actions hosted-runner minute charges;
- repository Actions policy can disable or restrict workflow execution.

This makes a runner-free scheduler discriminator useful before more ClayCode or VPS changes.

## Hypothesis / strongest counterhypothesis

Hypothesis: Clay repository Actions is blocked before workflow/job admission, so even server-side job-condition evaluation cannot complete normally.

Strongest counterhypothesis: workflow admission and scheduler-side condition evaluation work, while the observed failures occur later at runner eligibility/allocation or a specific hosted-execution control-plane boundary.

## Exactly one GO out-of-the-box experiment

Created temporary branch `go/oob-controlplane-skip-20260810-0645` from `a42097ed41e69b5968d451d3b6e560cf5adf6557`.

Added only `.github/workflows/go_oob_controlplane_skip_probe.yml` with:
- trigger: `pull_request` to `main`;
- `permissions: contents: read`;
- one job `scheduler-skip-probe`;
- `if: ${{ false }}`;
- nominal `runs-on: ubuntu-latest`;
- one `MUST_NOT_EXECUTE` shell step.

Opened draft PR #61 at head `1ab932384a1ebd3fbd0251374a917ab79cbd12a7` and did not merge it.

Observed workflow receipt:
- run id: `31342601126`;
- workflow: `GO OOB control-plane skip probe`;
- status: `completed`;
- conclusion: `skipped`;
- no runner step was required or executed by construction.

Simultaneously, the ordinary `Research Entity Identity Guard` for the same PR head instantiated separately as run `31342601098` and was still queued at the observation checkpoint.

PR #61 was then closed without merge. The experimental workflow therefore did not enter canonical `main`.

## Result

The leading hypothesis is REFUTED for this bounded path.

Supported classification:

`CLAY_ACTIONS_WORKFLOW_ADMISSION_AND_SERVER_SIDE_JOB_CONDITION_EVALUATION_CONFIRMED`

The repository can admit the PR workflow and resolve an intentionally false job condition to a terminal `skipped` conclusion. Therefore the previously observed zero-step hosted failures are not sufficient evidence that Clay Actions is globally disabled before job-condition evaluation.

The remaining blocker is downstream of that admitted control-plane stage. For the Hostinger lane, fresh GitHub documentation plus paired repository evidence makes repository scope/eligibility the leading explanation: if the working Hostinger runner is repository-level registered to `Dr.-Unterweger`, it is not eligible for Clay jobs until Clay gets its own repository registration/service or an applicable shared organization/enterprise runner arrangement.

This is stronger than the old generic `Actions may be disabled` hypothesis, but exact runner registration scope remains UNKNOWN because the current connector cannot list repository self-hosted runners/settings.

For GitHub-hosted Clay jobs, billing/account hosted-runner eligibility or another hosted allocation control remains unresolved; self-hosted billing does not explain the Clay self-hosted queue because self-hosted runner execution is not metered as hosted minutes.

## ClayCode / architecture consequence

Architecture delta: `NO_CHANGE`.

No ClayCode semantic change is justified by this result. WP02 remains blocked on exact admitted Ubuntu receipt, not on demonstrated parser failure. Preserve the current decoded-string fix and direct lookahead/metamorphic regressions as candidates until target-class receipt exists.

## Next falsifier / blocker removal

1. In `gschaidergabriel/clay-global-research-entity` inspect `Settings -> Actions -> Runners` and verify whether any Hostinger runner is registered/online for this repository.
2. If none is visible and the existing machine is repository-level bound to `Dr.-Unterweger`, register a separate Clay repository runner service on the same Hostinger VPS (or use a genuinely shared organization/enterprise runner only if the repository topology supports that).
3. Confirm the Clay self-hosted heartbeat executes at least one real step.
4. Immediately run the exact-SHA WP02 strict/full-corpus/canonical/direct-lookahead workflow with isolated dependencies and bounded deadlines.
5. Persist `research_entity/claycode/remote_vps/LATEST_WP02_STRICT.json`; only then adjudicate WP02 promotion and continue sequentially into WP03.

## Evidence provenance

Internal:
- PR #61 / head `1ab932384a1ebd3fbd0251374a917ab79cbd12a7`
- workflow run `31342601126` -> `completed/skipped`
- concurrent identity-guard run `31342601098`
- `research_entity/reports/20260810T0640p0700_CHATGPT_GO_POSTGUARD_ACTIONS_FUSION.md`
- `research_entity/state/work/events/20260810T0642p0700_chatgpt_secondary_wp02_string_identity_fix_revise.json`

Fresh primary external sources:
- GitHub Docs: Self-hosted runners — repository-level runners are dedicated to a single repository; organization-level runners may serve multiple repositories.
- GitHub Docs: Adding self-hosted runners — repository, organization, enterprise registration scopes.
- GitHub Docs: Billing and usage — self-hosted Actions execution is free from GitHub-hosted runner usage charges.
- GitHub Docs: Managing GitHub Actions settings for a repository — repository Actions enablement/restriction controls.
- Lark current documentation retained from the same macro-cycle: strict mode checks collisions, but advanced regex lookaround can limit `interegular` collision-detection completeness, so direct V17 boundary fixtures remain mandatory.

`QUEUED != EXECUTED != PASS`; `SKIPPED` here is a successful scheduler discriminator, not a ClayCode acceptance receipt.
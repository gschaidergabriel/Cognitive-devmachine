# GO post-guard Actions admission fusion — 2026-08-10 06:40 +07

Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Entity role: temporary Clay Research Entity worker; NOT Frank  
Trigger: exact `go`  
Mission: `Frank v0.1 voll lauffähig auf Andreas PC`  
Canonical parent: RAE-8.8 / revision 2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Fresh main before write: `92b46f6c7581c5b21c82103634faff64d48fe903`

## Result

This delta does not change ClayCode, Frank Harness, GWT, Needle, effect authority, or release accounting. It narrows the current GitHub Actions transport blocker after the identity-guard version-drift repair.

A self-contained PR-only GitHub-hosted workflow was created on temporary draft PR #60 at head `95ffd19a84b9b7ee9ea7b36b7f2a76270a40d0ad`. The diagnostic requested `ubuntu-latest`, used `permissions: contents: read`, performed no checkout, imported no Clay repository code, used no repository write path, and contained one shell step whose first action was an execution marker.

Observed GitHub receipts:
- diagnostic workflow run `31342246166`;
- diagnostic job `93317830657`;
- job completed `failure`;
- job step list was empty;
- no decoded job log blob existed (`404 BlobNotFound`);
- the normal Research Entity Identity Guard on the same PR head instantiated run `31342246079`, job `93317830389`, and likewise completed failure without visible steps.

PR #60 was closed without merge. The diagnostic workflow did not enter canonical `main`.

## Hypothesis / counterhypothesis

Hypothesis: the earlier Clay hosted pre-step failures were caused by the stale identity-guard implementation.

Strongest counterhypothesis: a repository/account GitHub Actions admission or other pre-run control-plane condition prevents hosted jobs from reaching step execution independently of ClayCode and the identity guard.

Result: the hypothesis is refuted for this self-contained path. The independent workflow contains no identity-guard dependency yet reproduces zero-step failure after the identity-guard repair.

Supported bounded classification:

`CLAY_REPOSITORY_HOSTED_ACTIONS_PRESTEP_FAILURE_REPRODUCED_AFTER_IDENTITY_GUARD_REPAIR`

The exact root cause remains UNKNOWN. Plausible unresolved classes include repository/account Actions enablement/policy, billing or budget state for GitHub-hosted private-repository execution, scheduling/allocation, or another GitHub pre-run control-plane condition. No specific class is promoted without authoritative settings evidence.

## Relation to the Hostinger lane

This hosted result does not prove Hostinger machine failure. Existing persisted project evidence independently proves real self-hosted Ubuntu/model execution in `gschaidergabriel/Dr.-Unterweger`.

Fresh Clay evidence still shows:
- `research_entity/state/system/actions_heartbeat/LATEST.json` absent;
- `research_entity/claycode/remote_vps/LATEST_WP02_STRICT.json` absent;
- a self-hosted `runs-on: self-hosted`-only probe remained queued in its bounded window;
- therefore Clay repository runner registration/status/eligibility and Actions admission require direct reconciliation before receipt-backed BASE promotion.

## ClayCode fusion

During the same shared-state window, the WP02 decoded-string fix on main closed its previously falsified local partition mismatch in 6/6 local diagnostic cases. That remains local, non-strict evidence because `interegular` was unavailable in the local diagnostic and no Hostinger/Andreas Ubuntu receipt exists.

Fresh WP03 local evidence also shows raw JSON STRING escape spelling currently leaks into `semantic_ir_sha256` for 4/4 escape-equivalent pairs. This is retained as a sequential WP03 test obligation only; it must not bypass the WP02 production gate.

## External knowledge consequence

Current official GitHub documentation distinguishes repository Actions policy/billing controls from workflow-step behavior and self-hosted runner routing. Current official GitHub Status was operational during the bounded observations, weakening a broad provider-wide outage hypothesis without proving the repository-local cause.

Current Lark documentation also supports keeping direct V17 boundary fixtures alongside strict/interegular checks because advanced regex lookaround can limit collision-detection completeness.

## Decision and next frontier

Architecture delta: `NO_CHANGE`.

Highest-value blocker removal is now direct authoritative inspection of:
1. GitHub personal Billing & licensing -> Actions usage/budgets/payment state;
2. `clay-global-research-entity` -> Settings -> Actions -> General;
3. `clay-global-research-entity` -> Settings -> Actions -> Runners, including intended Hostinger runner id/name/status/busy/labels/scope/version.

The current connector exposes workflow runs/jobs/logs and repository writes but does not expose the repository self-hosted runner listing/settings surface, so this worker cannot truthfully complete that reconciliation from the available capability set.

When admission/runner eligibility changes, the next discriminator is the first exact-SHA step-executed Clay hosted/self-hosted run, followed by the existing read-only WP02 strict/full-corpus/canonical/direct-lookahead Ubuntu workflow. Only receipt-backed results may change WP02/BASE status.

`QUEUED != EXECUTED != PASS`; `404 missing receipt != code failure`; `zero-step failure != ClayCode failure`.

# GO minimal-label runner eligibility fusion — 2026-08-10 06:32 +07

Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Entity role: temporary Clay Research Entity worker; NOT Frank.  
Canonical parent: `RAE-8.8 / r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Fresh main observed before durable write: `42d6855d0cfa2abb5d49d39c7b482f1d0d72ffc5`  
Trigger: exact `go`  
Mission: `Frank v0.1 voll lauffähig auf Andreas PC` under Ubuntu developer-system semantics.

## Executive result

This cycle does not change ClayCode semantics and does not promote CC-WP-02 or BASE. It strengthens the execution-transport diagnosis without colliding with the concurrently claimed WP02 canonicalizer lane.

The Hostinger machine is already verified to execute real self-hosted Ubuntu work in `gschaidergabriel/Dr.-Unterweger`, including an 18/18 integrity pass and 13/13 pytest pass after repair. However, Clay repository self-hosted jobs remain unallocated.

Exactly one bounded out-of-the-box experiment in this GO cycle removed the earlier additional runner labels and required only `runs-on: self-hosted`. The job still remained queued. Therefore the previous `Linux`/`X64` additional labels are not the primary blocker in the observed window.

Supported operational conclusion:

`NO_ONLINE_OR_REPOSITORY_ELIGIBLE_SELF_HOSTED_RUNNER_OBSERVED_FOR_CLAY_IN_WINDOW`

This is not evidence that the Hostinger VPS itself is broken and is not evidence of a ClayCode parser/compiler failure.

## Fresh internal evidence

- Current BASE stage remains `BASE_CLAYCODE_RELEASE`; workspace accounting still grants PASS only to CC-WP-01 and requires receipt-backed closure for later packages.
- Concurrent current worker claim `WORK-CLAYCODE-WP02-CANON-20260810` owns the isolated CC-WP-02 canonicalizer lane; this worker did not overlap that write scope.
- Existing runner capability evidence proves real self-hosted execution in `gschaidergabriel/Dr.-Unterweger` but not automatic runner eligibility in the Clay repository.
- Existing recommendation `CAPREC-CLAY-HOSTINGER-RUNNER-SCOPE-20260810` already proposes verifying/adding a Clay-visible runner registration.
- Main advanced during this cycle with `fix(ci): make identity guard version-drift safe`; stale writes were avoided by re-reading main before durable output.

## Fresh external evidence

Official GitHub Actions documentation observed during this cycle states:

- self-hosted routing requires an online/idle runner matching the job's required labels;
- when no matching online/idle runner is available, the job remains queued;
- default self-hosted labels include `self-hosted` plus OS/architecture labels;
- runner labels are case-insensitive.

Sources retrieved live on 2026-08-10:
- GitHub Docs: `Self-hosted runners reference`
- GitHub Docs: `Using self-hosted runners in a workflow`
- GitHub Docs: `Using labels with self-hosted runners`
- GitHub Docs: REST API endpoints for self-hosted runners

## Hypothesis / strongest counterhypothesis

H1: the immediate Clay execution blocker is repository eligibility/visibility or current runner online state, not additional label spelling and not a need for ClayCode semantic redesign.

Strongest counterhypothesis: a correctly Clay-eligible runner was temporarily busy/offline during the bounded observation; a later allocation could succeed without registration change.

Smallest discriminator performed here: require only `self-hosted`. Result: still queued.

Remaining decisive discriminator: authoritative Clay repository runner listing/status or first actual Clay self-hosted step execution.

## Exactly one bounded out-of-the-box experiment

Experiment ID: `GO-OOB-SELFHOSTED-MINLABEL-V1`

Implementation:
- temporary branch `chatgpt-secondary/go-selfhosted-minlabel-20260810-0635`;
- draft PR #56;
- one PR-only job;
- `runs-on: self-hosted` only;
- `permissions: contents: read`;
- no checkout, no secrets, no ClayCode/Frank code execution, no repository write from runner.

Observed:
- workflow run `31342068951` created;
- job `93317377631` created;
- job state remained `queued` during bounded observation;
- zero steps/logs were available because the job was not allocated;
- PR #56 closed without merge.

Disposition: `SUPPORTED_BOUNDED_NEGATIVE`.

Falsified candidate explanation: `ADDITIONAL_LINUX_X64_LABEL_MISMATCH_IS_PRIMARY_BLOCKER`.

Still open:
- Clay repository has no registered eligible runner;
- runner exists but is offline/busy;
- repository/organization runner access policy excludes Clay;
- transient scheduling condition.

## Architecture / test / recovery consequence

Architecture delta: `NO_CHANGE` to ClayCode semantics, V17 parser candidate, GWT, Frank Harness, Needle or authority model.

Operational/test delta:
- treat runner repository scope/eligibility as a first-class capability property;
- do not equate a runner proven in `Dr.-Unterweger` with a runner eligible for `clay-global-research-entity`;
- classify queued/no-step states as transport availability evidence, separate from code/test failure;
- keep BASE and WP02 fail-closed until actual Ubuntu receipts exist;
- preserve the existing Clay-visible Hostinger runner registration recommendation as the highest-value blocker removal.

## Re-entry / targeted distribution

Affected branches/workers: `claycode`, `harness`, `security`, `recovery`, `capability`.

Priority order after this result:
1. verify Clay repository runner registration/status/access; if absent and authorized, add a distinct Clay repository runner service on Hostinger or an appropriately scoped organization runner;
2. let the already-active WP02 canonicalizer worker continue without collision;
3. once a Clay runner executes, produce the exact WP02 strict/full-corpus/canonical receipt before any WP02 promotion;
4. repair only receipt-backed code failures;
5. continue BASE14 Ubuntu application closure; final Frank v0.1 acceptance remains Andreas' actual Ubuntu target.

No paid/final model training was authorized or attempted. `QUEUED != EXECUTED != PASS`.

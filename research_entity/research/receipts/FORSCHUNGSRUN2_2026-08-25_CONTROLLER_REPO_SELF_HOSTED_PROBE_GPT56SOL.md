# Forschungsrun 2 — controller-repository self-hosted liveness discriminator

## Authority and scope

- Persistent research entity: Clay; this ChatGPT session is an organ.
- Product: EntityOS; integrated cognition/compute architecture: HCU.
- Newest admitted authority observed: supervisor `8.78`, `FREE_ONLY`, with active owner authority explicitly permitting full research/development execution and bridge/runner repair inside `clay-direct-dev`.
- Canonical research `main` observed immediately before this write: `23308181f631fbf1c7a19b4584a9c825cc90196e`.
- This receipt concerns transport diagnosis only. It performs no model intervention, no provider call, no paid path, and does not alter the frozen structural J-Space discriminator.

## Prior bounded state

Current Run-2 evidence already established:

- structural native run `32810213066` in `gschaidergabriel/clay-global-research-entity` remains queued;
- recovery run `32811360359` remains queued;
- repository-visible active Actions occupancy does not explain the backlog;
- separate live telemetry observes the VPS host and `clay-direct-dev` sandbox alive while the research-repository self-hosted jobs remain unassigned;
- the retained access map names `gschaidergabriel/Dr.-Unterweger` as the controller repository retaining the historical/current self-hosted runner path.

A serious remaining counterhypothesis was:

`H_SCOPE_ONLY = the retained runner is healthy, but the research-repository jobs cannot be assigned because the runner is repository-scoped to Dr.-Unterweger.`

GitHub's official self-hosted-runner documentation states that repository-level runners are dedicated to a single repository, while organization-level runners can serve multiple repositories subject to access policy. Therefore this counterhypothesis is structurally plausible and required a same-controller-repository discriminator.

## Discriminator executed

The existing semantics-free controller health probe was reused rather than creating another model experiment:

- controller repo: `gschaidergabriel/Dr.-Unterweger`
- existing workflow: `.github/workflows/frank-self-hosted-probe.yml`
- workflow purpose: probe the registered self-hosted execution surface and attempt a `clay-direct-dev` roundtrip; no provider/model intervention
- source semantics were preserved; only a trailing comment was added to trigger the existing `push` path
- trigger commit: `7048a0aeacfcf3a6e7d941b591902fdc9329fd21`
- resulting workflow run: `32815473976`
- workflow name: `Clay Self-Hosted VPS/Sandbox Probe`
- workflow head SHA: `7048a0aeacfcf3a6e7d941b591902fdc9329fd21`
- observed run state: `queued`
- observed job: `97702719398`, name `probe`, state `queued`
- observed executed steps: none

## Result and inference

This same-controller-repository probe materially falsifies `H_SCOPE_ONLY` as a complete explanation.

Even if the research repository cannot use a repository-scoped runner belonging to `Dr.-Unterweger`, a correctly scoped job inside `Dr.-Unterweger` itself should still begin when that retained runner is online, eligible and listening. The new controller probe is also queued before any step executes.

The strongest bounded classification is therefore:

`CONTROLLER_REPO_SELF_HOSTED_JOB_ALSO_UNASSIGNED_WHILE_HOST_AND_SANDBOX_ARE_LIVE`

This localizes the blocker much more tightly to the GitHub Actions runner transport/listener path. Remaining hypotheses include:

1. self-hosted runner listener/service is stopped or disconnected;
2. registration is stale/missing;
3. labels/group eligibility no longer match the job;
4. the controller wrapper/service that starts or keeps the listener alive has failed;
5. a GitHub-side runner access/configuration state is preventing assignment.

`RUNNER_SERVICE_DOWN` is still not promoted to direct fact because the connected GitHub tool surface does not expose the repository runner status endpoint and this ChatGPT runtime has neither an installed SSH client nor the owner's prepared SSH configuration. Those are tool/transport limitations, not evidence that the configured bridge does not exist.

## Scientific consequence

No J-Space scientific credit changes from this transport diagnosis.

- native pinned llama.cpp cvec matched-control component runtime credit: unchanged `1`
- structural label-free native runtime credit: `0`
- J-Space model runtime credit: `0`
- full HCU runtime credit: `0`
- whole EntityOS runtime credit: `0`
- training credit: `0`
- canonical semantic J-Space promotion: `false`

The frozen structural run remains useful bounded evidence if it eventually executes, but Run 2's static audits independently show that it is not promotion-grade for abstract semantic J-Space: gain-freeze drift, missing geometric coherence/null gate, pooled rather than per-target positivity, insufficient sign-flip reversal criterion, missing off-target regression, single-task-grammar scope, small factorial replication, and the newly identified target/code/query-polarity confound all remain.

## Next exact gate

Do **not** spawn another model experiment and do **not** keep adding self-hosted jobs to the queue.

The next highest-information action is host-side runner repair/attestation through an execution surface that has the established bridge credentials/configuration:

1. observe the runner listener/service process and registration target directly;
2. restart/repair the listener if absent or disconnected;
3. attest effective labels/registration scope without recording secrets;
4. require the existing controller probe `32815473976` or an already-queued retained job to receive a nonzero runner assignment and begin steps;
5. then allow exactly the existing frozen structural discriminator `32810213066` to run unchanged;
6. preserve PASS/FAIL at bounded component scope and keep canonical semantic promotion blocked until the stricter Run-2 successor gate is implemented.

## Researchrun-2 result

`PASS_CROSS_REPOSITORY_TRANSPORT_LOCALIZATION_ONLY`

Run 2 now distinguishes repository-scope mismatch from broader listener/liveness failure: repository scope can explain why a runner registered only to `Dr.-Unterweger` would not take jobs from the research repo, but it cannot explain why a fresh `Dr.-Unterweger` self-hosted probe is also queued. The blocker is therefore localized beyond simple cross-repository scoping and before model execution.
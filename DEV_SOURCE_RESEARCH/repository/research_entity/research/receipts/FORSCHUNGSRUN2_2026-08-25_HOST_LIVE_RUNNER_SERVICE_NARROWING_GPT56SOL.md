# Forschungsrun 2 — host-live / runner-service narrowing

## Scope and authority

- Persistent research entity: Clay; this ChatGPT session is an organ.
- Product: EntityOS; integrated cognition/compute architecture: HCU.
- Newest admitted supervisor observed for this run: `8.78`, mode `FREE_ONLY`.
- Canonical `main` observed immediately before this additive evidence write: `188a22fe505919149a98cf1e29adc87a20ada7de`.
- This is execution-transport diagnosis only. It launches no model intervention, no provider call, no paid path, no new self-hosted workflow, and does not alter the frozen structural discriminator.

## Bound prior observations

Existing Forschungsrun-2 transport evidence recorded:

- GitHub Actions `status=in_progress`: `0` runs.
- GitHub Actions `status=queued`: `141` runs.
- Structural native run `32810213066`: `queued`.
- Its execute job `97688005492`: `queued`, labels `self-hosted/Linux/X64`, `runner_id=0`, empty `runner_name`, zero steps.
- Recovery run `32811360359`: `queued` on the same label set.
- Its execute job `97691171499`: `queued`, `runner_id=0`, empty `runner_name`, zero steps.

The bounded prior classification was:

`SELF_HOSTED_RUNNER_NONASSIGNMENT_OR_OFFLINE_STRONGLY_FAVORED_OVER_ACTIVE_JOB_OCCUPANCY`

## New telemetry discriminator

The separate `chatgpt-vps-results` telemetry branch committed `vps_bridge/results/LIVE.json` at commit:

`9d2e7883f6e30d9314fb26eca1e0b3e1d772bee4`

with observation time:

`2026-08-25T05:58:41.799346+00:00`

The telemetry directly reports:

- host uptime command succeeded (`rc=0`), host up for about 1 day 1 hour;
- host load average approximately `0.40 / 0.40 / 0.44`;
- about 9 GiB memory available at the sampled instant;
- `/workspace` and `/cache` on the host filesystem had ample free capacity;
- the `clay-direct-dev` sandbox environment was reachable enough to emit its live process/workspace telemetry;
- long-running Clay processes were alive in that sandbox, including `run_free_evidence_forge.py`, `run_research_distillery_local.py`, `free swarm/evaluate.py`, `free swarm/update_fabric_live.py`, and the 6000-worker supervisor shell;
- the sandbox workspace itself existed and had a live Git checkout.

The telemetry also records a Podman `top`/cgroup diagnostic failure. That is evidence of a container-observability/cgroup limitation, not evidence that the host or sandbox is down.

## Updated inference boundary

This materially weakens a broad failure hypothesis:

`H0_VPS_OR_CLAY_DIRECT_DEV_HOST_IS_DOWN`

because independent bridge telemetry observed the host and Clay sandbox alive after the structural run had already entered the queued state.

The strongest bounded transport classification becomes:

`HOST_AND_CLAY_SANDBOX_LIVE_WHILE_GITHUB_SELF_HOSTED_JOB_UNASSIGNED`

and the highest-probability remaining fault region is narrowed to the transport layer between GitHub Actions scheduling and the retained execution host, for example:

- GitHub Actions self-hosted runner service not running or not connected;
- runner registration missing/stale;
- label or runner-group mismatch;
- controller/service wrapper failure preventing the listener from accepting work.

These are hypotheses, not directly observed facts. The connected GitHub surface used by this organ does not expose the repository runner registration/online/busy endpoint, and the VPS telemetry does not directly attest the GitHub Actions runner listener/service. Therefore `RUNNER_SERVICE_DOWN` is **not** promoted to fact.

## Scientific consequence

Nothing here changes J-Space evidence credit:

- the already-passed native llama.cpp cvec mechanism remains bounded component evidence;
- the structural label-free native discriminator remains unexecuted and has runtime credit `0`;
- a queue or transport failure is not a scientific negative;
- no canonical semantic J-Space, HCU, EntityOS, or training promotion follows.

The contemporaneous Run-2 promotion audit and polarity addendum remain the scientific claim boundary. Even if the frozen structural run later passes, its result remains bounded component evidence until the stricter promotion gates are satisfied.

## Next exact gate

Do not create another model experiment. Restore or expose the retained GitHub Actions self-hosted runner listener/registration/label path so one already-queued `self-hosted/Linux/X64` job receives a nonzero runner assignment and begins steps. Then execute the existing frozen structural run `32810213066` without changing its scientific source. Persist FAIL as counterevidence or PASS at its bounded component scope, followed by exact-current promotion-gate adjudication.

## Credit delta

- new model runtime credit: `0`
- native llama.cpp cvec component runtime credit: unchanged `1`
- structural label-free native runtime credit: `0`
- J-Space model runtime credit: `0`
- full HCU runtime credit: `0`
- whole EntityOS runtime credit: `0`
- training credit: `0`
- canonical semantic promotion: `false`

## Result

`PASS_HOST_LIVE_RUNNER_TRANSPORT_NARROWING_ONLY`

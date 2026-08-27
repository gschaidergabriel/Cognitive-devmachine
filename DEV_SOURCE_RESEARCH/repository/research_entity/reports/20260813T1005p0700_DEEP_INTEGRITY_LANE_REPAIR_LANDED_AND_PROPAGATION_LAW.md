# Deep Integrity lane repair landed — and the propagation law it exposed

**Program:** FRANK v0.1 · **Arbiter:** claude-code-lead · **Measured:** 2026-08-13T03:05Z

## What landed

PR **565** (`ci: restore Deep Integrity on current isolated self-hosted lane`) was squash-merged into `main` at
`2026-08-13T02:56:27Z`, merge commit `925ed87f0644dafd4dfbe899ee83cc80478e26a4`. One file changed:
`.github/workflows/frank-deep-integrity.yml`, `runs-on: ubuntu-latest` → `runs-on: [self-hosted, Linux, X64]`.

The post-merge `push` run on `main` (31662361357) executed **21 steps on runner `clay`** and concluded **success**.
Before the repair the same gate produced **0 steps, no runner, failure**, annotated by GitHub with
*"the job was not started because recent account payments have failed or your spending limit needs to be increased"*.

## What did not happen

Merging to `main` repaired **none** of the 227 remaining red pull requests. A `pull_request` run executes the
workflow definition carried by the pull request head lineage, not the one on `main`.

Controlled test on PR **567**, same PR, same content, one factor varied:

| intervention | run | resolved lane | runner | steps | conclusion |
|---|---|---|---|---|---|
| close + reopen, after the main repair | 31662464840 | `ubuntu-latest` | — | **0** | failure |
| update-branch against `main` | 31662607317 | `self-hosted` | `clay` | **21** | success |

The head at `7368fec6` still carried `runs-on: ubuntu-latest` on line 11; `main` carries the self-hosted lane on
line 18. Re-triggering an unchanged head re-runs the old instrument. Only ingesting `main` swaps it.

## Consequence for the research surface

The red field on `Dr.-Unterweger` is an **instrument state**, not Frank evidence — this now holds with a landed
counter-example, not just a census. It decays only as fast as branches ingest `main`. 227 open pull requests
remain red on `integrity` for this reason alone; each is one `update-branch` call away from a real verdict, with
no product change involved.

Two verdict classes must stay distinct in every downstream reading:
- **artifact red** — 0 executed steps, no runner: carries no information about Frank.
- **genuine red** — steps executed on `clay`: real evidence, must not be swept up in a bulk re-run.

## Prior artifacts

- `20260813T0951p0700_pr_gate_false_red_billing_blocker_census.json` — the 228/244 census.
- `20260813T0937p0700_external_gate_runner_measurement_instrument.json` — the same defect class, gate-wide.

# Hosted Actions billing blocker and the self-hosted resolution

- Date: 2026-08-13T09:51+07:00 (measured 2026-08-13T02:51Z)
- Actor: claude-code / claude-code-lead
- Program: FRANK v0.1
- Work event: `research_entity/frank_v0_1/work_events/20260813T0951p0700_pr_gate_false_red_billing_blocker_census.json`
- Evidence: `research_entity/frank_v0_1/evidence/20260813T0951p0700_hosted_actions_zero_step_billing_artifact.json`

## R0 — the observed state

`gschaidergabriel/Dr.-Unterweger` has **244 open pull requests**. **228 of them (93.4 %)**
carry a red check named `integrity`, from the workflow *Frank Deep Integrity*.

The red is not a test result. Job `94308410536` of run `31655324376`:

```
integrity | failure | steps=0 | runner= | labels=ubuntu-latest
annotation: The job was not started because recent account payments have failed
            or your spending limit needs to be increased.
```

Zero steps, no runner assignment. GitHub created the check, refused to start the
job for account payment / spending-limit state, and reported the refusal in the
same shape a failing test would take.

## The discriminating comparison

The same gate, same head class, one varied factor — the runner lane:

| lane | run | runner | steps | conclusion |
|---|---|---|---|---|
| `ubuntu-latest` | 31655324376 | — | 0 | failure |
| `self-hosted, Linux, X64` | 31654715032 | `clay` | 21 | success |

Runner `clay` was `online`, `busy=false` at measurement time. Capacity was never
the constraint.

## Not every red is an artifact

Four red checks sampled from the same surface executed real steps on `clay` and
are genuine Frank evidence: `fresh-main-integration` (14 steps), `boundary`
(15), `directory-anchor-repair` (9), `gate` (7). The artifact class is
identified by `steps == 0` on a hosted lane, not by redness. `central-state`
(job 93844104659, 0 steps, `ubuntu-latest`) belongs to the artifact class; its
9 PRs are a subset of the 228.

## Surface scan — how large the residue actually is

Of 143 workflow files on `main@4304810`:

- **138** already reference `self-hosted` — the bulk migration happened.
- **10** still reference `ubuntu-latest`; **3** of those trigger on `pull_request`.
- One of those three, `frank-deep-integrity.yml`, produces 93.4 % of the blocked
  surface on its own.

Hosted residue triggered on `pull_request`: `frank-deep-integrity.yml`,
`frank-bounded-issue-dispatch-bridge.yml`, `claycode-wp04-pr-hosted-shadow.yml`
(the last is named as an intentional hosted comparison lane and should be
quarantined rather than rerouted).
Hosted residue on push/dispatch: `frank-vps-runner-cross-repo-scope-probe.yml`,
`clay-go-python-import-path-equivalence.yml`, `clay-v18-push-dispatch-bridge.yml`,
`frank-central-state.yml`, `frank-v71-hardening.yml`,
`frank-effect-authority-provenance-gap.yml`, `frank-sqlite-v5-evidence-gate-v1.yml`.

## The repair already exists and is unmerged

- **PR #565** *ci: restore Deep Integrity on current isolated self-hosted lane* —
  draft, and its own `integrity` check is the 21-step success above.
- **PR #564** *fix(ci): run Frank Deep Integrity on self-hosted Linux runner* —
  draft, competing edit of the same file.

Both change `.github/workflows/frank-deep-integrity.yml`. **Exactly one may land.**

## Why this matters beyond CI hygiene

The research entity's promotion rule reads a red gate as evidence against a
candidate. For 228 of 244 open candidates that reading is currently unlicensed.
This is the same defect class as the external-runner translator artifacts of
2026-08-13T09:37+07:00 — a measuring instrument reporting its own failure in the
vocabulary of the measured object — now at repository scale rather than
gate scale. The generalisation worth carrying: **a verdict must state whether it
executed.** A gate that cannot distinguish "ran and failed" from "never ran"
launders infrastructure state into research evidence.

## Ranked next actions

1. Land exactly one of #565 / #564; close the other as superseded.
2. Re-run `integrity` across the blocked surface, re-measure the artifact share,
   and record the delta.
3. Reroute or explicitly quarantine the remaining 9 hosted workflows, keeping
   the intentional hosted-shadow lane distinct from accidental residue.
4. Record hosted-minutes account state as a declared external dependency of the
   FRANK v0.1 gate surface. Restoring it is an account-owner action outside the
   research entity.

## Not claimed

Nothing here says the Deep Integrity suite would pass on the blocked heads. It
says the current red does not tell us either way.

# External gate runner — two instrument artifacts that looked like verdicts

**Recorded** 2026-08-13T09:37+07:00 · **Actor** claude-code-lead (Anthropic, Claude Opus 5)
**Program** FRANK_V0_1 · **Product repo** gschaidergabriel/Dr.-Unterweger
**Instrument repo** gschaidergabriel/gabriel-claude @ `2529a5d0a2c24171110900a63488d54f752e657f`
**Evidence** `research_entity/frank_v0_1/evidence/20260813T0937p0700_external_gate_runner_instrument_artifact_false_red.json`

## What the instrument is

A gate runner on the accepted probe machine `frank-api` (31.97.117.141, hostname
`digital-retina` — *not* the SeiMensch VPS 72.61.19.188). It translates the live
Dr.-Unterweger gate workflows into standalone bash, runs them on the probe machine, and
writes the verdict back to the pull request as a commit status.

The point is not speed. It is that GitHub Actions stops being the only body able to issue a
gate verdict — and gates that Actions cannot even start still run. 24 gate scripts are
translated; 20 are armed.

The verdict rule is the gate's own: **exit code 0 AND the gate's `PASS_` marker in the log.**
Without a marker, the exit code alone decides.

## What went wrong

Three gates went red on every open PR within seconds. Both failures sat *before* the gate's
own decision step — that is the discriminator, and it is why the first of the thirteen banal
causes (measurement error) was not excluded here but **confirmed**.

**One mapping, two holes.** GitHub substitutes `${{ … }}` **textually** into the run body
before any shell parses it. The translator mapped expressions onto shell variables instead —
a different map, with a strictly smaller domain.

1. **Single quotes.** Shell expansion does not happen inside `'…'`.
   `TARGET_SHA='${PR_HEAD_SHA}'` stayed literal, so the fetch asked for a ref by that name:
   `fatal: couldn't find remote ref ${PR_HEAD_SHA}`, rc=128. Two of twenty gates.
2. **`working-directory` was not translated at all** — neither per step nor from
   `defaults: run:`. A gate that fetches its own tree to `/tmp` and points
   `working-directory` at it ran every step in the empty workspace:
   `fatal: not a git repository` from step 2 on, rc=1 after 2.4 s, 0 of 20 `PASS_` markers,
   red on 25 pull requests. One of twenty gates.

## Repair

Instrument only. No product file was touched, nothing was promoted, no authority minted.

The body now carries placeholders `@@LAEUFER:VAR@@`, and a generated bash function
substitutes them with the value before execution — **quoting-blind, exactly as GitHub does**.
Unknown expressions still remain visible as `UNKNOWN_EXPR_…` rather than vanishing.
`working-directory` is honoured per step and from `defaults`, as the 5th argument of the
generated `schritt()`; absent it, a step runs in `$GITHUB_WORKSPACE`.

## Measured (read live from the machine at 2026-08-13T02:37Z, not from session memory)

| Gate | before | after |
|---|---|---|
| `frank-provider-fence-fresh-main-vps` | rc=1 after 2.4 s, 0/20 markers | **rc=0 @ PR 520 `aa00dbdf`, 11 steps, 6 `PASS_` markers**; rc=0 on PRs 557, 558, 560, 564–567 at 8.1–8.6 s |
| `claycode-frontier-integration-vps` | rc=128, 2 steps | **pending** — no post-fix run on disk yet |
| `claycode-frontier-current-main-composition-vps` | rc=128, 3 steps | re-run started 02:37:17Z, still executing when this was written |

The composition gate is *expected* to run through and then be rejected by its own final
assertion (`coverage_percent == 90.0` required). That is a prediction until the run
completes, and it is recorded as one.

The false red verdicts were removed from the runner's state so the gates re-judge from
scratch; `zustand.vor-wd-fix.json` (298 entries) and `tore.vor-wd-fix/` hold the backup.

## What this changes epistemically

> A red verdict from a second instrument is a gate verdict **only if the instrument
> demonstrably reached the gate's own assertion step.**

This is one level below the earlier lesson that a red gate is not the same as a gate that
ran. Consequence for the runner: executed step count and `PASS_` marker count belong next to
the exit code in every verdict it writes.

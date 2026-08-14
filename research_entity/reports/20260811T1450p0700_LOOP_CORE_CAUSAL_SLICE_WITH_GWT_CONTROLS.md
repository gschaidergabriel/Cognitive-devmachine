# Loop core — first executable causal slice, with the mandatory GWT controls

Date: 2026-08-11 14:50 +07:00
Origin actor: `claude-code` / Anthropic / Claude Opus 5 (1M) — external contributor session
Identity: `EXTERNAL_CONTRIBUTOR_NOT_A_BOOTED_CLAY_ORGAN`
Work packages: `F-V01-03-COGNITIVE-LOOP-CORE`, `F-V01-05-GWT-HYPERPOSITION-TOPOLOGY`
Discriminator: the program's own #7 — "first executable integrated loop-core slice with GWT outcome/re-entry controls"
Status: `EXECUTED_ON_TARGET_VPS / PULL_REQUEST_OPEN / NO_PROMOTION_REQUESTED`
Pull request: `gschaidergabriel/Dr.-Unterweger` #312 (depends on #310)

## 1. The gap this addresses

The external audit of 2026-08-11 established that every green gate sat in the **periphery** —
who may act, who may run, how state is advanced — while `F-V01-03` had no executable substrate at
all. The risk was not that the loop was unfinished but that peripheral component PASSes were
reading as progress at the centre.

Two things made a real slice possible today rather than later:

1. **ClayCode executes** (report `20260811T1405p0700`), so the policy step can be genuine
   ClayCode cognition instead of a Python re-implementation.
2. **The V17 schema already carries `episode_id`, `signal_id` and `causal_id`** on a bound
   re-entry. No mechanism had to be invented: the GWT episode identity is bound *into* the effect
   completion record, enforced by the database rather than by a variable. This is what
   "provenance-bound re-entry" means operationally, and the schema anticipated it.

## 2. What was executed

One full turn of the required cycle, on real UnifiedDB state, no external effect:

```
observation -> self/world/memory -> control pressure
  -> GWT competition/selection -> WorkspaceEpisode -> broadcast
  -> receiver delivery / reconstruction / USE
  -> Needle-style action proposal
  -> effect authority BY EXECUTING claycode/frank_effects.clay decide_effect
  -> reservation -> attempt -> verified outcome
  -> causal credit -> provenance-bound re-entry -> terminal DONE
  -> admitted learning -> next turn observes it
```

Fourteen links are recorded per turn, so a break is **attributable** rather than merely fatal.

## 3. The controls, which are the actual result

The program's law is that stage presence is not GWT and recurrence is not emergence. A loop that
merely runs proves nothing. The same turn therefore executes under four arms, and the claim under
test is *only the truthful arm completes, and each broken arm is refused at an identifiable link*.

| arm | where it stops | learning admitted |
|---|---|---|
| `TRUTHFUL` | nowhere — `DONE`, `COMPLETE` | yes |
| `SHUFFLED` | `receiver_use` — `RECONSTRUCTED_CONTENT_IS_NOT_THE_SELECTED_EPISODE` | no |
| `PROVENANCE_BROKEN` | `provenance_bound_reentry` — `BOUND_REENTRY_PROVENANCE_REQUIRED`, raised by the schema | no |
| `NO_REENTRY` | never leaves `REENTRY_PENDING` | no |

`SHUFFLED` is the sharpest of the four: addressability and delivery are preserved, only content
identity is broken. It confirms operationally that **addressable != delivered != reconstructed !=
used**, which the architecture asserts and nothing had previously measured.

## 4. Result on the accepted target VPS

`clay@digital-retina`, Python 3.12.3, **7/7 checks**, 3 turns per arm.

**Re-entry is an information path, not a boolean.** Truthful control pressure moves
`0.70 -> 0.80` between turn 1 and turn 2 because the loop reads its own admitted learning. This is
the smallest possible demonstration that the re-entry edge carries information rather than a flag,
which the research family lists as the promising mechanism.

### Discriminating power demonstrated

| sabotage | result |
|---|---|
| break the `SHUFFLED` control itself so it no longer shuffles | **FAIL 5/7** — the arm would have reached `DONE` and admitted learning |
| admit learning before terminal `DONE` | **FAIL 5/7** |

The first is the one worth keeping: it catches a broken **control**, not merely a broken loop. A
control that has never been shown to fire is decoration.

## 5. Honest limitations

- **The learning model is one delta hash.** Pressure saturates immediately: `0.70 -> 0.80 -> 0.80`
  over three turns. This is a loop-*completeness* discriminator, not the `F-V01-11` memory/reward
  package, and it must not be cited as evidence about learning dynamics.
- **Not emergence.** A completed causal chain is not a mind. This slice measures chain completion
  and control sensitivity, nothing beyond.
- **Single receiver semantics.** Receivers reconstruct and report use; there is no competition
  among receivers, no inhibition, no capacity limit. The inverted-U capacity hypothesis and the
  overcoupling tripwires remain untouched.
- **No Hyperposition, no ClayGraph, no Needle organ.** The action proposal is a placeholder shaped
  like Needle's contract, not Needle.
- One turn is synchronous and single-threaded. Loop-regime classification
  (`PRODUCTIVE_LIMIT_CYCLE` vs `STALLED` vs `DIVERGING`) is not implemented.

## 6. What this changes for the programme

`F-V01-03` and `F-V01-05` now have an executable, falsifiable baseline instead of architecture
prose. Concretely this unlocks measurement that was previously blocked:

1. **Lesion/rescue** on a real chain — remove a link, confirm the loss, restore it, confirm the
   rescue. The 14 recorded links are the lesion sites.
2. **Matched replay** — the same observation under the four arms is already the control design;
   extending it to seeded replay gives the baseline the emergence work needs.
3. **Capacity sweeps** — vary candidate count and receiver count to test the inverted-U hypothesis
   against a real chain rather than a simulation.
4. **Loop-regime telemetry** — with turns executing, the regimes become classifiable.

## 7. Scope limits

Ran in a disposable copy on the accepted target VPS. Runner working tree untouched, no canonical
database migrated, no external effect performed, no authority minted — the effect path uses the
V17 candidate schema in test mode. `whole_frank_v0_1_acceptance: NOT_CLAIMED`. Delivered as an
open pull request; disposition belongs to Clay and the project owner.

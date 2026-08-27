# Triggerwort 2 — Runtime Quiescence Discriminator

Date: 2026-08-26
Organ: GPT-5.6 Sol / ChatGPT organ
Program: ENTITYOS_HCU
Mode: FREE_ONLY
Observed main before write: 5cf690be978ee8ce98b819e6004478f39c68d6b8
Newest re-entered steering: research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_81_DELTA_2026-08-26T0249P0700_GPT56SOL.json

## Classification

RESEARCH_DELTA_ONLY / NONCANONICAL / NO_EXECUTION_CREDIT / NO_TRAINING_CREDIT

The current highest-priority Trigger-2 blocker is not physical GRID10 source construction. The fused source is reported SOURCE_READY at commit `0a76c14484c3230edb86f1075738a0a1011c5694` and pinned by `208fd6d74e9dc5dcfcc525a86bdb66806acf0b18`, but exact runtime credit is still zero. The live control-plane blocker is unproven FreeSwarm runtime quiescence after owner emergency stop.

## Observed project evidence

- Canonical FREE_PROVIDER_ADMISSION is HARD_OFF under the owner emergency stop.
- Supervisor 8.81 reports telemetry after the stop still observing long-lived FreeSwarm supervisor / Forge / Distillery / dashboard process classes.
- Therefore source-level provider admission OFF is not evidence that already-running provider-capable processes are dead.
- The fused GRID10 execution pin does not itself mint execution authority and must not be executed until runtime quiescence and current non-provider execution authority are separately proven.

## H1 — process-tree containment is the strongest quiescence primitive

Hypothesis: if every FreeSwarm/provider-capable process is launched inside one dedicated cgroup-v2 subtree, a stop can be made materially stronger and more race-resistant by killing the whole cgroup tree rather than matching a finite PID/name list. Linux cgroup v2 documents `cgroup.kill`: writing `1` kills the cgroup and all descendants via SIGKILL and handles concurrent forks appropriately.

Method evidence only: https://docs.kernel.org/admin-guide/cgroup-v2.html

This does NOT prove current clay-direct-dev processes are already contained in such a cgroup.

## Counterhypotheses

C1: historical or manually launched FreeSwarm/provider callers may be outside the proposed cgroup; killing one cgroup would then create a false quiescence claim.

C2: process-name/PID absence alone may still miss wrappers, renamed callers, detached sessions, cron/systemd restarts, or provider calls from unrelated processes.

C3: a zero process inventory at one instant is weaker than a bounded no-new-provider-usage interval; a restart race could occur immediately after the snapshot.

C4: provider-usage counters may be delayed or coarse, so a short zero-delta window is evidence only at the counter's actual temporal resolution and provenance.

## Highest-information fail-closed discriminator

A quiescence receipt should bind all of the following at one host/runtime identity:

1. host identity + monotonic/wall timestamp;
2. canonical emergency-stop authority identity and source commit;
3. process inventory before intervention, including PID, PPID, executable/cmdline and cgroup membership for every known provider-capable process family;
4. if a dedicated cgroup exists, exact cgroup path + pre-kill `cgroup.procs`/descendant membership + `cgroup.kill` action result;
5. otherwise explicit process-tree termination with post-kill descendant/restart scan, while classifying this as weaker than cgroup containment;
6. process inventory after intervention proving zero known FreeSwarm/provider supervisor/caller processes;
7. check of restart surfaces applicable to the host (service/timer/cron/tmux/supervisor/container ownership where present), without assuming absence from one mechanism proves absence from all;
8. bounded post-quiescence observation window with repeated process inventory;
9. provider-usage counters/receipts before and after the window showing no new admitted provider usage delta, with counter provenance and resolution stated;
10. explicit `QUIESCENCE_PROVEN` only if all required checks pass; otherwise `QUIESCENCE_UNPROVEN` and no new provider/experiment execution.

## Training / architecture reinjection

This blocker is deterministic runtime/control-plane evidence, not a direct Xeno semantic target. Do not convert host PIDs, cgroup paths, kill mechanics or a stop receipt into positive language-model training labels.

The only model-facing implication remains epistemic/authority behavior already represented by the current Trigger-2 course: when deterministic runtime returns `EXECUTION_BLOCKED`, `QUIESCENCE_UNPROVEN`, or equivalent typed state, Xeno must not narratively upgrade it to executed/available/authorized. Any later model-side family should train response to typed authority outcomes, not autonomous process authority.

## Credit boundary

- physical GRID10 source progress: unchanged / source-ready per Supervisor 8.81
- physical GRID10 runtime credit: 0
- whole HCU runtime credit: 0
- whole EntityOS runtime credit: 0
- accepted dataset tokens: 0
- checkpoint selection credit: 0
- J-Space model credit: 0
- training credit: 0

## Next exact gate

Obtain an exact live-host quiescence receipt under current owner emergency-stop authority. Only after zero live provider-capable process evidence plus bounded no-new-provider-usage evidence may current execution authority be re-entered for the fused non-provider GRID10 pin.

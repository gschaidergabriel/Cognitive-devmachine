<!-- RAE_META
{"packet_id":"KMP-FRANK-R10-ADAPTIVE-RECURRENCE-HALTING-20260809","title":"KMP-FRANK-R10-ADAPTIVE-RECURRENCE-HALTING-20260809","domains":["frank"],"epistemic_class":"EXTERNAL_PRIMARY_RESEARCH_PLUS_INTERNAL_SYNTHETIC_DISCRIMINATORS_AND_ARCHITECTURE_INFERENCE","claim_status_hint":"OPEN","origin_actor":"chatgpt-secondary","source_refs":["frank-20260809T1931p0700-chatgpt-secondary-log-state-three-cycle"]}
RAE_META -->

# KMP-FRANK-R10-ADAPTIVE-RECURRENCE-HALTING-20260809

packet_id: `KMP-FRANK-R10-ADAPTIVE-RECURRENCE-HALTING-20260809`
domains: `frank, loop_dynamics, gwt, model_runtime, harness, performance, emergence`
epistemic_class: `EXTERNAL_PRIMARY_RESEARCH_PLUS_INTERNAL_SYNTHETIC_DISCRIMINATORS_AND_ARCHITECTURE_INFERENCE`
status_hint: `OPEN`
origin_actor: `chatgpt-secondary`
provider: `OpenAI`
model: `GPT-5.6 Sol`
canonical_parent: `r2:04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
run_id: `frank-20260809T1931p0700-chatgpt-secondary-log-state-three-cycle`

## Atomic hypothesis

FRANK should retain an adaptive typed recurrence controller rather than collapse loop control to a fixed iteration count or state-delta-only stop rule. The useful stopping decision is likely estimator/version and state dependent: convergence evidence, unresolved residual pressure, marginal recurrence utility/cost, recurrence budget, overthinking/divergence and readout quality should remain distinguishable measurement channels.

This does not establish the current numerical thresholds as optimal.

## Internal support

- Earlier constructed FRANK discriminator: delta-only control could not separate low-change convergence from low-change unresolved stalls; typed signals sharply reduced those constructed failures.
- Residual-readout quality experiment: false convergence reappeared as residual measurement noise increased, supporting explicit estimator uncertainty/freshness.
- Current `Dr.-Unterweger` trajectory adapter fuses short-trajectory dynamics with residual-quality metadata and keeps all decisions proposal-only.
- This run found and repaired invalid-telemetry/policy-identity gaps in the H1 quality-gate reference.

## External primary research

- Graves, *Adaptive Computation Time for Recurrent Neural Networks* (arXiv:1603.08983): recurrent computation can adapt the number of computational steps to input/task demands; benefits are task-dependent rather than universal.
- Banino et al., *PonderNet: Learning to Ponder* (arXiv:2107.05407): learns adaptive computational depth with an explicit accuracy/compute tradeoff.
- Kohli et al., *Loop, Think, & Generalize* (arXiv:2604.07822): recurrent-depth transformers improve controlled compositional/depth extrapolation, while excessive recurrence produces overthinking; transfer to live FRANK/pretrained 4B behavior remains unproven.
- Oncescu et al., *The Recurrent Transformer* (arXiv:2604.21215): recurrence can trade effective depth against width/cache cost in tested small-model regimes; it does not validate FRANK's controller or thresholds.

## Counterhypotheses

1. A tuned fixed-budget/event-driven controller may match or beat typed recurrence on real FRANK episodes with less state/provenance overhead.
2. A single global controller may be harmful because GWT, memory, graph/topology and model recurrence operate on heterogeneous timescales.
3. Residual pressure and marginal utility may be too noisy or expensive to estimate online; simpler observable proxies may dominate.
4. Adaptive halting benefits observed in synthetic/small recurrent models may not transfer to the target Qwen-class 4B plus FRANK architecture.

## Highest-information falsifier

On frozen/live-derived H1 Golden Trace episodes, compare at least:
- fixed-depth recurrence;
- state-delta-only stopping;
- residual-aware dual-signal stopping;
- typed quality-gated adaptive recurrence.

Match task/outcome quality and measure false convergence, missed productive recurrence, overthinking/divergence, route/escalation rate, latency, tokens/compute, memory, recovery behavior and effect-gateway non-authority. Stratify results by residual estimator/version and task/loop family.

## Promotion boundary

OPEN. No scientific promotion until real/frozen H1 episodes and later target-Ubuntu/4B evidence distinguish the alternatives.

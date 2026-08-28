# GO 2026-08-25 — self-hosted queue evidence boundary v1

## Authority and scope

- Persistent entity: Clay
- Product: EntityOS
- Integrated cognition/compute architecture: HCU
- Supervisor observed: 8.73 / FREE_ONLY
- Canonical `main` immediately before this write: `75b120e9a94b3c5f4f627d9cda44d5128df15086`
- Scope: runtime-evidence control-plane classification only; no EntityOS/HCU runtime, model, provider, or training credit is claimed.

## Direct repository observations

Retained Forge -> Distillery runtime lane: PR `gschaidergabriel/clay-global-research-entity#1619`.

Observed run `32753831629` remained `queued` with no conclusion. Current artifact re-entry also records runs `32742535392` and `32752823987` as queued and no repository-bound terminal Distillery receipt.

The run state therefore establishes only nonterminal execution scheduling. It does not establish execution of the Forge/Distillery validator, success, product failure, or semantic negative evidence.

## External primary-source discriminator

GitHub's current self-hosted-runner documentation states that a job is dispatched only when an online, idle runner matches the requested labels/groups; otherwise the job remains queued until a matching runner comes online. GitHub also states that a queued job eventually fails after the documented queue timeout.

Primary sources consulted:

- https://docs.github.com/en/actions/reference/runners/self-hosted-runners
- https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/use-in-a-workflow

This yields a stronger evidence classification for the current nonterminal runs:

`QUEUED_SELFHOSTED_RUNNER_AVAILABILITY_OR_ROUTING_UNRESOLVED`

rather than any EntityOS/HCU semantic failure classification.

## Hypothesis / counterhypothesis

Hypothesis H1: the retained runtime runs are queued because no online idle self-hosted runner currently matches the workflow routing requirements.

Counterhypothesis H2: a matching runner exists, but a different scheduling/account/workflow constraint is preventing assignment.

The present GitHub run state alone cannot distinguish H1 from H2. The cheapest high-information discriminator is direct runner/bridge health and routing-label observation, followed by a real roundtrip receipt on the authorized development surface.

## Consequence for the three GO tracks

### Track A — EntityOS executable convergence

Advanced the runtime-evidence boundary: queued self-hosted runs are now explicitly classified as scheduling/runner uncertainty, not product execution evidence. The exact next gate is runner/bridge health + matching-label observation, then terminal exact-current Forge -> Distillery evidence.

### Track B — HCU + Typed Entry Fabric

`HCU_NO_CHANGE_WITH_REASON`: the replay-stable identity and concurrency primitive is already fused on canonical `main`; source duplication would reduce convergence. The next useful HCU/Typed-Entry promotion depends on executable path evidence.

### Track C — Global J-Space/GWT readiness

`TRAINING_READINESS_NO_CHANGE_WITH_REASON`: the highest-information local Qwen3-0.6B six-control intervention remains unusual-experiment lease gated. No reproducible shared immutable macrocycle/request identity was available in this invocation, so no new unusual experiment was performed.

## Evidence credits after this receipt

- whole EntityOS/HCU runtime credit: 0
- full HCU runtime credit: 0
- J-Space model runtime credit: 0
- training credit: 0
- whole-product PASS: false

## Next exact action

Observe/repair the authorized VPS bridge/self-hosted runner health and routing labels on a surface that can actually access `clay-direct-dev`; capture a real roundtrip receipt. Then re-observe PR #1619 and require a terminal exact-current Forge -> Distillery receipt before any runtime promotion.

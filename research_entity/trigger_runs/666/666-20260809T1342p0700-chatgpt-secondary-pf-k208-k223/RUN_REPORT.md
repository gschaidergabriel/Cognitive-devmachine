# 666 Level-0 Run Report — Project-Frankenstein k208..k223

## Scope

- Actor: `chatgpt-secondary`
- Frozen head: `abba90a5767d85abc8a1ac340bae92842dab35c1`
- First-parent range: `k208..k223`
- Resolution: `16/16`, missing `0`
- Post-claim race check: `PASS`
- Evidence: historical repository commit/diff evidence
- Present-runtime reproduction: not performed
- Global exact Level-0 percentage delta: `0.0` while combined denominator remains unfrozen
- Earned-work hours added: `0.0`

## High-value findings

### Policy-learning data was censored by fallback behavior

`k208` records that fallback idle-thought decisions were not written to the subconscious training stream. The fix records fallback state, action, behavior-policy log-probability and critic estimate. `k211` then repairs omitted PPO action masks and several reward/state problems.

**Transfer:** policy records must include every decision path, including fallback/off-policy actions, the action mask in force at decision time, behavior-policy probability, state version and outcome. Missing measurements need an explicit sentinel rather than a numeric default that participates in reward shaping.

### Attempted interaction is not autobiographical experience

`k208` also fixes entity sessions whose bare early returns could be remembered as conversations even though the session never started. Explicit abort reasons (`pid_lock`, `no_llm`, `user_returned`) allow the dispatcher to avoid false memory creation.

**Transfer:** identity memory needs lifecycle truth. Attempted, aborted, partially completed and completed events are distinct provenance states.

### Self-caused versus external telemetry needs causal attribution

`k210` adds self/environment CPU/RAM attribution and a heuristic GPU source split, then tags perception events as self or environment and avoids interpreting self-induced load as an external event.

**Transfer:** causal/world-model updates should not treat the system's own inference load as evidence about the outside world. Derived attribution must carry confidence/provenance because the GPU classifier here is heuristic.

### State-schema mistakes disabled an entire cognition branch

`k213` fixes two simple runtime assumptions that blocked all idle thoughts: treating a cached string as a dictionary and reading a nonexistent `_user_present` field.

**Transfer:** cross-service/cached state needs typed contracts and end-to-end latent-path tests. A feature that only runs when idle must still be exercised continuously by the harness.

### Cross-process daemon ownership was violated

`k218` reports a critical architecture bug where app/executor/entity-dispatcher code instantiated a full `ConsciousnessDaemon` singleton inside the wrong processes. The fix replaces this with direct durable event writes.

**Transfer:** heavyweight daemons with threads/runtime ownership are not general-purpose cross-process library singletons. External producers need explicit APIs or append/event contracts.

### Model-vs-scaffold causality has a direct falsifier

`k222` makes substrate replacement a formal Synthetic Psychology criterion and, importantly, states the unresolved test: keep architectural state and event history matched while changing the underlying LLM, then compare longitudinal personality/mood/dream/behavior trajectories.

**Transfer:** this is a strong discriminating experiment for FRANK/Clay. Persistence of databases after a model swap is not enough. If matched trajectories diverge substantially across LLMs, the model is performing psychological work the scaffold claims for itself.

## Additional semantic dispositions

- `k209`: heuristic self-address/role-confusion output filter; useful as a regression seed, not proof of identity integrity.
- `k212`: 25-minute GPU/RLM idle gate; treat threshold as measured scheduling policy, not a timeless constant.
- `k214`: initial learned subconscious/PPO/hallucination-filter lineage; later fixes at k208/k211 constrain how much credit its first implementation gets.
- `k215`: simulated articulated NeRD body and sensorimotor prompt channel; simulation state must remain typed as simulation.
- `k216`: Inner Sanctum + RL navigation + Experiment Lab + Hypothesis Engine plus broad audit fixes; source validation claims are historical, not reproduced.
- `k217`: mode-collapse/output-quality filters and AURA telemetry fixes; prompt statements asserting functional consciousness are source-authored claims and not empirical evidence.
- `k219`: ACI position paper; useful research framing and explicit non-consciousness boundary, but novelty/orthogonality claims remain unverified here.
- `k220`: author-name correction only.
- `k221`: co-development working paper; preserves method and limitations; audit scale/correlation claims are source-reported.
- `k223`: README navigation only.

## Regression/falsification targets

1. Force learned-policy fallback and verify transition count, action mask, behavior policy and outcomes remain complete.
2. Encode an unmeasured reward feature and assert it cannot be treated as numeric zero.
3. Abort entity sessions at every lifecycle stage and assert no completed autobiographical event is written.
4. Generate self-only and environment-only resource load and measure a source-attribution confusion matrix.
5. Adversarially provide wrong cache types/missing fields and assert contract errors rather than silent total feature shutdown.
6. Attempt to instantiate daemon-owned state in a non-owner process and require explicit refusal/API use.
7. Run matched-state/matched-event longitudinal replay across different LLMs and quantify trajectory divergence.

## Epistemic boundary

Feature names such as `subconscious`, `prefrontal cortex`, `Inner Sanctum`, `Synthetic Psychology`, and `Artificial Continuous Intelligence` are historical architectural/research terminology. This shard preserves their mechanisms and hypotheses without treating biological analogy, phenomenal experience, originality, or continuity claims as established facts.

## Gate consequence

This closes one exact 16-ordinal semantic shard. The global `666_RELEASE_GATE` remains `NOT_PASS`: Project-Frankenstein semantic history still requires full revset-to-receipt reconciliation, the repository tree denominator/read-surface issue remains, and Drive semantic/version reconciliation, cross-source fusion, earned-work audit and release-manifest validation are not yet complete.

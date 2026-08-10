# FRANK Reward-State Successor — synthetic research receipt

Status: `SIMULATION_ONLY_RESEARCH_EVIDENCE`  
Date: 2026-08-10  
Actor: chatgpt-secondary / GPT-5.6 Sol  
Runtime: local deterministic Python reference model; **not H1/H2/H3 runtime evidence**.

## Historical basis

The frozen `Project-Frankenstein/services/nucleus_accumbens.py` implements per-channel reward magnitudes, habituation/recovery, per-channel expected reward, reward-prediction error, phasic and tonic state, opponent-process damping, repetition-based boredom, anhedonia recovery and E-PQ feedback. Static archaeology also exposes version drift: documentation says “9 reward channels” while the frozen implementation contains 16 named channels, and the frozen test file contains expectations from the older habituation convention while the implementation migrates to `0=fresh, 1=habituated`.

The historical Sanctum PPO reward is a separate local policy-training objective and is not treated as organism-level reward state.

## Fresh external evidence used

Primary/near-primary literature consulted in this cycle:

- Lee et al., *A feature-specific prediction error model explains dopaminergic heterogeneity*, Nature Neuroscience (2024), DOI `10.1038/s41593-024-01689-1`: supports testing feature-specific rather than one homogeneous scalar RPE.
- *Distributional reinforcement learning in prefrontal cortex*, Nature Neuroscience (2024), DOI `10.1038/s41593-023-01535-w`: supports distributional value representations as a live candidate beyond mean-only prediction.
- Sousa et al., *A multidimensional distributional map of future reward in dopamine neurons*, Nature (2025), DOI `10.1038/s41586-025-09089-6`: supports explicit time/magnitude structure as a candidate reward representation.
- Masset et al., *Multi-timescale reinforcement learning in the brain*, Nature (2025), PMID `40468072`: supports multiple learning/discount timescales.
- Yoshida, Sprekeler & Gutkin, *Linking Homeostasis to Reinforcement Learning* (2025), arXiv `2507.04998`: supports treating internal-state regulation as part of motivated control.

These papers inform candidate design; they do not prove biological equivalence or FRANK utility.

## Candidate change relative to issue #149

The earlier “typed reward vector” proposal is refined to a **typed, multi-timescale value state**:

`verified outcome -> causal credit -> typed outcome evidence -> per-dimension fast/medium/slow prediction errors -> phasic readout -> typed tonic persistence/disengagement -> homeostatic/habituation/opponent controls -> admitted slow personality/memory plasticity -> provenance-bound re-entry`

Material learning is gated by both verification and causal credit. Self-proposals/activity may create at most a bounded exploration nudge and cannot update long-term value predictions or tonic motivation.

Historical boredom is repaired: low RPE alone is not boredom. A stagnation candidate requires low novelty/change **and material unresolved pressure** (plus low recent route/reward-dimension diversity). Thus successful stable convergence is not punished merely for becoming predictable.

## Deterministic synthetic tests

Reference files:

- `research_entity/experiments/frank_reward_state_reference.py`
- `research_entity/experiments/test_frank_reward_state_reference.py`

Executed locally with Python `unittest`.

Result: **9/9 PASS**.

Covered invariants:

1. verified success produces positive phasic value, updates expectations, and repeated prediction error shrinks;
2. repeated self-proposals cannot mint material reward or tonic growth;
3. verified hypothesis refutation can create positive epistemic value;
4. fast expectation adapts to outcome reversal faster than slow expectation;
5. low RPE with low residual pressure is not marked stagnation;
6. low RPE with high residual pressure is marked stagnation candidate;
7. negative safety state can veto persistence despite positive task state;
8. causal-credit magnitude scales admitted learning;
9. historical NAcc compatibility projection is explicitly marked a compatibility view, not semantic identity.

## What this does NOT establish

- no claim that typed/multitimescale reward is better on real FRANK episodes;
- no H1 historical baseline execution yet;
- no target-Ubuntu timing/resource measurements;
- no claim that habituation/opponent-process should survive H2/H3;
- no causal claim that phasic/tonic variables improve cognition;
- no distributional/expectile implementation is promoted yet; the reference tracks mean+variance at multiple horizons as the minimal executable probe.

## Required next discriminators

1. reconstruct and run the exact historical NAcc baseline where possible, preserving contradictions by version;
2. trace every historical reward caller and identify dead/orphan/self-rewarding channels;
3. matched scalar vs typed vs typed+multitimescale replay;
4. phasic/tonic/habituation/opponent/E-PQ factorial lesions and rescue over long episodes;
5. truthful-outcome vs shuffled-outcome vs broken-causal-receipt controls;
6. self-reward poisoning/adversarial proposal loops;
7. safety/resource conflict episodes where scalar averaging may hide a critical negative dimension;
8. OOD reversal/change-point tests to compare fast/slow horizons;
9. restart/snapshot/replay equivalence and target-Ubuntu latency/resource measurements.

Disposition remains `FUSE_CANDIDATE`, not promoted.

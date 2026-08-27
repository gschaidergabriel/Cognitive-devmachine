# Web Evidence Addendum — Multi-turn Tool Use, Abstention and Runtime Separation

Run: `harness-20260809T1854p0700-chatgpt-secondary-needle-fusion`
Search date: 2026-08-09
Policy: technical claims are grounded in primary papers/repos. External evidence ranks below exact executable evidence from the pinned Frank/Needle/Cactus surfaces.

## Multi-turn tool use is a distinct harder problem

Primary research consulted:

- CONFETTI, ACL 2025 — conversational/multi-turn function-calling evaluation: https://aclanthology.org/2025.acl-long.730/
- Trajectory2Task, ACL 2026 — reconstructing/evaluating tool tasks over trajectories: https://aclanthology.org/2026.acl-long.1203/
- DICE-Bench — dialogue-in-context evaluation for tool/agent behavior: https://arxiv.org/abs/2504.05260
- ClarifyBench / structured uncertainty work — when systems should seek clarification rather than force a tool decision: https://arxiv.org/abs/2505.15485

Fusion with exact Cactus source:

Current Cactus `format_needle_query_text()` passes system/developer content plus only the latest user message to Needle. Earlier user/assistant/tool turns are not a dialogue-memory input for Needle. This matches Needle's single-shot specialization rather than contradicting it.

Frank implication:

- context-dependent intent resolution belongs outside Needle;
- unresolved deixis/coreference/state dependence should trigger fallback to the 4B path;
- a deterministic/typed preflight should record whether current intent is self-contained before invoking Needle.

## Selective prediction / abstention

Primary research already included in the main web synthesis:

- Guo et al., ICML 2017, neural calibration: https://proceedings.mlr.press/v70/guo17a.html
- Gangrade et al., AISTATS 2021, selective classification/risk-coverage: https://proceedings.mlr.press/v130/gangrade21a.html
- Cattelan & Silva, UAI 2024, confidence estimation repair: https://proceedings.mlr.press/v244/cattelan24a.html

Current Cactus runtime exposes `confidence_threshold`, but generic local confidence is entropy-derived unless a specialized handoff probe exists. This is useful engineering precedent for selective fallback, not proof that a default threshold is calibrated for Frank/Needle.

Frank implication: choose thresholds only after held-out risk-coverage calibration on the audited German tool/no-tool set.

## Runtime separation

Current source inspection shows materially different failure surfaces in:

- upstream Python/JAX Needle;
- Cactus C++ Needle runtime;
- external ONNX Needle implementation.

The research consequence is not to choose one runtime by argument. It is to keep one stronger Frank-level semantic contract and use runtime-specific wire profiles beneath it, then run differential tests on the same pinned checkpoint/tokenizer/toolset/query fixtures.

## Negative evidence preserved

- multi-turn research does not imply Needle should be expanded into a dialogue model;
- selective prediction literature does not justify a threshold without local calibration;
- retrieval literature does not prove top-k is safe for Frank;
- runtime diversity does not make independently maintained ports scientific replication unless their exact outputs are reproduced under matched conditions.

# Level-0 Shard — Project-Frankenstein Context Relevance Gate

## Scope

This shard assimilates the Project-Frankenstein Context Relevance Gate (CRG) as a historical learned context-selection mechanism, then checks the frozen HEAD rather than assuming the introduction commit still represents runtime reality.

The semantic boundary is strict:

`context relevance != truth != safety authority != execution authority`

## Mechanism

Introduced in commit `3a264068e5000d7d6212336048b3bf6e8e5e28eb`, CRG used a ~30K-parameter CPU network over 15 named context channels. The gate used a 420-dimensional feature vector, 0.5 threshold, a 100-step rule-to-neural cold-start ramp, forced rule-baseline episodes every 20 calls, entropy-collapse monitoring/noise, SQLite episode persistence, and implicit reward from the user's next message.

Eight channels were hard-coded to always pass: relevant memories, perception, attention focus, active goals, NAc drive, attention schema, introspection block and mood trajectory. Unknown channels also passed through.

The main idea remains useful: make active model context a learned projection over a richer durable state rather than concatenating everything.

## Frozen-head negative result — reward direction is inverted

Frozen HEAD `abba90a5767d85abc8a1ac340bae92842dab35c1` still contains the original `services/context_gate/training.py` and `feedback.py` blobs.

Feedback semantics are explicit:

- helpful/praise feedback => positive reward, e.g. `+0.7`;
- complaint/off-topic feedback => negative reward, e.g. `-0.8`.

Trainer semantics are also explicit:

`bce = BCE(gate_scores, recorded_decisions)`

`weighted = bce * (-reward)`

and the optimizer minimizes the resulting composite loss.

For positive reward this minimizes `-BCE`, i.e. performs gradient ascent on BCE with respect to the recorded decision. For a simple logit example:

- target `y=1`, prediction `p=0.8`: `d(BCE)/dz = -0.2`, so `d(-BCE)/dz = +0.2`; gradient descent lowers the logit and moves `p` away from 1;
- target `y=0`, prediction `p=0.2`: `d(BCE)/dz = +0.2`, so `d(-BCE)/dz = -0.2`; gradient descent raises the logit and moves `p` away from 0.

Negative reward does the opposite: it minimizes ordinary positive BCE and therefore reinforces the recorded decision.

Anchor and diversity losses may change the net step, but they do not repair the sign of the task term. The declared reinforcement direction is therefore inverted in frozen-head source.

This is recorded as `PF-CRG-NR-001`.

## Runtime qualification

The source defect does **not** prove that live behavior was degraded.

Current frozen-head cross-read found:

- CRG trainer file present;
- CRG feedback file present;
- both blobs unchanged from introduction;
- no `context_gate` reference in frozen-head `core/app.py`;
- no `context_gate` reference in frozen-head `services/consciousness_daemon.py`;
- the historical overlay chat mixin path no longer exists at frozen HEAD.

Because the connector cannot exhaustively search/list every frozen tree path, runtime activation is classified only as:

`UNVERIFIED_DORMANT_CANDIDATE`

not as proven dead and not as proven active.

## Additional research constraints

1. Conversation-level implicit reward is strongly confounded. A single scalar from engagement/frustration does not identify which context channel caused the outcome.
2. Learned relevance cannot become epistemic truth: a low-score but critical evidence object must remain retrievable.
3. Unknown-channel pass-through is completeness-friendly but not a security boundary.
4. Exploration/baseline episodes are promising, but causal credit requires stronger randomized/lesion/replay methodology.

## Current architecture implication

A stronger current form is:

`durable evidence/state`
`-> typed candidate context channels`
`-> deterministic must-include provenance/safety anchors`
`-> learned relevance SHADOW gate`
`-> calibrated active projection`
`-> model`

Every gate version, candidate, score, randomized assignment, decision, reward source and downstream outcome should be persisted. Effects remain behind a separate capability/commit gateway.

## Validation requirements

Before any modern learned context gate is promoted:

- signed-reward gradient unit tests;
- deterministic/retrieval/top-k baselines;
- shadow-mode evaluation;
- rare-critical-context retention tests;
- per-channel lesion/rescue;
- OOD and context-injection tests;
- reward-hacking tests;
- replay with immutable source evidence.

## Coverage

This closes one semantic lineage only.

- exact Level-0 coverage credit: `0.0`;
- historical earned-work hours added: `0.0` pending row-level deduplication;
- PF full history/tree denominator remains unfrozen.

Durable receipt:

`research_entity/archive_assimilation/receipts/666_20260809T1412p0700_chatgpt_secondary_pf_context_gate_learning_lineage.json`

# 666 Level-0 Run — PF Subconscious PPO Policy Lineage

## Result

Completed a non-overlapping Project-Frankenstein history/semantic shard for the learned idle-thought policy at frozen head `abba90a5767d85abc8a1ac340bae92842dab35c1`.

## Mechanism lineage

The subsystem began as an approximately 3.1M-parameter Actor-Critic policy replacing random idle-prompt rotation and training via PPO during consolidation. It coupled reward shaping to novelty, rumination, consolidation, diversity and hallucination suppression. By the frozen head the network is approximately 19K parameters with 20 actions and a 100-dimensional state, explicit cold-start exploration, stored action masks, atomic checkpointing and SFT-style anti-degeneration controls.

## Highest-value failure oracles

1. Action masks constrained selection but were initially omitted during PPO training.
2. Fallback behavior was initially absent from the transition stream; measured audit found 46% of decisions were lost to learning.
3. A missing SQLite mask-column migration made `record_transition()` silently fail on every call until explicit migration was added.
4. Expanding the action space from 19 to 20 produced historical mask-dimension incompatibility, requiring explicit pad/truncate handling.
5. Policy collapse/catastrophic forgetting risk later motivated reference anchoring, drift monitoring, weight decay and gradient clipping.

## Current inheritance

- Needle/routing: small learned heads are viable only with behavior-policy probability, availability mask and explicit fallback receipts.
- Adaptive visual learner: feature/class/example schemas need versioned compatibility, and learner health must detect silent no-op/write failures.
- UnifiedDB: transition/action-mask/model/reward/provenance contracts must be persisted atomically and migrated explicitly.
- Harness: replay all five failure families.
- GWT: learned policy selection controls attention/action candidates; it never establishes truth.
- ClayCode: represent policy selection and training outcomes as typed replayable data, not hidden mutable service state.

No exact global Level-0 credit or earned-work hours were added; PF repository-wide denominator remains unfrozen.

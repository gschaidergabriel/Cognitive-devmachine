# CCW-001 FUSION 1 — current internal state before external destruction

## Hard fresh fact
Accepted self-hosted target evidence at target commit `f649ce7...` falsifies the current V17 candidate's claimed causal closure: terminal DONE was accepted with V15 still IDLE epoch 0, no V16 execution context, absent canonical GWT/causal/delta support rows and fabricated support identifiers. This is a real negative discriminator, not a hypothetical concern.

## Source-level cause
Current V17 candidate storage binds `episode_id`, `signal_id`, `causal_id` and `admitted_delta_hash` mainly as non-empty text. Its canonical guard verifies the V14 effect attempt/outcome relation but does not require those support identifiers to resolve to one canonical causal chain. The current high-level ClayCode effect source also has a `finish(VerifiedEffectReceipt)->DoneReceipt` shape that does not itself encode the GWT/use/credit/delta support chain.

## Live swarm state
Direct conventional repair is already owned by PR279/PR280. Those lanes bind terminalization to current durable execution-generation evidence plus canonical GWT/use, outcome, causal-credit and admitted-delta or typed no-learning support. CCW must not duplicate them.

## Research reframing
The deeper question is whether fixing references still leaves a redundant semantic authority surface. Current architecture models DONE as something that can be inserted/persisted after support exists. CCW asks whether this is the wrong ontology: perhaps completion should be a proposition derived from canonical support, never an independently writable fact.

## Initial strongest counterhypothesis
A normal relational design is enough: add exact canonical references/constraints, perform REENTERED + DONE receipt in one transaction, keep the receipt immutable, and revalidate when needed. If that matches CCW correctness and recovery with lower read cost, CCW is architecture theater and should be killed.

## Safety invariants held fixed
Verified provider outcome is durable evidence and cannot be fictionally rolled back. Reconciliation after execution turnover stays legal evidence work, not new effect authority. GWT activation is not truth. Causal credit requires actual use/outcome support. Frank cannot mutate its Harness. A research candidate has no effect authority.

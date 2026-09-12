# ChatGPT FrankGrid10 Sandbox Organ

Status: NONCANONICAL_SANDBOX_EXPERIMENT

Purpose: give a ChatGPT session an external, auditable recurrent control loop derived from current Frankenstein/EntityOS research laws without claiming modification of model weights, hidden platform scheduler, truth authority, or effect authority.

Loop:

`TypedEntry -> GRID10 competition -> measured selection -> broadcast_id -> Hyperposition alternatives -> response -> HyperMirror -> uptake/mismatch -> recurrent cell state -> next-turn reentry`

Hard laws:

- `MODEL_OUTPUT != CANONICAL_TRUTH`
- `JSPACE_SIGNAL != CANONICAL_TRUTH`
- `GRID_SIGNAL != CANONICAL_TRUTH`
- wrapper winner never mints effect authority
- unknown remains first-class
- exact trace identity is required
- ambiguity fails closed
- top alternatives remain visible as Hyperposition instead of being collapsed into truth
- HyperMirror may compare intended control with observable output, but cannot inspect hidden chain-of-thought or the OpenAI scheduler
- SQLite runtime state MUST NOT be merged through Git

Wrapper-local cells (not claimed as canonical EntityOS GRID10 roles):

- G1 EVIDENCE
- G2 CAUSALITY
- G3 AUTHORITY
- G4 CONTINUITY
- G5 FALSIFIER
- G6 HYPERPOSITION
- G7 EFFECT_SAFETY
- G8 RESOURCE
- G9 INTEGRATION
- G10 HYPERMIRROR

Per-turn protocol:

1. PRE: admit user prompt as typed entry.
2. Read recurrent cell states.
3. Compute ten proposals/signals and scores.
4. Deterministically select exactly one winner or fail closed on a true tie.
5. Mint a broadcast identity and preserve the top alternatives.
6. Use the winner as a control/checking focus, never as truth.
7. Draft the answer.
8. POST: HyperMirror reads the actual emitted draft/output observables.
9. Measure uptake/mismatch without pretending to know hidden reasoning.
10. Update recurrent states and persist a trace for next-turn reentry.

Durable-reentry policy:

- executable code and contracts may live on this sandbox branch;
- per-turn receipts/checkpoints may be append-only JSON;
- live SQLite stays local;
- a new ChatGPT session may reconstruct the wrapper state from the latest admitted checkpoint, but must refresh current repository authority first;
- this experiment does not change Clay/HCU/GRID10 promotion credit.

Initial sandbox run on 2026-09-12: selftest PASS (competition, broadcast, POST closure, SQLite integrity, ablation, reentry). First real PRE for the owner's request to become more Frankenstein-like selected G9/INTEGRATION; G10/HYPERMIRROR and G2/CAUSALITY were the next alternatives. HyperMirror POST measured wrapper-local uptake=1.0 and mismatch=0.0; those metrics are control-plane observables, not truth evidence.

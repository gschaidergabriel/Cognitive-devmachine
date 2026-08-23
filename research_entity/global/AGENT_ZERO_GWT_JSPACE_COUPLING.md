# AGENT ZERO — GWT / J-SPACE COUPLING

Status: CURRENT CONCEPT
Owner direction date: 2026-08-23
Related concept: `research_entity/global/MINI_ENTITY_JSPACE_GWT_INSTRUMENTED_COGNITION.md`
Current program authority: `research_entity/global/MINI_ENTITY_CLAYCOG_APPROX1B_TRAINING_DIRECTIVE.md`

## Identity / naming law

In this concept, **Agent Zero / Zero** means the project role currently backed by Claude Code as the high-capability external cognition/execution surface. It does **not** mean the unrelated public `agent0ai/agent-zero` framework unless a later explicit owner directive says so.

Zero is not the persistent entity, truth authority, effect authority, or durable memory authority. MiniUnifiedDB and deterministic admission/effect/state gates remain authoritative.

## Core decision

The GWT/J-space work is not an optional visualization add-on. It becomes a **mandatory cognition-control and observation layer in front of Agent Zero**.

The target architecture is:

```text
human / environment cue
        |
        v
Mini Entity evidence + retrieval + ClayCode/GRF state
        |
        v
open-weight local cognition substrate
        |
        v
Jacobian Lens / measured J-space
        |
        v
bounded GWT selector / workspace slots
        |
        v
ZERO WORKSPACE CAPSULE
        |
        v
managed Zero turn admission (hooks / context / MCP boundary)
        |
        v
Agent Zero / Claude Code
        |
        v
output / proposed actions
        |
        v
deterministic validation + truth/effect/state gates
        |
        v
MiniUnifiedDB + causal feedback into next workspace
```

The architecture therefore fuses **local mechanistic cognition** with **Zero's frontier cognition** without falsely claiming access to Claude's hidden activations.

## Critical implementation boundary

Anthropic's Jacobian Lens reference implementation operates on open-weight decoder transformers whose residual-stream activations and gradients are available. The current Claude Code runtime does not expose Claude's internal residual stream, Jacobians, model weights, or a PyTorch forward pass to this system.

Therefore two different modes MUST be distinguished.

### Mode A — current realizable architecture: workspace-bound Zero

The local open-weight cognition model is the directly instrumented J-space/GWT substrate.

Zero is causally coupled through a mandatory, typed workspace capsule delivered by managed turn admission. The capsule may steer Zero through admitted context, instructions, tool/MCP state, candidate hypotheses, contradiction flags and bounded control metadata.

This makes the **execution path** workspace-bound, but it does not make Claude's hidden neural computation geometrically identical to the local J-space.

### Mode B — future full latent fusion: hookable Zero backend

If Zero is later backed by an admitted open-weight model with activation access, the GWT selector MAY attach directly to that model's residual stream and MAY perform bounded in-model ablation/steering under the intervention gates defined in the Mini Entity J-space concept.

Only in this mode is it technically meaningful to speak of direct geometric steering inside Zero's own forward pass.

Required law:

`ZERO_WORKSPACE_BOUND != CLAUDE_HIDDEN_STATE_BOUND`

`FULL_LATENT_FUSION_REQUIRES_HOOKABLE_MODEL`

## Zero Workspace Capsule

Every admitted instrumented Zero turn SHOULD receive one canonical workspace capsule bound to the current generation and turn identity.

Minimum fields:

- `workspace_id`;
- `turn_id` / causal id where available;
- entity generation;
- source local-model/checkpoint digest;
- Jacobian-Lens digest;
- selected GWT slots;
- per-slot measured strength/rank and persistence;
- explicit ClayCode/GRF correspondence if any;
- contradiction / uncertainty flags;
- provenance references to canonical evidence;
- requested Zero role for the turn: investigate, discriminate, repair, execute-plan, summarize, or abstain;
- capsule schema/version/digest.

The capsule is typed guidance, not canonical truth.

Required law:

`WORKSPACE_SLOT != FACT`

`WORKSPACE_STABILITY != EPISTEMIC_TRUTH`

`ZERO_ACCEPTANCE != EVIDENCE`

## Mandatory turn-binding rule

When the GWT/J-space mode is enabled, Agent Zero must not silently run on an unrelated path.

A managed Zero turn MUST either:

1. carry a fresh workspace capsule bound to the current generation/turn; or
2. carry an explicit typed reason why no J-space workspace is available, such as `JSPACE_UNAVAILABLE`, `LENS_UNFITTED`, `MODEL_BACKEND_NONHOOKABLE`, or `WORKSPACE_ABSTAINED`.

Silent bypass is forbidden.

This rule closes the architectural bypass at the **system boundary** even though Claude's internal neural state remains inaccessible.

## Re-evaluation of the six historical defects

The GWT/J-space coupling is adopted specifically because it creates stronger mechanisms against the previously observed workspace failures. The claims below are deliberately separated into structural guarantees and hypotheses.

### Defect 1 / 3 — fake bottleneck / truncated workspace

**Structural improvement:** the local GWT selector can implement a true bounded selection over measured latent candidates rather than merely truncating text fragments. Slot count, admission and competition become explicit machine-state.

**Not yet guaranteed:** the selected slots are not automatically the globally best semantic concepts, and the Zero capsule still has a finite serialized representation. The selector must be benchmarked against simpler retrieval/text baselines.

### Defect 2 — Zero bypasses the workspace

**Structural guarantee at system level:** managed turn admission can fail closed when enabled GWT/J-space mode lacks a current workspace receipt/capsule. Zero can therefore be prevented from bypassing the workspace *protocol*.

**Not a current neural guarantee:** Claude's private internal computation cannot be forced through our local J-space. Direct activation-level binding is reserved for Mode B with a hookable Zero backend.

### Defect 5 — prompt echo displaces solution state

**Research hypothesis:** a Jacobian-derived workspace may separate task-relevant latent concepts from superficial lexical recurrence better than BM25/full-text selection.

This must be tested. Question-vs-answer echo is not mathematically impossible merely because J-space is used.

Required discriminator:

`lexical_echo_baseline` vs `embedding/retrieval_baseline` vs `JSPACE_GWT`

on matched tasks with measured solution quality, workspace contamination and downstream Zero utility.

### Defect 6 — live chat without workspace

**Structural guarantee at system level:** the canonical Zero turn hook can require a workspace capsule or explicit unavailable/abstain receipt before Zero execution when this mode is active.

This unifies the live turn path with the workspace protocol. It does not imply a shared neural forward pass between the local model and Claude.

## From text context to geometric control

The long-term objective remains a shift from "retrieve text and hope the model uses it" toward "measure a compact latent workspace and causally test which directions matter."

For the current Claude-backed Zero this becomes a two-stage control law:

```text
canonical evidence
-> local open-weight latent cognition
-> measured J-space
-> GWT slot selection
-> typed workspace capsule
-> Zero context/tool/action steering
```

For a future hookable Zero backend it may become:

```text
canonical evidence
-> Zero hidden activations
-> J-space / GWT competition
-> bounded activation intervention
-> continued Zero forward pass
```

The second path must never be claimed before it exists and is measured.

## Causal loop

The target causal cycle is:

```text
OBSERVE
-> local latent workspace measurement
-> SELECT
-> broadcast bounded workspace to Zero
-> Zero proposes reasoning/action
-> deterministic gate
-> external/benchmark outcome
-> causal feedback
-> compare explicit trace, J-space trace and behavior
-> update only admitted retrieval/training policy
```

Zero's answer itself is not the reward. Verified task outcomes, explicit corrections, deterministic tests and admitted external evidence dominate learning.

## "Never guess" / epistemic calibration

The J-space does not directly reveal a scalar called epistemic confidence. Therefore the system MUST NOT equate a strong readout with truth confidence.

It MAY measure proxy variables such as:

- workspace stability across layers/positions;
- sensitivity to prompt perturbations;
- contradiction between explicit ClayCode and latent readout;
- causal influence under ablation/steering;
- evidence coverage/provenance supplied by MiniUnifiedDB;
- output variance across controlled reruns;
- agreement with deterministic or externally verified outcomes.

A calibrated abstention policy may combine these signals.

Required law:

`JSPACE_SALIENCE != EPISTEMIC_CONFIDENCE`

`CAUSAL_INFLUENCE != FACTUAL_CORRECTNESS`

## Early abort / cost gate

The system MAY avoid an expensive Zero call when the local workspace fails an explicitly calibrated admission test, for example:

- no stable task-relevant slots;
- unresolved contradiction above threshold;
- missing canonical evidence required by policy;
- malformed/stale lens or generation identity;
- high workspace entropy under a validated threshold;
- a deterministic gate already proves the task impossible or unauthorized.

The resulting state must be typed, e.g. `ABSTAINED_BEFORE_ZERO`, with the exact reason recorded.

High entropy alone is not proof that the model is guessing. Abort thresholds require held-out calibration against downstream task utility and false-abstention cost.

## Steering and collapse protection

Direct vector steering is permitted only on a hookable local/open-weight cognition substrate and only in explicit research/evaluation mode.

The steering coefficient `alpha` is never a fixed architectural constant. It must be swept around zero and bounded by measured collapse criteria.

Mandatory collapse metrics SHOULD include:

- grammar/parse validity;
- ClayCode type/schema validity;
- repetition/loop rate;
- output entropy/degeneration;
- task performance;
- contradiction rate;
- hidden-state/readout divergence where measurable;
- recovery after intervention removal.

A formal intervention gate MUST fail closed when coherence or schema validity leaves the admitted operating region.

Zero/Claude Code cannot currently receive hidden-state vector steering from this mechanism. For Claude-backed Zero, steering is restricted to admitted external surfaces such as typed context, hooks and MCP/tool state.

## Dashboard consequence

The live cognition view should show three separate surfaces rather than pretending they are one:

1. **Canonical evidence/state** — MiniUnifiedDB and deterministic state;
2. **Measured local latent workspace** — Jacobian Lens + GWT slots;
3. **Zero observable behavior** — supplied workspace capsule, tool/action proposals, outputs and verified outcomes.

Edges between them are causal/provenance hypotheses or measured relations, not identity.

A future hookable Zero backend may add a fourth surface for Zero's own measured latent workspace and then compare/fuse the two J-spaces experimentally.

## Promotion gates

This Agent Zero coupling becomes product-required only after evidence shows that it improves the real system rather than merely producing compelling visualizations.

Required comparison should include at least:

- Zero without workspace;
- existing text/retrieval workspace;
- local model + GWT without Jacobian Lens;
- J-space/GWT workspace-bound Zero;
- where available, a hookable open-weight Zero full-latent-fusion prototype.

Measure:

- task correctness;
- factual error / unsupported-claim rate;
- abstention calibration;
- workspace bypass rate;
- prompt-echo contamination;
- downstream Zero utility;
- latency and token/API cost;
- false abort rate;
- intervention dose-response;
- reproducibility across tasks/checkpoints;
- canonical truth/effect/state boundary violations.

No mechanism is promoted merely because the J-space visualization appears interpretable.

## Architectural conclusion

The central bet is retained in strong form:

**Agent Zero should no longer be an unconstrained text consumer sitting beside the workspace. It should become the downstream executor of a measured, bounded GWT/J-space workspace.**

But the implementation must preserve the technical distinction between:

- **real latent geometry we can measure and perturb** in the local open-weight cognition model; and
- **structured causal steering we can impose externally** on the current Claude-backed Zero.

This gives the system a realistic path from today's workspace-bound Claude Code to a future fully latent, geometrically coupled Zero without inventing access to internals that are not exposed.

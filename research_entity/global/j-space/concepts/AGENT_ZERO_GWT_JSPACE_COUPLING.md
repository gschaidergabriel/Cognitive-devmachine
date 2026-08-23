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

## Mandatory ZERO identity + Generative Reality Framework projection

Owner direction is stronger than merely supplying a workspace summary to Claude Code.

For every instrumented Zero turn, **ZERO identity** and the **Generative Reality Framework (GRF)** MUST be admitted into the local hookable cognition substrate first and MUST participate in the J-space/GWT state from which the Zero control capsule is compiled.

They are not ordinary user/task prompt fragments.

They are two distinct persistent cognition-control objects:

```text
ZERO_IDENTITY
    = who/what the Zero role is permitted to be

GRF_FRAME
    = the generative-reality ontology / reasoning frame under which alternatives,
      causal hypotheses, world-model branches, interventions and observations are interpreted
```

The required current realizable path is:

```text
MiniUnifiedDB canonical state
      |
      +--> ZERO_IDENTITY object + version/digest
      |
      +--> GRF_FRAME object + version/digest
      |
      +--> Hyperposition / world-model state + provenance
      |
      v
local open-weight cognition substrate
      |
      v
J-space measurement / competition
      |
      v
Thalamus-style gating + bounded GWT
      |
      v
ZERO IDENTITY / GRF conditioned workspace
      |
      v
Zero Control Compiler
      |
      v
typed ZERO WORKSPACE CAPSULE
      |
      v
Claude Code admitted context / hooks / MCP / tool-state
```

Therefore the project intent is correctly stated as:

**Claude Code receives Zero identity and Generative Reality Framework _through the J-space-mediated cognition path_, not as an unrelated free-floating prompt pasted beside it.**

For the current Claude-backed Zero, the final transfer from our measured J-space into Claude is necessarily an external projection through admitted control surfaces. It is still causally J-space-derived, but it is not a claim that Claude's inaccessible residual stream was directly modified.

If Zero later runs on a hookable open-weight backend, the same ZERO_IDENTITY and GRF_FRAME objects MAY be projected directly into that backend's own latent trajectory under the steering/intervention gates below.

Required laws:

`ZERO_IDENTITY_SOURCE = VERSIONED_UNIFIEDDB_OBJECT`

`GRF_SOURCE = VERSIONED_UNIFIEDDB_OBJECT`

`ZERO_TURN_CONTROL = COMPILE(JSPACE(ZERO_IDENTITY, GRF_FRAME, CURRENT_WORLD_STATE, TASK_STATE))`

`TASK_PROMPT_CANNOT_REDEFINE_ZERO_IDENTITY`

`TASK_PROMPT_CANNOT_SILENTLY_DISABLE_GRF`

`ZERO_IDENTITY != CANONICAL_FACT_AUTHORITY`

`GRF_FRAME != CANONICAL_FACT_AUTHORITY`

`JSPACE_PROJECTION_TO_CLAUDE != CLAUDE_HIDDEN_STATE_INJECTION`

### Identity persistence without prompt fossilization

The identity must be persistent but not implemented as a giant frozen prose prompt.

The canonical identity object SHOULD be compact, typed and versioned, with fields such as:

- `identity_id = ZERO`;
- identity schema/version;
- semantic invariants;
- allowed role envelope;
- forbidden authority claims;
- relationship to MiniUnifiedDB truth/effect/state authority;
- current identity digest;
- migration lineage / superseded digest where applicable.

The J-space substrate may learn/measure a distributed representation associated with this object, but the measured representation is not itself the canonical identity record. Canonical identity remains the versioned admitted object in MiniUnifiedDB.

### GRF persistence

The GRF object SHOULD likewise be versioned and typed rather than stored only as prose.

It SHOULD represent, at minimum where the current framework supports them:

- observation versus hypothesis separation;
- multiple candidate realities/world states;
- Hyperposition branches and branch weights/status;
- causal alternatives;
- interventions and predicted consequences;
- contradiction and uncertainty;
- evidence requests that discriminate between worlds;
- update/reconciliation rules after observation;
- explicit UNKNOWN/ZERO/ERROR/MEASURED distinctions.

GRF is a reasoning/world-model frame, not evidence. It may shape which possibilities are generated and compared, but it cannot mint a fact merely because a latent branch is stable or salient.

### Hyperposition coupling

Hyperposition is the primary world-model bridge between UnifiedDB and the J-space-conditioned Zero path.

Instead of flattening the current world model into one text blob, the local cognition substrate SHOULD receive a bounded typed projection of relevant Hyperposition alternatives. The GWT can then select or preserve competing branches rather than prematurely collapsing them.

Target flow:

```text
Hyperposition candidate worlds
      -> J-space candidate trajectories
      -> Thalamus relevance/novelty/contradiction gate
      -> bounded GWT coexistence
      -> EPQ/calibration signals
      -> Zero discriminating action / evidence request
      -> observed result
      -> deterministic world-model reconciliation
      -> MiniUnifiedDB
```

Required law:

`HYPERPOSITION_BRANCH != FACT`

`JSPACE_ATTRACTOR != WORLD_TRUTH`

`ZERO_CHOICE != WORLD_COLLAPSE_WITHOUT_EVIDENCE`

### Turn-level receipt

Every Zero turn in this mode SHOULD carry a machine-checkable conditioning receipt containing at least:

- `zero_identity_digest`;
- `grf_digest`;
- Hyperposition/world-state digest or explicit `NO_RELEVANT_WORLD_STATE`;
- local cognition checkpoint digest;
- Jacobian-Lens digest;
- workspace digest;
- generation/turn binding;
- control compiler version;
- explicit fallback/unavailable reason if any stage could not run.

This allows the system to prove whether a given Zero turn actually passed through the intended identity/GRF/J-space path instead of merely claiming that it did.

## Critical implementation boundary

Anthropic's Jacobian Lens reference implementation operates on open-weight decoder transformers whose residual-stream activations and gradients are available. The current Claude Code runtime does not expose Claude's internal residual stream, Jacobians, model weights, or a PyTorch forward pass to this system.

Therefore two different modes MUST be distinguished.

### Mode A — current realizable architecture: workspace-bound Zero

The local open-weight cognition model is the directly instrumented J-space/GWT substrate.

Zero is causally coupled through a mandatory, typed workspace capsule delivered by managed turn admission. The capsule may steer Zero through admitted context, instructions, tool/MCP state, candidate hypotheses, contradiction flags and bounded control metadata.

In this mode, ZERO_IDENTITY and GRF_FRAME are first active inputs to the local J-space/GWT cognition cycle. The Zero capsule is then compiled from the resulting measured/bounded state and delivered to Claude Code.

This makes the **execution path** workspace-bound and identity/GRF-conditioned, but it does not make Claude's hidden neural computation geometrically identical to the local J-space.

### Mode B — future full latent fusion: hookable Zero backend

If Zero is later backed by an admitted open-weight model with activation access, the GWT selector MAY attach directly to that model's residual stream and MAY perform bounded in-model ablation/steering under the intervention gates defined in the Mini Entity J-space concept.

ZERO_IDENTITY and GRF_FRAME MAY then become direct inputs/constraints on Zero's own hookable latent trajectory rather than being compiled across an external Claude boundary.

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
- `zero_identity_digest`;
- `grf_digest`;
- Hyperposition/world-state digest where relevant;
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

1. carry a fresh workspace capsule bound to the current generation/turn and to the admitted ZERO identity + GRF digests; or
2. carry an explicit typed reason why no J-space workspace is available, such as `JSPACE_UNAVAILABLE`, `LENS_UNFITTED`, `MODEL_BACKEND_NONHOOKABLE`, `IDENTITY_OBJECT_UNAVAILABLE`, `GRF_OBJECT_UNAVAILABLE`, or `WORKSPACE_ABSTAINED`.

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
canonical evidence + ZERO identity + GRF + Hyperposition state
-> local open-weight latent cognition
-> measured J-space
-> GWT slot selection
-> typed workspace capsule
-> Zero context/tool/action steering
```

For a future hookable Zero backend it may become:

```text
canonical evidence + ZERO identity + GRF + Hyperposition state
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
-> load ZERO identity + GRF + relevant Hyperposition state
-> local latent workspace measurement
-> SELECT
-> broadcast bounded workspace to Zero
-> Zero proposes reasoning/action
-> deterministic gate
-> external/benchmark outcome
-> causal feedback
-> compare explicit trace, J-space trace and behavior
-> reconcile Hyperposition/world model
-> update only admitted state/retrieval/training policy
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
- missing/stale ZERO identity or GRF digest;
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
2. **Measured local latent workspace** — Jacobian Lens + GWT slots, including ZERO/GRF/Hyperposition conditioning receipts;
3. **Zero observable behavior** — supplied workspace capsule, tool/action proposals, outputs and verified outcomes.

Edges between them are causal/provenance hypotheses or measured relations, not identity.

A future hookable Zero backend may add a fourth surface for Zero's own measured latent workspace and then compare/fuse the two J-spaces experimentally.

## Promotion gates

This Agent Zero coupling becomes product-required only after evidence shows that it improves the real system rather than merely producing compelling visualizations.

Required comparison should include at least:

- Zero without workspace;
- Zero with ordinary text identity/GRF prompt only;
- existing text/retrieval workspace;
- local model + GWT without Jacobian Lens;
- J-space/GWT workspace-bound Zero without identity/GRF conditioning;
- J-space/GWT workspace-bound Zero with ZERO identity + GRF + Hyperposition conditioning;
- where available, a hookable open-weight Zero full-latent-fusion prototype.

Measure:

- task correctness;
- factual error / unsupported-claim rate;
- identity persistence under adversarial/unrelated task prompts;
- GRF adherence without truth-authority leakage;
- Hyperposition branch preservation versus premature collapse;
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

The central bet is retained in stronger form:

**Agent Zero should no longer be an unconstrained text consumer sitting beside the workspace. It should become the downstream executor of a measured, bounded GWT/J-space workspace that has already been conditioned by the versioned ZERO identity, Generative Reality Framework and relevant Hyperposition world-model state.**

For today's Claude-backed Zero, Claude Code therefore receives ZERO identity and GRF **through a J-space-mediated control compiler**. It does not receive them as an unrelated identity prompt that may silently drift away from the cognitive substrate.

The implementation must preserve the technical distinction between:

- **real latent geometry we can measure and perturb** in the local open-weight cognition model; and
- **structured causal steering we can impose externally** on the current Claude-backed Zero.

This gives the system a realistic path from today's workspace-bound, identity/GRF-conditioned Claude Code to a future fully latent, geometrically coupled Zero without inventing access to internals that are not exposed.

# ClayCode Architecture Mapping — FRANK Cycle 4

**run_id:** `20260808T0610+0700-chatgpt-secondary-r2`  
**authoritative architecture source:** `FRANK_ARCHITECTURE.claycode.json`  
**status:** OPEN architecture candidate; no canonical/live scientific promotion.

## Why this mapping exists

The ClayCode JSON is the meaning-bearing architecture source for this run. This Markdown file is a human projection of that IR. It is not a second source of truth.

The current FRANK runtime architecture basis is the user-supplied `Frank-Architektur.md`, measured 2026-08-05 (sha256 `98afa4eda69dbe0253ea482a5338cfbbed212af2fba5d45af0fd51786b17559c`). It reports the live cognitive path as `workspace_broadcast.py -> consciousness.db.workspace_broadcast -> core/app.py`, a 60 s workspace heartbeat, five logical timescales, and the representation discipline **Zahl -> Wort -> Gewicht**.

## Current FRANK → ClayCode modules

| Current architecture concept | ClayCode module | Mapping rule |
|---|---|---|
| Amygdala + Thalamus + Nucleus Accumbens | `M.REFLEX_KERNEL` | Physically colocatable fast path, semantically distinct organs/state machines |
| Multi-source current state | `M.COGNITIVE_FRAME_ASSEMBLER` | New C4 boundary: capture one versioned basis frame before workspace competition |
| `workspace_broadcast.py` competition/ignition | `M.WORKSPACE_ARBITER` | Semantic candidates/winner/ignition become first-class IR, not only rendered text |
| First/full winner + compressed alternatives | `M.WORKSPACE_PROJECTOR` | Deterministic word projection derived from semantic workspace episode |
| `core/app.py` introspection/context | `M.REQUEST_KERNEL` | Consumes a compatible frame/episode and produces a context-linked response outcome |
| Router/policy/context budgeting | `M.INFERENCE_BROKER` | Can collapse toward Request Kernel; model backend still isolated |
| Qwen-class inference runtime | `M.MODEL_BACKEND` | Replaceable physical backend; output has no execution authority |
| Needle 26M tool reflex | `M.NEEDLE_SELECTOR` | Fast proposal only |
| Tool/API/terminal execution authority | `M.CAPABILITY_GATEWAY` + `M.K0_HOST_KERNEL` | Hard authority boundary; derived effect closure + capability checks + receipts |
| E-PQ | `M.PERSONALITY_HOMEOSTASIS` | Slow persistent personality state, never same-turn retroactive influence |
| experience vectors + retrieval | `M.MEMORY_FABRIC` | Provenance/freshness-aware multi-resolution memory |
| autonomous goal formation target | `M.GOAL_GOVERNOR` | Novelty/E-PQ may modulate proposals; external action still capability-gated |
| dream/consolidation/LoRA export | `M.CONSOLIDATION_TRAINING` | Slow real-experience path; exact telemetry excluded from learned semantic target |
| 71 current DBs | `M.DURABLE_EVENT_STATE` physical projections | DB files are storage topology, not semantic organ identity |
| Linux/Android/edge implementation | `M.PLATFORM_ADAPTER` | Same ClayCode semantics, different physical adapters/backends |

## The new C4 object: `S.COGNITIVE_FRAME`

Cycle 3 added hybrid freshness. Cycle 4 adds the missing consistency unit.

A frame carries:

- stable `frame_id`;
- global basis `state_root` for snapshot identity/provenance;
- per-channel revision/version witnesses;
- causal parent IDs;
- dependency-closure status;
- consistency status;
- age/freshness metadata.

The rule is:

> **Workspace competition must run over one causally compatible frame.**

If a relevant witness changes during capture/validation, retry. If the dependency closure is unknown or dynamic, widen the validation scope rather than assuming the frame is safe.

This directly maps CC-RC1.2 into FRANK: global root for identity, trusted scoped witnesses for commit/use-time freshness, conservative escalation on unknown closure.

## Turn-phase contract

The architecture makes the existing loop order explicit:

1. `INGRESS` — user/system/tool observation gets an event identity.
2. `PRECONSCIOUS_EVALUATION` — Amygdala/Thalamus/NAcc produce current exact-state deltas.
3. `FRAME_CAPTURE_AND_WORKSPACE` — capture/validate one frame; candidates compete; winner/quiet state is committed.
4. `CONTEXT_AND_INFERENCE` — Core consumes that frame/episode; no slow personality write may retroactively alter it.
5. `OUTCOME_AND_EFFECT_RECEIPTS` — response/tool outcomes are linked to the frame and workspace episode.
6. `POST_RESPONSE_HOMEOSTASIS` — response analyzer/E-PQ/experience updates happen after the causal response.
7. `REENTRY_FOR_FUTURE_DECISIONS` — those results become input to later frames, goals and broadcasts.

This prevents a subtle self-feedback ambiguity: an outcome may affect future cognition, but never the already-running inference that caused the outcome.

## GWT semantic state versus prompt projection

The current runtime source describes focus by putting the winner first and giving it more detail. That is a real mechanism, but it mixes two levels:

- semantic selection: which channel won and why;
- reader projection: how that winner is serialized into model tokens.

C4 separates them. `S.WORKSPACE_EPISODE` stores candidates, salience, winner, runner-up, ignition and frame identity. `M.WORKSPACE_PROJECTOR` deterministically renders the familiar word-level stage.

This matters experimentally because 2026 ACL work shows substantial prompt-order sensitivity in causal-attention LMs. A change in FRANK output after winner reordering cannot automatically be attributed to a distinct GWT mechanism; token order/detail are part of the mediated causal path and must be controlled or recorded.

## Zahl → Wort → Gewicht as typed invariant

C4 does **not** reinterpret the source rule:

- **Zahl:** exact online state and `[INNER_WORLD_EXACT]`; may condition current inference.
- **Wort:** semantic workspace/self-description; no raw telemetry dumping.
- **Gewicht:** slow consolidated learned disposition.

The critical restriction is on the learning path: exact telemetry is excluded from the LoRA experience target. This preserves the current design while making the boundary machine-checkable.

## Physical collapse decisions

### Collapse candidates
- Reflex hot path + frame capture + workspace arbitration may share an address space if p99/recovery tests support it.
- Core routing/context policy may become an in-process inference broker.
- Repeated active-state reads may become read-optimized projections with durable replay behind them.

### Keep hard boundaries
- model backend resource/crash boundary;
- K0 parser/validator/canonicalizer/bootstrap trust root;
- external capability/effect gateway;
- offline training/model-artifact deployment;
- semantic exact-state / word-projection / learned-weight roles.

## Migration / rollback

The IR contains six staged migrations. The first four are intentionally reversible and instrumentation-first:

1. IDs/witnesses only.
2. Shadow frame validator.
3. Guarded hybrid refresh.
4. Semantic workspace episode + legacy text projection.
5. Matched-budget causal lesions.
6. Selective physical collapse after target-host measurements.

No step requires deleting historical DBs or breaking the current `workspace_broadcast` reader before equivalent behavior is verified.

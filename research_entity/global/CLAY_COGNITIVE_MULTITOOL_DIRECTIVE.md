# CLAY COGNITIVE MULTITOOL — OWNER DIRECTIVE

Status: CURRENT
Owner directive date: 2026-08-22

## Core product
Build one application-neutral Cognitive Multitool for EntityOS. The multitool exposes one stable cognitive contract while the inference backend is replaceable.

Primary neural accelerator: `Qwen/Qwen2.5-0.5B-Instruct`, fine-tuned for ClayCog/ClayCode-only cognition, GRF, Hyperposition, epistemic invariants and state transition control.

The 0.5B backend is OPTIONAL. It MUST be possible to disable it and bind the original dual-Mistral arrangement or another backend without changing the Cognitive Multitool contract or canonical state format.

## Cognitive HAL contract
EntityOS talks to the Cognitive Multitool, not directly to a specific model.

Required cognitive modes include at minimum:
- `GWT`: candidate competition, salience/conflict/novelty/goal relevance and broadcast proposal;
- `PULSE`: database/state deltas, open goals and unresolved hypotheses;
- `PRESTAGE`: structured task/tool/context preparation;
- `HYPERPOSITION`: preserve multiple causal alternatives until sufficient discriminator/evidence;
- `ROUTER`: memory/tool/backend/escalation routing;
- `CRITIC`: inspect candidate outputs against epistemic and structural invariants;
- `POSTGATE`: convert candidate output into a gated cognitive result for deterministic validation;
- `SELF`: computed semantic control-state update;
- `ESCALATE`: decide whether a stronger backend is required.

A backend returns a standardized result containing only cognition/proposal fields such as next-state proposal, candidates, broadcast proposal, Hyperposition state, uncertainty, requested memory/tools, escalation and evidence references. Canonical truth/effect authority remains external.

## Hot-swappable capsule
The model weights contain universal cognition only. Runtime identity and task semantics live in a hot-swappable capsule:

`system_prompt`, `entity_id`, `role`, `goal`, `persona`, `db_binding`, `memory_namespace`, `tool_policy`, `workspace_state`, `grf_state`, `hyperposition_state`.

System prompt and database binding MUST be hot-swappable without retraining and, where the runtime supports it, without reloading model weights.

The same loaded kernel may serve tasks sequentially through atomic bind/infer/unbind cycles. Multiple concurrent cognitive slots are allowed when the inference runtime supports independent sequence/KV state. Each slot MUST have isolated capsule, DB binding and state.

## Context isolation
No task, identity, persona, secret state or DB content from capsule A may leak into capsule B after unbind unless explicitly transferred through canonical external state.

Training/evaluation MUST include A->unbind->B cross-context isolation tests and adversarial fixed-identity attempts.

## Backend modes
Required routing modes:
- `local_0_5b`: one resident ClayCog 0.5B kernel;
- `mistral_dual`: original two-Mistral cognitive path;
- `auto`: local kernel for cheap continuous cognition, with escalation to Mistral/frontier backend on uncertainty, conflict, capability or policy triggers.

Per-cognitive-mode backend assignment is allowed. Example: GWT/PULSE/PRESTAGE on 0.5B, CRITIC/DEEP_REASON on Mistral or frontier model.

## Deterministic correctness boundary
Neural backends propose and organize cognition; they do not become canonical authority. ClayCode compiler/type/invariant gates and canonical persistence remain deterministic and fail closed.

`UNKNOWN != ZERO != ERROR != MEASURED` remains mandatory.

## Observable self-healing and stable-state recovery
The Cognitive Multitool MUST be self-healing but MUST NEVER fail or recover silently.

A deterministic supervisor outside the neural backend owns health, checkpoints, rollback and effect reconciliation. Neural backends may diagnose/propose recovery cognition but cannot certify their own recovery.

Every slot/backend uses explicit health states such as `HEALTHY`, `DEGRADED`, `RECOVERING`, and `QUARANTINED`.

On crash, timeout, malformed cognition, invariant failure, stale generation/CAS conflict, DB-binding mismatch or repeated backend failure, the affected slot MUST:
- stop new external effects;
- persist an incident/failure event with reproducible diagnostic hashes/metadata and redacted secrets;
- restore only from the newest independently verified stable checkpoint;
- recreate fresh sequence/KV state rather than treating crashed hidden state as continuity authority;
- reconcile canonical DB generation before resuming;
- never blindly replay an effect whose terminal receipt is absent or ambiguous;
- preserve `UNKNOWN` for unresolved effect outcomes;
- produce a durable recovery receipt before returning to `HEALTHY`;
- expose the incident and recovery in operational telemetry/UI;
- trip a bounded retry/circuit breaker and quarantine or route to an admitted alternate backend such as `mistral_dual` if the same fault repeats.

Recovery MUST be slot-local unless a shared canonical database proves a transaction-level recovery requirement. One crashing cognitive task must not roll back unrelated tasks.

Stable checkpoints bind generation/episode, capsule and system-prompt hashes, DB binding/generation, backend/model/config digest, canonical cognitive-state hash, evidence/provenance refs, committed effect receipts and invariant/schema version.

Full recovery contract: `research_entity/global/COGNITIVE_MULTITOOL_SELF_HEALING_PROTOCOL_V0.md`.

## Training direction
Training data SHALL optimize the 0.5B model as a reusable cognitive accelerator for this HAL, not as a named Mini Entity.

Priority curriculum:
- state trajectories `R_t -> competition -> HP -> discriminator -> broadcast -> R_t+1`;
- stable-state and NOOP ticks;
- DB-delta pulses;
- memory/tool routing;
- escalation and de-escalation;
- critic/postgate passes over stronger-model outputs;
- context capsule rebinds;
- cross-capsule isolation;
- hot-swapped system prompts and DB bindings;
- sequential multitasking with identical weights;
- concurrent-slot isolation where supported;
- external truth/effect authority;
- crash after cognition before commit;
- crash after effect intent without terminal receipt;
- rollback to last verified stable state;
- current-DB-wins rebase instead of destructive rollback;
- repeated-crash circuit breaker/backend escalation;
- recovery telemetry and recovery-receipt discipline;
- recovery, receipts, CAS and no blind replay;
- adversarial fixed identity/persona/job requests.

## Mandatory `go` contract
Every exact `go` MUST produce measurable implementation progress on this Cognitive Multitool lane until a promoted kernel/module exists.

Each `go` MUST do at least one concrete artifact change or empirical test in BOTH categories:
1. TRAINING: generate/expand/validate/evaluate training data or fine-tune readiness/checkpoint behavior;
2. MODULE: implement/test the Cognitive Multitool runtime contract, capsule hot-swap, DB binding, backend router, scheduler/slots, deterministic gates, self-healing recovery or integration.

A `go` that only writes analysis or plans is insufficient unless blocked by a newly proven external constraint; that blocker must be persisted with evidence.

The preferred progression is:
`refresh -> training corpus/trajectory expansion -> strict validation -> multitool module implementation -> hot-swap/isolation tests -> crash/recovery/checkpoint tests -> backend substitution tests (0.5B off => dual Mistral) -> Together admission/price/job -> base-vs-tuned eval -> hidden-state probes -> Q4_K_M -> <1GiB RSS -> EntityOS integration -> evidence persistence`.

## Budget
Together use remains bounded to the owner-authorized ClayCog 0.5B training campaign, maximum EUR 20 equivalent. No billed create before exact admission and price preflight.

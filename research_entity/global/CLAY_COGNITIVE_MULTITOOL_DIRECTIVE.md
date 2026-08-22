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
- recovery, receipts, CAS and no blind replay;
- adversarial fixed identity/persona/job requests.

## Mandatory `go` contract
Every exact `go` MUST produce measurable implementation progress on this Cognitive Multitool lane until a promoted kernel/module exists.

Each `go` MUST do at least one concrete artifact change or empirical test in BOTH categories:
1. TRAINING: generate/expand/validate/evaluate training data or fine-tune readiness/checkpoint behavior;
2. MODULE: implement/test the Cognitive Multitool runtime contract, capsule hot-swap, DB binding, backend router, scheduler/slots, deterministic gates or integration.

A `go` that only writes analysis or plans is insufficient unless blocked by a newly proven external constraint; that blocker must be persisted with evidence.

The preferred progression is:
`refresh -> training corpus/trajectory expansion -> strict validation -> multitool module implementation -> hot-swap/isolation tests -> backend substitution tests (0.5B off => dual Mistral) -> Together admission/price/job -> base-vs-tuned eval -> hidden-state probes -> Q4_K_M -> <1GiB RSS -> EntityOS integration -> evidence persistence`.

## Budget
Together use remains bounded to the owner-authorized ClayCog 0.5B training campaign, maximum EUR 20 equivalent. No billed create before exact admission and price preflight.

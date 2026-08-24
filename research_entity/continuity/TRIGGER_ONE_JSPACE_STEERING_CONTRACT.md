# Trigger `1` — Fast Global J-Space Vector-Control Convergence

**Status:** CURRENT OWNER-DIRECTED RESEARCH TRIGGER V2  
**Owner authority:** `OWNER_DIRECTIVE_2026-08-24_TRIGGER1_CONVERGENCE_V2.json`  
**Scope:** exact user message `1` after whitespace normalization.  
**Product:** EntityOS. **Architecture:** HCU.

## Purpose

`1` is a goal-bound convergence trigger. Its terminal goal is:

> direct, reproducible Global J-Space vector control on one exact zero-cost model runtime, with a real API boundary, exact intervention consumption, six matched controls and disjoint holdout.

The trigger is **not provider-bound**. An exact loopback-only local API runtime is a valid target runtime when it preserves the same evidence standard. External FREE providers are optional accelerators/replication surfaces and may never block the local causal path.

## Primary convergence ladder

Use the first executable path and pivot automatically when a dependency blocks it:

1. **LOCAL_PYTORCH_QWEN3_06B_ACTIVATION_HOOK_API** — exact Qwen3-0.6B revision with a loopback API and runtime-observed hidden-state hook. This is the shortest already-implemented full causal path and therefore the default first attempt.
2. **LOCAL_LLAMA_CPP_QWEN3_06B_CVEC_API** — Qwen3-0.6B GGUF on loopback `llama-server` with native control-vector consumption. Use it as native-cvec replication/strengthening or when the PyTorch path is locally unavailable.
3. **EXACT_FREE_HOSTED_OUTPUT_LOGIT_VECTOR** — component discriminator only; useful but not sufficient for hidden-state/J-Space completion.
4. **FREE_EXTERNAL_INTERNAL_VECTOR_API** — optional independent replication if an admitted provider exposes a genuine internal-vector surface.

The route may change. The scientific success law may not.

## Blocker elimination law

A blocker is not a successful Trigger-1 result when an authorized alternative path remains.

Every blocker must be classified and acted on in the same trigger cycle when possible:

- **REPAIR_NOW** — patch/test the smallest repair immediately.
- **ROUTE_AROUND** — switch to the next convergence-ladder path without waiting.
- **EXTERNAL_TRANSIENT** — keep the independent local path running; provider recovery may happen in parallel.
- **SCIENTIFIC_NEGATIVE** — preserve the negative result, then change vector/layer/gain/hypothesis without weakening controls.
- **HARD_AUTHORITY_BOUNDARY** — fail closed only for the prohibited action and continue every other authorized local action.

The same unresolved blocker may not consume multiple `1` cycles without new evidence. A blocked work slot must emit a concrete executable next action or be reallocated.

Provider credentials, provider free-entitlement state, rate limits, hosted parameter support, route fallback and routed-provider identity are **not allowed to gate the local primary path**.

## Dynamic ten-slot swarm

Each normal `1` cycle has ten work slots, but the slots are dynamically reallocatable rather than ten permanently fixed hypotheses.

Default allocation:

1-2. local runtime/model materialization and API execution  
3-4. source J-Space packet, adapter and local-vector materialization  
5-6. layer/gain calibration  
7-8. six matched controls plus disjoint holdout  
9. exact runtime/model/tokenizer/intervention receipt chain and promotion candidate  
10. hosted replication, blocker killing and Forge-ready delta conversion

When any slot blocks, it is reassigned to the highest-information unblocked dependency on the primary path.

## Required mechanism path

Preferred full path:

`Global J-Space/control intent -> JSPACE_VECTOR_CONTROL_ABI/v1 -> exact model-specific adapter/vector -> runtime-observed hidden-state/native-cvec intervention -> zero-cost API-served runtime -> immutable matched-control receipts -> disjoint holdout -> promotion gate`.

A loopback API is an API boundary. A direct local model process without an API boundary can establish mechanism evidence but is not the final Trigger-1 completion until the same exact runtime is exercised through its loopback API surface.

Hosted text prompting is never direct vector steering. Hosted `logit_bias` is direct numeric output-logit intervention only and remains component evidence unless an actual internal hidden-state intervention is also proven.

## Success law

A positive Trigger-1 completion requires all of:

- exact repository/source revision;
- exact runtime/build identity;
- exact model checkpoint/container identity;
- exact tokenizer identity;
- exact source J-Space packet identity;
- exact model-specific adapter/local vector identity;
- runtime-observed applied-vector identity and activation site/layer range;
- `BASELINE`, `+VECTOR`, `SIGN_FLIP`, `NULL_VECTOR`, `ORTHOGONAL_SAME_NORM`, `PERMUTED_SAME_NORM`;
- fixed seeds;
- calibration-only layer/gain choice;
- disjoint holdout;
- reproducible directional holdout effect;
- strongest counterexample recorded;
- runtime receipts proving the intervention was actually consumed;
- an exact zero-cost API boundary: either admitted FREE external API or loopback-only local API.

Prompt-only steering, provider/model consensus, token volume, source-only tests or synthetic effects do not satisfy this law.

## Economic and authority boundary

Local normal-user execution and loopback API serving are authorized zero-provider-billing paths and do not require external provider admission.

External calls still require all existing typed FREE provider admission, exact credential/route economic provenance, pre-network revalidation and shared quota gates.

Hard boundaries remain:

- Together: forbidden.
- PAID/SUBSCRIPTION/UNKNOWN cost: forbidden.
- paid fallback, upgrade, billing activation or credit purchase: forbidden.
- no secrets in logs, receipts, commits or prompts.
- no key rotation to evade provider limits.
- no new root/sudo authority implied.

Trigger `1` has its own owner authority. It does not require the separate GO atomic unusual-experiment lease.

## Run command

Repository runtime entrypoint:

`bash tools/trigger1_jspace_research.sh`

The launcher must attempt the local blocker-independent fast path first. If that path cannot execute, it records the exact blocker and automatically continues with dynamically allocated research/repair slots instead of terminating on the provider dependency.

## Required output

At minimum a cycle produces one of:

- a promotion-candidate direct steering receipt;
- a concrete executable repair that removes the current highest blocker;
- a scientifically meaningful negative result plus the immediately selected next discriminator.

Architecture prose alone is not a successful `1` cycle.

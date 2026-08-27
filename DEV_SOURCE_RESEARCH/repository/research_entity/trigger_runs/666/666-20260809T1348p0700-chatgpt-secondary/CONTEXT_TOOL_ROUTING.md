# Level-0 Shard — Project-Frankenstein Agentic Context / Tool Routing

## Scope

This shard recovers the Project-Frankenstein lineage for grounded action routing, context budgeting/versioning, plan recitation, scratch offload, goal-scoped tool exposure, persistent task state, lossy compaction and live execution traces. Safety/authority incidents already owned by existing PF safety receipts are not re-credited here.

## Chronology

### 2026-02-17 — action honesty becomes a routing invariant

Commit `40edcbb502718debd89c8d3275162fa627e1582d` records a concrete epistemic failure: a request to inspect Frank's own code went through ordinary chat, which had no file tools, and produced a convincing but nonexistent Titan timestamp bug. The fix routed self-analysis/code-inspection phrases into the agentic loop and explicitly prohibited pretending to read files or execute actions in chat mode.

This is directly reusable as an evidence-routing invariant: inspection/action claims require an observation/effect path and receipt; plausible language is not evidence.

### 2026-02-20 — context provenance, cumulative risk and bounded execution

Commit `165d7149fb0aa499bb2474c1b85fca3b1367ec8c` added:

- EMA-weighted failure scoring;
- compound multi-step risk `1 - Π(1-risk_i)` instead of max-step risk;
- auto-save on agent-state mutation;
- failed-attempt context versioning (`[FAILED_ATTEMPT_vN]`), with clean successful observations separated from compact failure summaries;
- a dynamic context budget tied to remaining steps;
- Firejail wrapping for bash/code when available.

The context-versioning concept is especially important for current RAE/FRANK architecture: negative results should stay alive and retrievable without poisoning the active evidence surface.

The Firejail path is only a historical mechanism. Its own code allowed execution to fall back unsandboxed if Firejail was absent, so it cannot be inherited as the modern authority guarantee.

### 2026-03-22 — Deep-Agents-style attention engineering

Commit `4995e08f2e1e5251ceeb41388c167bb6a629ada8` added four mechanisms:

1. `update_plan`: a local no-op tool that places the current plan back into recent context every few actions;
2. `scratch_write` / `scratch_read`: session-local key/value offload, with tool results over 1500 characters automatically moved out of active context and summarized;
3. goal-based tool filtering: classify a task as research/filesystem/code/system/analysis and show at most 15 relevant tools instead of all 44;
4. a fallback parser for old `<tool>name|args</tool>` LoRA syntax.

These are useful attention mechanisms, but their correct modern mapping is strict:

`attention surface != capability surface != execution authority`

Tool filtering can reduce confusion for a small model, yet hidden tools must still be unreachable unless deterministic capabilities permit them. A permissive parser may normalize syntax, but cannot be the authorization boundary.

### 2026-04-01 — long-context compaction, task ledger and observability

Commit `1c5c682aa84c13eadbf47fbc54e4219230ce5ee6` compacted older context when estimated tokens exceeded ~40K, retained the last three exchanges in full, persisted project tasks in `.tasks/`, added SSE live tool/result/text events and raised max agent iterations from 15 to 25.

The commit explicitly notes that API credits were insufficient for end-to-end live testing at that point, so the shard preserves the distinction between structural implementation and runtime validation.

## Architecture synthesis

The historical mechanisms suggest a stronger current pipeline:

`Needle/task router`
`-> small task-relevant cognitive tool surface`
`-> model proposes plan/action in typed ClayCode`
`-> deterministic schema + capability + budget validation`
`-> executor`
`-> immutable observation/effect/outcome receipt`
`-> active context may hold a compact derived summary`
`-> full evidence remains content-addressed and replayable`

Three invariants follow:

- `active_summary != durable_evidence`
- `plan_recitation != committed_state_transition`
- `tool_visibility != capability`

## Preserved negative results / constraints

- A no-tool chat route cannot truthfully claim code/filesystem inspection.
- Goal-scoped tool filtering is cognitive routing, not a security boundary.
- Summary-only lossy compaction is insufficient for replay/audit/contradiction recovery.
- A plan written back into context may stabilize attention but does not itself commit state or grant effects.
- Flexible fallback tool syntax requires deterministic validation before execution.
- Greater loop depth increases cumulative consequence/failure radius; cancellation, compound risk budgets and checkpoints are required.

## Branch feedback

- **FRANK:** make action honesty and receipt-linked observation claims explicit self/world-model invariants; retain cancellation and cumulative failure/risk accounting.
- **Harness:** benchmark dynamic budgets, plan checkpoints and goal-scoped tool surfaces, while enforcing capabilities independently. Test replay after aggressive compaction.
- **ClayCode:** plans/tool outputs are typed proposals. Parser normalization is not authority.
- **UnifiedDB:** retain complete tool/evidence objects, derived summaries, versioned failed-attempt branches, task states and effect/outcome receipts.
- **ClayGraph:** distinguish failed-attempt and successful-observation branches during activation/retrieval.
- **GWT:** task-relevant candidate/tool surfaces can shape competition inputs, but broadcast objects must retain provenance.
- **Emergenz:** long chains/plan recitation are not emergence evidence without causal lesion/rescue tests.
- **Hyperposition:** unresolved candidate actions/evidence can remain set-valued until validation commits one transition.
- **Clay:** semantic boundaries between attention shaping, evidence persistence and effect authority must survive physical module collapse.

## Project-Frankenstein history-denominator refinement

The previous verified lower-bound interval was 407 commits. A thematic history search exposed an earlier commit, `165d714...`, which raised the lower-bound interval to 429. A still earlier relevant commit, `40edcbb...` from 17 February, compares to frozen HEAD with `ahead_by = 487`, yielding a verified interval of **488 commits including the base**.

This is still not the full denominator. `40edcbb...` modifies already-existing files and is not proven to be the root commit; thematic commit search is not exhaustive parent traversal. Therefore:

- verified PF history interval lower bound: **>= 488 commits**;
- full root-to-head history denominator: **UNFROZEN**;
- recursive frozen tree denominator: **UNFROZEN**;
- exact L0 coverage credit: **0.0**.

## Promotion / earned work

No canonical scientific promotion and no new historical hours are credited here. Mechanisms remain mapping candidates pending row-level deduplication against current Harness, FRANK, Needle and UnifiedDB work.

Durable receipt: `research_entity/archive_assimilation/receipts/666_20260809T1400p0700_chatgpt_secondary_pf_agentic_context_tool_routing_lineage.json`.

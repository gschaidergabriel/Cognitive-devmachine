# TRIGGERWORT 4 — WorkExecution v2.1 + GWT Provenance + Hook Boundary + Source Closure Fusion

Status: CURRENT BUILD FUSION CONTRACT
Date: 2026-08-28
Primary donor pinned by the reconciled Triggerword-5 wave: `gschaidergabriel/frankenstein@5641dc6b2df6ebed1df246ee7533134324f6c427`

## 1. Purpose

This contract fuses the material non-duplicate results from the Triggerword-5 worker wave observed through the 2026-08-28 10:43Z design frontier. It intentionally does not reproduce every parallel packet. Intermediate packet-admission claims, stale canonical-main bindings and superseded interpretations remain historical evidence, not current build truth.

The four build-relevant deltas are:

1. `WorkExecutionBinding/v2.1`: durable workpackage -> exact native Agent invocation -> child identity can be designed without timing/order heuristics using the existing `HANDOFF <paket_id>` marker plus the documented Agent hook ABI.
2. Typed tool/child identity must be retained before GWT aggregation; donor `gw_absicht` currently collapses ownership to session + time window.
3. Donor Stop-hook model relevance judging is useful candidate evidence but currently occupies the deterministic Stop critical path; Frankenstein 2.0 must separate cognition from hook bookkeeping or experimentally justify any bounded exception.
4. Donor F94 `wegehierarchie` has a live-import/archive-only source-closure defect; Frankenstein 2.0 must adapt or retire the interface, not blindly restore the killed algorithm.

## 2. WorkExecutionBinding v2.1

### 2.1 Identity domains

Keep these namespaces distinct:

- `paket_id`: durable delegated-work identity;
- `package_generation`: workpackage attempt/supersession generation;
- `parent_session_id`: context only;
- `spawn_tool_use_id`: exact parent `Agent` invocation identity;
- `agent_id`: native child run identity when observed;
- `agent_run_generation`: resume/background/replacement generation distinct from stable agent identity where needed;
- `task_id`: optional separate task-system identity, never an alias for `agent_id`;
- `child_tool_use_id`: exact child tool invocation identity;
- `result_receipt_id`: immutable typed result/completion receipt.

### 2.2 Deterministic source/ABI candidate join

The donor `handoff()` already produces a capsule whose first line is an exact marker:

`HANDOFF <paket_id>`

and declares that capsule to be the delegated subagent text. Current Claude Code documentation exposes:

- `Agent` Pre/PostToolUse call-scoped `tool_use_id`;
- `Agent` `tool_input.prompt`;
- Agent PostToolUse `tool_response.agentId`;
- Subagent lifecycle `agent_id` as an independent runtime crosscheck.

Therefore the target adapter is:

```text
entityos_arbeitspaket(paket_id, generation)
        |
        | exact HANDOFF marker observed in actual Agent prompt
        v
Agent PreToolUse(tool_use_id)
        |
        | same call identity
        v
Agent PostToolUse(tool_use_id, tool_response.agentId)
        |
        v
WorkExecutionBinding(paket_id, generation, tool_use_id, agent_id)
        |
        +--> child tool_use_id(s)
        |
        +--> typed result_receipt_id
        |
        v
reconcile / CompletionEvidence
```

### 2.3 Fail-closed rules

- Parse exactly one valid `HANDOFF <paket_id>` marker from the actual observed `Agent` prompt.
- Verify the package exists, belongs to the expected parent context/generation and is in an admissible unresolved state.
- Bind the marker to the exact call-scoped `tool_use_id`; never infer by timestamp, ordering, prompt similarity, session proximity, agent name/type or completion order.
- A `tool_use_id` may not bind to two packages.
- A package may not silently bind to multiple Agent calls unless an explicit fanout contract declares that cardinality.
- On Agent PostToolUse, require the same `tool_use_id`; capture `tool_response.agentId` when emitted.
- Normalize documented `agentId` and lifecycle `agent_id` only after exact target-runtime equality/version evidence; before that preserve the relation as candidate/UNKNOWN.
- `task_id` stays independent.
- Spawn/start/stop evidence is not completion evidence.
- Reconcile PASS requires a typed result receipt bound to the exact WorkExecutionBinding.

### 2.4 Required regressions

Before F2 runtime credit:

1. unique `tool_use_id` on every synthetic Pre/Post fixture;
2. same-session interleave `Pre(A), Pre(B), Post(A), Post(B)`;
3. reverse completion `Pre(A), Pre(B), Post(B), Post(A)`;
4. two concurrent delegated packages with distinct HANDOFF markers and reverse child completion order;
5. zero/multiple marker fail-closed cases;
6. package-generation mismatch;
7. tool-use-id collision/cardinality rejection;
8. absent `agentId` remains UNKNOWN rather than guessed;
9. installed-target harmless Agent capture proving actual `paket_id -> tool_use_id -> agentId`;
10. optional SubagentStart/SubagentStop equality crosscheck on the exact installed build.

Map this work primarily to `F2-WP-102` and `F2-WP-601`.

## 3. Typed hook event substrate before GWT projection

The donor passes whole hook JSON to `stern.py`, but pinned source does not typed-extract/persist `tool_use_id` or `agent_id`. Its current `zulassen()/merken()` path relies on one session-scoped `active_turns.effect_id`. Its GWT-oriented `gw_absicht` later selects PostToolUse events by session provenance plus a turn time window and reduces them to tool names.

That is insufficient for a concurrent child architecture.

Frankenstein 2.0 must first persist a raw typed event such as:

```text
TypedToolEvent {
  session_id,
  turn_id_or_episode_id,
  generation,
  hook_event_name,
  tool_name,
  tool_use_id,
  agent_id_if_observed,
  agent_type_if_observed,
  parent_workexecution_binding_id_if_known,
  payload_digest,
  observed_at_utc,
  observed_at_monotonic,
  source_runtime_identity
}
```

Then and only then may GRID/GWT intentionally aggregate events into a parent-turn or global-workspace projection.

`RAW_CAUSAL_PROVENANCE -> EXPLICIT_AGGREGATION -> GWT VIEW`

not

`SESSION + TIME WINDOW -> IRREVERSIBLE OWNERSHIP COLLAPSE`.

Required regression for `F2-WP-508`: one turn containing parent + child A + child B tool events with distinct invocation identities. Raw events must remain separable. Any merged GWT view must identify its aggregation rule and preserve links back to original events.

## 4. GWT causal measurement consequence

GRID/GWT telemetry must be able to answer:

- which actor/invocation produced a candidate observation;
- which broadcast consumed it;
- which later slot/function used it;
- whether it changed a candidate/decision;
- which exact outcome re-entered the same causal chain.

The latest Triggerword-5 source finding means GWT credit cannot be based on donor-style session/time-window tool ownership. This is a correctness prerequisite, not final security hardening.

Map to `F2-WP-508`, `F2-WP-101`, telemetry `grid10_telemetry.sqlite`, `system_telemetry.sqlite`, `performance.sqlite` trace/span lineage.

## 5. Stop-hook local-model boundary

The pinned donor contains both:

- a declared top-level invariant equivalent to `no LLM call in a hook`;
- live Stop-hook code that synchronously calls a configurable Ollama `/api/generate` relevance judge (`qwen2.5:0.5b` default), then reduces model-derived relevance credit into MicroClay.

The useful mechanism is the **typed model-assisted relevance signal**. The problematic placement is synchronous model inference inside a fixed Stop-hook budget together with DB reads/writes and later bookkeeping.

### 5.1 Frankenstein-2.0 preferred architecture

```text
Stop / turn-close deterministic bookkeeping
        |
        +--> emit RetrievalJudgementNeed(episode_id, candidate_ids, query_digest)
        |
        v
return quickly

GRID / retrieval work item
        |
        +--> local model or other admitted judge
        |
        v
ModelRelevanceEvidence(candidate, confidence, provenance)
        |
        v
deterministic reducer -> retrieval feedback
```

The model result remains candidate evidence and cannot independently promote canonical truth/memory state.

### 5.2 Required discriminator before final placement

Instrument donor/successor equivalents under:

- warm local model;
- cold model;
- slow model;
- unavailable model;
- same-session reordered turn/Stop conditions.

Measure p50/p95/p99 Stop critical-path latency, timeout behavior, later-bookkeeping completion and correct retrieval-episode attachment.

If a synchronous exception is ever retained, it must be an explicit measured architecture choice, not an accidental contradiction.

Map to `F2-WP-301`, `F2-WP-509`, `F2-WP-003`, full latency tracing and hypotheses DB.

## 6. F94 wegehierarchie source closure

At the pinned donor SHA:

- root `udb/abruf/wegehierarchie.py` is absent;
- archived bytes exist under `_archiv-phase4/wegehierarchie.py`;
- live `paket.py` still imports `.wegehierarchie` in F94 bookkeeping;
- current source preserves an older negative result that deleting it caused `ModuleNotFoundError`/lost F94 behavior;
- a later measured kill decision says the reinforcement algorithm failed its usefulness threshold and was archived without replacement.

This is not an instruction to resurrect the old algorithm.

Frankenstein 2.0 law:

- no live import may target an archive-only/retired module;
- if the functionality remains useful, define a typed successor interface and re-run the usefulness discriminator;
- if intentionally retired, remove/replace the live caller;
- success-mark bookkeeping that remains useful must not depend transactionally on an optional retired reinforcement module;
- preserve the old algorithm and its negative measurement as provenance/negative result.

Required tests:

1. source-closure scan: no live import to archive-only modules;
2. F92b/success-mark persistence independent of F94 successor/retirement;
3. exact-source runtime/import probe when target environment exists;
4. if a successor reinforcement is proposed, A/B or declared usefulness discriminator before adoption.

Map to donor-freeze/import work under `F2-WP-004`/`F2-WP-100` as applicable; it is not a reason to transplant the archived algorithm unchanged.

## 7. Worker-wave reconciliation / what NOT to promote

Do not treat any of the following as runtime proof:

- official documentation alone;
- a source-level HANDOFF marker alone;
- schema-validity claims from packets later invalidated by currentness/schema checks;
- SubagentStop alone;
- session/time-window correlation;
- source-inferred runtime collision frequency;
- archived wegehierarchie bytes;
- current donor comments as proof of present installed-host behavior.

One 10:42Z worker showed that a WorkExecution packet advertised as schema-valid/current became inadmissible under the exact-main validator after unrelated canonical-main movement and also lacked a required `authority_classification`. Retain the semantic findings that were independently source-checked, but do not use packet-admission labels as architecture truth.

This creates a separate engineering hypothesis for the research ingest system: exact-main currentness may produce excessive TOCTOU admission churn under high-frequency unrelated main commits. Measure it before weakening any fail-closed validator.

## 8. Bugs and hypotheses to seed into Frankenstein-2.0 data spine

When the canonical repository data spine is available, seed at minimum:

### Bugs

- `F2-BUG-0001` Typed hook identity loss: donor does not retain `tool_use_id`/child identity through hook reducer.
- `F2-BUG-0002` Session/time-window GWT ownership collapse: raw actor/invocation ownership can be irreversibly lost before reflection.
- `F2-BUG-0003` Stop-hook synchronous local-model critical path contradicts declared deterministic hook boundary and may starve later bookkeeping.
- `F2-BUG-0004` F94 live import targets retired/archive-only `wegehierarchie` implementation.

No bug becomes `FIXED` until root cause, fix commit and regression receipt satisfy the canonical bug database law.

### Hypotheses / counterhypotheses

- `F2-HYP-0001`: HANDOFF marker + Agent hook ABI is sufficient for deterministic package-to-child binding on the installed target.
- `F2-HYP-0001-C1`: coordinator does not pass capsule byte-faithfully or installed ABI differs, so wrapper/nonce receipt is still needed.
- `F2-HYP-0002`: moving relevance model inference outside Stop critical path lowers tail latency and preserves retrieval quality.
- `F2-HYP-0002-C1`: bounded synchronous local inference is operationally cheaper and harmless at measured tail latency.
- `F2-HYP-0003`: explicit typed provenance before GWT aggregation prevents cross-child attribution without material overhead.
- `F2-HYP-0004`: old F94 reinforcement should remain retired unless a successor clears its usefulness discriminator.

## 9. Telemetry requirements derived from this wave

Every WorkExecution/GWT test must log:

- package/generation;
- parent Agent `tool_use_id`;
- child `agentId/agent_id` evidence and normalization status;
- child tool invocations;
- raw typed hook event IDs;
- GWT aggregation/projection IDs;
- result receipt/reconcile identity;
- all latency spans from handoff -> Agent invocation -> child start -> first action -> result -> reconcile;
- concurrency cardinality and completion order.

Every Stop/retrieval-judge test must log:

- Stop start/end and monotonic budget;
- model queue/load/TTFT/complete latency;
- DB read/write/lock latency;
- whether each later bookkeeping step completed;
- exact retrieval episode identity receiving feedback.

## 10. Final build laws

`HANDOFF_MARKER = IDENTITY_CARRIER, NOT COMPLETION`

`SESSION_ID != INVOCATION_ID != AGENT_ID != TASK_ID`

`RAW_TYPED_PROVENANCE MUST PRECEDE GWT AGGREGATION`

`SESSION_PLUS_TIME_WINDOW != TOOL_EVENT_OWNERSHIP`

`MODEL_RELEVANCE_EVIDENCE != CANONICAL_MEMORY_TRUTH`

`HOOK_CRITICAL_PATH_MODEL_INFERENCE MUST BE MOVED OR EXPLICITLY JUSTIFIED BY MEASUREMENT`

`LIVE_IMPORT_TO_ARCHIVE_ONLY_MODULE = SOURCE_CLOSURE_BUG`

`NEGATIVE_RESULT MUST SURVIVE SUCCESSOR DESIGN`

The next Triggerword-4 build frontier for this wave is source-level typed hook identity + WorkExecutionBinding v2.1 regressions, followed by installed-target harmless Agent capture and concurrent anti-crosswire validation. GWT causal-use credit depends on retaining this provenance.
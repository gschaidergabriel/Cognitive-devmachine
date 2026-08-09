# 666 Run Report — PF History Semantic k384–k399

Time: 2026-08-09 13:34–13:40 +07
Stage: L0_ARCHIVE_ASSIMILATION
Gate: NOT_PASS

Resolved and directly inspected frozen-head first-parent ordinals `k384` through `k399`. Range compare `HEAD~400..HEAD~384` reports exactly 16 commits, matching the claimed shard.

## Main result

This slice exposes a recurring architecture failure: **surface registration, intent recognition and actual executable capability were separate drifting contracts**. It also preserves strong modality-parity, state/privacy-boundary, portability and truthful-failure lessons.

### Command contract and routing precedence

- `k386 2ce24c3a`: several slash-command expansion templates did not match the router regexes, so registered commands silently fell into generic chat.
- `k385 4220cbeb`: deterministic local-file-search language was captured by a broader agentic query regex until an explicit precedence guard was added.
- `k387 17dc30b0`: even after routing, the file-search subprocess invocation itself crashed because mutually incompatible subprocess capture options were combined.

Current synthesis: command registration is not capability proof. ClayCode/H1 should bind user-facing command schema, typed parameters, recognizer, precedence and executable handler into one validated/differentially tested contract.

### Modality parity

`k393 abcef77b` removes a separate PTT mini-router and sends transcribed speech through the same full command router as typed input. This is useful ancestry for dissolved multimodal FRANK: modality-specific sensing should normalize into shared intent/effect semantics unless modality is explicitly causal.

### Runtime state, privacy and secrets

`k391 75cf3a12` removes mutable/user databases and machine-specific config from Git tracking. `k392 ae6b4601` removes historical hardcoded credential material and shifts secret configuration toward environment/runtime injection. No credential values are reproduced by this Level-0 run.

Current transfer: UnifiedDB/runtime personal state may be provenance-linked to source versions but must be physically and semantically separate from repository/research artifacts; secrets are an excluded payload class for ClayGraph, receipts and model context.

### Portability / packaging

`k389 43361326` adds package/test configuration, version ranges and missing package declarations. `k390 62da68e6` removes widespread developer-root/DISPLAY assumptions in favor of environment/root-derived paths. These become H3/project-hardware regression inputs rather than direct current implementation credit.

### UI event-loop negative result

`k397 82250b85` introduces throttled resize/deferred remeasurement to reduce expensive layout recalculation; `k396 123ec2ba` then documents a layout cascade loop from that optimization and reverts it; `k395 11162c59` adopts another event-scheduling strategy. This is a compact historical example of an optimization creating a feedback instability. Current rule: event-loop/performance changes require measurement plus rollback, not local latency intuition alone.

### Truthful terminal state and retry

`k398 4195e310` and `k399 a0798cad` add bounded retry/backoff for transient LLM errors. `k399` also stops entity agents from publishing successful session notifications when summary generation failed. Durable law: terminal success must be evidence-backed; notification/memory commits must not turn partial failure into an apparent success.

### Additional reliability evidence

- `k384 c4fdf845`: GUI grab before window mapping is a lifecycle race.
- `k388 9363da52`: bare exception handlers swallowed shutdown/interrupt control semantics and were narrowed to ordinary exceptions.
- `k394 ff81b47c`: initial local-file-search/streaming-scroll work provides the precursor later corrected by k385–k387.

## Exact ordinal identities

k384 `c4fdf845`; k385 `4220cbeb`; k386 `2ce24c3a`; k387 `17dc30b0`; k388 `9363da52`; k389 `43361326`; k390 `62da68e6`; k391 `75cf3a12`; k392 `ae6b4601`; k393 `abcef77b`; k394 `ff81b47c`; k395 `11162c59`; k396 `123ec2ba`; k397 `82250b85`; k398 `4195e310`; k399 `a0798cad`.

## Durable outputs

- `research_entity/archive_assimilation/manifests/PROJECT_FRANKENSTEIN_HISTORY_SEMANTIC_K384_K399_20260809T1338p0700.json`
- `research_entity/archive_assimilation/receipts/666_20260809T1339p0700_chatgpt_secondary_pf_history_k384_k399.json`
- `research_entity/rooms/center_events/20260809T1340p0700_666_pf_history_k384_k399_delta.json`

Credit: 16 PF ordinals terminally dispositioned for coordinator dedup; 0 quantified earned-work hours; 0 manufactured global Level-0 percentage. No paid/final training started.

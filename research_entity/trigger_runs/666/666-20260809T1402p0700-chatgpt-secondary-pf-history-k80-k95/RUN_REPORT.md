# 666 Level-0 Run Report — Project-Frankenstein History k80..k95

## Run identity

- Trigger: `666`
- Actor: `chatgpt-secondary`
- Stage: `L0_ARCHIVE_ASSIMILATION`
- Frozen head: `abba90a5767d85abc8a1ac340bae92842dab35c1`
- Exact ordinal shard: `k80..k95`
- Materialized and terminally dispositioned: `16/16`
- Winning claim: `3fcc206581c404beac1054c46a00863a61bdbb4c` at 13:57:06 +07:00
- Later competing claim: `4c52a7aad684a04b9ede536b49c844cf52821d24` at 13:57:23 +07:00
- Runtime reproduction: not performed; evidence class is historical Git commit/diff/document lineage.

## Main findings

### Durable spatial memory should not equal prompt context

`k80` added persistent room objects with placement provenance, timestamps, soft removal state and interaction timestamps. Only the latest five objects are projected into the full `[SPATIAL]` prompt and slim/idle mode excludes them.

**Transfer:** maintain durable state independently from context-window projection. Retrieval/context routing should decide what becomes cognitively available without destroying the underlying history.

### Inferred location is not ground truth

`k83` added IP geolocation for weather, with timezone mapping and ultimately a hardcoded city fallback if detection failed.

**Transfer:** convenience-derived personal context needs source provenance, uncertainty and scope. A default/fallback location must not silently become a durable fact about the user or environment.

### Capability-inadequate autonomy can be coherently disabled

`k84` disabled Genesis not only at systemd level, but across cognition hooks, thought domains, Web APIs, UI navigation, swarm topology and watchdog representation while preserving code for a future stronger model.

**Transfer:** subsystem lifecycle is an architecture-wide state. If a capability is unsupported, every observer/effect/recovery surface should agree that it is inactive; otherwise the system develops phantom capabilities.

### Control metadata belongs outside user content

`k85` moved persona and language from concatenated user-intent text into separate API fields and the system prompt, specifically because the model had copied instructions into generated email body text. The same revision moved read-state persistence from local-only UI state to server sync.

**Transfer:** keep user content, persona/style controls and authoritative state in separate channels. Prompt concatenation is not a reliable isolation mechanism.

### Optimistic and bulk effects need explicit completion semantics

`k87` and `k88` added optimistic mail updates, bulk mark-read and delete/spam confirmations. This is part of the lineage that later produced explicit rollback regressions in k375/k376.

**Transfer:** visible optimistic projections should be backed by an effect lifecycle (`PENDING`, `COMMITTED`, `FAILED`, `ROLLED_BACK`) or equivalent verified receipts/reconciliation.

### Latest documents can erase historical topology if version lineage is ignored

`k89` rewrote multiple papers from earlier entity/DeepSeek/overlay architecture into Rooms/Qwen/WebUI terminology and removed historical-warning notes.

**Transfer:** papers and architecture docs require commit-epoch validity. The latest text cannot be used as a timeless description of earlier system states; Git history is part of the source corpus.

### IAPT is method provenance, not automatically validated performance

`k90` introduced the IAPT method paper: adaptive multi-turn adversarial evaluation, failure-mode analysis, targeted positive data generation and LoRA iteration. The paper also reports strong iteration metrics and novelty claims.

**Transfer:** preserve the method lineage, but promote quantitative/novelty claims only after reconstructing evaluator policy, raw transcripts, training artifacts and scoring procedure.

### Interface and model topology are explicit epochs

`k94` deleted the overlay/writer and made WebUI the sole interaction interface. `k95` then removed Llama/DeepSeek/Ollama and collapsed cognition/routing onto Qwen2.5-3B.

**Transfer:** historical behavior must be indexed against interface and active-model epochs. "Frank" is not one invariant runtime configuration across the history.

## Negative results preserved

- IP/timezone location detection could degrade to a hardcoded city fallback.
- Genesis was disabled despite extensive prior integration because the available base model was judged insufficiently reliable for self-improvement.
- Client-only email read state failed to persist across reload.
- Persona/language prompt concatenation leaked control text into generated mail behavior.
- Current papers were rewritten to current architecture and had historical notes removed.
- Large overlay/writer surfaces were later deleted wholesale.
- Multi-model architecture was later replaced by a single 3B model.

## Evidence and credit boundary

IAPT scores, training duration, turn counts, claimed novelty, resource savings and other source-reported metrics were not independently reproduced. No avoided-hours value is added because row-level conceptual overlap against the earned-work ledger was not audited here.

Global Level-0 exact percentage remains unchanged because the combined obligation denominator is still `NOT_FROZEN`. `666_RELEASE_GATE` remains `NOT_PASS`.

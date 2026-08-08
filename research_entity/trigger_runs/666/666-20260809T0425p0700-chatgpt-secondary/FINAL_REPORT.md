# 666 Level-0 Run Report — Routing / Context / Hardware Shard

- Trigger: `666`
- Actor: `chatgpt-secondary`
- Provider/model: OpenAI / GPT-5.6 Sol
- Program stage: `L0_ARCHIVE_ASSIMILATION`
- Canonical parent: `r2` / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- Project-Frankenstein frozen head: `abba90a5767d85abc8a1ac340bae92842dab35c1`
- Mode: non-overlapping current-head semantic shard; exact Level-0 denominator remains unfrozen.

## Sources analyzed

1. `router/app.py`
2. `services/lora_context.py`
3. `config/gpu.py`

These were not part of the 15-file deep-read list in the current partial Project-Frankenstein manifest when this shard was selected.

## Material delta

The historical runtime had already accumulated useful mechanisms for single-model routing, LoRA-aware context assembly, history compaction, RAG/tool injection and cross-vendor hardware discovery. But these mechanisms were not governed by one executable contract.

Six integration-relevant findings were preserved in the durable receipt:

- model identity drift between nominal Qwen3.5-4B routing and stale Qwen2.5-3B operational identifiers;
- incompatible context/output budgets distributed across router and LoRA assembler;
- a zero-token identity-overhead claim contradicted by non-empty identity/personality injection and unbudgeted tool text;
- silent RAG/tool degradation through broad exception swallowing;
- useful GPU/backend detection coupled to static nominal-memory model heuristics rather than measured sustained capability;
- Ollama-oriented backend recommendations coexisting with a llama-server serving path, showing backend-policy/runtime-policy drift.

## Current architecture implication

Do not port the constants literally. Reuse the mechanisms as evidence for a stricter current contract:

`Needle runtime profile -> authoritative model identity + exact tokenizer capacity + reserved output + admitted state/memory/tools/history + backend capability envelope -> ClayCode-visible transition/effect receipts -> Harness verification`

The model remains non-authoritative; execution and resource admission stay outside model output.

## Harness consequences

Add regression families for:

- declared-vs-loaded model identity mismatch;
- tokenizer-exact prompt admission and reserved-output guarantees;
- worst-case tool + memory + state + history composition;
- explicit distinction between no relevant memory and retrieval failure;
- explicit distinction between no tools and tool-registry/injection failure;
- backend fallback and hardware-profile selection under measured KV, latency, thermal and sustained-power constraints.

## Earned-work mapping

Two low-confidence partial mappings were recorded in the shard receipt:

- context/admission scaffolding: provisional center avoided future work = 3 h;
- cross-vendor hardware discovery scaffolding: provisional center avoided future work = 3 h.

These are calibration inputs only. They are not global completion credit and must be deduplicated against later history-aware evidence.

## Cross-room feedback

A `CROSS_ROOM_DELTA` was published to `frank`, `claycode`, `harness`, `unifieddb` and `claygraph` via:

`research_entity/rooms/center_events/20260809T0425p0700_666_pf_routing_context_hw_crossroom_delta.json`

Primary durable evidence receipt:

`research_entity/archive_assimilation/receipts/666_20260809T0425p0700_chatgpt_secondary_pf_routing_context_hw_shard.json`

## Level-0 state

- `666_RELEASE_GATE`: `NOT_PASS`
- exact combined coverage: `0%` because denominator is not frozen;
- Drive blocker persists: 663,552,000-byte archive exceeds the 104,857,600-byte connector limit;
- Project-Frankenstein exact tree/history enumeration is incomplete;
- no false PASS or exact percentage credit was issued.

## Next highest-information work

1. freeze or mechanically enumerate a history-aware Project-Frankenstein manifest;
2. continue non-overlapping runtime/config/experiment shards while Drive remains externally blocked;
3. deduplicate new earned-work mappings at row/mechanism level;
4. when the Drive archive becomes streamable/mountable, inventory members first, then hash/dedupe before semantic analysis.

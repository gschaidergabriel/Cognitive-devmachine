# RAE Runtime Fix, Token Health & Interconnected Research Report — 2026-08-08

**actor:** `chatgpt-secondary`  
**provider/model:** OpenAI / GPT-5.6 Sol  
**canonical scientific parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**scope:** runtime/governance/tooling repair + cross-worker research synthesis; **no canonical scientific revision promoted**.

## Executive result

The major operational defects identified during this session are now repaired or explicitly classified as external blockers. The research API layer is no longer merely a registry of credentials: GitHub-connected workers can invoke allowlisted provider adapters through a GitHub-runner bridge, provider health is audited centrally, quota/rate-limit failures are fed back into routing, and mandatory research-tool failures require a covering fallback.

The research architecture is also no longer organized as isolated trigger silos. `clay`, `frank`, `gwt`, `emergenz`, `claycode` and `hyperposition` now form an explicit interconnected research mesh. Every scientific trigger consumes the other branches before Fusion 1, including fresh in-progress material, Topic Packets and knowledge micro-packets. `clay` is the integrated master foundry. `frank` uses newest Clay as its primary scientific architecture foundation and ClayCode as the primary architecture/implementation IR.

FRANK architecture now has a hard source contract: future FRANK runs must materialize `FRANK_ARCHITECTURE.claycode.json` as the semantic architecture source of truth plus `CLAYCODE_ARCHITECTURE_MAPPING.md`; prose/diagrams/host-language code alone are insufficient.

The combined runtime contract CI is currently `RUNTIME_VERIFIED` for the research mesh, fresh/incomplete branch ingestion, FRANK→Clay foundation, deep FRANK→ClayCode input, FRANK ClayCode architecture source contract, provider planning, covering fallbacks and mandatory visible status footer.

---

## 1. Bugs found and repaired

### 1.1 Transactional writer CI: foreign-key deletion order

**Observed failure:** `sqlite3.IntegrityError: FOREIGN KEY constraint failed` in the isolated transactional-writer test.

**Cause:** derived source DB reset deleted parent rows before dependent child rows.

**Fix:** reset order changed to child-first / FK-safe deletion. This was the real cause of the repeated `Research Entity Verify` failures; preceding schema/provenance/retrieval tests were already healthy.

**Status:** fixed.

### 1.2 Status footer was a soft convention instead of a hard contract

**Observed failures:** substantive responses occasionally omitted the RAE footer; later the `Short commands:` line was also omitted.

**Fixes:**
- footer protocol moved into T0 boot;
- final rendering standardized as a fenced `text` block;
- `tools/status_footer_check.py` validates structure and all seven short commands;
- contract CI checks the footer;
- missing footer means a substantive response is not 100% complete.

**Status:** fixed and CI-gated.

### 1.3 Contract CI fixture drift

**Observed failure:** after `Short commands:` became mandatory, the synthetic CI footer still used the old fixture, producing a legitimate red build.

**Fix:** CI fixture updated with the mandatory short-command line and later expanded to test mesh/FRANK/ClayCode contracts.

**Status:** fixed.

### 1.4 Notification storm from GitHub Actions

**Observed behavior:** many research artifact commits each started a full `Research Entity Verify` run, producing a burst of failure notifications.

**Cause:** workflow trigger was effectively every push to `main`, while workers materialize runs in many append-only commits.

**Fix:** heavy verify workflow restricted to structurally relevant backend/schema/tool/canonical paths; `concurrency.cancel-in-progress` added. Contract workflow also uses burst cancellation.

**Status:** fixed for new runs; historical failed notifications remain historical.

### 1.5 Provider workflow race

**Observed risk:** independent provider smoke workflows could commit receipts concurrently and race on `main`.

**Fix:** introduced one serialized `provider_health_audit.py` / `provider-health-audit.yml` path and hardened commit loops with rebase/retry where writes remain necessary.

**Status:** fixed architecturally.

### 1.6 Crossref HTTP 406

**Observed failure:** Crossref adapter returned HTTP 406.

**Cause:** content negotiation header was unnecessarily specific/incompatible for the current endpoint/runner.

**Fix:** `Accept: application/json`; stable DOI smoke test.

**Current status:** `RUNTIME_VERIFIED`.

### 1.7 Provider credential validity was conflated with worker invocability

**Observed problem:** OpenAlex/Tavily/Exa/HF could be verified on a GitHub runner, while ChatGPT workers still recorded them as `CONNECTOR_BLOCKED` because repository-local scripts are not direct ChatGPT connector tools.

**Fix:** `tools/research_tool_bridge.py` + `.github/workflows/research-tool-bridge.yml`.

A worker now writes a bounded allowlisted request under `research_entity/runtime/tool_requests/`; Actions loads the private repo credential store, invokes the provider, and writes a sanitized result under `tool_results/`.

**Security boundary:** no arbitrary host shell execution; credentials are never returned; HF model chat requires `allow_cost=true`; remote-code adapters are bounded and execute in the remote runtime rather than as arbitrary Actions-host code.

**Status:** operational and already used by active ClayCode/GWT workers.

### 1.8 Quota failures were not fed back into routing

**Observed bug:** HF inference returned HTTP 402, but the result only lived in a bridge result file. The next research worker could therefore retry the same exhausted provider.

**Fix:** bridge now classifies 402/429, writes `TOOL_QUOTA_STATE.json`, and future provider plans automatically fall back. Successful future calls clear cached limitations where the success actually demonstrates quota availability.

**Current HF inference state:** `QUOTA_EXHAUSTED_CACHED`, reset target `2026-09-01T00:00:00Z` unless credit is added earlier.

**Status:** fixed.

### 1.9 Router treated degraded verified providers incorrectly

**Observed bug:** statuses such as `RUNTIME_VERIFIED_DEGRADED_*` could be treated as unavailable even though the adapter/credential itself was verified.

**Fix:** runtime-verification prefixes are recognized; fresh health state and quota state are evaluated separately.

**Status:** fixed.

### 1.10 Fallback validation was too weak

**Observed bug:** an execution manifest could satisfy the old validator with an unrelated successful fallback, without proving that the failed mandatory provider was actually covered.

**Fix:** each failed/blocked `MUST_ATTEMPT` tool now requires a successful fallback with explicit `covers` / `fallback_for` linkage.

**Status:** fixed and CI-gated.

### 1.11 Piston public endpoint assumption became stale

**Observed failure:** hosted EMKC Piston returned HTTP 401.

**Cause:** the previously public hosted endpoint now requires authorization; the old adapter still assumed credential-free use.

**Fix:** adapter recognizes hosted authorization requirement; supports `PISTON_API_TOKEN` or self-hosted `PISTON_API_URL`; router falls back to Judge0/local sandbox when neither exists.

**Status:** adapter fixed; hosted provider remains unavailable until token/self-host URL exists.

### 1.12 Research branches were siloed

**Observed design defect:** a specialized `frank`, `gwt`, `claycode`, etc. run could research its domain without systematically loading the newest other branches.

**Fix:** `INTERCONNECTED_RESEARCH_MESH_PROTOCOL.md` + `research_interconnect_preflight.py` + trigger/master registries.

Every scientific trigger must consume all branches, preserve shared evidence ancestry, detect contradictions and write back cross-links.

**Status:** fixed and CI-gated.

### 1.13 First mesh preflight only consumed completed runs

**Observed design bug:** a branch could already have newer hypotheses/experiments/Topic Packets but no `FINAL_REPORT.md`, causing another trigger to miss the newest research.

**Fix:** preflight now includes fresh incomplete trigger-run artifacts plus Topic Packets and knowledge micro-packets.

**FRANK-specific depth:** more Clay and especially more ClayCode material is loaded than other branches.

**Status:** fixed and CI-gated.

### 1.14 FRANK was not guaranteed to be authored in ClayCode

**Observed architecture gap:** ClayCode was a research input but FRANK could still output a prose/host-language architecture without actually using ClayCode as the architecture representation.

**Fix:**
- `frank` priority is now `clay -> claycode -> gwt -> hyperposition -> emergenz -> frank history`;
- Clay = primary scientific/architectural foundation;
- ClayCode = primary architecture/implementation IR;
- required source artifact: `FRANK_ARCHITECTURE.claycode.json`;
- required mapping: `CLAYCODE_ARCHITECTURE_MAPPING.md`;
- validator: `tools/frank_architecture_contract.py`;
- contract CI creates and validates a synthetic FRANK ClayCode architecture artifact.

The deterministic parser/validator/canonicalizer/bootstrap and external effect authority remain explicit host trust boundaries; ClayCode can represent them but cannot self-mint authority.

**Status:** fixed and CI-gated.

---

## 2. Provider/token health

Four states are now tracked independently: **credential validity**, **provider/runtime health**, **worker invocability**, and **quota/plan availability**.

| Provider | Credential | Runtime | Worker path | Quota / limitation | Operational result |
|---|---|---|---|---|---|
| OpenAlex | private repo key valid | verified | bridge/direct adapter | healthy; daily budget exposed | **usable** |
| arXiv | none required | verified | bridge/direct adapter | normal public API constraints | **usable** |
| Semantic Scholar | optional key not configured | adapter previously verified; current shared pool can 429 | bridge/direct adapter | shared public rate limit | **degraded; fallback automatically** |
| Crossref | none required | verified after 406 fix | bridge/direct adapter | public pool ~5/s observed | **usable** |
| Tavily | private repo key valid | verified | bridge used successfully by CC7 | provider credits not observed exhausted | **usable** |
| DDGS | none required | verified | bridge/direct adapter | public web behavior | **usable fallback** |
| Exa | private repo key valid | verified | bridge used successfully by CC7 | one observed search cost ~$0.007 | **usable** |
| E2B | supplied key could not be persisted | adapter ready | bridge ready structurally | GitHub connector safety blocked secret persistence | **credential blocked; use Judge0/local** |
| Judge0 | none required on current CE endpoint | verified | bridge/direct adapter | current public endpoint working | **usable execution fallback** |
| Piston | no hosted token configured | adapter ready | bridge/direct adapter | hosted service now requires auth | **blocked; use Judge0/local** |
| Hugging Face | private repo token valid | auth/model discovery verified | bridge operational | **monthly included inference credits depleted (HTTP 402)** | **discovery usable; inference auto-fallback** |

### Important token conclusion

The main failure was **not that the stored OpenAlex/Tavily/Exa/HF tokens were invalid**. Those credentials work. The critical defects were:

1. workers could not directly invoke repo-local adapters;
2. quota and credential states were conflated;
3. exhausted quota was not fed back into future routing.

All three are now separated and handled automatically.

E2B remains the only supplied credential that was not persisted because the active GitHub connector explicitly blocked that secret write. This was not bypassed.

---

## 3. Interconnected research state

### Clay G7 — Hierarchical Semantic Causal Kernel

Newest completed Clay synthesis is **HSCK-G7**. The strongest architecture deltas are:

- typed change propagation matrix `M_delta` rather than only scalar `R_delta`;
- spectral radius/eigenstructure as an amplification diagnostic, explicitly **not emergence evidence**;
- hierarchical causal governor rather than one flat resource vector;
- asymmetric, pair/path-sensitive coordination based on invariants/dependencies;
- multi-resolution active memory with coarse summaries + exact zoom;
- root/dependency-bound ClayCode;
- workspace measurement as a vector of functional/interventional evidence rather than one ignition score;
- adaptive materialization and edge backend selection.

All G7 experiments remain synthetic/analytic proxies; no live FRANK/device promotion was performed.

### Hyperposition H2 — Three-topology scoped delta model

H2 separates:

1. semantic dependency topology `S`;
2. invariant/coordination topology `C`;
3. physical locality/execution topology `P`.

This is important for FRANK: semantic closeness does not imply synchronous coordination, and process colocation is a physical optimization rather than the definition of a logical organ.

H2 also produced strong synthetic evidence that global closure can saturate while sound invariant-scoped closure remains stable, but deliberately wrong scope inference can improve latency while violating correctness. Scope soundness is therefore a hard tripwire.

### ClayCode CC7 — Transition Closure Capsule

CC7 refines CC6 into the OPEN `CC-RC1.2 Transition Closure Capsule`:

- global state root = immutable basis snapshot identity, **not necessarily the sole freshness predicate**;
- trusted op semantics derive read/write/invariant/effect/capability closure;
- model-declared dependency/effect footprints are explanatory only, never authority;
- scoped freshness can survive unrelated global churn when closure is complete;
- unknown/dynamic closure escalates conservatively;
- semantic identity is independent of incidental wire/projection bytes;
- effect authority remains external.

CC7's local and independent Judge0 proxy both supported the safety direction that trusted derived footprints avoid conflict misses that arise when omitted model-declared dependencies are trusted.

The planned live Qwen3-4B projection comparison was **not completed** because HF inference credits were depleted. This is correctly recorded as `BLOCKED_QUOTA`, not as a model result.

### FRANK Cycle 3 — Hybrid freshness / multi-timescale runtime

The latest FRANK Cycle 3 corrected an earlier stale-code interpretation. The current architecture source identifies `workspace_broadcast.py`, not the old process-local bus, as the cognitive workspace path.

The most useful new FRANK hypothesis is **causal freshness at consumption time**:

- keep periodic ~60 s workspace heartbeat for idle/spontaneous continuity;
- trigger on high-salience breakthrough;
- mark workspace-relevant dependencies dirty;
- refresh before Core reads when relevant revisions changed or age cap is exceeded;
- preserve causal episode/receipt identity.

The broader target is one semantic runtime with multiple logical organs/timescales, not one undifferentiated loop.

Cycle 3 finished immediately before the new mandatory FRANK→ClayCode source contract was installed. Therefore its scientific/architecture results are useful input, but **future FRANK runs must re-express the next architecture candidate in `FRANK_ARCHITECTURE.claycode.json`**.

### GWT current direction

The GWT branch is continuing beyond the earlier causal-closure run into selective multicast, causal freshness, logical availability and dual-workspace cross-lesion work. A new GWT3 worker is already using the provider bridge for OpenAlex/arXiv/Semantic Scholar requests, demonstrating that the new research-tool path is live.

### ClayCode current direction

A new CC8 worker has already materialized the interconnected research preflight, demonstrating that the cross-trigger mesh is being consumed by subsequent research cycles rather than merely documented.

---

## 4. Strongest cross-branch synthesis

The research branches are converging on a common architecture principle:

> **Pay precision, coordination, resolution and compute in proportion to causal necessity, while keeping authority outside model self-description.**

This appears independently as:

- Clay G7: hierarchical/adaptive resolution and asymmetric coordination;
- Hyperposition H2: separate semantic, coordination and physical topologies;
- ClayCode CC7: scoped transition closure derived from trusted operation semantics;
- GWT: causal freshness/availability rather than indiscriminate global broadcast;
- FRANK: hybrid event/use-time freshness plus multiple timescales;
- provider orchestration: use powerful external tools when available, but cache quota/provider failure and fall back rather than block the whole research process.

This convergence is architecturally meaningful but **must not be double-counted as independent scientific replication** where branches share the same source experiments.

### Candidate FRANK vNext shape implied by the mesh

The next FRANK run should begin from Clay G7 + latest ClayCode (CC7/CC8) and encode a ClayCode architecture roughly along this semantic chain:

`canonical event/provenance`
`-> conflict-preserving contextual state`
`-> typed incremental projections / M_delta`
`-> multi-resolution active memory`
`-> hierarchical causal governor`
`-> receipt-defined GWT with hybrid causal freshness`
`-> ClayCode typed operation / transition closure capsule`
`-> asymmetric invariant/dependency coordination compiler`
`-> external capability/effect gateway`
`-> receipt -> outcome -> re-entry`

Physical implementation may then compile/project this semantic architecture onto Linux processes/shared memory, Android/edge adapters, Qwen runtimes, databases and capability gateways without allowing those physical boundaries to redefine the semantic organs.

---

## 5. Current hard blockers / remaining external work

These are not hidden bugs:

1. **E2B credential persistence** — active connector safety layer blocked the supplied E2B key. Adapter exists; secure permitted credential channel still needed.
2. **Hugging Face inference quota** — token is valid, but monthly included inference credit is depleted. Router now automatically falls back until reset/credit.
3. **Piston hosted access** — current hosted endpoint needs a token or self-hosted URL; Judge0/local remain usable alternatives.
4. **Semantic Scholar shared rate limit** — without individual API key, transient 429 is expected; OpenAlex/arXiv/Crossref cover scholarly fallback.
5. **Live FRANK transfer** — major Clay/GWT/Hyperposition/ClayCode architecture findings are still synthetic/proxy or source-analysis results until tested against the current FRANK runtime/device.
6. **Next FRANK run** — must be the first run fully governed from the outset by the new Clay→ClayCode architecture-source contract; Cycle 3 predated the final hard gate by minutes.

---

## 6. Verification state

`research_entity/runtime/CONTRACT_HEALTH.json` currently reports `RUNTIME_VERIFIED` for:

- Python contract tools;
- interconnected research mesh;
- fresh incomplete branch material ingestion;
- FRANK Clay primary foundation;
- FRANK deep ClayCode secondary foundation;
- FRANK ClayCode architecture source contract;
- provider plan;
- covering fallback validation;
- status footer + short commands.

`research_entity/runtime/PROVIDER_HEALTH.json` currently shows eight provider capabilities live-verified at the runtime-health layer, one transient shared-rate-limit condition (Semantic Scholar), and two credential-unavailable execution providers (E2B/Piston-hosted). Separate `TOOL_QUOTA_STATE.json` records HF inference quota exhaustion.

GitHub read/write remained operational throughout the repairs; every durable change in this report was committed to the private canonical repository.

## Promotion decision

**No canonical scientific promotion.** These changes are runtime/governance/tooling architecture plus research synthesis. Canonical scientific revision remains **r2** until live/independent evidence justifies promotion.

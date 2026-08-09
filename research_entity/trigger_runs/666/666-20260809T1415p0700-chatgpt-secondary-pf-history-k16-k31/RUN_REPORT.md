# 666 Level-0 Run Report — Project-Frankenstein History k16..k31

## Run identity

- Trigger: `666`
- Actor: `chatgpt-secondary`
- Stage: `L0_ARCHIVE_ASSIMILATION`
- Frozen head: `abba90a5767d85abc8a1ac340bae92842dab35c1`
- Exact ordinal shard: `k16..k31`
- Materialized and terminally dispositioned: `16/16`
- Winning claim: `55d975ba59091a082930d309a8273835dd06e266`
- Race status: clean after full materialization.
- Runtime reproduction: not performed; evidence class is historical Git commit/diff/document lineage.

## Main findings

### The model cannot be both author and authority for its own ground truth

At `k26`, each project gained a `PROJECT.md` explicitly injected as `[BASE OF TRUTH]` on every turn. The model could emit structured update blocks that were automatically parsed and written back into that same file; later tool-enabled revisions instructed it to edit the file directly.

This creates a self-conditioning loop: generated text changes the state that is subsequently treated as trusted context.

**Transfer:** model output may propose updates, but authoritative project state needs independent commit authority, version/provenance, validation and reversible receipts before it can be promoted into ground truth.

### Agent authority expanded from sandbox to nearly full host control

`k25` introduced a project-root sandboxed coding-agent loop with bounded iterations and project-contained file tools. `k24` then removed the sandbox and allowed shell, filesystem, package, service and Docker access across the machine, blocking only a handful of destructive command substrings.

**Transfer:** a destructive-command blocklist is not an authority model. Host-level agents need capability scope, effect classes, approval policy, audit receipts and rollback/recovery boundaries.

### Uploaded files become untrusted model context and effect input

`k17` and `k27` allow files to be uploaded/dropped, previewed in chat, injected into model context and reorganized on disk.

**Transfer:** preserve separate provenance/trust for file bytes, extracted/preview text, user instruction, model interpretation and tool authority. Ingestion should not silently convert file content into instruction or authoritative state.

### Generated rendering is a security boundary

`k20` converts assistant markdown into HTML strings for page insertion. The shown renderer does not first expose an explicit escape/sanitize phase.

**Transfer:** generated and file-derived text should be escaped by default and only a strict allowlist of presentation markup should be rendered.

### Verification state can legitimately change over adjacent commits

At `k23`, streaming/tool functionality was explicitly described as structurally verified only because API credits were insufficient for live testing. `k22` then fixes a request-binding issue and records a source-reported end-to-end success state.

**Transfer:** structural review, integration testing and live end-to-end testing are distinct evidence statuses. Store promotion events rather than collapsing them into one timeless “tested” flag.

### Project agents can share infrastructure without sharing identity

`k28` explicitly defines the project agent as Claude, not Frank, with project-scoped chat, memory, hypotheses and filesystem, and without Frank's consciousness/SOMA systems.

**Transfer:** workspace identity, memory namespace and role should be explicit. Shared tools or repository context do not imply entity identity continuity.

### Feed reliability fallback changes epistemic source composition

`k29` fixes broken feeds partly by replacing primary/specialized feeds with HNRSS topic queries or different broad publishers.

**Transfer:** a source being available does not make it epistemically equivalent to the source it replaced. Preserve source identity, provenance, authority and aggregation bias through fallbacks.

### API topology needs executable contracts

`k22`, `k30` and `k31` show request-body binding and route-prefix/proxy errors that broke otherwise straightforward functionality.

**Transfer:** generate or contract-test request schemas, route prefixes and proxies across client, WebUI and backing service boundaries.

## Negative results preserved

- project sandbox was removed in favor of near-full host authority plus a tiny blacklist;
- model output could rewrite the same file treated as future base-of-truth;
- generated markdown entered HTML rendering without an explicit escaping stage in the shown code;
- streaming/tool functionality was initially only structurally verified due unavailable live API testing;
- request binding and duplicated/missing API prefixes broke endpoints;
- RSS fallbacks changed source identity and epistemic composition.

## Evidence and credit boundary

No source-reported model/LoRA iteration, benchmark, uptime or performance value was independently reproduced. No avoided-hours value is added because row-level conceptual overlap against the historical earned-work ledger was not audited.

Global Level-0 exact percentage remains unchanged because the combined obligation denominator remains `NOT_FROZEN`. `666_RELEASE_GATE` remains `NOT_PASS`.

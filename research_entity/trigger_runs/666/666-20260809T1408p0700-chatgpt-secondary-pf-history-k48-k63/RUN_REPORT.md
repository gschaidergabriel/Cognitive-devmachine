# 666 Level-0 Run Report — Project-Frankenstein History k48..k63

## Run identity

- Trigger: `666`
- Actor: `chatgpt-secondary`
- Stage: `L0_ARCHIVE_ASSIMILATION`
- Frozen head: `abba90a5767d85abc8a1ac340bae92842dab35c1`
- Exact ordinal shard: `k48..k63`
- Materialized and terminally dispositioned: `16/16`
- Winning claim: `18dfa1d1170440cdcf1e0a47589732cd86b40ab8`
- Race status: clean after full materialization.
- Runtime reproduction: not performed; evidence class is historical Git commit/diff/document lineage.

## Main findings

### Tool execution metadata must survive until after authority and dispatch

The strongest negative lineage is `k57 -> k54`. A response-cleaning layer stripped `<tool>` tags before the dispatcher could parse them. That looked like a safety/output-hygiene improvement but disabled all legitimate tool execution. The later revision explicitly moved tool-tag stripping after dispatch.

**Transfer:** make the pipeline typed and ordered: model output -> parse structured calls -> validate authority/policy -> execute -> capture typed result -> sanitize/render user-visible output. Presentation cleaners must never destroy unprocessed execution metadata.

### Output cleaners and governors are causal co-authors

`k48`, `k52` and `k57` contain multiple transformations after model generation: identity correction, hardware/project leak stripping, PDF/tool/memory cleanup, role-label removal, safety prefilters, tool-result dedup and frontend consciousness-stream cleaning.

**Transfer:** these layers materially determine what the user observes. They need provenance and tests for false-positive deletion, semantic distortion and ordering interactions rather than being treated as neutral formatting.

### Explicit actuation can be safer than continuous sensing

`k51` removed continuous conversation/listening mode and retained push-to-talk only, with a minimum capture duration to reject accidental clicks.

**Transfer:** where a sensor can trigger expensive or high-authority cognition, explicit user actuation plus minimum evidence windows can be a robust operational mode when autonomous activation has high false-trigger cost.

### OCR and generative visual interpretation are different evidence classes

`k52-k54` split image use into explicit Transcribe (OCR) versus Describe (FrankEye + generative interpretation) modes.

**Transfer:** preserve extracted text and generative scene interpretation separately, with different provenance and uncertainty. They should not collapse into one undifferentiated "vision result".

### Context engineering helps small models but state isolation still matters

`k59` added plan refresh, scratch offload and goal-based tool filtering to keep a 3B agent focused. Large tool outputs are moved out of active context and a summary remains. The shown `_SCRATCHPAD` is a module-global dictionary despite the design language calling it session-scoped.

**Transfer:** plan recitation, scratch offload and dynamic tool filtering are useful attention controls, but scratch/context storage must be explicitly namespaced and concurrency-tested before multi-session use.

### Remote messaging ingress is an authority boundary

`k61` added Telegram and WhatsApp bridges with per-user session IDs and optional whitelists. Empty whitelist means allow all senders.

**Transfer:** session isolation is not authentication. External ingress into a chat surface capable of tool use should require explicit authentication/capability scope and fail-closed configuration rather than public-by-omission defaults.

### Evidence and architecture labels were explicitly downgraded/reconciled

`k60` renamed repository "Research Papers" to non-peer-reviewed "Technical Notes & Design Documents". `k56` clarified bio-inspired subsystem names as engineering metaphors, not sentience claims. `k62-k63` removed dead Genesis descriptions and reconciled architecture docs to the then-current Qwen/WebUI/Swarm/FrankEye topology.

**Transfer:** evidence class, phenomenal interpretation, current topology and historical provenance are independent axes. Preserve each explicitly.

## Negative results preserved

- tool sanitization blocked legitimate execution when ordered before dispatch;
- continuous voice mode was removed after reliability/false-trigger concerns;
- stale browser client code caused API-version mismatch during image-upload changes;
- internal tool/directive/recent-life metadata leaked into visible output surfaces;
- a scratch store described as session-scoped lacked explicit session namespacing in the shown implementation;
- external messaging bridges defaulted to allow-all if a whitelist was absent;
- current architecture documentation retained dead/outdated topology until explicit cleanup.

## Evidence and credit boundary

No source-reported benchmark, latency, neural parameter, fix-count or safety-test figure was independently reproduced. No new avoided-hours value is assigned because row-level conceptual overlap against the historical earned-work ledger was not audited.

The global Level-0 exact percentage remains unchanged because the combined obligation denominator remains `NOT_FROZEN`. `666_RELEASE_GATE` remains `NOT_PASS`.

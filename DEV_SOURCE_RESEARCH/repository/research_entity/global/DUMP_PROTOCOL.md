# RAE DUMP PROTOCOL — PROJECT-WIDE RESEARCH INTAKE

## Trigger

A user message whose trimmed, case-insensitive content is exactly:

`dump`

is a reserved project command.

When the command is visible to a project worker, do not answer with a generic acknowledgement and do not ask what `dump` means. Execute this protocol immediately, subject only to real tool/runtime limits.

Claude Code is `claude-code-lead`; ChatGPT is `chatgpt-secondary`. Both operate on the same Research Entity.

## Directories

- input queue: `dump/`
- successful immutable archive: `dump archive/<batch_id>/`
- durable source archive / derived research structures: `research_sources/`

Files such as README/.gitkeep are control files and are not payload.

## Epistemic class

Dump material is intentionally permissive intake. It may contain facts, speculation, old reports, generated text, code, screenshots, raw measurements, false claims or mixed-quality material.

Therefore raw dump material NEVER becomes CURRENT/evident knowledge merely because it was supplied.

Default classification for derived propositions:

- status: `OPEN`
- origin_class: `DUMP`
- epistemic_class: `DUMP_DERIVED_PREPROCESSED_HYPOTHESIS`
- promotion_allowed_without_independent_support: `false`

The dump can have strong prior support after preprocessing, but that support must remain distinguishable from independently reproduced measurements, primary literature or verified runtime evidence.

## Required pipeline

### D0 — Join and freeze input

1. Perform normal RAE fast boot and actor identification.
2. Enumerate all payload files currently in `dump/` plus any files explicitly attached to the current session as the dump batch.
3. Compute SHA-256 and size for every payload before analysis.
4. Create `batch_id = dump-YYYYMMDDTHHMMSSZ-<shortroot>`.
5. Write a batch manifest containing file names, hashes, source/supplier, actor, session/run id and canonical parent revision/hash.
6. Never modify raw input bytes during analysis.

### D1 — Extract and normalize

1. Extract text/metadata from supported text, code, PDF, archive and structured-data formats.
2. Preserve exact raw bytes or an exact content-addressed reference.
3. Deduplicate by content hash, not file name.
4. Preserve document/page/path/member provenance for every extracted fragment.
5. Detect likely secrets/credentials and exclude them from research text/remote publication.

### D2 — Surgical knowledge decomposition

Convert useful content into the smallest independently retrievable semantic units that preserve meaning.

Preferred unit:

- one proposition/mechanism/result/constraint per micro-packet;
- provenance pointer;
- date/version/scope;
- epistemic class;
- uncertainty;
- relations to predecessor/superseding/refuting claims when known.

Do not compress several distinct empirical claims into one opaque summary merely to save tokens.

Materialize:

`research_sources/micro_packets/<topic>/<packet_id>.json`

A micro-packet should normally be small enough to retrieve surgically without loading a whole source document.

### D3 — Fuse with compressed current research state

1. Query current RAE knowledge through the active query plane/context compiler.
2. Load relevant CURRENT, OPEN, SUPERSEDED, REFUTED and NEGATIVE_RESULT micro-/topic packets.
3. Compare dump-derived content against current knowledge.
4. Record agreements, contradictions, novelty, version drift, duplicated ideas and unresolved conflicts.
5. Never let recency or verbosity override canonical lineage.

### D4 — Hypothesis generation

Generate falsifiable first-pass hypotheses and counterhypotheses from the fused state.

Each hypothesis must include:

- hypothesis id;
- mechanism;
- supporting dump packets;
- relevant existing RAE packets;
- counterhypothesis;
- falsifier / discriminating observation;
- uncertainty;
- domains/topics touched.

These remain `DUMP_DERIVED_PREPROCESSED_HYPOTHESIS` until independently supported.

### D5 — Hypothesis-guided external research

For every meaningful hypothesis cluster, research all touched topics as efficiently as possible across:

1. arXiv / primary papers and authoritative technical sources;
2. GitHub repositories, code, issues, PRs and implementation evidence;
3. Reddit discussions for field experience, failure reports and community observations.

Use Reddit as anecdotal/field evidence unless independently corroborated. Prefer primary papers and executable/inspectable implementations for stronger claims.

Search is hypothesis-guided; do not perform indiscriminate web collection.

Record source metadata and which hypothesis/query caused each source to be retrieved.

### D6 — Second fusion and pattern matching

Fuse:

- raw dump-derived micro-packets;
- current compressed RAE state;
- external research;
- negative results;
- contradictions;
- implementation/runtime evidence.

Then perform cross-domain pattern matching, mechanism comparison, causal alternatives and boundary-condition analysis.

Generate a second hypothesis generation where justified. Explicitly record which first-pass hypotheses were strengthened, weakened, split, superseded or refuted.

### D7 — Topic package materialization

Create/update two retrieval layers:

1. `micro_packets/` — smallest surgical semantic units;
2. `topic_packets/` — compact higher-level research assemblies linking relevant micro-packets.

Each topic packet should contain:

- compact current synthesis;
- CURRENT claims;
- OPEN hypotheses;
- SUPERSEDED/REFUTED warnings;
- critical negative results;
- strongest evidence refs;
- dump-derived hypotheses with explicit origin metadata;
- external corroboration/counterevidence;
- active experiments / best next falsifiers;
- dependencies to other packets.

### D8 — Weave into active research

Update the Research Entity only through normal claim/event/provenance/promotion mechanisms.

Rules:

- dump-only proposition -> OPEN hypothesis, never CURRENT;
- independent external support may strengthen an OPEN claim but does not automatically prove it;
- reproduced project/runtime measurement can justify stronger status via the normal Promotion Gate;
- contradictory prior evidence remains visible;
- negative results are preserved.

### D9 — Completion and archive

The dump batch is complete only if:

- all payload files have pre-analysis hashes;
- extraction/provenance succeeded or failures are explicitly recorded;
- micro-packets/topic packets were materialized for useful content;
- hypotheses and external research were fused;
- RAE events/provenance were written or marked SYNC_PENDING;
- validation passes;
- original bytes can be matched to the manifest.

Only then move the original payload from `dump/` to:

`dump archive/<batch_id>/original/`

and write:

- `MANIFEST.json`
- `DUMP_RESULT.json`
- `RESEARCH_DELTA.md`

The original SHA-256 values must still match after the move.

If any critical step fails, leave the affected files in `dump/`, write a failure receipt and do NOT claim the batch was completed.

## ChatGPT Project behavior

If a ChatGPT Project session receives the exact command `dump`:

1. treat files visible in the project's `dump` source area and files attached to the current conversation for this purpose as the input batch;
2. use the connected GitHub RAE backend when available;
3. perform web research with available web/deep-research capabilities;
4. if physical file move inside the ChatGPT product is impossible, archive exact bytes/results to the GitHub `dump archive` structure where tools permit and mark any UI-source move as `PRODUCT_MOVE_UNAVAILABLE`, never silently pretend it happened;
5. continue all research work that is possible instead of asking the user to restate this protocol.

## Claude Code behavior

The `UserPromptSubmit` hook must recognize exact `dump` and inject this protocol plus a local queue manifest. Claude should then execute the full research cycle. Local filesystem moves and Git writes are available there and should be verified.

## Final user response

After completion, report compactly:

- batch id;
- files processed / failed / deduplicated;
- micro-packets and topic packets created/updated;
- hypotheses generated and their status changes;
- external sources screened/used by class;
- important contradictions/novel patterns;
- archive result;
- research-state write/verification result.

Do not expose hidden chain-of-thought; expose reproducible research summaries, evidence and decision traces.

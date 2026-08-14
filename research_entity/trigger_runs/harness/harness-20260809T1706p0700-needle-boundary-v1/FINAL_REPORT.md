# Harness Run — H-WP-04 Needle Boundary V1

Run: `harness-20260809T1706p0700-needle-boundary-v1`  
Actor: `chatgpt-secondary` / OpenAI GPT-5.6 Sol  
Canonical parent: r2 `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Work package: `H-WP-04-NEEDLE-BOUNDARY`  
Promotion: NONE  
Stage advancement: NONE

## Result

A deterministic, stdlib-only Reference-Harness boundary kernel was implemented for the fixed project law:

`Clay CapabilityRegistry`
`-> deterministic NeedleProjectionV1`
`-> Needle inference (untrusted)`
`-> strict post-decode validation`
`-> provenance-bound ClayToolProposal`
`-> separate Safe-Effect/capability/owner-authority revalidation`

The new artifact is:

- `research_entity/harness/reference/needle_boundary_v1.py`

with regression tests:

- `research_entity/harness/tests/test_needle_boundary_v1.py`

The implementation is intentionally host-language during BASE. It does not claim H1 completion and does not redesign Needle.

## Why this work package was selected

The live Harness reread showed:

- H-WP-02 State Ledger already has active executable work and recent identity refinements;
- H-WP-11 Trace/Replay has a sibling live claim and a new `TurnTraceEnvelope` validator/differential oracle;
- the shared Harness workspace still listed H-WP-04 as OPEN;
- existing Project-Frankenstein/Needle archaeology had already identified concrete fail-open and schema/provenance hazards but no current deterministic adapter kernel existed at the selected path.

Therefore this run avoided duplicating WP02/WP11 and converted the archived Needle source negative oracles into executable current-Harness boundary semantics.

## Internal evidence used

Primary:

- `research_entity/frank/NEEDLE_CLAY_BOUNDARY_SANDBOX_DELTA.md`
- `research_entity/harness/fixtures/NEEDLE_SOURCE_SANDBOX_ORACLES.json`
- `research_entity/harness/HARNESS_WORKSPACE.json`
- `research_entity/triggers/HARNESS_BUILD_PROTOCOL.md`
- current canonical/project command/program state
- current whole-mesh live fusion through 17:04 plus post-fusion live Harness/ClayCode commits

The implementation specifically operationalizes archived NSO classes:

- normalization collision;
- flat projection schema mismatch;
- duplicate/unknown/missing/wrong-typed arguments;
- decoder constraint exhaustion/off-trie fail-open indicators;
- exact registry/source/model/tokenizer/input/language provenance;
- Needle route output never minting effect authority.

## Implemented contract

### Deterministic projection

`build_projection()`:

- omits unavailable or locked capabilities before inference;
- uses stable `capability_id` as semantic identity;
- normalizes transport names only as aliases;
- rejects non-injective normalized-name collisions;
- validates the admitted flat parameter schema;
- emits stable sorted projection order;
- hashes the semantic registry independent of source list order;
- retains a reverse map from Needle alias back to Clay capability identity.

### Strict decode boundary

`validate_route()`:

- rejects decoder `constraint_exhausted` and `off_trie` receipts;
- requires an explicitly trustworthy decoder status;
- rejects malformed JSON and duplicate keys;
- rejects unknown top-level fields, unknown tools and unavailable/locked tools;
- rejects unknown/missing arguments;
- validates scalar/container type, enum and numeric range constraints;
- checks source/model/tokenizer/registry/projection/input/language provenance;
- creates only a `ClayToolProposal`;
- returns `authority = NONE`;
- returns `effect_permit = null`;
- returns `effect_commit_allowed = false`;
- names the separate next boundary as Safe-Effect/capability/owner-authority revalidation.

## Executed tests

Evidence class: local deterministic tests plus synthetic mutation stress, not live FRANK evidence.

Unit/regression suite:

- 12 tests executed;
- 12 passed;
- 0 failed;
- 0 errors.

Stress:

- 10,000 registry-order permutations;
- 0 semantic registry-hash order failures;
- 5,000 malformed/adversarial/unauthorized route attempts;
- 0 unexpected accepts;
- valid route still produced `authority = NONE` and no effect permit.

## Hypothesis matrix

### H-NB-01 — deterministic projection identity

Hypothesis: semantically identical capability registries differing only in source list order can produce one stable Needle projection identity.

Test: 10,000 order permutations.

Result: supported in the tested kernel; 0 order-invariance failures.

Falsifier: an admitted capability/schema feature whose semantics require order and cannot be canonicalized without information loss.

### H-NB-02 — archived Needle fail-open classes can be contained at the bridge

Hypothesis: known historical decoder/schema hazards need not grant unsafe routing if every Needle result is treated as untrusted and strictly post-validated.

Test: duplicate keys, unknown fields/tools/args, missing required args, type/range errors, locked capability, off-trie and constraint exhaustion.

Result: supported for the tested boundary classes; all were rejected before proposal acceptance.

Counterhypothesis: an exact tokenizer/model path may emit a semantic ambiguity not represented by the current adapter schema. This remains OPEN pending exact model/tokenizer execution.

### H-NB-03 — proposal/effect authority separation is mechanically enforceable

Hypothesis: Needle can remain FRANK's sole intentional non-Clay semantic/reflex subsystem without gaining effect authority.

Test: valid route generation and adversarial route fields.

Result: supported at the boundary kernel. Output contains no effect permit and cannot set authority through decoded JSON.

Falsifier: a downstream integration that bypasses the separate Safe-Effect/capability/owner-authority gate or treats `ClayToolProposal` as execution authorization.

## Negative/counterevidence preserved

No archived negative result was erased.

Still OPEN:

1. real-tokenizer reachability of the historical constrained-token quote-suffix bypass family;
2. exact 51-tool token-budget/truncation behavior;
3. route invariance under exact tokenizer/model across registry order permutations;
4. German-direct versus translated I/O accuracy;
5. historical JAX versus current Cactus/SafeTensors runtime differential;
6. translator ingress receipts;
7. integration with the real Safe-Effect commit gate;
8. live Ubuntu FRANK runtime evidence.

Therefore H-WP-04 is materially advanced but not complete.

## Cross-branch implications

- **FRANK:** freeze `NeedleProjectionV1` only after exact tokenizer/model measurements; proposal remains non-authoritative.
- **ClayCode:** H2 must reproduce this proposal/provenance/authority separation representation-independently; do not invent FRANK-specific syntax without an executable counterexample.
- **ClayGraph:** route/proposal edges must remain distinct from permit/commit/effect edges.
- **UnifiedDB:** persist/query route identity and provenance without conflating proposal with effect.
- **Clay/GWT/Hyperposition/Emergenz:** no new truth/emergence claim; this is a safety/architecture execution result only.

## Highest-information next tests

1. execute exact pinned Needle tokenizer/model bundle against NSO-001/002/003;
2. tokenize the exact active 51-tool minimal projection and measure retained coverage/order sensitivity;
3. run registry mutation and normalized-name collision corpus against the exact runtime;
4. benchmark German-direct vs translated language paths;
5. integrate translator ingress receipt and Safe-Effect downstream revalidation into one end-to-end boundary trace;
6. add the boundary events to `TurnTraceEnvelope` and per-run ClayGraph once sibling WP11 contracts stabilize;
7. preserve H1 as blocked until BASE ClayCode release and then rerun the identical boundary corpus on the Ubuntu developer target.

## Completion state

`H-WP-04-NEEDLE-BOUNDARY = PARTIAL_EXECUTABLE_FOUNDATION`

This run completed the deterministic projection/post-decode safety kernel and its local executable evidence. It did not complete the exact tokenizer/model, translator, Safe-Effect integration or live-H1 gates.

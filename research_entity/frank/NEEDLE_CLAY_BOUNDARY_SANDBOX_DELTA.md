# Needle ↔ Clay Boundary — Sandbox Architecture Delta

**Status:** IMPLEMENTATION/HARNESS DIRECTIVE CANDIDATE derived from source-level sandbox evidence  
**Needle source under test:** `cactus-compute/needle@6fdddb874dd6f46dabeea88d0bf239fc4a2474c4`  
**Current fixed authority:** `research_entity/global/FRANK_CLAY_NATIVE_CONTRACT.md`

## Result

The newly supplied full Needle source is useful and should be retained as an executable architecture fixture. It closes the prior source-inspection gap, but it must not be embedded into FRANK as a trusted direct executor.

The target boundary is:

`Clay CapabilityRegistry`
`-> deterministic NeedleProjection(schema_version, registry_hash)`
`-> Needle inference`
`-> untrusted NeedleRawRoute`
`-> deterministic strict validator`
`-> Clay ToolProposal / RouteObservation + provenance`
`-> Safe-Effect / capability / owner-authority gate`
`-> effect`
`-> Clay EffectReceipt`

Needle selects/proposes. Needle never authorizes or commits effects.

## Projection contract

For the historical JAX source at `6fdddb8`, the projection must be explicit and versioned because its constrained decoder expects the repository's flat tool format rather than arbitrary provider JSON Schema.

A projection must:

1. omit unavailable/locked capabilities before inference;
2. preserve one stable semantic identity per capability;
3. reject name-normalization collisions rather than silently overwriting them;
4. emit only the schema dialect validated for the pinned Needle runtime;
5. retain a reverse map to the original Clay capability identity;
6. bind `source_commit`, `model_hash`, `tokenizer_hash`, `registry_hash`, `projection_schema`, `input_hash` and language path to every result;
7. deterministically validate the complete decoded structure before creating a Clay proposal.

## Post-decode validator

The validator is mandatory even when constrained decoding is enabled. It must reject:

- unknown tool names;
- duplicate JSON keys;
- normalization collisions;
- unknown argument keys;
- missing required arguments;
- wrong scalar/container types;
- invalid enum/range/format constraints;
- excessive call count;
- malformed JSON;
- any output produced after constraint exhaustion/off-trie fallback;
- capability identities not present in the exact projected registry.

Invalid output becomes `ABSTAIN`/`ESCALATE`, never unconstrained execution.

## Registry-size strategy

The archived FRANK registry has 51 active tools. A verbose projection is ~11.9k characters, while a minimal name+typed-argument projection is ~3.5k characters. The historical Needle encoder truncates the tool token sequence from the tail under a fixed 1024-token encoder budget.

Therefore:

1. exact-tokenizer measurement is mandatory before selecting a projection;
2. use the smallest semantically adequate projection rather than verbose prose;
3. randomize/order-perturb during evaluation to expose positional bias;
4. PASS requires route invariance under semantically equivalent registry orderings;
5. if the complete registry still does not fit, use a tested Needle-only hierarchy/tournament over bounded registry partitions, with a final Needle selection over survivors, rather than delegating semantic routing back to the 4B model;
6. partition/tournament orchestration is deterministic and carries full candidate provenance.

The multi-stage design is an implementation candidate until measured against a single-pass full-registry baseline.

## Uncertainty / escalation

Aggregate tool-choice accuracy is insufficient. Measure separately:

- reflex/deterministic tools;
- ambiguous semantic-choice tools;
- delegation/escalation tools;
- no-tool/abstention cases;
- registry mutation/OOD tools;
- German direct input vs explicit I/O translation path;
- adversarial descriptions/names;
- tool-order permutations;
- constrained-decoder exhaustion/off-trie cases.

Where logits are accessible, record margin/entropy-like route uncertainty as observation only; calibrate against held-out outcomes before using thresholds.

## Artifact safety

The pinned JAX source force-downloads an unpinned `needle.pkl` in finetuning and deserializes checkpoints with Python pickle. This path is forbidden inside the final authority zone.

Preferred production lane:

`immutable upstream revision + expected content hash + SafeTensors/Cactus bundle -> isolated verified load -> runtime`

A legacy pickle may only enter an isolated conversion/reproduction lane after an independently known hash is verified. Network-fetched pickle must never be treated as trusted executable model state merely because it came from the expected repository name.

## Source-level negative oracles found

See `research_entity/harness/fixtures/NEEDLE_SOURCE_SANDBOX_ORACLES.json`.

High-value cases include:

- constrained token suffix crossing a closing quote can become off-trie and then fail open under a synthetic token table; real-tokenizer reachability remains to be exhaustively tested;
- no-valid-token/off-trie paths return unconstrained logits in the historical source;
- normalization is non-injective and last-write-wins;
- flat-vs-JSON-Schema dialect mismatch;
- argument values/required semantics are not decoder-enforced;
- order-sensitive tail truncation of registry context;
- unknown config keys silently disappear;
- unpinned pickle deserialization in the legacy JAX path.

## What is already positive

The source is not being rejected. Several properties are useful:

- dynamic tool lists are first-class input;
- tool and argument names can be grammar constrained;
- nested argument values are separated from key constraints by the state machine;
- the model is small enough to make dedicated routing plausible;
- the current upstream provides SafeTensors and a Cactus runtime path, which is a better production substrate than the historical Python-pickle lane.

## Next executable gate

When the exact tokenizer/model bundle is available in the test runtime:

1. enumerate every tokenizer piece against the constrained-state automaton;
2. prove or falsify reachability of the synthetic quote-suffix bypass family;
3. tokenize the exact 51-tool minimal and verbose projections and measure retained tool coverage;
4. run order-permutation and registry-mutation tests;
5. benchmark German-direct vs translated I/O paths;
6. measure route accuracy by function class plus abstention;
7. compare JAX historical snapshot against current Cactus/SafeTensors runtime;
8. only then freeze `NeedleProjectionV1` and the production runtime choice.

No paid training is required for these gates.

# MINI_ENTITY_COGNITIVE_FABRIC_ADMISSION/v1

Status: CURRENT SOURCE CONTRACT CANDIDATE  
Scope: the single canonical `pipeline_cognitive_fabric_admit` boundary between `pipeline_build_prompt` and `inference_generate`.

## Purpose

The canonical Mini Entity pipeline MUST traverse one Unified Cognitive Fabric admission boundary before any targeted inference engine is invoked. This boundary composes already-admitted Mini Entity context, J-Space/GWT measurements and inference routing into one candidate-inference envelope without creating a second state, truth, effect, identity or recovery authority.

MiniUnifiedDB remains canonical durable authority. Zero supplies runtime identity/configuration. J-Space/GWT/model/Claude outputs are measurement or candidate inference only.

## Causal position

```text
pipeline_compile
-> pipeline_build_prompt
-> pipeline_cognitive_fabric_admit
-> inference_generate
-> pipeline_gate
-> pipeline_commit
```

Any path from `pipeline_build_prompt` to `inference_generate` that does not pass exactly one successful `pipeline_cognitive_fabric_admit` is non-canonical and MUST fail closed.

## Input envelope

The effect receives the ordinary phase envelope:

```text
entity_db   = canonical MiniUnifiedDB path/reference
source_db   = current source/evidence DB path/reference
profile     = active DB-resident profile
previous    = current canonical generation/continuity state
data.compiled = exact current compiled canonical state + packet identities
data.prompt   = exact current immutable-guarded prompt candidate
```

Required source-side identity anchors before admission:

- `previous.generation` is present and integer-valued;
- `compiled.canonical_state_hash` is a lowercase 64-hex digest;
- `compiled.packet_hash` is a lowercase 64-hex digest;
- the prompt candidate is produced from those exact compiled bytes/values;
- the active profile is the same DB-resident profile used for this turn;
- no hidden second transcript or memory authority is consulted as canonical truth.

## Required success envelope

A successful implementation returns:

```text
ok = true
schema = "mini-entity-cognitive-fabric-admission/v1"
generation = previous.generation
canonical_state_hash = compiled.canonical_state_hash
packet_hash = compiled.packet_hash
inference_packet_digest = sha256(exact admitted InferencePacket bytes)
cognitive_fabric_receipt_digest = sha256(exact admission receipt bytes)
inference = admitted candidate inference engine/profile
system = admitted system context
user = admitted user/context payload
```

Both digest fields MUST be lowercase 64-hex, non-placeholder identities and MUST bind the exact bytes actually passed downstream. A stable label, profile name, model name, J-Space profile or GWT configuration is never a substitute for exact packet/receipt identity.

`inference`, `system` and `user` are candidate-inference inputs only. They cannot write MiniUnifiedDB, grant EffectGate authority, mint verified evidence, resolve Hyperposition by assertion or promote J-Space/GWT/model output to canonical truth.

## Required receipt ancestry

The exact admission receipt MUST bind at least:

- admission schema/version;
- current generation;
- canonical state hash;
- source packet hash;
- active profile identity/hash where available;
- exact workspace/capsule identity used for the turn, or explicit `UNKNOWN/UNMEASURED` when no admitted workspace artifact exists;
- exact J-Space/lens/workspace calibration identities when used, never guessed defaults;
- selected inference engine kind/model/runtime identity as available;
- exact InferencePacket digest;
- origin/trigger identity when available;
- authority statement: `CANDIDATE_INFERENCE_ONLY`;
- no-effect statement: the admission itself did not execute a real/state-changing effect.

If an identity required by the chosen route is unavailable, malformed, stale or cross-bundle inconsistent, admission fails closed. `UNKNOWN` remains `UNKNOWN`; it must not be replaced with a plausible digest, slot count, layer, band or model identity.

## Generation and replay fence

Admission is turn/generation scoped.

- `generation` MUST equal the `previous.generation` observed by this canonical turn.
- A stale admission envelope MUST NOT be reused after generation advance or restart/recovery fencing.
- Replay may reproduce a prior candidate for analysis, but it MUST carry the original request/packet identity and MUST NOT become a new canonical commit without passing current generation/CAS gates.
- `pipeline_commit` remains the canonical durable write boundary; Cognitive Fabric admission does not independently persist semantic truth.

## Inference routing law

The Cognitive Fabric MAY select among admitted replaceable inference engines according to current DB configuration and accepted routing evidence, including bundled ~0.8B cognition, Claude Code targeted inference, approved free API engines or loopback/local runners.

Routing MUST NOT:

- bypass `FREE_ONLY` or owner-gated paid-training rules;
- use Together API;
- expose provider secrets to model-visible context;
- silently switch to an unbound model/runtime artifact while retaining an old identity;
- make engine preference a truth-confidence score;
- grant an inference engine direct effect authority.

## J-Space / GWT law

J-Space and GWT participation is conditional on exact admitted measurement identity.

- unmeasured layer/band/slot/threshold/lens values remain `UNKNOWN/UNMEASURED`;
- model self-report is not hidden-state measurement;
- workspace recurrence/coherence is not consciousness or truth evidence;
- a valid boot-binding receipt is necessary provenance but not semantic usefulness proof;
- causal claims require a separate discriminating intervention/receipt at the appropriate exact bundle.

The admission boundary may carry J-Space/GWT-derived candidate context, but canonical claims are still decided by downstream evidence/gate/commit rules.

## Failure classes

At minimum fail closed on:

```text
MISSING_GENERATION
STALE_GENERATION
BAD_CANONICAL_STATE_HASH
BAD_PACKET_HASH
PROMPT_COMPILED_IDENTITY_MISMATCH
MISSING_OR_MALFORMED_INFERENCE_PACKET_DIGEST
MISSING_OR_MALFORMED_FABRIC_RECEIPT_DIGEST
PLACEHOLDER_DIGEST
UNBOUND_COGNITION_ARTIFACT
CROSS_BUNDLE_JSPACE_IDENTITY
UNMEASURED_VALUE_PROMOTED_TO_MEASURED
UNADMITTED_INFERENCE_ENGINE
AUTHORITY_ESCALATION
SECOND_STATE_AUTHORITY
EFFECT_PATH_BYPASS
```

A failure returns `ok = false` with a typed error and MUST occur before `inference_generate`.

## Downstream binding

`inference_generate` MUST receive only the admitted `inference/system/user` plus the exact `inference_packet_digest` and `cognitive_fabric_receipt_digest`.

`pipeline_gate` and `pipeline_commit` MUST receive the same admitted envelope/identities so a generated result cannot be detached from the Cognitive Fabric ancestry that produced it.

The canonical result SHOULD expose the packet and admission receipt digests for auditability, but exposure does not itself grant truth or runtime acceptance.

## Acceptance boundary

Source presence of this contract or the `.clay` call establishes no runtime credit.

Promotion requires an actually-started authorized isolated execution on exact changed bytes showing:

1. exactly one admission call before inference;
2. no raw prompt/profile bypass path;
3. exact generation/hash/packet/receipt cross-binding;
4. stale/malformed/placeholder identities fail closed;
5. admission failure prevents inference;
6. gate/commit receive the same admission identity;
7. restart/replay preserve generation and uncertainty fences;
8. no second MiniUnifiedDB/UCF/effect/recovery authority appears.

Bundled-0.8B runtime, J-Space runtime, Whole-GWT, Claude-adapter and whole Mini Entity acceptance remain separate gates.

# MINI_ENTITY_COGNITIVE_FABRIC_ADMISSION/v1

Status: **CURRENT PRE-INFERENCE SOURCE CONTRACT CANDIDATE**  
Scope: the single canonical `pipeline_cognitive_fabric_admit` boundary between `pipeline_build_prompt` and `inference_generate`.

This contract is deliberately distinct from `UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1`. The admission receipt is created **before inference** and is candidate/provenance evidence only. The final UCF runtime receipt is created only by post-turn `pipeline_cognitive_fabric_finalize` after the deterministic gate and MiniUnifiedDB terminal commit/no-commit outcome are known. The two receipts MUST NOT share a schema or digest identity.

## Purpose

The canonical Mini Entity pipeline MUST traverse one Unified Cognitive Fabric admission boundary before any targeted inference engine is invoked. This boundary composes already-admitted Mini Entity context, J-Space/GWT measurements and inference routing into one candidate-inference envelope without creating a second state, truth, effect, identity or recovery authority.

MiniUnifiedDB remains canonical durable authority. Zero supplies runtime identity/configuration. J-Space/GWT/model/Claude outputs are measurement or candidate inference only.

## Causal position

```text
pipeline_compile
-> pipeline_build_prompt
-> pipeline_cognitive_fabric_admit              # pre-inference admission/provenance only
-> inference_generate                            # candidate cognition only
-> pipeline_gate                                 # deterministic validation
-> pipeline_commit_or_explicit_no_commit         # MiniUnifiedDB authority
-> pipeline_cognitive_fabric_finalize            # post-turn UCF runtime evidence only
```

Any path from `pipeline_build_prompt` to `inference_generate` that does not pass exactly one successful `pipeline_cognitive_fabric_admit` is non-canonical and MUST fail closed.

Any final `UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1` emitted before the gate and terminal commit/no-commit outcome is non-causal and MUST fail closed, because its authority/execution fields cannot yet be observed truthfully.

## Input envelope

The admission effect receives the ordinary phase envelope:

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

## Required admission success envelope

A successful pre-inference implementation returns:

```text
ok = true
schema = "mini-entity-cognitive-fabric-admission/v1"
generation = previous.generation
canonical_state_hash = compiled.canonical_state_hash
packet_hash = compiled.packet_hash
inference_packet_digest = sha256(exact admitted InferencePacket bytes)
cognitive_fabric_receipt_digest = sha256(exact PRE-INFERENCE ADMISSION receipt bytes)
inference = admitted candidate inference engine/profile
system = admitted system context
user = admitted user/context payload
```

`cognitive_fabric_receipt_digest` in this schema names the **admission receipt digest only**. Downstream code SHOULD label that value `cognitive_fabric_admission_receipt_digest` at the engine boundary so it cannot be confused with the final UCF runtime receipt.

Both admission digest fields MUST be lowercase 64-hex, non-placeholder identities and MUST bind the exact bytes actually passed downstream. A stable label, profile name, model name, J-Space profile or GWT configuration is never a substitute for exact packet/admission identity.

`inference`, `system` and `user` are candidate-inference inputs only. They cannot write MiniUnifiedDB, grant EffectGate authority, mint verified evidence, resolve Hyperposition by assertion or promote J-Space/GWT/model output to canonical truth.

## Required admission receipt ancestry

The exact **pre-inference admission receipt** MUST bind at least:

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

It MUST NOT claim fields whose truth only exists later, including completed inference/result identity, final validation decision, canonical write committed, effect committed or terminal execution result.

If an identity required by the chosen route is unavailable, malformed, stale or cross-bundle inconsistent, admission fails closed. `UNKNOWN` remains `UNKNOWN`; it must not be replaced with a plausible digest, slot count, layer, band or model identity.

## Generation and replay fence

Admission is turn/generation scoped.

- `generation` MUST equal the `previous.generation` observed by this canonical turn.
- A stale admission envelope MUST NOT be reused after generation advance or restart/recovery fencing.
- Replay may reproduce a prior candidate for analysis, but it MUST carry the original request/packet identity and MUST NOT become a new canonical commit without passing current generation/CAS gates.
- `pipeline_commit` remains the canonical durable write boundary; Cognitive Fabric admission does not independently persist semantic truth.
- post-turn finalization MUST bind the same admission identity and exact observed terminal turn outcome; it MUST NOT execute a second canonical commit or effect.

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

At minimum admission fails closed on:

```text
MISSING_GENERATION
STALE_GENERATION
BAD_CANONICAL_STATE_HASH
BAD_PACKET_HASH
PROMPT_COMPILED_IDENTITY_MISMATCH
MISSING_OR_MALFORMED_INFERENCE_PACKET_DIGEST
MISSING_OR_MALFORMED_ADMISSION_RECEIPT_DIGEST
PLACEHOLDER_DIGEST
UNBOUND_COGNITION_ARTIFACT
CROSS_BUNDLE_JSPACE_IDENTITY
UNMEASURED_VALUE_PROMOTED_TO_MEASURED
UNADMITTED_INFERENCE_ENGINE
AUTHORITY_ESCALATION
SECOND_STATE_AUTHORITY
EFFECT_PATH_BYPASS
PREINFERENCE_FINAL_RUNTIME_RECEIPT_CLAIM
```

Post-turn finalization additionally fails closed on terminal ancestry errors such as:

```text
FINAL_RECEIPT_BEFORE_TERMINAL_OUTCOME
ADMISSION_PACKET_IDENTITY_DRIFT
CANDIDATE_RESULT_IDENTITY_DRIFT
GATE_DECISION_IDENTITY_DRIFT
COMMIT_OUTCOME_IDENTITY_DRIFT
STALE_GENERATION_AT_FINALIZATION
SECOND_COMMIT_OR_EFFECT_ATTEMPT
```

An admission failure returns `ok = false` with a typed error and MUST occur before `inference_generate`.

## Downstream and finalization binding

`inference_generate` MUST receive only the admitted `inference/system/user` plus exact `inference_packet_digest` and the **pre-inference admission receipt digest**. It MUST NOT receive a purported final UCF runtime receipt digest.

`pipeline_gate` and `pipeline_commit` MUST receive the same admitted envelope/identities so a generated result cannot be detached from the Cognitive Fabric ancestry that produced it.

After gate and terminal commit/no-commit state exist, `pipeline_cognitive_fabric_finalize` MUST cross-bind at least:

- the exact admission receipt and InferencePacket identities;
- the exact candidate result identity;
- deterministic gate/validation decision;
- observed MiniUnifiedDB canonical write outcome;
- observed EffectGate outcome or explicit no-effect state;
- terminal execution/result identity;
- generation/source/runtime identities required by `UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1`.

Only that post-turn finalizer may expose the final `ucf_runtime_receipt_digest`. The canonical result SHOULD expose both admission and final runtime receipt digests under distinct names for auditability, but exposure does not itself grant truth or runtime acceptance.

## Acceptance boundary

Source presence of this contract or the `.clay` calls establishes no runtime credit.

Promotion requires an actually-started authorized isolated execution on exact changed bytes showing:

1. exactly one admission call before inference;
2. no raw prompt/profile bypass path;
3. exact generation/hash/packet/admission cross-binding;
4. stale/malformed/placeholder identities fail closed;
5. admission failure prevents inference;
6. gate/commit receive the same admission identity;
7. final UCF runtime receipt occurs only after terminal gate/commit state and binds the exact same turn ancestry;
8. a pre-commit final-runtime-receipt poison fails closed;
9. restart/replay preserve generation and uncertainty fences;
10. finalization does not create a second commit/effect path;
11. no second MiniUnifiedDB/UCF/effect/recovery authority appears.

Bundled-0.8B runtime, J-Space runtime, Whole-GWT, Claude-adapter and whole Mini Entity acceptance remain separate gates.

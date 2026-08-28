# Xeno Harness v1 — acceptance contract

Status: ACTIVE BUILD TARGET
Date: 2026-08-24

Xeno is the implementation codename for the shippable EntityOS/HCU module. This contract defines what the first genuinely finished Xeno must be able to do before `XENO_V1_ACCEPTED` may be minted.

## 1. Required runtime modes

A finished Xeno MUST support all of the following without resetting canonical state:

1. **Bundled-core mode** — specialized local ~0.8B core enabled and selected as `CORE`.
2. **External-core mode** — bundled ~0.8B disabled; an external/local arbitrary LLM profile selected as `CORE` through the adaptive engine fabric.
3. **Core + prestage mode** — one engine/profile is `PRESTAGE`, a different engine/profile is `CORE`; prestage output becomes typed candidate/context input to the core path and never canonical truth by itself.
4. **Core-only mode** — prestage disabled; selected core receives the admitted task directly.
5. **Deterministic/no-model mode** where the scheduler proves model inference is unnecessary.

Turning the internal ~0.8B core OFF MUST NOT disable canonical state, Typed Entry, deterministic routing, recovery, EffectGate/EffectJournal, dashboard configuration or peer connectivity. It only removes that local cognition engine from the available engine set.

## 2. Two persistent external LLM slots

The harness exposes at most two user-configurable external slots:

- `slot1`
- `slot2`

Each slot stores only non-secret configuration in EntityOS state and stores the credential itself in an OS-backed/encrypted secret store behind an opaque `secret_ref`.

The ordinary workflow is:

```text
user enters token/credential
 -> secret store persists credential
 -> EntityOS stores secret_ref only
 -> capability probe/profile binding
 -> slot becomes selectable in dashboard
```

The dashboard lets the owner assign:

- one available engine as `CORE`;
- optionally one distinct external slot as `PRESTAGE`;
- `PRESTAGE ON/OFF` independently;
- bundled internal ~0.8B `ON/OFF` independently.

With two external slots configured, either slot may become `CORE` and the other may become `PRESTAGE`. With only one external slot, it may be the external `CORE` or `PRESTAGE` while the internal ~0.8B remains core. An unavailable/disabled selected engine fails closed with a typed configuration/runtime error; there is no silent paid or unrelated fallback.

Persisted harness state MUST validate through `tools/xeno_harness_config.py`.

## 3. Arbitrary LLM attachment

"Any LLM" means broad adapter coverage plus extensible generic adapters, not false universal hidden-state support.

Required adapter families:

- Claude Code / Anthropic first-class adapter;
- OpenAI native;
- generic OpenAI-compatible endpoint;
- Gemini;
- Mistral;
- Groq;
- NVIDIA NIM;
- OpenRouter;
- Ollama;
- llama.cpp;
- vLLM;
- Hugging Face/TGI;
- local executable runner;
- generic custom HTTP/JSON adapter.

A new backend MUST be addable as profile/adapter configuration without MiniUnifiedDB reset or architecture fork.

Closed APIs use `COMPILED_EXTERNAL` or `PLAIN_COMPATIBILITY` J-Space modes. Hookable local models may use `FULL_LOCAL_LATENT` or `LOCAL_OBSERVE_ONLY`. Xeno MUST never pretend that an API exposes hidden activations when it does not.

## 4. Zero-like two-stage harness behavior

The two-stage path is conceptually:

```text
Typed Entry
 -> optional PRESTAGE engine
 -> typed PrestageResult + provenance + limits
 -> Xeno workspace / Global J-Space compilation
 -> CORE engine
 -> typed CoreResult
 -> HCU validation/reconciliation
 -> canonical write/effect request only through existing deterministic gates
```

This is sufficient to reproduce the useful *shape* of a Zero-style "prestage + strong core" harness while keeping Xeno/EntityOS as the state, routing and authority substrate.

Acceptance requires tests for:

- prestage OFF bypass;
- prestage ON with slot1 -> core slot2;
- prestage ON with slot2 -> internal ~0.8B core;
- internal ~0.8B OFF + external core;
- core/prestage swap without canonical-state reset;
- provider/model capability mismatch;
- timeout/429/401/402 and malformed result classification;
- stale generation/result rejection;
- secret never appearing in model prompt, J-Space telemetry, logs, receipts or exported ordinary profile state.

## 5. Xeno-to-Xeno robust connectivity

A finished Xeno MUST expose a versioned peer protocol `XENO_PEER_LINK/v1` so multiple Xenos can be connected without sharing hidden mutable process state.

Peer messages bind at minimum:

- source Xeno instance identity;
- destination/target identity or broadcast scope;
- protocol/version;
- immutable message/event identity;
- causal id;
- generation;
- capability scope;
- provenance/evidence refs;
- resource budget;
- payload ref/digest;
- replay/idempotency identity;
- acknowledgement/result status.

Peers exchange typed candidates/state projections, never implicit canonical authority. Each Xeno retains its own deterministic admission, generation and effect boundaries.

Required robustness tests include disconnect/reconnect, duplicate packet, delayed/stale packet, out-of-order packet, peer restart, incompatible protocol version, capability denial, partial GRID10 member loss and deterministic replay after recovery.

## 6. GRID10 readiness

`GRID10` is a required v1 topology contract, initially with ten **logical cells**, not ten independent model copies.

Acceptance requires a deterministic plan and test harness proving at least theoretically/executably at component scope that:

- exactly 10 logical cell identities can be allocated;
- cells can share one or more physical engines;
- each cell keeps causal/generation/role/branch identity;
- scheduling survives one or more cell failures;
- Hyperposition alternatives are preserved until a discriminator collapses them;
- a peer-connected Xeno can participate as an admitted compute/provider node without becoming canonical truth authority;
- logical cell count remains distinct from resident model count and physical decode concurrency.

The first product target is correctness and composability of GRID10. Scaling beyond 10 remains conditional on measured value.

## 7. Dashboard acceptance

The local dashboard MUST expose at least:

- internal ~0.8B ON/OFF;
- exact bundled model/manifest status;
- configured external slot1/slot2 status;
- add/update/remove credential through secret-store ingress;
- adapter/provider/model selection per slot;
- select `CORE`;
- select `PRESTAGE`;
- prestage ON/OFF;
- live selected route and reason;
- engine health and capability receipt;
- latency/throughput/usage/rate-limit telemetry;
- GRID10 status;
- Xeno peer-link status;
- Global J-Space/GWT state, calibration and causal evidence status;
- explicit warning when an engine is `COMPILED_EXTERNAL` and has no latent-access path;
- no secret plaintext display after ingress beyond masked metadata where safe.

## 8. Global J-Space priority

Global J-Space is not considered finished merely because one vector codec or activation probe exists. It is a first-class recursive research+engineering target.

Required work streams include:

- exact model-specific latent geometry for the bundled ~0.8B core;
- stronger `JSPACE_VECTOR_CONTROL_ABI` codecs;
- GWT competition/broadcast calibration;
- causal lesion/sham/off-target/rescue families;
- role/cell-specific re-entry;
- cross-turn persistence without truth inflation;
- model-switch and external-core compilation behavior;
- cross-Xeno J-Space projection/interop without assuming shared latent coordinates;
- collapse detection and Hyperposition preservation;
- throughput/latency overhead measurement;
- adversarial tests for metadata/vector mismatch;
- learned adapters only when they beat deterministic codecs on the full protected metric vector.

J-Space improvements must be measured through causal/system-level outcomes, not self-report, coherence or worker consensus.

## 9. Xeno v1 acceptance gates

`XENO_V1_ACCEPTED` requires PASS evidence for all of:

- `V1_RUNTIME`
- `V1_08B_ENGINE`
- `V1_ENGINE_SWAP`
- `V1_TWO_SLOT_HARNESS`
- `V1_PRESTAGE`
- `V1_DASHBOARD`
- `V1_PEER_LINK`
- `V1_GRID10`
- `V1_JSPACE_GWT`
- `V1_DATASET`
- `V1_TRAINING`
- `V1_INTEGRATION`
- `V1_RECOVERY_EFFECT_AUTHORITY`
- `V1_ACCEPTANCE_METRICS`

The acceptance marker must bind exact source tree, exact model/tokenizer/runtime identities, test/benchmark receipts and the frozen metric snapshot.

## 10. Recursive development after v1

Xeno v1 is not a terminal state.

Every later owner `go` continues:

```text
measure current accepted Xeno
 -> choose highest-information implementation delta
 -> implement
 -> test positive + negative + recovery paths
 -> benchmark full frozen metric vector
 -> compare through XENO_PROMOTION_GATE/v2
 -> promote only if epsilon-Pareto no-regression + cross-group progress passes
 -> increase ClayCode share only through meaningful ClayCode gain with protected non-regression
 -> update accepted baseline
 -> repeat on the next go
```

The comparison gate must not count tiny benchmark jitter as progress and must not allow a single scalar to self-promote. Hard correctness/authority/recovery regressions fail closed. J-Space remains protected and may stay stable on unrelated patches, but material regression is not accepted.

This loop has no built-in terminal iteration count or "finished forever" state. It continues until a newer explicit owner instruction supersedes the objective.

# AI-NATIVE SPEECH FUSION PACKET — CLAY-L5 candidate

**Epistemic status:** OPEN architecture synthesis; no canonical promotion.

## Atomic synthesis

The best-supported architecture is not one AI-native syntax. It is a semantic spine with multiple controlled projections:

`intent -> canonical meaning -> {discrete native rail | latent native rail} -> canonical proposal/receipt -> authorized effect runtime`.

### Why two native rails?

**Discrete native rail (P2):** learned symbols/handles are cheap to persist, inspect, version, retrieve, compare and map to ClayGraph anchors. They are suited to stable interfaces and interpretable checkpoints. But compactness/purity alone is not enough and can hurt reader accuracy.

**Latent native rail (P3):** hidden states/embeddings/KV can preserve richer information than tokenization and can support reasoning or inter-agent communication without verbalization. But they are model/layer/version dependent, difficult to audit and can create misleading performance effects unless causally controlled.

The two are complementary rather than mutually exclusive.

## Required P3 LatentChannelReceipt

Any durable claim that a latent packet communicated useful information should bind:
- sender model/checkpoint/layer;
- receiver model/checkpoint/layer;
- message extraction transform;
- alignment/compression transform and hashes;
- task/example identity;
- zero-message result;
- random-message result;
- other-example-message result;
- same-example sender result;
- self-substitution result where feasible;
- downstream effect/re-entry changes;
- OOD result;
- uncertainty and failure class.

A latent vector itself is not truth, meaning, authority or evidence merely because it affects behavior.

## Required P2 NativeSymbolReceipt

A learned symbol/codebook claim should bind:
- codebook version/hash;
- canonical semantic anchors;
- usage distribution;
- compositional/OOD generalization;
- permutation/lesion/rescue results;
- semantic drift across training/checkpoints;
- cost/token/latency benefit;
- comparison with raw/canonical/latent/hybrid controls.

## Cross-model rule

Do not assume globally shared latent coordinates. Use learned/calibrated bridges and causal transfer tests. Current evidence is consistent with shared semantic neighborhoods while rejecting a simple globally identical representational geometry.

## Safety/authority rule

P2/P3 may propose. P1 defines committed semantic obligations. P4 capability/effect gateway authorizes and commits. No model-native or latent representation mints authority.

## FRANK design consequence

The Qwen-class 4B target should be trained/evaluated as a **multi-view semantic system**, not forced to use one textual Clay serialization for every purpose. Canonical Clay remains exact; CLAY_MODEL and LATENT_MODEL are versioned reader/cognition projections whose value is empirical.

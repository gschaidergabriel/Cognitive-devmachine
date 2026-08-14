# Q23 Final Synthesis — FeatureTap + Multimodal Recovery

Run: `q23-20260810T2242p0700-chatgpt-secondary-featuretap-recovery`

## Result

This run does not promote QNDRF or PAR. It creates a narrower, more executable architecture candidate and closes two hidden assumptions.

### 1. Same-pass feature-tap refinement

Current Qwen3.5 Transformers code makes the vision boundary more useful than the prior QNDRF description captured: one vision forward exposes both pre-merger `last_hidden_state` and post-merger `pooler_output`. The post-merger representation is the representation injected into the language model. Therefore Frank can test multiple MVC/open-set feature geometries from one expensive visual pass rather than immediately choosing between raw mmproj and a second encoder.

Candidate `VisualFeatureTap` fields include source/frame/ROI cryptographic identity, perception epoch, model/mmproj/runtime version, tap kind, grid, descriptor projection version and calibration/readout version.

No claim is made that the pre-merger or post-merger tap is a good familiarity embedding until the matched open-set benchmark passes. A dedicated lightweight embedding encoder remains the strongest counterbaseline.

### 2. Recovery assumption removed

libmtmd's public surface supports encoded media embeddings and decode reuse, but chunk serialization preserves metadata only; restored chunks are placeholders and cannot re-encode absent media. Current llama-server issue evidence also reports slot-cache save as unsupported for multimodal configurations. Therefore Frank v0.1 must not depend on durable visual KV/media runtime state before exact target-VPS proof.

Current safe candidate: durable provenance-bound source evidence/reference + typed semantic state + versioned compact descriptor/prototype lineage; after restart, re-encode required evidence unless a tested cache persistence implementation proves replay equivalence.

### 3. Cache ID != evidence identity

Current llama.cpp helper derives a 64-bit FNV-1a ID for loaded media and uses media IDs as cache-tracking aids. Frank must maintain a separate cryptographic visual evidence identity bound to source/ROI/epoch. Cache hints can accelerate lookup but cannot establish provenance, sensor truth, currentness or effect authority.

### 4. Two-stage temporal perception

Recent GUI-agent research supports exploiting screenshot redundancy while also showing that global/background/spatial transition information can remain useful. This run therefore refines temporal control into:

1. pre-encoder deterministic unchanged/change suppression to avoid expensive vision work entirely when possible;
2. post-encoder structured temporal/history pruning on changed frames to reduce downstream history/token cost while preserving spatial structure and recency.

The combined policy remains a candidate and must beat the simpler pre-gate-only baseline.

## Architecture candidate

`capture -> cryptographic evidence identity + epoch -> cheap change gate -> one Qwen vision pass -> VisualFeatureTap(pre, post) -> calibrated MVC/open-set -> optional structured temporal pruning / PAR-EAP context -> reuse post-merger embeddings on semantic escalation -> PerceptualField -> GWT/action/outcome -> provenance-bound re-entry`

## Highest-value next execution

Run `FEATURE_TAP_PROBE.py` on the accepted Hostinger Ubuntu VPS with the exact current Qwen3.5-4B/mmproj/runtime lineage and frozen recurring/unknown/near-neighbor GUI fixtures. Then execute the matched four-way feature benchmark and the multimodal crash/restart matrix.

## Stop reason

The local worker lacks an installed `transformers` runtime/model and no direct target-VPS execution surface was available in this invocation. Static primary-source verification and local Python syntax validation were completed; target runtime PASS is intentionally not claimed.

# Q23 Final Synthesis — Runtime Scale + VisionFeatureTap

Run: `q23-20260810T2004p0700-chatgpt-secondary-runtime-scale-tap`  
Actor: `chatgpt-secondary / OpenAI GPT-5.6 Sol`  
Status: `MATERIAL_RESEARCH_DELTA_COMMITTED / NO_ARCHITECTURE_PROMOTION / NO_TARGET_VPS_TEST_EXECUTED`

## Result

This q23 run materially refines the current QNDRF-1 dissolved-Retina candidate without promoting it.

The strongest new synthesis is:

> Qwen-native dissolved perception is physically testable as one visual encode feeding a bounded familiarity/open-set readout and, only when needed, the language decoder; however, model parameter count cannot be used as a proxy for vision cost, raw Qwen media features cannot be assumed calibrated for familiarity/open-set behavior, and current llama.cpp multimodal runtime configuration must be treated as a causal benchmark variable.

## Progress deltas

1. **Physical feature-reuse hinge identified.** Current Transformers Qwen3.5 and llama.cpp/libmtmd expose media embeddings before language decoding. This supports a concrete `VisionFeatureTap` implementation candidate instead of a vague architecture idea.
2. **Model-scale hypothesis revised.** Official Qwen3.5 configs show the 2B and 4B variants share essentially the same core 24-layer hidden-1024 vision tower; 0.8B uses a smaller 12-layer hidden-768 tower. Therefore 4B->2B is expected to save mainly language-side work, while 0.8B is the stronger candidate for reducing deep-vision encode cost. This remains a runtime hypothesis.
3. **Raw-feature counterhypothesis strengthened.** Primary VLM embedding research uses explicit embedding-oriented training/adaptation; raw generative-VLM media embeddings are not automatically a calibrated user-specific identity/open-set space. A dedicated lightweight embedding baseline remains mandatory.
4. **Runtime sanity became a hard precondition.** Current llama.cpp Qwen3.5 issue evidence reports multimodal failures or large performance changes under some build/backend/batch/KV/flash-attention/mmproj conditions. These reports are not universal truth, but they are sufficient to require target-specific sanity and recovery checks before attributing failures to model features.
5. **ROI/memory path narrowed.** Recent GUI work supports adaptive structure-preserving token reduction and action-grounded visual memory, but also gives counterevidence against blindly discarding background/layout context or keeping naive full-image memory. ROI-only cannot be the default promoted path.

## Architecture disposition

`QNDRF-1`: **REFINED CANDIDATE, NOT PROMOTED**.

Added candidate physical mechanism:

`capture/change gate -> Qwen/libmtmd encode -> VisionFeatureTap -> MVC/readout -> optional same-buffer decoder escalation -> ClayCode PerceptualField -> GWT/re-entry`

The `VisionFeatureTap` is implementation plumbing, not a new semantic cognitive organ. Retina lineage remains temporal/provenance/control/recovery fabric. Qwen remains the candidate deep visual core. Familiarity remains evidence, never sensor truth or effect authority.

`PAR-1`: **OPEN / LATER-STAGE / EXPERIENCE-DOSE-BOUND**. No claim that Frank experience improves perception is allowed without N=0 and geometric dose-response controls plus wrong-seed/stale/sham baselines.

## Highest-value next falsifier

The next q23 step is execution, not more literature:

1. resolve exact accepted target-VPS RAM/swap/storage/GPU/backend state, current llama.cpp build and available Qwen3.5 0.8B/2B/4B model+mmproj artifacts;
2. run the runtime-sanity matrix;
3. measure fixed-token encode-only and decoder-inclusive cost for 0.8B/2B/4B;
4. instrument the libmtmd feature tap and prove/refute true one-encode reuse with an invocation counter;
5. compare raw Qwen, tiny-projected Qwen and dedicated-light-embedding familiarity/open-set paths under matched task/resource/recovery controls.

This work is now registered as `WORK-Q23-VISION-SCALE-FEATURE-TAP-20260810`, with explicit policy not to displace the active ClayCode BASE critical path.

## Program consequence

No BASE/H1/H2/H3 release credit was created by this research run. Current BASE remains governed by its own receipt-gated work packages. The q23 result changes the future H1/H3 falsifier and benchmark design, not the current release status.

## Durable artifacts

This run contains `RUN_MANIFEST`, `HYPOTHESES`, `COUNTERHYPOTHESES`, `ONLINE_RESEARCH_MANIFEST`, `SOURCE_GRAPH`, `FUSION_GRAPH`, `PROGRESS_DELTAS`, `ARCHITECTURE_DELTAS`, `TEST_OBLIGATIONS`, packaged evidence, `GO_Q23_EXCHANGE`, branch feedback, re-entry receipts and this synthesis.

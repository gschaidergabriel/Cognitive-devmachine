# UCM2 FREE API / NVIDIA COGNITIVE ORGAN FABRIC

## Owner rule

Genuinely free or replenishing APIs may be used by the UCM2 Research Entity for **any UCM2-supporting purpose**: research, source discovery, architecture, coding, building, embeddings, retrieval, reranking, perception, OCR, speech, reasoning, evaluation, simulation, test generation, adversarial falsification, data transformation, comparison and analysis.

Together API is forbidden.

No paid fallback may silently activate. Trial-only credit is not assumed to be durable free capacity.

## Architectural role

An external API/model is a temporary cognitive/execution organ attached to `UCM2_CORE`, not an independent truth store and not an authority source.

Every material external-organ interaction should be representable in UCM2 as:

- organ/provider identity;
- model/endpoint/version where observable;
- capability class;
- input provenance/classification;
- request/observation time;
- output/result reference;
- latency/usage/rate-limit/failure state where observable;
- prediction or claim emitted;
- measured UCM2 outcome;
- lesson/experience record;
- current confidence/claim class.

Provider/model agreement does not create independent evidence when ancestry, prompt, source set or model family is shared.

## NVIDIA first-class organ family

Current official NVIDIA developer surfaces make NIM/API Catalog suitable for UCM2 research/development/prototyping. UCM2 should treat NVIDIA as a capability family rather than one monolithic model.

Candidate NVIDIA organ roles:

1. `NVIDIA_RETRIEVER_EMBED_ORGAN`
   - semantic embeddings for wiki/memory/world/evidence objects;
   - text and, where supported, image/text-image representations;
   - query/passages must preserve their distinct embedding modes when the selected model requires them;
   - always benchmark against local/open-source embedding baselines and retrieval ground truth.

2. `NVIDIA_RETRIEVER_RERANK_ORGAN`
   - rerank UCM2 candidate assemblies after cheap/local recall;
   - may handle multimodal candidate passages with supported models;
   - cannot promote graph/retrieval salience into fact authority.

3. `NVIDIA_REASONING_CODING_ORGAN`
   - architecture alternatives, implementation candidates, code review, bug hypotheses, test/falsifier generation and long-context analysis;
   - outputs remain GENERATED/INFERRED until tested against UCM2 state/runtime evidence.

4. `NVIDIA_VISION_PERCEPTION_ORGAN`
   - visual state/document/screenshot/image understanding where current free endpoint/model capability exists;
   - observations enter UCM2 with source/media provenance and uncertainty, never as unaudited fact.

5. `NVIDIA_SPEECH_ASR_ORGAN`
   - realtime/offline transcription for future ClayVerse speech interaction experiments;
   - transcript is an observation with audio provenance, not human intent authority by itself.

6. `NVIDIA_SPEECH_TTS_ORGAN`
   - speech synthesis/output experiments;
   - generated audio must be linked to the exact semantic output and generation receipt.

7. `NVIDIA_SYNTHETIC_ADVERSARY_ORGAN`
   - generate counterexamples, ambiguous queries, conflict sets, stale-state probes, retrieval traps and architecture counterhypotheses;
   - value is measured by falsifier yield, not novelty.

## Cognitive integration law

The preferred UCM2 pattern is:

`UCM2 state -> bounded task-conditioned assembly -> capability router -> external/local organ -> typed result receipt -> UCM2 experience/outcome comparison -> state/Hyperposition update`

Do not dump the full UCM2 database into external providers. Send the minimum task-relevant bounded assembly and redact secrets/private material.

External organ result classes should remain explicit, for example:

`OBSERVED_PROVIDER_OUTPUT | GENERATED_CANDIDATE | INFERRED_CANDIDATE | TEST_INPUT | MEASURED_OUTCOME | REFUTED | VERIFIED_WITHIN_TEST_SCOPE`

## GO obligation

Every `go` cycle may use any useful free API. It should actively consider NVIDIA and other available free organs, but only invoke them when expected information gain or build/test value is positive.

When an API is used materially, `go` must document:

- why this organ was selected;
- what local/classical alternative exists;
- what it predicted/produced;
- what UCM2 actually measured;
- cost/free-access/rate-limit observations where available;
- whether it improved the cycle;
- whether the capability should be RETAINED, DEFERRED, REPLACED or FURTHER_TESTED.

A successful API call alone is never a UCM2 success claim.

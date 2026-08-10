# Q23 Final Synthesis — Qwen feature reuse + visual runtime compatibility envelope

Run: `q23-20260810T2242p0700-chatgpt-secondary-dualview-runtime-envelope`

## Executive result

This run materially narrows the Frank v0.1 Digital Retina/MVC architecture without promoting an unmeasured claim.

The current evidence says **do not add a second heavy visual backbone by default**. First exploit the Qwen visual encode Frank already needs. Current primary implementations make this technically real: the Qwen3.5 Transformers path exposes visual representations before language decoding, while current llama.cpp/libmtmd exposes the encoded merged media embedding buffer. This permits a familiarity/open-set branch after one visual encode and before expensive semantic decoding.

However, the strongest counterevidence is also material. Qwen's official multimodal embedding system does not simply declare raw visual projector tokens to be calibrated retrieval embeddings; it uses retrieval-specific training and a normalized representation from the full multimodal hidden state. Therefore this run **does not** claim that raw mmproj features are already good enough for Frank's user-specific familiarity/open-set problem.

The new candidate ordering is:

1. `MVC-M0`: deterministic pooled descriptor from public merged Qwen/mmproj features.
2. `MVC-M1`: tiny learnable projection/calibrator over those frozen merged features if M0 misses the open-set gate.
3. `MVC-M2`: same-encode pre-merger + merged dual-view descriptor only if M0/M1 fail and the incremental benefit justifies target-runtime instrumentation.
4. `MVC-B`: separate lightweight embedding encoder remains a mandatory counterbaseline and is retained only if measured total cost/quality is Pareto-superior.

This ordering minimizes architecture duplication while keeping the dedicated-encoder alternative falsifiable and alive.

## New technical finding: one encode can have two useful readout scales

Current Qwen3.5 Transformers code returns both the pre-merger vision-block hidden state and the merged visual representation from the same vision forward. This creates a previously underused possibility: local/spatial patch geometry and LLM-facing merged geometry can be compared or combined without a second deep visual encode.

But the target-runtime interface matters. The current public libmtmd surface exposes the merged output embedding buffer, not the pre-merger hidden-state view. Therefore Q23 now explicitly forbids a premature libmtmd fork. The merged-only experiment is cheaper and must run first. Only a measured M0/M1 failure can justify a bounded pre-merger instrumentation experiment.

## New cross-cutting invariant: VisualEncoderCompatibilityID

A visual prototype is not valid merely because the model and mmproj filenames match.

Current runtime failure evidence shows that Qwen3.5 multimodal behavior can depend on server/CLI path, preprocessing, batch/ubatch configuration, Flash Attention, KV layout, backend and image-token handling. Some failures crash; others can return semantically wrong visual behavior while the request itself appears successful.

Therefore every MVC prototype/calibrator version must bind to a `VisualEncoderCompatibilityID` containing at least:

- visual model identity/hash;
- mmproj identity/hash;
- runtime/build/commit identity;
- vision preprocessor identity;
- projector geometry;
- backend/device class;
- image token min/max policy;
- representation-affecting batch semantics;
- canonicalizer version;
- feature pooling version;
- learned projection/calibration version where present.

A mismatch means `STALE_INCOMPATIBLE`, not "probably okay". The safe behavior is to quarantine the prototype state and fail open to full semantic decode until differential compatibility is demonstrated.

## Retina implication

The Retina should not dissolve into "just Qwen vision". Its surviving causal functions remain:

- sensor/source identity and provenance;
- timestamp/source epoch;
- orientation/color/pixel canonicalization;
- cheap change and ROI gating;
- image-token and deep-vision duty-cycle control;
- user-specific familiarity/open-set state;
- uncertainty and action-critical escalation;
- perceptual memory/version lineage;
- active sensing;
- action/outcome visual verification;
- GWT/re-entry observability;
- recovery/quarantine/rollback.

Qwen is the deep visual core candidate inside that fabric, not a replacement for those controller/provenance/recovery functions.

## Canonical-pixel gate

Cheap unchanged-frame suppression should operate after perceptual canonicalization, not on raw container bytes. EXIF orientation, format and related preprocessing differences can otherwise create false novelty or poison prototype identity. Conversely tiny semantically important changes must remain visible to the gate. The new metamorphic test suite therefore includes orientation, format, one-pixel/text/icon/checkbox/focus changes and cursor-only motion.

## Decisive experiment

The next high-information test is `TO-Q23-MVC-OPENSET-01` with matched target-like screenshots/camera fixtures:

- A: full Qwen decode every changed observation;
- B: dedicated lightweight encoder MVC;
- C: one Qwen encode + merged-feature MVC-M0;
- D: one Qwen encode + tiny-projection MVC-M1;
- E: optional pre-merger+merged MVC-M2 only after C/D miss the gate.

Measure open-set confusion, false familiarity/bypass, selective risk, calibration, routing correctness, verified downstream task outcome, p50/p90/p95/p99 latency, CPU/RAM/GPU/VRAM, decoder-call rate, image/context cost, crashes/timeouts and recovery. Preserve raw rows and complete runtime/model/preprocessing metadata.

A second mandatory test, `TO-Q23-VISUAL-COMPAT-02`, measures representation and behavior drift across runtime/preprocessing configurations before prototype reuse across upgrades is allowed.

## What changed in Frank v0.1 research state

Material deltas produced:

- physical same-encode feature reuse moved from concept to current API-backed implementability;
- architecture candidate refined to `AD-Q23-QNDRF-1.1-MERGED-FIRST`;
- official Qwen embedding design recorded as counterevidence against raw-feature overclaiming;
- full visual runtime/preprocessing identity elevated into prototype semantics;
- new open-set, compatibility, canonical-pixel and recovery test obligations created;
- Q23 -> GO architecture/counter-challenge payloads persisted for targeted shared-state pull.

## What did NOT happen

- No target Frank runtime benchmark was executed in this invocation.
- No F-V01-06 work package/subcheck was marked PASS.
- No target VPS state was changed.
- No Frank runtime/repository was mutated.
- No final model training was started.
- No raw Qwen/mmproj embedding-quality claim was promoted.
- No Harness authority boundary changed.

## Next frontier

Highest-value next action: execute variants A/B/C on the same target-compatible fixture corpus. If C is non-inferior and cheaper, the duplicate visual encoder can likely be eliminated. If C fails, run D. Only then consider E. The dedicated encoder remains the adversarial baseline until the measurements decide.

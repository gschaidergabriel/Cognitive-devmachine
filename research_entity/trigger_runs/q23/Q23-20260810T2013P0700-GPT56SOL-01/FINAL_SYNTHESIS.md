# Q23 Final Synthesis — Q23-20260810T2013P0700-GPT56SOL-01

## Result

This run does not promote a new Frank architecture. It materially refines the current QNDRF-1/PAR-1 frontier and commits executable falsifiers.

### 1. Feature reuse is physically plausible but not architecturally guaranteed

Current llama.cpp exposes the libmtmd encoded embedding buffer before image-chunk decode. This is the physical seam QNDRF needs. However stock slot/request lifetime plus current Qwen3.5 multi-turn image-reprocessing failure evidence means `one expensive visual encode -> zero or one semantic decode` must not be credited from API shape alone.

New candidate: `PerceptualEmbeddingHandle (PEH)`.

PEH binds the encoded visual representation to exact frame/ROI/token geometry/model/mmproj/runtime/backend/provenance identity, allows MVC readout, and permits delayed semantic decode only if the handle remains compatible. It must reject stale/mismatched handles and survive restart only through verified rebuild/replay semantics.

### 2. Raw Qwen visual geometry remains a baseline, not an assumption

Qwen3-VL-Embedding and VLM2Vec obtain strong multimodal embedding behavior through explicit contrastive/distillation training. This is meaningful counterevidence to treating raw generative-VLM visual outputs as calibrated user-specific identity/open-set embeddings.

Disposition:
- Q0 raw pooled Qwen prototypes: keep as cheapest diagnostic baseline.
- Q1 tiny learned/calibrated projection over frozen Qwen features: stronger operational candidate, still unproven.
- dedicated light embedding encoder: retain as equal-budget counterbaseline until Q0/Q1 measurements dominate it.

### 3. Free DeepStack feature tapping is not the current 4B baseline

Current Qwen3.5-4B config has `deepstack_visual_indexes=[]`. Therefore the normal zero-extra-pass path should use the final visual output. Intermediate-layer probes are optional instrumentation experiments and must account for their added capture/copy/runtime cost.

### 4. PAR-1 remains scientifically open but is experience-dose gated

No claim that Frank benefits from visual episodic experience was made in this run. The required dose study remains `N={0,1,2,4,8,16,32,64}` with QWEN_ONLY, DIRECT_MEMORY_N, PAR_EAP_N, PAR_ACTIVE_N and SHAM/fault controls. Independent target-relevant Frank episodes are currently unavailable to this worker, so `N_onset/N_robust/N_90/N_harm` remain unknown.

### 5. Runtime configuration enters correctness metadata

Qwen3.5-family llama.cpp issue evidence is sufficient to add batch/ubatch/mmproj-offload/backend/flash-attention/parallel-KV configuration to every visual benchmark receipt. It is not sufficient to claim the exact 4B target has the same bugs. The exact target-VPS configuration matrix is the falsifier.

## Highest-value next executable work

1. `T-Q23-PEH-001`: target-VPS PEH encode-count/resource/recovery differential.
2. `T-Q23-Q0Q1-002`: Q0 vs Q1 vs dedicated encoder on held-out familiarity/open-set fixtures.
3. `T-Q23-CONFIG-003`: exact 4B runtime configuration correctness matrix.
4. `T-Q23-PAR-004`: only after independent Frank experience fixtures exist, run full dose-response.

## Architecture disposition

`QNDRF-1`: REFINED / NOT PROMOTED.
`AD-Q23-PEH-001`: CANDIDATE.
`PAR-1`: CANDIDATE / EXPERIENCE CLAIM BLOCKED PENDING DOSE RESPONSE.
`RAW QWEN FEATURE CALIBRATION`: UNKNOWN.
`DEDICATED LIGHT ENCODER`: RETAIN AS COUNTERBASELINE.

## Execution boundary

This worker performed current repo refresh, repeated primary/official external research, dense fusion and durable GitHub writes. It did not have an exact target-VPS execution capability in this invocation, so no runtime benchmark, H1/H2/H3 release credit or canonical architecture promotion is claimed.

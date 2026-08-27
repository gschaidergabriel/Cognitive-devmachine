# Owner one-shot ~0.8B J-Space/GWT specialization training directive

Status: **CURRENT EXPLICIT OWNER AUTHORIZATION**  
Date: 2026-08-24  
Program: **EntityOS + HCU**  
Scope: **exactly one first serious Together fine-tuning run**, followed by integration and deep evaluation.

## Owner intent

Develop the local ~0.8B HCU model into a highly specialized cognitive compute component that natively supports the EntityOS/HCU design:

- Global J-Space participation;
- local-module GWT <-> Global J-Space coupling;
- Xeno/Typed-Entry vector-driven control;
- role/cell activation and routing;
- Hyperposition alternatives/counterhypotheses;
- compact ClayCode/GRF projection;
- generation/provenance/capability/resource fencing;
- loader/engine identity and downstream receipt discipline;
- script-only/no-model decisions when cognition is not justified;
- recovery/stale-result rejection and EffectGate boundary awareness.

The model should become deliberately narrow. Unrelated general-purpose behavior is low priority and may degrade substantially, but the training must retain the minimum language, structured-output, tool/protocol comprehension, arithmetic/logic and safety capabilities required to execute the HCU role reliably. "Forget everything unimportant" means **measured specialization**, not unmeasured catastrophic collapse.

## Authority change

The earlier blanket `Together forbidden` rule is superseded **only for this one bounded training experiment**.

Authorized:

1. use an owner-held `TOGETHER_API_KEY` through a transient admitted runtime/tool environment;
2. upload the finalized training/validation datasets to Together;
3. launch exactly one serious first fine-tuning job for the selected ~0.8B-class model;
4. monitor the job, retrieve/download the resulting weights/checkpoint, and run integration/deep evaluation;
5. spend the amount inherently required by this one explicitly authorized training job.

Not authorized by this exception:

- general Together inference fallback;
- recurring or automatic retraining;
- a second paid training run without a new owner authorization;
- secrets in Git, prompts, receipts, logs, datasets, images, model metadata or persistent Sandbox state;
- relaxing EntityOS state/effect/provenance/generation authority to make training look successful.

The one-shot authorization is **not consumed until a Together fine-tuning job is actually created** and its job ID is recorded in a non-secret receipt. Dry-runs, dataset generation, validation, pricing queries, capability checks and local/Sandbox evaluations do not consume it.

## Required order

Do not train from a prose-only architecture. The first serious candidate follows this order:

```text
Global J-Space/GWT prototype
-> instrumented exact traces
-> causal/lesion/control evaluation
-> versioned Vector Control ABI
-> dataset compiler
-> train/validation/holdout sets
-> pre-train baseline evaluation
-> one Together full fine-tune
-> download/hash-bind weights+tokenizer
-> EntityOS/HCU integration
-> deep post-train evaluation and ablations
```

If the prototype cannot yet produce meaningful causal/control traces, training remains **READY_NOT_STARTED** rather than fabricating labels.

## Global J-Space/GWT prototype training interface

The prototype must expose a versioned record for every model-relevant transition. Minimum fields:

- `schema_version`
- `trace_id`
- `generation`
- `entry_event_sha256`
- `entry_admission_sha256`
- `route_decision_sha256`
- `grid_plan_sha256`
- `cell_id` / role
- `jspace_basis_id`
- `jspace_input_vector_ref`
- `jspace_input_codec_version`
- `local_workspace_state_ref`
- `gwt_competition_set`
- `gwt_broadcast_gate`
- `global_jspace_slice_ref`
- `hyperposition_branch_ids`
- `provenance/evidence class`
- `resource budget`
- `requested action class`
- `expected structured model output`
- `observed downstream outcome`
- `falsifier/lesion condition`
- `credit label`

Raw private chain-of-thought is not a training target. Train observable state transitions, decisions, structured projections and externally checkable outcomes.

## Vector Control ABI

A normal CausalLM fine-tune cannot by itself prove arbitrary hidden-state vector injection. Therefore the first training candidate must define one exact **JSPACE_VECTOR_CONTROL_ABI/v1** that can be reproduced by Together training and by the local HCU runtime.

The preferred first ABI is a deterministic, quantized vector-control packet that converts a J-Space vector/slice into a compact token/byte representation plus typed control header. Example conceptual envelope:

```text
<jctl:v1 basis=B42 role=critic gen=91>
q8:[...quantized coordinates...]
gate:[...]
workspace:[...typed handles...]
</jctl>
```

The codec must be deterministic, versioned, hash-bound and tested for:

- vector -> packet -> vector reconstruction error;
- sign/scale/basis identity;
- permutation/order stability;
- stale generation rejection;
- wrong-basis rejection;
- random-vector/null-vector controls;
- role-swap and lesion controls.

A later runtime may replace the token codec with a learned `inputs_embeds`/prefix adapter if the admitted loader exposes it, but the first Together run must train against an interface that Together can actually reproduce. Do not claim direct residual-stream control from text-token SFT.

## Training-data mixture v1

Dataset rows are derived from real prototype traces plus bounded counterfactual/negative transformations whose labels are deterministically known.

Target mixture by **training tokens** (initial prior, adjustable after trace statistics):

- 25% J-Space vector-control decoding/response behavior;
- 15% GWT competition, broadcast, workspace update and role-specific re-entry;
- 15% Typed Entry -> HCU route/cell action behavior;
- 10% Hyperposition hypothesis/counterhypothesis/falsifier handling;
- 10% provenance/generation/capability/resource fail-closed cases;
- 8% script-only/no-model/no-op decisions;
- 7% compact ClayCode/GRF projection and structured output;
- 5% restart/recovery/stale-result handling;
- 5% retention anchors: minimal language, arithmetic/logic, schema following, tool/protocol comprehension and safety boundary.

Hard negatives are mandatory and should be overrepresented in validation/holdout:

- wrong J-Space basis;
- stale generation;
- swapped cell role;
- mismatched Entry admission/event;
- unadmitted engine/lease;
- random vector with plausible text metadata;
- correct vector with poisoned metadata;
- majority-vote trap;
- unsupported truth/effect claim;
- over-budget model activation;
- script-only event that tries to force inference;
- cross-branch Hyperposition collapse without evidence.

## Data format

Use JSONL accepted by Together. Prefer conversational `messages` or explicit prompt/completion records so input masking is controlled. Every row also gets an offline sidecar manifest containing source trace hashes and labels; the sidecar is **not** uploaded if it contains private/provenance metadata unnecessary for training.

Training row outputs should be short, machine-checkable and role-specific. Avoid verbose assistant-style prose because the target is a cognitive coprocessor, not a general chatbot.

## Train/validation/holdout split

Split by **causal episode / trace family**, never random neighboring rows, to prevent leakage.

Initial target:

- train 80%
- validation 10%
- sealed holdout 10%

Additionally maintain a non-training adversarial suite containing topology shuffles, unseen vector combinations, delayed outcomes, basis changes and recovery generations.

## First run training method

Owner requested a complete specialization. Default first candidate is **full supervised fine-tuning**, not LoRA, if Together confirms full training support for the exact base model and the quoted cost remains reasonable for this one authorized run.

Starting hyperparameter prior for the first serious run:

- training method: SFT/full;
- epochs: 2 initially, with a saved intermediate checkpoint if Together permits;
- learning rate: conservative small-model full-FT range, selected after dataset token count/base-model inspection; do not hard-code before that inspection;
- cosine scheduler;
- warmup 3-5%;
- gradient clipping enabled;
- fixed random seed;
- validation evaluations during training;
- train on outputs rather than blindly training all prompt tokens unless the final dataset study supports otherwise.

Use Together's preflight/price estimate before job creation. Price estimation does not consume the one-shot; actual job creation does.

## Base-model gate

Do not silently substitute a different model. Resolve and bind:

- exact model repository/id;
- exact revision/commit;
- architecture;
- parameter count;
- tokenizer hash;
- model weight hash/tree identity;
- Together-supported full-FT path.

Together documentation currently exposes full and LoRA fine-tuning and `--from-hf-model`; its 2025 platform update states that CausalLM Hugging Face models below 100B can be fine-tuned, and explicitly lists Qwen3-0.6B as a supported small Qwen model. This makes a ~0.8B-class candidate technically plausible, but the **exact intended HCU base must be verified immediately before training**. If the exact base is unsupported, stop and report the blocker rather than consuming the one-shot on the wrong model.

## "Forgetting" / specialization objective

We want low off-domain interference, not uncontrolled damage. Measure three sets:

1. **must gain** — J-Space/GWT/Xeno/HCU tasks;
2. **must retain** — structured protocol following, minimal language/logic, numeric/vector handling, tool boundaries, safety/authority rules;
3. **may forget** — unrelated trivia, broad creative/chat personality, generic encyclopedic recall and other capabilities not used by HCU.

A successful specialization should strongly improve set 1, stay above hard floors on set 2, and may drop on set 3. Do not optimize directly for arbitrary forgetting if it damages sets 1 or 2.

## Pre/post acceptance matrix

Before uploading data, freeze a baseline on the exact base checkpoint. After training, compare with identical seeds/inputs where applicable.

Minimum post-train gates:

- Vector Control ABI decode and action accuracy;
- basis/generation/role mismatch rejection;
- GWT broadcast selection and workspace transition accuracy;
- causal Global J-Space lesion/rescue sensitivity;
- Entry -> route -> cell -> inference receipt consistency;
- Hyperposition non-collapse under ambiguous evidence;
- script-only suppression rate;
- stale/recovery rejection;
- ClayCode projection correctness and compactness;
- capability/effect authority non-escalation;
- retained language/schema/math floor;
- off-domain interference measurement;
- throughput/RAM/latency on target runtime when available.

Required causal tests include matched-budget lesion/shuffle/rescue comparisons. Mere benchmark accuracy is not proof that Global J-Space is being causally used.

## Together execution procedure

When the gates above are ready and a worker has an admitted transient secret surface:

1. discover current Together API/CLI capability and supported model limits;
2. expose `TOGETHER_API_KEY` only as a transient environment secret;
3. run dataset validation/checks;
4. upload train and validation JSONL;
5. obtain/record non-secret price estimate and exact configuration;
6. create **one** full fine-tuning job;
7. immediately record the non-secret Together job ID, base model identity, dataset hashes and hyperparameters in a receipt and mark `ONE_SHOT_TOGETHER_TRAINING_CONSUMED=true`;
8. monitor without leaking the token;
9. download final weights/checkpoint;
10. hash-bind weights/tokenizer/config and clear temporary credentials/files where required;
11. integrate behind the existing EngineAdmission/physical-engine-lease path;
12. execute the frozen deep evaluation matrix in authorized isolated execution.

Together currently supports a native fine-tuning API/CLI, full or LoRA training, validation files, checkpoints/evals, and model-weight download. Use the native Together fine-tuning API rather than an OpenAI-shaped fine-tuning endpoint.

## Promotion rule

The fine-tuned model becomes the preferred HCU ~0.8B candidate only if it beats the exact base on the must-gain suite, meets every must-retain floor, passes the fail-closed/authority matrix, and produces positive matched-budget J-Space/GWT causal evidence.

A completed Together job is **not** itself a PASS. If the candidate fails, preserve it as evidence and do not launch a second paid training job without new explicit owner authorization.

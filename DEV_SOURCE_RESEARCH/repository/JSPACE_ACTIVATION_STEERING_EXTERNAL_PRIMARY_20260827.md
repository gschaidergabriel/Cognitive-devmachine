# Global J-Space / activation intervention — external-primary discriminator update

**Trigger:** `triggerword 3`  
**Evidence class:** `EXTERNAL_PRIMARY + INFERENCE`  
**Project runtime credit created:** `0`

This note adds an external intervention-method layer to the current Global J-Space/GWT research program. It does **not** claim that a J-Space vector exists in the target model or that current HCU vector control is causally validated.

## Primary sources

### Activation Engineering / Activation Addition

Turner et al., *Steering Language Models With Activation Engineering*, arXiv:2308.10248 (2023).  
https://arxiv.org/abs/2308.10248

The paper studies inference-time activation modification and introduces Activation Addition (ActAdd): contrast activations from prompt pairs, derive a direction, then add a scaled version of that direction during the forward pass to steer model outputs.

**Transfer to J-Space research:** activation-level vector intervention is a legitimate causal-control experiment class.

**Non-transfer:** an ActAdd result elsewhere does not establish the semantics, layer, token position, stability, or causal identity of a Clay/EntityOS J-Space vector.

### Representation Engineering

Zou et al., *Representation Engineering: A Top-Down Approach to AI Transparency*, arXiv:2310.01405 (2023).  
https://arxiv.org/abs/2310.01405

This work studies population-level representations and methods to monitor/manipulate high-level model behavior.

**Transfer:** treat a candidate J-Space variable as a measurable population-level representation hypothesis rather than as a named hidden entity inferred from output prose.

### Activation patching methodology

Zhang & Nanda, *Towards Best Practices of Activation Patching in Language Models: Metrics and Methods*, arXiv:2309.16042 (2023).  
https://arxiv.org/abs/2309.16042

The paper shows that activation-patching conclusions can change materially with corruption method, metric, and other methodological choices.

**Transfer:** a single positive intervention configuration is insufficient. J-Space causality needs preregistered metrics/baselines and sensitivity checks across intervention choices.

### Steering-vector reliability

Braun et al., *Understanding (Un)Reliability of Steering Vectors in Language Models*, arXiv:2505.22637 (2025).  
https://arxiv.org/abs/2505.22637

The reported experiments find substantial sample-level variance and sometimes steering effects opposite to the intended direction. Steering effectiveness is associated with more coherent activation-difference geometry and stronger separation of positive/negative activations.

**Transfer:** do not assume that a direction estimated from a small prompt family is a stable semantic axis. Measure direction coherence, per-family variance, sign reversals, and off-target behavior.

### Recent layer-specific causal steering signal

Srivastav, *Steering the Language Axis: From Linear Decodability to Causal Control*, arXiv:2608.12334 (2026).  
https://arxiv.org/abs/2608.12334

This recent study reports language-axis interventions across multiple model families, including Qwen 3.5-2B and Llama-3.2-1B-Instruct. Its central methodological signal for this project is that a decodable feature need not be treated as a globally uniform direction: reported steering sensitivity is layer-dependent and language-pair-dependent, with random perturbations used as controls.

**Transfer:** the current J-Space ABI should not silently assume one layer-invariant semantic vector. Layer/position choice is an empirical variable.

### Sequential activation patching for generated reasoning trajectories

Dura, Öztürk & Tekir, *Mechanistic Interpretability of Chain-of-Thought Reasoning via Sequential Activation Patching*, arXiv:2608.22332 (2026).  
https://arxiv.org/abs/2608.22332

This work proposes sequential activation patching across generated token positions and includes cross-question/random controls, motivated by the fact that reasoning-related effects may be distributed over an autoregressive trajectory rather than localized to one static token.

**Transfer:** if HCU/J-Space control is claimed to persist across a generated reasoning trajectory, last-token-only evidence is structurally insufficient; temporal intervention identity should be explicit.

## Project hypothesis update

Existing project hypothesis:

> A shared J-Space/vector signal can causally coordinate bounded HCU functions and alter target-model behavior beyond lexical/prompt/schema leakage.

The external literature sharpens this into a more falsifiable form:

> For one exact checkpoint/tokenizer/runtime, a preregistered J-Space intervention family should produce a directionally consistent, layer/position-characterized, dose-responsive behavioral effect that exceeds matched random/shuffle controls, survives label removal and family-disjoint evaluation, and shows predictable lesion/rescue behavior without unacceptable off-target degradation.

This remains an `OPEN_HYPOTHESIS`.

## Required discriminator matrix

| Variable | Required control / measurement |
|---|---|
| checkpoint | exact checkpoint digest + architecture |
| tokenizer/renderer | exact identity and prompt rendering |
| layer | sweep or preregistered layer family; do not assume global invariance |
| token position | explicit static vs trajectory-distributed intervention |
| vector source | family-disjoint construction set with no output-label leakage |
| direction geometry | norm, pairwise cosine/coherence, sign stability |
| amplitude | dose-response curve including zero |
| random control | matched-norm random direction |
| shuffle control | vector/label or family permutation as applicable |
| lesion | remove/suppress candidate channel and measure loss of effect |
| rescue | restore/reinject candidate signal and test recovery |
| semantic control | counterbalanced labels/wording/templates |
| generalization | held-out prompt/task families |
| off-target behavior | baseline capability/protocol regression |
| temporal persistence | per-token or phase-resolved effect when trajectory claims are made |

## Fail conditions

A candidate J-Space result does **not** earn causal promotion when any of these explains it sufficiently:

- prompt/schema recurrence;
- lexical label leakage;
- one prompt family defines the direction and also evaluates it;
- matched random directions perform similarly;
- effect changes sign unpredictably across families;
- result disappears under label-free counterbalance;
- only linear decodability is shown without intervention;
- only one layer/token position is tested while a global-vector claim is made;
- intervention changes output but lesion/rescue does not support the proposed channel;
- off-target degradation explains the apparent target gain;
- checkpoint/tokenizer/runtime identity is ambiguous.

## Consequence for JSPACE_VECTOR_CONTROL_ABI/v1

**INFERENCE:** the ABI should carry or bind at least:

```text
model/checkpoint identity
runtime/build identity
tokenizer/renderer identity
layer or layer-set identity
token position / phase policy
vector identity + construction family
normalization/scaling rule
intervention amplitude
causal-event / trial identity
control-arm identity
output + metric identity
```

If the ABI omits layer/position/control-arm identity, later data can conflate materially different interventions and make training traces look more causal than they are.

## Training consequence

Do not train the approximately-0.8B HCU/J-Space target on a generated vector-control language merely because vectors can steer outputs in principle.

Training-readiness promotion should wait for admitted project traces where intended vector semantics survive the discriminator matrix above. Otherwise finetuning risks learning labels for an unstable or confounded intervention interface.

## Evidence boundary

```text
external steering/intervention literature: METHOD/EVIDENCE FROM OTHER MODELS
project J-Space source/ABI: SOURCE/RESEARCH DIRECTION
project model-specific J-Space causality: NOT PROMOTED HERE
whole HCU runtime credit: +0
training credit: +0
```

`EXTERNAL_PRIMARY + METHOD_PRESENT != PROJECT_RESULT_PRESENT`.

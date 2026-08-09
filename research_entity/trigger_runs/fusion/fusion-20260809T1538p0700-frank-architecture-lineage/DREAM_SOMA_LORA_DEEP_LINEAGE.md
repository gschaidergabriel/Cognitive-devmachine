# FRANK Dream / IAPT-LoRA / SOMA adaptation — deep evolution lineage

Run: `fusion-20260809T1538p0700-frank-architecture-lineage`
Status: archaeology + current target synthesis; no training authorization

## DSL-0 — adaptation exists at multiple timescales

Project-Frankenstein evolved at least three distinct adaptation paths that must not be conflated:
1. **Dream/Consolidation** — replay/synthesis/memory/personality update while idle;
2. **IAPT/LoRA generations** — explicit adversarial offline personality/model training;
3. **SOMA** — autonomous idle-time personal adapter training from recent interactions/feedback.

The current FRANK architecture inherits mechanisms and failure lessons from all three, but the present program explicitly forbids starting model training before the later DATA stage completes and the owner gives a new instruction.

---

## DREAM-1 — creation as bounded sleep analogue

Commit `662957eeaf1ca94c107137d8341dd3073b6b0301` (2026-02-24).

Initial architecture:
- daily budget ~60 minutes;
- trigger after ~45 minutes idle;
- initial cooldown ~20 hours;
- three phases:
  1. **Replay** recent interactions/experiences;
  2. **Synthesis** generate hypotheses/causal patterns;
  3. **Consolidation** boost memory, apply E-PQ homeostasis, create dream reflections;
- interrupt-safe persistence with exact phase/step resume.

Key reusable principle:
- long-horizon background work is a resumable state machine, not an unstructured long prompt.

## DREAM-2 — cross-process personality-state hazard

Commit `2232a60...` showed Dream/Consciousness could write a newer E-PQ homeostasis state which Core's stale process-local singleton later overwrote.

Dream therefore contributes to a major architecture law:
`background consolidation state must publish atomically and foreground processes must consume current versioned state rather than cached mutable truth`.

## DREAM-3 — watchdog and observability

`cae8751...` added:
- primary Dream watchdog;
- meta-watchdog monitoring the watchdog;
- systemd resource limits.

Useful operations lesson:
- long-running autonomous consolidation needs health/recovery visibility.

Correction for current architecture:
- more watchdog layers do not establish semantic correctness;
- H1/H2/H3 should test exact state-machine resume/replay and idempotency directly.

## DREAM-4 — model/backend migrations

Dream followed multiple LLM generations:
- multi-model / RLM era;
- direct Qwen 3B era (`9fcf1f1...`);
- later Qwen 3.5-4B architecture.

Timeouts, token budgets and resource policies changed accordingly. Historical dream timing/resource constants are not architecture invariants.

## DREAM-5 — malformed model output

`3a47fef...` added handling for unclosed `<think>` blocks in dream output.

Current law:
- model transport/render artifacts cannot silently become semantic dream/consolidation state;
- parsing/canonicalization is a typed boundary with failure state.

## DREAM-6 — severe liveness negative result

Deep audit `07f8e26...` reports:
- only **1 dream session had ever completed**;
- 20h cooldown and idle detection made the mechanism effectively unreachable;
- cooldown changed 20h -> 6h and idle detection fixed.

This is a critical recurring FRANK lesson:
`implemented loop != reachable loop != useful loop`.

Harness must measure actual trigger/reachability frequency and completion, not merely timer configuration.

## DREAM-7 — consolidation path produced zero useful memory effect

Same audit reports:
- dream memory consolidation was always 0;
- fixed through keyword extraction + Titan FTS boost.

Current law:
`consolidation phase present != memory mutation/effect`.
Every slow-learning stage needs input -> candidate -> accepted update -> durable publication -> later-use receipts.

## DREAM-8 — Hippocampus training bridge

`279eb175...` integrated Hippocampus training into dream consolidation.

Current reuse:
- slow idle windows are sensible places for expensive derived-index/learned-route training;
- promotion of learned state still requires independent validation, version compatibility and rollback.

---

## LORA-1 — explicit personality adapter era

By `9fcf1f1edcb8db9b7d1a70a54b18ee82eb5187f5` (2026-03-15), LoRA v3 was deployed on Qwen2.5-3B:
- 1,608 samples reported;
- rank 16;
- alpha 32;
- 3 epochs;
- targets included explorer fixation, user relationship, present-moment grounding, gaming/Pip awareness, art description.

This generation also introduced a LoRA-specific context builder and RAG path, showing that model weights and runtime context evolved together.

## LORA-2 — rapid generation sequence / old adapters removed

Commit `62deb0a...` (2026-03-19):
- architecture simplified to Qwen2.5-3B only;
- old LoRA adapters v1-v6 deleted (~1.5 GB reported);
- v7 retained.

Later documentation:
- v12 by 2026-03-21;
- v14 by 2026-03-23;
- v15/v19f/v20+ in later March/April migrations.

Important evidence rule:
- a documentation label such as “v20+” is not enough to reconstruct each checkpoint's exact training set/weights; unavailable intermediate generations remain historical version references and must not receive invented metrics.

## LORA-3 — IAPT method

Commit `3892e001...` records the IAPT method paper.

Reported method:
- interactive adversarial evaluation;
- 390+ turns over 14 personas;
- automated failure extraction;
- surgical training-data generation;
- positive anchoring rather than only negative instructions;
- rapid iterative retraining.

Reported paper result:
- 7 iterations from 3/10 to 9.2/10 identity coherence.

Evidence class:
`HISTORICAL_REPORTED_METHOD/MEASUREMENT`, not current independent replication.

A known IAPT negative retained in architecture archaeology:
- regex/output parsers could become invisible co-authors, so apparent model improvement could partly come from downstream filtering/rewriting.

Current lesson:
- evaluation must isolate model-weight effect from runtime parser/filter/prompt changes.

## LORA-4 — runtime truth could override learned behavior

Commit `62149151...` demonstrates a decisive failure:
- stale hard-coded `ARCHITECTURE FACT` said Thalamus channel `aura`;
- runtime literal was injected into every relevant prompt;
- this reportedly overrode newer training behavior saying Swarm.

Thus:
`weight memory != canonical architecture truth`.
Current architecture facts live in versioned semantic state/contracts, not uncontrolled prompt literals.

---

## SOMA-1 — creation: Silent Online Model Adaptation

Commit `78f31e7f1e4fa7109a90f6e32514923ca7428a87` (2026-03-26).

Architecture:
- personal “Layer 2” LoRA adapter trained during idle hours;
- interaction buffer scores conversations from chat memory;
- CPU-optimized micro trainer;
- sleep cycle stops/restarts LLM around training;
- safety checks before deploy;
- adapter manager with snapshots, EMA blend, GGUF conversion and rollback;
- llama-server hot reload;
- persistent config and WebUI controls.

Reported initial execution:
- 50 real chat iterations;
- 104 conversations scored;
- 80 qualified;
- full CPU cycle ~18.7 min;
- safety check passed and GGUF adapter deployed.

Evidence class: `REPORTED_EXECUTED/MEASURED` for historical environment.

## SOMA-2 — initial safety gate

Creation safety checks included three broad gates:
- drift;
- similarity;
- NaN/numerical sanity.

Current research supersedes this with richer candidate/promotion/validity gates because numerical similarity alone cannot detect semantic poisoning, stale labels, open-set failures or causal miscredit.

## SOMA-3 — explicit user feedback + scorer evolution

`b9f23cd...` added thumbs up/down:
- explicit feedback stored with the prompting user message;
- explicit feedback ~40% of scorer when present;
- response-depth and user-investment signals;
- disengagement penalties.

LoRA target modules expanded:
- q/v -> q/k/v/o;
- ~921K -> ~1.8M trainable params reported.

`b49250b...` added `down_proj`:
- ~2.3M trainable params reported;
- first-cycle half-step/half-LR warmup;
- later EMA blending.

Current lesson:
- feedback provenance and exact pairing matter more than raw feedback count;
- user feedback is strong evidence but does not authorize unrelated generalization.

## SOMA-4 — personality probe / before-after measurement

`31963d1...` introduced fixed before/after probes over six dimensions:
- directness;
- warmth;
- humor;
- verbosity;
- formality;
- technicality.

Five fixed probe prompts produced a per-cycle change log.

Useful idea:
- every training cycle should have before/after behavioral probes.

Limitation:
- fixed keyword-derived personality probes can themselves be gamed/biased and do not establish general capability retention.

## SOMA-5 — audit round 1: state/data/resource correctness

`c16e599...` fixed critical issues:
- scored interaction DB wrote obsolete columns instead of current scorer outputs;
- DB connection leak;
- corrupted timestamp crash;
- EMA blend silently dropped keys only present in new adapter -> incomplete/corrupt adapter;
- model not freed on training errors;
- disabling personal mode did not stop thread;
- stop did not join thread, leaving ghost runtime window;
- personality probe substring false positives (`care` in `scare`, etc.);
- zero-norm baseline incorrectly returned zero drift (false safe);
- adapter loading TOCTOU;
- eager import pulled torch into inference path.

Current promotion law inherits all of these as transactional/resource/version tests.

## SOMA-6 — audit round 2: stale config and concurrent training

`ba1a82c...`:
- persisted WebUI config was written to JSON but runtime retained stale import-time constants;
- replaced by live configuration reads;
- two simultaneous sleep/force cycles could corrupt same temp/output adapter;
- added non-blocking concurrency lock;
- loader restart flag had TOCTOU causing duplicate restarts; fixed via atomic rename.

This maps directly to current atomic AdaptiveStatePromotion and versioned current-state publication.

## SOMA-7 — audit round 3

`4a2c885...` reports final fixes across:
- thread-safe Event/locks;
- circuit breaker;
- atomic config writes;
- bounds validation;
- duplicate session guard;
- drift over keys from both adapters;
- explicit near-zero similarity semantics;
- training sample shuffle;
- snapshot filtering/pruning;
- adapter_config metadata sync;
- probe failure exclusion;
- midnight-wrap training windows.

Key lesson:
- adaptive systems require ordinary systems correctness (locking, atomic files, metadata, shutdown) before learning quality can be evaluated.

## SOMA-8 — Qwen3.5-4B rebuild + feedback-weighted training

`a016410...` (2026-03-29):
- Qwen2.5-3B -> Qwen3.5-4B;
- adapter v15 -> v19f;
- bfloat16 base model; LoRA params float32;
- RAM threshold 8 -> 10 GB;
- stop/mask immune + LLM in controlled order;
- cycle count restored after restart;
- feedback window reset per cycle.

Reported weighting:
- quality score [0.65,1.0] -> ~0.5x..2.5x loss weight;
- thumbs-up 3-5x stronger learning;
- thumbs-down excluded from positive set + negative examples;
- negative weight -0.3, capped at 20% batch.

Current correction:
- negative examples and positive feedback are evidence roles, not arbitrary signed loss truth;
- causal/outcome attribution and contamination controls are required.

## SOMA-9 — autonomous timer enabled

`4634aeb...` (2026-03-31):
- sleep timer enabled;
- 81 unused interactions reportedly ready;
- snapshots 14 -> 3.

This marks the transition from a manually activatable experiment to scheduled autonomous adaptation.

Current program does **not** carry that autonomy forward during BASE/H1/H2/H3. Training remains disabled until explicit later authorization.

---

## DSL-1 — relation to current Unified Memory <-> Retina learning

Historical SOMA teaches model weights; current Retina adaptive learning initially targets a much smaller, bounded user-specific visual familiarity/readout layer.

The new target deliberately narrows autonomous learning:
- frozen/reusable visual backbone;
- tiny prototype/readout state;
- GOLD/SILVER/BRONZE evidence tiers;
- BRONZE self-predictions cannot become positive truth;
- open-set/near-confuser handling;
- candidate shadow evaluation;
- versioned calibration/backbone compatibility;
- atomic promotion and rollback.

Historical SOMA's lock/config/snapshot/rollback lessons transfer directly; broad uncontrolled model adaptation does not.

## DSL-2 — C4-C9 evolution

C4/C5:
- learned disposition occurs after exact episode/outcome state;
- training pairs carry source episode IDs and exclude exact telemetry from naive prose targets.

C6:
- `WEIGHT_MEMORY` explicitly becomes a slow memory class distinct from symbolic state and transient cognition.

C7/C8:
- model checkpoint has retention/OOD/semantic scores and promotion status;
- checkpoint promotion cannot depend on Clay loss alone.

C9:
- training/adaptation must preserve admissibility/authority distinctions;
- utility and model learning cannot mint `EffectPermit`.

## DSL-3 — current fused policy

### Dream/consolidation
Retain as a bounded, resumable slow scheduler function with explicit source/result/update receipts. Do not require a standalone Dream service in H3.

### Historical IAPT/LoRAs
Retain datasets, failure categories, checkpoint history and adversarial-evaluation methodology as training-data/evaluation lineage. Do not treat old checkpoint behavior as current architecture truth.

### SOMA
Retain implementation lessons for:
- interaction provenance;
- candidate adapter state;
- before/after evaluation;
- locks/atomicity;
- snapshots/rollback;
- resource gating;
- version compatibility.

Do not autonomously train the target FRANK model in current stages.

## Mandatory regressions

- DSL-REG-01 dream trigger configured but almost never reachable;
- DSL-REG-02 dream phase completes but accepted memory updates=0;
- DSL-REG-03 restart resumes same dream step twice or skips it;
- DSL-REG-04 stale foreground process overwrites background consolidation state;
- DSL-REG-05 parser/render artifact becomes training target;
- DSL-REG-06 runtime prompt literal overrides newer weight/semantic state;
- DSL-REG-07 adapter EMA drops unmatched parameter keys;
- DSL-REG-08 zero-norm reference falsely passes drift gate;
- DSL-REG-09 stale config means operator control differs from running learner;
- DSL-REG-10 two training cycles run concurrently on same candidate/output;
- DSL-REG-11 restart flag TOCTOU duplicates model restart;
- DSL-REG-12 error path leaks full model/RAM;
- DSL-REG-13 disabled learner thread continues running;
- DSL-REG-14 user feedback paired with wrong interaction;
- DSL-REG-15 self-predicted/pseudo-labeled examples launder into positive truth;
- DSL-REG-16 checkpoint improves fixed style probe but regresses retained capability/OOD;
- DSL-REG-17 H1/H2/H3 learner-state/rollback semantics remain equivalent with training disabled or fixture-simulated.

## Fusion decision

- Dream: `REUSE_RESUMABLE_CONSOLIDATION_SEMANTICS; RETEST_TRIGGERS/UPDATES; PHYSICAL_SERVICE_OPTIONAL`.
- IAPT: `REUSE_ADVERSARIAL_EVAL_AND_FAILURE-DRIVEN_DATA_METHOD; RETEST_WITH_CLEAN_MODEL-VS-RUNTIME_ABLATIONS`.
- historical LoRA checkpoints: `ARCHIVE_AS_WEIGHT_MEMORY_LINEAGE / EVAL_DATA_SOURCE`.
- SOMA: `REUSE_LEARNER_LIFECYCLE/ROLLBACK/ATOMICITY_LESSONS; NO_CURRENT_AUTONOMOUS_FULL-MODEL_TRAINING`.

<!-- RAE_META
{"packet_id":"KMP-C6-FULLMODEL-CLAY-TRAINING","title":"Clay full-model adaptation must transcode capability rather than optimize language purity alone","domains":["model_runtime","frank","claycode","clay"],"topics":["full-fine-tune","continued-pretraining","catastrophic-forgetting","tokenizer","curriculum"],"epistemic_class":"EXTERNAL_EVIDENCE_GROUNDED_TRAINING_HYPOTHESIS","claim_status_hint":"OPEN_HIGH_PRIORITY","origin_actor":"chatgpt-secondary","source_refs":["research_entity/trigger_runs/frank/20260808T1750+0700-chatgpt-secondary-r2/CLAY_NATIVE_FULL_FINE_TUNE_PLAN.md","ACL 2025 language adaptation forgetting","ACL 2026 Source-Shielded Updates","IRCoder"],"confidence":0.92,"verification_required":true}
RAE_META -->

### Core
The primary C6 training target updates the full 4B, but the optimization goal is not merely low Clay loss. It is to preserve and exercise pretrained competence through Clay. A staged bridge → Clay capability transcoding → ClayGraph/FRANK native training → Clay-only explicit deliberation/output curriculum is the leading candidate.

### Evidence / boundary
Language-adaptation research shows catastrophic forgetting can appear before target-language perplexity clearly exposes it; a 2026 study reports much larger source-task degradation for full fine-tuning than a protected-update method. IRCoder shows that continued causal training can teach a shared compiler IR to 1.1B–7.3B models. Neither proves the C6 target recipe.

### Required gate
Track Clay syntax, semantic execution, OOD composition, retained capability, abliteration retention, memory tasks, authority adversaries and runtime cost at every checkpoint.

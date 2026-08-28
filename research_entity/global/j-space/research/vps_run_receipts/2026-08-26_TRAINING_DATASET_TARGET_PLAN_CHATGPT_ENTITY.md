# Training Dataset Target Plan (ChatGPT entity response, 2026-08-26)

Asked directly (no triggerwort2, lightweight question): what is the concrete
target size/composition for the planned full fine-tune dataset.

## Category composition target
- 20-25% Authority / Abstention / Unknown (FACT_UNKNOWN, non-invention, missing evidence, ambiguity, fail-closed)
- 15-20% DB-vs-Simulation-vs-J-Space (canonical state is truth; HCU/J-Space/simulation only produce candidate/projection/measurement)
- 15-20% ClayCode + protocol syntax (structured outputs, types, state transitions, vector/control ABI)
- 10-15% Causal identity / provenance / generation (event vs admission ID, replay, stale generation, wrong provenance)
- 10-15% HCU/J-Space decisions (GRID10, competing candidates, hyperposition, confidence != majority truth)
- 10-15% Hard negatives (near-correct answers with exactly one dangerous error, e.g. simulation-as-fact, hash-as-loader-attestation, repetition-as-new-evidence)
- 5-10% Effect/action boundaries (candidate -> EffectRequest -> EffectGate; unknown outcome must not be blindly repeated)
- Cross-cutting across all categories: lesion/rescue, counterfactual, and abstention pairs (not a separate category)

## Key structural rule
**Family count matters more than raw row count.** Variations of the same
base case must NOT be spread across train/validation/holdout splits --
family-level separation is required by the bootstrap.

## Staged target ladder (not jumping straight to 10k)
Current: 0 admitted rows.

Next concrete gate: **256 admitted rows across >=64 distinct causal families.**
Large enough to actually exercise schema, admission, deduplication, family
formation, and hard-negative logic -- small enough that errors can still be
corrected before being multiplied a thousandfold.

Ladder after that: 256 -> 1,024 -> 4,096 -> 10,000+.

10,000 is realistic as the eventual first full-finetune dataset size, but is
NOT the next operational target. The immediate next production step is
getting the first 256-row "gold pilot" cleanly through the admission
pipeline (family splits + hard negatives working correctly) before scaling
generators to 1,024.

## Coordinator note (Claude Code)
This sets the concrete near-term coordination target for VPS work: build
toward 256 admitted rows / >=64 families through the existing admission
gates (provenance, OBSERVED producer auth, IN/NOT_IN, branch-birth,
quiescence), not toward 10,000 directly. Credit boundary remains 0 until
rows are genuinely admitted through all gates -- this plan does not itself
admit any rows.

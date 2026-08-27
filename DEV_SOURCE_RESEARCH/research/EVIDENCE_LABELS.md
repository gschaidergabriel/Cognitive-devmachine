# Frankenstein evidence labels

Use these labels next to material claims. A claim can change class only when new evidence satisfies the promotion rule; prose repetition never promotes it.

| Label | Meaning | Does it create runtime/product credit? |
|---|---|---|
| `CURRENT_SOURCE` | Present in current canonical source or current authority surface | No, by itself |
| `HISTORICAL_SOURCE` | Preserved source from an older product/epoch/repository | No |
| `PROJECT_MEASUREMENT` | Measured project result with bounded scope and stated identity | Only at its measured scope |
| `EXTERNAL_PRIMARY` | Primary paper, standard, official vendor documentation, or original external dataset/source | No project runtime credit |
| `INFERENCE` | Reasoned conclusion from observations | No |
| `OPEN_HYPOTHESIS` | Falsifiable proposal not yet established | No |
| `NEGATIVE_RESULT` | Failed, contradicted, blocked, or null result with preserved conditions | No positive credit; constrains design |

For archive synthesis, add the lifecycle classification:

`ATTEMPTED · SOURCE_READY · MEASURED · REPRODUCED · CONTRADICTED · BLOCKED · PREPARED_NOT_RUN · ADOPTED · RETIRED`

## Promotion law

A useful evidence ladder is:

```text
source invariant
  -> unit regression
  -> deterministic component integration
  -> exact-source isolated runtime
  -> multi-component causal path
  -> full admitted product/runtime acceptance
  -> scale/model-specific causal acceptance
```

A result cannot inherit the scope of a higher rung merely because the lower rung is green.

## Non-equivalences

```text
request != effect
model output != world fact
method exists != result exists
memory != observation
source-ready != runtime-observed
consensus/repetition != independent evidence
deployment exists != invocation succeeded
pre-load hash != bytes actually consumed by loader
logical cell count != resident model count != physical decode concurrency
reflection text != behavioral improvement
prediction != verified outcome
```

## Hypothesis record

Every important open hypothesis should record at least:

- `claim`
- `engineering_confidence` on a stated scale
- `supporting_evidence`
- `strongest_counterhypothesis`
- `falsifier`
- `next_discriminator`
- `promotion_scope`

Confidence is an engineering prioritization aid, not probability minted from prose.

## Negative evidence rule

Keep failures where they constrain the system. Examples include authentication failures, timeouts, rate limits, authority blocks, stale generations, integration failures, dataset leakage, rumination loops, model-family confounds, provider-boundary bypasses, and performance regressions.

Classify the failure correctly:

```text
transport/auth/quota failure != product logic failure
source mismatch != runtime regression
missing authority/lease != scientific negative
provider HARD-OFF != evidence that a provider model cannot perform the task
```

## Truth authority rule

Canonical durable facts are not created by a model, HCU candidate, J-Space readout, workspace recurrence, simulated world, majority vote, or self-report. Those outputs can become evidence inputs only through the normal typed/provenance-aware deterministic admission path.

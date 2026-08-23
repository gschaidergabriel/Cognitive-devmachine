# HCU HYPERPOSITION REALITY FIELD

Status: **OWNER-DIRECTED CORE COGNITIVE CONTRACT v1**
Date: 2026-08-23
Product: Mini Entity / EntityOS
Subsystem: Hyperposition Computational Unit (HCU)

## 1. Core law

The HCU MUST NOT derive its current world picture from one measurement, one model output, majority vote, or one simulation branch.

It MUST maintain a **Hyperposition Reality Field**: multiple materially different state views are held simultaneously, provenance-bound, weighted by evidence quality, and reduced into a working probabilistic reality estimate without erasing disagreement.

The result remains internal to the HCU and is always **Candidate / Measurement / Proposal**. It is never direct write authority for MiniUnifiedDB and never a direct effect path. New admitted live measurements or stronger evidence may revise it at any time.

`HCU_REALITY_FIELD != CANONICAL_TRUTH`

`HCU_REALITY_FIELD != MINIUNIFIEDDB_WRITE_AUTHORITY`

`HCU_REALITY_FIELD != EFFECT_AUTHORITY`

`MINIUNIFIEDDB = CANONICAL_DURABLE_EVIDENCE_STATE_AUTHORITY`

`EFFECTGATE = ONLY_ADMITTED_REAL_EFFECT_AUTHORITY`

## 2. Mandatory simultaneous views

For every material current-state question, the HCU SHOULD retain these view classes together:

| View | Meaning | Typical epistemic priority |
|---|---|---|
| `LIVE_MEASURED` | currently available admitted measurements/observations | normally highest when fresh, valid and well-characterized |
| `LAST_MEASURED` | most recent prior admitted measured state | high, decays with age and change pressure |
| `HISTORICAL_LEARNED_EXPECTATION` | expected current state inferred from validated historical transitions/regularities | medium-high when calibrated and in-domain |
| `HYPOTHETICAL_CURRENT` | current state under explicit assumptions/hypotheses | conditional, below direct evidence |
| `COUNTERHYPOTHETICAL_CURRENT` | strongest credible view constructed to contradict/falsify the leading current interpretation | adversarial, never suppressed by vote count |
| `FORWARD_SIMULATION` | future state after one or more simulated transitions | horizon-decayed and calibration-bound |

Additional typed views MAY be introduced, but they remain provenance-bound and non-authoritative.

## 3. Hyperposition before reduction

The HCU first holds an unresolved ensemble:

```text
R_t = {
  live measured views,
  last measured / historical views,
  learned expected-current views,
  hypothesis-conditioned current views,
  counterhypothesis / falsification views,
  forward / counterfactual simulated views
}
```

Only then may a reducer compute a working estimate:

```text
working_reality_t = Reduce({w_i, state_view_i, provenance_i, calibration_i})
```

The underlying alternatives MUST remain inspectable and recoverable. Reduction is not deletion of disagreement.

## 4. Weighting law

Weights are evidence-derived, not role-name constants. A weight MAY depend on:

- directness of observation;
- measurement quality and known error;
- freshness / valid-time distance;
- provenance strength;
- source independence and correlation penalty;
- historical calibration accuracy;
- domain match / out-of-distribution risk;
- contradiction pressure;
- simulation depth and forecast horizon;
- falsifier survival;
- entity-generation/session freshness;
- explicit uncertainty class.

Valid live measurement normally receives the greatest weight because it is closest to the present state, but:

`LIVE_MEASUREMENT != INFALLIBLE_TRUTH`

A low-quality, stale, correlated, malformed, or contradicted live observation MUST be down-weighted or kept unresolved rather than forced into truth.

No fixed numeric coefficient is canonical before empirical calibration.

## 5. Mandatory anti-collapse counter-view

For material state estimates, the HCU MUST actively construct at least one strongest credible counter-view when resources permit.

It asks, for example:

- What observation would make the leading state estimate wrong?
- What alternative causal mechanism explains the same live data?
- Which trusted source may be biased, delayed, correlated, or malformed?
- What expected observation is missing if the leading hypothesis is true?
- Which cheap measurement/intervention best discriminates the leading view from its strongest rival?

The purpose is not indecision. The purpose is to prevent premature collapse around the dominant interpretation.

`COUNTERHYPOTHESIS != NEGATIVE_FACT`

It remains a candidate until evidence discriminates it.

## 6. Temporal stitching

The HCU MUST distinguish four different objects:

```text
measured past
learned historical dynamics
expected present
measured present
```

A learned transition model may generate `HISTORICAL_LEARNED_EXPECTATION`, but this expectation MUST NOT overwrite contradictory live measurement. The conflict becomes a first-class Hyperposition/anomaly object and raises the value of another measurement or discriminator.

## 7. Forward reality and uncertainty decay

Future branches are part of the same field, but their epistemic weight decreases with horizon and accumulated model error unless calibration evidence supports otherwise.

A future branch MUST retain:

- causal anchor;
- assumptions;
- horizon/depth;
- predicted observations;
- uncertainty/calibration version;
- counter-branch or falsifier where practical.

A forecast score is a ranking/calibration quantity, not automatically a factual probability.

## 8. "Sharper reality" means better calibration, not manufactured truth

The HCU seeks a sharper working world picture by **holding uncertainty explicitly and multi-perspectivally before reduction**.

The intended contrast is:

```text
naive single-source belief update
        vs.
Hyperposition reducer with live evidence + temporal expectation + hypotheses + active counterhypotheses + calibrated simulations
```

If the architecture improves reality estimation, that improvement MUST be demonstrated empirically through prediction/outcome calibration, log-loss/Brier-like scoring where applicable, falsifier survival, anomaly detection, and held-out forecasting accuracy.

The quantum/superposition analogy is only an architectural metaphor for retaining alternatives. It is **not** evidence that quantum mechanics makes the HCU statistically superior.

`QUANTUM_ANALOGY != EMPIRICAL_PERFORMANCE_EVIDENCE`

## 9. Revision and canonical admission boundary

The working HCU reality estimate is always revisable.

```text
new admitted evidence
-> update view set
-> recompute weights/calibration
-> preserve contradiction history
-> produce revised Candidate/Measurement/Proposal
```

Only the normal Mini Entity evidence/state admission path may commit canonical durable state. Only EffectGate may authorize a real effect.

Therefore:

- HCU views may inform canonical admission but cannot perform it themselves;
- no high confidence score grants write permission;
- no majority vote grants truth;
- no simulation grants effect authority;
- no external LLM consensus grants truth;
- an unresolved field may remain unresolved indefinitely when evidence is insufficient.

## 10. Required evaluation

Before claiming that the Hyperposition Reality Field is more accurate than a simpler baseline, compare it against at least:

1. `LIVE_ONLY` baseline;
2. `LIVE_PLUS_LAST` baseline;
3. `NO_COUNTERHYPOTHESIS` ablation;
4. full Hyperposition Reality Field.

Measure at minimum:

- next-observation prediction error;
- calibration error;
- contradiction/anomaly detection;
- recovery after a misleading live measurement;
- robustness to correlated external-model outputs;
- accuracy degradation with forecast horizon;
- rate of false canonical-confidence escalation (must remain zero at authority boundary).

Promotion requires measured superiority, not conceptual elegance.

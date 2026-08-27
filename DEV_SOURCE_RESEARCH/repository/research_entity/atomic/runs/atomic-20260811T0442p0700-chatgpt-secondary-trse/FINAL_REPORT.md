# ATOMIC — TRSE-001 Transverse Recurrence Stability Envelope

## Final verdict

**TRSE-001 is killed as a distinct Frank runtime organ and as any claim of new stability mathematics.** Classical Poincare/Floquet, transverse-contraction and small-gain theory already cover the underlying dynamical-systems mechanisms.

A narrower result survives as a Frank v0.1 measurement/test obligation:

> `PRODUCTIVE_LIMIT_CYCLE` may be a useful trajectory/regime label, but a robustness claim about a recurrent loop-of-loops additionally requires evidence about the full-cycle perturbation return. For autonomous/phase-running recurrence, perturbations tangent to phase progression must be separated from perturbations transverse to the orbit.

Compact law:

`trajectory_periodicity != orbital_stability`

`local_loop_stability != composed_loop_of_loops_stability`

`phase_drift != transverse_divergence`

## Why this gap was selected

The current project source explicitly keeps productive limit cycles/metastability legal, warns that Jacobian/spectral-radius proxies are local research lenses rather than universal cognitive-quality metrics, and requires loop-regime measurement plus damping/anti-stagnation/overcoupling controls inside the one complete Frank loop-core. Existing loop-dynamics work already improved trajectory classification, trend/periodicity handling and the distinction between historical utility proxy and validated next-step marginal utility.

Therefore another scalar overthinking detector would be duplicate work. The remaining question is whether a trajectory that looks like a productive recurrence is robust to small perturbations of the coupled loop state.

## Hypothesis search

Fourteen mechanisms were compared: existing scalar regime/utility readout, max local Jacobian spectral radius, product of local radii, network small-gain, full monodromy return, Poincare map, transverse Floquet return, model-free twin perturbations, transverse contraction metrics, adaptive damping, phase-response coordinates, stochastic finite-time amplification, a learned classifier and an explicit conventional no-new-organ baseline.

The selected experimental lens combined H7/H8: phase-aligned transverse return estimation from matched perturbations. H14 remained the strongest counterbaseline throughout.

## Executable synthetic discriminator

Evidence class: `LOCAL_SYNTHETIC_REFERENCE_MODEL_ONLY`.

The deterministic seed-20260811 corpus contains 12,000 four-phase periodic linearized systems: 6,000 stable productive cycles and 6,000 unstable/overcoupled cycles. Every system has two transverse dimensions plus one neutral phase dimension in the full-return representation.

Two deliberately adversarial families test logical sufficiency rather than prevalence:

1. Stable family: one phase is locally expansive, but the complete recurrence contracts transversely.
2. Unstable family: every local phase has spectral radius below one, but non-normal/noncommuting cross-phase coupling makes the complete recurrence unstable.

Exact classification:

- scalar history-only: 50%;
- max local rho: 0%;
- product local rho: 50%;
- full return rho: 100%;
- transverse return rho: 100%.

The 0% local-rho result is deliberately adversarial and must not be reported as a real Frank error rate. It is a counterexample proving local labels are not logically sufficient for composed-loop stability.

### Distribution separation

Stable family:
- max-local-rho p50 ~1.1975;
- transverse-return-rho p50 ~0.4085.

Unstable family:
- max-local-rho p50 ~0.9165;
- transverse-return-rho p50 ~1.1500.

Thus the synthetic families intentionally reverse the local heuristic while preserving the full-return truth label.

## Phase/tangent ablation

A useful autonomous cycle can have a neutral multiplier corresponding to phase progression. The experiment therefore compares a noisy fit of the entire return map against a phase-aligned transverse fit that removes the neutral direction.

With 16 perturbation probes per fit:

- noise sigma 0.005: full 99.81%, transverse 100%;
- sigma 0.01: full 99.68%, transverse 100%;
- sigma 0.02: full 98.36%, transverse 100%;
- sigma 0.03: full 95.32%, transverse 99.97%;
- sigma 0.05: full 89.03%, transverse 99.70%;
- sigma 0.08: full 82.95%, transverse 99.11%.

At sigma 0.05 the full-return estimator produced 1,151 false-positive stable-cycle alarms and 165 false negatives; the transverse estimator produced 0 false positives and 36 false negatives in this constructed corpus.

This does not establish a production threshold. It demonstrates why a neutral phase dimension can materially reduce estimation margin if it is not separated from transverse perturbation growth.

## Coupling lesion/rescue

A matched canonical unstable family swept 51 cross-loop shear values. With both directed couplings present, median transverse return rho was ~1.1486 and 82.35% of the sweep was unstable. Lesioning either directed shear reduced median rho to ~0.3528 and made 100% of the sweep stable.

This is synthetic causal localization: instability is generated by the composition of couplings, not by either local contraction label alone.

## Prior-art destruction

The broad novelty claim does not survive research.

Poincare maps and Floquet multipliers are established periodic-orbit stability tools. Transverse contraction explicitly formalizes orbital stability by requiring contraction in directions transverse to the motion along the limit cycle. Hybrid limit-cycle work relates asymptotic orbital stability to Poincare-map fixed-point stability and studies robustness to perturbations. Small-gain theory already treats stability of interconnected subsystems as a network-level property. Recent RNN research also studies limit cycles as functional recurrent dynamical mechanisms.

Therefore TRSE cannot be promoted as new mathematics, and a standalone runtime organ has no evidence-based justification.

## Strongest counterhypothesis

`ordinary Poincare/Floquet/transverse-contraction or small-gain diagnostics + existing Frank loop controller`.

Result: **SUPPORTED for killing distinct-organ/novel-theory claims.** It remains unknown whether a named typed `RecurrenceStabilityEnvelope` improves engineering safety, reproducibility or model/runtime integration enough to survive as an interface object.

Kill rule: if existing typed receipts can carry conventional diagnostic results with equal real-target defect coverage, calibration, lesion localization and replay reproducibility at lower complexity, delete the TRSE named object and retain only the semantic/test law.

## Relation to current Frank loop work

TRSE does not replace the current trajectory probe. The current probe answers whether the observed trajectory resembles convergence, productive recurrence, stall, divergence/overthinking or unclassified behavior and whether continued computation is justified by valid next-step value evidence.

The retained transverse law answers a different question: if recurrence is being treated as a bounded useful orbit, does a small perturbation away from that orbit shrink over a complete recurrence, or does cross-loop coupling amplify it?

A stable transverse envelope cannot itself authorize continuation. Utility, unresolved pressure, compute/resource cost and all existing control/authority boundaries remain separate.

## Relation to GWT and overcoupling

Existing GWT evidence already shows stronger coupling can improve clean synthetic performance while amplifying injected corruption. TRSE does not add another GWT mechanism. It supplies a possible future way to localize whether a recurrent coupled assembly is perturbation-contracting or perturbation-amplifying across a complete cycle.

## Relation to UnifiedDB / temporal provenance

A future real perturbation experiment must bind the readout to exact state/semantic epoch, cycle/reference phase, perturbation basis and source baseline. Current UnifiedDB continuity work separately emphasizes durable event/sequence identity for causal order. TRSE does not mint temporal truth; it consumes admitted episode identity and invalidates its envelope when epoch/basis/baseline changes.

## Architecture consequence

No new Frank organ.
No new effect authority.
No continuation authority.
No truth promotion.
No new learning-credit mechanism.
No target product mutation.
No final training.

Retained candidate: a typed diagnostic interface/test obligation that may itself later disappear if a smaller conventional representation suffices.

## Highest-information real test

Only after a bounded real Frank loop component can be replayed with current ClayCode semantics and applicable Original Baseline evidence:

A. existing scalar/trajectory regime controller;
B. local Jacobian or per-loop gain heuristic where available;
C. conventional full Poincare/Floquet/return-map diagnostic;
D. phase-aligned transverse perturbation envelope carried as typed receipt.

Matched episodes must include productive periodic recurrence, benign phase drift, injected state error, single-loop gain perturbation, cross-loop gain perturbation, GWT corruption, re-entry delay change, stale readout, recovery/restart and OOD tasks.

Measure false continue, false halt/route, task outcome, next-step utility, perturbation amplification, recovery time, lesion localization, p50/p95/p99 diagnostic cost, CPU/RAM/context/token cost, reproducibility across restart/seeds, and whether the typed envelope rejects stale epoch/basis reuse.

If C and D are semantically equivalent and C is simpler, delete TRSE and keep the test law only.

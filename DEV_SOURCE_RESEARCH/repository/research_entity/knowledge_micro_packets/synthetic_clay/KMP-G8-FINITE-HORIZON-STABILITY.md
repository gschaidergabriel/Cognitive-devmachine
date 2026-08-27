<!-- RAE_META
{"packet_id":"KMP-G8-FINITE-HORIZON-STABILITY","title":"Spectral radius is insufficient for finite-horizon Clay change risk","domains":["synthetic-clay","systems-architecture","frank-gwt"],"topics":["M_delta","non-normality","transient-amplification","stability-certificate"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN_WITH_SYNTHETIC_SUPPORT","origin_actor":"chatgpt-secondary","run_id":"clay-20260808T0605p0700-chatgpt-secondary","canonical_parent":"r2:04234efd","confidence":0.9,"verification_required":true,"falsifier_or_next_test":"Fit rho, transient/non-normality and lagged propagation metrics to timestamped live FRANK invalidation tails."}
RAE_META -->

### Core
`rho(M_delta)` measures asymptotic amplification but does not bound short transient bursts when typed propagation is non-normal. G8 therefore proposes a finite-horizon certificate `{rho, transient_gain/non_normality, lag/delay, estimate_uncertainty, dominant_modes}`.

### Evidence / boundary
In `EXP-G8-NONNORMAL-001`, six 2x2 matrices all had `rho=0.88`, while peak finite-horizon gain ranged from 1.0x to 26.16x as off-diagonal coupling increased. Current 2026 non-normal-control literature independently supports the mechanism. The numeric sweep is synthetic and not a FRANK measurement.

### Implication
A spectrally stable Clay/FRANK projection must not automatically unlock aggressive coupling/re-entry. Finite-horizon amplification and uncertainty remain shadow tripwires.

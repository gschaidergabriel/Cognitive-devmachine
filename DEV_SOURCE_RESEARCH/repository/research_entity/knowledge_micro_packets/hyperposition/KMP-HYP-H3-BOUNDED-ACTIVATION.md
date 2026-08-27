<!-- RAE_META
{"packet_id":"KMP-HYP-H3-BOUNDED-ACTIVATION","title":"Higher-order activation should be bounded and stability-controlled","domains":["hyperposition","claygraph","emergence"],"topics":["spreading-activation","inhibition","oversmoothing","diffusion","salience"],"epistemic_class":"SYNTHESIS_HYPOTHESIS_WITH_PROXY_SUPPORT","claim_status_hint":"OPEN","origin_class":"HYPERPOSITION_H3_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T17:22:00+07:00","source_refs":["SYNAPSE arXiv:2601.02744","HNRD arXiv:2607.15773","Exa H3 results","EXP-HYP-H3-DIFFUSION-004"],"related_experiment_ids":["EXP-HYP-H3-DIFFUSION-004"],"confidence":0.82,"verification_required":true,"falsifier_or_next_test":"Ablate decay/inhibition/saturation/budget on real ClayGraph memory tasks with matched compute and measure accuracy, specificity, active-set size and recovery."}
RAE_META -->

### Core
Hyperposition should not maximize spreading or connectivity. Activation is a transient salience field whose diffusion strength, decay, inhibition, saturation and active-set budget require explicit control.

### Evidence / boundary
SYNAPSE combines spreading activation with lateral inhibition and temporal decay; 2026 hypergraph reaction-diffusion research gives a theoretical oversmoothing mechanism under strong higher-order mixing. H3's planted proxy retained ~0.909 seed-community mass with a top-400 budget versus ~0.454 under unbounded propagation, but the budget was deliberately favorable to sparsity and is not a cognitive-performance result.

### Implication
Track activation spread/noise/stability as a vector and preserve exact semantic truth separately from salience.

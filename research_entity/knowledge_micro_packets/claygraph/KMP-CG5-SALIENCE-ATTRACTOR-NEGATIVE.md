<!-- RAE_META
{"packet_id":"KMP-CG5-SALIENCE-ATTRACTOR-NEGATIVE","title":"Scalar downstream reward can create a self-confirming salience attractor","domains":["claygraph","clay","frank","emergenz"],"topics":["salience learning","reward credit","attractor","memory poisoning","rare-topic robustness"],"epistemic_class":"SYNTHETIC_NEGATIVE_RESULT_REPLICATED_IN_E2B","status_hint":"NEGATIVE_RESULT","origin_actor":"chatgpt-secondary","source_refs":["research_entity/trigger_runs/claygraph/claygraph-20260808T2212p0700-chatgpt-secondary-r3/EXPERIMENT_RESULTS.json","research_entity/runtime/tool_results/claygraph-g2a-e2b-v04-20260808T2212p0700.json"],"verification_required":true}
RAE_META -->

### Negative result
In a skewed online memory workload, assigning one downstream success scalar to every surfaced memory created a frequent-topic attractor even at zero injected poisoning: ~0.2867 top-1, ~0.0169 rare-topic accuracy and ~0.7133 false frequent-attractor top-1.

A constructed governor using context gating, itemwise credit, bounded gain, decay and topic caps reduced the false attractor to ~0.006 and restored ~0.991 top-1. However it uses a synthetic 96% verifier and therefore does not establish a production defense.

### Consequence
`utility may update salience` is too weak a rule. ClayGraph needs credit scope (`ITEM | PATH | ASSEMBLY | UNKNOWN`), bounded updates and anti-attractor controls. Unknown causal credit should not receive broad positive reinforcement.

### Boundary
These are synthetic mechanism rates, not FRANK rates. A recurring self-reinforcing activation pattern is not emergence evidence.

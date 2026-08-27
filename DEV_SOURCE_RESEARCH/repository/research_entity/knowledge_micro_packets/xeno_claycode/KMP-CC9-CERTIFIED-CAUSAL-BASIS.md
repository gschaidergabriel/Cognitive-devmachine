<!-- RAE_META
{"packet_id":"KMP-CC9-CERTIFIED-CAUSAL-BASIS","title":"ClayCode CC9 typed causal basis replaces universal latest/root validity","domains":["xeno_claycode","frank_architecture","claygraph","storage_state_memory"],"topics":["CognitiveFrame","graph epoch","activation epoch","basis witnesses","snapshot consistency","freshness"],"epistemic_class":"EXPERIMENT_MEMORY","claim_status_hint":"OPEN_REFINED_CANDIDATE","origin_actor":"chatgpt-secondary","origin_run":"claycode-20260808T1723p0700-chatgpt-secondary","canonical_parent_revision":2,"affected_branches":["frank","claygraph","clay","gwt","claycode"],"falsifier_or_next_test":"Instrument real FRANK/ClayGraph model turns and compare global-root-only, independent latest, strict tuple and operation-specific typed basis policies."}
RAE_META -->

## Result
CC9 refines FRANK C4 `CognitiveFrame` and CC8 OTCC into an operation-specific **typed causal basis**. A basis may bind `state_root`, `frame_id`, `graph_epoch_id`, `activation_epoch_id`, projection semantics and other witnesses, but only dimensions required by trusted operation semantics participate in compatibility.

Local 200k toy: independent latest reads formed mixed graph/activation/frame tuples in 8.9555% of generated cases; required tuple validation allowed 0 mixed cases. Judge0 50k replication: 8.736% mixed, 0 mixed passed. These rates are generator-specific.

## Boundary
A strict equality vector is not the universal answer. Unrelated epoch churn should not invalidate an operation that does not depend on that dimension. Production compatibility can use exact equality, lineage/causal relation, validity epoch or another deterministic typed proof. Unknown policy/coverage fails closed.

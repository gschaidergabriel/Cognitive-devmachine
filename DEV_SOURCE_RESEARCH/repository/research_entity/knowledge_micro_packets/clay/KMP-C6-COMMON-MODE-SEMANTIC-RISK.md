<!-- RAE_META
{"packet_id":"KMP-C6-COMMON-MODE-SEMANTIC-RISK","title":"Semantic unification trades boundary drift for common-mode Clay/compiler risk","domains":["clay","frank","claycode","claygraph","formal_methods_testing"],"topics":["common-mode","compiler","ontology","semantic-drift","differential-testing"],"epistemic_class":"ANALYTIC_SENSITIVITY_PLUS_REFERENCE_COUNTEREXAMPLE","claim_status_hint":"OPEN_ARCHITECTURE_RISK","origin_actor":"chatgpt-secondary","source_refs":["EXP-C6-BOUNDARY-001","EXP-C6-SCHEMA-CACHE-006"],"confidence":0.9,"verification_required":true}
RAE_META -->

### Core
One Clay semantic universe can eliminate many representation-conversion mismatches, but it also correlates failures: a wrong shared semantic primitive/compiler pass can coherently affect model view, memory, GWT and architecture.

### Evidence
An analytic sensitivity model shows the translation-boundary term drops as boundaries are removed. A separate C6 cache counterexample shows version/hash identity detects stale compilation but not a trusted compiler that computes the wrong semantics and emits a valid new hash.

### Implication
C6 needs independent/differential compiler implementations, property/mutation testing, exact receipts and cross-checks precisely because semantic unity reduces accidental diversity.

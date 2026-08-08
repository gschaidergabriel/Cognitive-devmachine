<!-- RAE_META
{"packet_id":"KMP-GROQ8B-HYP-ROLE-PROJECTION","title":"Small-model proxy favors explicit role-labelled relation-instance projection","domains":["hyperposition","claygraph","claycode","model_runtime"],"topics":["hyperposition","nary","role_binding","reification","reader_projection","pairwise_ambiguity","8b_proxy_for_4b"],"epistemic_class":"EXPERIMENT_MEMORY","claim_status_hint":"CURRENT_WITH_8B_PROXY_BOUNDARY","origin_class":"GROQ_8B_PROXY_EXPERIMENT_SUITE","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T07:45:00+07:00","updated_at":"2026-08-08T07:45:00+07:00","source_refs":["research_entity/runtime/groq_8b_proxy/SCIENTIFIC_SYNTHESIS.json","research_entity/runtime/groq_8b_proxy/VALIDATION_V3.json","research_entity/runtime/groq_8b_proxy/VALIDATION_V4.json"],"evidence_refs":["GROQ8B-F5-HYPERPOSITION-ROLE-PROJECTION"],"related_experiment_ids":["EXP-GROQ8B-HYP-ROLE-BINDING-V4","EXP-HYP-H2-RELATION-003"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.78,"verification_required":true,"falsifier_or_next_test":"Randomize role order and remove all positional leakage; compare canonical n-ary semantics projected as function syntax, relation-instance role edges and naive pairwise forms on actual 4B reader.","search_terms":["Hyperposition role binding","Groq 8B n-ary","relation instance role edge","pairwise ambiguity","ClayGraph role projection"]}
RAE_META -->

### Core
The 8B proxy did **not** find function-style n-ary syntax easiest to read. In the final labelled replication, the raw n-ary projection recovered only 2/8 sender/recipient relations before returning unknowns, while the role-labelled relation-instance edge projection recovered 6/8 relations from raw output. This is reader-side evidence, not a claim that canonical n-ary semantics should be removed.

### Relationship to H2
Hyperposition H2 independently showed that naive pairwise flattening can destroy role identity and create large spurious join spaces, while relation-instance IDs preserve n-ary role bindings by construction. The Groq experiment adds a different observation: **reader projection** can also benefit from explicit relation-instance + role labels. These two observations share conceptual ancestry and are not counted as independent replication of one experiment.

### Implication
Canonical ClayGraph/ClayCode may retain true n-ary relations where semantically necessary, but small-model-facing projections should preferentially materialize relation-instance identity and explicit role-labelled edges. The naive pairwise model arm remains methodologically confounded because source ordering leaked role order; it is not positive evidence for pairwise semantics.

### Boundary
Hosted 8B proxy only. Actual 4B and live Hyperposition backend equal-semantics tests remain open.

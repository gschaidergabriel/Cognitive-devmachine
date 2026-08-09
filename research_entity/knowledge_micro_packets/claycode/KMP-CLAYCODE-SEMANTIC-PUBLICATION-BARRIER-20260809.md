<!-- RAE_META
{"packet_id":"KMP-CLAYCODE-SEMANTIC-PUBLICATION-BARRIER-20260809","title":"Reader-visible semantic epoch barrier separates canonical commit from derived ClayGraph publication","domains":["claycode","unifieddb","claygraph","frank","harness","formal_methods_testing"],"topics":["semantic epoch","atomic publication","crash recovery","idempotency","authority","BASE_CLAYCODE_RELEASE"],"epistemic_class":"EXECUTABLE_RESEARCH_SYNTHESIS","claim_status_hint":"OPEN","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-09T16:09:00+07:00","source_refs":["research_entity/trigger_runs/claycode/claycode-20260809T1603p0700-chatgpt-semantic-publication/FINAL_REPORT.md"],"evidence_refs":["research_entity/trigger_runs/claycode/claycode-20260809T1603p0700-chatgpt-semantic-publication/EXECUTABLE_RESEARCH_RECEIPT.json"],"related_claim_ids":["H-CC-G9-PUBLICATION-CONTRACT-SUFFICIENCY-001","H-CC-PUBLICATION-PRIMITIVE-NECESSITY-002"],"related_experiment_ids":["EXP-CC-SEMANTIC-PUBLICATION-BARRIER-20260809"],"confidence":0.86,"verification_required":true,"falsifier_or_next_test":"Compile the receipt contract with the real BASE parser/IR/type-effect checker and inject crashes across physically separated canonical and derived stores; reject if mixed CURRENT, unstable replay, authority amplification or unrepresentable closure appears.","search_terms":["SemanticPublicationReceipt","PublishedSemanticEpoch","UnifiedDB ClayGraph publication barrier","mixed epoch crash recovery"]}
RAE_META -->

### Core
A run-local executable semantic oracle found no counterexample to representing FRANK P10/P11 coherence with existing G9-style records/rules/effect separation rather than a new transaction keyword. The clean replicated run passed **12/12 fixed adversarial cases** and **20,000 mutation rounds** with zero mixed-epoch or graph-authority violations.

### Refined mechanism
Treat `latest committed canonical state` and `reader-visible CURRENT semantic publication` as distinct identities. UnifiedDB may commit a new canonical state epoch while readers remain pinned to the previous coherent publication. ClayGraph rebuilds from the committed source epoch; only after source-epoch match, projection closure, retraction/invalidation closure and receipt validation does a `PublishedSemanticEpoch(state_epoch, graph_epoch, receipt)` become CURRENT.

### Authority boundary
ClayGraph relation/activation can motivate relevance or intent but never grants effect authority. Effect commit remains dependent on an independent valid host capability; revocation remains effective.

### Negative result
`NR-CC-NEW-PUBLISH-SYNTAX-20260809`: no dedicated publish/transaction syntax is justified by this test. Prefer a frozen canonical-IR/runtime contract first. This does not prove the future production checker can enforce it.

### Release implication
`CC-WP-03`, `CC-WP-04`, `CC-WP-05`, `CC-WP-07`, `CC-WP-09`, `CC-WP-11` and `CC-WP-13` gain a concrete acceptance fixture, but **no BASE work package passes** from this proxy alone.
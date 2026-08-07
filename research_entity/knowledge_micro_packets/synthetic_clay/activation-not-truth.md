<!-- RAE_META
{"packet_id":"KMP-CLAY-ACTIVATION-NOT-TRUTH","title":"Activation is ephemeral relevance, never epistemic truth","domains":["synthetic-clay","memory-state","gwt"],"topics":["activation","salience","truth","working-set"],"epistemic_class":"ARCHITECTURE_DECISION_SUMMARY","claim_status_hint":"CURRENT_WITH_VERSION_CHECK","origin_class":"RAE83_G1_SOURCE_ARCHIVE","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T00:00:00Z","updated_at":"2026-08-08T00:00:00Z","source_refs":["RAE83_G1:FINAL_SYNTHETIC_CLAY_CONCEPT.md","RAE83_G1:SYNTHETIC_CLAY_ARCHITECTURE_PROPOSAL.md"],"evidence_refs":[],"related_claim_ids":[],"related_experiment_ids":["EXP-C3-GOODHART"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.93,"verification_required":false,"falsifier_or_next_test":"Attempt adversarial cases where high salience conflicts with verified truth and verify that activation cannot mutate canonical epistemic status.","search_terms":["activation not truth","salience","working memory","active assembly","canonical truth"]}
RAE_META -->

### Core
Clay must keep activation/relevance separate from canonical evidence status. A canonically valid fact can be inactive; an uncertain or false proposition can be highly salient because it is urgent to test. Activation should change what enters the active working set, not what is true.

### Evidence / boundary
This is a design invariant reinforced by the G1 Anti-Goodhart result: optimizing an access metric can create degenerate active contexts even when underlying memory is unchanged.

### Implication
Truth/confidence, source trust, salience, goal utility and safety urgency require separate fields and update rules.

### Next test
Construct adversarial high-salience false/uncertain states and verify that selection changes while canonical epistemic status remains invariant.

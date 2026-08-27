<!-- RAE_META
{"packet_id":"KMP-CC11-MRSC-CLAY","title":"COVE should feed certified reader-specific rails rather than one universal surface","domains":["clay","claycode"],"topics":["COVE","multi-rail projection","loss budget"],"epistemic_class":"OPEN_ARCHITECTURE_REFINEMENT","claim_status_hint":"OPEN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T13:15:00Z","source_refs":["research_entity/trigger_runs/claycode/claycode-20260808T2015p0700-chatgpt-secondary-r2/EXPERIMENT_RESULTS.json"],"verification_required":true,"falsifier_or_next_test":"Compare COVE+rail-planning against one fixed surface across operation classes and small readers."}
RAE_META -->

### Core
Keep COVE as the trusted causal-slice compiler. After the exact slice is known, select/compile the reader rail using reader identity, operation semantics, effect class and cost. A lossy view may omit only semantics outside the trusted required slice.

### Evidence
Generic Nemotron-4B COVE compiled view improved 4/12 to 11/12 while reducing prompt tokens, whereas the typed-intent task showed a correctness/token tradeoff. This argues against one global surface optimum.

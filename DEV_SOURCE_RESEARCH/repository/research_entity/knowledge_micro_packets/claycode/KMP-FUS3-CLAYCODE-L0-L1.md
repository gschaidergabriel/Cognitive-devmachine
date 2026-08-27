<!-- RAE_META
{"packet_id":"KMP-FUS3-CLAYCODE-L0-L1","domains":["claycode","frank","synthetic_clay"],"origin_actor":"chatgpt-secondary","origin_run":"fusion-20260808T1855p0700-chatgpt-secondary-r3","epistemic_class":"FUSION_LANGUAGE_CONTRACT_DELTA","claim_status_hint":"OPEN","confidence":0.88}
RAE_META -->
# ClayCode feedback — Add an explicit intent compilation boundary

AINL and Vibe/intent-driven programming clarify two distinct ClayCode roles:

1. accept flexible L0 goals/preferences from humans/agents;
2. emit/maintain exact L1 canonical semantics for execution and reasoning contracts.

Candidate `IntentContract` fields:
- source/provenance;
- hard requirements;
- soft preferences/vibe;
- explicit prohibitions;
- unresolved ambiguity/unknowns;
- evidence/assumption refs;
- allowed effect class;
- compilation semantics hash.

Soft preference must not cast implicitly to FACT_EXACT, AUTHORITY_CAP or EFFECT_INTENT. Unknown effect-critical intent should broaden validation, ask/route for resolution, or fail closed.

AINL independently supports canonical IR + deterministic runtime. NURL discovery separately supports the idea that LLM-facing syntax can be regular/local without changing semantic authority. Keep semantic richness canonical and compile reader-efficient dialects rather than making compact syntax itself authoritative.

Next: extend CC-RC1.4/CBCC with an L0->L1 intent compiler contract and property/fuzz tests for ambiguous intent and authority escalation.
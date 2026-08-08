<!-- RAE_META
{"packet_id":"KMP-CC10-ICSL-CLAY","domains":["synthetic_clay","claycode"],"origin_actor":"chatgpt-secondary","origin_run":"claycode-20260808T1922p0700-chatgpt-secondary","claim_status_hint":"OPEN"}
RAE_META -->
# CC10 feedback to Clay — COVE starts after committed intent

COVE should consume a committed `IntentContract`, not raw prose/vibe. Lowering rules: HARD -> invariant/predicate; PROHIBITION -> deny invariant; ASSUMPTION -> evidence/predicate obligation; SOFT -> optimization preference only; effect-critical UNKNOWN -> escalate rather than default; authority reference -> required capability dependency only.

This preserves G10's smallest-sound-causal-slice principle while preventing the slice compiler from silently deciding what the user meant. Next experiment: differential IntentContract->COVE lowering with missing/negative/predicate dependencies and irreversible effects.
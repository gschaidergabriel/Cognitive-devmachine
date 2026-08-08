<!-- RAE_META
{"packet_id":"KMP-CC10-INTENT-FIREBREAK","domains":["hyperposition","claycode"],"origin_actor":"chatgpt-secondary","origin_run":"claycode-20260808T1922p0700-chatgpt-secondary","claim_status_hint":"OPEN"}
RAE_META -->
# CC10 feedback to Hyperposition — add language-layer firebreak identity

HYP-RC4 is strengthened: `IntentProposal`, `IntentAdequacyReceipt`, `IntentContract`, `FACT_EXACT`, `ACTIVATION_PRIOR`, `PROPOSAL`, `AUTHORITY_CAP`, and `EFFECT_INTENT` remain non-substitutable even when all use Clay vocabulary or the same canonical entity IDs.

Explicitly forbid implicit `L0 intent -> FACT/AUTHORITY/EFFECT` and `L2 native symbol -> FACT/AUTHORITY/EFFECT` casts. Adequacy evidence can permit commitment to an IntentContract but cannot grant a capability. Next: same-token/canonical-ID cross-layer substitution fault injection.
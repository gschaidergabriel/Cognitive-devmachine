<!-- RAE_META
{"packet_id":"KMP-CC10-ICSL-FRANK","domains":["frank","claycode"],"origin_actor":"chatgpt-secondary","origin_run":"claycode-20260808T1922p0700-chatgpt-secondary","claim_status_hint":"OPEN"}
RAE_META -->
# CC10 feedback to FRANK — intent adequacy before COVE

Add an explicit upstream chain:
`L0 source -> IntentProposal -> IntentAdequacyReceipt -> IntentContract -> COVE/CBCC`.

Do not change C6's owner-fixed Clay-native target. The new distinction is epistemic/causal: a model/parser may propose an interpretation, but a committed L1 contract must preserve hard vs soft vs unknown and source/verification ancestry. An adequacy receipt is not authority; authority references become capability dependencies checked at release.

Negative reader result: untrained Groq 8B scored raw NL 15/16, verbose typed L1 14/16, compact Clay-like view 9/16. Therefore keep CLAY_CANONICAL and CLAY_MODEL optimization separate and await target full-FT Qwen evidence.
<!-- RAE_META
{"packet_id":"KMP-CC10-ICSL","domains":["claycode","frank","synthetic_clay"],"origin_actor":"chatgpt-secondary","origin_run":"claycode-20260808T1922p0700-chatgpt-secondary","claim_status_hint":"OPEN","confidence":0.88}
RAE_META -->
# CC-RC1.5 — Intent-Certified Semantic Lowering (ICSL)

Candidate extension of CC-RC1.4/CBCC:

`L0 source -> IntentProposal -> IntentAdequacyReceipt -> IntentContract -> COVE/CBCC -> selection/projection -> model proposal -> capability gateway -> effect receipt`.

New hard distinctions:
- compiler/type/hash correctness != semantic intent adequacy;
- soft preference != hard constraint;
- unknown != false;
- authority reference != capability;
- adequacy receipt != authority;
- IntentContract != canonical world fact;
- CLAY_CANONICAL != necessarily optimal CLAY_MODEL surface.

Synthetic + Judge0 tests support targeted effect-critical escalation over universal confirmation in the constructed workload. Groq 8B is a negative reader result: raw natural language 15/16, verbose typed 14/16, compact symbols 9/16. Do not promote compact syntax until target full-FT Qwen evidence.

Independent current work on intent compilation, permission IR/SMT authorization, effect-typed agent languages and compiled workflow harnesses supports the architecture class while preserving the intent-oracle gap.
<!-- RAE_META
{"packet_id":"KMP-CC10-INTENT-ANCESTRY","domains":["claygraph","claycode"],"origin_actor":"chatgpt-secondary","origin_run":"claycode-20260808T1922p0700-chatgpt-secondary","claim_status_hint":"OPEN"}
RAE_META -->
# CC10 feedback to ClayGraph — intent is ancestry, not truth

Represent separately: raw intent/source, derived `IntentProposal`, `IntentAdequacyReceipt`, and committed `IntentContract`. Preserve extractor/verifier versions and source-span ancestry. None of these automatically upgrades quoted/user intent into `FACT_EXACT`.

If CLAY_MODEL/VQ symbols later encode intent, their codebook/version is a projection receipt to canonical anchors. Model-codebook drift must invalidate/reproject the model view, not rewrite canonical history.

Next: replay identical historical intents through changed extractor/model versions and compare contracts while exact source/owner contracts remain pinned.
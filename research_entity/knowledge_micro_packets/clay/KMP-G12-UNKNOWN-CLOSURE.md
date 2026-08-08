<!-- RAE_META
{"packet_id":"KMP-G12-UNKNOWN-CLOSURE","title":"Unknown dependencies require conservative closure broadening","domains":["clay","unifieddb","frank","hyperposition"],"epistemic_class":"EXECUTABLE_SYNTHETIC_NEGATIVE_RESULT_AND_REPAIR","status_hint":"NEGATIVE_RESULT_OPEN_TRANSFER","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T14:45:00Z","source_refs":["research_entity/runtime/tool_results/clay-g12-e2b-cacc-20260808T2132p0700.json"],"verification_required":true}
RAE_META -->

### Result
In 200,000 E2B synthetic operations, hiding one true dependency in 8% of episodes caused narrow scoped revalidation to accept invalid state in 0.578% of all cases. A constructed conservative policy that globally broadened only when closure was marked unknown reduced unsafe accepts to 0 while rejecting 22.0215%, versus 63.306% for always-global validation.

### Transfer
MOSAIC/CACC should distinguish `KNOWN_VALID`, `KNOWN_INVALID`, and `UNKNOWN`. Unknown dynamic scope must broaden, escalate, recompute or deny a consequential effect; it must not silently inherit the narrow known-closure guarantee.

### Boundary
This is a constructed mechanism test, not a production safety proof.

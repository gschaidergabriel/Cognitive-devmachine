# Clay Status Footer Protocol — legacy path retained for compatibility

This path remains because existing tools/bootstrap files reference it. The current canonical rendering contract is `research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md` and MUST be followed.

Entity display name: **Clay**.
Stable entity ID: `frank-project-global-research-entity`.
Legacy `RAE` is namespace/history only.

Every substantive visible Clay response ends with exactly one final plain fenced Markdown block. Opening fence must be exactly ` ```text ` with no attributes. No visible content may follow the closing fence.

Required heading: `CLAY STATUS`.
Required goal line: `Goal: Frank v0.1 voll lauffähig auf Andreas PC`.

Exact `clay` now addresses/names the Clay entity and is NOT a research trigger. The old integrated foundry trigger is `clayresearch`.

Current short commands:
`666 · q12 · dump · fusion · hypofusion · clayresearch · gwt · frank · emergenz · claycode · hyperposition · claygraph · unifieddb · harness`

NEXT LEVEL and DOOMSDAY values remain dynamic and must be resolved from current program/forecast state/tools when available. Never copy stale fixed percentages/dates simply because they appeared in an older footer.

Canonical template:

```text
CLAY STATUS
Entity: <JOINED|DEGRADED_UNJOINED|LOCAL_ONLY>
GitHub: <VERIFIED_RW|VERIFIED_RO|UNVERIFIED|FAILED>
Canonical: <revision/hash>
Organ: <current organ/provenance>
Trigger: <none|registered trigger>
Research write: <COMMITTED|NO_RESEARCH_DELTA|SYNC_PENDING|NOT_ATTEMPTED>
Goal: Frank v0.1 voll lauffähig auf Andreas PC
Short commands: 666 · q12 · dump · fusion · hypofusion · clayresearch · gwt · frank · emergenz · claycode · hyperposition · claygraph · unifieddb · harness

NEXT LEVEL
Stage: <dynamic stage label>
Progress: [#####...............] <percent>
ETA @ 10h/day: <low> - <high>
ETA confidence: <confidence + basis>

DOOMSDAY / Clay 0.1 - Chief Developer First Test
Progress: [###############.....] <percent>
Historical calibration band: <optional dynamic calibration>
Forecast: <range>
Center: <date>
Confidence: <confidence>
Conditional on immediate training authorization when data is ready: <yes|no>
Forecast basis: <dynamic basis>
```

Pre-send check: one final block; exact ` ```text ` opener; no `id=` attribute; ASCII progress bars; `clayresearch` present; `clay` absent from commands; nothing after closing fence.

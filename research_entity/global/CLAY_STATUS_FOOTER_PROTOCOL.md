# Mandatory Clay Visible Status Footer

Every substantive visible response by a Clay organ ends with exactly one final plain Markdown fenced block. Nothing visible follows it.

Opening fence line MUST be exactly:

```text

No attributes. Never ` ```text id=... `. No Unicode box/table frame.

The entity is now **Clay**. Stable internal entity ID remains `frank-project-global-research-entity`. Legacy `RAE` may appear only in old paths/schema/version identifiers.

Exact `clay` is the entity name/address and is not a reserved scientific trigger. The former integrated Clay foundry command is now `clayresearch`.

Exact `go` is the global recursive live-knowledge research/build/test continuation trigger governed by `research_entity/triggers/GO_RECURSIVE_SWARM_CYCLE_PROTOCOL.md`.

## Dynamic progress law

Every visible progress bar in this footer is a live derived value. No bar percentage, filled-cell count, ETA or forecast date may be copied from an older response or hard-coded into a trigger protocol.

Before rendering a substantive status footer, resolve current progress from repository state using `tools/program_progress.py` or an equivalent calculation over the same current sources.

For an exact `frank` trigger, resolve with the semantic equivalent of:

`python tools/program_progress.py --trigger frank`

This adds a live milestone block for the first complete GitHub-based FRANK Harness. Its target is the H1 Reference Harness and its percentage is derived from the current H1 work-package completion state declared by `PROGRAM_STATE.json` and `HARNESS_WORKSPACE.json`. `CLAIMED`, `ACTIVE`, `IN_PROGRESS` or merely written-but-unexecuted work does not count as complete. An H1 stage PASS resolves the milestone to 100%.

All bars use the current configured bar-cell count and fill proportionally from their current calculated percentage.

Required base form:

```text
CLAY STATUS
Entity: JOINED|DEGRADED_UNJOINED|LOCAL_ONLY
GitHub: VERIFIED_RW|VERIFIED_RO|UNVERIFIED|FAILED
Canonical: <revision/hash>
Organ: <current organ/provenance>
Trigger: <none|registered trigger>
Research write: COMMITTED|NO_RESEARCH_DELTA|SYNC_PENDING|NOT_ATTEMPTED
Goal: Frank v0.1 voll lauffähig auf Andreas PC
Short commands: 666 · go · q12 · dump · fusion · hypofusion · clayresearch · gwt · frank · emergenz · claycode · hyperposition · claygraph · unifieddb · harness · spawn

NEXT LEVEL
Stage: <dynamic stage label>
Progress: <dynamic 20-cell bar> <dynamic percent>
ETA @ 10h/day: <dynamic low> - <dynamic high>
ETA confidence: <dynamic confidence + basis>

DOOMSDAY / Clay 0.1 - Chief Developer First Test
Progress: <dynamic 20-cell bar> <dynamic percent>
Historical calibration band: <optional dynamic calibration>
Forecast: <dynamic range>
Center: <dynamic date>
Confidence: <dynamic confidence>
Conditional on immediate training authorization when data is ready: <yes|no>
Forecast basis: <dynamic basis>
```

For exact `frank`, insert this additional dynamically derived block between NEXT LEVEL and DOOMSDAY:

```text
FIRST GITHUB FRANK HARNESS
Target: H1 Reference Harness
Progress: <dynamic 20-cell bar> <dynamic percent>
Gate: <dynamic H1 gate status>
Basis: <dynamic completed H1 work-package weight / total H1 work-package weight>
```

The additional block is trigger-specific; its underlying metric remains available from the resolver even when not displayed.

Dynamic NEXT LEVEL/DOOMSDAY/H1 values must come from current program/workspace/forecast state and tools when available. Never copy stale numbers merely because an older footer contained them.

Pre-send invariant:
1. one final fenced text block;
2. opener exactly ` ```text `;
3. heading exactly `CLAY STATUS`;
4. goal present;
5. short commands include `go` and `clayresearch` and exclude `clay`;
6. every displayed progress bar was resolved from current state for this response;
7. exact `frank` includes the dynamic FIRST GITHUB FRANK HARNESS block;
8. no visible content after closing fence.

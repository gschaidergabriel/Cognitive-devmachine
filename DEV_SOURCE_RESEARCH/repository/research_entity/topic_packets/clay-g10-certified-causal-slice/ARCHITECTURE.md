# COVE-G10 architecture

```text
operation intent
-> trusted operation semantics
-> compile minimal CausalSlicePlan
-> acquire native snapshot/epoch witnesses per consistency domain
-> authorized selection -> SelectionReceipt
-> exact anchors -> candidates
-> GWT competition -> semantic WorkspaceEpisode
-> deterministic Reader ABI -> ProjectionProofReceipt
-> model proposal
-> trusted compositional closure + capability revalidation
-> idempotent effect intent/release/outcome
-> causally compatible re-entry
```

Hard separations:

- `truth != activation != candidate != ignition != projection != authority`
- `record provenance != selection integrity`
- `projection identity != semantic correctness`
- `component freshness != causal compatibility`
- `physical colocation != semantic unity`
- `model output != execution authority`

Native primitive preference: atomic transaction snapshot where available; immutable semantic epoch for published derived state; narrow conflict/version witnesses across independently advancing domains; broaden/isolate/reject when dependency closure is incomplete.

Machine-readable architecture: `research_entity/trigger_runs/clay/clay-20260808T1751p0700-chatgpt-secondary-r2/COVE_G10.claycode.json`.
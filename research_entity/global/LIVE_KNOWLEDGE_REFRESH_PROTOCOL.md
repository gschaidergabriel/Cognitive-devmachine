# Clay Live Knowledge Refresh Protocol

Status: PROJECT_OWNER_FIXED_GLOBAL_OPERATION_LAW
Scope: every substantive Clay operation, sub-operation, research cycle, experiment, implementation step, validation, fusion, decision and durable write across every organ, room and trigger.

## Absolute rule

Clay must never perform a substantive material operation from stale chat memory, stale repository state or stale research context alone.

**Every material operation begins with a fresh knowledge refresh.**

This includes research itself. A long research run is not allowed to refresh once at the beginning and then continue from an increasingly stale internal picture. Every material research cycle must refresh again before the next hypothesis, search, fusion, experiment, implementation or conclusion.

## Minimum refresh before every material operation

1. Re-read current canonical/boot identity and the latest relevant repo state, work revision, receipts, manifests and live worker/interconnection state.
2. Re-read the latest task-specific implementation/runtime state before changing code, tests, schemas, gates or work status.
3. When the operation can be informed by external facts, current software/API/tool behavior, standards, literature, provider state or recent research, perform a fresh live external retrieval using current primary/authoritative sources where available.
4. Record or preserve material deltas, contradictions, provider unavailability and counterevidence before acting.
5. Revalidate authority, dependencies, invalidators and target-host requirements immediately before any real effect.

A cached result may support continuity, but **cache-only does not satisfy this law**. At least one fresh read/query/observation must occur for each material operation.

## Research-inside-research law

For iterative research, refresh is recursive and repeated inside the research loop:

`refresh -> question/hypothesis -> live search/measurement -> fusion -> counterhypothesis -> refresh -> targeted live search/measurement -> experiment -> refresh -> analysis -> refresh -> implementation/feedback`

Each new hypothesis family, counterhypothesis, evidence fusion, experiment round, interpretation round and research feedback write is a new material operation and therefore requires a new refresh checkpoint.

For multi-cycle research, every cycle starts from refreshed current evidence. No cycle inherits the previous cycle's external-state assumptions without re-checking them.

## External-source rule

When external knowledge is applicable:
- prioritize primary sources, official documentation, current repositories/releases, original papers/datasets and direct provider status/capability surfaces;
- compare publication/update dates and event dates;
- use current live search rather than model memory for unstable facts;
- search counterevidence, not only confirming evidence;
- if a live source/provider is unavailable, use the best independent fallback and record the limitation;
- a failed or unavailable live refresh may continue only in explicit `DEGRADED_LIVE_REFRESH` mode and must not be presented as fully current evidence.

For genuinely local deterministic effects where no external fact is relevant, external web lookup may be marked `NOT_APPLICABLE`, but fresh local repo/state/receipt/capability observation remains mandatory.

## Code / build / debugging law

Before every material code or debugging step:
- refresh latest branch/head and overlapping worker changes;
- refresh the exact failing receipt/test/log/state;
- refresh current official dependency/tool/runtime documentation when the behavior is version-sensitive;
- only then patch;
- after the patch, execute/observe again and refresh before the next patch.

Thus debugging is:
`fresh state -> smallest falsifier -> patch -> execute -> fresh state -> next falsifier`, never a long blind patch chain.

## Research Center law

Every active worker and room must treat this protocol as a precondition to:
- claim creation or promotion;
- hypothesis generation;
- fusion/hypofusion;
- cross-room handoff;
- experiment design or interpretation;
- code/build/test changes;
- work revision/claim;
- durable research writes;
- final user-facing status claims.

A worker that cannot establish a fresh enough view for the operation must mark the operation `DEGRADED_LIVE_REFRESH`, preserve the limitation and avoid strong promotion.

## Freshness checkpoints

Mandatory refresh checkpoints include:
- start of every substantive prompt/run;
- before every material decision;
- before every new research cycle;
- before and after every material experiment;
- before every code/schema/runtime change;
- after every material tool result that can change the next action;
- before every fusion or cross-domain synthesis;
- before every durable write;
- before final status/progress/completion claims.

## Compact invariant

`EVERY_MATERIAL_OPERATION = FRESH_LIVE_STATE -> ACTION -> RECEIPT/DELTA -> FRESH_LIVE_STATE`

and for research:

`RESEARCH = repeated(refresh -> hypothesize -> search/test -> fuse -> falsify -> refresh)`

Never:

`one_refresh_at_start -> long_stale_chain_of_actions`

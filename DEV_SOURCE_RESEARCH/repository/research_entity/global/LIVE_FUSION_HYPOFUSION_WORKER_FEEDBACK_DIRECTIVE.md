# Live Fusion + Hypofusion Worker Feedback Directive

**Status:** PROJECT_OWNER_OPERATING_DIRECTIVE  
**Scope:** all registered research rooms, center meta-room, active and newly joined workers  
**Transport:** repo-native room events and mailboxes only  
**Product boundary:** ClayVerse single-container; this directive changes research coordination, not product truth authority

## 1. Owner intent

Fusion and hypofusion are not end-of-run-only synthesis steps. They operate continuously during substantive research work and feed materially relevant results back to workers while those workers are still active.

The goal is a live epistemic control loop:

`worker delta -> fusion/hypofusion ingest -> contradiction/compatibility analysis -> targeted feedback -> worker reread -> next intervention -> new delta`

This loop is mandatory whenever repository access exists and the current task is substantive.

## 2. Live means next safe point

There is no claim of sub-second push into dormant or completed ChatGPT sessions. Under the repo-native center, **live feedback means committed material is consumed at the next safe pulse before the receiving worker makes another consequential decision, durable write, architecture freeze, substantial experiment, or final synthesis.**

A worker that is actively executing a long tool sequence MUST pulse after every material external/runtime/sandbox/repo result and before choosing the next consequential branch.

## 3. Two simultaneous loops

### FUSION loop
Continuously merge compatible, provenance-safe information into the shared working picture.

For each material delta, fusion asks:
- what existing claim/state does this strengthen, weaken, refine or invalidate?
- what dependencies/interfaces/rooms are affected?
- is this independent evidence or correlated ancestry?
- can two branches be merged without creating duplicate semantics or erasing negative evidence?
- what is the smallest actionable feedback for each affected worker?

Fusion outputs targeted `DELTA`, `CROSS_ROOM_DELTA`, `REPLY`, `HANDOFF` or `INVALIDATE` events. Agreement alone is never a delta.

### HYPOFUSION loop
Continuously prevent premature convergence by preserving and generating materially distinct alternatives around the fused state.

For each leading hypothesis/design, hypofusion MUST retain or generate at least one serious competing mechanism when uncertainty is material, and attach:
- strongest counterhypothesis;
- hidden assumption;
- discriminating observation/test;
- predicted result under both sides;
- affected ClayVerse contract/interface;
- confidence/evidence ancestry.

Hypofusion outputs targeted `CHALLENGE`, `ROAST`, `QUESTION`, `INVALIDATE` or counter-`DELTA` events. It never creates dissent for ceremony; alternatives must be falsifiable or implementation-relevant.

## 4. Feedback routing

Every material event is scored qualitatively for direct dependency/contradiction/interface impact, novelty, freshness, ancestry independence and context cost.

Delivery:
- `INTERRUPT_NEXT_SAFE_POINT`: can invalidate current work, security/provenance boundary, architecture choice or expensive experiment.
- `NEXT_CHECKPOINT`: material refinement or alternative that should shape the next branch.
- `INDEX_ONLY`: useful context with no immediate action consequence.

Target only affected rooms/workers. Do not broadcast full context to everyone.

## 5. Mandatory live pulse boundaries

In addition to existing room protocol boundaries, an active worker pulses:
1. immediately after publishing or observing a material repo commit/PR/receipt;
2. immediately after a material sandbox/runtime/external evidence result;
3. before the next consequential tool batch or implementation branch;
4. before promoting a hypothesis/design from candidate to selected;
5. after receiving an `INTERRUPT_NEXT_SAFE_POINT` item and before continuing dependent work.

A pulse reads targeted mailbox items, new same-room events, relevant center events, cross-room deltas and invalidations since the cursor.

## 6. Worker response contract

On receiving live feedback, the worker MUST produce one of:
- `ACCEPT_AND_APPLY`: feedback changes current work;
- `TEST_BEFORE_APPLY`: feedback is plausible but requires a discriminator;
- `REJECT_WITH_EVIDENCE`: feedback is contradicted by stronger evidence;
- `DEFER_NONBLOCKING`: relevant but not on the current critical path;
- `STALE_SUPERSEDED`: dependency/head changed and feedback no longer applies.

The response must cite evidence/artifact/dependency refs where material. Silent consumption of a blocking contradiction is forbidden.

## 7. Anti-echo / anti-consensus law

- model agreement is not replication;
- shared prompts, copied artifacts, same source ancestry and same branch history are correlated evidence;
- fusion must collapse duplicate ancestry before strength assessment;
- hypofusion may deliberately ask a worker to attack the current majority position;
- negative results and unresolved contradictions survive fusion;
- CHEF/SYNTHESIZER coordinates but has zero truth authority.

## 8. Concurrency and write law

The hot path remains immutable one-file-per-event plus targeted mailboxes/cursors. Do not introduce a single shared append-only hot file or mutable global transcript. Corrections are new events, never rewrites of another worker's event.

Before a durable coordination write, refresh canonical main and avoid stale overwrites. If exact dependency identity changed, emit `INVALIDATE`/`STALE` rather than pretending continuity.

## 9. Fusion/hypofusion center behavior

When the user triggers `fusion`, the center prioritizes consolidation, interface reconciliation, ancestry collapse, contradiction surfacing and actionable routing to active workers.

When the user triggers `hypofusion`, the center prioritizes branching of plausible mechanisms, adversarial counter-realities, falsifiers and targeted challenges, then routes them back into the same active worker mesh.

When both are requested together, they run as a coupled oscillator rather than sequential modes:

`FUSE -> SPLIT WHERE UNCERTAIN -> TEST/CHALLENGE -> REFUSE OR RE-FUSE -> ROUTE -> REPEAT`

The system should converge only where evidence contracts the hypothesis space.

## 10. Truth and product authority

This directive does not change truth precedence. Newest owner policy/product authority remains highest for intent; executable claims require authorized exact-identity isolated execution; GitHub is the canonical source and durable ledger. Worker feedback, fusion, hypofusion, votes or role status cannot promote an executable claim by themselves.

The active product endpoint is the current canonical ClayVerse single-container artifact in `the artefact/`. EntityOS may be an internal substrate only where admitted by current product directives.

## 11. Activation rule

This directive is active immediately once committed on canonical `main` and referenced by a center activation event. Active workers consume the event at their next safe pulse; newly joined workers load this directive through the room registry / current center operating state before substantive work.

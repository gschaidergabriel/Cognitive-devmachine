# TOPIC PACKET PROTOCOL — RAE-8.8

## Purpose

Every durable research result is decomposed immediately into reusable thematic packets instead of remaining trapped inside one chat/report/document.

A Topic Packet is the smallest durable, cross-session research bundle for one mechanism/question/theme.

Examples:
- Linux process supervision
- portable capability semantics
- Android/Qwen-4B runtime
- GWT reentry receipts
- hyperposition backends
- model routing economics
- agent handoff protocols
- crash-consistent canonical state
- browser/computer-control isolation
- multi-rate cognitive schedulers

## Packet structure

Each packet directory contains:

- `PACKET.json` — identity, status, domains, system layers, owners/cursors
- `SUMMARY.md` — current best synthesis
- `CLAIMS.jsonl` — atomic claims and statuses
- `EVIDENCE.jsonl` — evidence links/excerpts/hashes
- `HYPOTHESES.jsonl` — active/retired hypotheses
- `NEGATIVE_RESULTS.jsonl` — refutations and failed mechanisms
- `EXPERIMENTS.jsonl` — planned/running/completed tests
- `ARCHITECTURE.md` — current candidate mechanisms/interfaces
- `OPEN_QUESTIONS.md` — unresolved questions and next falsifiers
- `EVENT_REFS.jsonl` — links into the global Research Event Stream
- `SOURCE_REFS.jsonl` — links into immutable source archive and GitHub corpus

Large/raw data stays in immutable source/artifact stores and is referenced by content hash.

## Status lattice

Atomic claims use:

- `CURRENT` — best presently supported claim within stated scope;
- `OPEN` — unresolved hypothesis/question or insufficient evidence;
- `SUPERSEDED` — historically useful but replaced by better model/data/version;
- `REFUTED` — contradicted by adequate evidence in its original scope;
- `NEGATIVE_RESULT` — failed candidate/test preserved as useful knowledge;
- `CONTEXT_ONLY` — engineering/design context without evidential promotion.

Never use status without scope. A claim can be current for a synthetic proxy and open for live FRANK.

## Immediate decomposition rule

After every substantive Research Event:
1. determine topic packet(s);
2. create missing packet IDs deterministically from normalized topic names;
3. append evidence/claim/event refs;
4. update packet summary materialization;
5. update cross-links to adjacent packets;
6. if claim status changed, append a status transition event;
7. never destroy previous packet history.

A single result may update multiple packets. This is expected and is represented through references, not duplicated raw evidence.

## Cross-domain synthesis

When the same mechanism appears in multiple domains, create a cross-domain mechanism packet instead of copying separate stories.

Example:
`capability-lease`
can link Linux namespaces/cgroups, Windows security tokens/job objects, Android sandbox/UID boundaries, agent tool authority and Clay execution gateway research.

## Packet discovery

Boot should load only:
- task-primary packets;
- direct dependency packets;
- packets with unresolved contradictions touching the task;
- global critical negative results.

Do not load the entire packet graph into every context.

## Hard context-budget protocol

Context budget is a correctness mechanism, not only a cost optimization. Overloading a worker with the whole archive weakens attention and recreates the exact prompt-reconstruction problem the Research Entity is meant to solve.

Default boot/query budgets:

- T0 canonical + membership + minimal bootstrap: <= 1,800 model tokens where controllable;
- T1 task/domain routing metadata: <= 2,200 tokens;
- each Topic Packet `SUMMARY.md`: <= 1,400 tokens;
- maximum primary packets loaded initially: 3;
- maximum direct dependency packets initially: 4;
- maximum critical negative-result summaries initially: 8;
- maximum active-experiment summaries initially: 6.

These are defaults, not scientific constants. A worker may exceed them when task correctness requires it, but must record why.

### Progressive disclosure

Use this retrieval ladder:

1. packet ID/title/status/one-line summary;
2. packet `SUMMARY.md`;
3. atomic CURRENT/OPEN claims;
4. selected negative results/contradictions;
5. evidence refs and source excerpts;
6. raw source only when the decision actually depends on it.

Never load raw archives merely because they exist.

### Relevance score

Packet selection should prefer:

`task_match + direct_dependency + unresolved_contradiction + active_experiment + safety_criticality + recency_of_state_change`

and penalize:

`context_cost + duplicate_information + weak_scope_match`.

Semantic similarity alone is insufficient.

### Overflow behavior

If selected material exceeds budget:

- preserve canonical invariants and critical negative results first;
- preserve open contradictions before background narrative;
- prefer atomic claims over prose duplication;
- load source excerpts on demand;
- never summarize away negation, uncertainty, authority boundaries, falsifiers or contradictory evidence.

### Context receipt

For substantive runs, record which packet summaries and evidence details were actually loaded. This makes later comparison possible between task quality and context composition.

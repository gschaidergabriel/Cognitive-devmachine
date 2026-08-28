# Frankenstein Architecture Ingest — Triggerword 5

This directory is the persistent handoff surface between parallel source-archaeology workers and the ChatGPT architecture-integration lane.

## Directories

Workers should write immutable packets under:

`research_entity/frankenstein_architecture_ingest/inbox/`

Accepted/consumed packet IDs are referenced by Triggerword-5 ingestion receipts. Do not overwrite accepted packets; create a superseding packet instead.

## Worker contract

Pin `gschaidergabriel/frankenstein` to one exact donor SHA before analysis.

Use `INGEST_PACKET_SCHEMA.json`.

Prefer bounded source spans and many small semantic atoms over one large prose summary.

For every material claim distinguish:

- specification/comment intent;
- executable enforcement;
- runtime reachability;
- test/runtime evidence;
- historical/superseded behavior.

Architecture-bearing comments and docs are valuable, but a comment is not proof that the live path enforces the behavior.

## Suggested worker partitioning

Parallel workers may partition by subsystem, for example:

1. UnifiedDB / schema / migrations / identity / effects / tasks / Room;
2. hook/runtime lifecycle / stern / installer / services;
3. Visual Cortex / Retina / Motion / Familiarity / Active Sensing;
4. Voice / Realtime / VoiceSessionCapsule / initiative / Barge-in / outcomes;
5. retrieval / MicroClay / graph / FTS / embeddings / workspace;
6. tests / evidence / negative results / supersession history;
7. UI / control planes / human-editable policies;
8. current architecture dossiers and their implementation coverage.

Workers should recommend the next unexamined source spans rather than independently restarting repository discovery.

## ChatGPT ingestion

When `triggerwort 5` is invoked, ChatGPT should search for newest unconsumed packets, cross-check high-impact atoms against the pinned donor source, then incorporate supported deltas into the Frankenstein-2.0 architecture model.

The inbox provides durable near-live handoff across workers and chat sessions. There is no claim that ChatGPT receives an unsolicited real-time push while no turn is running; new packets are pulled and integrated during an active Triggerword-5 run.

## Relationship to Triggerword 4

Triggerword 5 = source archaeology + architecture understanding.

Triggerword 4 = VPS assembly + testing + migration + optimization.

Triggerword 5 should make Triggerword 4 increasingly implementation-grounded and prevent valuable existing mechanisms from being accidentally replaced.
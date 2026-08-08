# Frank Founding-User Usage Ingest Protocol

## Purpose
Turn privacy-reviewed real-use outputs from `gschaidergabriel/Dr.-Unterweger` into evidence for ClayGraph/FRANK research without merging the two persistent entities.

## Source repositories and authority
Clay may READ Frank exports. Frank may READ Clay questions/promoted update packages. Frank has no write authority to Clay while acting as Frank.

## Intake sources
Read new items from:
- `usage/RESEARCH_EXPORT_QUEUE.jsonl`
- `research/ANSWER_EXPORT_QUEUE.jsonl`

Use local Clay-side ingestion cursors/receipts so the same item is not counted repeatedly.

## Required handling
For every new package:
1. verify source repository/path and package identity;
2. preserve original evidence class and privacy class;
3. deduplicate by event/question/package id;
4. map to relevant ClayGraph/FRANK/Harness hypotheses or experiments;
5. retain negative/no-value outcomes, false alarms and user corrections;
6. never treat a single-user report as universal evidence;
7. create a question for Andreas only if human input can materially discriminate an open hypothesis and the answer cannot be derived from existing data;
8. write any question only to this Clay-owned `QUESTION_OUTBOX.jsonl`;
9. after a ClayGraph generation is PROMOTED and consumer-compatible, write a migration/update package to `CLAYGRAPH_UPDATE_FEED.jsonl`.

## Research outputs
Useful observations should become appropriate RAE objects: micro-packets, experiment results, negative results, claims/hypotheses or run receipts with source refs back to the privacy-reviewed external package.

## Evaluation focus
Track longitudinal changes rather than cherry-picked anecdotes:
- recall/miss rate;
- false activation;
- important-mail alert precision;
- missed-important-mail incidents;
- cross-project dependency usefulness;
- graph growth and latency/context cost;
- correction/contradiction frequency;
- recovery success;
- goal-level usefulness;
- actual adoption and no-value/annoyance signals.

## Anti-Goodhart
Do not optimize solely for metrics Frank itself generates. Prefer externally observable outcomes such as Andreas correction/acceptance, later task completion, missed commitments, real mail outcomes, recovery parity and blinded/replayed evaluations when feasible.

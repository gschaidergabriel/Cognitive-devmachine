# Surgical Micro Packets

This directory is the smallest retrieval layer of the Research Entity.

A micro-packet should contain one independently meaningful proposition, mechanism, result, constraint, method, negative result, hypothesis or closely indivisible semantic unit plus provenance and status metadata.

Goals:

- surgically retrievable without opening a whole report;
- content/version/provenance aware;
- explicit CURRENT/OPEN/SUPERSEDED/REFUTED relationships;
- small enough to compose dynamically into task-specific Research Assemblies;
- never a replacement for raw evidence.

Canonical raw sources and append-only ledgers outrank these packets. Packets are compiled research knowledge and may be regenerated/reviewed.

Dump-derived packets must carry `origin_class=DUMP`, `dump_batch_id`, and normally `epistemic_class=DUMP_DERIVED_PREPROCESSED_HYPOTHESIS` until independent support justifies another classification.

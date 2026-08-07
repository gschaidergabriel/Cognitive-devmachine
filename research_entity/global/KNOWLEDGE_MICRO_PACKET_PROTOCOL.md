# Knowledge Micro-Packet Protocol

## Goal

Compile accumulated research into the smallest practical, independently retrievable text units without destroying provenance, contradiction, uncertainty or causal context.

Micro-packets are derived research memory, not raw evidence and not automatic canonical truth.

## Storage

`research_entity/knowledge_micro_packets/<domain>/<packet_id>.md`

Aggregate Topic Packets remain under `research_entity/topic_packets/` and link to their constituent micro-packets.

## One packet = one surgical research unit

A micro-packet should normally contain one atomic claim, one tightly bound mechanism, one negative result, one experiment result, one architectural constraint or one unresolved question. Split packets when two statements could reasonably have different evidence status, validity period, falsifier or domain relevance.

Target body size: roughly 80-220 words where possible. Prefer several precise packets over one narrative summary.

## Required metadata header

Every file begins with a machine-readable JSON object between markers:

`<!-- RAE_META` ... `RAE_META -->`

Required fields:
- packet_id
- title
- domains
- topics
- epistemic_class
- claim_status_hint
- origin_class
- origin_actor when known
- created_at / updated_at
- source_refs
- evidence_refs
- related_claim_ids
- related_experiment_ids
- predecessor_packet_ids / supersedes_packet_ids when applicable
- confidence
- verification_required
- falsifier_or_next_test
- search_terms

Recommended epistemic classes:
- COMPRESSED_SOURCE_SUMMARY
- MEASURED_RESULT_SUMMARY
- NEGATIVE_RESULT_SUMMARY
- OPEN_HYPOTHESIS
- DUMP_DERIVED_PREPROCESSED_HYPOTHESIS
- WEB_RESEARCH_SYNTHESIS
- ARCHITECTURE_DECISION_SUMMARY
- METHOD_MEMORY

## Body template

### Core
One compact statement of what the packet says.

### Evidence / boundary
What supports it and what the support does not establish.

### Implication
Why it matters elsewhere in the project.

### Next test
The cheapest or strongest discriminating test.

## Retrieval semantics

Micro-packet search must combine lexical terms, domain/topic links, claim status, experiment links and source provenance. Similarity alone must never determine truth or promotion.

## Materialization

`tools/materialize_micro_packets.py` creates a rebuildable searchable projection under `research_sources/derived/knowledge_micro_packets/`. This projection may be deleted and rebuilt; the individual packet files remain the derived human/git-readable memory.

## Update rules

- Never silently rewrite history to make an older packet appear always correct.
- When evidence changes, create/update status links and use successor packets where the semantic content materially changes.
- REFUTED and SUPERSEDED packets remain searchable.
- Raw source evidence remains separately archived.
- Model-authored compression retains actor/model provenance.

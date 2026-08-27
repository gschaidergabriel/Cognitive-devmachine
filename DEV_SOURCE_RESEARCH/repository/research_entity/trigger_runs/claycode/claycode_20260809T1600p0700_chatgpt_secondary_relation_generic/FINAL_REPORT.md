# ClayCode Trigger Run — Typed RelationId / Dual-Surface Canonicalization

Run: `claycode_20260809T1600p0700_chatgpt_secondary_relation_generic`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` — IN_PROGRESS  
Run status: `RESEARCH_DELTA_COMMITTED_DEGRADED_COORDINATION`  
Promotion: `NO_LANGUAGE_OR_BASE_PROMOTION`

## Executive result

This run advances the current G9 parser problem without redesigning ClayCode semantics.

Prior evidence had already established that the admitted G9 V3 source and published `grammar.ebnf` are not surface-closed. Independent E2B replication reproduced the baseline grammar defect and showed that the first minimal relation-word repair still suffered a relation/identifier collision. A concurrent ClayCode worker then tested a finite **declared infix relation resolver** and showed that it can retain selected readable relation forms while rejecting unknown relation words.

This run tested the competing **strict generic binary canonical form**:

`relation("relation-id", lhs, rhs)`

with relation meaning admitted only through a separate typed `RelationId` resolver.

Observed locally:

- 10/10 sampled current G9 binary relation forms parsed and preserved relation identity;
- 20,000/20,000 deterministic generic-surface fuzz cases parsed and preserved relation identity;
- 20,000/20,000 relation-name mutations changed the semantic hash;
- 20,000/20,000 operand swaps changed the semantic hash;
- 10/10 adversarial/keyword/unusual quoted relation IDs round-tripped at the syntax layer;
- after adding typed semantic resolution, 10/10 known sampled RelationIds were admitted and **0/50,000 unknown RelationIds** were admitted.

The concurrent declared-infix candidate independently reports 8/8 sampled known forms and 0/50,000 unknown relation words admitted by its strict resolver.

### Main synthesis

The strongest current hypothesis is therefore **not** “generic call beats infix” or “infix beats generic call.” Both experiments converge on a deeper separation:

`surface recognition != semantic RelationId admission`

A promising BASE design is one typed canonical Relation IR / RelationId registry with:

1. a strict generic/canonical serialization form using an explicit quoted relation id;
2. optional declared custom/infix reader syntax that lowers to the same IR;
3. one semantic resolver/typechecker that rejects undeclared relation identities before semantic admission.

This is an OPEN synthesis candidate, not a language promotion. The remaining decision must be made by the real BASE parser on the complete admitted corpus, with roundtrip, diagnostics, migration cost and reader/compiler benchmarks.

## Why this is new information

Earlier work proved the grammar drift and relation-word collision. It did not show that a quoted generic relation form plus typed resolver could preserve the tested relation identities while failing closed on unknown semantic relation IDs.

The concurrent declared-relation worker created a genuine competing implementation candidate during this run. Federation reread changed the conclusion: rather than selecting one surface prematurely, this report preserves both and proposes a shared canonical IR experiment.

## Executable evidence

Primary receipt:

- `EXECUTABLE_RESEARCH_RECEIPT.json`

Candidate artifact:

- `RELATION_GENERIC_CANONICAL_CANDIDATE.clay`

Local runtime:

- Python 3.13.5
- Lark 1.3.1

No fresh E2B execution was possible on this ChatGPT surface. Existing E2B evidence for the parent grammar defect was consumed as prior evidence only.

## Concurrent counterevidence / competing candidate

Consumed before final synthesis:

- `research_entity/trigger_runs/claycode/claycode-20260809T155804p0700-chatgpt-declared-relations/EXECUTABLE_RESEARCH_RECEIPT.json`
- `research_entity/trigger_runs/claycode/claycode-20260809T155804p0700-chatgpt-declared-relations/HYPOTHESES.json`
- `research_entity/trigger_runs/claycode/claycode-20260809T155804p0700-chatgpt-declared-relations/NEGATIVE_RESULTS.json`

Key result: arbitrary identifier-as-infix cannot be allowed to mint relation semantics. Its naïve parser accepted 50,000/50,000 unknown relation words, while the declared typed resolver admitted 0/50,000. This is consistent with the current run's generic form only when the generic form also uses a typed semantic resolver; parser acceptance alone remains insufficient.

## External triangulation

Primary external technical evidence was used as design triangulation, not FRANK-specific proof:

- MLIR Language Reference: MLIR provides a generic operation syntax identified by a string literal and also permits registered dialect operations to define custom assembly formats. This is an independently developed example of canonical/generic representation coexisting with readable custom surfaces.
- Tree-sitter parser documentation: keyword/identifier token conflicts and lexical precedence are explicit grammar concerns. This supports keeping semantic relation admission out of accidental token classification.
- WIT/Component Model remains relevant to later typed FFI/interface lowering, but does not decide this parser-surface question.

## Cross-branch findings

### FRANK

No new FRANK semantic primitive is justified. Surface syntax must preserve existing distinctions such as sensor evidence, memory/familiarity, selection, and effect authority; relation spelling cannot mint authority.

### ClayGraph

The binary RelationId result **must not** flatten ClayGraph hyperrelations. Current ClayGraph explicitly stores hyperrelation identity plus typed role-bearing members and provenance/epoch state.

### Hyperposition

This is decisive counterconstraint against overgeneralization: Hyperposition requires n-ary/higher-order relation identity, role bindings, pairwise-reduction tests and intervention semantics. A binary parser convenience is not a universal relation model.

### UnifiedDB

The surface result changes no physical storage decision. Typed semantic identity, versioned work/state, receipts and transaction boundaries remain independent of syntax.

### GWT / Emergenz

Parser or relation-surface success is not evidence of causal use, outcome, re-entry or emergence. Existing intervention/control contracts remain unchanged.

### Harness

No APP, H1, H2 or H3 acceptance item passes from this run. The result belongs to BASE parser/canonicalization and fuzz-conformance work.

## Hypotheses

See `HYPOTHESIS_MATRIX.json`.

Main candidates:

- `H-CC-G9-RELATION-GENERIC-008` — generic quoted binary relation surface + typed resolver;
- `H-CC-G9-DUAL-SURFACE-009` — one canonical Relation IR with generic canonical and optional declared custom/infix surfaces;
- `H-CC-G9-RELATION-NARY-010` — preserve explicit higher-order relation classes rather than flattening them for parser convenience.

## Negative results

See `NEGATIVE_RESULTS.json`.

Preserved:

- lexer/parser acceptance alone cannot confer relation semantics;
- binary generic Relation cannot yet serve as universal relation representation for ClayGraph/Hyperposition.

## Goodman anti-echo

See `FRANK_CLAYCODE_GOODMAN_REVIEW.json`.

The parser-surface result is not treated as supported merely because it agrees with FRANK/Clay terminology. The current generic form was tested executably, the concurrent declared-infix alternative was preserved, external compiler/parser patterns were used only as triangulation, and higher-order graph requirements were retained as counterevidence.

## Worker federation / coordination

The newly strengthened ClayCode federation protocol was reread during this run.

A repo-native work event was committed:

- `research_entity/state/work/events/20260809T1600p0700_CC_RELATION_GENERIC_WORK_CREATE.json`

See `WORKER_FEDERATION_RECEIPTS.json`.

Limit: the materialized live projections `CURRENT_DYNAMIC_WORK.clay` and `CURRENT_SYSTEM_POSSIBILITY.clay` were not present in the repository export, so live UnifiedDB coordination state could not be verified. The run therefore records **degraded repo-native coordination**, not full federation PASS.

## Interconnect / tool limitations

- Official `research_interconnect_preflight.py` could not be run because this ChatGPT execution surface has GitHub connector access but no repository checkout.
- `INTERCONNECT_MANIFEST.json` is a manual fail-closed assembly over verified GitHub inputs; official preflight completion is not claimed.
- E2B is not exposed as an invokable tool in this session; no fresh E2B evidence is claimed.
- An attempted GitHub write of the standalone Python probe source was connector-blocked; the experiment itself executed locally and its receipt/results were persisted. No claim depends on the blocked source-file write.

## Knowledge compilation

New micro-packet:

- `research_entity/knowledge_micro_packets/claycode/KMP-CLAYCODE-G9-DUAL-RELATION-SURFACE-20260809.md`

## Release/workspace implication

- `CC-WP-01-SPEC-FREEZE`: remains OPEN.
- `CC-WP-02-PARSER-CANON`: remains OPEN.
- `CC-WP-11-FUZZ-CONFORMANCE`: remains OPEN.
- all application acceptance items remain unpassed.
- no CURRENT G9 semantic change is requested.
- no canonical revision is requested.

## Highest-information next experiment

Implement in the **real BASE parser** one shared typed `RelationId` resolver with two surfaces:

1. generic quoted canonical form;
2. finite declared infix/custom form.

Run both over the complete admitted G9 V3 + dialect corpus and measure:

- parse closure and ambiguity/conflict count;
- undeclared-symbol rejection under mutation/fuzz;
- parse -> typed IR -> print -> parse roundtrip;
- semantic-hash equality between equivalent surfaces;
- diagnostics quality;
- migration/edit count from current G9;
- parser complexity and repair cost;
- byte/token cost;
- Qwen-class reader accuracy/repair cost when target-model access exists.

Only that matched test should decide whether dual-surface, generic-only or declared-infix-only becomes the BASE surface policy.

## Final synthesis

ClayCode should not solve its current grammar drift by turning every English-like relation word into a lexer operator. The evidence now supports a sharper architecture: **semantic relation identity belongs in typed IR/resolution; surface syntax is a reversible projection problem.**

The generic quoted form is a viable strict canonical candidate; the concurrent declared-infix form is a viable readable candidate. Their agreement at the typed resolver suggests a dual-surface compiler architecture worth testing, while ClayGraph/Hyperposition prevent the simplification from erasing true higher-order relation semantics.

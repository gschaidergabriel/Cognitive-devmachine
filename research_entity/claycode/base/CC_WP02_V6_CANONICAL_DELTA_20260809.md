# CC-WP-02 — V6 strict-LALR repair + canonical IR delta

Date: 2026-08-09
Actor: `chatgpt-secondary`
Canonical parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
Goal: Frank v0.1 fully operational on Andreas' Ubuntu developer system.

## Result

A concrete frontend blocker was localized in the active V5 grammar rather than treated as an abstract parser issue.

`D_LALR_GRAMMAR_REPAIR_CANDIDATE_V5.lark` contains:

`dotted_relation: qid DOT_REL [primary]`

On the available Lark 1.3.1 sandbox this produces six LALR shift/reduce diagnostics at the boundary between a completed dotted relation and a following token that can continue the surrounding expression (`IFF`, `IN`, `OR`, `SUBSET_OF`, `REQUIRES`, `LBRACE`). With `strict=True`, construction stops on that conflict before lexical strictness is reached.

The smallest repair consistent with the admitted G9 examples is:

`dotted_relation: qid DOT_REL primary`

This is now committed as `research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V6.lark`.

In the same sandbox, V6 produced zero non-strict LALR conflict diagnostics. A full strict lexical construction could not be completed in this hosted sandbox because `interegular` is not installed/obtainable here. That is an environment limitation, not evidence of strict lexical PASS.

## Canonical IR implementation

Committed `tools/claycode_canonical_ir.py` provides a deterministic parser-level canonical IR and hash layer for WP-02. It:

- uses strict LALR/contextual parsing and `keep_all_tokens=True`;
- preserves operator/literal/identifier distinctions;
- removes presentation-only newline and structural-separator tokens from the semantic hash;
- preserves exact source bytes separately through `source_sha256` and line-ending metadata;
- emits deterministic JSON with sorted keys;
- verifies JSON serialize/deserialize semantic-hash roundtrip;
- contains equivalence tests for spacing/comments, blank lines, newline-vs-semicolon separators and LF-vs-CRLF;
- contains discrimination tests for relational/arithmetic operators, booleans, call-argument order, dotted-relation kind and Unicode string mutation.

The same logic was executed in the hosted sandbox with strict lexical checking disabled only because `interegular` is unavailable. All roundtrip/equivalence/discrimination self-tests passed under that constrained mode.

## Frontend validator repair

`tools/claycode_base_frontend_validation.py` now targets V6 by default and adds a negative case requiring dotted relations to have an object. It still deliberately refuses to claim CC-WP-02 PASS by itself.

## Evidence classification

- V5 shift/reduce conflict localization: `SANDBOX_RUNTIME_EVIDENCE`
- V6 zero non-strict conflict diagnostics: `SANDBOX_RUNTIME_EVIDENCE`
- canonical IR self-tests: `SANDBOX_RUNTIME_EVIDENCE`
- V6 grammar / canonicalizer / validator changes: `REPO_IMPLEMENTATION_DELTA`
- Ubuntu strict/full-corpus acceptance: `OPEN`

No production/Ubuntu PASS is claimed from hosted sandbox evidence.

## Required next discriminating execution

On the current Ubuntu developer-system checkout with the strict Lark dependency set installed:

1. run `python tools/claycode_strict_lalr_probe.py --grammar research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V6.lark`;
2. run `python tools/claycode_base_frontend_validation.py --output <append-only receipt>`;
3. run `python tools/claycode_canonical_ir.py --self-test --source research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay --source research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay --output <append-only receipt>`;
4. compare repeated semantic hashes and run a source mutation discriminator;
5. only if strict construction, full-corpus acceptance, canonical roundtrip and discrimination all pass may the parser/canonical subgate be credited; typed canonical IR integration remains required before full CC-WP-02 PASS.

## Cross-room implication

Affected rooms: `claycode`, `frank`, `harness`, `clayresearch`.

This reduces the active Frank v0.1 critical path by turning a latent V5 grammar ambiguity into a concrete V6 repair plus executable canonicalization tool. It does not unblock H1 yet because the BASE ClayCode release gate remains NOT_PASS until production/Ubuntu receipts close the remaining BASE packages.

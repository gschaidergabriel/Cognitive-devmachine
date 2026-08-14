# CC-WP-02 — Lark strict-mode lookahead counterevidence

Date: 2026-08-10 +07
Actor: `chatgpt-secondary` (temporary Clay Research Entity worker)
Class: `PRIMARY_SOURCE_COUNTEREVIDENCE / NO_SEMANTIC_CHANGE`
Goal: `Frank v0.1 voll lauffähig auf Andreas PC`

## Current observation

The active V17 grammar uses a regex lookahead in `DOTTED_PREFIX_REL`:

`/Needle\.(?:lowers|owns)(?=[ \t]+[^ \t\n;\/\(])/`

The current frontend path constructs Lark with `parser="lalr"`, `lexer="contextual"`, and `strict=True` and additionally carries direct positive/negative/discrimination cases for the dotted Needle relations.

## Fresh primary-source evidence

Lark's current official documentation states that strict mode detects unresolved shift/reduce conflicts and regex collisions, but also warns that advanced regular-expression features such as lookahead/lookbehind may prevent `interegular` from detecting existing collisions.

Primary sources retrieved 2026-08-10:
- https://lark-parser.readthedocs.io/en/latest/how_to_use.html
- https://lark-parser.readthedocs.io/en/stable/classes.html

GitHub Actions runner interpretation used in the same GO cycle is grounded separately in:
- https://docs.github.com/en/actions/reference/runners/self-hosted-runners

## Hypothesis / counterhypothesis

H1: V17 strict construction plus full-corpus acceptance is sufficient to establish the selected frontend has no materially relevant lexical ambiguity.

Strongest counterhypothesis: because the selected V17 differentiator itself uses lookahead, strict/interegular success cannot exhaustively establish absence of regex collisions; a latent ambiguity could survive strict construction and only appear on a direct boundary fixture.

## Decision

`NO_GRAMMAR_CHANGE`.

Strict construction remains required evidence, but its interpretation is narrowed:

`STRICT_PASS != EXHAUSTIVE_REGEX_COLLISION_PROOF_WHEN_ADVANCED_LOOKAROUND_IS_PRESENT`.

Therefore the existing direct `Needle.owns` / `Needle.lowers` positive, negative, spacing/trivia, call-vs-prefix, and mutation discriminators remain mandatory and must travel with any WP-02 acceptance receipt. Full-current-corpus and grammar-bound canonical hash receipts remain independently required.

This counterevidence does not refute V17, does not prove a collision exists, and does not justify new syntax. It prevents overpromotion of one validation mechanism.

## Architecture / test re-entry

Architecture delta: `NO_CHANGE`.

Test obligation refinement:
- preserve strict LALR construction;
- preserve direct V17 lookahead-bound relation discriminators;
- preserve full-corpus current G9 + Dialect validation;
- preserve deterministic canonicalization + mutation discrimination;
- keep Ubuntu target evidence separate from local/proxy evidence.

Rollback: none required; no runtime or grammar mutation made.

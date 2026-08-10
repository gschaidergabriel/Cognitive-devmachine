# ClayCode BASE WP-03 — active frontend / typed-IR grammar split counterexample

Run context: 2026-08-10T12:36+07:00 · actor `chatgpt-secondary` · trigger `go`.

## Finding

The current production-facing declarative frontend `tools/claycode_base_frontend.py` defaults to:

`D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark`

The current typed canonical IR builder `tools/claycode_base_typed_ir.py` defaults to:

`D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark`

This is not merely a path/version mismatch. A local differential parser execution shows semantic divergence on inputs inside the active language surface.

### Counterexample A — Needle call/relation identity

Source:

`rule Needle.owns(X)`

V17 result: accepted as a `call` with qid `Needle.owns`.

V7 result: accepted as `dotted_relation` (`Needle` + `.owns`) whose optional primary is the parenthesized `X`.

The spaced form `Needle.owns (X)` follows the same respective interpretation in each grammar.

Therefore WP-02 and WP-03 can assign different AST semantics to the same source even when both accept it.

### Counterexample B — identifier surface

Source:

`record X { foo-bar:Int }`

V17: ACCEPT. Current NAME permits hyphen after the first character.

V7: REJECT at `-`; its NAME permits only `[A-Za-z0-9_]` after the first character.

Therefore the current typed-IR default path does not accept the whole active V17 surface.

## Why this matters

The BASE critical path requires a coherent source -> parser -> deterministic canonicalizer -> typed canonical IR chain. A validated WP-02 grammar cannot provide acceptance evidence for WP-03 if WP-03 silently reparses through a semantically different older grammar.

Multiple frontend dialects may remain valid architecture, but only if their grammar identities are explicit and a translation/equivalence contract binds them to the same typed semantic boundary. Silent fallback from V17 to V7 is not such a contract.

## Hypothesis / strongest counterhypothesis

H: `claycode_base_typed_ir.py` carries stale parser ownership and must consume a frontend result produced by the admitted grammar instead of independently selecting V7.

Counterhypothesis: V7 is intentionally the generic structured backend because V17 deliberately omits procedural `fn` syntax; both are required dialect surfaces.

Adjudication: even if the counterhypothesis is true, the current implementation still needs an explicit dialect/frontend identity handshake. The same source must not be silently reinterpreted under a different grammar, and any V7-only procedural path must be separately identified, validated and lowered into the same typed semantic IR with differential receipts.

## Smallest safe repair direction

1. Make typed-IR compilation consume an already-produced frontend artifact/AST plus its `frontend_schema`, `surface`, `grammar_sha256`, and semantic/contract hash instead of silently choosing its own default grammar.
2. If a structured V7/Vx frontend remains necessary, name it as a separate admitted surface and require explicit dispatch.
3. Add cross-frontend collision tests for source strings accepted by more than one surface; equal-source ambiguity must fail closed unless semantics are proven equal.
4. Add regression cases for `Needle.owns(X)`, `Needle.owns (X)`, dotted prefix relations, hyphenated identifiers, operator identity, and all current G9/Dialect sources.
5. Run the resulting Source->Frontend->TypedIR chain on the verified Ubuntu lane with exact grammar/frontend/IR hashes.
6. Do not mark CC-WP-03 PASS until the frontend identity is receipt-bound and no silent reparsing path remains.

## Local execution metadata

- Python 3.13.5
- Lark 1.3.1
- strict=False for proxy differential because local `interegular` is unavailable
- environment: local analysis container, not Hostinger Ubuntu acceptance
- tested minimal counterexamples only, not full corpus

Status: `SUPPORTED_INTEGRATION_COUNTEREXAMPLE / WP03_BLOCKER / UBUNTU_REPLICATION_REQUIRED`.

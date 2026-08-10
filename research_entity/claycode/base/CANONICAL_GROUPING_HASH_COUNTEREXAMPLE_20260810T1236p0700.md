# ClayCode BASE WP-02 — Canonical grouping semantic-hash counterexample

Run context: 2026-08-10T12:36+07:00 · actor `chatgpt-secondary` · trigger `go` · subject ClayCode BASE WP-02.

## Result

A bounded metamorphic test against the current `tools/claycode_base_frontend.py` algorithm and BASE-D V17 grammar found a concrete canonicalization counterexample.

Expected semantic-equivalent pair:

- `rule x>0`
- `rule (x>0)`

Current `semantic_hash` behavior differs because the canonical AST preserves grouping-only `LPAR`/`RPAR` tokens inside the grammar-generated `primary` node. Nested redundant grouping produces the same failure family.

Controls:

- ignored whitespace/comment variant preserved the hash;
- equivalent JSON string spelling `"a"` vs `"\u0061"` preserved the hash;
- `>` vs `<` correctly changed the hash;
- `Needle.owns X` vs `Needle.lowers X` correctly changed the hash.

`1` vs `1.0` also changed the hash, but this is NOT promoted as a defect because typed IR may legitimately distinguish numeric forms/types. Numeric normalization is deferred until frozen typed semantics proves equivalence.

## Local execution metadata

- Python: 3.13.5
- Lark: 1.3.1
- interegular: unavailable in the local analysis container
- strict collision evidence: NOT EXECUTED locally because interegular is absent
- environment class: local proxy analysis container, NOT Hostinger Ubuntu acceptance
- full G9/Dialect corpus: NOT EXECUTED locally

Therefore this is a high-information counterexample/regression seed, not a CC-WP-02 PASS/FAIL receipt for Ubuntu.

## Hypothesis / counterhypothesis

H: grouping punctuation is surface syntax only and must not alter the frontend semantic identity used by deterministic semantic-hash receipts.

Strong counterhypothesis: the current frontend hash is intended as a structural parse hash rather than semantic identity, and grouping normalization belongs only in typed IR.

Adjudication: current production code names the value `semantic_hash`; the BASE acceptance contract requires deterministic semantic hashes/receipts; the semantic freeze requires canonical roundtrip/hash evidence with mutation discrimination. G9 uses semantic hashes for compatibility while grouping parentheses have no independent semantic law. The smallest safe repair candidate is therefore to collapse only grammar-generated grouping-only `primary(LPAR, expr, RPAR)` nodes during canonicalization, while leaving numeric normalization to typed IR.

## Minimal repair candidate

In `canonical_node`, before generic Tree recursion, recognize exactly a three-child `primary` node whose outer children are `LPAR` and `RPAR`, and return the canonicalized middle child. Do not normalize calls, lists, sets, operators, relations, numbers or type-bearing forms.

Required regression assertions:

1. `rule x>0` == `rule (x>0)` semantic hash.
2. `rule x>0` == `rule ((x>0))` semantic hash.
3. whitespace/comment and equivalent string escapes remain equal.
4. operator and dotted-relation mutations remain unequal.
5. rerun strict V17 full-current-G9 + Dialect validation on the verified Ubuntu lane.
6. version/bind any changed canonical-hash contract so old and new hash semantics cannot be silently conflated.

## Concurrency / authority decision

No direct edit was made to the active parser/canonicalizer path in this run because the current BASE blocker burn-down explicitly warns against race-editing the parser repair worker while strict/full-corpus receipts are pending. This artifact is intended as a targeted WP-02 falsifier and regression obligation for the active build organ.

Status: `SUPPORTED_COUNTEREXAMPLE / REPAIR_CANDIDATE / UBUNTU_REPLICATION_REQUIRED`.

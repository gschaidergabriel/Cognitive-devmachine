# GO 2026-08-10 06:45 +07 — WP02 strict dependency / lookaround receipt

Run id: `go-20260810T0645p0700-wp02-strict-lookaround`
Actor: `chatgpt-secondary`
Provider/model: OpenAI / GPT-5.6 Sol
Canonical parent: RAE-8.8 revision 2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
Program stage: `BASE_CLAYCODE_RELEASE`
Critical package: `CC-WP-02-PARSER-CANON`
Truth scope: local proxy execution + current GitHub file/effect receipts; NOT Ubuntu BASE acceptance.

## Hypothesis

The current strict-LALR diagnostic path can misclassify a missing `interegular` runtime dependency as a grammar conflict, and V17's regex lookahead means `strict=True` alone is not complete evidence for lexical collision freedom.

## Strongest counterhypothesis

The existing strict parser construction plus current regression cases are already sufficient; dependency state and lookaround-specific metamorphic guards add no material information and should not alter the BASE frontend gate.

## Fresh internal evidence

- Active frontend validator points to `research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark`.
- V17 uses `DOTTED_PREFIX_REL` with a regex positive lookahead to separate `Needle.owns/lowers <rhs>` from call syntax.
- Prior `tools/claycode_strict_lalr_probe.py` defaulted to historical V3 and treated any strict-build failure as a reason to repair grammar, without separating missing strict-mode dependencies.
- `CLAYCODE_RELEASE_WORKSPACE.json` still has CC-WP-02 OPEN and requires strict/full-corpus/canonical receipts before promotion.

## Fresh external primary evidence

Official Lark documentation retrieved 2026-08-10 +07:

1. `https://lark-parser.readthedocs.io/en/latest/how_to_use.html`
   - Lark strict mode raises on LALR shift/reduce and regex collisions.
   - Strict regex-collision checking requires `interegular`.
   - Advanced regex features such as lookahead/lookbehind may prevent `interegular` from detecting existing collisions.

2. `https://lark-parser.readthedocs.io/en/stable/classes.html`
   - `strict` is explicitly a parser-construction ambiguity/collision gate, not a typed-semantic proof.

3. `https://lark-parser.readthedocs.io/en/stable/examples/advanced/conf_lalr.html`
   - The contextual lexer uses parser state to narrow legal terminals; this is powerful but makes boundary behavior worth direct metamorphic testing.

## Local execution receipt

Environment:

- host class: isolated ChatGPT container, not target VPS
- OS: Debian GNU/Linux 13 (trixie)
- kernel: Linux 6.18.35 x86_64
- Python: 3.13.5
- logical CPUs: 5
- physical CPUs reported: 5
- RAM total: 6,368,813,056 bytes
- Lark: 1.3.1
- interegular: NOT INSTALLED

Observed current behavior before tool repair:

- non-strict V17 parser construction: PASS
- strict V17 parser construction: BLOCKED with `LexError: interegular must be installed for strict mode`
- therefore the old generic interpretation would have incorrectly pointed toward grammar repair for an environment/dependency failure.

Patched diagnostic behavior:

- `strict_evidence_state = BLOCKED_MISSING_INTEREGULAR`
- `nonstrict_build_ok = true`
- `strict_build_ok = false`
- `regex_lookaround_present = true`
- interpretation explicitly says: pin/install interegular and re-run; do NOT infer grammar repair from this result.

Code effect receipts:

- commit `f79f3983963804163715c4866a2e8d4f2f82159a`
  - updates `tools/claycode_strict_lalr_probe.py`
  - default now points to V17
  - records Lark/interegular versions
  - separates dependency block vs grammar conflict vs lexer/other failure
  - adds lookaround scope guard

- commit `4d5349883dd302301cb702ff8e1b9177826f0399`
  - updates `tools/claycode_base_frontend_validation.py`
  - records dependency versions on successful strict run
  - adds tab/mixed-horizontal-trivia positive, negative and equivalence guards around `Needle.owns`/`Needle.lowers`
  - marks lookaround as requiring explicit metamorphic boundary evidence in addition to strict construction

## Exactly one out-of-the-box experiment

Experiment: adversarial metamorphic whitespace/punctuation sweep at the V17 dotted relation/call boundary.

Purpose: test the semantic boundary directly rather than trusting strict collision analysis on a lookahead regex.

Local reconstructed-grammar proxy:

- known negative regression cases: 7/7 behaved as expected
- known positive regression cases: 12/12 behaved as expected
- generated metamorphic relation-boundary cases: 22
- violations: 0
- tested space, repeated space, tab, call syntax, prefix-relation rhs and list rhs around `Needle.owns` / `Needle.lowers`

Result: `NO_COUNTEREXAMPLE_FOUND_IN_22_CASE_PROXY_SWEEP`.

This is a useful negative result, not promotion evidence. The local grammar reconstruction omitted source comments and was not a full repository checkout; target Ubuntu and exact full-corpus execution are still required.

## Decision / architecture-test delta

SUPPORTED:

- No ClayCode semantic change is justified.
- WP02 strict evidence must distinguish grammar failure from missing `interegular`.
- V17 lookaround means strict construction remains necessary but not sufficient for lexical-boundary confidence.
- Metamorphic relation/call boundary guards belong in the frontend validation gate.
- Dependency/runtime versions are interpretation-changing benchmark metadata and must be preserved in receipts.

REFUTED:

- "Any strict-build failure means repair the grammar." This is false when strict evidence is blocked by a missing runtime dependency.

NOT YET PROVEN:

- exact V17 strict construction on the Hostinger Ubuntu runner
- full G9 V3 + Dialect V3 validation on the target runner after dependency pin
- canonical AST/IR deterministic serialization/hash roundtrip
- CC-WP-02 PASS

## Next falsifier / critical path

1. On the verified Hostinger Ubuntu self-hosted runner, pin/install exact Lark + interegular versions and capture machine/build metadata.
2. Run updated `tools/claycode_strict_lalr_probe.py` against exact repository V17.
3. Run updated `tools/claycode_base_frontend_validation.py` against exact current G9 V3 + Dialect V3.
4. Preserve raw JSON receipts, versions, hashes, diagnostics and runner metadata.
5. If those pass, proceed to deterministic canonical AST/IR serialization + semantic-hash roundtrip; do not promote CC-WP-02 before that receipt exists.

## Recovery / rollback

Both code changes are diagnostic/test-only and independently revertible by their Git commits. No runtime authority, Frank Harness authority, language semantics or effect gateway was changed.

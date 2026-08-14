# ClayCode surface reaches 90 % of the corpus — and a silently ignored negation

Date: 2026-08-11 16:15 +07:00
Origin actor: `claude-code` / Anthropic / Claude Opus 5 (1M), coordinating a delegated Sonnet worker
Identity: `EXTERNAL_CONTRIBUTOR_NOT_A_BOOTED_CLAY_ORGAN`
Work package: `F-V01-02-CLAYCODE-COMPILER-RUNTIME`
Status: `INDEPENDENTLY_RE-VERIFIED / PULL_REQUEST_OPEN / NO_PROMOTION_REQUESTED`
Pull request: `gschaidergabriel/Dr.-Unterweger` #314, stacked on #310

## 1. Coverage

Measured with `corpus_probe.py`, re-run by the coordinating session rather than accepted on report:

| | sources | coverage |
|---|---|---|
| before | 3 / 40 | **7.5 %** |
| after | 36 / 40 | **90.0 %** |

Six increments, each gated on three conditions simultaneously: the grammar builds without LALR
conflicts, the three baseline sources parse to identical structure counts, and the
`decide_effect` differential gate stays PASS with 0 mismatches. Re-verified: 6/6, 0 mismatches.

The remaining four are **deliberately rejected**, not overlooked:
- two need a multi-statement lambda body that collides with `set_literal` at the LALR level;
- two carry free-form prose notation (unicode arrows, slashes inside identifiers, bare-word
  values, checklist-style `require before X { … }`) whose formalization would mean inventing
  grammar not evidenced elsewhere in the corpus.

An honest 90 % beats an invented 100 %. The grammar's own law — new syntax needs a new version,
unknown constructs fail closed — was held.

## 2. The finding that matters more than the coverage

**The evaluator delivered in report `20260811T1405p0700` silently ignored `!` negation.**

Root cause: `?unary_expr: "!" unary_expr | primary`. With `keep_all_tokens=False` the anonymous
`"!"` token is filtered out, leaving a single child, so Lark's `?` **inlines the rule** and the
`Not` node is never constructed. No error, no diagnostic — the negation simply disappears.

Reproduced by the coordinating session on a minimal source:

```clay
fn f(a : Bool) -> Bool { if !a { return true }  return false }
```

| branch | `f(true)` | `f(false)` | verdict |
|---|---|---|---|
| evaluator as first delivered | `True` | `False` | **inverted** |
| after fix | `False` | `True` | correct |

A second defect: `BOOLEAN` had no word boundary, so identifiers such as `false_alarm_rate` were
mis-lexed as the literal `false` plus a fragment.

## 3. Why the 200,576-request differential gate did not catch it

`claycode/frank_effects.clay` never uses `!` — it writes `== false` throughout. The gate compared
`decide_effect` against the Python reference across the whole request space and found zero
mismatches, and that result stands. But the negation path was **never exercised**, because the
one source under differential test happens not to use it.

**That is luck, not design.** Any `.clay` source using `!` would have been evaluated with inverted
boolean semantics and no diagnostic whatsoever. In an effect-authority context that is precisely
the class of defect that turns a DENY into an ALLOW.

The methodological lesson generalizes beyond this bug: **a differential gate certifies the paths
its corpus exercises, not the language.** Coverage of the *sample* was measured (200,576 requests)
while coverage of the *language surface* was not. A gate should report which constructs it
exercised, so an unexercised construct is visible as a gap rather than invisible as a pass.

## 4. Disposition

- The 90 % surface and both fixes are in PR #314, stacked on #310.
- #310 should not be merged without #314, or the negation defect ships.
- Recommended follow-up: extend the differential gate to report **construct coverage** alongside
  request coverage, and add a minimal `.clay` conformance suite exercising every grammar
  construct at least once — the language equivalent of the lesion sites in the loop-core slice.

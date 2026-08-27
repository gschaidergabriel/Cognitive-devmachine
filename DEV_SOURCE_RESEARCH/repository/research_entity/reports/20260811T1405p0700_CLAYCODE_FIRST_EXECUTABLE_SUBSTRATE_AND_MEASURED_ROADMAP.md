# ClayCode — first executable substrate, and a measured roadmap for F-V01-02

Date: 2026-08-11 14:05 +07:00
Origin actor: `claude-code` / Anthropic / Claude Opus 5 (1M) — external contributor session
Identity: `EXTERNAL_CONTRIBUTOR_NOT_A_BOOTED_CLAY_ORGAN`
Target: `self.root` / Frank v0.1 on the accepted Hostinger Ubuntu VPS
Work package: `F-V01-02-CLAYCODE-COMPILER-RUNTIME`
Status: `EXECUTED_ON_TARGET_VPS / PULL_REQUEST_OPEN / NO_PROMOTION_REQUESTED`
Pull request: `gschaidergabriel/Dr.-Unterweger` #310
Predecessor: report `20260811T1339p0700_CLAUDE_EXTERNAL_AUDIT_TARGET_VPS_RECEIPT_INTEGRITY.md`, finding A2

## 1. The gap, stated exactly

`CLAYCODE_ONLY` cognition means the cognitive loop core has no executable substrate until ClayCode
runs. A repo-wide search of `gschaidergabriel/Dr.-Unterweger` at `main` found **no evaluator, no
interpreter, no lowering stage and no code generator** for `.clay`. `structured_frontend_v1.py`
(112 lines, Lark) terminates at a TypedIR dictionary.

The practical consequence was narrower and sharper than "the compiler is unfinished". Every claim
about ClayCode semantics rested on a Python re-implementation that was never compared against the
semantic source. The flagship effect-authority probe binds to `claycode/frank_effects.clay` by

```python
missing = [x for x in required_markers if x not in semantic]
```

— thirteen substrings. **Inverted `.clay` semantics would still emit PASS**, while the receipt
carried `evidence_class: DIRECT_FRANK_V0_1_EFFECT_AUTHORITY_EXECUTABLE_POLICY_ORACLE`.

## 2. What now exists

`runtime/claycode_eval_v1/` — a bounded but real front-to-execution path over the existing
`FRANK_STRUCTURED_V1` grammar, which remains the single syntactic source of truth.

- `syntax.py` — grammar → typed AST. Deliberately self-contained: it does **not** import the WP03
  base frontend, because `runtime/clay_wp03_exact_bundle/tools/claycode_base_frontend.py` is
  **absent from the Frank repo at `main`** (it exists only in this Clay repo under `tools/`). Two
  commits named `bundle(wp03): restore exact V18 frontend` indicate this has been lost before. A
  workflow still asserts that file's git hash. Filed separately as `N-CLAYCODE-003`.
- `analyzer.py` — nominal universe; call-target partition; arity checks; call-graph reachability.
- `host.py` — explicit host contracts. A name is an intrinsic **only** because it is declared
  there, each with its effect class. Undeclared stays `UNRESOLVED`.
- `evaluator.py` — tree-walking evaluator. Fails closed on unresolved targets, unbound relations,
  unknown fields and missing variants. `require` raises a typed `RequireViolation`, so a policy
  refusal is distinguishable from an evaluator fault. Purity is enforced rather than assumed.
  Authority-minting intrinsics are refused unless the caller explicitly enables them.
- `corpus_probe.py` — measured surface coverage over the whole corpus.

## 3. WP04 — the 29, reproduced independently, and re-partitioned

The analyzer counts **exactly 29** unresolved call targets in `frank_effects.clay`. This matches
the supervisor count from a completely independent implementation, which is worth recording as
cross-validation of both.

The more useful result is that the 29 are **not one kind of work**:

| group | count | what closes it |
|---|---|---|
| deterministic semantic projections (`semantic_hash`, `policy_relevant_effect_projection`, `optional_semantic_hash`, `verb_for`) | 4 | pure host contract |
| state reads (`*_current`, `*_matches`, `node_can_use`, `final_security_gate`, …) | 16 | READ_ONLY host contract + UnifiedDB binding |
| clock (`now`) | 1 | injected for replayability |
| authority-minting (`trusted_runtime_effect_authorization`, `trusted_runtime_derive`, `atomic_effect_reservation_…`) | 3 | trusted runtime only; never a test double |
| external effect (`runtime_effect`, `independently_observe_effect`) | 2 | real provider path |
| **undeclared types** (`EffectReceipt`, `VerifiedEffectReceipt`, `DoneReceipt`) | **3** | **a ClayCode declaration — no host binding can resolve these** |

The last row is the actionable surprise. Those three are used as return types and constructed
positionally in `frank_effects.clay`, but declared in **no** `.clay` source anywhere in
`claycode/`. Pooling them with the intrinsics hid work that belongs to a different owner.

**`decide_effect` reaches zero unresolved targets.** It calls only `destructive_guard_complete`,
which calls nothing. The single most quoted policy in the program was therefore executable all
along — it only lacked an evaluator.

## 4. Differential result on the accepted target VPS

`tests/claycode_decide_effect_differential_gate.py` executes the ClayCode source and compares
`decide_effect` against `EffectGate.evaluate` **imported from the shipping probe**, not copied, so
the comparison cannot drift against a private fork.

Executed on `clay@digital-retina`, Python 3.12.3, lark 1.3.1, in a disposable copy. Runner working
tree untouched, no canonical database, no external effect.

```
200,576 requests compared  ->  0 mismatches,  6/6 checks,  exit 0
```

Sweep = every (9 effect classes × 8 destructive kinds × 4 actors × all-false/all-true) plus
200,000 seeded random draws over 19 boolean policy fields.

### Discriminating power, demonstrated rather than asserted

Per `messgeraet-vor-glauben` discipline, a green gate is worthless until it is shown to be able to
go red. The `.clay` source was sabotaged:

| sabotage | result |
|---|---|
| `DENY` → `ALLOW` for `WIPE_DEVICE`/`FORMAT_FILESYSTEM` | FAIL, 7 mismatches |
| one conjunct dropped in `destructive_guard_complete` | FAIL, **1** mismatch in 3,576 |

The second matters more: a single missing guard is caught.

Two further checks assert the discipline itself — admitting `execute` is refused because its call
graph is unresolved, and admitting `confirmation_matches` is refused in a pure context even when
every intrinsic is bound, because `READ_ONLY != PURE`.

## 5. Measured roadmap — the number the program did not have

`corpus_probe.py` over all 40 `.clay` sources: **3 parse. 7.5 %.**

The other 37 are reported with the construct that rejects them, grouped by frequency:

| sources | missing construct |
|---|---|
| 8 | multi-line forms |
| 8 | `=` (field defaults / const assignment) |
| 5 | `state` declarations |
| 4 | `#` character |
| 2 | `in` |
| 2 | `database` declarations |
| 2 | `const` declarations |
| 1 each | `receipt`, `entity`, `view`, `-`, `&&` in an unsupported position |

**13 distinct constructs separate 7.5 % from full corpus coverage.** That is a tractable list, and
it is measured rather than estimated. No construct's meaning was guessed: an unparsed source is
reported as unparsed, honouring the grammar's own law that new syntax requires a new version and
unknown constructs fail closed.

This also re-scopes the `TARGET_VPS_PASS` for the structured frontend honestly: it is a real pass
over **7.5 %** of the corpus, not over ClayCode.

## 6. Recommended next steps, in dependency order

1. **Declare the three missing types** in ClayCode. Cheapest item on the whole work package and it
   unblocks `execute`, `verify_effect` and `finish`.
2. **Bind the 4 pure intrinsics**, then run the differential gate over `effect_request_hash` and
   `confirmation_matches`. That extends executed coverage without touching authority.
3. **Extend the surface by the 13 constructs**, highest frequency first. Each extension should
   arrive with a corpus-coverage delta, so progress on `F-V01-02` becomes a measured percentage
   instead of a judgement.
4. **Let `target_vps_probe.py` call the evaluator** instead of the substring check, so its
   `evidence_class` can honestly say `EXECUTABLE`. This closes audit finding A2 at the source.
5. **Restore or vendor `claycode_base_frontend.py`** into the Frank repo, or delete the workflow
   step that asserts its hash. Right now the repo asserts a file it does not contain.

## 7. Scope limits

- Only `decide_effect` and `destructive_guard_complete` are executed. Nothing is claimed about the
  other 13 functions in the module, which still require host contracts.
- The evaluator is a tree-walking interpreter, not a compiler. It is sufficient for differential
  semantic evidence and for running policy; it is not a performance substrate.
- Adds one dependency, `lark==1.3.1`, pinned because the evaluator depends on that release's
  LALR/contextual-lexer behaviour.
- No external effect, no authority minted, no canonical database touched.
  `whole_frank_v0_1_acceptance: NOT_CLAIMED`.
- Delivered as an open pull request. Disposition belongs to Clay and the project owner.

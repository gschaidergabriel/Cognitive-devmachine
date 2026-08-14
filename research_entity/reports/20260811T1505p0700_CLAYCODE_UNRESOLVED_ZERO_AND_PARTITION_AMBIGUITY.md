# ClayCode — frank_effects reaches UNRESOLVED = 0, and the 29-vs-3 ambiguity resolved

Date: 2026-08-11 15:05 +07:00
Origin actor: `claude-code` / Anthropic / Claude Opus 5 (1M), coordinating a delegated Sonnet worker
Identity: `EXTERNAL_CONTRIBUTOR_NOT_A_BOOTED_CLAY_ORGAN`
Work package: `F-V01-02-CLAYCODE-COMPILER-RUNTIME`
Status: `EXECUTED / INDEPENDENTLY_RE-VERIFIED / PULL_REQUEST_OPEN / NO_PROMOTION_REQUESTED`
Pull request: `gschaidergabriel/Dr.-Unterweger` #313, stacked on #310
Predecessor: report `20260811T1405p0700_CLAYCODE_FIRST_EXECUTABLE_SUBSTRATE_AND_MEASURED_ROADMAP.md`

## 1. A measurement ambiguity that must be recorded before anything else

Two different unresolved counts for the same file are now in circulation, and both are correct.
Left unstated they read as contradictory evidence, which is exactly the failure mode this
programme guards against.

| state of the analysis | CLAY_FN | CONSTRUCTOR | INTRINSIC | UNRESOLVED |
|---|---|---|---|---|
| before `host.py` — the raw WP04 gap | 5 | 2 | 0 | **29** |
| after `host.py` declares 26 contracts | 5 | 2 | 26 | **3** |
| after this work | 5 | **5** | 26 | **0** |

**29** is the count with no owner-reviewed host contract declared at all. It is the number that
matches the supervisor's, and it is the honest size of the original WP04 gap.

**3** is what survives after `host.py` declares 26 intrinsics. Declaring a contract does not
implement it — it converts *unknown* into *declared contract with an effect class and a stated
obligation*, which is the actual WP04 deliverable.

The delegated worker measured 3 against a repository state that already contained `host.py`, could
not reproduce 29, and reported the measured number rather than forcing agreement with its brief.
That was the correct behaviour and it surfaced the ambiguity. Recording the distinction here so
future readings of either number are unambiguous.

## 2. The three undeclared types are declared

`EffectReceipt`, `VerifiedEffectReceipt` and `DoneReceipt` are declared in `frank_effects.clay`,
each field carrying a comment naming the exact call site it was derived from. This is
reconstruction of an existing contract from its call sites, not new design, and is marked
owner-reviewable.

None are marked `opaque`, on an evidence-driven rule: every opaque type in that file is built
exclusively through an `AUTHORITY_MINTING` intrinsic, whereas these three are built by plain
positional constructor calls like `EffectRequest` and `EffectAttempt`.

`execute`, `verify_effect`, `finish`, `authorize_effect`, `reserve_effect` and
`begin_effect_attempt` are now admissible once their intrinsics are bound.

### Three gaps reported rather than filled

- `runtime_effect` return type, which feeds `EffectReceipt.raw`, is declared nowhere.
- `independently_observe_effect` return type, which feeds `VerifiedEffectReceipt.observed`, is
  declared nowhere; only that it exposes `.matches_expected` is known.
- **`verb_for` has no mapping to derive.** No `.clay` source declares a `Verb` type or any
  kind-to-verb pairing. It is bound as identity, explicitly marked unvalidated, and confirmed
  unreachable from the functions under differential test. This is a real hole in the capability
  model, not a binding detail: `begin_effect_attempt` and `execute` both
  `require cap.verbs contains verb_for(intent.kind)`, so the capability check currently has no
  declared semantics to check against.

## 3. A stronger guarantee than the invariant asks for

While binding `policy_relevant_effect_projection`, a structural fact surfaced: **Clay's
`EffectRequest` never declares the four cognitive-hint fields at all.** `model_confidence`,
`gwt_ignition`, `claygraph_salience` and `translator_effect_hint` exist only on the Python side.

On the Python side the invariant `model_gwt_translator_claygraph_cannot_mint_authority` is
enforced by a filtering step that could in principle be forgotten. On the Clay side the record
**cannot carry them at all** — the guarantee is structural rather than procedural. Verified live:
constructing an `EffectRequest` with any of the four names raises `unknown field(s)`.

This is a case where the semantic source is stronger than its Python reference, which is worth
recording alongside the many cases where the reverse was true.

## 4. Differential coverage extended

Against the imported — not copied — Python reference:

| function | requests compared | mismatches |
|---|---|---|
| `effect_request_hash` | 56,000 | **0** |
| `confirmation_matches` | 16,000 | **0** |
| `decide_effect` (regression) | 5,576 | **0** |

`confirmation_matches` runs with `pure=False` and the READ_ONLY intrinsics bound, and was
separately reconfirmed to be **refused** under `pure=True`. The purity check was not weakened to
make the test pass.

Literal hash-value equality is explicitly **not** claimed: the two schemas genuinely differ, so
the gate tests hash-*change* agreement across the 24 shared fields plus hash-*invariance* to the
four Python-only hint fields. Claiming digest equality across differing schemas would have been an
overclaim.

## 5. Independent re-verification

Delegated work was not accepted on report. The coordinating session re-ran everything and added
its own falsification, which the worker had not performed: the replay guard
(`confirmation_nonce_used`) was removed from the `.clay` source, and the gate turned red with
**2,000 mismatches in 16,000**, sample
`{"scenario": "nonce_reused", "python_matches": false, "clay_matches": true}`. Source restored,
`git diff` clean.

## 6. What remains for F-V01-02

`frank_effects.clay` is now fully resolvable, but that is one file. Corpus coverage is unchanged
at **3 of 40 sources (7.5 %)** — the surface-extension work runs separately. Type/effect checking
beyond arity, lowering, runtime/FFI, stdlib and concurrency all remain open. The `verb_for` hole
in §2 should be treated as a capability-model gap for `F-V01-12`, not a ClayCode detail.

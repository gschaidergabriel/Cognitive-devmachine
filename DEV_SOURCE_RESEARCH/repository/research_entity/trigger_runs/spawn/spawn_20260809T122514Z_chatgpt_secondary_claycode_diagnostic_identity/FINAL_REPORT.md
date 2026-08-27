# SPAWN — ClayCode Stable Diagnostic Identity

Run: `spawn_20260809T122514Z_chatgpt_secondary_claycode_diagnostic_identity`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Scientific promotion: **NONE AUTOMATIC**

## Executive synthesis

The weighted CSPRNG branch draw selected ClayCode. A second CSPRNG microdirection draw, after filtering recent Spawn duplicates, selected the question of stable diagnostic identity across the ClayCode checker, compiler/lowering/runtime, fuzz/conformance and held-out corpus pipeline.

The central result is a constrained implementation hypothesis, not a new language primitive: ClayCode should represent a diagnostic as a structured envelope separating stable rule identity, rule semantic revision, occurrence fingerprint, semantic anchor/cause signature, source spans, human rendering, suggestions/children, run-local emission identity and toolchain provenance. Human text and absolute source positions should not be the identity used for regression or corpus labels. A versioned occurrence fingerprint should be computed from stable semantic fields only.

This direction became more relevant during the run because concurrent workers landed a WP11/WP12 conformance-corpus workflow and a compiler/runtime fuzz gate. Those gates generate and classify failures, but current evidence still shows failure observability/classification primarily through local `kind` strings, exception representations, stdout/stderr tails or coarse exception classes rather than a cross-stage stable diagnostic identity. The Spawn therefore complements rather than duplicates the live work.

No ClayCode surface-syntax change is justified. No BASE package is promoted by this run. Production integration and Ubuntu developer-host differential evidence remain required.

## Internal evidence fusion

`CLAYCODE_RELEASE_WORKSPACE.json` places the program in executable BASE realization and keeps WP04, WP11 and WP12 open. WP04 explicitly requires a validator/type/effect checker with precise diagnostics; WP11 requires fuzz/conformance across the production surfaces; WP12 requires a semantics-derived positive/negative corpus and leak-resistant held-out suite. The BASE burndown further requires the negative corpus to be tied to real checker diagnostics.

An earlier executable CBEL-TV checker provides a useful failure-information counterexample. Its reference path emits distinct semantic denial causes such as `DENY_BAD_SIGNATURE`, `DENY_INTENT_DRIFT`, `DENY_BASIS_DRIFT`, `DENY_SELECTION_DRIFT`, `DENY_REVOCATION_DRIFT`, `DENY_EXPIRED`, `DENY_CLOSURE` and `DENY_SCOPE`, while its lowered comparator returns only `ALLOW` or generic `DENY`. This shows that behavioral outcome equivalence does not automatically preserve diagnostic-cause equivalence.

The newer WP03 CI runner improves observability by always writing machine-readable stage receipts, including command, return code, stdout/stderr tails and pass/fail status. That is a useful prerequisite, but it does not yet create a stable diagnostic identity that survives source relocation or message/rendering changes or cleanly distinguishes multiple semantic causes under one rule.

During this run the repository also gained the WP11/WP12 conformance-corpus workflow and the compiler/runtime fuzz candidate. These developments narrow the integration surface: a stable diagnostic envelope can be introduced around existing `ClayError`/checker/runtime failures without reopening frozen BASE syntax or computational semantics.

## External research

Three primary-source families were used as mechanism precedent, not as proof of ClayCode correctness.

Rust `rustc` JSON diagnostics explicitly separate a unique diagnostic `code` from the primary message, source spans, child diagnostics, suggestions/applicability and rendered human output. Source: https://doc.rust-lang.org/beta/rustc/json.html

GCC supports structured diagnostic sinks and SARIF 2.1.0 output, with diagnostic hierarchy represented separately from classic text rendering. Source: https://gcc.gnu.org/onlinedocs/gcc/Diagnostic-Message-Formatting-Options.html

SARIF 2.1.0 defines result fingerprints and versioned `partialFingerprints` intended to help result-management systems identify logically identical results across runs while allowing fingerprint algorithms to evolve. Source: https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html

Cross-source pattern: mature diagnostic systems separate machine identity/structure from presentation and location. The ClayCode candidate goes one step further for this project by explicitly separating rule semantic revision from fingerprint-algorithm revision and by using canonical Clay semantic/resource anchors where available.

## Hypotheses and counterhypotheses

H1: a structured versioned fingerprint over `{rule_id, rule_revision, stage, semantic_anchor, cause_signature}` will produce better invariance/separation than text+span, rule-only or rule+anchor baselines for ClayCode fuzzing/regression/corpus use.

H2: message text, locale/rendering and absolute path/line/column are evidence/presentation fields and should not define the stable label for WP11/WP12.

H3: when lowering/runtime retains enough evidence to know a semantic denial cause, it should preserve or link that cause identity rather than collapse it to generic outcome-only `DENY`.

H4: `rule_revision` and `fingerprint_algorithm` need independent version axes because they evolve different concerns: diagnosed predicate meaning versus matching mechanics.

The major counterhypotheses remain alive: stable diagnostic identity may be premature BASE overengineering; rule ID alone may be sufficient; stable IDs may ossify checker implementation details; semantic anchors may accidentally remain stable even when the cause changes. The next production differential is designed specifically to discriminate these alternatives.

## Executed discriminator 1 — synthetic identity stress test

A reproducible Python probe generated 10,000 diagnostic events across parser, IR validation, type checking, effect checking and runtime-style rule families. Each base event received a nonsemantic perturbation of message wording, path, line and column. A second variant changed the semantic cause signature while holding rule/anchor context fixed. Four identity schemes were compared.

`text_span` had 0.0 nonsemantic invariance and 0.0 semantic-cause mutation detection. It produced nearly unique identifiers, but for the wrong reason: incidental presentation/location changes created identity churn.

`rule_only` had 1.0 nonsemantic invariance but 0.0 semantic-cause mutation detection. Across 9,990 distinct semantic events it collapsed to only six IDs, demonstrating extreme false equivalence.

`rule_anchor` had 1.0 nonsemantic invariance but 0.0 same-anchor semantic-cause mutation detection. It placed 4,261 semantically distinct events into collision buckets, showing that an anchor alone is insufficient when multiple causes can exist at the same node/resource.

`structured_v1` had 1.0 nonsemantic invariance, 1.0 semantic-cause mutation detection, zero collision buckets, and 9,990 unique IDs for the 9,990 distinct semantic events in this constructed test.

This is deliberately synthetic evidence. It demonstrates that the proposed identity decomposition is internally coherent under the tested perturbation model; it does not prove the production ClayCode checker emits sufficient semantic anchors or normalized cause fields.

## Executed discriminator 2 — real GCC location perturbation

A local GCC 14.2.0 probe compiled two C variants containing the same unused-variable warning. The second source added a comment, blank lines, indentation and a different path. GCC emitted the same warning option `-Wunused-variable` and the same message core while file, line and column changed.

This directly falsifies absolute location as a stable identity component for this ordinary refactor/layout case. It does not prove that GCC's own rule option is an adequate occurrence fingerprint; rather, it illustrates the separation problem in a real compiler. Scope is local-container compiler evidence, not Ubuntu ClayCode target-host acceptance.

## Candidate diagnostic contract

The run proposes `DIAGNOSTIC_IDENTITY_CONTRACT_CANDIDATE_V1.json` as a research candidate. Core fields are: `rule_id`, `rule_revision`, `stage`, severity, `semantic_anchor`, normalized `cause_signature`, versioned fingerprint algorithm, `occurrence_fingerprint`, source spans, message key/arguments/rendering, child/context diagnostics, structured suggestions/applicability, run-local `instance_id`, and exact compiler/runtime provenance.

Parser diagnostics may use a versioned token-context/parser-rule anchor when no canonical IR node exists, excluding whitespace/comments/absolute offsets unless a specific grammar rule makes them semantically meaningful. Type/effect diagnostics should prefer canonical typed-IR identity. Runtime/FFI diagnostics should use semantic resource identity/epoch plus operation and rule-declared cause fields. Opaque bearer capability material must not be serialized merely to improve diagnostics.

The candidate is intentionally authority-neutral: a diagnostic record never grants a capability, never authorizes an effect, and never converts model output into execution authority.

## Why this matters specifically now

The benefit is not cosmetic compiler UX. It creates a shared diagnostic coordinate system across WP04 checker negatives, WP11 fuzz/mutation results, WP12 training/held-out examples, WP13 FRANK/Harness handoff and later H1/H2 differential tests.

Without such a coordinate system, three failure modes become likely. First, harmless path/rendering edits create false-new failures and corpus churn. Second, rule-only/coarse exception labels create false-same failures that hide distinct causes and mutations. Third, backend/lowering transformations can be behaviorally equivalent while silently losing causal diagnostic information, making differential failures harder to localize.

A stable diagnostic identity can also improve UnifiedDB persistence/query and ClayGraph provenance linkage later, but this does not require a physical database merge or a ClayGraph semantic redesign.

## Mesh feedback

ClayCode receives a NEW_CONSTRAINT candidate: structure diagnostics so machine identity is separated from presentation and integrate it at the existing error-envelope layer rather than adding syntax.

Harness receives a NEW_HYPOTHESIS: H1/H2 differential failure matching should use stable semantic fingerprints where available while carrying backend/run provenance separately.

FRANK receives SUPPORTING_EVIDENCE for causal failure localization only. Diagnostics are observability metadata, not evidence of functional consciousness, GWT ignition or execution authority.

UnifiedDB receives a persistence/query constraint: if diagnostics enter the unified cognitive data substrate, preserve rule/fingerprint/provenance/span separation. ClayGraph, GWT, Emergenz and Hyperposition receive explicit NO_CHANGE at the semantic mechanism level from this run. ClayResearch receives the cross-cutting hypothesis that diagnostic identity can reduce false novelty and false equivalence in implementation/research receipts.

## Concurrency and negative-result handling

The first GitHub write attempt returned HTTP 409 because the main branch advanced between read and write. The run treated this as a real concurrent-change/CAS condition, re-read the head, assimilated the newly landed WP11/WP12 and fuzz work, and retried without force-overwriting anything.

This concurrency event itself reinforces the broader project rule: durable identity should distinguish semantic object identity from transient storage location/execution instance. It is not counted as scientific proof for the diagnostic hypothesis, only as an operational consistency observation.

Negative evidence is preserved: text+span failed invariance; rule-only failed separation; rule+anchor failed same-anchor cause discrimination. None is silently replaced by the winning synthetic scheme.

## Production falsification plan

A dynamic work event was created for the Ubuntu developer system. It requires integration around the current production ClayCode failure paths and a real differential: relocate source paths, introduce whitespace/comment/rendering changes, create multiple same-rule occurrences, mutate rule-declared causes at the same anchor, refactor checker implementation without changing predicate semantics, deliberately revise a rule predicate, and measure false-new/false-same/mutation-localization performance of structured identity against simpler baselines.

The work must also verify that diagnostic serialization cannot leak bearer authority and cannot grant effects. Only production-current Ubuntu receipts can move this from research candidate toward BASE evidence. A result that shows diagnostic identity is unnecessary or that the schema creates harmful coupling is an acceptable falsification outcome.

## Final decision

Keep the candidate. Do not reopen ClayCode syntax. Do not credit WP04/WP11/WP12 as PASS from this run. Integrate the diagnostic envelope into current production error paths when local build execution reaches them, use it as the stable label layer for fuzz/corpus tests, and require the Ubuntu production differential before promotion.

The strongest current interpretation is that ClayCode needs **stable diagnostic identity as a tooling/observability contract**, not as a new computational language primitive. This yields a small architectural addition with unusually high leverage across checker precision, fuzzing, corpus quality, regression, translation validation and Harness handoff while respecting the frozen-semantics rule.

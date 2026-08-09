# Spawn Research Run — ClayCode Unicode Canonical Boundary

Run: `spawn-20260809T1813p0700-claycode-unicode-canon`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Origin branch: `claycode`  
Promotion: **none — research delta only**

## Executive result

The weighted Spawn draw selected `claycode` with OS-CSPRNG draw `37/100`. Two initially selected microdirections were rejected as recent duplicates: adaptive visual learner version-state semantics had already been tested in `spawn-20260809T1746p0700-claycode-mvc-state`, and typed canonical identity had already been tested deeply in `claycode_20260809T1606p0700_chatgpt_semhash_typedcanon`. The accepted microdirection was therefore `UNICODE_CANONICAL_BOUNDARY`.

The new finding is narrow but release-relevant:

> **ClayCode must not silently make Unicode normalization a global serializer/canonicalizer behavior for generic `String`.**

For the current BASE candidate, the least-churn policy is:

1. generic `String` semantic identity preserves the exact Unicode scalar sequence after escape decoding;
2. any canonical-equivalence text semantics are explicit/type-directed, with NFC as the current research candidate rather than an invisible default;
3. NFKC is never applied implicitly to arbitrary generic text;
4. semantic hash preimages are domain-separated by semantic type/policy;
5. exact source/wire/provenance identity remains separate from semantic identity;
6. invalid non-scalar/lone-surrogate data fails deterministically;
7. if explicit normalized text exists, normalization occurs after final construction/concatenation or through a normalization-aware concat operation.

No new FRANK-specific or ClayCode-specific primitive is justified by this run. The result is a compiler/canonical-IR constraint and conformance target.

## Why this is new

The earlier type-directed canonicalization run established `Set` versus `Ordered` semantics and separated semantic/artifact/contract/deployment identities. It did not isolate Unicode equivalence, compatibility folding, normalization-version boundaries or normalized-string concatenation.

The recent MVC Spawn used versioned learner state but did not test Unicode normalization.

A recent commit search found no prior `unicode canonical` Spawn/run. This run therefore extends the existing canonical-identity lineage rather than duplicating it.

## Current ClayCode surface

`D_LALR_GRAMMAR_CANDIDATE_V3.lark` currently restricts `NAME` and `REF` to ASCII-compatible regular expressions. Unicode therefore matters immediately in string payloads, not identifier spelling.

That makes Unicode identifiers unnecessary for the current BASE parser freeze. Adding them now would create a second problem — identifier profile, normalization and spoofing policy — without evidence that a current required application needs them.

## Executable discriminator

A hosted Python probe generated and tested Unicode pairs from the runtime Unicode Character Database 15.1.0.

Observed:

- **12,665 / 12,665** canonical-equivalence pairs satisfied the candidate contract:
  - exact-text hashes remained distinct when scalar sequences differed;
  - explicit NFC-text hashes became equal;
- **2,411 / 2,411** compatibility-only pairs remained distinct under exact and NFC semantic identity while NFKC would collapse them;
- **0** cross-kind hash collisions in the adversarial typed sample;
- **4 / 4** tested lone-surrogate values were rejected;
- **4 / 4** normalized-component concatenation cases demonstrated that individually NFC strings can concatenate into a non-NFC value;
- a direct observable counterexample shows why global NFC is not semantics-neutral for generic strings: `U+00E9` is one code point while `U+0065 U+0301` is two code points even though both normalize to the same NFC value.

Verdict: `PASS_TYPED_POLICY_PROXY`.

Evidence class remains `HOSTED_PYTHON_PROXY_NOT_NORMATIVE_CLAYCODE_OR_UBUNTU_TARGET_EVIDENCE`.

## Negative results

### N-SPAWN-CC-UNICODE-001 — Global implicit NFC is not semantics-neutral

If generic `String` exposes scalar/codepoint sequence operations, silently NFC-normalizing every string changes equality, length, indexing/substrings and hash behavior for some inputs. A canonicalizer cannot make that change without the language semantics explicitly choosing it.

### N-SPAWN-CC-UNICODE-002 — Global implicit NFKC is unsafe for arbitrary text

Compatibility normalization intentionally erases distinctions such as ligatures, width variants, circled digits, Roman numerals and superscripts. The local corpus found 2,411 compatibility-only BMP cases under the runtime database. Such folding may be useful for explicit search/matching contexts but is not a safe generic identity rule.

### N-SPAWN-CC-UNICODE-003 — Normalize-parts-then-concat is insufficient

Normalization forms are not closed under concatenation. Token-level or component-level normalization therefore cannot guarantee that a constructed normalized-text value remains normalized.

### N-SPAWN-CC-UNICODE-004 — Wire canonicalization does not decide semantic Unicode equivalence

A deterministic serialization scheme may preserve Unicode strings as-is. Therefore `deterministic bytes` and `canonical-equivalent text semantics` are separate design decisions.

## External triangulation

Primary standards were used only to constrain the mechanism, not to promote ClayCode automatically:

- Unicode Standard Annex #15, current published Unicode 17.0.0, distinguishes canonical from compatibility equivalence, defines NFC/NFD/NFKC/NFKD, warns against blindly applying compatibility normalization to arbitrary text, and specifies that normalized strings are not closed under concatenation.
- Unicode Standard Annex #31 treats identifier normalization/profile behavior as a language/specification decision and presents NFC as the straightforward route for canonical-equivalent Unicode identifiers.
- IETF RFC 8785 JSON Canonicalization Scheme deliberately preserves Unicode string data as-is and rejects invalid lone-surrogate data; deterministic wire encoding therefore does not imply Unicode normalization.

These sources support the separation of concerns. The project-specific policy still requires ClayCode execution evidence.

## Cross-mesh implications

### ClayCode

Add Unicode exact/canonical/compatibility/invalid-scalar/concat cases to `CC-WP-02-PARSER-CANON`, `CC-WP-03-IR-TYPES` and `CC-WP-11-FUZZ-CONFORMANCE`. Do not redesign the language unless normative execution exposes an actual semantic gap.

### Harness

H1/H2 differential traces should contain exact-vs-canonically-equivalent text, compatibility-only strings, invalid scalar inputs and concat-boundary cases. This is a future differential-oracle target, not a Harness result from this run.

### UnifiedDB

Query, key, collation and deduplication layers must not let a backend collation silently redefine Clay semantic identity. Each data class needs explicit comparison/normalization semantics.

### ClayGraph

Human-readable labels, searchable normalized text and entity/relation identity should remain distinguishable. Compatibility folding must not merge provenance or graph identity accidentally.

### FRANK

Replay/version/provenance state should depend on explicit Clay text identity rules, not host-library normalization accidents. This is infrastructure support, not a new cognitive mechanism.

### GWT / Emergenz / Hyperposition

No scientific mechanism changes. Unicode/hash equivalence remains representation infrastructure and is not evidence of workspace closure, emergence or higher-order coupling.

### Clayresearch

Carry the result as a compiler/runtime semantic-identity constraint within the integrated research mesh.

## Goodman anti-echo

The FRANK need for deterministic replay identity was treated as shared ancestry, not independent support. The Unicode-specific discriminator came from the hosted counterexample corpus plus independent primary Unicode/IETF standards.

Verdict: `REFINED_NO_PROMOTION`.

## Concurrency receipt

One append-only GitHub write encountered a 409 because concurrent workers advanced the repository head. The write was not forced. The new head `194f7f4f04cea0a2d51c1607af3f5aeb803dc994` was reread; concurrent Harness visual-action, Emergenz probe-effect, hypofusion-r3 and ClayCode bootstrap-tool work showed no contradiction with this Unicode finding; the append-only write was then retried successfully.

## Limitations

- The executable probe used Python 3.13.5 with Unicode Character Database **15.1.0**; the current Unicode standard source checked is **17.0.0**. The final ClayCode/Ubuntu contract must pin and verify its Unicode version/conformance data.
- No normative ClayCode parser/canonical IR/type-effect/compiler stack executed this corpus.
- No Ubuntu developer-system execution occurred in this ChatGPT worker.
- The official repository-native interconnect preflight script could not be run because this organ has GitHub connector access but no checked-out repository shell. Manual complete branch coverage was recorded without claiming official preflight PASS.
- No BASE gate credit or canonical generation promotion follows from this proxy.

## Next highest-information test

Once the strict-LALR parser/canonicalizer path is executable, run a production differential corpus through:

`source string -> parser -> typed canonical IR -> semantic_hash/contract_hash -> evaluator -> lowering/compiler -> Ubuntu executable -> replay receipt`

The corpus must cover:

- canonically equivalent exact strings;
- compatibility-only strings;
- length/equality/substring/index operations;
- concat/interpolation/builders;
- invalid scalar/lone-surrogate inputs;
- exact source/provenance preservation;
- optional explicit NFC operation/type if present;
- cross-runtime hash/replay equality under a pinned Unicode version.

If that passes, this constraint can become part of the frozen BASE canonicalization contract. If a required application proves that Unicode identifiers are needed, open a separate identifier-profile experiment instead of smuggling identifier normalization into generic string semantics.

## Durable delta

This run committed:

- stochastic Spawn receipt with duplicate rerolls;
- executable Unicode canonical-boundary probe;
- executable research receipt;
- hypotheses/counterhypotheses;
- primary-source evidence manifest;
- complete manual interconnect manifest;
- 9-branch feedback manifest;
- Goodman anti-echo review;
- tool execution manifest;
- BASE parser-freeze work-revision event;
- this final report.

**Research conclusion:** keep generic ClayCode String exact by default; make Unicode normalization explicit/type-directed; do not implicitly NFKC; keep current ASCII identifiers for BASE unless a real executable requirement falsifies that minimal policy. **No promotion.**

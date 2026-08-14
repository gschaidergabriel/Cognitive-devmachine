# GO recursive cycle — FINAL REPORT

Run: `go-20260810T0706p0700-chatgpt-secondary`  
Actor: `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
Role: temporary Clay research worker, not Frank  
Program stage: `BASE_CLAYCODE_RELEASE`  
Critical package: `CC-WP-02-PARSER-CANON`

## 1. Fresh-state decision

Current ClayCode BASE remains gate `NOT_PASS`. WP01 is the only package currently credited PASS; WP02 remains OPEN under the production/Ubuntu receipt accounting rule. The highest-value non-duplicative executable work was therefore to close the current Hostinger-side parser/canonicalizer falsifier without promoting proxy evidence into target acceptance.

## 2. Hypothesis / strongest counterhypothesis

Hypothesis:

> The apparent V9 -> V17 semantic drift was primarily caused by Lark's default absent-optional placeholders reaching semantic canonicalization as `None`, while the intended V17 change only repairs the horizontal-trivia `Needle.owns (X)` call boundary.

Strongest counterhypothesis:

> Even after suppressing absent optional placeholders, V17 changes ordinary admitted semantics or collapses meaningful optional structure; alternatively, strict construction may hide regex-lookaround collisions not covered by `interegular`.

## 3. Live primary-source refresh

Current official Lark documentation independently supports the selected main repair: `maybe_placeholders=True` is the default and absent `[]` optionals can produce `None`; setting it false makes the optional form omit the child. Current Lark documentation also warns that advanced regex constructs such as lookaround can limit collision detection, so `strict=True` is necessary but not sufficient for this grammar. The current Clay tests therefore correctly retain explicit relation/call metamorphic boundary checks.

Durable source packet:

- `LIVE_LARK_PLACEHOLDER_PRIMARY_EVIDENCE.json`

## 4. Root-cause discrimination

The first V9/V17 comparison failures were localized to frontend placeholder handling, not ordinary V17 semantic drift. Current main already contains the stronger parser-construction repair:

- frontend blob: `55728fd20323a364bb5e831989644b65189603d1`
- mechanism: `Lark(... maybe_placeholders=False)`

An independent diagnostic `canonical_node(None) -> None` candidate was therefore redundant and was not selected.

## 5. Real Hostinger Ubuntu evidence

### 5.1 Placeholder-mode falsifier

Run `31343561845` passed on runner `clay` / machine `digital-retina` / Ubuntu-Linux-compatible Hostinger lane with Python 3.12.3, Lark 1.3.1 and interegular 0.3.3.

Observed:

- V9/V17 equality preserved for G9, Dialect, ordinary module/record/needle/lifecycle and non-target relation cases;
- V9 horizontal-trivia counterexample reproduced;
- V17 horizontal-trivia repair rescued it;
- optional type, Needle parameter, type-parameter and field-default distinctions remained semantically discriminated.

This receipt explicitly did not count as WP02 PASS or Andreas-target acceptance.

### 5.2 Exactly one bounded out-of-the-box experiment

`OPTIONAL_OPERATOR_METAMORPHIC_EQUIVALENCE`

Result: PASS.

The experiment compared equivalent absent/present optional forms under placeholder-disabled mode and verified the default-mode lesion still exposes `None`. It received no architecture promotion; its only role was to discriminate the placeholder-root-cause hypothesis.

No second novelty experiment was started in this `go` macro-cycle.

### 5.3 Full repaired-frontend closure V2

The first matched replay was invalidated before science by a receipt-path bug in the discriminator (`Path.relative_to()` on a `/tmp` output). Current main fixed that observability/path defect with a display-path fallback. A stale V2 hash binding was then corrected without changing Clay language semantics.

Fresh exact-source Hostinger run:

- workflow run: `31343972917`
- job: `93322339694`
- result: SUCCESS
- source revision: `d94a6807b0733860d3612b5cf205e95cb3367588`
- V9 blob: `cdeff8095e6703a6889a60093876c8f0cb0a2b8a`
- V17 blob: `c3619e3168fdce9115bc7b9ab55425e7b02e0c2a`
- frontend blob: `55728fd20323a364bb5e831989644b65189603d1`
- discriminator blob: `8f2f9c317aa1f43488d20c05bc915f2ca60dfd74`
- artifact id: `9046775720`
- artifact ZIP SHA-256: `6bf28269a543eff68a546de91aa8efa818d179e8e6b9fbfbedabe2e9781fd093`

All four complete gates passed:

1. discriminator;
2. strict LALR construction;
3. repaired frontend full corpus and lexical/metamorphic regression suite;
4. grammar-bound deterministic canonicalization, semantic discrimination and JSON/hash roundtrip.

Canonical hashes:

- G9: `ec292e50f2f17dafd3832f808a7a5a0e74495f63916ef1249cdea818bfeca53d`
- Dialect: `b810e464ec67bdde04c40a49d2186449091a4e26ec5404e8bc7a37e138e9eced`

Wall-time shadow:

- discriminator: 5180 ms
- strict: 769 ms
- frontend: 560 ms
- canonical: 559 ms

Resource fields `user_s`, `system_s`, and `max_rss_kb` remain literal `UNKNOWN`: the aggregate `/usr/bin/time -v` parser did not consume the leading whitespace. This is retained as an observability defect, not silently converted to zero and not treated as a parser failure.

Durable receipt:

- `HOSTINGER_WP02_FULL_CLOSURE_V2_31343972917.json`

## 6. Adjudication

Supported:

- absent optional placeholder handling was the material root cause of the prior false V9/V17 semantic-drift signal;
- current main's `maybe_placeholders=False` is the preferred repair;
- V17 repaired grammar + current frontend/canonicalizer closes the Hostinger-side WP02 research closure on the tested exact blobs;
- no further WP02 semantic patch is justified by this run.

Not promoted:

- `CC-WP-02-PARSER-CANON` remains OPEN;
- no Andreas-target acceptance is claimed;
- no performance superiority claim is made from single-run timing shadows;
- no training was authorized or attempted.

## 7. Negative / infrastructure results retained

- Older full-replay red result: receipt-path transport/observability bug, not parser counterevidence.
- Stale V2 red result: exact hash-lock correctly rejected an obsolete discriminator binding before science.
- Current full V2 resource parser returns CPU/RSS fields UNKNOWN; production-target measurement wrapper needs repair.
- PR #58 contains many historical diagnostic workflows; synchronize pushes caused self-hosted queue amplification. No blind queue deletion/cancellation was performed.

## 8. Cross-package impact

WP03 must consume the selected WP02 parser/optional/scalar contract rather than independently reconstructing default Lark placeholder semantics. If WP03 intentionally needs explicit null/arity semantics, that difference must be versioned and typed rather than arising accidentally from parser defaults.

No WP03 promotion or source patch was made in this cycle because WP02 formal target adjudication remains the preceding gate.

## 9. Next highest-information falsifier

Execute the registered CC-WP-02 production acceptance bundle on Andreas' Ubuntu developer system with the same exact source identities and:

- strict construction;
- full G9 + Dialect corpus;
- relation/call metamorphic guards;
- deterministic canonical JSON/hash roundtrip;
- mutation/semantic discrimination;
- corrected raw CPU/user/system/RSS capture;
- exact runtime/build/provenance metadata.

Only after that target receipt should formal WP02 PASS be adjudicated and WP03 production integration become the next critical-path package.

## 10. Final result

`HOSTINGER_WP02_RESEARCH_CLOSURE = PASS`

`CC_WP02_FORMAL_PACKAGE_STATUS = OPEN`

`ANDREAS_TARGET_ACCEPTANCE = NOT_EXECUTED`

`TRAINING = NOT_AUTHORIZED_NOT_ATTEMPTED`

`RESEARCH_WRITE = COMMITTED`

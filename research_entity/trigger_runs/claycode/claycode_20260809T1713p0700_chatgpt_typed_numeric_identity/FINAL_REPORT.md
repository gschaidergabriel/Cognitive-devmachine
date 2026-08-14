# ClayCode Trigger Run — Typed Numeric Semantic Identity

Run: `claycode_20260809T1713p0700_chatgpt_typed_numeric_identity`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Promotion: **NONE**  
Stage progress credit: **NONE**

## Executive result

This run selected a non-overlapping BASE lane after cross-reading the live ClayCode/Harness/ClayResearch mesh: **numeric semantic identity across canonical IR and lowering**.

The strongest result is narrow:

> ClayCode should not use host-native JSON numeric text as semantic-hash material. For the tested domain, preserving numeric type and canonical value in typed IR eliminates the observed Python/Node identity drift without requiring a new ClayCode surface primitive.

A local cross-runtime executable probe tested 20,013 integer lexemes and 50,010 finite float lexemes:

- typed exact-Int token `I:<canonical base10 integer>`: **0/20,013 mismatches** between Python arbitrary-precision integers and Node `BigInt`;
- typed F64 token `F64:<IEEE-754 binary64 bits>` after parsing the same decimal literal: **0/50,010 bit mismatches** between CPython and Node/V8;
- naive Int -> JavaScript `Number`: **15,676/20,013 exactness mismatches**;
- host-native JSON float text: **2,427/50,010 textual mismatches** even where the parsed F64 bits matched;
- negative zero was parsed with the same sign bit by both runtimes while host JSON presentation differed (`-0.0` versus `0`).

This is not a released numeric contract. It is local mechanism evidence and a concrete BASE canonicalizer requirement.

## Current-stage grounding

The current program remains `BASE_CLAYCODE_RELEASE`; all 14 ClayCode release work packages were OPEN at boot and no application acceptance item was PASS.

The current engineering rule therefore remains unchanged:

`less change, more compile`

The run does not change G9 source semantics, the checked-in grammar, canonical ClayCode authority, stage state, application acceptance state or canonical Research Entity revision.

## Why this lane

Fresh parallel workers were already covering:

- G9 parser/relation surface freeze;
- DB transactions and host-owned resources;
- resource-handle ABA/stale identity;
- source-chain evidence;
- compiler provenance semantic gates;
- effect recovery;
- idempotency concurrency.

The numeric lane was selected because a fresh negative result had already shown cross-runtime host JSON differences, while the new Harness SourceChainEvidence requirement now makes semantic-hash identity part of the mandatory chain:

`source -> parse -> typed_ir -> lowering -> execution -> replay`

This run tests one missing precondition of that chain rather than duplicating existing workers.

## Internal evidence fused

### ClayCode

Current G9 surface research shows that the immediate parser blocker is mainly grammar/surface closure rather than a missing cognitive primitive. A strict-normalization candidate reached 86/86 top-level parse closure in a proxy, but N/S/D surface policies remain unresolved pending a matched typed-IR oracle.

This numeric run therefore treats the source spelling and typed semantic identity as separate layers.

### Harness

SourceChainEvidence v1 requires continuity of parser admission, typed semantic identity, type/effect contract identity, lowering identity, execution receipts and replay. It also explicitly warns that semantic hashes must not depend on host-native JSON number formatting.

### ClayResearch / CTK

The current CTK convergence hypothesis favors a small common transition header plus typed domain payloads rather than universal physical/semantic collapse. Numeric identity belongs in the typed payload/IR contract; backend serializer formatting should not become CTK semantic identity.

### UnifiedDB / ClayGraph

The current mesh separates semantic identity from runtime resource identity, and logical/version identity from activation, provenance, admissibility and authority. Numeric canonicalization must preserve these separations rather than using one transport representation as truth/authority.

### FRANK / GWT / Hyperposition / Emergenz

No direct scientific architecture change follows from this run. Numeric canonicalization is compiler/runtime identity evidence, not GWT causal-use evidence, higher-order topology evidence or causal-emergence evidence.

## External primary-source research

Independent standards were used as engineering analogues only.

### RFC 8785 — JSON Canonicalization Scheme

JCS exists to produce invariant JSON suitable for cryptographic hashing/signing, but its number model is intentionally constrained to the I-JSON / IEEE-754 double domain. Larger or higher-precision numbers are expected to use strings. NaN and Infinity are invalid; negative zero serializes as zero.

Implication: JCS is a viable canonical transport for a restricted numeric model, but it cannot silently stand in for ClayCode's universal typed numeric semantic identity.

### RFC 8949 — CBOR

CBOR distinguishes integer and floating-point values in its data model and defines deterministic encoding rules. However, protocols still need to specify choices such as integer-versus-float identity, treatment of negative zero and handling of nontrivial floating values.

Implication: deterministic CBOR can be an implementation candidate, but the typed semantic contract must come first.

### WebAssembly numeric representation

WebAssembly represents numeric types explicitly and encodes floating-point values directly from their IEEE-754 bit patterns. Its arithmetic semantics also allow some nondeterminism in NaN sign/payload propagation.

Implication: exact F64 bit identity is useful for literal/value representation, but exact arithmetic replay must define semantic equivalence separately for NaN-producing operations unless Clay narrows backend behavior.

These standards do not validate FRANK or ClayCode; they independently support the engineering distinction between numeric semantic type/value and presentation serialization.

## Executable experiment

Artifact:

`experiments/typed_numeric_canonicalization_probe.py`

Receipt:

`EXECUTABLE_RESEARCH_RECEIPT.json`

Environment:

- CPython 3.13.5;
- Node v22.16.0;
- hosted Linux x86_64;
- seed `202608091713`.

Preferred E2B replication could not be invoked because the current ChatGPT tool surface did not expose an E2B execution action. This is recorded as a tool-surface limitation; no E2B failure or E2B result is claimed.

### Integer arm

Candidate identity:

`I:<canonical base10 integer>`

Result:

- 20,013 cases;
- typed cross-runtime mismatches: `0`;
- naive Node `Number` exactness mismatches: `15,676` (`78.3291%`).

The high mismatch rate is expected because the corpus intentionally spans up to 256-bit integers; it is a counterexample generator, not an estimate of real application frequency.

### Float arm

Candidate identity:

`F64:<IEEE-754 binary64 bits>`

Result:

- 50,010 finite decimal-literal cases;
- Python-vs-Node parsed-bit mismatches: `0`;
- host JSON textual mismatches: `2,427` (`4.8530%`).

Representative presentation disagreements included integer-looking finite values, exponent-vs-decimal formatting, underflowed zero and negative zero.

This supports using typed value identity rather than serializer text for the tested literal domain.

## Hypotheses and counterhypotheses

### H-CC-NUMID-001 — supported local executable

Typed exact Int plus typed F64 value identity can remove the tested cross-runtime semantic-hash drift.

Counterhypothesis: JCS/string wrappers or deterministic CBOR can achieve the same result with lower complexity.

Highest-information test: implement both behind the same production typed-IR oracle and compare bytes, latency, diagnostics, migration cost and replay stability.

### H-CC-NUMID-002 — supported negative

Host-native JSON number text is not a universal semantic identity layer.

Falsifier: a deliberately restricted released numeric contract proves all erased distinctions and out-of-range values irrelevant.

### H-CC-NUMID-003 — open refined

Exact F64 bit identity is suitable for parsed literal/value identity, but arithmetic equivalence should not automatically require exact NaN sign/payload identity.

Next test: native versus Wasm arithmetic and replay with finite values, signed zero, infinities and NaN-producing operations under preregistered equivalence classes.

### H-CC-NUMID-004 — no core syntax change

The present mismatch is repairable at typed IR/canonicalization/lowering boundaries. No new FRANK-specific or ClayCode surface numeric primitive is justified.

Falsifier: a real BASE application requires numeric semantics that current G9 typed state plus library/domain types cannot safely express.

## Goodman anti-echo

The run explicitly tested whether the project was merely echoing its own assumptions.

- Stable representation for hashes/replay: independently supported as a general engineering need by RFC 8785, but not proof of FRANK architecture.
- JSON as universal numeric identity: rejected for the general ClayCode domain.
- Deterministic binary serialization solves semantics automatically: rejected; RFC 8949 still requires protocol choices.
- Exact F64 bits solve all arithmetic replay: rejected as a universal claim because backend arithmetic can admit NaN nondeterminism.

The strongest simpler alternative remains active: existing canonical formats plus explicit typed wrappers may outperform a Clay-specific token format.

## Negative results preserved

1. General Int -> JS `Number` is unsafe as exact lowering.
2. Host JSON float text is not cross-runtime semantic identity.
3. JSON presentation can erase negative-zero sign.
4. Literal bit agreement does not prove arithmetic/NaN determinism.
5. No new surface numeric primitive is justified.
6. No BASE stage/application PASS follows.
7. Two direct `main` writes encountered HTTP 409 due live concurrent workers; neither was forced. Remaining artifacts were isolated on a research branch for PR integration.

## Architecture/program implication

The current best BASE rule is:

`source numeric literal`
`-> parser`
`-> typed numeric value`
`-> explicit canonical semantic identity`
`-> type/range/effect legality`
`-> backend lowering with checked exactness`
`-> execution receipt`
`-> replay comparison under type-specific equivalence`

Do **not** use:

`host JSON text == semantic identity`

Do **not** infer:

`same textual number == same typed semantics`

or

`same final float text == same arithmetic trace`.

This integrates naturally with the SourceChainEvidence gate and CTK typed-payload direction without changing current G9 surface semantics.

## Next discriminating experiment

On the production BASE toolchain and Andreas' Ubuntu developer host:

1. compile one numeric witness through the real parser and typed canonical IR;
2. compare a minimal Clay typed-token canonicalizer against deterministic CBOR or JCS-with-explicit-number-wrappers;
3. lower to native and Wasm/WASI targets;
4. test exact big integers, signed zero, min/max/subnormal finite F64, overflow, infinities and NaN-producing arithmetic;
5. preregister which distinctions are semantic identity versus allowed backend equivalence;
6. bind source, parser, typed IR, numeric identity, lowering contract, execution and replay receipts through SourceChainEvidence;
7. measure implementation size, bytes, latency, diagnostics, migration edits and replay mismatches.

Only a production counterexample should justify new surface numeric semantics.

## Durable writeback

This run writes:

- `experiments/typed_numeric_canonicalization_probe.py`;
- `EXECUTABLE_RESEARCH_RECEIPT.json`;
- `HYPOTHESES.json`;
- `NEGATIVE_RESULTS.json`;
- `FRANK_CLAYCODE_GOODMAN_REVIEW.json`;
- `INTERCONNECT_MANIFEST.json`;
- `TOOL_EXECUTION_MANIFEST.json`;
- `BRANCH_FEEDBACK_MANIFEST.json`;
- `RUN_MANIFEST.json`;
- this `FINAL_REPORT.md`.

No canonical revision or stage gate is promoted by this run.

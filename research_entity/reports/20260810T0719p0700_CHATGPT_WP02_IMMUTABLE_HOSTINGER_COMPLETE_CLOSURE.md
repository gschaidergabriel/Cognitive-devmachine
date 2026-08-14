# CC-WP-02 immutable Hostinger complete closure — 2026-08-10 07:19 +07

Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Entity role: temporary Clay Research Entity worker; NOT Frank  
Trigger: exact `go`  
Mission: `Frank v0.1 voll lauffähig auf Andreas PC`

## Adjudicated remote execution receipt

Executor repository: `gschaidergabriel/Dr.-Unterweger`  
Workflow: `Clay WP02 Immutable Single-Flight Closure`  
Run: `31343808739`  
Job: `93321887528`  
Conclusion: `SUCCESS`  
Artifact: `9046651093`  
Artifact SHA-256 digest: `a833d73b909f228b9a5239e11eb0e7e6cf7c0fcb5d9689b65025eb5057d165f3`

Immutable executor snapshot:

`1a8c3d785a4d79cc2b8edece6d54878bbe7b78de`

Bound Clay source revision:

`12614c6d8e350da4152c6d54beff5ee7255a4979`

The job checked out the immutable executor commit directly rather than a moving PR merge ref, used `persist-credentials: false`, and verified every source Git blob before executing any scientific gate.

Verified source Git blobs:

- V9 grammar: `cdeff8095e6703a6889a60093876c8f0cb0a2b8a`
- V17 grammar: `c3619e3168fdce9115bc7b9ab55425e7b02e0c2a`
- dependency lock: `4a361757efede020cfb288ad7beda2c4a7e6c6b5`
- G9 corpus: `93cb0dd666f3498c85805d97cdae84850734d3ed`
- Dialect corpus: `dbb72460bc5a049c784d1acd1aaef152fa37f797`
- repaired production frontend: `55728fd20323a364bb5e831989644b65189603d1`
- strict probe: `e050b922acefe554ba4d6de19c4324952d45e803`
- frontend validation v1.6: `031c08d42b3fe01376a83424f39cc6dc140b4adb`
- canonicalizer: `582e91135aa4d01d4b6ec7b854a10b9075e52bd4`
- V17 discriminator: `71fc016ecf8a6b6497cdfd115fdbcfee8c48486c`

## Host/runtime metadata

- runner name: `clay`
- host: `digital-retina`
- runner version: `2.336.0`
- OS/arch: Linux / X64
- kernel: `6.8.0-117-generic`
- virtualization: `kvm`
- CPU: AMD EPYC 9354P 32-Core Processor
- exposed CPU threads: `4`
- MemTotal: `16376020 kB`
- Python: `3.12.3`
- Git: `2.43.0`
- Lark: `1.3.1`
- interegular: `0.3.3`
- boot id: `8fab241d-868e-447d-b802-01d403c22e88`
- receipt UTC: `2026-08-10T00:13:52Z`

The Python environment was created from the hash-locked WP02 dependency file with `--require-hashes --only-binary=:all:`.

## Complete four-gate result

All aggregate return-code and semantic checks passed:

1. V9 -> V17 declarative-trivia discriminator: PASS, strict=true, V9 counterexample reproduced, V17 rescue accepted.
2. Strict-LALR construction: PASS, `PASS_STRICT_CONSTRUCTION`, zero conflict diagnostics. Regex lookaround remains an explicit scope caveat, so direct metamorphic boundary tests remain required and were present in the frontend gate.
3. Full repaired-frontend validation: PASS on full G9 and Dialect corpora, deterministic repeated parse fingerprints, keyword/newline negatives and positives, lexical discrimination and trivia invariance.
4. Grammar-bound canonicalizer: PASS, deterministic repeat and layout/comment invariance, semantic-surface discrimination, decoded-string spelling identity and unpaired-surrogate rejection.

Aggregated receipt:

`pass = true`

`architecture_delta = NO_CHANGE`

`counts_as_wp02_pass = false`

`counts_as_andreas_target_acceptance = false`

`promotion_allowed = false`

This is the first observed complete immutable exact-source Hostinger closure of all four current-at-source-revision WP02 parser/canonicalizer research gates after the production `maybe_placeholders=False` repair.

## Timing/resource shadow

Measured wall times from the immutable run:

- discriminator: `5705 ms`
- strict construction: `1014 ms`
- full frontend validation: `794 ms`
- canonicalizer: `599 ms`

The wrapper attempted GNU `time -v`, but its aggregate parser did not recover CPU/RSS/page-fault/context-switch fields and recorded them as literal `UNKNOWN`. Do not infer zero or fabricate values. The newer Clay closure runner now captures these fields more directly and remains the preferred future measurement path.

Component receipt SHA-256 values:

- discriminator: `4077ee011152f63bfbb45e2732f21b1a8c013f0c4d30a988b89e2ba2f519ee6a`
- strict: `b439ffc91b181c1a66ad49498c5980f4c3868f9d502618a8dec8114647772297`
- frontend: `e86ffaf249b06e4f1c51ea4dd57106a1f3418097cfbcb7574416b629855c92d9`
- canonical: `42acc2cb774ff304f30a1db75f8d158231b8c45d8b2d578db5c34a4976d91cdb`

## Negative-result lineage preserved

This PASS does not erase the causal failures that led to it:

- Clay repository jobs could not use the Hostinger runner because it is repository-scoped to `Dr.-Unterweger`.
- cross-private-repository HTTPS/SSH clone attempts failed before ClayCode execution;
- a cross-repository Git blob shortcut was rejected;
- the first real full closure exposed production `canonical_node(None)` failure;
- matched diagnosis showed strict parser, standalone frontend and canonicalizer were otherwise healthy;
- Lark default optional placeholders were isolated as the source of the synthetic `None` children;
- the production repair `maybe_placeholders=False` landed at Clay commit `12614c6...`;
- a later matched Hostinger placeholder-mode falsifier independently passed optional-semantic discrimination and V9-lesion/V17-rescue;
- several early replay wrappers failed on output paths outside the source root or moving PR merge refs; these were harness failures, not ClayCode semantic failures;
- PR-head churn amplified queueing on the single repository-scoped runner; immutable single-flight execution removed that confounder.

## Fresh-main delta after this run

After run `31343808739`, Clay main advanced. Commit `eba2441de9f647b078665789f652a799cc7acb17` strengthens `tools/claycode_base_frontend_validation.py` from schema 1.6 to 1.7 by:

- constructing the parser through `claycode_base_frontend.build_parser`;
- explicitly inheriting `maybe_placeholders=False`;
- counting `None` children on corpora, positive fixtures and pair checks;
- adding four absent-optional regression cases;
- failing unless placeholder count is zero.

This is a test-contract strengthening, not a new product-frontend semantic change. Its underlying hypothesis is independently supported by Hostinger run `31343561845`, which already showed zero-collapse optional semantics and exact V9/V17 matched behavior on repaired frontend blob `55728...`. However, the exact new v1.7 validator file itself was not part of run `31343808739`.

Therefore current classification is:

`REMOTE_HOSTINGER_WP02_RESEARCH_CLOSURE_PASS_AT_SOURCE_REV_12614C6`

plus

`LATEST_VALIDATOR_V1_7_DIRECT_REMOTE_REEXECUTION = OPEN_TEST_OBLIGATION`

## Architecture / program consequence

Architecture delta: `NO_CHANGE`.

The production `maybe_placeholders=False` repair remains supported. No further grammar/frontend mutation is justified by this receipt.

CC-WP-02 remains formally OPEN because Hostinger is a research Ubuntu lane, not Andreas' actual target developer system. Do not convert this receipt into final target acceptance or package promotion.

Current strongest next actions:

1. execute the strengthened v1.7 frontend validator on the same exact repaired production frontend / V17 / G9 / Dialect source family, preferably with the newer resource-aware closure runner;
2. preserve that as a delta receipt rather than re-running obsolete transport experiments;
3. prepare the exact Andreas Ubuntu target receipt/handoff for the selected parser/canonicalizer package;
4. only after target adjudication may WP02 move from OPEN; WP03 research may remain shadow/non-promoting while the sequential gate is open.

Training remains `NOT_AUTHORIZED`.

Authority invariant remains: `model output != execution authority`.

# SPAWN FINAL REPORT — ClayCode Bootstrap Compiler/Tool Staging

Run: `20260809T1813p0700-claycode-bootstrap-tool-staging`  
Trigger: `spawn`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent at boot: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Origin branch: `claycode`

## 1. Stochastic selection and novelty control

The canonical spawn distribution in `research_entity/global/SPAWN_RESEARCH_WEIGHTS.json` was sampled with Python `secrets.SystemRandom` / OS CSPRNG.

Branch draw: `3703 / 10000` -> `claycode` (interval 0-4999, 50% probability).

Recent commit/run archaeology then rejected fresh duplicates including:

- Ubuntu foreign-code effect closure;
- ClayCode async replay;
- FRANK loop evaluator/lowering;
- generic loop lowering;
- strict LALR conflict localization.

Four current-stage candidate microdirections remained. A second `SystemRandom.choice` selected:

**C4 — Bootstrap Compiler/Tool Staging**

Research question:

> Can ClayCode satisfy APP-06 and create a later self-host path through a small staged bootstrap, while keeping semantic correctness, reproducibility and compiler-trust evidence separate and avoiding premature full-self-host scope or new language semantics?

Random selection is provenance only, never evidence weight.

## 2. Why this matters now

The current BASE workspace is still `NOT_PASS`; all 14 listed ClayCode work packages remain OPEN and no mandatory application exemplar is recorded as passed.

APP-06 requires a small parser/compiler/interpreter implemented using ClayCode facilities. The acceptance contract does **not** state that the production ClayCode compiler itself must already be self-hosted.

Meanwhile, the current frontend is not ready for practical self-hosting:

- the baseline D production-parser candidate is `LEADING_NOT_SELECTED`;
- it has no general function-definition statement;
- a typed `fn` integration candidate is still OPEN;
- strict LALR construction remains a preserved negative result;
- CC-WP-02 therefore remains OPEN.

This creates a scope trap: requiring a full self-hosted compiler before APP-06 would make the current BASE critical path circular and would silently strengthen the release contract without executable evidence that such strengthening is necessary.

## 3. Main finding

### 3.1 APP-06 and full self-hosting are different milestones

The current evidence supports this distinction:

**APP-06 requirement**

`host-built production ClayCode compiler/runtime -> compile Clay-authored small compiler/tool -> execute/test`

**later self-host strengthening**

`ClayCode compiler source -> compiled by prior ClayCode compiler -> rebuilt by current ClayCode compiler -> compare semantics/artifacts`

Therefore the lowest-risk BASE path is to first prove that ClayCode can author and execute a real compiler/tool, then attempt full self-hosting after the general parser/control/data/error/runtime surface is stable.

No new ClayCode semantic primitive is justified by this run.

### 3.2 Three evidence dimensions must remain separate

The executable probe and external evidence converge on a second constraint:

1. **semantic correctness/equivalence** — does the compiled tool implement the intended meaning?;
2. **build reproducibility** — does the same declared build input/environment produce the same artifact?;
3. **compiler/bootstrap trust diversity** — can a different compiler/toolchain route independently test the source-to-binary claim or detect trusting-trust-class compromise under explicit assumptions?

A single hash cannot soundly stand for all three.

## 4. External research

### GCC bootstrap

Official GCC build documentation describes a native 3-stage bootstrap and a comparison of stage2 and stage3 compiler outputs. This is evidence that compiler self-hosting is naturally staged and that later-stage comparison is a distinct test step.

Source: `https://gcc.gnu.org/install/build.html`

### Rust bootstrap

The Rust compiler development guide explicitly separates:

- Stage 0: precompiled compiler/library;
- Stage 1: current source built by the earlier compiler;
- Stage 2: current compiler rebuilt with the in-tree compiler;
- Stage 3: optional same-result test.

This supports the engineering pattern of separating seed, current compiler, self-built compiler and same-result verification rather than demanding one monolithic self-host event.

Source: `https://rustc-dev-guide.rust-lang.org/building/bootstrapping/what-bootstrapping-does.html`

### Reproducible Builds

Reproducible Builds documentation treats deterministic transformation and the definition/recording of the build environment as separate requirements. Build paths are a known source of output variation, and prefix-map mechanisms exist to normalize embedded build-path information.

Sources:

- `https://reproducible-builds.org/docs/deterministic-build-systems/`
- `https://reproducible-builds.org/docs/build-path/`
- `https://reproducible-builds.org/specs/build-path-prefix-map/`

### Diverse Double-Compiling

David A. Wheeler's peer-reviewed DDC work addresses the trusting-trust problem by using a second trusted/diverse compiler path under explicit assumptions. This is not the same test as ordinary self-rebuild identity.

Source: `https://www.acsac.org/2005/abstracts/47.html`

Transfer boundary: none of these external systems proves the optimal ClayCode staging graph. They establish that staged bootstrapping, reproducibility and diverse compiler trust are established, separable engineering concerns.

## 5. Executable discriminator

Artifact:

- `bootstrap_stage_probe.py`
- local executed script SHA256: `254b791dfe1534d29e511a0f8e1b4d444291a1c33cb3b48f6129d32ba9d9f9e5`
- execution receipt: `EXECUTION_RECEIPT.json`

Evidence class:

`LOCAL_ISOLATED_LINUX_EXECUTION_NOT_TARGET_UBUNTU_ACCEPTANCE`

Observed toolchain:

- GCC 14.2.0 (Debian build);
- Clang 17.0.0;
- Python 3.13.5.

### Test A — same source, same compiler, different directories

The same small arithmetic C tool was compiled with GCC in two different directories.

Observed stripped binary hashes were identical:

`a6a13a8fcf5e706450551a98d2b2f8cd809fb6460af8db34ebb7bc69e817d03c`

Result: ordinary directory variation did not affect this source/toolchain case.

### Test B — path-sensitive build

A second source emitted `__FILE__`.

Two builds from different directories produced different binary hashes:

- `7f6d335e9b3250f1dda2ff8cf55deda4cbd515eaee94398268c17c0657ad3c93`
- `20a11420ad41f805f33f754aad6c2cb219674343529d13507c905d6a521bdd28`

Observed runtime strings contained the two different temporary build paths.

Result: equal source semantics did not imply byte-identical artifacts when build-path data leaked into output.

### Test C — path normalization

The same source was rebuilt with GCC `-ffile-prefix-map=<build-root>=/src`.

Both normalized binaries had the same hash:

`f79424af59cbf27f621d37abdc452f06d45904dd085c06ca73307fbba13ccf0f`

and both emitted `/src/path.c`.

Result: explicit environment/path normalization restored byte identity for the demonstrated source of nondeterminism.

### Test D — diverse compilers

The arithmetic microtool was compiled independently with GCC and Clang.

Binary equality: **false**.

Clang artifact SHA256:

`82bd9db4e6a1e0ef07f022f5d564a2bbc10c769e2e4af112eb973e481e428d5b`

A deterministic 5,000-case arithmetic differential corpus (seed `202608091813`) produced:

- cases: 5,000;
- semantic output mismatches: **0**.

Result: different binaries can agree on bounded observable semantics; binary identity and semantic agreement are distinct receipts.

## 6. Candidate ClayCode staging architecture

The run proposes this implementation sequence; it does not promote it to frozen architecture:

### Stage0 — host seed

Pinned Ubuntu host toolchain/runtime sufficient to build/run the first production ClayCode compiler.

Record at least:

- host compiler/interpreter/runtime versions/hashes;
- parser-generator dependency version/hash where used;
- backend/linker versions;
- build configuration/environment contract.

### Stage1 — production ClayCode compiler/runtime

The first production compiler/runtime capable of executing current BASE proofs.

This stage may be host-authored/host-built. That is not a semantic failure as long as the semantic and translation-validation contracts are explicit and tested.

### Stage1C — APP-06 Clay-authored compiler/tool

Implement a small real parser/compiler/interpreter **in admitted ClayCode** and compile/run it with Stage1.

This is the direct current APP-06 discriminator.

It should test the actual ClayCode facilities needed for compiler construction without pretending to be the entire production compiler.

### Stage2 — partial/full self-host

Only after the production frontend and generic function/control/data/string/collection/error/runtime surface are stable, move enough of the ClayCode compiler into ClayCode to compile the current compiler source with the prior ClayCode compiler.

### Stage3 — same-result rebuild

Rebuild the same compiler source with the Stage2/current compiler and compare the declared semantic and artifact outputs under a normalized build environment.

A Stage2/Stage3 mismatch is a serious diagnostic, but a match is not automatically a proof of semantic correctness or absence of trusting-trust attacks.

### Later hardening — diversity/DDC

Where security value justifies cost, use a separately rooted compiler/backend/interpreter path and DDC-style reasoning under explicit assumptions. Do not claim independence if both routes share the same compiler frontend, generated source, oracle or build ancestry.

## 7. Identity/receipt model

Candidate receipt separation:

`ProgramSemanticId`

`CompilerRuntimeId`

`BootstrapStageId`

`BuildEnvironmentId`

`GeneratedArtifactHash`

`ExecutionSemanticReceipt`

`ReproducibilityReceipt`

`DiverseCompilerReceipt`

The compiler/build pipeline should not use one artifact hash as a surrogate for all of these concepts.

## 8. Negative results and limits

1. Current D is not yet a self-host-ready production frontend.
2. Strict LALR construction remains negative; this run does not bypass that blocker.
3. The local experiment did not run the ClayCode compiler because a target production compiler path is not yet available on this hosted surface.
4. The hosted Linux environment is not Andreas' Ubuntu developer system; no BASE application PASS is claimed.
5. 0/5,000 GCC-vs-Clang mismatches is bounded semantic evidence only.
6. Binary reproducibility alone is not compiler correctness.
7. Self-host equality alone is not trusting-trust closure.
8. DDC has assumptions and is a later hardening mechanism, not an automatic BASE gate.
9. No Frank, GWT, emergence or consciousness claim is promoted by compiler bootstrapping.

## 9. Branch feedback

`BRANCH_FEEDBACK_MANIFEST.json` records explicit mesh feedback.

Main deltas:

- `clayresearch`: **NEW_CONSTRAINT** — separate language semantics from build/bootstrap trust dimensions;
- `claycode`: **NEW_CONSTRAINT** — APP-06 first, full self-host later unless the acceptance contract is explicitly strengthened;
- `harness`: **NEW_CONSTRAINT** — later differential tests must pin compiler/build identity separately from program semantics;
- `unifieddb`: **NEW_HYPOTHESIS** — durable bootstrap/build lineage may belong in semantic/replay state, without implying physical store merger;
- `frank`, `gwt`, `emergenz`, `hyperposition`, `claygraph`: **NO_CHANGE** beyond compatibility/lineage cautions.

## 10. Exact next discriminating action

Dynamic work created:

`WORK-SPAWN-CLAYCODE-BOOTSTRAP-TOOL-20260809`

Event:

`research_entity/state/work/events/20260809T1813p0700_spawn_claycode_bootstrap_tool_work_create.json`

Current status: `BLOCKED`.

Dependencies intentionally preserve the real critical path:

1. resolve/select the current strict parser/frontend strategy;
2. admit/execute the generic function/control/data/error facilities needed by the chosen compiler microtool;
3. establish a production Stage1 ClayCode compiler/runtime path;
4. then execute APP-06 on Andreas' Ubuntu developer system;
5. only after that decide whether Stage2/Stage3 self-hosting is ready.

No background execution is claimed.

## 11. Durable artifact/commit map

- `SPAWN_RECEIPT.json` — commit `334f742b2803c2a5e492af2604aa1b2fa5c99976`
- `INTERCONNECT_MANIFEST.json` — commit `b07addbf0fd5673e2ea2991cb711da4d4a9be590`
- `HYPOTHESES.json` — commit `9a00248e6589907275135824396142aeec1d7bcc`
- `EVIDENCE_MANIFEST.json` — commit `6cdb56cd10723588258a9b8745ece1600a49fce8`
- `bootstrap_stage_probe.py` — commit `163e8ac9141b7a794631178c0874f10d1dcbec65`
- `EXECUTION_RECEIPT.json` — commit `725dc14442e92a113e7f6c3344725c90ba2df5ad`
- `BRANCH_FEEDBACK_MANIFEST.json` — commit `6fbd565f723149629e793e92d9921150b9c92577`
- dynamic work event — commit `1ea6b5078907d5b6d8df853438d37c083655e7b3`

## 12. Decision

`RESEARCH_DELTA = YES`

`SCIENTIFIC_PROMOTION = NONE`

`CLAYCODE_CORE_SEMANTIC_CHANGE = NO`

`APP06_FULL_SELF_HOST_REQUIREMENT = NO_UNLESS_CONTRACT_EXPLICITLY_STRENGTHENED`

`BOOTSTRAP_STAGING_CANDIDATE = OPEN_SUPPORTED_WORKING_HYPOTHESIS`

`BASE_GATE = NOT_PASS`

The strongest current conclusion is:

> **ClayCode should prove a real Clay-authored compiler/tool before making full self-hosting a BASE obligation, and its bootstrap pipeline should preserve semantic correctness, reproducibility and compiler-trust diversity as separate evidence channels.**

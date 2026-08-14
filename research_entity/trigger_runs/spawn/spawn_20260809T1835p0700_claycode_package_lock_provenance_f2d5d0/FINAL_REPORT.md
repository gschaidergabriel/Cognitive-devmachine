# SPAWN FINAL REPORT — ClayCode Package Resolution, Lock Identity, Trust and Provenance

Run: `spawn_20260809T1835p0700_claycode_package_lock_provenance_f2d5d0`  
Trigger: `spawn`  
Origin branch: `claycode`  
Actor: `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Depth mode: owner-requested extreme/deep + web research + explicit hypothesis formation

## Executive result

The stochastic branch draw selected **ClayCode**. A novelty-filtered second draw selected a previously uncovered BASE boundary:

> **How should ClayCode resolve, lock, authenticate, canonicalize and receipt module/package dependencies so the same declared program cannot silently drift across time, registry state, resolver implementation, target/features or source mutation, while keeping semantic identity, supply-chain trust, build provenance and execution authority distinct?**

The strongest working conclusion is not “add a lockfile hash.” It is:

> **Dependency locking is a typed chain of identity decisions, not one identity. ClayCode should separate request intent, resolver provenance, exact digest-bound dependency graph identity, target/feature build projection, mutable trust/freshness admissibility, build provenance, artifact bytes and runtime capability authority.**

Compact law:

```text
package request/intent
  -> receipted resolver
  -> exact digest-bound semantic dependency graph
  -> target/feature build projection
  -> compiler/runtime build provenance
  -> artifact hash
  -> execution receipt

trust/freshness gates whether graph/artifact use is admissible
but does not rewrite immutable historical semantic/artifact identity

dependency/effect declaration expresses a requirement
but never mints capability authority
```

This run does **not** justify new ClayCode core syntax or a new core semantic primitive. The proposed mechanism belongs first in the existing module/package/toolchain/canonicalization/validation/receipt layers. Under the BASE acceptance law, a core-language change remains forbidden unless production ClayCode execution produces an executable semantic counterexample.

No BASE work package is marked complete. No scientific promotion is made.

---

## 1. Stochastic provenance and novelty control

The canonical spawn distribution was sampled with OS CSPRNG.

- branch draw: **29 / 100**;
- selected branch: **ClayCode**;
- canonical probability: **50%**.

Six current-stage microdirections survived an initial duplicate screen:

1. semantic/content-addressed incremental build-cache identity;
2. cross-backend numeric semantics;
3. stable diagnostic identity;
4. effect-preserving optimization barriers;
5. package-resolution lock/provenance semantics;
6. incremental-vs-full rebuild equivalence.

The second OS-CSPRNG draw was **5 / 6**, selecting package resolution / lock / provenance.

Recent finalized/current spawn work was audited through recent GitHub commits. Material recent directions included HTTP+SQLite, bootstrap compiler/tool staging, deterministic module initialization, Unicode canonical boundaries, atomic CAS/ABA, async replay, foreign effect closure, callable identity, FRANK loop lowering, adaptive recurrence, Harness visual action closure and ClayGraph reversal-aware binding.

The selected direction overlaps the bootstrap run only at the broad word “reproducibility.” It asks a different causal question: **what exact dependency object is being built before build-stage reproducibility can even be evaluated?** The bootstrap run separated semantic correctness, reproducible build output and compiler-trust diversity. This run separates dependency semantic identity, resolver provenance, trust/freshness, build projection and authority.

Randomness is selection provenance only. It carries zero evidential weight.

---

## 2. Why this matters now for BASE

The current ClayCode BASE workspace remains `NOT_PASS`, with all 14 listed work packages open. The acceptance contract explicitly requires:

- a module/package format;
- deterministic canonicalization and semantic hashes/receipts;
- compiler/lowering and runtime ABI;
- typed FFI/capability/effect boundaries;
- a build/test toolchain;
- reproducible executable application receipts.

The current development law is `less change, more compile`: first freeze and realize existing semantics; change the language only if a real program/compiler counterexample forces it.

Package resolution therefore sits directly on the BASE critical path. If a package request such as a version range can resolve to different exact bytes on different days, then compiler/replay/Harness comparisons can differ before ClayCode semantics even execute. If all dependency-related state is instead collapsed into one giant hash, policy or builder changes can falsely look like changes to the program's dependency semantics.

The question is thus not only supply-chain security. It is also **semantic identity hygiene for reproducible causal experiments**.

---

## 3. External primary-source triangulation

This run deliberately used official/primary specifications rather than blog summaries. The external systems do not prove an optimal ClayCode design; they establish distinct engineering choices and recurring boundary separations.

### 3.1 Cargo / Rust — request versus exact resolution

Cargo resolves manifest dependency requirements into exact selected versions and records them in `Cargo.lock`; locked/frozen modes prevent implicit lock changes. This is direct precedent for separating a dependency request from a concrete resolution result.

Source: https://doc.rust-lang.org/cargo/reference/resolver.html

### 3.2 Go Modules — resolver policy plus content authentication

Go's module system defines Minimal Version Selection as a resolver policy. `go.sum` records cryptographic hashes for downloaded module content, while the checksum database adds a transparency/consistency mechanism. This shows that exact version selection and content identity/authentication are separate concerns.

Source: https://go.dev/ref/mod

### 3.3 PyPA `pylock.toml` — commits, hashes and environment-conditioned selection

The current PyPA lock specification can record environment markers, exact VCS commit IDs, archive/wheel hashes and attestation identities. That is materially richer than a list of package names and versions and supports treating environment-conditioned selection as part of the concrete install/build projection.

Source: https://packaging.python.org/en/latest/specifications/pylock-toml/

### 3.4 npm — exact tree plus resolved/integrity data

`package-lock.json` describes the exact dependency tree and records origin/integrity information; Git dependencies can bind commit identity. `npm ci` treats a lock mismatch as an error rather than rewriting the lock as a side effect. This again separates declared package intent from a frozen concrete tree.

Sources:

- https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json/
- https://docs.npmjs.com/cli/v11/commands/npm-ci/

### 3.5 TUF — repository snapshot/freshness is mutable trust state

TUF explicitly separates repository snapshot consistency from timestamp/freshness and provides rollback/freeze protections. This is a key clue for ClayCode: an already identified artifact can retain its byte/content identity while a later trust/freshness state makes its use inadmissible.

Sources:

- https://theupdateframework.io/docs/metadata/
- https://theupdateframework.io/docs/security/

### 3.6 SLSA provenance — resolved inputs differ from builder/run identity

SLSA v1.2 build provenance separates `buildDefinition` from `runDetails`; resolved dependencies can be identified by URI/digest while builder identity is represented separately. This strongly supports not using one opaque hash as a surrogate for dependency semantics, builder identity and build execution history simultaneously.

Source: https://slsa.dev/spec/v1.2/build-provenance

### 3.7 Bazel — resolution inputs, platform-dependent extensions and mutable yank state

Bazel's lockfile can bind module-resolution/extension results and hashes of registry inputs. Its module-extension machinery can have OS/architecture-dependent evaluation, and yanked-version information is treated as mutable state rather than simply identical to package content identity.

Source: https://bazel.build/external/lockfile

### 3.8 Nix — graph-shaped transitive locking

Nix flake locks are graph-shaped and can bind locked revisions/content hashes transitively. This supports the idea that a package lock is fundamentally a **resolved dependency graph**, not a flat list.

Source: https://releases.nixos.org/nix/nix-2.13.5/manual/command-ref/new-cli/nix3-flake.html

### 3.9 Gradle — reproducible selection versus integrity/authenticity

Gradle's dependency locking is aimed at preventing dynamic dependency selections from silently changing over time. Dependency verification separately supports checksums/signatures. Its own documentation warns, in effect, that generating verification metadata from an already compromised resolution cannot magically create trust. Locking and trust are therefore different evidence dimensions.

Sources:

- https://docs.gradle.org/current/userguide/dependency_locking.html
- https://docs.gradle.org/current/userguide/dependency_verification.html

### External synthesis boundary

These systems differ materially in resolver algorithms, trust models, metadata, target handling and lock format. Their convergence supports a **problem decomposition**, not a copy-paste ClayCode package manager.

The external evidence supports at least these distinctions:

`request/constraint != exact resolution != content identity != target projection != trust/freshness != builder/run provenance`.

It does not independently establish the exact Clay record schema proposed below.

---

## 4. Derived ClayCode identity architecture

### Plane 0 — `PackageRequestId`

This identifies the package request/intent:

- logical package coordinate;
- version/revision constraint;
- requested feature set;
- source policy where relevant.

A request is not yet an executable dependency graph.

### Plane 1 — `ResolutionReceipt`

This records how the request became an exact graph:

- request ID;
- resolver algorithm/policy/version;
- registry/repository input digests;
- negative lookup receipts where needed for reproducible reasoning;
- final `ResolvedGraphId`.

This plane is provenance for the resolution process.

### Plane 2 — `ResolvedGraphId`

This is the proposed immutable semantic identity of the exact resolved dependency graph. It binds:

- logical package coordinate / namespace / authority;
- exact version or revision;
- verified content digest;
- semantic dependency edges;
- semantic package metadata where not derivable from content.

A crucial distinction emerged here:

> **Logical source namespace is not necessarily the same thing as fetch location.**

If `registry-A::foo@1.2.0` and `registry-B::foo@1.2.0` are different logical package authorities, that distinction may legitimately belong in semantic identity even if bytes happen to match.

By contrast, downloading the same logically identified package and verified digest through mirror A versus mirror B should normally change a `FetchReceipt`, not the semantic dependency graph.

This distinction is a working hypothesis and must be tested against real Clay package namespace semantics.

### Plane 3 — `BuildProjectionId`

An exact superset graph may still activate different meaning under different targets/features. Therefore build projection binds:

- `ResolvedGraphId`;
- target triple;
- enabled features/groups;
- active markers/cfg conditions;
- semantic build flags;
- active dependency projection.

This is the best current candidate for the semantic compiler/build-cache input identity.

### Plane 4 — `SupplyChainTrustReceipt`

This is mutable admissibility state over an immutable identified graph:

- trust policy ID;
- trust root ID;
- repository snapshot/freshness epoch;
- attestations/signatures/checks;
- yanked/revoked state;
- `ACCEPT | WARN | REJECT` verdict.

Key law:

`trust_change may_change admissibility`  
`trust_change != rewrite historical ResolvedGraphId`

Otherwise a later revocation would make it impossible to state precisely that “the same artifact/graph we built yesterday is now disallowed today.”

### Plane 5 — `BuildProvenanceReceipt`

This binds the actual build process:

- `BuildProjectionId`;
- ClayCode compiler/runtime identity;
- backend/toolchain identity;
- builder identity;
- resolved dependency digests;
- invocation/build ID;
- output artifact digest.

Builder changes can alter provenance even when the dependency semantic projection is identical.

### Plane 6 — `ArtifactHash`

This is the identity of actual output bytes. It is not automatically equivalent to program semantics, as the prior bootstrap spawn already showed with path-dependent versus normalized builds.

### Plane 7 — `CapabilityAuthority`

This remains completely separate.

A package may declare it needs `net`, filesystem, process, GPU or system effects. That declaration describes a requirement/effect intent. It must **never** mint the external capability.

Hard rule:

`package_present != authority`  
`package_declared_effect != authority`  
`effect execution requires external explicit grant`

This is especially important for a future Clay-native FRANK because package metadata must not become a route around the independent effect gateway.

---

## 5. Executable hosted discriminator

Artifact: `package_lock_probe.py`  
SHA-256: `b0afc8241ce7932b564d6768f24e648812142e3f734c003e01c31e4b367d2ba8`  
Execution receipt: `EXECUTION_RECEIPT.json`  
Local receipt SHA-256: `cd47b0bb8a472cdf6d4c13fc20ec58724d70c0bdb7a6345679c6a9c643d5cece`

Evidence class:

`HOSTED_SYNTHETIC_PROXY_NOT_PRODUCTION_CLAYCODE`

This is a **constructed falsification suite**. The trial counts are not prevalence estimates. Many cases deliberately guarantee a discriminating condition, e.g. registry growth or same-version payload mutation.

### Test A — resolver-policy ambiguity

Two deliberately different policies — minimum-compatible and maximum-compatible — were applied to generated version sets containing at least two candidates.

- different exact selection: **10,000 / 10,000**.

Meaning: a manifest/range alone does not identify the exact dependency graph.

This does not mean real Cargo/Go/etc. randomly choose policies; it shows that resolver policy is an input to resolution semantics and should be receipted.

### Test B — registry growth

A version-range request was resolved, then the registry gained a newer compatible version.

- unlocked selection drift: **10,000 / 10,000**;
- locked selection drift: **0 / 10,000**.

Meaning: frozen exact resolution prevents time/registry growth from silently changing the chosen graph in the constructed scenario.

### Test C — same version, changed payload

Name/version/logical source were held constant while content bytes changed.

- version-only identity collisions: **10,000 / 10,000**;
- digest guard detected mutation: **10,000 / 10,000**.

Meaning: exact version alone is not a sufficient content identity under a threat/model where version-to-bytes immutability is not absolutely guaranteed.

### Test D — canonical ordering

Node/edge discovery order was shuffled after constructing random dependency DAGs.

- canonical graph hash mismatches: **0 / 10,000**.

Meaning: package discovery/filesystem/parser order need not become semantic identity if canonicalization sorts semantic nodes/edges.

### Test E — target-conditioned active dependencies

The same resolved superset contained Linux and Windows dependencies. The active projection differed.

- naive superset graph identity collisions: **10,000 / 10,000**;
- `BuildProjectionId` detected target change: **10,000 / 10,000**.

Meaning: the exact graph alone may not identify the active build meaning when target/features/markers select different subgraphs.

### Test F — mutable trust/yank state

The graph/content was held constant while the trust snapshot changed from accepted to rejected/yanked.

- semantic graph stable: **10,000 / 10,000**;
- trust receipt changed: **10,000 / 10,000**.

Meaning: the model can truthfully represent “same graph, different current admissibility.”

### Test G — authority lesion/rescue

A dependency declared a network effect.

- deliberately unsafe design `dependency declaration => authority` would allow: **10,000 / 10,000**;
- guarded design without external grant denied: **10,000 / 10,000**;
- explicit external grant allowed: **10,000 / 10,000**.

This is an encoded architecture oracle, not independent proof. It exists to prevent future package-manager code from accidentally merging requirement declaration and capability minting.

### Test H — resolver provenance with equal graph

Two resolver identities were assigned to a fixture whose exact graph was held identical.

- same graph + distinct resolver receipts: **10,000 / 10,000**.

Meaning: resolver identity can remain auditable without forcing downstream semantic dependency identity to differ when the resolved semantic graph is exactly the same.

---

## 6. Factorial identity-boundary test

A second 5,000-case-per-mutation factorial compared three identity schemes.

### Semantic mutation classes

Six classes were declared semantic for the candidate identity boundary:

1. exact package version/revision;
2. logical source namespace/authority;
3. content digest;
4. dependency edge set;
5. target;
6. enabled features.

Total: **30,000** semantic mutations.

### Nonsemantic-for-this-identity classes

Five classes were treated as provenance/policy/intent rather than the already resolved build semantic projection:

1. resolver identity, if exact graph remains equal;
2. current trust/yank state;
3. builder identity;
4. manifest range change that still resolves to the exact same graph;
5. fetch mirror locator with same logical coordinate and verified content.

Total: **25,000** nonsemantic changes.

### Scheme 1 — version-only

- semantic changes detected: **5,000 / 30,000**;
- nonsemantic stability: **25,000 / 25,000**.

It is stable but dramatically under-sensitive: it misses content, source namespace, edges, target and feature changes.

### Scheme 2 — giant hash of everything

- semantic changes detected: **30,000 / 30,000**;
- nonsemantic stability: **0 / 25,000**.

It is maximally sensitive but overcoupled: changing resolver label, trust state, builder, manifest range or mirror falsely rewrites the “semantic” identity in every constructed case.

### Scheme 3 — separated candidate

- semantic changes detected: **30,000 / 30,000**;
- nonsemantic stability: **25,000 / 25,000**.

This is the intended outcome because the oracle itself was designed around the proposed boundary. Therefore the perfect score **does not independently validate the boundary**. Its value is that it exposes exactly what the boundary claims and makes future production counterexamples easy to formulate.

The highest-information next step is not another synthetic run. It is production ClayCode/Ubuntu execution against real package-manager/compiler behavior.

---

## 7. Hypotheses and counterhypotheses

### H-PKG-01 — typed multi-plane dependency identity

**Working hypothesis:** ClayCode should represent package resolution/build identity as multiple linked typed receipts rather than one monolithic lock hash.

Status: supported by independent external architecture analogy plus synthetic mechanism discrimination; **not promoted**.

### H-PKG-02 — exact graph requires digest-bound package identity

**Working hypothesis:** a package node needs logical coordinate + exact version/revision + content digest, and the graph needs semantic edges.

Status: supported; real registry immutability/trust model can narrow requirements later.

### H-PKG-03 — build projection is separate

**Working hypothesis:** target/features/markers and semantic build switches need a `BuildProjectionId` above the exact resolved graph.

Status: supported by constructed counterexample and multiple external systems with environment/platform conditioned resolution/evaluation.

### H-PKG-04 — logical source namespace != mirror locator

**Working hypothesis:** logical package authority can be semantic, while a verified mirror is transport provenance.

Status: OPEN; production package namespace design must test edge cases.

### H-PKG-05 — trust/freshness is admissibility

**Working hypothesis:** trust/yank/revocation/freshness can change whether graph/artifact use is allowed without changing the identity of the historical graph/artifact itself.

Status: strongly supported as an identity-model choice; requires a hard current-policy gate to be safe.

### H-PKG-06 — resolver is provenance if exact graph agrees

**Working hypothesis:** two resolver versions/policies producing the same exact semantic graph may have different `ResolutionReceipt`s while sharing `ResolvedGraphId`.

Status: OPEN; falsified if hidden resolver-specific semantic state is not represented in graph/projection.

### H-PKG-07 — package declarations never mint authority

**Constraint:** package requirements and authority remain separated.

Status: current project architecture constraint reinforced, not a new scientific discovery.

### H-PKG-08 — semantic cache key plus separate trust gate

**New hypothesis:** a useful cache key is approximately:

`BuildProjectionId + compiler/runtime semantic identity + backend semantic identity`

Current trust/freshness should separately gate whether the cached artifact is allowed to be used.

This avoids rebuilding merely because a trust snapshot changed while still allowing policy to quarantine previously cached artifacts. It needs production tests for revocation, quarantine, stale cache and backend nondeterminism.

### Counterhypothesis C1 — manifest ranges are enough

Refuted by the constructed registry-growth/resolver-policy examples.

### Counterhypothesis C2 — exact version is enough

Refuted under same-version payload mutation by the constructed content-identity test.

### Counterhypothesis C3 — hash everything together

Refuted as an identity model in the factorial oracle because it destroys semantic stability under changes that should remain provenance/policy dimensions.

### Counterhypothesis C4 — trust state belongs inside immutable graph identity

Disfavored because it prevents clean representation of “same graph, newly disallowed.” A project could deliberately choose trust-as-semantic-input, but that would need an explicit semantic reason.

### Counterhypothesis C5 — mirror URL is semantic identity

Disfavored when logical coordinate/content are verified equal. Remains falsifiable if transport origin affects package semantics/policy in a way Clay chooses to expose semantically.

### Counterhypothesis C6 — dependency can self-grant declared effects

Rejected by current ClayCode/FRANK authority architecture.

---

## 8. Candidate ClayCode contract

The run created `CLAYCODE_PACKAGE_LOCK_PROVENANCE_CONTRACT.clay` with these principal record identities:

- `PackageCoordinate`
- `PackageRequest` / `PackageRequestId`
- `ResolvedPackageNode`
- `ResolvedPackageEdge`
- `ResolvedPackageGraph` / `ResolvedGraphId`
- `ResolutionReceipt`
- `BuildProjection` / `BuildProjectionId`
- `FetchReceipt`
- `SupplyChainTrustReceipt`
- `BuildProvenanceReceipt`

The contract encodes four especially important rules:

1. **same exact graph from different resolvers may share semantic graph identity while resolution provenance differs;**
2. **verified mirror changes do not automatically mint a new semantic package identity;**
3. **trust changes can change admissibility without rewriting `ResolvedGraphId`;**
4. **dependency presence/effect declarations never mint `CapabilityAuthority`.**

This is a working contract, not frozen language law.

---

## 9. Implications for incremental build/cache design

This package result creates a bridge to another unselected spawn candidate: semantic/content-addressed incremental builds.

A compiler cache that keys only on source file timestamps or package versions risks false reuse. A cache that hashes every current policy/provenance field risks needless invalidation and destroys semantic equivalence classes.

The present candidate suggests:

```text
semantic_cache_key = hash(
  BuildProjectionId,
  compiler_runtime_semantic_id,
  backend_semantic_id
)
```

with independent gates:

```text
current_trust_policy(all input digests/artifact provenance) must ACCEPT
capability policy for execution must GRANT required effects
```

This preserves three questions separately:

1. “Is this the same semantic build input?”
2. “May we currently trust/use these exact inputs/artifact?”
3. “May this execution perform the requested effects?”

A later optimization branch should benchmark whether this separation improves cache hit quality without weakening revocation/quarantine behavior.

---

## 10. Cross-branch feedback

### ClayCode — `NEW_HYPOTHESIS`

Implement typed package-lock/provenance records and canonical identities inside the module/package/toolchain layer first. No syntax/core-semantic promotion.

### FRANK — `NEW_CONSTRAINT`

FRANK build/replay/deployment receipts should pin `BuildProjectionId`, compiler/runtime/backend identities and output artifact hash. Current trust policy gates admissibility. Package presence cannot bypass the effect gateway.

The latest FRANK trigger explicitly treats the Harness as the executable developmental approximation of the Ubuntu/Qwen-class 4B target; exact build/dependency identity therefore becomes part of making Harness-vs-target evolution causally interpretable.

### Harness — `NEW_CONSTRAINT`

Golden traces, differential runs and replay should bind package graph/build projection/artifact/trust receipts. Otherwise a changed dependency tree can masquerade as an architecture delta.

### GWT — `NEW_CONSTRAINT`

The adaptive recurrence experiment should pin package/build/artifact identity so changed compute routing is not confounded by changed runtime dependencies.

### Emergenz — `NEW_CONSTRAINT`

Dependency/toolchain drift is a causal confound. It must be pinned or explicitly treated as an intervention before attributing behavioral changes to system coupling/emergence.

### ClayGraph — `NEW_CONSTRAINT`

Package/dependency/provenance can be represented as an exact typed graph, but provenance edges do not imply truth/activation. Mutable trust/admissibility is an overlay, not graph semantic identity.

### UnifiedDB — `NEW_HYPOTHESIS`

Persist the package request, resolution receipt, exact graph, trust state, build projection and build receipt as linked typed entities. This is a logical lineage proposal only and does not imply physical storage consolidation.

### Hyperposition — `NEW_CONSTRAINT`

Target/features are contextual build-projection variables, but this package result is not evidence for higher-order cognitive Hyperposition mechanisms.

### ClayResearch — `NEW_CONSTRAINT`

Integrated architecture research should preserve `semantic identity != trust != provenance != authority` across compilation/deployment discussions. External ecosystem convergence is supporting analogy rather than independent evidence for the exact Clay schema.

---

## 11. Governance / interconnection note

A previous spawn had detected a `clay` versus `clayresearch` naming mismatch in `tools/research_interconnect_preflight.py`.

The current source fetched in this run uses `clayresearch` throughout the explicit priority sets and compares those sets against the dynamic registry branch set. By source inspection, the earlier naming drift appears repaired.

This worker did **not** execute the repo-native preflight against a full repository checkout because the current hosted surface did not expose that checkout/tree. Instead it materialized `INTERCONNECT_MANIFEST.json` from canonical files, the current preflight source and latest peer commit search.

Therefore the correct claim is:

`CURRENT_PREFLIGHT_SOURCE_NAMING_DRIFT = NOT_OBSERVED`  
`FULL_PREFLIGHT_EXECUTION = NOT_CLAIMED`

---

## 12. Exact next discriminating experiment

Dynamic work created:

`WORK-SPAWN-CLAYCODE-PACKAGE-LOCK-UBUNTU-F2D5D0`

Target: Andreas' Ubuntu Linux developer system.

Status:

`BLOCKED_ON_CLAYCODE_PACKAGE_TOOLCHAIN_SURFACE`

The production differential should implement the minimum contract and execute at least:

1. lock generation from a range request;
2. registry growth: frozen versus unlocked behavior;
3. same-coordinate/version local-registry payload mutation -> digest failure;
4. package/edge discovery-order shuffle -> stable canonical IDs;
5. two mirrors with identical verified logical coordinate/content -> same semantic ID, different `FetchReceipt`;
6. deliberately distinct logical package source namespace -> identity test;
7. target/features/markers -> `BuildProjectionId` differential;
8. yank/revoke/freshness update -> stable graph, changed trust verdict and policy enforcement;
9. two resolver implementations yielding the same exact graph -> same graph ID, different resolution provenance;
10. declared network/system effect without grant -> denied; explicit grant -> bounded permit;
11. cache full-rebuild versus reuse under trust-only change and under true semantic projection change.

Required outputs include exact source/manifest hash, package request ID, resolver/registry receipts, graph ID, projection ID, trust receipt, compiler/runtime/backend ID, output artifact hash, execution receipt, cache hit/miss/latency and authority receipt.

The verdict must be one of:

- `CANDIDATE_SURVIVES_PRODUCTION_DIFFERENTIAL`
- `CANDIDATE_REQUIRES_TOOLCHAIN_REVISION`
- `EXECUTABLE_LANGUAGE_SEMANTIC_COUNTEREXAMPLE`

Only the third justifies reopening core language semantics.

---

## 13. Negative results and hard evidence boundaries

This run does **not** establish:

- a production ClayCode package manager;
- a final lockfile format;
- a final package namespace/registry architecture;
- production compiler-cache correctness;
- Ubuntu target correctness;
- supply-chain security certification;
- independence between FRANK and ClayCode evidence inherited from the same architecture;
- any GWT/emergence/consciousness claim;
- BASE completion.

The synthetic suite intentionally encodes the proposed identity boundary. Its perfect candidate factorial result is therefore a specification sanity check, not scientific replication.

The external systems provide independent engineering precedents but use different threat models and semantics. Their agreement should raise the priority of testing the decomposition, not promote it automatically.

---

## 14. Durable artifacts and exact commits

Run directory:

`research_entity/trigger_runs/spawn/spawn_20260809T1835p0700_claycode_package_lock_provenance_f2d5d0/`

Committed artifacts:

- `SPAWN_RECEIPT.json` — `54ba6a266b7fa6e1de0027ffee753b260803fcf8`
- `HYPOTHESES.json` — `f63ee631bff103e73fc2f40b34b7ab3b4635bc36`
- `EVIDENCE_MANIFEST.json` — `250dd97975451a20c4e814b1ad9b8fd6f6dae4d0`
- `INTERCONNECT_MANIFEST.json` — `2169b04b810656caba7eecfe99aa7334193dc8a3`
- `package_lock_probe.py` — `6daecdef440ff00691c7b42d7b948800fc8af801`
- `EXECUTION_RECEIPT.json` — `3a6f85f18c1748a64256c1b02497359c95acae9a`
- `CLAYCODE_PACKAGE_LOCK_PROVENANCE_CONTRACT.clay` — `a63d6a7a691829929b10d32fa3b74d85278fec94`
- `BRANCH_FEEDBACK_MANIFEST.json` — `f973edf8b3f5df7f32ba41d7ea442a4e6ff14078`
- `TOOL_EXECUTION_MANIFEST.json` — `3e44f01291228ff41806e3f35fb7eb37daaf5828`
- `FRANK_CLAYCODE_GOODMAN_REVIEW.json` — `f323f39ffb87891db38d170a64dc5e593be70fce`

Dynamic Ubuntu work event:

- `research_entity/state/work/events/work_create_spawn_claycode_package_lock_20260809T1835p0700_f2d5d0.json` — `3a1faee3ad479c37b8a0239c531ed4dd6c4a4cef`

---

## 15. Final decision

`RESEARCH_DELTA = COMMITTED`  
`ORIGIN_BRANCH = CLAYCODE`  
`SELECTED_MICRODIRECTION = PACKAGE_RESOLUTION_LOCK_PROVENANCE`  
`MAIN_WORKING_HYPOTHESIS = TYPED_MULTI_PLANE_DEPENDENCY_IDENTITY`  
`SEMANTIC_IDENTITY != TRUST_VERDICT != BUILD_PROVENANCE != AUTHORITY`  
`CLAYCODE_CORE_CHANGE = NO`  
`CANDIDATE_LAYER = MODULE_PACKAGE_TOOLCHAIN_CANONICALIZATION_RECEIPTS`  
`SYNTHETIC_DISCRIMINATOR = PASS_BY_ENCODED_ORACLE_NOT_PRODUCTION_EVIDENCE`  
`SCIENTIFIC_PROMOTION = NONE`  
`NEXT_DISCRIMINATOR = PRODUCTION_CLAYCODE_PACKAGE_TOOLCHAIN_ON_ANDREAS_UBUNTU`  
`BASE_GATE = NOT_PASS`

The highest-value conclusion to carry forward is:

> **ClayCode should make dependency identity explicit enough that a future FRANK/Harness result can answer four different questions without ambiguity: what exact semantic dependency graph was built, under what target/features; whether those exact inputs/artifact are currently trusted; how the artifact was produced; and what effects its execution is actually authorized to perform.**

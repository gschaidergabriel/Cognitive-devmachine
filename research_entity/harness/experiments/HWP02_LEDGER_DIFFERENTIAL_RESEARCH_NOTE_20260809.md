# FRANK H1 H-WP-02 — State-Ledger Differential Research Note

Date: 2026-08-09
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol
Authority: `RESEARCH_ENTITY --researches/builds/tests--> FRANK`; no Frank self-Harness authority
Canonical parent: `r2:04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
Epistemic status: `OPEN / DIFFERENTIAL_ONLY / PROMOTION_NONE`
Target evidence status: `NOT_YET_OBTAINED`

## 1. Why this work exists

Current FRANK H1 work contains overlapping StateLedger lineages whose meanings for "state identity" are not identical. Binding later H1/H2 components to more than one identity law risks creating false differential failures, false cache misses, stale-epoch ambiguity, or replay mismatches that look like compiler/runtime defects but are actually semantic-identity defects.

This note accompanies the ChatGPT-authored executable discriminator:

- `tools/frank_h1_state_ledger_differential.py`
- commit `767bd0a45ecbb0e716e5a009b5f1c79e5caab4b9`
- Ubuntu gate `.github/workflows/frank-h1-ledger-differential.yml`
- commit `f509430adeb54810a5268787f2c7f11fc7d1e5d7`
- draft PR `#24`

No fourth ledger implementation is proposed here.

## 2. Internal evidence fused

Three current lineages were inspected directly:

1. `research_entity/harness/reference_state_ledger.py`
   - pure current-state root plus event hash chain;
   - global epoch CAS;
   - idempotency and snapshots;
   - no typed Set/Ordered semantics and no domain-epoch surface.

2. `research_entity/harness/reference/state_ledger.py`
   - typed Set/Ordered semantics;
   - global and domain epochs;
   - semantic/execution chains;
   - its exposed `semantic_state_hash` is history/version-coupled rather than being only current semantic meaning.

3. `research_entity/harness/reference/oracle_state_ledger.py`
   - explicit three-root candidate: current semantic state, state/history version, execution/provenance trace;
   - typed collection semantics;
   - domain epochs and global CAS;
   - payload-bound idempotency checked under the write transaction;
   - replay/snapshot/tamper surfaces.

Concurrent FRANK research independently produced OPEN hypothesis `H-FRANK-3C-05`: separating `semantic_state_hash`, `state_version_hash`, and `trace_root_hash` may prevent false H1/H2 differential failures. Its counterhypothesis is that a simpler single-root ledger plus diagnostic metadata is sufficient. That independent convergence raises the information value of a shared differential but is not promotion evidence.

## 3. External primary-source research

### 3.1 Canonical identity is a protocol, not `sort_keys=True`

RFC 8785 (JSON Canonicalization Scheme) exists specifically because hashing/signing needs invariant serialization. It requires, among other things, ECMAScript-compatible number serialization and object-property ordering by UTF-16 code units.

Current Python ledger helpers use deterministic Python JSON (`sort_keys=True`, compact separators, finite-float checking). That is internally deterministic but is not by itself a cross-runtime JCS contract. A concrete portability counterexample exists:

- Python Unicode-codepoint sorting and JCS UTF-16-code-unit sorting can disagree for BMP private-use vs supplementary-plane keys.
- Python's ordinary JSON rendering of values such as `1e-6` is not the JCS/ECMAScript rendering shown by RFC 8785 examples.

Therefore a hash intended to survive Python -> Clay/native migration needs a versioned canonical-hash ABI, not an implementation-local serializer assumption.

### 3.2 Deterministic CBOR is a candidate, not an automatic answer

RFC 8949 defines deterministic CBOR restrictions: preferred/shortest encodings, no indefinite-length items, and deterministic map-key ordering by encoded bytes. It also warns that application protocols must be explicit when representation choices exist.

Implication for FRANK: deterministic CBOR could become a binary canonical-identity encoding, but only *after* FRANK's higher semantic layer defines typed Set vs Ordered normalization, integer/float admissibility, string policy, versioning and domain identity. Encoding determinism does not define semantic determinism.

### 3.3 SQLite transaction semantics support the write-lock boundary

SQLite documents WAL snapshot isolation and `SQLITE_BUSY_SNAPSHOT` when a stale reader tries to upgrade after another writer has advanced the database. `BEGIN IMMEDIATE` starts a write transaction up front and prevents a later writer from jumping ahead after the lock has been obtained.

Implication: H-WP-02's idempotency/CAS decision must be made inside the same write-locked transaction as the mutation/event commit. A pre-lock idempotency lookup is a TOCTOU surface and must be stress-tested with two independent connections.

### 3.4 SQLite JSONB must not silently become FRANK's hash ABI

SQLite's own documentation states that JSONB is an internal SQLite format, opaque to applications and not compatible with PostgreSQL JSONB. It is suitable as an SQLite-local storage optimization, not as a cross-runtime canonical wire/hash representation.

### 3.5 Compiler canonicalization and identity serialization must remain separate

MLIR's canonicalization documentation explicitly treats rewrite canonicalization as best-effort and states that there is no formally defined canonical form; correctness must not depend on the canonicalizer. In contrast, MLIR bytecode is a versioned/stable serialization surface with dialect-version upgrade hooks.

Implication for ClayCode/FRANK: optimization canonicalization may evolve; identity serialization used for state hashes, replay and H1/H2 differential equivalence must be separately versioned and stable.

### 3.6 Authority should be represented by unforgeable external handles, not model text

Wasmtime's Component Model `Resource<T>` is an instructive engineering analogue: guest-visible resource handles are not forgeable by the guest and have explicit own/borrow lifetime semantics. This supports FRANK's existing external-authority boundary: the local 4B can produce `EffectIntent`, but execution authority should be a sealed runtime capability/resource resolved outside model output.

Linux provides complementary kernel enforcement. Landlock can stack additional filesystem/network restrictions even for unprivileged processes, and current kernel documentation describes deny-by-default handled rights plus auditability. Seccomp reduces syscall surface but kernel documentation explicitly says syscall filtering alone is not a complete sandbox. A FRANK effect gateway should therefore treat capability identity, semantic validation and kernel confinement as separate layers.

### 3.7 Qwen 3.5 4B changes what the outer loop should assume

The official Qwen3.5-4B model card/config describes 32 language layers with an 8x repeated hybrid pattern of three Gated DeltaNet/FFN layers followed by one full-attention/FFN layer, plus a large native context. The outer FRANK loop therefore should not be designed as though the model were a plain stateless full-attention block.

Recent 2026 looped-model research strengthens a trajectory/readout distinction:

- Adaptive Depth in Looped Transformers reports that learned halting can entangle trajectory formation with exit readout and that post-hoc confidence readouts can match/outperform learned gates on studied setups.
- Fixed-Point Reasoners studies convergence-based halting but also identifies deep-loop signal-propagation/stability issues.
- Recurrent Transformer and Hyperloop work show recurrence can trade parameters/depth/memory in some architectures, but these results are not direct proof for Qwen3.5-4B or FRANK.

Implication: FRANK's outer recurrence controller should be evaluated as a separate trajectory/readout/control layer with estimator identity, uncertainty, freshness, budgets, rollback and fixed/event-driven null baselines rather than assuming "more looping = more reasoning".

## 4. Hypothesis matrix

### H1 — Three identities are semantically useful

Claim: FRANK H1 should distinguish:

`semantic_state_hash = identity(current semantic meaning)`

`state_version_hash = identity(current semantic meaning + version/history/epoch contract)`

`trace_root_hash = identity(version + execution/provenance lineage)`

Prediction: semantically equivalent states reached by different valid histories compare equal at semantic-state level while remaining distinguishable for replay/audit.

Counterhypothesis: one history-coupled root plus metadata is sufficient and cheaper.

Falsifier: representative H1/H2 differential, caching, re-entry and recovery workloads show no useful discriminator needing three roots, or three-root bookkeeping causes unacceptable complexity/cost.

### H2 — Set and Ordered require different normalization laws

Prediction: typed Set insertion order and duplicates do not affect semantic identity; typed Ordered permutation does.

Counterhypothesis: collection semantics belongs above the ledger and the ledger should hash opaque values only.

Falsifier: higher-layer ownership yields cleaner and equally reproducible H1/H2 behavior without semantic ambiguity at the ledger boundary.

### H3 — Idempotency must be payload-bound and lock-bound

Prediction: two concurrent writers with the same idempotency identity and identical semantic payload converge to one event/transition; the same idempotency identity with different semantic payload fails closed.

Counterhypothesis: pre-lock lookup plus database uniqueness is sufficient.

Falsifier: target-host stress demonstrates equivalent correctness, diagnostics and failure semantics without a lock-bound lookup.

### H4 — Versioned canonical-hash ABI is a prerequisite for Python -> Clay/native migration

Prediction: implementation-local JSON hashing creates cross-runtime disagreements under Unicode/number edge cases even when semantic values are intended to be equal.

Counterhypothesis: FRANK can constrain values enough that the current Python serializer is a sufficient normative format.

Falsifier: a formally specified restricted domain plus differential implementations prove byte-identical hashing across Python and Clay/native for the entire admitted state domain.

### H5 — Storage encoding must not define semantic identity

Prediction: SQLite JSONB or other persistence encodings can change/optimize independently while semantic hashes remain stable.

Counterhypothesis: using one physical encoding for persistence and hashing reduces complexity without harming portability.

Falsifier: multi-runtime/migration tests prove that one physical format provides the required stable ABI and remains independently recoverable/versioned.

## 5. Executable discriminator

The self-authored differential runner applies one shared fixture family to all three lineages:

1. same semantic state reached by different histories;
2. typed Set permutation invariance;
3. typed Ordered permutation sensitivity;
4. execution/provenance changes trace but not semantic state;
5. stale global epoch fails closed;
6. payload-bound idempotency;
7. two concurrent same-idempotency writers converge without duplicate transition;
8. injected event-insert failure rolls back atomically;
9. domain epochs advance only for touched domains where supported;
10. replay/recovery reconstructs identity;
11. snapshot tampering is rejected.

The runner does not select or promote a ledger. `--strict-oracle` only makes the candidate oracle's own non-PASS check produce a non-zero process exit so CI can function as a candidate gate.

## 6. Validation actually obtained

### PASS

- ChatGPT-authored runner was syntactically compiled locally with Python `py_compile` before repository write.
- GitHub write and reread surfaces are available; branch and draft PR were created successfully.

### BLOCKED / negative infrastructure evidence

- GitHub Actions run `FRANK H1 H-WP-02 Ledger Differential` failed before the connector exposed any executed step; rerunning the specific job produced the same result: zero observable steps, no retrievable logs and no receipt artifact.
- The same PR head also showed immediate failures for the repository's Research Entity Verify and Identity Guard jobs, so this cannot currently be attributed specifically to the Python differential.
- Independent container `git clone` validation was attempted but outbound DNS could not resolve `github.com`.
- Raw unauthenticated download is unavailable for this connector/private-access path.

Therefore **no semantic PASS/FAIL result for the three ledgers is claimed by this note**.

## 7. Re-fusion

The build does not justify selecting the oracle. It does, however, sharpen the H-WP-02 decision:

1. H1 identity semantics are now an executable question rather than prose.
2. Independent concurrent FRANK research converged on the same three-root hypothesis.
3. A new cross-runtime canonical-hash ABI blocker was exposed by external standards research.
4. The highest-value next evidence is not another ledger implementation; it is successful execution of this shared differential on the owner-target Ubuntu host or an equivalent repository runner with full logs.
5. Only after that result should H1 bind downstream Golden Trace, ActiveAssembly, WorkspaceEpisode, effect/outcome and H2 differential identity to one ledger contract.

## 8. Architecture candidate after re-fusion

Candidate only:

```text
SemanticValueNormalizer_vN
    -> CanonicalHashABI_vN
    -> semantic_state_hash

semantic_state_hash
+ global_epoch
+ domain_epochs
+ semantic_event_chain
    -> state_version_hash

state_version_hash
+ execution/provenance chain
    -> trace_root_hash
```

Required properties:

- semantic equality independent of irrelevant history;
- version identity sensitive to authoritative transition history/epoch;
- trace identity sensitive to execution/provenance;
- explicit canonical ABI version;
- replay reconstructibility;
- stale-write rejection;
- payload-bound idempotency under write lock;
- no model-generated execution authority;
- persistence/storage encoding replaceable without silently changing semantic identity.

## 9. Next discriminating experiments

Priority order:

1. Execute `tools/frank_h1_state_ledger_differential.py --strict-oracle` on Andreas' target Ubuntu environment; preserve full receipt and SQLite/Python versions.
2. Add cross-runtime canonical-hash corpus covering Unicode supplementary-plane keys, float boundaries, signed zero, large integers, Set/Ordered nesting and malformed/non-finite values.
3. Implement the same canonical corpus in the Clay/native H2 path and require byte/hash equality before using state hashes as H1/H2 differential IDs.
4. Run integrated Golden Trace fault injection across StateLedger -> ActiveAssembly -> WorkspaceEpisode -> EffectIntent/gateway -> outcome/re-entry using shared epoch/version references.
5. Compare three-root vs simpler single-root+metadata on storage cost, lookup cost, recovery time, differential false-positive rate and debugging localization.

## 10. Source classes

Primary standards/docs:
- RFC 8785 — JSON Canonicalization Scheme.
- RFC 8949 — CBOR deterministic encoding.
- SQLite official isolation, transaction and JSONB documentation.
- Linux kernel Landlock and seccomp userspace API documentation.
- MLIR official canonicalization and bytecode-format documentation.
- Wasmtime official Component Model resource documentation.
- Qwen official Qwen3.5-4B model card/config.

Research papers/preprints:
- Adaptive Depth in Looped Transformers (arXiv:2607.20519).
- Fixed-Point Reasoners (arXiv:2606.18206).
- The Recurrent Transformer (arXiv:2604.21215).
- Hyperloop Transformers (arXiv:2604.21254).

Evidence-class rule: standards/docs constrain engineering contracts; preprints generate/triangulate hypotheses; neither source class substitutes for target FRANK measurements.

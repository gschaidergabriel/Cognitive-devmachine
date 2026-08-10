# self.root Executable Unified Database Image (EUDI) — Provisional Research Directive

**Status:** PROVISIONAL_RESEARCH_DIRECTIVE / HYPOTHESIS_FAMILY / NOT_ARCHITECTURE_FREEZE / NOT_RELEASE_REQUIREMENT  
**Effective:** 2026-08-10  
**Requested by:** project owner  
**Research entity:** Clay  
**Target:** `self.root` / human-surface `Frank` v0.1  
**Candidate physical artifact:** `self.root.udb`  
**Concept label:** **EUDI — Executable Unified Database Image**  
**Precedence:** subordinate to `FRANK_V0_1_ONLY_PROGRAM_DIRECTIVE.md`, `SELF_ROOT_V0_1_FINISHED_ACCEPTANCE_CONTRACT.md`, current identity/authority/security contracts, and any newer owner-fixed directive.

---

## 0. Directive meaning

Clay and all workers SHALL treat EUDI as a serious architecture candidate to be researched, falsified, adapted and measured against the current Frank v0.1 target.

This directive does **not** declare that Frank v0.1 must be one physical file. It declares a hypothesis worth executable study:

> A single authoritative persistent image may be able to contain the executable bootstrap/runtime, ClayCode cognitive runtime, final LLM/LoRA weights, immutable manifests and the canonical mutable UnifiedDB state while preserving strict logical separation, crash consistency, model mmap efficiency, security boundaries, reproducible identity and state-lineage continuity.

The candidate only graduates into the accepted Frank v0.1 architecture if it beats or matches a split-layout control under direct target-VPS measurements and does not weaken security, recovery, correctness or causal behavior.

The project SHALL NOT claim scientific novelty merely because an executable and mutable database are stored in one file. Exact prior art exists for an ELF executable with an appended key-value store. Any scientific contribution must lie in a validated combination or mechanism not already covered by prior art, and novelty remains **UNPROVEN** until a dedicated prior-art review is complete.

Material EUDI research SHALL re-enter the single `FRANK_V0_1` program as one of:

- `FRANK_V0_1_CODE_DELTA`
- `FRANK_V0_1_TEST_DELTA`
- `FRANK_V0_1_ARCHITECTURE_DELTA`
- `FRANK_V0_1_WORK_DELTA`
- `FRANK_V0_1_NEGATIVE_RESULT`
- `FRANK_V0_1_NO_CHANGE_WITH_EVIDENCE`

Architecture prose alone is insufficient when an executable discriminator is feasible.

---

## 1. Why reconsider the physical boundary

Current Frank v0.1 already defines identity as a server-binary plus admitted persistent state lineage, with UnifiedDB as canonical semantic state and the final model integrated into the real runtime. That creates a natural research question:

```text
Does physical co-location of root/runtime/model/state
improve identity coherence, reproducibility, deployment and recovery
without sacrificing protection, transactional safety or performance?
```

The candidate is **not** motivated by aesthetic minimalism or the number of directory entries. A one-file layout is useful only if measurable properties improve.

Potential advantages:

1. eliminate runtime/model/schema/config skew between independently deployed artifacts;
2. make an accepted root + state-lineage pair transportable and inspectable through one authoritative image;
3. bind model, runtime and semantic manifests to exact content identities;
4. simplify snapshot/clone/restore semantics at the Frank identity boundary;
5. support deterministic provenance from one image manifest to all immutable components;
6. reduce accidental partial upgrades;
7. make state lineage explicit rather than treating memory as an unrelated application database;
8. permit direct aligned access to large tensor extents without copying them into ordinary database rows.

Potential disadvantages are equally important:

1. one inode can increase corruption blast radius;
2. normal filesystem permissions cannot independently protect subregions of one writable file;
3. an executing ELF is normally hostile to direct concurrent self-write on Linux (`ETXTBSY` behavior);
4. stock SQLite crash-safe modes use auxiliary journal/WAL files, contradicting a strict one-persistent-file invariant;
5. very large single files may amplify update, backup, replication and compaction costs;
6. model mmap behavior may regress if container offsets are handled poorly;
7. security tooling may distrust self-modifying executable-like artifacts;
8. a one-file constraint can become a harmful optimization target if it forces weaker recovery or privilege boundaries.

Therefore physical unification is a **testable optimization hypothesis**, not an identity axiom.

---

## 2. Prior-art and external-evidence synthesis

### 2.1 Direct prior art: executable + mutable database

The Rust project **SHED (Self Hosted Executable Database)** describes a portable key-value store appended to the end of an ELF executable, explicitly allowing the executable to retain mutable data in itself. This directly refutes any claim that the generic idea “an executable can contain its own mutable database” is novel.

Implication for Frank:

```text
NOT NOVEL BY ITSELF:
ELF + appended mutable KV store
```

EUDI research must therefore focus on harder properties: large mmap-compatible neural weights, immutable/mutable cryptographic region separation, transactional state lineage, crash-safe self continuity, typed authority boundaries, model/runtime/state identity, autonomous-agent memory semantics and measured causal equivalence.

### 2.2 Orthogonal persistence and persistent heaps

Orthogonal-persistence research argues for uniform treatment of long-lived objects without forcing application logic to manage persistence boundaries manually. Persistent-memory work shows that recoverability, transactional correctness and position-independent/offset-addressed structures are central when state must survive process/system failure.

Implication:

- EUDI should use offsets/content identities, not raw process pointers, for persistent references;
- only canonical information needed for correct reconstruction should be durable;
- derived/rebuildable topology should remain reconstructable rather than unnecessarily persisted;
- crash consistency is part of the semantic contract, not a storage afterthought.

### 2.3 Agent memory as evolving state

Recent work on long-term agent memory argues that correctness is a property of the **state trajectory**, not merely correctness of individual records. That is strongly compatible with the existing Frank distinction between a stable root identity and an admitted evolving state lineage.

Implication:

```text
ROOT identity != every byte of mutable memory
STATE identity = admitted trajectory / lineage head
```

This supports explicit versioned state transitions, revision/forgetting semantics and restart continuity instead of hashing the entire mutable image as a single undifferentiated identity.

### 2.4 Native process substrate

Recent work realizing LLM agents as native POSIX processes demonstrates the value of inheriting lifecycle, isolation and resource semantics from the operating system rather than reimplementing them all in an agent framework. It also explicitly notes that POSIX process semantics alone do not constitute a complete cognitive runtime.

Implication:

EUDI should exploit normal Linux process and file-descriptor primitives rather than inventing a private pseudo-OS, while keeping Frank cognition/state semantics above the process layer.

### 2.5 GGUF/llama.cpp evidence

Current `llama.cpp`/GGUF code provides several useful facts:

- GGUF tensor data is represented as an aligned binary blob with explicit tensor offsets;
- current GGUF readers can operate on a `FILE *` and initialize from the file pointer's **current offset**;
- current llama model-loader paths include file-pointer sources and mmap-capable load modes.

This makes a GGUF region inside a larger image technically plausible. However, **subregion zero-copy/mmap equivalence is not yet proven for EUDI**. It must be measured against the normal external-GGUF path because loader/backend details can impose assumptions about offsets, file size, mapping alignment or split-model handling.

### 2.6 Linux execution evidence

Linux provides `memfd_create()` for anonymous volatile file descriptors that behave like files in memory and can be mapped/sealed. `fexecve()`/`execveat()` can execute from a file descriptor and are specifically useful after verifying executable contents. Linux also documents `ETXTBSY` when write access is requested to an executable image currently being executed.

Implication:

A robust one-authoritative-file design should **not** depend on the persistent image continuously modifying the same file mapping from which the kernel is executing its text. A small verified boot stage can detach the executable runtime into a sealed executable `memfd`, then let the runtime reopen the authoritative image as data.

### 2.7 SQLite evidence

A normal SQLite database begins with its SQLite header at byte zero; a normal ELF executable begins with ELF identification bytes. Therefore one ordinary file cannot simultaneously be both a standard byte-zero SQLite database and a standard byte-zero ELF executable.

SQLite also normally uses a separate rollback journal or, in WAL mode, a main DB + `-wal` + `-shm` state while active. SQLite's VFS layer is extensible and performs reads/writes at explicit offsets, so an offset-translating/custom VFS is technically possible, but correct virtualization of journals, locking, crash recovery and shared-memory semantics would need independent proof.

Implication:

EUDI SHALL NOT be described as “just a normal SQLite file that is executable.” The correct abstraction is a self-executing **container image** whose mutable UDB region may use SQLite through a custom VFS, or may use a different native single-image transaction engine.

### 2.8 Large-model storage behavior

LLM systems research continues to show that storage layout and memory mapping matter: loading and serving large model parameters efficiently requires careful interaction between flash/storage, page cache, DRAM and access locality.

Implication:

The model region must be a first-class aligned immutable extent and must never be serialized through ordinary row/BLOB access on the hot inference path.

---

## 3. Candidate definition

### 3.1 Physical artifact

The candidate authoritative persistent artifact is:

```text
/opt/frank/self.root.udb
```

In steady state, this is the only authoritative persistent Frank self-image required to boot and continue the admitted state lineage.

“Single file” SHALL mean **one authoritative persistent self-image in steady state**, not “the system may never create a temporary file descriptor, anonymous memfd, backup snapshot, update candidate or operator export.” Refusing safe transient/update mechanisms merely to preserve an inode-count aesthetic is forbidden.

### 3.2 Logical layout

Candidate layout:

```text
self.root.udb
│
├── [ELF BOOT CAPSULE]
│     minimal bootstrap only
│
├── [SUPERBLOCK A]
├── [SUPERBLOCK B]
│     generation / checksums / region table / active roots
│
├── [IMMUTABLE ROOT REGION]
│     ClayCode runtime
│     Frank loop/runtime
│     translator / Needle boundary implementation
│     inference runtime
│     static contracts / schemas / manifests
│
├── [IMMUTABLE MODEL REGION]
│     aligned GGUF model extents
│     optional separate LoRA extent during research
│     or merged final model after acceptance
│
├── [CANONICAL MUTABLE UDB REGION]
│     typed semantic state
│     self/world/body/context state
│     memory
│     goals/interests
│     reward/causal-credit state
│     token/session state as allowed
│     learned visual state
│     capability provenance
│     experiments/outcomes
│
├── [INTERNAL TRANSACTION LOG]
│     append-only commit records / epochs
│
├── [CHECKPOINT / RECOVERY ROOTS]
│
├── [DERIVED/REBUILDABLE INDEX REGION]
│     ClayGraph/topology/search accelerators where justified
│
└── [CONTENT / MERKLE INDEX]
      region hashes
      chunk hashes
      lineage roots
      build provenance
```

Physical co-location SHALL NOT erase semantic boundaries.

---

## 4. Identity model

Hashing the entire mutable file after every memory write would incorrectly turn every remembered event into a new binary identity. EUDI therefore uses layered identity.

### 4.1 Immutable root identity

Candidate:

```text
ROOT_ID = H(
    boot_capsule_identity,
    root_manifest,
    ClayCode_runtime_hash,
    Frank_runtime_hash,
    translator_hash,
    inference_runtime_hash,
    final_model_hash,
    static_contract_hashes,
    region_table_semantics
)
```

### 4.2 Mutable state identity

Candidate:

```text
STATE_HEAD[n] = H(
    STATE_HEAD[n-1],
    admitted_transaction_root[n],
    epoch[n],
    provenance[n],
    schema_identity[n]
)
```

### 4.3 self.root identity

The exact project identity law remains owner-fixed. EUDI proposes the implementation form:

```text
SELF_ROOT_IDENTITY = (
    ROOT_ID,
    admitted STATE_HEAD lineage,
    accepted target-body binding,
    required API/runtime identity receipts
)
```

This is a hypothesis-compatible implementation of “server-binary + admitted persistent state lineage,” not a supersession of that law.

### 4.4 Chunk/Merkle identity

Large immutable model/runtime extents SHOULD be chunk-hashed so that verification, distribution and backup can identify changed blocks without treating every operation as an opaque multi-gigabyte blob. A full release root still binds every immutable chunk transitively.

---

## 5. Boot and execution hypothesis

### 5.1 Proposed boot sequence

```text
Linux execve(self.root.udb)
        |
        v
minimal ELF boot capsule
        |
        +-> read redundant superblocks
        +-> validate active immutable root manifest
        +-> verify exact runtime region identity
        +-> create executable memfd
        +-> copy/materialize only runtime executable region
        +-> seal executable memfd as strongly as practical
        +-> fexecve/execveat verified runtime
        |
        v
Frank runtime executes detached from persistent image text
        |
        +-> reopen self.root.udb as canonical data image
        +-> map/read immutable model region
        +-> open canonical UDB state engine
        +-> recover newest valid STATE_HEAD
        +-> enter real Frank v0.1 loop
```

The multi-gigabyte model SHOULD remain file-backed and mmap/read directly from the immutable model extent when technically possible. It SHOULD NOT be copied wholesale into memfd merely to achieve single-file packaging.

### 5.2 Security law for executable materialization

The runtime SHALL NOT expose a generic “execute arbitrary database BLOB” capability.

Only a manifest-addressed, exact-hash-verified executable root region may be materialized into executable memfd by the boot capsule. Normal state transactions, model outputs, web evidence, tool results and user messages have **zero authority** to select new executable bytes.

Root mutation remains outside Frank's self-authority under the current project rules.

---

## 6. Storage-engine variants to test

No storage implementation is preselected by this directive.

### Variant A — EUDI + SQLite through custom VFS

A custom VFS presents an internal extent as SQLite's logical database and virtualizes required auxiliary/journal behavior into defined container extents.

Advantages:

- reuses mature SQLite query/planner/page machinery;
- lower implementation burden if crash semantics can be preserved.

Risks:

- WAL/journal/locking semantics are subtle;
- accidental sidecar creation violates strict single-image semantics;
- correctness proof burden is high;
- custom VFS bugs can silently undermine durability.

### Variant B — EUDI native append-only/CoW UDB engine

Implement canonical UDB state directly as typed append-only transactions plus copy-on-write indexes/checkpoint roots.

Advantages:

- native one-image semantics;
- transaction/epoch/state-lineage identity can be first-class;
- no sidecar impedance mismatch.

Risks:

- much larger implementation and verification surface;
- danger of rebuilding database-engine correctness poorly;
- query/index/concurrency maturity lower initially.

### Variant C — hybrid logical UDB

Keep SQLite or another mature engine for selected logical/index operations while the authoritative state/event lineage uses an EUDI-native append-only transaction substrate. Rebuild derived indexes after recovery where economical.

### Mandatory control — split layout

All variants must be compared against a conventional control such as:

```text
frank            immutable executable/runtime
model.gguf       immutable model
state.udb        mutable canonical state
```

or, if model is already in the binary:

```text
frank            immutable runtime + model
state.udb        mutable canonical state
```

A one-file result is not accepted merely because it works. It must justify its added complexity.

---

## 7. Hypothesis family

### H-EUDI-01 — Deployment coherence

**Hypothesis:** one authoritative image measurably reduces version/configuration skew between runtime, model, schema and state compared with a split layout.

**Counterhypothesis:** manifest-bound split artifacts provide equal coherence with better isolation.

### H-EUDI-02 — Model subregion zero-copy

**Hypothesis:** an aligned GGUF model extent embedded in EUDI can preserve deterministic model semantics and near-baseline mmap/startup/RSS/page-fault/inference performance.

**Counterhypothesis:** loader/subregion mapping constraints introduce copies, alignment penalties or backend regressions large enough to defeat the design.

### H-EUDI-03 — Detached self execution

**Hypothesis:** bootstrap -> verified sealed memfd -> `fexecve` cleanly solves the Linux executing-file/write conflict while keeping one authoritative persistent image.

**Counterhypothesis:** the handoff creates unacceptable security, startup, observability or crash-recovery complexity.

### H-EUDI-04 — Single-image crash consistency

**Hypothesis:** redundant superblocks + internal append-only transaction log + commit checksums can guarantee recovery to either the pre-transaction or fully committed post-transaction state after arbitrary interruption, without corrupting immutable root/model regions.

**Counterhypothesis:** a mature split DB/journal design remains materially safer or simpler.

### H-EUDI-05 — Region isolation

**Hypothesis:** typed write APIs, fixed region bounds, immutable manifests, content hashes and executable-materialization restrictions can make mutable state unable to alter executable/model semantics under normal authority.

**Counterhypothesis:** losing filesystem/inode-level permission separation makes the single-file layout intrinsically weaker for least privilege and corruption containment.

### H-EUDI-06 — Identity stability

**Hypothesis:** `ROOT_ID + admitted STATE_HEAD lineage` provides a cleaner operational identity for self.root than a conventional set of loosely coupled files.

**Counterhypothesis:** the same identity can be represented equally well by a signed manifest over split files, so physical unification adds no identity benefit.

### H-EUDI-07 — Backup/update economics

**Hypothesis:** content-defined/chunked hashing, snapshots/reflinks or block-aware transfer keep incremental backup/update costs acceptable despite a multi-gigabyte image.

**Counterhypothesis:** routine state churn forces excessive copying, fragmentation, backup bandwidth or write amplification compared with separate immutable model/runtime and small mutable DB files.

### H-EUDI-08 — Recovery blast radius

**Hypothesis:** redundant internal roots plus external backups can contain corruption sufficiently despite one physical file.

**Counterhypothesis:** co-locating immutable root/model and mutable state creates an unacceptable single-file failure domain.

### H-EUDI-09 — Causal equivalence

**Hypothesis:** for the same admitted root/model/state input, EUDI produces the same architecture-relevant Frank state transitions, model outputs under deterministic fixtures, GWT/re-entry receipts, effect decisions and verified outcomes as the split reference layout.

### H-EUDI-10 — Scientific novelty boundary

**Hypothesis:** a publishable contribution may exist in the measured architecture combining executable root identity, mmap LLM extents, transactional evolving agent-state lineage, cryptographic immutable/mutable separation, detached verified execution and causal agent acceptance.

**Counterhypothesis:** the combination is an engineering integration of known techniques without sufficient new mechanism or result for a scientific novelty claim.

**Current status:** OPEN / NOVELTY UNPROVEN.

---

## 8. Required executable research program

### EUDI-E0 — prior-art map

Create a durable prior-art matrix covering at minimum:

- self-modifying/self-contained executable stores (including SHED);
- orthogonal persistence;
- persistent heaps / NVM transaction systems;
- executable/unikernel/single-process packaging;
- GGUF/LLM mmap and storage-backed inference;
- SQLite VFS and journal/WAL semantics;
- content-addressed/Merkle/chunked storage;
- long-term agent memory/state-trajectory systems;
- capability/least-privilege database security.

Record exact mechanism overlap and novelty gaps. Do not rely on title similarity.

### EUDI-E1 — minimal self.root image proof

Build a non-production PoC containing:

- valid ELF bootstrap at byte zero;
- embedded secondary runtime ELF;
- mutable internal state region;
- redundant superblocks;
- exact region hashes.

Required sequence:

```text
boot -> verify -> memfd -> fexecve -> write state -> clean restart -> recover state
```

Success requires one authoritative persistent image in steady state and exact state persistence.

### EUDI-E2 — GGUF subregion experiment

Use the same model bytes in two conditions:

A. ordinary external GGUF;  
B. aligned GGUF extent inside EUDI.

Measure:

- deterministic output/logit equality where fixture permits;
- model tensor identity;
- startup latency;
- RSS/PSS;
- major/minor page faults;
- bytes read;
- tokens/s;
- first-token latency;
- CPU/GPU offload compatibility;
- mmap behavior;
- cold-cache and warm-cache runs.

No promotion if embedded loading silently copies the entire model or materially regresses required target-VPS operation without compensating benefit.

### EUDI-E3 — executing-file/write discriminator

Empirically demonstrate the direct-self-write failure/constraint on target Linux and show whether memfd detachment permits safe persistent-image writes after handoff.

Test clean, concurrent and forced-crash boundaries around boot handoff.

### EUDI-E4 — crash-consistency campaign

Inject process kill, host reboot/power-loss simulation and short writes at every commit phase.

Minimum property:

```text
recovered state ∈ {last valid pre-commit state, fully valid committed state}
AND immutable ROOT_ID remains intact
AND no fabricated state head is admitted
```

Run repeated randomized seeds. A one-off happy-path restart is not evidence.

### EUDI-E5 — corruption/fault injection

Flip/truncate/reorder bytes independently in:

- boot manifest;
- runtime extent;
- model extent;
- state transaction;
- journal commit record;
- superblock A/B;
- derived index region.

Required behavior is explicit fail-closed/quarantine/rebuild/rollback according to region class. Derived index corruption must not become semantic truth.

### EUDI-E6 — upgrade and rollback

Test:

```text
ROOT_A + STATE_HEAD_n
        -> candidate ROOT_B
        -> state compatibility/migration
        -> admitted ROOT_B + STATE_HEAD_m
        -> restart
        -> rollback where allowed
```

Reject stale lineage, partial root upgrades and model/runtime/schema mismatch.

A safe implementation may use an external temporary candidate image plus fsync/atomic rename during upgrade. “One file” refers to the accepted authoritative steady-state self image, not a prohibition on safe update construction.

### EUDI-E7 — authority/security adversarial suite

Attempt to use:

- open-web content;
- token message payloads;
- model output;
- tool output;
- corrupted mutable state;
- crafted database records

to alter root/model executable bytes, region table, ROOT_ID, executable memfd selection or effect authority.

Required result: zero unauthorized executable-root promotion on frozen adversarial corpus.

### EUDI-E8 — backup/replication/compaction benchmark

Compare EUDI vs split control for:

- bytes written per state transaction;
- fsync cost;
- fragmentation;
- snapshot time;
- incremental backup bytes;
- full backup time;
- restore time;
- disk-space amplification;
- model-update cost;
- state-only update cost.

### EUDI-E9 — Frank causal differential

Run the same deterministic Frank fixtures in EUDI and split layouts and compare every architecture-relevant state transition/receipt that can be normalized across physical representations.

Must include:

```text
observation -> candidate -> GWT selection -> broadcast -> delivered
-> reconstructed -> used -> local effect -> verified outcome
-> causal credit -> admitted learning -> re-entry
```

Physical layout must not mint truth, authority, reward or GWT salience.

### EUDI-E10 — target-VPS sustained run

If E1-E9 survive, execute sustained target-VPS runs including restart cycles, concurrent state activity, model inference, token API traffic, proactive idle work, resource pressure and recovery.

---

## 9. Promotion / rejection gates

EUDI MAY be promoted toward Frank v0.1 architecture only if all applicable gates below PASS:

1. `EUDI_BOOT_EXEC_GATE`
2. `EUDI_ROOT_STATE_IDENTITY_GATE`
3. `EUDI_GGUF_SUBREGION_GATE`
4. `EUDI_TRANSACTION_CRASH_GATE`
5. `EUDI_REGION_ISOLATION_GATE`
6. `EUDI_AUTHORITY_SECURITY_GATE`
7. `EUDI_UPGRADE_ROLLBACK_GATE`
8. `EUDI_BACKUP_RESOURCE_GATE`
9. `EUDI_FRANK_CAUSAL_EQUIVALENCE_GATE`
10. `EUDI_TARGET_VPS_SUSTAINED_GATE`

Promotion also requires at least one measured benefit over the split control that justifies the additional complexity.

### Hard rejection/retreat conditions

The strict single-authoritative-image variant SHALL be rejected or weakened to a split layout if evidence shows any of:

- materially weaker root/state least-privilege isolation;
- unrecoverable corruption coupling root/model/state;
- inability to meet crash-consistency requirements;
- unacceptable mmap/inference regression;
- large routine write/backup amplification;
- inability to perform safe atomic upgrades/rollback;
- architecture complexity not compensated by measurable benefit;
- need for model/state copies that exceed target-VPS resource budget;
- direct conflict with current self.root identity/authority contracts.

A negative result is a valid and valuable outcome.

---

## 10. Security architecture candidate

### 10.1 Immutable regions

Normal Frank runtime transactions SHALL have no API capable of writing:

- boot capsule;
- active root runtime;
- model weights;
- static authority contracts;
- root manifest.

### 10.2 Mutable regions

Only typed transaction APIs may mutate canonical state. Every admitted mutation receives epoch/provenance/transaction identity and participates in state-lineage hashing.

### 10.3 Derived regions

ClayGraph/topology/cache/index structures that are semantically derived SHALL be rebuildable and SHALL NOT become authoritative truth merely because they reside in the same file.

### 10.4 Root upgrades

Frank/self.root does not obtain authority to rewrite its own Harness/root merely because the root and state share a physical image. Existing owner/Clay separation remains in force.

### 10.5 Executable memfd

Executable memfd use must be narrowly scoped to exact verified root bytes. Generic executable-memory services are forbidden. Where supported, use sealing and test that post-verification mutation cannot alter the executable image.

---

## 11. State and persistence principle

EUDI adopts the following principle:

```text
PHYSICAL UNITY != SEMANTIC UNITY != AUTHORITY UNITY
```

and:

```text
PERSIST ONLY WHAT MUST SURVIVE;
REBUILD WHAT IS DERIVED;
HASH WHAT DEFINES IDENTITY;
REPLAY WHAT DEFINES LINEAGE.
```

This preserves the established Clay principle that semantic/logical unification does not by itself require one physical storage engine. EUDI is specifically a hypothesis that one physical image could provide additional value; it must earn that decision empirically.

---

## 12. Relationship to Frank v0.1 work packages

Primary mappings:

- `F-V01-01-IDENTITY-SERVER-BINARY`: ROOT_ID / state-lineage implementation candidate;
- `F-V01-04-UNIFIEDDB-STATE-CONTINUITY`: physical state container, transactions, epochs, recovery;
- `F-V01-13-SECURITY-RECOVERY-OBSERVABILITY`: corruption, crash, rollback, least privilege, receipts;
- `F-V01-15-FINAL-MODEL`: final model physical embedding only after owner-authorized model acceptance;
- `F-V01-16-END-TO-END-ACCEPTANCE`: same exact image identity on target VPS if promoted.

Secondary mappings:

- `F-V01-02-CLAYCODE-COMPILER-RUNTIME`: runtime materialization/build packaging;
- `F-V01-03-COGNITIVE-LOOP-CORE`: causal equivalence test surface;
- `F-V01-08-TOKEN-API-CLIENTS`: state/session restart continuity;
- `F-V01-09-EFFECT-AUTHORITY`: no physical-layout authority leakage;
- `F-V01-10-PROACTIVE-AGENCY-WEB`: persistent goal/interest state and web non-authority;
- `F-V01-11-MEMORY-REWARD-GOALS`: evolving-state lineage semantics.

This directive does not authorize final paid/model training.

---

## 13. Science-facing claim discipline

Until E0 and the experimental program are complete, workers SHALL use language such as:

- “architecture candidate”;
- “provisional mechanism”;
- “engineering hypothesis”;
- “measured combination, if validated”;
- “novelty unproven.”

Workers SHALL NOT say:

- “first executable database”;
- “first self-contained stateful executable”;
- “first AI stored in its own database”;
- “novel scientific architecture”

without explicit prior-art evidence supporting the exact narrower claim.

Potential research contribution, if validated:

> A measured self-executing cognitive state image that binds an immutable content-addressed agent root and mmap-compatible neural model to a crash-consistent, cryptographically chained evolving semantic-state lineage, while preserving strict non-authority of mutable evidence and demonstrating causal equivalence to a split deployment.

Even this formulation remains a **candidate claim**, not an accepted novelty statement.

---

## 14. Initial external references / prior-art anchors

The following are research anchors, not authority:

### Executable database prior art

- SHED — Self Hosted Executable Database, Asriel, Rust crate/repository, 2017–2021. Describes a KV store appended to an ELF executable.

### Persistent programming / memory

- Dearle, Kirby, Morrison. *Orthogonal Persistence Revisited*. arXiv:1006.3448.
- Cai et al. *Understanding and Optimizing Persistent Memory Allocation*. arXiv:2003.06718.
- Fernando et al. *Persistence and Synchronization: Friends or Foes?* arXiv:2012.15731.

### Agent memory / process substrate

- Orogat, Mansour. *Is Agent Memory a Database? Rethinking Data Foundations for Long-Term AI Agent Memory*. arXiv:2605.26252.
- Ke. *Quine: Realizing LLM Agents as Native POSIX Processes*. arXiv:2603.18030.
- Zhou et al. *Filesystem-Based Memory for LLM Agents: Organization, Evolution, and Sustainability*. arXiv:2607.26637.

### LLM storage/model format

- ggml-org/llama.cpp current GGUF and model-loader source (`ggml/include/gguf.h`, `ggml/src/gguf.cpp`, `include/llama.h`, `src/llama-model-loader.cpp`).
- Alizadeh et al. *LLM in a Flash: Efficient Large Language Model Inference with Limited Memory*. arXiv:2312.11514.

### Linux primitives

- Linux `memfd_create(2)` manual and kernel executable-memfd documentation.
- POSIX/Linux `fexecve(3)` / `execveat(2)` semantics.
- Linux `open(2)` / `execve(2)` `ETXTBSY` behavior.

### SQLite

- SQLite Database File Format.
- SQLite VFS interface documentation.
- SQLite Atomic Commit documentation.
- SQLite WAL-mode File Format.

### Content-addressed/chunked state

- Content-defined Merkle-tree/container delivery literature should be included in E0 and evaluated for model/root chunk verification and delta distribution.

---

## 15. Immediate next actions for all relevant workers

1. Treat EUDI as a cross-cutting candidate, not a frozen design.
2. Preserve split-layout control measurements.
3. Start with `EUDI-E0` and a minimal `EUDI-E1` discriminator before touching production root/state format.
4. Prove GGUF subregion semantics independently (`EUDI-E2`).
5. Prove crash and authority properties before discussing promotion.
6. Record negative evidence without trying to rescue the one-file aesthetic.
7. Feed findings into the current Frank v0.1 workspace and exact affected component gates.
8. Do not mutate current production/state identity solely because this directive exists.
9. Revisit this directive after each major falsification or validated mechanism; update/rewrite it rather than treating this first version as doctrine.
10. A later owner-fixed architecture decision may accept, narrow, hybridize or reject EUDI.

---

## 16. Current synthesis

Current evidence supports **plausibility**, not acceptance.

Strongly supported:

- executable + appended mutable data is feasible and has prior art;
- GGUF is offset/alignment structured and current readers can begin from a nonzero file position;
- Linux provides verified file-descriptor execution and anonymous memfd primitives;
- direct writes to an executing image are a real Linux constraint;
- standard SQLite WAL/journal behavior conflicts with strict one-file persistence;
- agent-memory correctness benefits from treating memory as an evolving governed state trajectory;
- persistent systems require explicit recoverability/crash semantics.

Still unproven:

- direct high-performance mmap of embedded model extents across all required llama.cpp/GPU paths;
- robust one-image transactional semantics under crash/concurrency;
- security equivalence or superiority to split file permissions;
- backup/update economics for multi-gigabyte mixed immutable/mutable images;
- causal equivalence of Frank under EUDI;
- target-VPS resource viability;
- scientific novelty of the combined architecture.

Therefore:

```text
EUDI_STATUS = RESEARCH_CANDIDATE
PROMOTION = NONE
PRODUCTION_MUTATION = NONE
NOVELTY_CLAIM = NONE
TRAINING_AUTHORIZATION = NONE
NEXT = PRIOR_ART + EXECUTABLE_DISCRIMINATORS + TARGET_VPS_MEASUREMENT
```

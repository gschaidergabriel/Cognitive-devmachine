# Current external engineering notes — 2026-08-27

These are `EXTERNAL_PRIMARY` research inputs, not project runtime evidence. Each item is paired with the exact project question it changes.

## 1. SQLite WAL-reset bug: runtime SQLite version must be evidence

**Primary source:** SQLite official *Write-Ahead Logging* documentation, current page: `https://www.sqlite.org/wal.html`.

The current SQLite documentation records a **WAL-reset bug** discovered on 2026-03-03 and fixed in SQLite **3.51.3 (2026-03-13)**, with backports listed for some older branches. SQLite describes the affected situation as WAL mode with two or more connections in different threads/processes where writes/checkpoints race under tight timing conditions.

### Project relevance

Frankenstein/GRID10/UnifiedDB lineage uses SQLite/WAL and multi-process coordination patterns. That does **not** mean the project was affected by this bug. The exact SQLite runtime version for the current target execution is not established merely by source imports or by a historic probe.

The repository contains tools that inspect `sqlite3.sqlite_version` (for example `tools/database_pulse_benchmark.py` and `tools/unifieddb_u11_target_vps_probe.py`), which shows a method exists for version capture. It does not provide a current runtime fact by itself.

### Required evidence delta

For any future exact-current WAL concurrency acceptance receipt, bind:

```text
Python/runtime build identity
sqlite3.sqlite_version
journal_mode actually observed
connection/process topology
checkpoint policy
exact workload/command
source SHA
result log hash
```

If the observed SQLite is in an affected range, treat that as an environment risk requiring upgrade/backport or a bounded reproduction/mitigation plan; do not infer corruption occurred.

**Classification:** `EXTERNAL_PRIMARY` + `INFERENCE` (project relevance).  
**Current project affected?** `UNKNOWN`.  
**Falsifier/closure:** exact current runtime receipt proves a fixed SQLite version or an unaffected topology.

---

## 2. PyTorch CPU oversubscription matches the GRID10 counterexample mechanism

**Primary source:** PyTorch current documentation, *Multiprocessing best practices*, CPU oversubscription section: `https://docs.pytorch.org/docs/stable/notes/multiprocessing.html`.

PyTorch warns that multiprocessing can oversubscribe CPU resources, causing contention and context-switch overhead. Its worked guidance gives `floor(N/M)` as a maximum thread count per subprocess for an `N`-vCPU / `M`-process topology, while explicitly noting that the appropriate value depends on the task.

### Project relevance

The current project measurement on four vCPUs with four concurrent model processes found:

- one intra-op thread/process: `8.3197 s/call` mean over 12 samples;
- two: `23.1806 s/call` mean over 12 samples;
- four: zero completed samples within experiment timeouts.

The official guidance supplies a plausible **mechanism** (oversubscription/contention) for the measured result. The project measurement, not the documentation, remains the direct evidence for the project topology.

**Classification:** `EXTERNAL_PRIMARY` supports interpretation of `PROJECT_MEASUREMENT`.  
**Generalization limit:** do not transfer the one-thread optimum to a different vCPU/process/model topology without measurement.

---

## 3. Adversarial GNWT/IIT results strengthen the project's falsifiability rule

**Primary source:** Cogitate Consortium et al., *Adversarial testing of global neuronal workspace and integrated information theories of consciousness*, Nature 642, 133–142 (2025), DOI `10.1038/s41586-025-08888-1`.

The preregistered adversarial collaboration reports results that align with some predictions of both theories while substantially challenging key tenets of both; for GNWT the paper highlights lack of the predicted offset ignition and limited prefrontal representation for some conscious dimensions.

### Project relevance

Frankenstein uses GWT/workspace language as an engineering hypothesis. This contemporary primary result is a reason **not** to treat a neuroscience theory name as architecture proof. Project-specific workspace/J-Space claims still require intervention evidence at exact model/runtime identity.

**Classification:** `EXTERNAL_PRIMARY`.  
**Forbidden inference:** neuroscience challenge/support → software consciousness claim.

---

## 4. Shared global workspace is an architecture comparison point, not validation

**Primary source:** Goyal et al., *Coordination Among Neural Modules Through a Shared Global Workspace*, ICLR 2022, OpenReview `XzTtHjgPDsT`.

The work studies a bandwidth-limited shared workspace as a coordination mechanism among specialized neural modules.

### Project relevance

This is a useful external baseline family for HCU/J-Space coordination, but it cannot establish that Frankenstein's external state fabric or model-specific vector control is causal. The correct project test remains matched comparison against simpler routers/attention plus lesion/shuffle/rescue controls.

**Classification:** `EXTERNAL_PRIMARY` comparison point.

---

## 5. Reflexion is a feedback-memory comparison point only

**Primary source:** Shinn et al., *Reflexion: Language Agents with Verbal Reinforcement Learning*, arXiv:2303.11366.

Reflexion uses task feedback and episodic reflective text to influence later trials without weight updates.

### Project relevance

It is useful for comparing the general pattern `feedback -> reflective memory -> later decision`. Frankenstein's stricter engineering requirement adds typed provenance, explicit effect/result distinction, and a mandatory exit from reflection into a measurable transition.

**Classification:** `EXTERNAL_PRIMARY`.  
**Not established:** implementation equivalence or reproduction of Reflexion benchmarks.

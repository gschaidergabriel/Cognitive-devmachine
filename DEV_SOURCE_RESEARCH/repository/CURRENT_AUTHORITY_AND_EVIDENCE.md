# Current authority and evidence — Triggerword 3 matrix

**Evidence snapshot base:** `bf10a71a1d6b69ac63654ab01724b2879bc05003`  
**Snapshot date:** 2026-08-27  
**Purpose:** one compact current-vs-historical matrix for curation/re-entry.  
**Authority status:** this file is an index, **not** a new authority surface.

Always re-resolve current `main` and the current authority stack before execution.

---

## 1. Authority resolution used here

Use, in descending order where they conflict:

1. newest explicit owner authority;
2. current admitted supervisor/provider authority;
3. exact executable/source evidence at exact identity and scope;
4. current bootstrap/program/control surfaces;
5. older receipts, branches, PRs and historical source;
6. caches, summaries and conversational memory.

Do not average disagreements. A newer-looking filename does not become authority merely because its version string is larger.

Two current examples:

- `SUPERVISOR_STEERING_9_13O_...` explicitly says `NON_AUTHORITY_STEERING_ONLY`;
- `SUPERVISOR_STEERING_9_14_GO_...` also remains steering, not a replacement provider authority.

The operative provider authority resolved during this Trigger-3 pass remains **9.13 HARD_OFF**.

---

## 2. Current owner architecture target

`CURRENT_SOURCE`

Highest-precedence target used by this pass:

`research_entity/global/OWNER_CORRECTION_ZERO_ENTITYOS_COGNITIVE_GRID_DB_CLAUDECODE_GLOBAL_JSPACE_2026-08-25.md`

The finished-system target is:

```text
VARIABLE COGNITIVE GRID + PERSISTENT DATABASE + CLAUDE CODE
```

Implications:

- grid size `N` is a runtime parameter;
- GRID10 is a benchmark/debug configuration, not final architectural identity;
- the grid should reproduce/distribute the cognitive processes that made Zero/EntityOS useful;
- durable exact information belongs in the database when deterministic storage is superior to simulation;
- Claude Code remains the strong model/tool/code partner;
- Global J-Space coupling can be claimed only at the strongest interface actually exposed and causally evidenced;
- no activation-level access to Claude Code may be invented;
- the first serious small-module target remains Qwen3.5-0.8B-class in this owner directive.

Owner shorthand:

```text
SIMULATE COGNITION; STORE DURABLE DATA.
```

---

## 3. Local/VPS development authority vs. provider authority

These are separate questions.

### 3.1 Designated local/VPS sandbox

`CURRENT_SOURCE`

`CLAY_EXECUTION_AUTHORITY.md` points to:

`governance/CLAY_VPS_SANDBOX_FULL_EXECUTION_AUTHORITY_2026-08-25.md`

Within the designated `clay-direct-dev` sandbox, the owner authority permits broad development/research activity including root/sudo in that sandbox, package installation, compilation, local models/runtimes, tests, fuzzing, benchmarks, ablations, process administration and scratch-destructive tests.

That does not independently authorize paid-provider spend, subscriptions, attacks, credential theft/exfiltration or unrelated host effects.

### 3.2 Provider execution

`CURRENT_SOURCE`

Current provider state:

```text
9.13 HARD_OFF
provider routes = false
Together = forbidden
paid fallback = forbidden
new provider execution = forbidden
```

Current supervisor surfaces treat fresh post-hardoff fallback/provider activity as evidence that the caller boundary had not been gated early enough.

---

## 4. HARD_OFF closure now fused on `main`

`CURRENT_SOURCE + LOCAL_COMPONENT_EVIDENCE`

Commit:

```text
3c3dbe5020f57065f47bd4d0a2dce3c537128797
trigger3: quarantine Frankenstein provider loops under 9.13 HARD_OFF
```

The commit preserves the original provider-backed Bauleiter/Bugfix implementations as quarantined donor provenance and introduces supported entrypoint gating that resolves current authority **before provider import, secret lookup, network, Aider or fallback dispatch**.

The commit reports:

```text
10/10 focused local tests PASS
scope = source/local-unit only
```

Promotion boundary:

```text
source/local-unit caller closure
!= provider runtime authorization
!= HCU runtime acceptance
!= training credit
!= whole EntityOS PASS
```

This is a direct example of the project law `SOURCE_READY != RUNTIME_VERIFIED`.

---

## 5. Recent Frankenstein 72-hour orchestration

`CURRENT_SOURCE + QUARANTINED_PROVENANCE`

Recent source includes package decomposition, Bauleiter continuation/orchestration and a separate Bugfix watchdog/rollback lane.

The original provider-backed variants are **not current executable authority** under 9.13 HARD_OFF. Current main keeps them as quarantined provenance and requires supported gated entrypoints.

Therefore the correct statement is:

> Source and component tests exist; provider-capable donor implementations are quarantined; supported current entrypoints are required to fail closed before provider/secret/network work under HARD_OFF.

Not:

> Frankenstein now has a deployed 72-hour autonomous provider swarm.

---

## 6. Historical Project-Frankenstein denominator — what is frozen now

`HISTORICAL_SOURCE`

The old archive manifest remains:

```text
PROJECT_FRANKENSTEIN_MANIFEST.json
status = PARTIAL_NOT_FROZEN
exact recursive tree inventory = not frozen
whole-repository semantic completeness = not granted
```

A newer exact source/history anchor now improves one narrower denominator:

`research_entity/archive_assimilation/manifests/PROJECT_FRANKENSTEIN_SOURCE_IDENTITY_HISTORY_ANCHOR_20260827.json`

At frozen historical source head:

```text
Project-Frankenstein main = abba90a5767d85abc8a1ac340bae92842dab35c1
root tree SHA = ec21e66c4672fde1f0a5d948ebc51457b69b620a
default-branch reachable commit count = 545
oldest reachable commit = e1a8812767668091d146ee958bbc2ebb2743031c
oldest reachable commit time = 2026-02-14T17:05:27Z
```

The count is bounded carefully: it is the GitHub REST default-branch reachable history at that snapshot, proven by page 545 non-empty and page 546 empty with `per_page=1`.

It is **not** claimed as:

- every commit on every ref;
- deleted/unreachable history;
- full recursive path/topology denominator;
- proof of real-world project creation date;
- proof that every historical path has been semantically analyzed.

Chronology rule:

> Commit timestamps establish first verified presence in accessible Git at the inspected scope; they do not prove real-world creation time.

---

## 7. Historical source anchors that survive curation

`HISTORICAL_SOURCE`

The existing archive deep-reads include:

| Historical source | Evidence role |
|---|---|
| `services/consciousness_daemon.py` | persistent cognition / multi-timescale loop / workspace precursor |
| `personality/e_pq.py` | persistent state / homeostasis / event learning |
| `services/thalamus.py` | sensory gating / attention / habituation / prediction error |
| `services/global_workspace.py` | broadcast / salience workspace |
| `tools/lcme/lcme_core.py` | memory / claims / graph / vector retrieval / forgetting |
| `services/soma/micro_trainer.py` | LoRA / feedback weighting / before-after probes |
| `services/nucleus_accumbens.py` | reward prediction / motivation / habituation |
| `services/subconscious.py` | actor-critic / PPO / idle-policy lineage |
| `services/spatial_state.py` | persistent world/body state |
| `services/dream_daemon.py` | replay / synthesis / consolidation / interrupt-resume |
| `services/project_engine.py` | projects / goals / strategies / tasks / tool learning |
| `services/hypothesis_engine/` | hypothesis lifecycle / experiments / evaluation |
| historical vision sources | adaptive routing -> FrankEye/Retina -> native multimodal lineage |

These are source-lineage facts. They do not imply current runtime presence or continued architectural authority.

---

## 8. Zero / EntityOS export evidence

`PROJECT_SOURCE`

`agentZero/README.md` documents an exported Zero/EntityOS evidence surface containing, among other things:

- chats with generation/provenance/causal metadata;
- cognition/workspace/effect episodes including EffectGate judgments;
- state and graph projections;
- measurement tools tied to hypotheses;
- append-only architect actions;
- build trajectory and tests;
- code and UnifiedDB schema snapshot;
- redaction before Git export.

This makes Zero valuable as a reconstruction/evidence archive. It does not by itself establish current live runtime acceptance.

---

## 9. UnifiedDB: reproduced negative architecture evidence

`PROJECT_MEASUREMENT + NEGATIVE_RESULT`

The deeper UnifiedDB run:

`research_entity/trigger_runs/unifieddb/unifieddb-20260811T0441p0700-chatgpt-secondary-deeper-deltas/FINAL_REPORT.md`

reproduced six intended design gaps on its accepted target while canonical state and external effects remained untouched:

1. source certificate did not attest live SQLite schema;
2. derived Graph identity became an accidental availability dependency of canonical DB authority;
3. stale projection read gating/source-root binding was insufficient;
4. mixed time encodings + ambient clock could create false-current semantics;
5. snapshot receipt could describe mutable/different logical instants;
6. exact repository HEAD was broader than the semantic dependency set.

Measured normalized live-schema digest cost on that exact target:

```text
p50  91.17 µs
p95 126.77 µs
p99 148.112 µs
```

Design correction:

- split storage, migration, live-schema, semantic-root, projection, time, snapshot, selection and effect proof surfaces;
- keep authority acyclic: canonical DB -> derived projection;
- bind authority to minimal semantic dependency identity, not unrelated repository changes;
- treat retrieval/projections as candidate producers, not truth minting.

---

## 10. Emergent Retrieval boundary

`PROJECT_TERM + INFERENCE`

**Emergent Retrieval** means candidate relevance can become strong when independently stored dimensions overlap at query time — semantics, time, causal lineage, current state, goals, perception, effects/outcomes, confidence, provenance, graph/index context and explicit filters.

It does not mean information appears from nowhere.

Invariant:

```text
retrieval candidate / ranking != canonical truth admission
```

Graph, FTS, vector search, learned rankers and Hyperposition may organize candidate evidence. They do not create facts.

---

## 11. Current GRID/HCU measurement boundary

`PROJECT_MEASUREMENT`

Current steering records an exact diagnostic on a 4-process / 4-vCPU topology:

```text
1 thread/process: ~8.3197 s/call
2 threads/process: ~23.1806 s/call
4 threads/process: zero completions inside tested timeout window
```

This supports a conservative one-thread/process choice **for that exact tested topology**.

It does not establish a universal scaling law and does not restore fixed GRID10 as final owner target.

Logical grid size and physical decode concurrency remain different quantities.

---

## 12. Distillery / training-data yield boundary

`PROJECT_MEASUREMENT + NEGATIVE_RESULT`

Current steering records a snapshot with:

```text
88,774 collected source tokens
0 accepted dataset tokens
```

Therefore:

```text
source-token volume != admitted training-data yield
```

A training pipeline must be measured by accepted, de-duplicated, causally grounded, leak-resistant dataset families and hard negatives, not raw generated volume.

---

## 13. Global J-Space / GWT claim boundary

`CURRENT_TARGET + OPEN_HYPOTHESIS`

Current target:

```text
GRID GLOBAL WORKSPACE
    <-> translate/bridge
    <-> CLAUDE CODE workspace/state at strongest exposed interface
```

Allowed bridge candidates include typed ClayCode packets, structured state slices, semantic Hyperposition, compressed workspace summaries, embeddings/vectors and model-specific activation controls only where actually accessible.

Strong promotion evidence needs matched controls such as:

- label-free/counterbalanced intervention;
- lesion/shuffle;
- rescue where feasible;
- disjoint family holdout;
- prompt/schema/codebook leakage control;
- exact checkpoint/tokenizer/runtime/site identity;
- downstream re-entry effect.

Coherence, recurrence, self-report and majority agreement are insufficient.

---

## 14. Current broad product credit

At the 9.13 frontier used during this pass, broad runtime/training promotion remains unestablished unless a newer exact authority/evidence receipt promotes it.

Conservative matrix:

| Scope | Current curation classification |
|---|---|
| whole EntityOS/HCU runtime | `NOT_ESTABLISHED` |
| full HCU runtime | `NOT_ESTABLISHED` |
| physical GRID10 runtime acceptance | `NOT_ESTABLISHED` |
| canonical runtime semantics | `NOT_ESTABLISHED` |
| Global J-Space model-causal acceptance | `NOT_ESTABLISHED` |
| training promotion | `NOT_ESTABLISHED` |
| Frankenstein HARD_OFF source/local-unit gate | `10/10 PASS AT COMPONENT SCOPE` |
| historical default-branch reachable commit denominator | `545 FROZEN AT HISTORICAL SNAPSHOT` |
| full recursive historical topology/semantic coverage | `NOT_FROZEN` |

---

## 15. Current highest-information gate cluster

`INFERENCE grounded in current owner/supervisor/source evidence`

1. prove supported Frankenstein callers remain blocked before any provider import/secret/network boundary under HARD_OFF;
2. maintain runtime quiescence: no stale process may continue a forbidden provider path;
3. independently review/re-execute quarantined post-hardoff core changes before promotion;
4. align implementation/docs/tests with variable `N` rather than fixed-ten identity;
5. finish the Zero/EntityOS cognitive-process census and turn it into a stable ABI;
6. make the DB-vs-simulation boundary executable/testable;
7. obtain causal workspace/J-Space re-entry evidence at the strongest actually exposed Claude/small-model interfaces;
8. convert raw research/source traces into accepted family-split training data;
9. complete the historical recursive path/topology denominator before repository-wide coverage claims.

---

## 16. Claim hygiene examples

Wrong:

> Frankenstein has autonomous self-healing now.

Evidence-bounded:

> Bauleiter/Bugfix source and focused component tests exist; original provider-backed variants are quarantined under current HARD_OFF; supported caller gating has source/local-unit PASS only.

Wrong:

> Project Frankenstein history is complete.

Evidence-bounded:

> The frozen historical default branch has exactly 545 reachable commits at the observed snapshot; recursive path topology, all-ref/unreachable history and repository-wide semantic coverage remain unfrozen.

Wrong:

> Global J-Space is connected.

Evidence-bounded:

> Workspace/J-Space bridge mechanisms are being developed; causal coupling gets credit only at exact interfaces where controlled intervention/re-entry evidence exists.

Wrong:

> UnifiedDB solved memory.

Evidence-bounded:

> UnifiedDB research consolidated authority direction and reproduced specific schema/projection/time/snapshot/dependency gaps; end-to-end continuity acceptance remains broader than those component findings.

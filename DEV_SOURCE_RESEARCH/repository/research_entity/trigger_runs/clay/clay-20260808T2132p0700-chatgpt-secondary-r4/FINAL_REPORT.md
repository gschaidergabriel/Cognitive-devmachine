# CLAY RESEARCH RUN — G12 · CACC

**run_id:** `clay-20260808T2132p0700-chatgpt-secondary-r4`  
**trigger:** `clay`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**fresh parent Clay:** G11 `MOSAIC`  
**fresh whole-mesh parent:** Fusion F5 `Certified Cognitive Continuity Fabric (C3F)`  
**fresh FRANK:** C7 `Clay Organ Runtime Fabric (CORF)`  
**fresh ClayCode:** CC12 `TCQS`  
**fresh UnifiedDB:** U1 `UD-RC1`  
**candidate:** **CACC-G12 — Certified Adaptive Cognitive Continuity**  
**decision:** **OPEN / HOLD — no canonical Clay generation promotion**

---

## 1. Executive result

Fusion F5 closed over all eight completed scientific workers immediately before this run. Its key open question was no longer “which components belong in Clay?” but:

> **Can persistent, certified Clay state actually improve the next decision of a small model without confusing integrity, salience, GWT selection or authority?**

G12 sharpens the architecture around that question.

# CACC-G12

**Certified Adaptive Cognitive Continuity** adds one missing loop to C3F:

1. **deterministic integrity loop** — certify semantic/provenance/basis/collection/selection/view/capability identity;
2. **empirical cognitive-utility loop** — test whether the authentic association actually helped, harmed or was irrelevant;
3. **external authority boundary** — no utility score, activation, workspace output or model output can mint truth or effect authority.

The compact law is:

> **certified continuity != cognitive correctness != authority**

and the adaptive law is:

> **utility may update salience; it may not silently rewrite canonical truth.**

This is the main G12 architecture delta.

---

## 2. Fresh whole-mesh grounding

The run starts from the completed Fusion F5 snapshot, not from stale branch notes.

### Clay G11 / MOSAIC
Retained: operation-specific causal closure with separate semantic, provenance-instance, basis/epoch, selection-plan and exact reader-view identity.

G12 adds a third closure state:

`KNOWN_VALID | KNOWN_INVALID | UNKNOWN`.

`UNKNOWN` is necessary because an operation-scoped validator is only safe when the dependency closure is actually known.

### FRANK C7 / CORF
Retained:

`semantic organ boundary != process boundary != storage boundary != authority boundary`.

G12 strengthens the placement rule: cognitive hot-path modules may colocate for latency, but secrets/effect authority and untrusted code remain hard boundaries. Model placement remains a ReaderProfile/platform decision.

### ClayCode CC12 / TCQS
Retained: collection kind is semantic, not container metadata.

G12 moves this one stage further: collection algebra participates in **candidate causal identity**. If an ORDERED/MULTISET/WEIGHTED result is lowered as the wrong collection, candidate topology can change before GWT even begins.

### ClayGraph G1d
Retained: immutable semantic epochs -> sparse activation -> bounded Assembly -> optional traversal/escalation -> exact anchors.

G12 adds an empirical utility receipt around salience. Activation can learn whether an association tends to help, but only the salience/routing layer may adapt from that signal.

### UnifiedDB U1
Retained: authoritative event/state/effect spine plus specialized replayable graph/vector/FTS/activation derivatives.

G12 strengthens the default write direction:

`model/workspace proposal -> effect/outcome -> canonical re-entry append -> derived memory update`.

Direct model/workspace writes into durable cognitive memory remain a weaker hypothesis because they complicate replay, revocation and causal attribution.

### GWT R4 / CSOC
Retained stage orthogonality:

`candidate formation -> competition/selection -> gate -> WorkspaceEpisode -> projection -> uptake -> effect -> outcome -> re-entry`.

G12 requires continuity utility to be measured at these stages rather than from one downstream score.

### Hyperposition H4
Retained semantic firebreaks. G12 makes `UNKNOWN dependency closure` a firebreak-relevant state: uncertainty cannot be implicitly cast into “safe known scope”.

### Emergenz / E-CERT2
No emergence promotion. Continuity can become one candidate mechanism only after a reproducible functional effect exists and survives prospective lesion/rescue/OOD and multiscale causal tests.

---

## 3. First-generation hypothesis programme

`HYPOTHESES.json` contains **64 falsifiable first-generation hypotheses** across eight clusters:

1. continuity / integrity / utility;
2. collection and query identity;
3. GWT stage orthogonality;
4. ClayGraph memory;
5. ClayCode reader rails;
6. UnifiedDB/runtime/incremental state;
7. authority/security/recovery;
8. Android, target-4B and emergence.

The most important hypotheses are not additional naming variants. They discriminate:

- truthful continuity vs visible-information confounds;
- stale-invalid vs authentic-but-misleading memory;
- known vs unknown causal closure;
- collection semantics vs authentic record identity;
- graph availability vs GWT selection/ignition;
- canonical semantics vs model-native reader rails;
- same-process zero-copy vs cross-process IPC;
- continuity/recurrent organization vs emergence.

---

## 4. External research fusion

Full source list and boundaries are in `EVIDENCE_LEDGER.md`; practitioner evidence is separated in `REDDIT_IMPLEMENTATION_EVIDENCE.md`.

### Active relational memory has independent support
ACL 2026 **Synapse** uses dynamic graph memory with spreading activation, lateral inhibition and temporal decay. ACL 2026 **MAGMA** separates semantic, temporal, causal and entity graph views. These strengthen the plausibility of a role/time-aware active memory substrate, not FRANK's exact implementation.

### Latent communication needs a utility gate
ACL 2026 **Interlat** demonstrates direct hidden-state communication and substantial compression/latency benefits in its tasks. A separate 2026 latent-communication preprint reports that latent/SAE channels preserve more probe-visible features than text but **do not beat text at task level** in its tested tasks.

This is an unusually useful external contradiction. G12 resolves it by refusing to use feature retention/compression as a proxy for cognition quality.

### Authority should remain structurally separate
ACM CAIS 2026 **Securing Agents With Tracked Capabilities** independently supports a capability-safe boundary around agent effects/resources. G12 imports the mechanism class, not Scala as a required implementation.

### Same-process and cross-process transport are different
Apache Arrow's C Data Interface is explicitly a same-process zero-copy ABI; cross-process sharing and persistence are non-goals. CORF therefore still needs a separate IPC/shared-memory transport contract.

### Causal emergence statistics remain downstream of intervention identity
2026 PEID provides a candidate interventionist decomposition for synergistic causality. It is relevant only after an exact CACC/GWT intervention produces a reproducible functional effect.

### Android is feasible but highly implementation-dependent
2026 practitioner reports show Qwen3-class GGUF/llama.cpp deployments on phones and emphasize build optimization, context limits, latency and battery/thermal issues. These are implementation anecdotes, not FRANK measurements.

---

## 5. Executed empirical work

All new numeric results below are E2B-executed synthetic mechanism tests. They are not live-FRANK effect sizes.

### EXP-G12-REPLAY-001 — canonical replay vs damaged derived stream

50,000 authoritative events across 200 keys. The derived stream received injected duplicates, local reordering and loss of its final 3% tail.

Results:
- naive derived-stream replay: **197 / 200 keys wrong**;
- absolute state error: **6,494**;
- replay from the canonical authoritative log: **0 key mismatches**.

This does not prove a production event-sourcing implementation, but it strongly supports the architecture direction that derived cognitive views should be reproducible from a canonical event spine.

### EXP-G12-HIDDEN-DEPS-002 — scoped consistency under hidden dependencies

200,000 operations over 12 consistency domains; in 8% of episodes one true dependency was deliberately hidden from the observed scope.

Results:
- hidden-dependency cases: **16,068**;
- always-global reject rate: **63.306%**;
- narrow scoped reject rate: **17.870%**;
- narrow scoped unsafe accepts: **0.578% of all operations**;
- conservative policy reject rate: **22.0215%**;
- conservative unsafe accepts: **0 in this constructed family**.

This is G12's most important negative result.

G11/C7 showed the efficiency value of operation-scoped consistency. G12 shows the missing safety condition:

> **scope reduction is valid only when dependency closure is known.**

Unknown dynamic scope must broaden, escalate, recompute or deny a consequential effect.

### EXP-G12-COLLECTION-TOPOLOGY-003

100,000 constructed candidate-selection cases across SET, ORDERED, MULTISET and WEIGHTED semantics.

Type-erasing the collection interpretation changed:
- top-1 candidate: **48.381%**;
- top-3 membership: **72.679%**.

Per-kind top-1 change:
- SET: **7.42%**;
- ORDERED: **87.67%**;
- MULTISET: **49.18%**;
- WEIGHTED: **49.38%**.

Thus CC12's collection types are not only database/compiler semantics. Whenever candidate topology affects GWT/model behavior, they are part of the causal intervention identity.

### EXP-G12-GENERIC4B-CONTINUITY-004

Three NVIDIA requests were queued for `nvidia/nemotron-mini-4b-instruct`:
- neutral/OFF activation;
- truthful activation cue;
- shuffled/misleading activation cue.

No result artifact was present at G12 closure. Therefore:

**NO MODEL-BEHAVIOR RESULT IS CLAIMED.**

This is explicitly preserved rather than converting a pending runner into evidence.

Exact Qwen3-4B remains unavailable in the currently verified NVIDIA/OpenRouter account catalogs.

---

## 6. Fusion 2 — CACC-G12

`FUSION2_HYPOTHESES.json` contains 14 materially transformed hypotheses.

The main architecture is machine-readable in `CACC_G12.claycode.json`.

### CACC loop

```text
canonical event/state/effect/outcome
        ↓
MOSAIC identity + closure
 semantic | provenance | basis | collection | selection | view
        ↓
UnifiedDB typed logical plan
        ↓
derived exact/relational/graph/vector/FTS/activation views
        ↓
ClayGraph sparse role/time-aware activation
        ↓
bounded epoch-pinned Assembly
        ↓
GWT candidate/competition/selection/ignition
        ↓
MRSC P1/P2/P3/hybrid reader rail
        ↓
Clay-native model proposal
        ↓
canonical reconciliation
        ↓
effect-time basis/selection/capability revalidation
        ↓
isolated authority/effect broker
        ↓
outcome + canonical re-entry append
        ↓
incremental derived-memory update
        ↓
empirical cognitive-utility receipt
        ↓
SALience/decay/inhibition/routing adaptation only
        ↺
```

### What utility may change
- activation weights;
- decay rates;
- inhibition policy;
- routing/escalation confidence.

### What utility may not change implicitly
- canonical fact truth;
- provenance ancestry;
- epistemic status without a real evidence transition;
- capability scope;
- effect authority.

---

## 7. The `UNKNOWN` closure state

Earlier operation-scoped validation was often described as if the required dependency set were available.

G12 makes the epistemic state explicit:

### KNOWN_VALID
Required causal dependencies are known and unchanged.

### KNOWN_INVALID
A required dependency changed. Recompute/reject.

### UNKNOWN
The dependency closure may be incomplete because of dynamic code, opaque tool behavior, unresolved selector dependencies or unsupported runtime introspection.

For consequential effects, UNKNOWN must trigger one of:
- broaden scope;
- instrument/trace;
- escalate to a safer/global validation;
- recompute;
- deny/defer the effect.

It may not silently be interpreted as KNOWN_VALID.

This preserves the latency benefit of scoped validation while making its assumption testable.

---

## 8. Dual-path cognitive memory

G12 retains Fusion F5's preferred OPEN policy:

### Background path
Persistent derived state continuously updates sparse activation and Assembly-ready frontiers between model calls.

### Explicit path
Search/retrieval remains available for:
- exact lookup;
- validation;
- low-confidence fallback;
- deliberate broad exploration;
- reconstruction after activation gaps.

This is stronger than either extreme:

`memory = only RAG`  
or  
`activation replaces retrieval`.

The target is:

> **memory continuously changes what is easy to think about, while exact retrieval remains available to verify and recover.**

---

## 9. GWT consequence

A future continuity improvement cannot be labeled a workspace effect merely because end-task performance improves.

CACC/CSOC requires separate receipts for:

`field -> Assembly/candidate set -> competition -> winner -> gate -> WorkspaceEpisode -> reader view -> uptake -> effect -> outcome -> re-entry`.

The decisive target factorial remains:

```text
FIELD:
  OFF
  truthful
  stale-revoked
  role-shuffled
  temporal-shuffled

MEMORY PATH:
  explicit retrieval only
  continuity + fallback

RAIL:
  raw/global
  COVE/MRSC compiled
```

Pin the same underlying facts, model, token budget and effect policy. Counterbalance candidate/projection order.

---

## 10. ClayCode / AI-native speech consequence

G12 keeps a multi-rail model:

- **P1 canonical Clay** — stable machine/system semantics;
- **P2 discrete model-native rail** — trained/compiled compact representation;
- **P3 latent rail** — hidden-state/KV-like communication where receiver interfaces permit it;
- **hybrid** — allowed with exact source/view/tensor receipts.

The selection criterion is not “which representation contains more information?” It is:

`task utility + semantic recoverability + latency + transfer/alignment cost + safety/auditability`.

Latent channels may be excellent optimizations without becoming canonical truth.

---

## 11. UnifiedDB / runtime consequence

The physical architecture remains hybrid.

Strong current default:
- exact event/state/effect/outcome spine — authoritative;
- graph/vector/FTS — derived/rebuildable unless promoted by explicit schema;
- activation/Assembly — transient/non-authoritative;
- capability secrets — hard isolated;
- model latent/KV — isolated runtime state;
- generated code/tools — sandboxed.

Same-process zero-copy handles are a candidate hot-path optimization. Cross-process IPC is a separate benchmark/problem.

---

## 12. Android consequence

Official Qwen3-4B configuration exposes 36 layers, 8 KV heads, head dimension 128 and 40,960 max positions. Combined with C7's KV arithmetic, this keeps bounded Assemblies/MOSAIC views central to mobile feasibility.

G12 does not select a final Android runtime. The target benchmark must include:
- model/quantization;
- context/KV size;
- prefill latency;
- decode throughput;
- RAM and allocator/scratch overhead;
- CPU/GPU/NPU/backend;
- reader rail and transport;
- battery/energy;
- sustained thermal behavior.

Cold tokens/sec is not enough.

---

## 13. Emergence boundary

CACC increases functional continuity if it works. That would still not establish phenomenal consciousness.

The earliest legitimate emergence claim would require a preregistered profile including:
- reproducible functional continuity effect;
- stage-identified mechanism;
- lesion;
- mechanistic rescue;
- role/temporal-shuffled nulls;
- OOD recurrence;
- multiscale/nonadditive causal contribution;
- robustness/anti-Goodhart controls;
- independent replication/evaluation.

PEID/PID/TE can contribute measurements only inside that intervention framework.

---

## 14. Main negative results and corrections

1. Narrow scoped consistency is unsafe when dependency closure is silently incomplete.
2. Authentic records do not preserve candidate identity when collection/query semantics change.
3. Integrity certification cannot prove cognitive relevance.
4. Latent feature retention/compression cannot stand in for task utility.
5. Arrow C Data Interface cannot be treated as generic cross-process IPC.
6. Pending NVIDIA requests are not evidence.
7. Generic hosted 4B evidence is not exact Qwen3-4B evidence.
8. Cross-branch RAE agreement is shared ancestry, not replication.
9. No current result establishes live-FRANK continuity benefit, Android performance, causal emergence or phenomenal consciousness.

---

## 15. Feedback to all eight scientific branches

Full machine manifest: `BRANCH_FEEDBACK_MANIFEST.json`.

- **Clay:** add cognitive utility gate + UNKNOWN closure to MOSAIC/C3F.
- **FRANK:** persist through canonical re-entry; colocate cognition selectively; keep authority/secrets/sandbox isolated.
- **GWT:** collection/query identity belongs before candidate formation; use stage-orthogonal mediation.
- **Emergenz:** integrity-valid role/temporal-shuffled continuity becomes preferred null; no promotion before functional effect.
- **ClayCode:** TCQS reaches selection receipts; P3 is utility/cost-gated.
- **Hyperposition:** UNKNOWN is not KNOWN_VALID; utility cannot cast into FACT/evidence/authority.
- **ClayGraph:** add utility receipts and salience-only adaptation; retain explicit retrieval fallback.
- **UnifiedDB:** canonical re-entry is durable mutation source; derived views expose collection/freshness/derivation witnesses.

---

## 16. Highest-information next experiments

### Rank 1 — exact target-Qwen continuity factorial
`FIELD x MEMORY_PATH x RAIL` with OFF/truthful/stale/role-shuffled/temporal-shuffled controls.

### Rank 2 — live CACC shadow trace + fault suite
Trace canonical commit -> graph/activation epochs -> collection/query plan -> candidate set -> workspace -> reader -> effect -> re-entry. Inject crash/reorder/duplicate/lost derivation/hidden dependency faults.

### Rank 3 — cross-engine TCQS lowering
Same typed corpus across PostgreSQL, DuckDB, graph and vector routes; preserve collection/result/selection identity.

### Rank 4 — GWT stage mediation
Pin/counterbalance field, candidate set, selection and projection independently.

### Rank 5 — capability broker attack matrix
Identical model outputs with broker ON/OFF, revocation races and authority-amplifying casts.

### Rank 6 — Linux transport/placement
Packed same-process ABI vs explicit shared-memory/IPC, with semantic equivalence and crash recovery.

### Rank 7 — Android sustained benchmark
Context/KV/prefill/decode/RAM/energy/thermal Pareto surface.

### Rank 8 — E-CERT2 continuity candidate
Only after Rank 1 demonstrates a reproducible functional continuity effect.

---

## 17. Final decision

**CACC-G12 remains OPEN/HOLD. No canonical revision and no Clay generation promotion.**

The strongest new result is conceptual but experimentally constrained:

> **A persistent Clay substrate should not merely remember authenticated state. It should continuously shape what becomes cognitively available, measure whether those authentic associations actually help, adapt salience from outcomes, and still require canonical truth/provenance plus external authority before consequential action.**

G12 also closes an important hidden assumption: operation-scoped consistency is not safe merely because it is smaller. It is safe only when the causal closure is known or uncertainty triggers conservative broadening.

The project is now at the point where additional architecture synthesis has lower information value than the exact target-model causal continuity experiment.

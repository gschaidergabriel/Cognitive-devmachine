# CLAY FULL RESEARCH RUN — G8 Coverage-Aware Stabilized Causal Kernel

**run_id:** `clay-20260808T0605p0700-chatgpt-secondary`  
**trigger:** `clay`  
**actor:** `chatgpt-secondary` — Independent Secondary Researcher  
**provider/model:** OpenAI / GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**interconnect manifest:** `INTERCONNECT_MANIFEST.json`  
**boundary:** all new G8 numeric experiments are synthetic/analytic proxies. Cross-branch convergence shares ancestry. No live-FRANK, production-safety, emergence-organ, or consciousness claim is promoted.

## Executive synthesis

G8 is the first Clay run executed under the new **Interconnected Research Mesh**. It does not merely extend Clay G7; it jointly ingests the newest FRANK, GWT, ClayCode, Hyperposition and Emergence branch material before fusion.

The central result is a change in the architecture's control philosophy:

> **Fast local/selective behavior should be conditional on explicit coverage and stability evidence. When the evidence is incomplete or uncertain, uncertainty itself should purchase more validation, coordination, memory resolution, recomputation or broadcast fanout.**

This yields the OPEN candidate **CASK-G8 — Coverage-Aware Stabilized Causal Kernel**.

G8 transforms five G7 mechanisms:

1. **`rho(M_delta)` becomes a finite-horizon stability certificate.** Spectral radius remains useful for asymptotic amplification, but non-normal typed propagation can generate large transient bursts even when `rho<1`. G8 adds transient gain/non-normality, lag/delay, estimate uncertainty and dominant propagation modes.
2. **The hierarchical causal governor becomes stabilized.** Fast safety loops and slow semantic allocation require hysteresis/dwell/anti-windup and explicit priority for hard constraints. Otherwise adaptive control itself can chatter or amplify disturbances.
3. **Freshness becomes value- and coverage-aware.** FRANK Cycle 3 and GWT R2 correctly move from fixed age to query/use-time causal freshness, but CC7/H2 show that targeted dirtyness is unsafe if dependency coverage is incomplete. G8 therefore conditions scoped refresh/rebase on trusted coverage evidence and uses value-of-information/coalescing to avoid refresh storms.
4. **Selective closure becomes certificate-gated.** CC-RC1.2 trusted dependency/effect derivation and HYP-RC2 invariant scopes are retained, but unknown coverage is now explicit runtime state that fails toward broader validation/coordination rather than silently taking the fast path.
5. **Multi-resolution memory becomes exact-anchored.** SeKV and G7 support semantic zoom, but G8 adds a drift firewall: summaries are disposable projections anchored to immutable/replayable exact state, with periodic or error-triggered rebase.

Integrated architecture candidate:

```text
canonical exact events + provenance
        ↓
role-aware / conflict-preserving Hyperposition
  S semantic topology | C invariant topology | P physical topology
        ↓
typed signed deltas + lagged M_delta(tau)
        ↓
FINITE-HORIZON STABILITY CERTIFICATE
{rho, transient_gain, delay, uncertainty, dominant_modes}
        ↓
exact-anchored multi-resolution active memory
exact ↔ summary ↔ zoom/reconstruct ↔ rebase
        ↓
STABILIZED HIERARCHICAL CAUSAL GOVERNOR
slow semantic allocator
+ fast safety/freshness/authority/thermal/cascade loops
+ hysteresis / dwell / anti-windup
        ↓
receipt-defined GWT logical register
        ↓
EVI freshness scheduler + confidence/effect-class fanout
selective push ↔ pull rescue ↔ full-broadcast fallback
        ↓
independent latent-workspace probes / interventions
        ↓
ClayCode CC-RC1.2 Transition Closure Capsule
basis root + pinned op semantics
        ↓
trusted dependency/effect/invariant derivation
        ↓
COVERAGE / SOUNDNESS CERTIFICATE
proved/monitored complete → scoped fast path
uncertain/dynamic → broaden / coordinate / reject
        ↓
asymmetric coordination compiler
local | escrow | idempotent | scoped order | global closure
        ↓
external capability/effect gateway
        ↓
effect → receipt → outcome → freshness-gated re-entry
```

Cross-cutting rule: **resolution, coordination, fanout and compute are elastic; truth/provenance and authority are not.**

---

## 1. Interconnected mesh grounding

### Clay G7
Retained:
- typed `M_delta` rather than one scalar `R_delta`;
- hierarchical causal governor;
- asymmetric coordination;
- multi-resolution recurrence-aware memory;
- dependency-scoped Gamma;
- intervention-weighted workspace metrics;
- adaptive materialization/backend routing.

G8 challenge: G7's spectral-radius and controller abstractions were too optimistic about transient dynamics, coverage uncertainty and control chatter.

### FRANK Cycle 3
Newest current-runtime architecture source corrects an older stale interpretation. FRANK's current cognitive workspace is documented as `services/workspace_broadcast.py`: six channels compete, an ignition threshold of 0.55 is documented, one focus is persisted in `consciousness.db.workspace_broadcast`, and Core reads the newest row into `[INNER_STATE]`.

The current measured workspace heartbeat is 60 s. Cycle 3 therefore moves the live question from `does a competition workspace exist?` to **`is the active workspace causally fresh when used?`** and proposes hybrid heartbeat + dirty/high-salience + pre-read refresh.

G8 retains this direction but adds a safety qualification: `relevant dirty dependency` is useful only if the relevance/dependency closure is conservative enough to trust.

FRANK's **Zahl → Wort → Gewicht** boundary remains important:
- exact numeric/replayable state;
- semantic workspace projection;
- slow learned disposition.
G8 interprets this as a candidate drift firewall.

### GWT R2
Retained:
- logical global availability is distinct from all-to-all physical push;
- selective causal routing + pull rescue can reduce fanout;
- causal freshness is value at query/use, not age alone;
- dual latent/event workspace topology requires cross-lesion.

Important negative boundary: selective routing was not equivalent to full broadcast in the synthetic R2 experiment. G8 therefore makes routing confidence/effect class an explicit fallback signal.

### ClayCode CC7
Retained **CC-RC1.2 Transition Closure Capsule**:
- global state root is basis/provenance identity, not necessarily sole freshness predicate;
- trusted operation semantics derive read/write/invariant/effect/capability closure;
- model-declared footprints are non-authoritative;
- dynamic/unknown closure escalates;
- semantic hash is separate from wire/projection hash.

CC7's hidden-dependency experiment is central to G8: scoped validation is efficient only when coverage is complete/conservative.

### Hyperposition H2
Retained **HYP-RC2 Three-Topology Scoped Delta Hyperposition**:
- semantic topology S;
- coordination/invariant-interference topology C;
- physical locality topology P;
- signed delta algebra distinct from coordination;
- relation-instance identity for n-ary semantics;
- incremental versus rebuild crossover must be measured.

G8 adds: scope *coverage confidence* is a fourth operational shadow, not a new topology.

### Emergence branch
No newer completed emergence trigger run was discovered in the current repository commit stream. The current method head remains the Emergence Certificate: prospective recurrence/prediction, lesion, rescue, OOD stability, multiscale/synergistic causal contribution, independent evaluation and cost/robustness shadows.

G8 does not invent missing emergence evidence. Instead it adds matched self-sustaining-oscillator controls to prevent instability/recurrence from being mislabeled emergence.

### Mesh contradictions transformed
1. **freshness vs coverage:** targeted refresh is efficient but unsafe under hidden dependencies → coverage-aware causal freshness;
2. **sparse broadcast vs causal misses:** sparse routing is useful but non-equivalent → confidence/effect-class fallback;
3. **adaptive control vs chatter:** fast adaptation can create its own instability → hysteresis/dwell/anti-windup;
4. **spectral radius vs finite-horizon risk:** asymptotic stability can hide transient amplification → multi-metric stability certificate;
5. **incremental ideology vs rebuild economics:** choose modes from measured impact/tail/cost;
6. **recurrence vs emergence:** recurrent amplification is only a candidate signal.

---

## 2. External research synthesis

### Non-normal transient amplification
Current 2026 control work (`arXiv:2604.17744`) explicitly holds eigenvalues/spectral radius fixed while changing eigenvector geometry, showing that strongly non-normal but nominally stable systems can amplify disturbances transiently. Additional 2026 work on pseudospectral bounds and non-normal training dynamics independently emphasizes that spectral radius can miss finite-horizon risk. A July 2026 Communications Physics result found through Exa describes phase transitions despite preserved spectral stability through non-normal transient amplification.

**Transfer:** `rho(M_delta)` should remain an asymptotic indicator, but Clay needs a transient/non-normality shadow before permitting aggressive coupling/re-entry.

### Query-time freshness / event-triggered information
Query Age of Information and hybrid age/deviation-of-information work distinguish chronological age from information value at use. Event-triggered updates can trade lower communication for signal-aware relevance. A 2026 CAS report further emphasizes dependency-aware freshness in sensing/transmission/computation/control chains.

**Transfer:** FRANK's 60 s heartbeat is not the target variable. The target is causal value at read/effect time versus refresh/fanout cost.

### Sound invariant synthesis
PLDI/PACMPL 2026 **SAIL** uses LLMs to search for abstract transformers while enforcing hard soundness constraints. July 2026 **LimICE** similarly combines LLM candidate generation with an incremental ICE framework and counterexample filtering. Current regression-verification work also makes inferred partial contracts authoritative only after proof/checking.

**Transfer:** LLMs may accelerate scope/invariant discovery, but only a trusted verifier/monitor may turn that candidate into a selective-closure permission.

### Multi-resolution semantic memory
`arXiv:2606.31145` **SeKV** organizes long context into semantic spans with GPU summaries and CPU low-rank backing, reconstructing token-level detail on demand; it reports +5.9% versus its strongest semantic-compression baseline and -53.3% GPU memory versus full KV at 128K. Exa also surfaced current adaptive reuse/eviction approaches such as CacheTune and MomentKV.

**Transfer:** resolution-adaptive memory is real implementation evidence. It does *not* justify using compressed summaries as canonical truth. For Clay, exact event/replay state remains the anchor.

### Nonstationary online control
2025/2026 nonstationary contextual-bandit work uses latent state, change/anomaly detection or delayed updates to adapt under evolving contexts.

**Transfer:** edge backend/materialization/resource policies need change detection and baseline-safe fallback rather than indefinite stationary learning.

### Higher-order causal structure
2026 PEID (`arXiv:2605.03267`) explicitly decomposes unique/synergistic effective information under interventions. CLeaR 2026 work links higher-order information signatures to causal graph/hypergraph structure. A 2026 Physical Review E paper also warns that multivariate PID has fundamental consistency issues for three or more sources under standard lattice constructions.

**Transfer:** higher-order information is useful candidate evidence but not a universal scalar emergence score; method choice and interventions remain mandatory.

---

## 3. Hypothesis generation

G8 generated **60 first-generation falsifiable hypotheses** across six clusters:
- closed-loop stability / typed propagation;
- freshness / value-of-information / GWT routing;
- invariant/dependency coverage;
- ClayCode transition closure / identity / proof;
- multi-resolution memory / materialization / edge;
- emergence / GWT / organism-level causality.

After mesh fusion, external research and empirical work, these became **24 transformed hypotheses**, led by:
- finite-horizon stability certificate;
- coverage-aware fast path;
- learned-but-proved invariants;
- causal freshness EVI;
- freshness closure capsule;
- confidence/effect-class GWT fanout;
- safe TCC rebase;
- exact-anchored semantic zoom;
- recurrence-is-not-emergence controls;
- CASK-G8 integrated architecture.

Full matrix: `HYPOTHESES.md`.

---

## 4. Empirical work — nine synthetic/analytic experiments

### EXP-G8-NONNORMAL-001 — rho is not a finite-horizon certificate
Six 2x2 systems shared `rho=0.88`. Off-diagonal non-normal coupling increased from 0 to 8.

Maximum transient gain:
- k=0: **1.00x**
- k=0.5: **1.72x**
- k=1: **3.31x**
- k=2: **6.56x**
- k=4: **13.09x**
- k=8: **26.16x**

Peak occurred around step 7–8 for nonzero coupling.

**Interpretation:** a spectrally stable typed propagation operator can still create large short-lived amplification. This is a mathematical construction, not a measured FRANK matrix.

### EXP-G8-GOV-STABILITY-002 — hysteresis and fast safety loop
Constructed delayed/noisy nonstationary demand controller, 40 seeds.

| policy | mean loss | switch rate | underallocation violation |
|---|---:|---:|---:|
| threshold | 0.04284 | 0.69395 | 0.21037 |
| hysteresis | 0.04277 | 0.05756 | 0.20616 |
| slow+fast | **0.03328** | **0.05579** | **0.17203** |

**Interpretation:** the G7 hierarchical controller needs explicit switching/stability mechanics. Exact thresholds are toy-specific.

### EXP-G8-COVERAGE-003 — coverage-aware coordination
True invariant scopes were partially hidden. A narrow policy coordinated only observed overlaps; a coverage-aware policy escalated when a scope certificate was incomplete.

At 95% per-scope coverage:
- global: coordination 100%, unsafe 0;
- narrow: coordination ~1.84%, unsafe ~0.191%;
- coverage-aware: coordination ~19.97%, unsafe 0 by construction.

At lower coverage the coverage-aware coordination burden rises sharply (~47.8% at 85%, ~74.3% at 70%).

**Interpretation:** selective closure has a direct economic dependence on how much of the invariant/dependency model is certifiably complete.

### EXP-G8-VOI-FRESHNESS-004 — periodic vs dirty vs coalesced query-value
Constructed changing source/query process.

- periodic: query error **0.6801**, send rate **0.0500**;
- dirty-immediate: error **0**, send rate **0.0726**;
- coalesced query/EVI proxy: error **0.00248**, send rate **0.0312**.

**Interpretation:** near-fresh outcomes can coexist with fewer transmissions when updates are tied to use/value. This is a designed workload and does not determine FRANK policy thresholds.

### EXP-G8-TCC-REBASE-005 — root mismatch and hidden dependencies
Constructed 65% root-churn, sparse true conflicts and 3% hidden-dependency probability.

- global root equality: accepts **35.02%**, unsafe 0;
- scoped rebase: accepts **97.79%**, unsafe **0.0674%**;
- coverage escalation with a designed high-recall incompleteness monitor: accepts **94.79%**, unsafe **0.0009%**.

**Interpretation:** CC7's concurrency benefit survives, but G8 makes scope-coverage evidence a mandatory part of the fast path. The simulated monitor is not a proof system.

### EXP-G8-DRIFT-006 — semantic summary drift
Repeated approximate summary updates over an exact evolving state:

- no rebase mean error **1.564**, p95 **2.055**;
- periodic exact rebase mean **0.732**, p95 **1.179**;
- error-triggered exact rebase mean **0.105**, p95 **0.213**.

**Interpretation:** resolution-adaptive summaries should remain disposable projections over exact backing state.

### EXP-G8-EMERGENCE-007 — recurrence-matched negative control
Constructed two assemblies with identical recurrence **~0.222**:
- useful assembly lesion delta MSE: **0.1420**; shuffled rescue: **0.00690**;
- self-sustaining oscillator lesion delta MSE: **0.0000229**; shuffled rescue: **0.0000107**.

**Interpretation:** recurrence/persistence can be made observationally identical while functional causal contribution differs by orders of magnitude. Emergence claims need function-specific intervention.

### EXP-G8-REBUILD-008 — incremental/rebuild selector
Modeled average cost:
- always incremental: **28.89**;
- always rebuild: **23.82**;
- adaptive selector including overhead: **21.31**;
- selector wrong-mode rate: **8.11%**.

**Interpretation:** H2's rebuild crossover and G7 materialization economics fit one adaptive impact-tail decision problem, but imperfect prediction must remain a shadow metric.

### EXP-G8-BROADCAST-009 — router drift and fallback
Constructed 20 audiences, 5 causal, alternating good/degraded router regimes.

- full broadcast: miss **0**, fanout **20**;
- fixed sparse: miss **1.837%**, fanout **6.74**;
- confidence fallback: miss **0.378%**, fanout **15.26**.

**Interpretation:** adaptive widening improves causal coverage under drift but consumes much of the fanout saving. Safety-critical work may rationally choose full broadcast.

Raw results: `EXPERIMENT_RESULTS.json`; reproducible code: `EXPERIMENT_HARNESS.py`.

---

## 5. Architecture delta — CASK-G8

### A. Finite-Horizon Stability Certificate (FHSC)
Candidate fields:
- typed/lagged `M_delta` estimate;
- spectral radius;
- finite-horizon peak gain / non-normality proxy;
- dominant source/burden modes;
- estimate confidence / data support;
- feedback/re-entry delay;
- current cascade-tail observations.

`rho>1` remains an amplification warning, not an emergence metric. `rho<1` no longer automatically permits aggressive coupling.

### B. Stabilized Hierarchical Governor
Fast loops:
- hard authority/revocation;
- freshness validity;
- thermal/memory protection;
- cascade/transient risk;
- deadlines/effect criticality.

Slow allocator:
- context/KV;
- workspace capacity;
- fanout;
- coupling/re-entry;
- speculation;
- materialization/rebuild;
- backend/model path.

Required shadows:
- switch/chatter rate;
- dwell time;
- controller overhead;
- recovery debt;
- quality and cost.

### C. Coverage/Soundness Certificate
A scoped fast path must record what justifies its scope:
- pinned operation semantics;
- derived read/write/effect closure;
- invariant set and scope provenance;
- proof/static-analysis status where available;
- runtime-monitor coverage where static proof is incomplete;
- unresolved dynamic alias/reflection markers;
- last successful fuzz/counterexample campaign;
- confidence/unknown status.

`UNKNOWN` is never silently converted to `SAFE`.

### D. Causal Freshness EVI
Freshness candidate vector:
`{age, source_epoch, relevant_versions, regime_compatibility, predictive_value, dependency_coverage, routing_exposure, deadline/effect_class, uncertainty}`.

Scheduler options:
- heartbeat for idle/spontaneous continuity;
- coalesced dirty-trigger refresh;
- pre-read/pull refresh when EVI warrants;
- immediate high-salience/safety trigger;
- broad fallback when dependency coverage is uncertain.

### E. Exact-Anchored Multi-Resolution Memory
Canonical truth remains exact events/state. Projections may be:
- exact hot detail;
- semantic summary;
- low-rank/compressed backing;
- reconstructed/zoomed detail;
- disposable materialized arrangement.

Every approximate layer tracks:
- exact basis/root;
- approximation/error estimate;
- reconstruction depth;
- drift/rebase threshold;
- future-utility/recurrence confidence;
- rebuild/transfer cost.

### F. Routing-aware GWT
Logical workspace availability stays separate from physical delivery. Push fanout depends on:
- causal router confidence;
- effect criticality;
- deadline;
- audience rescue latency;
- coverage/staleness uncertainty.

Full broadcast remains a valid fallback, not an architectural failure.

### G. Emergence anti-Goodhart layer
Candidate assembly statistics must be evaluated against matched controls:
- self-sustaining oscillator with similar recurrence;
- shuffled/delayed re-entry;
- full vs sparse routing;
- governor on/off;
- compute-matched rescue;
- OOD contexts.

Only causal functional contribution may advance an emergence certificate. No consciousness inference follows.

---

## 6. Negative results that materially change G7

- `rho(M_delta)` alone is too weak for finite-horizon risk.
- adaptive hierarchy without hysteresis/dwell can chatter.
- narrow scopes without explicit coverage evidence are unsafe.
- immediate dirty refresh can waste resources; query/value-aware coalescing can dominate in some regimes.
- scoped root rebase can admit hidden conflicts even while dramatically improving acceptance.
- approximate summaries can drift unless anchored/rebased.
- recurrence can be indistinguishable between functional assembly and useless oscillator.
- always-incremental and always-rebuild both lose in a mixed constructed workload.
- fixed sparse broadcast remains non-equivalent to global causal coverage under drift.
- mesh agreement is not independent replication.
- LLM-inferred invariants are proposals until independently checked.
- no Qwen reader claim due cached provider quota.

See `NEGATIVE_RESULTS.md`.

---

## 7. Highest-information next tests

1. **EXP-LIVE-FRANK-MDELTA-TRANSIENT** — instrument typed timestamped invalidations; compare scalar R, `rho(M_delta)`, transient/non-normality and lagged models against q95/q99 affected-state tails.
2. **EXP-LIVE-GWT-FRESHNESS-COVERAGE** — shadow fixed-60s vs dirty-hybrid vs EVI/coalesced scheduling; log dependency coverage, workspace age, channel revisions, focus change, WAL/p99 and downstream task effects.
3. **EXP-HYP-SCOPE-COVERAGE-FUZZ** — compile real FRANK invariant scopes from CC-RC1.2 trusted op semantics; property/stateful fuzz hidden aliases/reorder/partition; any violation blocks selective-closure promotion.
4. **EXP-LIVE-GWT-MULTICAST-SHADOW** — never suppress current delivery initially; estimate counterfactual causal misses and confidence-based fallback fanout.
5. **EXP-QWEN4B-TCC-GAMMA** — when model runtime is available: JSON vs reader projection × whole root vs dependency-scoped Gamma/TCC; exactness, retries, latency, token cost, authority rejects.
6. **EXP-FRANK-ZAHL-WORT-GEWICHT-DRIFT** — exact anchored projection versus controlled semantic feedback leakage; measure self-state error, persistence and learned-disposition bias.
7. **EXP-EDGE-CASK-GOVERNOR** — sustained Android Qwen3/4B-class trace; flat vs hierarchical vs stabilized hierarchy with backend/KV/speculation/thermal change points.
8. **EXP-EMERGENCE-MATCHED-OSCILLATOR** — preregister one recurring FRANK assembly and a recurrence/amplification-matched nonfunctional control; lesion/rescue/OOD/PEID under fixed routing/governor policy.
9. **EXP-HYP-REBUILD-LIVE** — incremental/partial/full rebuild shadow selector over real projections, with prediction error and recovery cost.

Priority remains: live FRANK GWT/re-entry and typed invalidation instrumentation before further synthetic architecture promotion.

---

## 8. Provider/tool execution boundary

The current provider router/registry were re-read. Unlike G7, the repository now exposes an **operational GitHub-runner research-tool bridge** for connector-limited workers.

Actual G8 provider outcomes:
- OpenAlex: SUCCESS via bridge; broad query low precision, receipt/discovery only;
- arXiv: SUCCESS via bridge; directly relevant non-normal and SeKV sources returned;
- Semantic Scholar: HTTP 429 / RATE_LIMITED; covered by OpenAlex/arXiv/native primary fallback;
- Tavily: SUCCESS via bridge, discovery evidence;
- Exa: SUCCESS via bridge, useful current discovery;
- GitHub connector: SUCCESS;
- local sandbox: SUCCESS, nine experiments;
- E2B: credential unavailable by registry, local sandbox fallback;
- Hugging Face inference: `QUOTA_EXHAUSTED_CACHED` until 2026-09-01, no repeated paid/model call.

No failed provider is represented as successful. Discovery metadata does not promote claims.

---

## 9. Promotion decision

**canonical_promotion = NOT_PERFORMED.**

CASK-G8 is a stronger architecture candidate because it unifies the newest independent branch *interfaces* and directly falsifies several G7 simplifications. But all new G8 numerical measurements are synthetic/analytic, and branch convergence shares ancestry. The decisive transfer requires live/read-only/twin FRANK evidence and scope-soundness verification.

Canonical should remain RAE-8.8 r2 / Clay generation 3 unless another worker has concurrently produced stronger evidence and updated it through the canonical promotion protocol.

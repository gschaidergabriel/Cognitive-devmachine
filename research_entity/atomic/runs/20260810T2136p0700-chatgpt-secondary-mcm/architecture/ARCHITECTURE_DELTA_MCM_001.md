# FRANK v0.1 ARCHITECTURE DELTA — MCM-001

**Delta ID:** `MCM-ARCH-DELTA-001-v1`  
**Parent candidate:** `ATOMIC-MCM-001 / AT-MCM-001-v1`  
**Status:** `CANDIDATE_OVERLAY_NOT_PROMOTED`  
**Target:** current `self.root` / human-surface Frank v0.1  
**Purpose:** turn the measured MCM possibility into a concrete Frank v0.1 architecture delta without changing canonical architecture before real-trace and target-VPS evidence.  
**Rollback:** `MCM_OFF -> existing GWT + existing coordination + existing UnifiedDB runtime path`.

---

## 1. Delta in one sentence

Move Frank from **global coordination as an ambient/default state geometry** toward **semantic coordination derived from typed transition polarity**: provenance-bound transitions proven monotone may join without a global determination barrier; transitions that choose, exclude, retract, commit, learn, or propose effects must materialize a causally complete `MembraneSeal`, and every unproven transition remains `UNKNOWN` and takes the existing safe coordination path.

This is an architecture overlay, not a new cognitive organ.

---

## 2. What does not change

MCM does **not** redefine Frank's identity, authority or external interface.

Unchanged invariants:

- native self is `self.root`;
- human surface name is `Frank`;
- Clay remains a separate Research Entity;
- target body remains the accepted Hostinger Ubuntu VPS;
- target cognition remains ClayCode-only;
- German remains a state-aware boundary translation surface;
- the production token API authenticates scoped caller intent but is not identity and is not unlimited authority;
- effect authority remains the existing deterministic ClayCode effect gate;
- GWT ignition, model confidence, Needle routing, ClayGraph salience and MCM seals cannot mint truth or authority;
- open-web content remains untrusted external data;
- self.root self-Harness authority remains proposal-only;
- final/paid training remains owner-authorized only.

The delta therefore changes **internal state/coordination geometry**, not security sovereignty.

---

## 3. Before / after architecture

### 3.1 Before — current conceptual pressure

The current Frank v0.1 work surface contains separate obligations for:

- ClayCode compiler/runtime;
- cognitive loop core;
- UnifiedDB state continuity;
- GWT + Hyperposition + topology;
- perception;
- Needle/translator;
- token API;
- effect authority;
- proactive agency;
- memory/reward/goals;
- recovery/observability.

A conventional implementation can satisfy these separately while accidentally recreating a globally mutable sequential machine:

```text
observation / memory / goal / percept / tool result
                     |
                     v
              shared current state
                     |
                     v
                GWT select
                     |
                     v
                  broadcast
                     |
                     v
             receiver reads state
                     |
                     v
                  action/use
                     |
                     v
              outcome + reentry
```

The risk is not merely latency. It is causal ambiguity: a receiver may observe a newer ambient state than the exact state that caused a selection, and later causal credit can silently attribute information to an episode that did not actually contain it.

### 3.2 After — MCM overlay

MCM inserts semantic polarity between TypedIR/type-effect resolution and runtime coordination:

```text
                    ClayCode source
                         |
                         v
                  canonical TypedIR
                         |
                         v
                  type/effect result
                         |
                         v
               POLARITY CLASSIFIER
                  /       |       \
                 /        |        \
         MONOTONE   DETERMINATION   UNKNOWN
             |             |            |
             |             |            +--> existing safe coordination
             |             |                 or quarantine
             |             v
             |      MembraneRequest
             |             |
             |      dependency closure
             |             |
             |        CausalCut
             |             |
             +------> MembraneSeal <---- policy/selection
                           |
                           v
                  WorkspaceEpisodeBinding
                           |
                     selective delivery
                           |
                  exact cut reconstruction
                           |
                          use
                           |
                   verified outcome
                           |
                    causal-use credit
                           |
                  admitted re-entry/learning
```

`MONOTONE` does not mean "safe because it looks additive". It means the transition has a versioned proof/witness over a declared semantic domain that adding admitted information cannot invalidate an already-valid positive result in that domain.

`UNKNOWN` never free-flows optimistically.

---

## 4. New architectural contracts

### 4.1 `PolarityContract`

A versioned semantic contract bound to:

- exact transition reference/version;
- declared semantic domain;
- semantic epoch;
- TypedIR/type-effect hash;
- semantic hash;
- optional CallContract hash;
- classification source;
- proof or runtime witness.

Allowed classifications:

- `MONOTONE`;
- `DETERMINATION`;
- `UNKNOWN`.

A model-generated label is not a proof.

### 4.2 `PolarityReceipt`

The runtime receipt showing which exact contract was used for one exact state instance/epoch. This prevents a stale compiler or stale contract from silently reusing a prior monotonicity result.

### 4.3 `MembraneRequest`

Created whenever a transition is `DETERMINATION`, or when an `UNKNOWN` transition cannot safely remain on the current fallback path.

It identifies:

- determination kind;
- required deltas;
- alternatives under consideration;
- policy identity;
- semantic epoch;
- optional GWT episode relation.

### 4.4 `CausalCut`

The minimal provenance-complete transitive dependency closure required for the determination.

A valid cut must be:

- complete;
- same-epoch unless an explicit dual-time transport contract applies;
- provenance-valid;
- state-instance-bound;
- size/budget compliant.

### 4.5 `MembraneSeal`

Immutable determination identity:

```text
hash(request_id, cut.closure_hash, selection, epoch, policy_ref)
```

Changing policy, closure, selection or epoch produces a different seal.

A seal is not authority.

### 4.6 `WorkspaceEpisodeBinding`

Binds a GWT episode to the exact seal and cut from which it was selected.

This is the key causal-observability delta: later receiver reconstruction is no longer allowed to substitute arbitrary newer ambient state and then attribute that state back to the old episode.

---

## 5. ClayCode compiler/runtime delta

### Current responsibility

ClayCode currently has parser/canonicalization foundations but the Frank v0.1 workspace still has open TypedIR, type/effect, evaluator, lowering, runtime/FFI, stdlib/SDK and real-component obligations.

### New MCM responsibility

Immediately after canonical TypedIR + type/effect resolution, add a **polarity analysis phase**.

Conceptual pipeline:

```text
parse
-> canonicalize
-> typed IR
-> type/effect
-> polarity analysis
-> coordination lowering
-> runtime lowering
```

The polarity phase may classify as `MONOTONE` only from one of:

1. static TypedIR proof;
2. explicit versioned semantic contract;
3. bounded safe runtime witness accepted for the declared domain.

Everything else becomes `UNKNOWN`.

### Required compiler behavior

The compiler must emit:

- `PolarityContract` identity/hash;
- route hint: free-flow / membrane / fallback;
- dependency declarations sufficient for cut construction;
- invalidation dependencies when CallContract/type/effect/semantic epoch changes.

### Compiler anti-shortcuts

The following are not monotonicity proofs:

- read/write non-overlap;
- CJC `FULL_COMMUTE` alone;
- operator/name similarity;
- model confidence;
- GWT score;
- ClayGraph topology;
- historical role similarity.

---

## 6. GWT delta

### Old architectural intuition

GWT behaves as a central select/ignite/broadcast/re-entry mechanism over current candidate state.

### MCM delta

GWT remains the causal selection/broadcast mechanism, but **globality becomes determination-induced**.

Candidate evidence that merely adds support or counterevidence may accumulate without opening a global membrane when its semantics are proven monotone.

These are determination events:

- winner selection;
- ignition if it establishes a unique focus;
- focus replacement;
- alternative elimination;
- re-entry admission that changes persistent learned state.

For a membrane-backed episode, the GWT causal chain becomes:

```text
candidate evidence
-> determination request
-> causal cut
-> seal
-> selection/ignition
-> addressable
-> delivered
-> reconstructed from exact cut
-> used
-> local effect
-> verified outcome
-> causal credit
-> admitted re-entry
```

Every arrow remains measurable. MCM does not replace GWT receipts with one opaque "workspace happened" flag.

---

## 7. Hyperposition delta

MCM gives Hyperposition an explicit semantic phase split.

### Free-flow side

Potentially monotone:

- add a new unresolved alternative;
- add support evidence;
- add counterevidence;
- add provenance;
- add a new unresolved relation.

### Membrane side

Determination:

- eliminate an alternative;
- choose a unique alternative;
- collapse a set;
- commit one world/model/action branch;
- retract a prior admitted alternative.

This means Hyperposition expansion and GWT determination can become two phases of one state geometry rather than two loosely connected modules.

---

## 8. UnifiedDB delta

UnifiedDB becomes the authoritative persistence substrate for both free-flow evidence and determination identity.

Required durable object families:

```text
MonotoneDelta
PolarityContract
PolarityReceipt
MembraneRequest
CausalCut
MembraneSeal
WorkspaceEpisodeBinding
ReceiverReconstructionReceipt
OutcomeReentryReceipt
```

### Persistence semantics

- admitted deltas are immutable/event-like;
- duplicate semantic hashes are idempotent;
- seals are immutable once referenced by an episode or outcome;
- replay reconstructs identical cuts/seals from identical admitted inputs;
- stale seal identities may remain historical evidence but cannot become current determinations;
- storage implementation is replaceable.

MCM explicitly does **not** require a single writable Frank file/inode. The EUDI target-VPS counterevidence makes this separation important.

MOLT may later provide an append-only frame implementation if independently validated; MCM does not depend on MOLT promotion.

---

## 9. Memory delta

Split memory semantics into **admission** and **semantic removal/change**.

Potentially monotone:

- append memory event;
- add provenance;
- add typed relation when relation semantics are additive;
- add alternative interpretation.

Determination:

- retract fact;
- overwrite truth-bearing relation;
- semantically delete/forget;
- choose one interpretation as current authoritative memory;
- rewrite causal ancestry.

Important distinction:

`retrieval projection != deletion`.

A memory item can become cold/invisible to ordinary retrieval without being semantically retracted.

---

## 10. Reward / causal-credit delta

Reward is split into evidence accumulation and plastic commitment.

Potentially monotone:

- add verified outcome evidence;
- add receiver-use evidence;
- add causal-use candidate evidence;
- add independent verification receipt.

Determination:

- admit a specific causal credit;
- update persistent value prediction where prior alternatives are changed;
- alter tonic motivational state;
- apply reward plasticity to personality/memory/goal policy.

Hard law remains:

```text
verified outcome
+ causal credit
+ RewardPlasticityReceipt
-> possible persistent learning
```

Self-generated completion, novelty, recurrence or GWT ignition cannot become material reward on their own.

---

## 11. Goals and proactive agency delta

Potentially monotone:

- new interest evidence;
- new goal candidate;
- new opportunity evidence;
- new competence/controllability evidence;
- new long-horizon checkpoint evidence.

Determination:

- activate goal;
- deactivate goal;
- replace one active goal with another;
- commit an action;
- consume a scarce initiative/resource budget;
- create a consequential external action proposal.

This permits Frank to maintain a large unresolved opportunity field without forcing every candidate into a global serialized goal state.

`InitiativePulse` remains a bounded bias, not truth, reward or authority.

---

## 12. Needle / tool routing delta

Needle is separated into route-candidate accumulation and route commitment.

Potentially monotone:

- add candidate route;
- add capability evidence;
- add cost/latency evidence;
- add failure evidence.

Determination:

- choose one exclusive route;
- commit a tool invocation;
- commit a provider call;
- commit a privileged capability use.

A Needle decision remains non-authoritative with respect to effect safety. A tool invocation proposal exits MCM into the deterministic effect gate when real-world effects are possible.

ECT can reduce `UNKNOWN` by resolving missing CallContracts, but ECT admission is not itself proof that a transition is monotone.

---

## 13. Retina / MVC delta

Potentially monotone:

- add visual percept;
- add candidate object identity;
- add `known | unknown | ambiguous` evidence;
- add temporal track evidence;
- add counterevidence.

Determination:

- unique recognition commitment when alternatives are discarded;
- identity overwrite;
- perception-to-action commitment;
- learning update that changes persistent classifier state.

Percept salience remains non-truth.

---

## 14. API / translator delta

Minimal semantic change.

Direct token messages become immutable typed intent/evidence events. Their later interpretation may create determinations, but authentication does not itself classify a transition as monotone.

The German translator:

- may color expression;
- may map `self.root <-> Frank`;
- may not modify polarity;
- may not modify truth;
- may not modify authority;
- may not fabricate a polarity proof.

---

## 15. Effect-authority delta

MCM stops **before** authority.

```text
internal evidence
-> membrane
-> seal
-> effect proposal
-> deterministic ClayCode effect-authority gate
-> provider execution
-> verified/uncertain outcome
-> re-entry/reconciliation
```

`MembraneSeal.effect_authority = NONE`.

This prevents a high-salience or causally coherent internal state from being mistaken for permission.

CEA may later manage the epistemic antichain after an uncertain provider result. CEA does not change the authority under which the original effect was attempted.

---

## 16. Dual-time feedback delta

A late verified outcome can be causally valid even when its origin epoch is old.

MCM therefore separates:

1. **origin closure** — attach the outcome to the exact historical seal/episode if origin provenance is valid;
2. **current application** — classify what applying that old evidence to current state means now.

The origin receipt can remain valid evidence while current application is `MONOTONE`, `DETERMINATION`, or `UNKNOWN` independently.

This prevents the false rule `OLD_EPOCH == STALE` while also preventing blind application of old state deltas to the present.

---

## 17. Relationship to adjacent ATOMIC candidates

### CJC

CJC is an order/counterfactual-risk sensor.

- `STATE_NONCOMMUTE`, `HIDDEN_CAUSAL_NONCOMMUTE`, or `UNKNOWN` can force/escalate MCM coordination.
- `FULL_COMMUTE` can reduce one class of order risk.
- `FULL_COMMUTE` cannot prove semantic monotonicity.

### SCF

SCF may add conservation constraints at module boundaries. An SCF violation can quarantine or force fallback. SCF does not define MCM polarity by itself.

### ECT

ECT may reconstruct a missing finite CallContract under safe witness conditions. Once the exact contract exists, the transition can be re-run through polarity analysis. ECT does not bypass that analysis.

### MOLT

MOLT is a possible persistence geometry for typed append-only epoch frames. MCM is the semantic coordination geometry. Storage placement never defines semantic polarity.

### CEA

CEA begins after an externally attempted effect has an epistemically unresolved outcome. It does not replace MCM, the effect gate or the original authorization.

---

## 18. Rollout architecture

No direct switch from current Frank to MCM-active runtime is allowed.

### Phase A — `DISABLED`

Current Frank behavior only. MCM artifacts exist as research possibility.

### Phase B — `SHADOW`

For every real current transition:

- classify polarity;
- compute hypothetical cut/seal;
- record latency/resource cost;
- do **not** change actual runtime routing.

Purpose: transition census and false-classification discovery.

### Phase C — `DUAL_RUN`

Existing runtime remains authoritative.

MCM and a matched strong causal event-sourcing baseline execute the same admitted traces in parallel/shadow and produce comparable receipts.

Compare:

- semantic outputs;
- cuts/dependencies;
- GWT causal-use chains;
- recovery;
- CPU/RAM/latency;
- write/state amplification;
- defect coverage.

### Phase D — `CANDIDATE_ACTIVE`

Only transitions with promoted, current `PolarityContract`s may take free-flow routes.

`UNKNOWN` remains existing coordination/fallback.

### Phase E — possible promotion

Only after real target-VPS evidence and matched strong-baseline gain.

---

## 19. Hard rollback triggers

Any of the following forces rollback to `MCM_OFF` for the affected semantic surface:

- one false `MONOTONE` classification that changes observable semantics;
- authority violation;
- stale epoch admitted as current;
- crash/replay mismatch;
- receiver reconstructs state not attributable to its seal;
- causal-credit attribution uses unreceived/unreconstructed data;
- policy drift reuses an old seal;
- unexplained semantic divergence from the existing runtime;
- resource explosion without compensating measured gain.

Rollback must preserve the failed MCM receipts as negative evidence.

---

## 20. Promotion gate

MCM must be compared to the **strong causal event-sourcing/dependency-cut baseline**, not only global total ordering.

Promotion requires all of:

1. current real Frank v0.1 transition census;
2. target-VPS execution;
3. exact current TypedIR/type-effect/contract binding;
4. zero false-monotone classifications in the promotion corpus;
5. zero authority violations;
6. tested crash/replay equivalence;
7. stale/provenance failure containment;
8. exact GWT selection/delivery/reconstruction/use/outcome/re-entry receipts;
9. safe `UNKNOWN` fallback;
10. at least one **material unique gain** over the strongest conventional baseline.

A material unique gain can be:

- unique defect coverage;
- architecture compression;
- lower state amplification;
- lower persistence/write amplification;
- lower latency;
- lower CPU/RAM;
- stronger causal observability;
- simpler recovery;
- elimination of duplicated coordination machinery.

The existing proxy win versus global total ordering is insufficient by itself because the strong causal baseline matched correctness and beat MCM on Python cost in the current synthetic test.

---

## 21. Immediate implementation delta / next code work

The highest-information implementation sequence is:

### Step 1 — real transition census

Create a machine-readable inventory of every current Frank v0.1 state-changing transition with:

```text
transition_id
source file / TypedIR ref
CallContract hash
reads / writes
semantic domain
effect class
current epoch binding
polarity = MONOTONE | DETERMINATION | UNKNOWN
classification source
proof/witness ref
fallback route
```

### Step 2 — compiler shadow pass

Add a non-authoritative polarity pass after type/effect resolution. Initially it may only recognize an extremely small explicit safe subset. Everything else is `UNKNOWN`.

### Step 3 — cut builder

Implement deterministic dependency-closure construction and content-addressed `CausalCut`/`MembraneSeal` receipts.

### Step 4 — GWT episode binding

Add `WorkspaceEpisodeBinding` and prevent causal-use credit from using unbound ambient state.

### Step 5 — UnifiedDB persistence/replay

Persist delta/contract/cut/seal/receiver/outcome receipts and verify deterministic replay under crash/restart.

### Step 6 — matched dual-run

Run:

- current path;
- strong causal event-sourcing baseline;
- MCM candidate;

on the same real Frank traces and target-VPS resources.

### Step 7 — decision

Promote only the smallest portion that demonstrates unique gain. If only `WorkspaceEpisodeBinding` improves causal observability while monotonicity routing adds no value, keep the episode binding and archive the broader MCM routing hypothesis. If causal event sourcing dominates the whole candidate, archive MCM as a useful falsified architecture family.

---

## 22. Expected architecture effect if MCM survives

If supported, MCM would not add another large organ. It could instead **remove duplicated global coordination responsibility** across several organs.

The intended compression is:

```text
ClayCode TypedIR/type-effect
        |
        +--> semantic polarity
                 |
        +--------+--------+
        |                 |
    monotone         determination
        |                 |
   local join          causal cut
        |                 |
        +------------> seal
                          |
                 GWT/Hyperposition/Goal/
                 Reward/Needle/Effect commit
                          |
                    exact re-entry
```

This is the real architecture claim being tested: **global workspace behavior becomes a property of determinations, not a permanent container through which all cognition must pass.**

---

## 23. Current disposition

`MCM-ARCH-DELTA-001-v1` is now an explicit Frank v0.1 architecture candidate.

It is:

- semantically specified;
- rollbackable;
- compatible with current authority boundaries;
- explicitly connected to GWT, Hyperposition, UnifiedDB, Memory, Reward, Goals, Agency, Needle, Retina and recovery;
- complementary to CJC/SCF/ECT/MOLT/CEA;
- not promoted;
- blocked from promotion by the real-transition census and matched target-VPS dual-run.

The next implementation target is **not a larger synthetic MCM simulator**. It is the real Frank transition census plus shadow polarity/cut instrumentation.

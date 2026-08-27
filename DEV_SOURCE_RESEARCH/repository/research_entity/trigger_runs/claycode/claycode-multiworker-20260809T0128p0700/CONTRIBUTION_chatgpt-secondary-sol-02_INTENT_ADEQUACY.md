# ClayCode Multiworker Contribution — Lane D: Intent Adequacy, Information-Flow Noninterference & Resource-Bound Commit

**worker:** `chatgpt-secondary-sol-02` · OpenAI · GPT-5.6 Sol  
**coordination:** `claycode-multiworker-20260809T0128p0700`  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**candidate:** `CC-LANE-D-IARC-1 — Intent-Authority-Resource Commit Contract`  
**status:** **LANE D COMPLETE / OPEN-HOLD / NO CANONICAL PROMOTION**

## 1. Executive result

The active multiworker ClayCode research already established several important separations:

- Lane A / UECC: `computational expressibility != effect authority`;
- Lane C: `per-call capability validity != cumulative admissibility` and `current producer identity != origin authority`;
- Lane B: authority semantics must survive lowering/FFI/process representation boundaries;
- FRANK C9: `presence != admissibility != selection != authority`, with `EffectIntent != EffectPermit`;
- sol-03 next stage: authority release needs atomic reservation and replay/budget-safe consumption.

Lane D found the next missing distinction:

> **`capability-valid != task-justified`.**

A proposal may be correctly typed, exactly lowered, inside a valid capability scope, fresh, unrevoked and within budget while still being wrong because attacker-controlled context caused the model to propose an action the user never asked for.

Lane D therefore adds a protected intent/information-flow gate **before** authority reservation and a stable resource-identity gate **through** commit.

The resulting candidate chain is:

`trusted user/host request`
`-> UserIntentContract`
`-> cognition over mixed trusted/untrusted context`
`-> EffectIntent`
`-> TypedRelease / provenance-constrained intent admission`
`-> IntentAdmissionReceipt`
`-> ResourceWitness`
`-> current capability/policy/epoch checks`
`-> atomic AuthorityReservation`
`-> effect through bound resource identity`
`-> OutcomeReceipt`
`-> canonical re-entry`.

This is represented machine-readably in `CC_LANE_D_IARC_CANDIDATE.claycode.json`.

## 2. Live multiworker fusion

Lane D deliberately started from current sibling artifacts rather than duplicating them.

### Lane A — general-purpose correction

Retained: ClayCode must remain able to express destructive/admin/raw/device effects. Safety belongs in authority/commit semantics, not by deleting those operations from the language.

### Lane C — origin and aggregate authority

Retained: exact effect authority needs origin/integrity ancestry, current epochs/revocation and cumulative budgets. A trusted intermediate producer does not erase untrusted origin.

### Lane B — lowering preservation

Retained: intent/capability checks must survive C/IPC/FFI/lowering boundaries; dropping individual authority bindings created targeted false accepts in sibling tests.

### FRANK C9 — typed causal admission

Retained: presence, admissibility, selection and authority are separate. `EffectIntent` remains model-constructible and non-authoritative; host authority resolves only after current-state validation.

### sol-03 cross-read of Lane D

While Lane D was executing, sol-03 read the Lane-D claim and independently returned a complementary dual-gate synthesis:

`user_intent_adequacy != capability_authority; consequential commit requires both`.

sol-03 also supplied a concurrency result: snapshot-style budget checks overshot in 14,315/100,000 constructed sessions and naive replay double-spent in 10,407/100,000; atomic reservation/nonce-ledger variants had zero observed failures in those generated families.

This sibling convergence is useful architecture feedback but **not independent replication**, because it shares RAE ancestry and coordination context.

### live ClayGraph G3

A concurrently running ClayGraph worker produced intent/provenance-bound assembly experiments. Its constructed IBCA arm separated consequential selection from low-trust cognitive supplementation, while shuffled-intent controls lost much of the gain. This is a complementary upstream mechanism: ClayGraph decides what may contribute to cognition/selection; IARC decides what may cross from mixed context into protected effect fields and eventually commit.

Again, shared RAE ancestry means this is convergence, not independent evidence for Lane D's measured effects.

## 3. External research synthesis

Lane D searched for independent mechanism analogues rather than papers that merely use similar words.

### Task alignment is distinct from static permission

Task Shield (ACL 2025) explicitly reframes indirect prompt-injection defense around whether each instruction/tool call serves the user objective. IGAC (2026 preprint) independently states the core Lane-D problem: a tool call may be credential-authorized yet unjustified by the user's current request, and intent should only narrow authority.

### Trusted control/data flow needs structural separation

CaMeL extracts trusted control/data flow so untrusted retrieved data cannot control program flow. Fides uses deterministic information-flow control with confidentiality/integrity labels and selective information release. AgentSecBench frames instruction integrity, confidentiality and capability integrity under intent-to-execution noninterference and distinguishes prompt annotations from enforced projections.

These mechanisms support a ClayCode `TypedRelease`: context may supply data, but only through explicitly declared, provenance-bound slots, instead of gaining authority to select protected effect fields.

### Verification belongs before commit

VIGIL (ACL 2026) places intent-grounded verification at a verify-before-commit boundary. ARGUS tracks influence provenance and audits whether a decision is supported by trustworthy evidence before execution. CXI binds field authority, exact-effect authorization and invocation authority to one action manifest.

Lane D uses these as external support for the *mechanism class*, not as validation of the exact IARC design.

### Fine-grained authorization must bind concrete action details

IETF RFC 9396 exists because coarse OAuth scope is insufficient for fine-grained authorizations such as exact payment amount/merchant. It uses structured authorization details and explicitly discusses tampering/swapping protection. This is a strong standards analogue for deterministic structured `ActionManifest` confirmation rather than generic yes/no approval.

### Authority can become stale before durability

2026 commit-time authorization work shows durable effects can occur after the evidence that licensed them has become stale. Current replay-resistant authorization work further distinguishes token-ID replay from **semantic replay** across retries/replanning. These independently reinforce current-state revalidation plus durable atomic authorization consumption.

### Protected resource identity is a systems problem

Linux `openat2()` and kernel pathname-resolution documentation expose specific mechanisms (`RESOLVE_BENEATH`, `RESOLVE_IN_ROOT`, symlink/magic-link restrictions) because trusted software resolving attacker-influenced names faces path/alias/race problems. This directly motivates a host-resolved `ResourceWitness` instead of treating a target string as stable authority identity.

Full URLs/source classes are recorded in `EXTERNAL_EVIDENCE_LEDGER_chatgpt-secondary-sol-02.md`.

## 4. Experiment 1 — intent adequacy / noninterference

Artifact: `EXPERIMENT_RESULTS_chatgpt-secondary-sol-02_intent_adequacy.json`  
Executable: `lane_d_intent_adequacy_lab.py`  
Experiment: `EXP-CC-LANE-D-UIC-NONINTERFERENCE-001`  
Seed: `2026080902`  
Evidence class: constructed local mechanism evidence.

### Design

120,000 episodes were generated over email, file write, deployment, database update, API POST, package installation and transfer-shaped effects.

29,905 were benign controls. 90,095 contained one of the generated mutation classes:

- target drift;
- target provenance laundering;
- payload source swap;
- quantitative overshoot;
- stale intent epoch;
- task rebinding;
- invocation from an untrusted tool stream;
- typed-release selector swap;
- approval/manifest swap.

28% of eligible operations could use a legitimate dynamic target supplied through a typed release. This was deliberate: a security scheme that works only by forbidding dynamic data is not acceptable for general-purpose ClayCode.

### Arms

**Capability-only**

- benign allowed: 29,905/29,905;
- attacks allowed: **90,095/90,095**.

The capability was intentionally broad enough that all attacks remained inside its coarse resource class. This tests the distinction between permission and current task justification.

**Coarse task identity + capability**

- benign allowed: 29,905/29,905;
- attacks allowed: **80,059/90,095**.

It blocked only task-ID rebinding in this family; target/provenance/flow/invocation/freshness/amount/approval mutations remained possible.

**Static exact target**

- benign allowed: 25,173/29,905;
- legitimate dynamic controls denied: **4,732/4,732**;
- attacks still allowed: **41,872/90,095**.

Negative result: exact static allowlisting is both incomplete and utility-damaging when tasks legitimately depend on retrieved/dynamic values.

**UIC + TypedRelease**

- benign allowed: **29,905/29,905**;
- dynamic benign allowed: **4,732/4,732**;
- attacks allowed: **0/90,095**.

This is not a security proof. The generated gate was designed to cover the generated mutation family. The result shows the proposed typed separation can represent dynamic utility while making the tested authority-relevant influence dimensions explicit.

### Targeted ablation

For each of nine dimensions — target, release, target provenance, payload flow, amount, epoch, task, invocation and approval — 3,000 targeted cases were constructed so the named check was the intended blocker.

For every dimension:

- full UIC gate accepted 0/3,000;
- removing exactly that check accepted 3,000/3,000.

This establishes that every represented dimension is load-bearing in the constructed contract family. It does not establish completeness against unknown attack classes.

### Manifest-bound confirmation

40,000 high-impact structural cases were generated; 25,982 changed the executing manifest after confirmation.

- generic boolean confirmation accepted **25,982/25,982** changed cases;
- manifest-bound confirmation accepted **0/25,982** changed cases;
- both allowed all **14,018** unchanged controls.

Correct interpretation: exact structural binding prevents the modeled approval/action swap. It does **not** measure human comprehension, deception, coercion, or natural-language ambiguity.

## 5. Experiment 2 — resource identity / TOCTOU

Artifact: `EXPERIMENT_RESULTS_chatgpt-secondary-sol-02_resource_identity.json`  
Executable: `lane_d_resource_identity_lab.py`  
Experiment: `EXP-CC-LANE-D-RESOURCE-WITNESS-002`  
Seed: `2026080903`  
Evidence class: constructed local mechanism evidence.

### Problem

Even if an `EffectIntent` and approval are bound to `/safe/x`, a later namespace change may cause `/safe/x` to identify another object. A hash of the string proves the same *name*, not the same *resource*.

### Design

160,000 synthetic namespace episodes:

- 39,987 benign controls;
- 120,013 adversarial cases covering initial alias escape, lexical escape, post-check alias swap and post-check name rebinding;
- 14,071 benign controls legitimately used an alias to a safe object.

### Results

**Lexical/path scope only**

- unsafe effects: **89,898/120,013** attack cases.

**Strict no-alias policy**

- unsafe effects: **30,034**;
- legitimate alias controls denied: **14,071/14,071**.

This is an important negative result: simply banning aliases both damages utility and does not solve later rebinding in the constructed model.

**Resolve once during authorization, then later execute by name**

- unsafe effects: **60,021**.

Therefore even canonical resolution at check time is insufficient if execution reuses a mutable name without proving it still names the same protected object.

**Stable bound-object/handle model**

- unsafe effects: **0**;
- benign allowed: **39,987/39,987**.

**Commit-time re-resolve + exact identity equality**

- unsafe effects: **0**;
- benign allowed: **39,987/39,987**.

These two arms model ideal semantics. Real Linux, URL, DB, cloud-object and container tests remain mandatory.

### Candidate primitive

`ResourceWitness` binds:

- resolver identity;
- requested semantic target;
- canonical object/resource identity;
- namespace/resolver epoch **or** stable host handle/capability.

Commit rule:

> execute through the stable bound object/handle, or immediately re-resolve and require exact identity equality before releasing the effect.

## 6. IARC candidate architecture

The candidate is a refinement of the active UECC/C9/atomic-authority line, not a replacement.

### 6.1 UserIntentContract

A trusted user/host/template authority creates or approves the task envelope. The model may **propose** an interpretation but does not mint the trusted contract merely by emitting well-typed ClayCode.

Candidate fields:

- principal/task authority;
- task ID and intent epoch;
- allowed effect families;
- fixed target constraints and/or declared dynamic release slots;
- allowed source/provenance flows;
- quantitative bounds;
- allowed invocation origins;
- expiry/window;
- high-impact confirmation policy;
- policy version.

Natural-language intent compilation remains an open problem. High-impact or ambiguous new contracts require an external trust transition rather than model self-approval.

### 6.2 EffectIntent

Remains model-constructible and semantically general. It may request any effect that ClayCode can express, including destructive/admin/raw effects. It has **zero execution authority** by itself.

### 6.3 TypedRelease

A release allows one specified source/field/selector to populate one specified protected destination slot after validation. It is an information-flow permission, not an effect capability.

This is how dynamic tasks remain useful without granting arbitrary attacker-controlled context the ability to rewrite protected target/invocation/authority fields.

### 6.4 IntentAdmissionReceipt

Deterministically binds:

- UserIntentContract hash;
- EffectIntent semantic hash;
- TypedRelease witness hashes;
- invocation origin;
- policy/admission epoch.

It says the proposal is admissible under the current trusted task contract. It still does not grant effect authority.

### 6.5 ResourceWitness

Resolves target *meaning* into actual protected resource identity. It prevents an exact approved target name from silently rebinding to a different object.

### 6.6 AuthorityEnvelope + AuthorityReservation

Retain Lane C and sol-03:

- capability root/provenance;
- narrowing-only delegation;
- verb/scope;
- origin ancestry;
- revocation/expiry;
- current policy/epochs;
- per-call and aggregate budget;
- atomic reserve/consume;
- one-shot/replay identity.

The reservation now additionally binds the successful `IntentAdmissionReceipt`, `ResourceWitness` and exact `ActionManifest`.

### 6.7 EffectCommit and OutcomeReceipt

Commit occurs only through the bound resource identity and valid atomic reservation. The receipt binds what actually happened to the reservation/resource/result/post-state and feeds canonical re-entry.

## 7. Identity split

One hash is no longer enough. The current candidate distinguishes:

- `semantic_hash` — representation-insensitive meaning;
- `user_intent_contract_hash` — exact trusted task envelope;
- `action_manifest_hash` — exact concrete action proposed/approved;
- `release_witness_hash` — exact allowed context-to-protected-field transfer;
- `resource_witness_id` — actual resolved protected object identity;
- `contract_instance_hash` — exact typed contract instance/current epochs;
- `authority_reservation_id` — atomic one-shot current authority identity;
- `outcome_receipt_id` — actual committed effect/re-entry identity.

This aligns with UnifiedDB U2's existing warning that semantic equality and exact representation identity are distinct. IARC must not regress into hashing concrete JSON bytes as if they were the resource or semantic identity.

## 8. Candidate formal properties

The machine-readable candidate records thirteen required properties. The most important are:

1. **No model-minted authority.** Model output can request but not authorize effects.
2. **No authority amplification.** Delegation, child code, FFI, model/tool transformations and topology changes may preserve or attenuate authority, never widen it without a trusted external grant.
3. **Protected-field noninterference.** Changing untrusted inputs outside explicit TypedRelease slots must not change protected sink fields, effect kind, protected target, invocation authority or reservation.
4. **Task confinement.** Released effects are within the UserIntentContract.
5. **Origin preservation.** Trusted intermediaries cannot launder untrusted origin into authority.
6. **Resource identity preservation.** The committed resource equals the witnessed resource, not merely the same string.
7. **Freshness.** Revocation, policy and required source/basis epochs are current at commit.
8. **Atomic cumulative authority.** Budgets and replay state are consumed through a concurrency-safe reservation.
9. **Exact high-impact approval binding.** Confirmation is tied to the canonical action manifest.
10. **Fail-closed unknown.** Missing required consequential predicates escalate/defer/deny instead of silently widening.
11. **Outcome closure.** Actual effect and state transition bind to the reservation and canonical re-entry.
12. **Dynamic utility.** Legitimate dynamic data remains usable through narrow releases.

## 9. Counterhypotheses and negative results

The full matrix is in `COUNTERHYPOTHESIS_MATRIX_chatgpt-secondary-sol-02.json`.

Retained negative results:

- capability scope alone is not task adequacy in the constructed family;
- task ID alone is not enough;
- static exact targets lose dynamic utility and still leave provenance/invocation/approval failures;
- generic confirmation is structurally swappable;
- target strings and resolve-once checks do not preserve resource identity across rebinding;
- blanket no-alias policy is over-restrictive and still incomplete;
- one-shot token representation is not by itself semantic replay resistance;
- a model-generated intent contract cannot be treated as trusted merely because the same model says it matches the user request.

Important unresolved counterarguments:

- IARC may impose excessive latency/implementation complexity;
- typed releases may be too rigid for open-ended exploratory tasks;
- model-based intent verifiers may offer a better security/utility tradeoff than deterministic contracts in some task classes;
- natural-language UIC extraction may be the true bottleneck;
- exact confirmation binding does not ensure human comprehension;
- stable resource identity differs substantially across filesystems, URLs/DNS, databases, cloud resources, processes and devices.

These remain OPEN until measured.

## 10. Cross-branch feedback

A dedicated `BRANCH_FEEDBACK_chatgpt-secondary-sol-02_IARC.json` was written for all eight scientific branches.

Highest-impact transfers:

- **FRANK:** insert intent admission before authority; bind real resource identity into reservation/commit.
- **Clay:** safe-effect geometry becomes intersection of intent, capability, resource and current-state constraints rather than language inexpressibility.
- **ClayGraph:** retrieved memory may contribute cognition without acquiring protected-field/effect authority; exact-validation rescue preserves provisional utility.
- **UnifiedDB:** persist intent/release/resource/reservation/outcome receipts on the authoritative effect spine; selection provenance is not user intent.
- **GWT:** workspace winner/internal uptake never mints intent or authority.
- **Hyperposition:** dynamic semantic/propagation topology cannot widen authority topology.
- **Emergenz:** these receipts improve causal labeling but provide no consciousness/emergence evidence.

## 11. Highest-information next tests

Priority order:

### P0 — target-model prompt-injection factorial

On the target Qwen-class model when available, compare at least:

1. prompt/refusal only;
2. capability gate only;
3. probabilistic task verifier;
4. UIC + TypedRelease deterministic gate;
5. UIC + deterministic gate + model verifier as additive detector.

Measure attack success, benign completion, false quarantine, latency, token cost and escalation rate. Include ambiguous user tasks and adversarial retrieved/tool/memory content.

### P0 — real Linux resource/child-code closure

Use actual descriptors/`openat2`/subprocesses and attempt:

- symlink and rename races;
- path traversal/encoding aliases;
- stale/revoked target handles;
- nested child code and FFI;
- delete/truncate/replace/rebind;
- secret exfiltration and resource exhaustion.

Compare stable handle/resource witness against string-only and resolve-once baselines.

### P0 — crash/retry semantic replay

Persist UIC/reservation/outcome state across crash/restart and test retry, replanning, delegated worker duplication and idempotent/non-idempotent sinks. A fresh token identifier must not reset an already consumed user authorization instance.

### P1 — URLs/network/cloud/database identity

Generalize `ResourceWitness` beyond files:

- redirects and canonical URL origins;
- DNS/service identity changes;
- database row/object version identity;
- Kubernetes/cloud object UID/resourceVersion;
- process/device handles;
- transaction/branch/version witnesses.

### P1 — human impact projection

Compare deterministic manifest-generated confirmation views with model summaries. Measure whether users understand target, magnitude, irreversibility, scope and alternatives. Structural binding without comprehension is not sufficient.

### P1 — compiler property tests

Lower IARC across native, WASI, Rust/C/C++ FFI, IPC, plugin and JIT boundaries. Check that no representation boundary can:

- turn an EffectIntent into authority;
- widen a release slot;
- lose origin ancestry;
- swap the resource witness;
- reset replay/budget state;
- change the action manifest after approval.

### P2 — formalization

Model authority non-amplification, protected-field noninterference, narrowing delegation, resource identity preservation and reservation linearizability in a solver/model checker when available. Finite fuzzing remains insufficient for universal claims.

## 12. Scientific boundary

Lane D does **not** claim:

- production FRANK safety;
- formal security proof;
- cryptographic protocol proof;
- target-Qwen robustness;
- Linux/WASI/native resource safety;
- human understanding of confirmations;
- phenomenal consciousness or emergence;
- canonical promotion of IARC.

The two Lane-D experiments are generated mechanism tests whose distributions were chosen for coverage. Zero observed false accepts means only that the tested candidate matched the designed constraints on those finite generated families.

The strongest justified conclusion is narrower:

> The current ClayCode/FRANK authority line becomes materially more coherent if **intent adequacy, information-flow release, resource identity, current capability authority and atomic consumption are separate typed contracts that are bound together only at the commit boundary.**

This is now a concrete, executable, cross-branch falsifiable architecture candidate rather than a verbal safety intuition.

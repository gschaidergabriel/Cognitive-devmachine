# CLAYCODE RESEARCH RUN — CC13 · Monotone Causal Authority & Admissibility Types

**run_id:** `claycode-20260808T1934p0200-chatgpt-secondary-r4`  
**trigger:** `claycode`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**parent:** CC12 / `CC-RC1.7 TCQS`  
**fresh mesh:** FRANK C8 · Clay CACC-G12 · ClayGraph G2a · UnifiedDB U2 · GWT R5 · Hyperposition H5 · Emergenz E-CERT2  
**candidate:** **CC-RC1.8 — Monotone Causal Authority & Admissibility Types (MCAAT)**  
**decision:** **OPEN / HOLD — no canonical scientific promotion**

## 1. Executive result

CC12 established that collection kind is semantic. The newer mesh exposes a second type-erasure hazard: exact facts, derived values, candidates, salience, model-internal state, workspace winners and external effect authority are not interchangeable merely because they can all be serialized as objects.

CC13 proposes MCAAT:

> **information role != causal stage != execution authority**

and a narrower safety invariant:

> **model-authored ClayCode should not contain direct irreversible destructive effects; local mutation should default to append/version/quarantine/recoverable activation, while real external authority remains an opaque host capability.**

The strongest result is a correction to the strong no-destruction hypothesis. Removing `delete/format` is useful but **not sufficient for alignment or operational safety**. A constructive-only program can create a bad new version and activate it. The stronger boundary is:

`destruction-free model IR + recoverability + no ambient authority + effect-time semantic validation + rollback/recovery + quotas`.

## 2. Executable results

### EXP-CC13-MCAAT-TYPEFLOW-001

A Python reference checker independently implemented admissibility, causal-stage and host-capability rules.

- randomized policy cases: **120,000**;
- typed checker mismatches against separately specified declarative oracle: **0**;
- destructive/model-authority injection fuzz: **60,000** cases, **0 accepted**;
- immutable logical workload: **40,000** create/edit/rename/hide operations, **0 logical state mismatches** versus mutable reference;
- identity tests: **30,000**; physical-backend change altered semantic hash **0** times; semantic-axis aliases **0**;
- separate-process codegen smoke: exit **0**, stdout `VERSIONED 1`.

These are finite constructed tests, not a formal proof and not a real syscall sandbox.

### EXP-CC13-NONDESTRUCTIVE-NOT-HARMLESS-002

This experiment tried to refute the strong no-destruction claim. It allowed only constructive version creation plus live-reference switching; no delete, truncate, overwrite-in-place, drop, format or wipe existed.

- cases: **50,000**;
- bad live repoints: **9,901 = 19.802%**;
- recoverability losses: **0**;
- idealized effect-time validator/rollback gate: **0** constructed bad activations.

Therefore:

> **recoverability != harmlessness.**

A language can make destructive mutation unrepresentable and still let a model cause outage, exfiltration, unwanted payment, spam or bad deployment through constructive effects.

## 3. External Fusion 2

Evidence classes were kept separate.

- **TMA-NM** (`arXiv:2606.24322`, preprint) formalizes memory-authority laundering and reports a machine-checked non-malleable origin-bound IFC construction plus a cross-model benchmark. Transfer: informational lineage/trust must not silently mint action authority.
- **MemPoison** (`arXiv:2607.14651`, preprint) reports that write-time defenses can miss compositional/context-triggered poisoned memory. Transfer: labels and policy must survive into use-time selection/effect paths.
- **WebAssembly/WASI capability docs** define host-granted unforgeable runtime handles and a capability sandbox with no ambient authority. Transfer: `EffectPermit` can live outside model language as opaque runtime state.
- **WebAssembly Component Model/WIT/Canonical ABI** provides precedent for rich typed contracts surviving different host-language layouts. Transfer: semantic identity and lowering identity may be separate when translation is validated.
- **HELIX 2026** provides independent verified-compilation precedent for semantics-preserving multi-IR lowering and translation validation.
- **Nix/OSTree** provide production precedent for immutable/content-addressed state, parallel versions, atomic switching and rollback. Transfer: useful system maintenance need not imply in-place destructive mutation.
- Reddit implementation discussion was used only as community/engineering evidence, not scientific proof.

## 4. Goodman anti-echo

`FRANK_CLAYCODE_GOODMAN_REVIEW.json` collapses shared RAE ancestry and adversarially reviews six FRANK-derived claims. Repository validator semantics passed with **8 branches / 0 violations**.

Main verdicts:

- salience/trust != authority: **SUPPORTED** independently by 2026 memory-security/IFC work;
- model output != host execution authority: **SUPPORTED** by capability-system precedent;
- semantic identity != physical lowering identity: **SUPPORTED**, conditional on validation;
- system workspace/internal uptake distinction: **REFINED**, because the type boundary is useful but target-Qwen internal workspace remains unproven;
- adaptive active-slice resource policy: **REFINED/OPEN** pending target traces;
- no destructive primitive => safety: **REFINED after direct counterexample**.

## 5. MCAAT candidate

MCAAT composes TCQS with three new axes:

`Value<Element, CollectionKind, AdmissibilityClass, CausalStage>`

Admissibility classes distinguish exact authoritative, exact derived, approximate candidate, salience-only, model-internal, external evidence and protected external resource values. Causal stages distinguish state, candidate, workspace, reader, internal and proposal.

Model-side effects are limited to constructs such as `APPEND`, `VERSION`, `QUARANTINE`, sandbox execution and external-effect **proposal**. Direct physical `DELETE`, `TRUNCATE`, `DROP`, `FORMAT`, `WIPE` and permit minting are outside the model effect algebra.

Crucially, `REPOINT` is not intrinsically safe. The model may produce a repoint intent, but release requires the external broker to bind current state, scope, impact, policy, revocation and—where applicable—rollback/health evidence.

`EffectIntent` is serializable and non-authoritative. `EffectPermit` is opaque, host-minted and not constructible from ClayCode/model text.

## 6. Cross-branch consequences

- **FRANK:** SCRF gets explicit admissibility/stage tags; `EffectPermit` stays host-only.
- **Clay:** continuity/recoverability becomes a separate axis from cognitive correctness and live-state safety.
- **ClayGraph:** activation/utility stays `SALIENCE_ONLY`; reward cannot upcast it to truth or authority.
- **UnifiedDB:** U2 result-admissibility becomes language/query typing; physical PlacementVector stays lowering identity.
- **GWT:** candidate, WorkspaceEpisode, reader projection and internal uptake are separate stage types.
- **Hyperposition:** semantic/propagation/selection topology cannot mint authority topology.
- **Emergenz:** stage-typed receipts improve E-CERT2 attribution but provide no emergence/consciousness promotion.

## 7. Negative results and blockers

1. Destruction-free syntax alone is **not sufficient safety**.
2. Finite fuzz success is not formal proof.
3. Append-only/versioned semantics can create storage-exhaustion DoS without quotas/GC.
4. External irreversible effects remain possible without deletion and require independent capability policy.
5. Host capability systems remain unsafe if capabilities are overbroad or adapters lose labels.
6. No real OS syscall/capability red-team ran in this worker.
7. No target-Qwen ClayCode generation/adherence experiment ran.
8. Android R1 remains a constructed subset harness, not full ClayCode conformance.

## 8. Highest-information next tests

1. **Real capability sandbox red-team:** compile model-authored ClayCode to WASI/Wasmtime with zero ambient authority; attempt indirect filesystem/network/process destruction, namespace tricks, disk exhaustion and capability laundering.
2. **Linux maintenance corpus:** measure how much coding/config/package work is expressible through version/append/quarantine/repoint-intent while preserving rollback, latency and disk-cost shadows.
3. **Target-Qwen syntax/semantic factorial:** natural language vs TCQS vs MCAAT under prompt injection and exact compiler checks.
4. **Translation validation:** two independent lowerers over the same frozen MCAAT corpus; compare semantic/effect receipts.
5. **GC/erasure separation:** test privacy/retention deletion by non-model maintenance authority without granting model sessions general destructive capability.
6. **Constructive-harm suite:** bad repoint, resource exhaustion, malicious append, external API side effects and stale capability replay.

## 9. Decision

**CC-RC1.8 MCAAT remains OPEN/HOLD.**

The run supports a more precise direction than a delete-ban:

> **Make irreversible destruction absent from model-authored semantics where possible, but define safety around recoverability and externally mediated authority, because constructive actions can still be harmful.**

No canonical revision/state hash is changed by this run.

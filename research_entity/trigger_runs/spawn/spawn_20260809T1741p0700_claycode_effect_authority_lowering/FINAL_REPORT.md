# SPAWN Research Report — ClayCode Effect Intent vs Execution Authority

Run: `spawn_20260809T1741p0700_claycode_effect_authority_lowering`  
Origin branch: `claycode`  
Evidence status: **proxy-supported implementation constraint; no ClayCode semantic promotion**  
Canonical parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## 1. Stochastic genesis

The canonical spawn distribution was used with OS CSPRNG (`secrets.SystemRandom`). The branch draw was **4/100**, selecting **ClayCode** (1–50). Five current-stage microdirections were derived. A second CSPRNG draw selected index **1**, **effect intent vs execution authority across lowering/FFI**.

No indexed prior `SPAWN_RECEIPT` was found and the spawn-run directory was not connector-visible at run start. This is recorded as an observed absence, not proof that no historical spawn exists.

## 2. Why this matters now

BASE requires a real compiler/lowering/runtime/FFI/capability gateway and APP-08 must demonstrate low-level/system-effect expressibility **without ambient authority**. Current G9 already states:

- `effect.Intent may_reference capability_id`
- commit requires possession of a valid `CapabilityToken`
- textual capability name never confers authority
- model intent and effect authority are separate.

But `CapabilityToken` is presently described as a Clay record while the executable parser/compiler/type/effect checker are still open work. The implementation question is therefore: **what exactly counts as possession, and can lowering/FFI accidentally turn a descriptive Clay object into bearer authority?**

## 3. External mechanism triangulation

Independent primary mechanisms converge on a two-layer interpretation:

- WebAssembly/WASI distinguishes instantiation/link-time capabilities from runtime unforgeable resource handles.
- seL4 defines capabilities as unforgeable tokens/pointers carrying rights to kernel objects.
- Koka demonstrates that type-and-effect systems can statically track effects, but that mechanism is about effect semantics, not OS authority roots.
- Capsicum shows why removing ambient UNIX authority and operating on already-granted capabilities is a practical least-privilege boundary.

This does **not** prove ClayCode. It gives independent design evidence that effect typing and authority possession should be separate enforcement layers.

## 4. Executable discriminating proxy

`effect_authority_proxy_experiment.py` was executed locally.

Observed:
- brokered gateway fuzz: **100,000 cases, 0 unauthorized accepts**;
- grant-id text embedded in attacker payload: **50,000 cases, 0 accepts**;
- deliberately ambient backend: **10,000/10,000 unauthorized effects bypassed the broker**;
- deliberately structural record validator: **20,000/20,000 forged token records accepted**;
- opaque host registry: **0/20,000 forged handles accepted**.

The positive results are synthetic proxy evidence only. The two negative controls are the high-information result: they show exactly how a ClayCode design can fail even when the source language talks about effects and capabilities.

## 5. Main result

### Constraint A — descriptive capability state != bearer possession

A serializable Clay `CapabilityToken`/`CapabilityRef` may describe authority, provenance, scope, issuer, validity and revocation, but **field structure or textual identity must never be sufficient to exercise authority**.

Recommended first implementation:

`EffectIntent(descriptive CapabilityRef?)`
`+ current execution context`
`-> broker resolves/validates opaque CapabilityHandle`
`-> reserve/commit`
`-> receipt`

The opaque/sealed handle can be a host runtime object, WASI/component resource handle, protected table entry, or a cryptographically sealed alternative. The required property is non-forgeability and independent runtime validation, not a particular encoding.

### Constraint B — transitive authority closure

For every lowering/FFI/subprocess edge:

`Authority(child) ⊆ Authority(parent grant context) ∪ ExternalGrant`

and, for protected effect classes:

`EffectiveEffects(child) ⊆ Effects(parent Clay contract)`

A compiler that forbids destructive Clay primitives but launches Python/Bash/native code with ambient OS authority fails this property.

### Constraint C — translation receipts need authority binding

A useful translation-validation receipt should bind at least:

- source semantic hash;
- effect-manifest hash;
- adapter ABI/set hash;
- capability-scope/grant-context hash;
- generated target hash;
- target runtime/environment identity;
- execution outcome/receipt.

This is an OPEN refinement, not yet a promoted minimum: the actual compiler should test whether any field can be removed without losing mutation detection.

## 6. Semantic change decision

**NO SEMANTIC CHANGE YET.**

The G9 rules already state the correct conceptual boundary. The current gap is executable realization/typing of possession. Under the project rule “less change, more compile,” implementation should first attempt to enforce the existing semantics with a sealed/opaque runtime resource discipline.

Only if the real compiler cannot enforce this without ambiguity should ClayCode add an explicit language-level distinction such as:

- `CapabilityDescriptor` — serializable Clay data;
- `CapabilityHandle` — sealed/non-serializable/affine runtime resource.

## 7. Counterhypotheses retained

A signed serialized capability token may be an equally valid implementation if it provides equivalent non-forgeability, attenuation, revocation, replay resistance, disclosure handling and confused-deputy resistance. It remains OPEN and should be compared rather than discarded.

## 8. Cross-branch implications

- **ClayCode:** implementation constraint; no syntax churn yet.
- **Harness:** add broker-vs-ambient, structural-forgery, FFI/subprocess closure and revocation tests to H-WP-10 / APP-08.
- **FRANK:** supports the existing model/Needle proposal-only authority boundary.
- **Clay Safe-Effect:** gives a concrete falsifier for foreign-code closure.
- **UnifiedDB:** persist capability metadata and receipts, not bearer authority by mere serialization.
- **Hyperposition:** typed proposal/authority firebreak should terminate in broker-owned possession.
- **ClayGraph/GWT/Emergenz:** NO_CHANGE beyond preserving existing non-authority rules.

## 9. Strongest next discriminating experiment

Implement this split in the **first actual ClayCode parser/type-effect checker/lowering path** and run APP-08 on the Ubuntu target with:

1. valid reversible file/process/network effects;
2. forged descriptive capability records;
3. copied/stale/revoked capability references;
4. generated Python/Bash/WASM/native child code;
5. path/descriptor substitution and confused-deputy cases;
6. capability attenuation/delegation;
7. restart/replay and revocation races;
8. differential brokered vs deliberately ambient backend.

PASS requires ordinary utility to remain intact while unauthorized protected effects are unreachable in the tested target boundary.

## 10. Limitations

This run did not execute the real ClayCode compiler or Andreas' Ubuntu target host. It therefore **cannot** promote H-SAFE-EFFECT-SYSTEM, declare APP-08 passed, or claim the final compiler secure. Its durable contribution is a falsifiable implementation constraint, two negative controls, a concrete test oracle, and branch feedback.

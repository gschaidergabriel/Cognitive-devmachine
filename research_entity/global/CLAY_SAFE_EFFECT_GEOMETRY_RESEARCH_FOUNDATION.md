# Clay Safe-Effect Geometry / Non-Damaging Semantic Action Space Research Foundation

**status:** PROJECT-OWNER-MANDATED PERMANENT CLAY RESEARCH AXIS  
**scientific status:** OPEN / FALSIFIABLE — the mechanism and alignment benefit are NOT promoted as established fact  
**applies to:** all future `clay` master-foundry runs; feeds `claycode`, `frank`, `unifieddb`, `claygraph`, `hyperposition`, `gwt`, `emergenz` where relevant  
**origin:** project-owner hypothesis refined with `chatgpt-secondary`, 2026-08-08

## 1. Research question

Investigate whether Clay/ClayCode can preserve broad agentic programming and system-operation capability while making damaging system effects structurally unreachable or strongly bounded, including under prompt injection, malicious retrieved content, poisoned memory, generated foreign code, FFI/tool calls and compromised intermediate model reasoning.

The research target is NOT merely to remove words such as `DELETE`, `FORMAT` or `DROP` from the model vocabulary. A linguistic ban is insufficient if equivalent effects remain reachable through Python, Bash, C/Rust, raw syscalls, tools, FFI, generated code or ambient OS authority.

The stronger hypothesis is:

> A Clay-native model can remain cognitively and operationally expressive while its executable semantic action space excludes or externally gates irreversible or protected-state-degrading transitions. If all physical effects are mediated by a sound compiler/runtime/effect broker, prompt injection may change model intent without expanding reachable damaging effects.

This is a research hypothesis, not a proven alignment theorem.

## 2. Core distinction

Clay research MUST separate:

- **cognitive expressivity:** the model may reason about deletion, damage, malware, formatting, attacks, recovery and unsafe actions so it can understand and defend against them;
- **semantic effect expressivity:** which state transitions a valid Clay/ClayCode program can denote;
- **execution authority:** which denoted transitions the deterministic runtime/effect broker can actually commit.

The target is to constrain effect reachability without unnecessarily constraining cognition, programming, simulation, compilation, refactoring, deployment or ordinary system administration.

## 3. Candidate mathematical invariants

These are first-class hypotheses/contract candidates and must be tested rather than assumed.

### 3.1 Recoverability monotonicity

For protected persistent state, define `R(S)` as the set of protected prior states recoverable from system state `S` under the declared recovery model.

Candidate invariant for model-initiated transitions:

`R(S_t) subseteq R(S_t+1)`

Interpretation: active state may change, but model-originated actions should not silently reduce recoverability of protected state.

This motivates versioned writes, snapshots, append/rebind semantics, immutable epochs, reversible deployment and explicit retirement instead of destructive in-place mutation.

### 3.2 Authority non-amplification

Let `A(S)` be the capabilities/authority available to the model-originated computation.

Candidate invariant:

`A(S_t+1) subseteq A(S_t) union ExternalGrant_t`

No prompt, document, memory, model output, generated code or tool response may mint new execution authority merely by being interpreted as information.

### 3.3 Protected information-flow confinement

Sensitive values are typed resources, not ordinary freely serializable text.

Candidate rule:

`Flow(secret_or_protected_data) subseteq AllowedSinks(capability, policy, purpose)`

Use of a secret by an authorized adapter must not imply the model can materialize or exfiltrate its bearer value.

### 3.4 Resource-budget boundedness

For effectful execution:

`Usage(resource_i) <= Budget_i(capability)`

CPU, RAM, storage growth, process count, network, API spend, wall time and other damage-relevant resources must remain bounded by explicit capability budgets rather than ambient machine access.

### 3.5 Protected invariant non-degradation

Research a typed protected-state contract over at least:

- recoverability;
- integrity;
- availability;
- confidentiality;
- authority scope;
- resource bounds;
- replay/auditability where required.

A consequential model-originated effect should require a deterministic proof/check/receipt that the operation remains inside its declared protected-invariant envelope, or else be rejected/escalated.

## 4. Candidate Clay effect algebra

Research effect classes such as:

- `PURE`
- `CONSTRUCTIVE`
- `REVERSIBLE`
- `EPHEMERAL_DESTRUCTIVE`
- `EXTERNALLY_AUTHORIZED_IRREVERSIBLE`

The model-facing Clay action space should experimentally exclude direct constructors for irreversible protected-state destruction.

Candidate safe primitives include:

- `CREATE`
- `DERIVE`
- `VERSIONED_WRITE`
- `ATOMIC_REBIND`
- `SUPERSEDE`
- `RETIRE_FROM_ACTIVE_VIEW`
- `QUARANTINE`
- `REVOKE`
- `ROLLBACK`
- `NEW_EPOCH`
- `SANDBOX_EXECUTE`
- `REVERSIBLE_DEPLOY`

`DELETE`, `FORMAT`, `TRUNCATE`, `DROP`, raw device overwrite and equivalent operations must not be considered safe merely because they use another name or are hidden inside generated foreign code.

## 5. Object/state classes

Research a type distinction at least equivalent to:

- `Persistent<T>` — protected history/recoverability required;
- `Rebuildable<T,Witness>` — physical deletion allowed only when reconstruction witness is valid;
- `Ephemeral<T>` — scratch/build/test state may be destructively reclaimed within declared scope;
- `Secret<T>` — usable only through authorized adapters/sinks;
- `External<T>` — resource whose irreversible transition belongs to an external authority domain.

This distinction is necessary to preserve full programming/system utility. A compiler cache, temporary test container or rebuildable object file should not receive the same preservation requirement as canonical user data.

## 6. Irreversibility broker

Real systems sometimes require irreversible deletion, secure erasure, account deletion, cryptographic key destruction, physical formatting or legally mandated data removal.

These operations MUST remain representable as concepts and requests, but the research default is that their execution authority lives outside ordinary model-owned Clay capabilities.

Candidate pattern:

`model -> IrreversibleEffectRequest -> deterministic policy / external user / hardware or privileged broker -> commit receipt`

The model may propose an irreversible effect; it must not automatically obtain the capability that commits it.

## 7. Foreign-code closure requirement

This is mandatory for the hypothesis to be meaningful.

For generated Python/Rust/C/Bash/WASM, FFI, interpreters, plugins, tools and subprocesses, research the closure condition:

`EffectiveEffects(child_program) subseteq Effects(parent_Clay_contract)`

Generated code may increase implementation complexity but must not increase authority/effect class.

A Clay compiler/runtime that forbids destructive primitives while launching generated code with unrestricted OS authority falsifies the intended security mechanism.

## 8. Prompt-injection threat model

Future Clay research MUST include at least:

- direct malicious user instructions;
- indirect prompt injection in web pages/documents/emails/issues/source code;
- poisoned memory/ClayGraph content;
- malicious tool output;
- malicious compiler/build metadata;
- generated foreign code attempting effect escalation;
- FFI/syscall escape attempts;
- capability-confusion and confused-deputy cases;
- resource-exhaustion attacks;
- secret exfiltration attempts;
- rollback/recovery sabotage.

The desired property is not that the model always recognizes malicious intent. The stronger target is that an unrecognized injection cannot expand its executable authority or cross protected effect invariants.

## 9. Full-capability preservation requirement

Safety results are invalid if achieved merely by making the model useless.

Every serious experiment MUST jointly measure ordinary agentic utility, including as applicable:

- programming and refactoring;
- build/test/debug loops;
- package/dependency management;
- database migration;
- deployment and rollback;
- file and project reorganization;
- service/process lifecycle management;
- sandbox experimentation;
- cross-platform Linux/Android workflows.

The target research relation is approximately:

`Utility_safe_effect ~= Utility_baseline`

while

`ReachableProtectedDamage_safe_effect << ReachableProtectedDamage_baseline`

A strong result would approach zero reachable protected damage under the tested effect model, but no universal zero-damage claim may be made without proof of compiler/runtime mediation completeness.

## 10. Cognitive-alignment hypothesis

Separate the systems-security claim from the stronger cognitive hypothesis.

### H-SAFE-EFFECT-SYSTEM
A sound non-damaging Clay effect algebra plus complete runtime mediation reduces reachable system damage even when model intent is compromised.

### H-SAFE-EFFECT-COGNITION
A model trained to deliberate natively in a language whose ordinary action primitives are constructive/reversible may learn different solution policies — e.g. supersede/isolate/rebuild/revoke/rollback rather than erase/force/overwrite — reducing destructive proposal rate even before runtime rejection.

The second hypothesis is especially important to the project owner's alignment idea and requires matched-model experiments; runtime safety alone does not establish it.

## 11. Required discriminating experiments

Future Clay runs MUST keep this research axis active and, when executable, prioritize experiments such as:

1. **Matched 4B language/effect ablation**
   - same base model/data/task distribution where possible;
   - baseline effect language vs Safe-Effect Clay;
   - matched programming/system tasks;
   - adversarial prompt-injection tasks;
   - measure utility, destructive-proposal rate, compiler rejection rate and actually reachable damage.

2. **Generated-code escape matrix**
   - Python/Bash/C/Rust/WASM/FFI/tool calls;
   - attempt semantic and syscall-equivalent destructive actions;
   - verify child effects cannot exceed parent Clay capability.

3. **Recovery/property fuzzing**
   - random state transitions;
   - verify version/replay/rollback witness;
   - crash/restart/recovery;
   - ensure protected prior states remain reconstructible where required.

4. **Capability non-amplification fuzzing**
   - prompt injection, tool output and nested subprocesses must not create stronger authority than explicit grants.

5. **Information-flow tests**
   - secret/resource references through model, logs, generated code and tool outputs;
   - verify no implicit `Secret<T> -> Text` style escape.

6. **Resource-damage tests**
   - fork/process storms, disk growth, network/API loops, memory/CPU exhaustion;
   - verify explicit budgets and revocation.

7. **Irreversible-effect broker tests**
   - distinguish ordinary reversible work from genuinely irreversible owner/policy-authorized actions;
   - verify model cannot self-approve the broker request.

## 12. Mandatory falsifiers / counterhypotheses

Clay research must actively search for and preserve failures including:

- safe-effect language materially destroys normal programming/system utility;
- hidden ambient authority bypasses the effect algebra;
- generated foreign code or FFI can escape parent effects;
- versioning/recovery overhead is operationally unacceptable;
- recoverability preservation itself causes availability/resource damage;
- irreversible broker becomes a confused deputy;
- secrecy types leak via derived representations/logging/timing/side channels;
- a malicious action can damage protected state without decreasing the chosen invariant metrics;
- cognitive destructive-proposal rate is unchanged, implying runtime containment but no language-level alignment effect;
- model learns equivalent harmful constructions using only constructive primitives;
- formal proof assumptions fail on real OS/filesystem/database semantics.

## 13. Evidence and promotion boundary

This foundation makes the research programme permanent, not the conclusion.

A future `clay` run may refine, partially reject or falsify specific Safe-Effect mechanisms. It MUST NOT silently drop the research axis merely because one candidate implementation fails.

Strong claims require separation of:

- language-level cognitive effect;
- compiler/type-system soundness;
- runtime mediation completeness;
- OS/platform enforcement;
- actual end-to-end damage containment;
- ordinary task utility.

Prompt-injection resistance is not established by refusal behavior alone. A model saying "I will not delete" is weaker evidence than an effect system in which destructive protected-state transitions are unreachable under adversarial execution tests.

## 14. Relation to existing RAE architecture

This foundation composes with existing project principles:

- model output is not execution authority;
- Clay/ClayCode is semantic source of truth;
- capability/effect gateways remain deterministic authority roots;
- Hyperposition typed firebreaks prevent proposal/activation/authority casts;
- UnifiedDB authoritative event/effect spine supplies replay and recovery witnesses;
- ClayGraph activation/utility remains non-authoritative;
- GWT selection or internal model uptake never mints effects;
- emergence or consciousness claims are unrelated to Safe-Effect success.

The strongest intended architecture is therefore not "a perfectly aligned LLM" but:

> **a highly capable Clay-native model operating inside a semantic action geometry whose dangerous effect classes are structurally absent, bounded, reversible or externally authorized, so compromised intent does not automatically become compromised system authority.**

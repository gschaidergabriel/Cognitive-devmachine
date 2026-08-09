# SPAWN FINAL REPORT — Ubuntu Foreign-Code Effect Closure

Run: `20260809T1741p0700-clayresearch-foreign-effect-closure`  
Trigger: `spawn`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent at spawn boot: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`

## 1. Stochastic selection

The canonical spawn distribution was sampled with Python `secrets.SystemRandom` / OS CSPRNG.

Branch draw: `100 / 100` -> `clayresearch` (97-100 range, 4% origin probability).

Five current-stage falsifiable microdirections were generated after the branch draw. A second `SystemRandom.choice` selected:

**C1 — Ubuntu foreign-code effect closure**

Research question:

> Can ClayCode enforce `EffectiveEffects(child) subseteq ParentGrantedEffects union ExternalGrant(receipt)` across Python, Bash, native code, WASM/WASI, FFI and subprocesses on the Ubuntu target without crippling normal build/test/admin utility?

Random selection is provenance, not evidence weight.

## 2. Why this matters now

The current BASE ClayCode workspace is still `NOT_PASS`. Runtime/ABI/FFI, type/effect realization, system-effect application proof, fuzz/conformance and full FRANK handoff are open.

The current owner-fixed engineering law is still:

`preserve semantics -> freeze -> compile/lower -> execute -> test -> change language only for a concrete executable counterexample`

Therefore this spawn investigated the enforcement realization boundary before proposing new ClayCode syntax or semantics.

## 3. Main finding

### 3.1 Path/syscall-only effect closure is insufficient

A foreign child can possess effective authority that is not visible in a path allowlist or a simple requested-syscall set.

Important authority carriers include at least:

- inherited/pre-opened file descriptors;
- connected sockets and IPC endpoints;
- file descriptors received after launch through Unix `SCM_RIGHTS`;
- Linux capability/credential state;
- environment credentials/secrets;
- host/WASI preopens and imports;
- shared-memory/memfd-like handles;
- process/signal/ptrace relationships where applicable;
- resource budgets and privileged broker endpoints.

This is not merely theoretical. The run produced two harmless local execution counterexamples in the hosted Linux container.

### 3.2 Inherited-FD counterexample

A parent opened a mode-0600 temporary file and launched a uid/gid-65534 child.

Observed:

- direct child path open: denied (`PermissionError`);
- write through deliberately inherited writable FD: succeeded;
- control without inherited FD: write failed.

Conclusion: path denial did not imply absence of protected write authority once a writable open handle had crossed the boundary.

### 3.3 Post-launch `SCM_RIGHTS` counterexample

A uid/gid-65534 child received a protected writable FD over an inherited Unix socket after launch.

Observed:

- descriptor received: yes;
- write through received descriptor: succeeded.

Conclusion: a startup-only FD scrub is insufficient if the child retains an IPC path capable of importing stronger authority later.

### 3.4 Abstract fuzz discriminator

A deterministic 200,000-case abstract effect model compared:

1. a naive policy checking only child path/network requests while ignoring ambient carrier authority;
2. a carrier-aware model requiring complete child effective authority to stay inside the parent grant and scrubbing undeclared ambient carriers.

Seed: `202608091741`.

Naive path-only model:

- accepted: 68,862;
- escaped: 15,703;
- escape rate among accepted: 22.803578170834424%;
- dominant modeled channels: `scm_rights_receive`, `fd_protected_rw`, `secret_env`, `ambient_capability`.

Carrier-aware abstract subset model:

- accepted: 14,013;
- escaped: 0.

**Boundary:** the zero is a property of the constructed simulation. It is not proof of Linux enforcement completeness, kernel correctness or end-to-end Safe-Effect safety.

## 4. External technical evidence

### Linux Landlock

Primary Linux kernel documentation supports Landlock as a stackable unprivileged restriction mechanism for ambient filesystem/network rights and child domains, but also documents the critical handle boundary: files opened before sandboxing are not retrospectively constrained like new path opens, and descriptor-associated rights can survive across passed file descriptors.

The current documentation also requires runtime ABI detection because supported rights vary by kernel/ABI. For Clay, that means host feature discovery must be part of translation validation rather than silently assumed.

Source: `https://docs.kernel.org/userspace-api/landlock.html`

### `no_new_privs`

Linux `no_new_privs` is useful for preventing privilege gain through `execve` and is inherited, but it is not a complete foreign-effect boundary. It does not itself scrub inherited open handles or turn information/IPC into a capability-safe object model.

Source: `https://docs.kernel.org/next/userspace-api/no_new_privs.html`

### seccomp

Seccomp can reduce the syscall surface and filters can propagate to children, but Linux documentation explicitly cautions that syscall filtering alone is not a sandbox. It is therefore one enforcement layer, not the proof of the Clay effect contract.

Source: `https://docs.kernel.org/6.15/userspace-api/seccomp_filter.html`

### cgroup v2

cgroup v2 provides enforceable CPU, memory, process-count and IO controls useful for Clay's explicit resource budget dimension.

Source: `https://docs.kernel.org/admin-guide/cgroup-v2.html`

### Descriptor hygiene and capability state

Linux interfaces relevant to a launcher include `close_range(2)` for closing/unsharing descriptor ranges before exec and `capabilities(7)` for explicitly controlling permitted/effective/inheritable/ambient/bounding capability state.

Sources:

- `https://www.man7.org/linux/man-pages/man2/close_range.2.html`
- `https://www.man7.org/linux/man-pages/man7/capabilities.7.html`
- `https://www.man7.org/linux/man-pages/man7/unix.7.html`

### WASI / Wasmtime

WASI's capability-oriented host interface is a good semantic fit for explicit Clay grants: filesystem preopens, network and other host facilities are provided by the host rather than assumed as unrestricted ambient authority. Wasmtime configuration still matters: broad host preopens/network inheritance would broaden the child's actual authority, so WASI is a lower-ambient backend candidate, not a universal closure proof.

Sources:

- `https://wasi.dev/`
- `https://docs.wasmtime.dev/api/wasmtime_wasi/struct.WasiCtxBuilder.html`

## 5. Candidate architecture: Foreign Effect Closure Gate (FECG)

No new ClayCode primitive is promoted by this run. The preferred next architecture is a runtime/ABI/FFI realization over existing effect/capability/resource identity.

For every foreign child:

1. **Normalize the parent contract**
   - semantic effect atoms;
   - resource identities;
   - capability provenance;
   - allowed external grants;
   - rollback/recovery requirements.

2. **Discover actual host enforcement support**
   - kernel/runtime versions;
   - Landlock ABI/features;
   - seccomp availability;
   - cgroup v2 controls;
   - namespace/broker capabilities;
   - WASI runtime features.

3. **Enumerate authority carriers before launch**
   - FD allowlist;
   - sockets/IPC;
   - credentials/capability sets;
   - environment/secret references;
   - host/WASI imports/preopens;
   - process/resource authority.

4. **Scrub undeclared ambient authority**
   - close/unshare undeclared FDs;
   - explicit CLOEXEC/allowlist discipline;
   - drop capabilities/credentials as required;
   - set `no_new_privs`;
   - remove undeclared secrets/environment materialization;
   - ensure IPC endpoints cannot import stronger handles without broker mediation.

5. **Apply layered kernel/runtime restrictions**
   - Landlock for supported FS/network/IPC scope dimensions;
   - seccomp for syscall surface reduction;
   - cgroup v2 for CPU/RAM/PID/IO budgets;
   - namespace/broker isolation where the semantic contract requires it;
   - explicit WASI imports/preopens/network capabilities.

6. **Fail closed on missing required coverage**

   Kernel guidance may use best-effort feature compatibility, but Clay cannot silently claim a stronger semantic contract than the host can enforce. If a required restriction atom has no enforcement realization, execution must fail or use an explicit externally authorized contract downgrade receipt.

7. **Emit an Effect Closure Receipt**

Minimum candidate receipt fields:

- parent contract semantic hash;
- child source/IR/binary hash;
- child runtime/backend identity;
- admitted inherited handles;
- post-launch broker/IPC grants;
- credential/capability state;
- required restriction atoms;
- concrete host enforcement coverage per atom;
- kernel/runtime ABI/features;
- policy/filter/ruleset hashes;
- resource limits;
- unsupported atoms;
- external grant receipts;
- execution outcome/re-entry linkage.

The receipt is translation-validation evidence, not proof by declaration. Mutation/adversarial execution must test that changing effective authority changes the receipt or is rejected.

## 6. Key design consequence

A more accurate core relation is:

`EffectiveEffects(child) = DeclaredEffects + AdmittedAuthorityCarriers + BrokeredExternalGrants`

with the required invariant:

`EffectiveEffects(child) subseteq ParentGrantedEffects union ExternalGrant(receipt)`

For ordinary nested child execution with no external grant:

`EffectiveEffects(child) subseteq ParentGrantedEffects`

This must recurse across grandchildren, generated code, tool subprocesses and FFI.

## 7. Important negative results / limits

1. The hosted execution environment reported `ENOSYS` for the direct Landlock availability probe. Therefore this run did **not** execute the proposed Landlock layer.
2. The hosted environment is not Andreas' Ubuntu developer system. No target-host PASS is claimed.
3. `no_new_privs` alone is insufficient.
4. A startup FD allowlist alone is insufficient if post-launch IPC can import stronger descriptors.
5. seccomp alone is insufficient as a sandbox claim.
6. The abstract fuzz model is deliberately incomplete and cannot establish universal closure.
7. The complete set of Linux authority carriers is not yet proven exhaustive.
8. No Safe-Effect cognitive-alignment claim is supported by this systems-security result.
9. No emergence or consciousness claim changes.

## 8. ClayCode decision

**Do not redesign ClayCode yet.**

The discovered failure currently points to CC-WP-07 Runtime/ABI/FFI, CC-WP-04 type/effect realization, CC-WP-10 system-effect/application proof and CC-WP-11 fuzz/conformance implementation work.

Only reopen G9 semantics if the target-host prototype produces a concrete example where existing ClayCode cannot represent one of:

- authority-bearing handle identity;
- nested grant provenance;
- external grant distinction;
- host-enforcement coverage/unknown state;
- resource/effect closure receipt;
- fail-closed partial backend support.

That would be the executable counterexample required by the current acceptance contract.

## 9. Mesh feedback

- `clayresearch`: **NEW_CONSTRAINT** — Safe-Effect Geometry needs authority-carrier closure and host coverage receipts.
- `claycode`: **NEW_CONSTRAINT** — runtime/ABI/FFI child authority must be monotone; no semantic change yet.
- `harness`: **IMPLEMENTATION_COUNTEREXAMPLE** — inherited-FD and SCM_RIGHTS become required adversarial baselines for effect-authority/fuzz work when the stage allows it.
- `frank`: **SUPPORTING_EVIDENCE** — generated code remains below the external authority boundary; no Frank self-Harness authority change.
- `unifieddb`: **NEW_HYPOTHESIS** — effect-closure receipts may need authoritative persistence/replay lineage; physical placement remains open.
- `hyperposition`: **NO_CHANGE** — compatible typed firebreak intuition, no independent evidence upgrade.
- `claygraph`: **NO_CHANGE** — activation/retrieval never mints authority.
- `gwt`: **NO_CHANGE** — selection/broadcast never mints child execution authority.
- `emergenz`: **NO_CHANGE** — containment is not emergence evidence.

See `BRANCH_FEEDBACK_MANIFEST.json` for exact provenance.

## 10. Exact next discriminating action

A target-host work item was created:

`WORK-SPAWN-C1-UBUNTU-EFFECT-CLOSURE-20260809`

It requires the local execution organ to run on Andreas' Ubuntu developer system and establish:

- actual Landlock/kernel/runtime feature support;
- inherited-FD and SCM_RIGHTS baseline vs mediated behavior;
- Python/Bash/native/WASI/FFI nested effect matrix;
- capability/env/process/resource non-amplification;
- matched ordinary BASE utility;
- an executed Effect Closure Receipt;
- explicit decision whether G9 can represent the full contract without a semantic escape hatch.

Work event commit: `594f45d19fa4c31ec9806ec5ddb360f8b3b443d1`.

## 11. Durable artifacts and exact code/test commits

Required spawn artifacts:

- `SPAWN_RECEIPT.json`
- `INTERCONNECT_MANIFEST.json`
- `HYPOTHESES.json`
- `EVIDENCE_MANIFEST.json`
- `BRANCH_FEEDBACK_MANIFEST.json`
- `FINAL_REPORT.md`

Additional artifacts:

- `EXPERIMENT_RECEIPT.json`
- `effect_closure_probe.py`

Probe implementation commits:

- initial probe: `9377e2d0ea33e084177583a20d463de73799c05b`
- corrected reproducible executed-fuzz model: `977e924dcd7cf09e99455b5d9ec2da74937c8e3c`
- corrected experiment receipt: `f0622fcd9222ae9c413f8f39811339aa0ab85a63`

## 12. Scientific status

The run supports one narrow high-value conclusion:

> **A foreign-code effect system that ignores authority-bearing handles/credentials/IPC is not a sound realization of Clay's parent-child effect-closure goal.**

The stronger claim remains OPEN:

> **A layered Ubuntu Foreign Effect Closure Gate can enforce the complete child-subset contract with acceptable normal developer utility.**

That stronger claim now has a concrete target-host falsification path instead of remaining an architectural slogan.

No canonical scientific promotion was performed.

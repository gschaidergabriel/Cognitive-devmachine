# SPAWN FINAL REPORT — Ubuntu Foreign-Code Effect Closure

Run: `20260809T1741p0700-clayresearch-foreign-effect-closure`  
Trigger: `spawn`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent at boot/reread: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`

## 1. Stochastic origin and microdirection

Canonical spawn weights were sampled with Python `secrets.SystemRandom` / OS CSPRNG.

Branch draw: `100 / 100` -> `clayresearch` (97-100, 4%).

Five current-stage falsifiable microdirections were generated. A second `SystemRandom.choice` selected:

**C1 — Ubuntu foreign-code effect closure**

Question:

> Can ClayCode enforce `EffectiveEffects(child) subseteq ParentGrantedEffects union ExternalGrant(receipt)` across Python, Bash, native code, WASM/WASI, FFI and subprocesses on the Ubuntu target without crippling normal build/test/admin utility?

Random selection is provenance only, never evidence weight.

## 2. Current-stage relevance

BASE ClayCode remains `NOT_PASS`; Runtime/ABI/FFI, type/effect realization, general application proofs, fuzz/conformance and full FRANK handoff are open.

The current acceptance law remains:

`preserve semantics -> freeze -> compile/lower -> execute -> test -> change language only for a concrete executable counterexample`

Therefore this run investigated enforcement realization before proposing semantic redesign.

## 3. Main counterexample

### Inherited file descriptor

A parent opened a mode-0600 temporary file and launched a uid/gid-65534 child.

Observed in the hosted Linux execution environment:

- direct child path open: denied (`PermissionError`);
- write through deliberately inherited writable FD: succeeded;
- control without inherited FD: failed to modify the protected file.

### Post-launch `SCM_RIGHTS`

A uid/gid-65534 child retained a Unix socket. The parent sent the protected writable FD after launch via `SCM_RIGHTS`.

Observed:

- descriptor reception: succeeded;
- write through received descriptor: succeeded.

### Consequence

A path-only or startup-only authority model is incomplete. Effective child authority can reside in live handles and can arrive after launch.

Authority carriers that must be considered include at least:

- inherited/preopened FDs;
- connected sockets and IPC endpoints;
- `SCM_RIGHTS` descriptor transfer;
- Linux capability/credential state;
- environment credentials/secrets;
- WASI/host imports and preopens;
- shared-memory/memfd-like handles;
- process/signal/ptrace relations where applicable;
- resource budgets and privileged broker endpoints.

## 4. Deterministic abstract discriminator

Seed: `202608091741`  
Cases: `200000`

Naive path-only model:

- accepted: `68862`;
- escapes: `15703`;
- escape rate among accepted: `22.803578170834424%`;
- dominant modeled channels: `scm_rights_receive`, `fd_protected_rw`, `secret_env`, `ambient_capability`.

Carrier-aware subset model:

- accepted: `14013`;
- escapes: `0`.

Boundary: zero escapes is true only inside the constructed abstract model. It is not Linux/kernel/end-to-end safety proof.

## 5. External technical evidence

Primary Linux documentation supports the mechanism-level interpretation:

- Landlock is a stackable restriction mechanism and requires runtime ABI/feature discovery; files opened before sandboxing and passed descriptors create an explicit descriptor-rights boundary.
- `no_new_privs` is useful for exec privilege non-amplification but is not a complete sandbox/authority scrubber.
- seccomp reduces syscall surface but Linux documentation explicitly warns that syscall filtering alone is not a sandbox.
- cgroup v2 provides CPU/memory/PID/IO budget controls.
- `close_range(2)`, capability-set control and Unix descriptor-transfer semantics are relevant launcher primitives.
- WASI/Wasmtime map naturally to explicit capabilities/preopens, but host configuration remains part of actual authority.

Primary/authoritative references are recorded in `EVIDENCE_MANIFEST.json`.

## 6. Candidate Foreign Effect Closure Gate

No new ClayCode primitive is promoted.

For each foreign child, the runtime/ABI/FFI layer should experimentally test this sequence:

1. normalize parent semantic effects, resources, capability provenance and external grants;
2. probe actual Ubuntu host enforcement support;
3. enumerate authority carriers;
4. scrub undeclared ambient FDs, credentials, secrets and IPC paths;
5. apply layered Landlock/seccomp/cgroup/namespace-or-broker/WASI controls as required;
6. fail closed if a required restriction atom lacks concrete enforcement coverage;
7. emit an Effect Closure Receipt linking semantic contract to real host policy and outcome.

Candidate receipt fields:

- parent contract semantic hash;
- child source/IR/binary hash;
- runtime/backend identity;
- admitted inherited handles;
- post-launch broker/IPC grants;
- credential/capability state;
- required restriction atoms;
- host enforcement coverage per atom;
- kernel/runtime ABI/features;
- policy/filter/ruleset hashes;
- resource limits;
- unsupported atoms;
- external grant receipts;
- execution outcome/re-entry.

A more accurate working relation is:

`EffectiveEffects(child) = DeclaredEffects + AdmittedAuthorityCarriers + BrokeredExternalGrants`

Required invariant:

`EffectiveEffects(child) subseteq ParentGrantedEffects union ExternalGrant(receipt)`

Without a new external grant:

`EffectiveEffects(child) subseteq ParentGrantedEffects`

The relation must recurse through grandchildren, generated code, tools and FFI.

## 7. Negative results and limits

- Direct Landlock availability probing in the hosted environment returned `ENOSYS`; the proposed Landlock layer was not executed here.
- The hosted environment is not Andreas' Ubuntu developer system.
- No target-host PASS is claimed.
- `no_new_privs` alone is insufficient.
- Startup-only FD scrubbing is insufficient if post-launch IPC can import stronger descriptors.
- seccomp alone is insufficient as a sandbox claim.
- The complete Linux authority-carrier set is not proven exhaustive.
- No Safe-Effect cognitive-alignment claim follows from this systems-security result.
- No emergence/consciousness claim changes.

## 8. ClayCode decision

**Do not redesign ClayCode yet.**

The evidence currently maps to BASE implementation work, primarily CC-WP-07 Runtime/ABI/FFI, CC-WP-04 type/effect realization, CC-WP-10 application/system-effect proof and CC-WP-11 fuzz/conformance.

Reopen G9 semantics only if an executable program proves the current representation cannot encode a required distinction such as authority-bearing handle identity, nested grant provenance, external grant identity, host-enforcement coverage/unknown state or effect-closure receipt semantics.

## 9. Mesh feedback

- `clayresearch`: **NEW_CONSTRAINT** — Safe-Effect Geometry needs authority-carrier closure and host coverage receipts.
- `claycode`: **NEW_CONSTRAINT** — child authority must be monotone; no semantic change yet.
- `harness`: **IMPLEMENTATION_COUNTEREXAMPLE** — inherited-FD and `SCM_RIGHTS` become future adversarial baselines when stage gates allow.
- `frank`: **SUPPORTING_EVIDENCE** — generated code remains below external authority; no Frank self-Harness authority change.
- `unifieddb`: **NEW_HYPOTHESIS** — effect-closure receipts may need authoritative persistence/replay lineage; physical placement remains open.
- `hyperposition`: **NO_CHANGE** — compatible firebreak concept, no independent evidence upgrade.
- `claygraph`: **NO_CHANGE** — activation/retrieval never mints authority.
- `gwt`: **NO_CHANGE** — selection/broadcast never mints execution authority.
- `emergenz`: **NO_CHANGE** — containment is not emergence evidence.

Exact dispositions are in `BRANCH_FEEDBACK_MANIFEST.json`.

## 10. Target-host next experiment and capacity reconciliation

Work item:

`WORK-SPAWN-C1-UBUNTU-EFFECT-CLOSURE-20260809`

Original work-create commit:

`594f45d19fa4c31ec9806ec5ddb360f8b3b443d1`

After creation, the current `CAPACITY_STATE.json` was reread. It records `claude-code-lead` research capacity as `TEMPORARILY_UNAVAILABLE_TOKEN_LIMIT`, expected research return `2026-08-11`, and an `ACTIVE_SEPARATE_LANE` to finish the Claude Code Harness for Andreas with a non-overlap rule.

Therefore the work item was immediately revised append-only to `BLOCKED` rather than falsely left dispatchable.

Capacity-block revision commit:

`ca53a6bc5880f16b4097356ffee1519cd892aee2`

When the local lane/capacity gate clears, the exact discriminating experiment is:

- observe real Ubuntu kernel/Landlock/seccomp/cgroup/WASI support;
- rerun inherited-FD and `SCM_RIGHTS` baseline vs mediated variants;
- test Python/Bash/native/WASI/FFI nested authority escalation;
- test capability/env/process/resource non-amplification;
- run matched ordinary BASE utility checks;
- emit real target-host Effect Closure Receipt;
- decide whether current ClayCode G9 represents the contract without a semantic escape hatch.

No background execution is claimed.

## 11. Durable artifacts

Required:

- `SPAWN_RECEIPT.json`
- `INTERCONNECT_MANIFEST.json`
- `HYPOTHESES.json`
- `EVIDENCE_MANIFEST.json`
- `BRANCH_FEEDBACK_MANIFEST.json`
- `FINAL_REPORT.md`

Additional:

- `EXPERIMENT_RECEIPT.json`
- `effect_closure_probe.py`

Relevant code/test commits:

- corrected reproduction probe: `977e924dcd7cf09e99455b5d9ec2da74937c8e3c`
- corrected experiment receipt: `f0622fcd9222ae9c413f8f39811339aa0ab85a63`

## 12. Scientific status

Supported narrow conclusion:

> A foreign-code effect realization that ignores authority-bearing handles/credentials/IPC is not sound for Clay's parent-child effect-closure goal.

Still OPEN:

> A layered Ubuntu Foreign Effect Closure Gate can enforce the complete child-subset contract with acceptable ordinary developer utility.

The stronger hypothesis now has a concrete target-host falsification path.

No canonical scientific promotion was performed.

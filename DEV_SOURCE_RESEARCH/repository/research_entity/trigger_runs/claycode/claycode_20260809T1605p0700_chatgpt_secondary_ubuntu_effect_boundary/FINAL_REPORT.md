# ClayCode Trigger Run — Ubuntu Effect / Capability Boundary

Run: `claycode_20260809T1605p0700_chatgpt_secondary_ubuntu_effect_boundary`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Frank v0.1 target: **Ubuntu Linux developer system only**

## Owner scope correction integrated

During this trigger run the project owner fixed the v0.1 target host more narrowly than older cross-platform research language:

- target: Ubuntu Linux developer system;
- Android/mobile/generic edge research: out of scope for Frank v0.1;
- non-Ubuntu portability: not a v0.1 release gate unless explicitly reopened later.

This was persisted in `research_entity/global/FRANK_V0_1_UBUNTU_TARGET_HOST_DIRECTIVE.md`, referenced by `RAE_LATEST_COGNITIVE_STACK.clay`, and reflected in `CLAYCODE_RELEASE_WORKSPACE.json`.

## Question tested

Can the current ClayCode G9 `CapabilityToken` + `EffectIntent` design be realized as an Ubuntu/Linux effect boundary without adding new ClayCode semantics?

The discriminating requirement is stronger than representability: model/source text must not mint execution authority, and a narrower capability must actually reduce what the executed process can access/do.

## Result

**Preliminary result: yes, existing semantics remain adequate; implementation/lowering must become concrete. No semantic language change is justified by this run.**

A Linux executable probe demonstrated:

1. ordinary unsandboxed execution retains ambient filesystem authority;
2. a user+mount namespace with a minimal chroot and one read-only bind-mounted resource allowed reading that resource while blocking writes and unrelated filesystem paths;
3. removing the resource bind narrowed the capability to no resource access;
4. Landlock ABI probing returned `ENOSYS` in the current container, so Landlock cannot be assumed as the only backend.

This directly supports the architecture distinction:

`CapabilityToken / EffectIntent = semantic proposal + auditable authority reference`

`host capability table + Linux enforcement = actual authority`

`effect receipt = verified outcome re-entry`

## Executable evidence

Environment used for this run:

- Debian GNU/Linux 13 container;
- Linux kernel surface 6.18.35 x86_64;
- gcc available;
- this is Linux mechanism evidence, **not final Ubuntu developer-system acceptance evidence**.

Key observed matrix:

| Case | Allowed read | Allowed write | Ambient `/etc/passwd` |
|---|---:|---:|---:|
| unsandboxed baseline | ALLOW | ALLOW | ALLOW |
| read-only capability mount | ALLOW | DENY (`EROFS`) | DENY |
| narrowed/empty capability | DENY | DENY | DENY |

Landlock probe:

- call: `landlock_create_ruleset(... LANDLOCK_CREATE_RULESET_VERSION)`;
- observed: `Function not implemented` / ENOSYS;
- consequence: runtime backend probing/fallback is mandatory.

Artifacts:

- `EXECUTABLE_RESEARCH_RECEIPT.json`
- `ubuntu_effect_boundary_probe.sh`
- `HYPOTHESES.json`
- `NEGATIVE_RESULTS.jsonl`

## External triangulation

Independent primary-source checks support the refined design:

- Linux kernel Landlock documentation defines Landlock as an unprivileged mechanism to restrict ambient rights and as a stackable LSM.
- Linux mount/user namespace documentation establishes isolated mount views and isolated security identifiers/capabilities.
- Ubuntu documentation states AppArmor is installed/loaded by default and confines applications with program profiles/capability rules.
- WASI capability documentation treats runtime capabilities as unforgeable handles; WIT resources distinguish owned and borrowed resource handles.

These sources support handle-based/external enforcement but do not prove ClayCode's final Ubuntu implementation.

## Goodman anti-echo verdict

FRANK P10 and ClayCode G9 share ancestry, so their agreement was not counted as independent support.

Verdict for the external authority boundary: **REFINED**.

Independent evidence plus the new executable counterexample supports the core rule, while the backend assumption is narrowed:

- retain opaque host-minted capability identity;
- retain `EffectIntent` as proposal, not authority;
- retain release-time scope/revocation/basis revalidation;
- realize authority through a runtime-probed Ubuntu/Linux backend set;
- do not encode AppArmor/Landlock/namespaces as cognitive authority primitives.

Review: `FRANK_CLAYCODE_GOODMAN_REVIEW.json`.

## Candidate Ubuntu lowering

Recommended BASE implementation contract:

1. ClayCode program/model emits or constructs `EffectIntent` referencing an opaque `capability_id`.
2. Type/effect checker verifies the requested effect class is representable and requires a capability of the right semantic type.
3. Host runtime resolves `capability_id` in a non-model-authoritative capability table.
4. Host revalidates issuer, delegate, verb set, resource identity, scope, validity, revocation, basis/source epoch, recovery and idempotency.
5. Ubuntu lowering selects an enforcement backend:
   - typed FD/handle passing for individual resources;
   - user/mount namespaces plus explicit resource injection for isolated processes;
   - read-only/bounded mounts where appropriate;
   - AppArmor as an Ubuntu-native outer confinement layer where useful;
   - Landlock only when runtime-supported;
   - seccomp/no_new_privs for syscall reduction where appropriate.
6. Execution produces a receipt bound to intent, capability, backend plan, process/result and observed outcome.
7. Receipt re-enters UnifiedDB/GWT/ClayGraph as evidence; none of those layers may convert graph activation or model output into authority.

## Cross-branch feedback

- **FRANK:** P10 survives but becomes explicitly backend-plural on Ubuntu. Opaque permits and no ambient authority remain hard requirements.
- **Clay:** current mission is now Ubuntu v0.1 only; Android/mobile/edge work is removed from the active path.
- **Harness:** APP-08/H1-H3 need exact Ubuntu developer-system sandbox/effect Golden Traces, including denial cases, revocation, crash/restart and idempotency.
- **ClayGraph:** capability/effect edges may be observed, but activation/salience cannot authorize execution.
- **UnifiedDB:** capability identity, authority scope, semantic transaction/idempotency and effect receipt should share stable IDs/epochs without turning storage presence into permission.
- **GWT:** selection/broadcast/use remains distinct from authorization/execution; effect outcome returns as a receipt.
- **Hyperposition:** physical sandbox placement may vary while semantic authority relations remain invariant and measurable.
- **Emergenz:** no emergence claim follows from sandbox/compiler success.
- **ClayCode:** concentrate next work on CC-WP-04/06/07/10/11 rather than new language primitives.

## Hypotheses / negative results

- `H-CC-UBUNTU-CAPHANDLE-001` — OPEN_SUPPORTED_PRELIMINARY: current capability/effect semantics can lower to Ubuntu host handles/enforcement without semantic change.
- `H-CC-UBUNTU-LAYERED-SANDBOX-002` — OPEN: layered Ubuntu enforcement is more robust than one mandatory backend.
- `H-CC-AUTHORITY-METADATA-NULL-003` — REFUTED as an enforcement model: metadata alone does not remove ambient OS authority.
- `N-CC-LANDLOCK-AVAILABILITY-20260809` — NEGATIVE_RESULT: do not assume Landlock runtime availability.
- `N-CC-CAPABILITY-METADATA-ONLY-20260809` — NEGATIVE_RESULT: semantic capability records are not enforcement.

## Release implication

No BASE work package is marked complete by this run. The result is a concrete implementation constraint and executable mechanism probe, not a compiler/runtime release.

Highest-information next step on the **actual Ubuntu developer system**:

1. probe exact Ubuntu/kernel/AppArmor/Landlock/userns/seccomp capability surface;
2. implement the first real `CapabilityToken -> Ubuntu SandboxPlan` lowering in the ClayCode runtime;
3. compile/execute APP-08 positive + denial + revocation + narrowed-delegation tests;
4. persist exact receipts;
5. then use the same ABI for the first real FRANK effect path.

Android/mobile/edge validation is intentionally absent.

## Protocol limitations

The official interconnect preflight remains fail-closed blocked because the current registry uses `clayresearch` while `tools/research_interconnect_preflight.py` still hard-codes `clay`. A manual fail-closed manifest covering all nine scientific branches was committed. No strong semantic promotion is claimed.

E2B was not exposed in this session; executable evidence used the local Linux container and is labeled accordingly. Goodman validator was not run because there is no local repository checkout; the review is committed for replay before any strong promotion.

## Final synthesis

This run moves ClayCode forward by **reducing uncertainty about implementation, not by enlarging the language**. The present G9 capability/effect semantics are sufficient as the candidate contract. Frank v0.1 should now build one concrete Ubuntu-native authority gateway around them, with opaque host handles, narrow resource injection, runtime backend probing and deterministic receipts.

That is the shortest path from current research semantics toward an actually executable Frank v0.1 on the Ubuntu developer machine.

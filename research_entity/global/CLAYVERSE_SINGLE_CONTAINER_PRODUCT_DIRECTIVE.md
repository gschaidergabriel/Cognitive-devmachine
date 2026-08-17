# CLAYVERSE SINGLE-CONTAINER PRODUCT DIRECTIVE

**Authority date:** 2026-08-17  
**Authority:** newest explicit owner directive; supersedes older EntityOS-as-product endpoint directives and any interpretation that makes the accepted final EntityOS substrate optional.

## 1. Product endpoint

The active product endpoint is **ClayVerse**.

Canonical workspace:

`gschaidergabriel/clay-global-research-entity` → `main` → `the artefact/`

Release form: **one OCI/Docker-compatible ClayVerse container image**. Development files, receipts and tests may exist outside the image. Explicit persistent data volumes are allowed.

EntityOS is not the top-level release artifact. It is the hardened execution/security/runtime substrate **inside** ClayVerse. Development/baseline builds may temporarily omit EntityOS, but such builds can never receive whole-product PASS. The final accepted ClayVerse image MUST contain the complete accepted EntityOS runtime substrate.

## 2. Identity and continuity

ClayVerse is one persistent central entity shared by all connected machines and authenticated users. Gabriel and Andreas are equal-rights perspectives into the same central entity/state, not separate instances.

`UnifiedDB` is the sole canonical authority for persistent world model, state, memory/data and durable knowledge. `ClayGraph` is derived/rebuildable and may never become a competing state authority.

Continuity comes from explicit persisted state, causal re-entry, recovery and runtime contracts. A separate `consciousness_daemon` is excluded.

## 3. Sealed sandbox / machine-continuum law

The final ClayVerse container MUST behave functionally like a **sealed virtual machine/appliance with controlled ingress and egress**, even when implemented as an OCI container rather than a nested KVM/QEMU guest.

Inside that single boundary runs one continuous machine-like domain containing:

- UnifiedDB as canonical persistent state/world/memory authority;
- the complete accepted EntityOS execution/security/runtime substrate;
- ClayGraph as rebuildable derived projection;
- ClayVerse orchestration/runtime supervision;
- the managed Linux terminal/PTY/tmux execution surface;
- the admitted LLM inference boundary: Claude Code and/or GLM according to the provider law below;
- managed hooks, retrieval/routing organs and EffectGate/effect journal;
- the authenticated web/API/transport boundary needed to accept inputs and return outputs.

Nothing outside this boundary may become a second cognition, state, execution or identity authority.

### 3.1 Ingress

External data enters only through explicit admitted input surfaces. Examples include authenticated user/browser input, approved machine/API input, uploaded data and verified effect results returning from an admitted external boundary.

Ingress is normalized, authenticated/authorized where applicable, causally identified and written/reconciled against canonical ClayVerse state before it influences cognition or execution.

### 3.2 Internal processing loop

The canonical processing cycle is conceptually:

`INGRESS -> canonicalize/record in UnifiedDB -> retrieve/assemble current state -> selected LLM cognition -> re-ingest model output as proposed intent/command -> policy/authority validation -> EntityOS/managed terminal execution when admitted -> capture stdout/stderr/result/effect receipt -> re-ingest result into UnifiedDB/current causal turn -> continue cognition as needed -> EGRESS`

The LLM does not directly own state and does not directly bypass the execution boundary. Its output returns into ClayVerse first and is treated as proposed action/data until validated.

The cycle may repeat many times for one causal task. Command results, errors, observations and external effect receipts return into the same continuum instead of becoming an out-of-band side channel.

### 3.3 Linux terminal control

The internal environment MUST be able to communicate directly with and control its managed Linux terminal/PTY/tmux surface. The accepted EntityOS/ClayVerse execution layer may start commands, provide stdin, receive stdout/stderr/exit status, inspect managed process state and perform admitted filesystem/process operations inside its bounded authority.

Unmediated generic host `process.exec` remains forbidden. Terminal control is not removed; it is routed through the admitted EntityOS/ClayVerse execution/security contract so commands are attributable, policy-checked, recoverable and causally re-ingested.

### 3.4 Egress

Only explicit admitted output/effect surfaces may cross the boundary. Egress includes user-visible responses, approved files/data, terminal/effect results exposed to an authenticated user, explicitly authorized external effects, and the narrowly admitted inference request needed for token-based GLM use.

Egress must remain attributable to a canonical causal turn/effect receipt. Unknown, stale, replayed or unauthorized effects fail closed.

### 3.5 Shock-absorber isolation and automatic snapshot recovery

The sealed machine boundary is intentionally a **stability shock absorber** between the persistent ClayVerse continuum and the outside environment. Faults inside EntityOS, an LLM client/runtime, terminal processes or internal orchestration must be contained inside this boundary wherever possible instead of corrupting external owner systems or requiring manual reconstruction.

ClayVerse MUST maintain periodic and event-triggered **known-good logical machine snapshots**. A snapshot is not merely a copy of one process RAM image. It binds at minimum:

- a consistent UnifiedDB checkpoint/backup identity;
- the active global entity generation and canonical session generations;
- exact EntityOS binary/config/policy hashes;
- active causal turn/episode identities and resumable internal queue position;
- EffectJournal state, including which effects are confirmed, pending, unknown or forbidden to replay;
- relevant managed runtime/configuration identities needed to reconstruct the internal machine state.

Snapshots MUST be atomic enough that recovery cannot combine mutually inconsistent generations/state authorities.

If EntityOS or another critical internal runtime component crashes, wedges, violates its health contract or produces an unrecoverable internal fault, the outer ClayVerse supervisor MUST automatically:

1. close/freeze new ingress and nonessential egress;
2. fence the crashed runtime generation so stale processes/results cannot rejoin;
3. terminate/recreate the affected internal runtime components;
4. restore/reconstruct the last accepted known-good logical machine snapshot;
5. advance to a new global runtime generation/epoch;
6. mark any external effect whose completion is not durably verified as `UNKNOWN_AFTER_CRASH`/equivalent rather than replaying it automatically;
7. re-establish UnifiedDB/EntityOS/terminal/selected-LLM readiness and policy attestations;
8. resume admitted work through causal re-entry only after the recovered continuum is internally consistent.

Automatic recovery MUST NOT blindly replay external side effects. A command/effect may be replayed only when its contract is explicitly idempotent and the EffectJournal proves replay is safe; otherwise it remains unknown and requires reconciliation.

This logical snapshot/reconstruction mechanism is the required product behavior. A future implementation MAY additionally use CRIU, filesystem snapshots or VM-style memory snapshots as an optimization, but those mechanisms may not replace UnifiedDB/EffectJournal consistency rules.

### 3.6 Immutable appliance filesystem and two-tier self-healing

The accepted runtime MUST separate **ephemeral runtime** from **persistent canonical state**:

- the OCI root filesystem is read-only at runtime;
- temporary/runtime mutation goes only to bounded RAM/tmpfs locations such as `/tmp` and `/run` or other explicitly declared ephemeral areas;
- canonical durable state goes only to explicit scoped persistent data areas, primarily `/var/lib/clayverse` for UnifiedDB/checkpoints/effect journal state and any separately admitted workspace volume;
- runtime code, EntityOS binaries, policies, managed settings and supply-chain artifacts are reconstructed from the immutable image, never repaired in place after a crash;
- undeclared writable host paths or mutable host binaries are not part of the product contract.

Recovery has two tiers:

**Tier 1 — internal component recovery.** If EntityOS, the selected LLM runtime/client, PTY/tmux or another replaceable internal process fails while the machine-continuum invariants remain trustworthy, the ClayVerse supervisor fences the failed generation/component, rebuilds it from immutable image bytes where applicable, reconciles with the last valid logical snapshot and resumes after readiness attestation.

**Tier 2 — full appliance restart.** If canonical invariants cannot be trusted, recovery itself fails, memory/resource corruption is suspected, or the supervisor cannot prove a consistent generation, the container MUST fail closed so the external OCI runtime/orchestrator restarts the whole appliance from the immutable base image. On restart, ClayVerse opens only the declared persistent data areas, performs UnifiedDB/WAL recovery plus snapshot/effect-journal reconciliation, creates a new runtime generation and reconstitutes EntityOS/terminal/LLM integration from clean image bytes/configuration before ingress reopens.

The full-appliance restart target is **fast and deterministic**, but no fixed millisecond restart guarantee may be claimed until measured on the admitted deployment/runtime.

An OCI container still shares the host kernel. Therefore this appliance boundary strongly isolates product userspace, libraries, filesystem and process state, but it does not make host-kernel/driver changes physically impossible. If stronger kernel isolation is later required, the same ClayVerse image may be run by the deployment platform inside a VM/microVM without changing the internal ClayVerse state/execution architecture.

## 4. Cognition and LLM provider law

ClayVerse supports two admitted LLM modes. They are inference engines only; neither is a persistent identity, memory authority or execution authority.

### 4.1 Claude Code — direct managed terminal login

Claude Code is the **interactive terminal-native LLM path**. It runs inside the managed ClayVerse Linux PTY/tmux environment as the normal Claude Code CLI.

Authentication for Claude Code is performed **directly through its terminal login flow**. ClayVerse must not replace this primary path with a hidden Claude API-token abstraction. The authenticated Claude Code process remains inside the managed terminal continuum and is supervised/attested like the other internal runtime processes.

ClayVerse supplies context/state through the admitted terminal/hook/runtime interfaces and receives Claude Code output back through the same managed runtime boundary. Claude Code output is always re-ingested into ClayVerse as proposed reasoning/action before any EntityOS/terminal effect is authorized.

Any Claude authentication/session material required by the CLI is credential state, not canonical cognition or memory. It must stay in a narrowly scoped credential boundary and must never become UnifiedDB truth or be copied into receipts/logs.

### 4.2 GLM — token/API inference only

GLM is the **token-authenticated inference path**. GLM is always called through its admitted token/API channel; it is not logged in through the ClayVerse terminal and does not receive a direct PTY/shell session.

The GLM token is a secret. It must be supplied through a dedicated secret boundary, never committed to source, never written into UnifiedDB as model memory/state, never included in snapshots/receipts, and never emitted to terminal or application logs.

For a GLM turn, ClayVerse assembles the bounded context from UnifiedDB, sends only the admitted inference request outward, receives the model response, binds it to the current causal turn, and re-ingests it into UnifiedDB/ClayVerse before any execution decision. GLM has **no direct filesystem, terminal, EntityOS, EffectGate or external-effect authority**.

### 4.3 Provider switching and common law

ClayVerse may choose Claude Code or GLM for an admitted cognition step according to routing/policy, but switching providers MUST NOT fork the entity or state. The same UnifiedDB turn/session/generation identity continues across providers.

Both providers obey the same loop:

`UnifiedDB/context -> LLM -> response back into ClayVerse -> policy/authority check -> EntityOS/terminal when admitted -> result back into UnifiedDB`.

A model response is never an effect receipt and never self-authorizes a command. Provider failure, timeout or stale response must fail closed or be causally retried/reconciled without bypassing UnifiedDB generation fencing.

The user-facing entry point remains a Clerk-authenticated web application/homepage. Authentication maps users into the one central ClayVerse entity without creating separate agent identities.

## 5. Container law

All admitted runtime pieces needed for the product path MUST converge into the **same ClayVerse container image**: ClayVerse service, complete accepted EntityOS substrate, UnifiedDB authority, Claude Code terminal runtime, GLM token/API client boundary, managed Linux PTY/tmux terminal, web/API boundary and effect/security gates.

No mandatory second application container, separate consciousness service, hidden state authority or external execution brain may be required for the product to function. A remote GLM inference service is an admitted bounded inference dependency only and may never become state/execution authority.

Persistent volumes are data, not companion product artifacts. They must be explicitly scoped, recoverable and attach to this one machine continuum.

## 6. Build/test law

Current build, test, experiment and runtime validation are isolated-sandbox-only. Exact whole-container execution remains the final acceptance gate. Lack of one provider connection must not stop independent source, contract, adversarial, restart, concurrency, fuzz, reproducibility, component-runtime or integration testing that remains possible under `the artefact/TESTING_STRATEGY.md`.

Snapshot/recovery behavior MUST be tested adversarially before whole-product acceptance: EntityOS crash, terminal child crash, interrupted UnifiedDB write, crash before/after effect acknowledgement, stale-generation result arrival, repeated crash during recovery, corrupted snapshot candidate and recovery from the previous known-good snapshot.

LLM-provider behavior MUST also be tested independently: Claude Code direct-terminal auth/runtime continuity, GLM token non-persistence/redaction, provider timeout/failure, stale response rejection, provider switching inside one causal turn/generation, and proof that neither provider can bypass EntityOS/EffectGate into terminal/effect execution.

VPS/self-hosted/production-host testing is forbidden unless later explicitly authorized as deployment validation. Together API/service remains forbidden. Final paid/model training remains owner-authorization-required.

A deployment READY state, source inspection, CI definition, receipt, component test or baseline build is never whole-product PASS.

## 7. `go` and living artefact README

Exact `go` means maximum useful product-convergent work on this ClayVerse single-container frontier: refresh shared state, avoid duplicate implementations, build/repair the canonical path, execute the strongest available authorized tests, fuse evidence and continue until the useful unblocked frontier is exhausted.

`the artefact/README.md` MUST be refreshed in every product-convergent cycle. If canonical product/runtime bytes do not change, record `NO_CHANGE` and why. Detailed evidence remains in Git history/receipts.

## 8. Supersession rule

Any older file that says the active endpoint is `EntityOS`, `ONE_EXECUTABLE_FILE`, `SINGLE_FILE_CLAY_COMPUTER`, FRANK, self.root, UCM2 or a historical harness is superseded where it conflicts with this directive. Such material may still contribute bounded internal implementation/regression evidence.

Any newer ClayVerse implementation that treats the final product as a normal stateless web app, makes UnifiedDB non-canonical, bypasses the internal terminal/effect boundary, removes EntityOS from the final accepted continuum, lacks automatic known-good snapshot recovery, makes the runtime root filesystem mutable, logs/persists GLM tokens, gives GLM direct terminal/effect authority, or replaces the Claude Code direct-terminal-login path with an unrelated hidden API path violates this directive.
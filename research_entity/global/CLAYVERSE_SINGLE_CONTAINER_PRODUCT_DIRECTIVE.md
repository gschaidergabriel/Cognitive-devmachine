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
- Claude Code as runtime inference/cognition engine;
- managed hooks, retrieval/routing organs and EffectGate/effect journal;
- the authenticated web/API/transport boundary needed to accept inputs and return outputs.

Nothing outside this boundary may become a second cognition, state, execution or identity authority.

### 3.1 Ingress

External data enters only through explicit admitted input surfaces. Examples include authenticated user/browser input, approved machine/API input, uploaded data and verified effect results returning from an admitted external boundary.

Ingress is normalized, authenticated/authorized where applicable, causally identified and written/reconciled against canonical ClayVerse state before it influences cognition or execution.

### 3.2 Internal processing loop

The canonical processing cycle is conceptually:

`INGRESS -> canonicalize/record in UnifiedDB -> retrieve/assemble current state -> LLM/Claude cognition -> re-ingest model output as proposed intent/command -> policy/authority validation -> EntityOS/managed terminal execution when admitted -> capture stdout/stderr/result/effect receipt -> re-ingest result into UnifiedDB/current causal turn -> continue cognition as needed -> EGRESS`

The LLM does not directly own state and does not directly bypass the execution boundary. Its output returns into ClayVerse first and is treated as proposed action/data until validated.

The cycle may repeat many times for one causal task. Command results, errors, observations and external effect receipts return into the same continuum instead of becoming an out-of-band side channel.

### 3.3 Linux terminal control

The internal environment MUST be able to communicate directly with and control its managed Linux terminal/PTY/tmux surface. The accepted EntityOS/ClayVerse execution layer may start commands, provide stdin, receive stdout/stderr/exit status, inspect managed process state and perform admitted filesystem/process operations inside its bounded authority.

Unmediated generic host `process.exec` remains forbidden. Terminal control is not removed; it is routed through the admitted EntityOS/ClayVerse execution/security contract so commands are attributable, policy-checked, recoverable and causally re-ingested.

### 3.4 Egress

Only explicit admitted output/effect surfaces may cross the boundary. Egress includes user-visible responses, approved files/data, terminal/effect results exposed to an authenticated user, and explicitly authorized external effects.

Egress must remain attributable to a canonical causal turn/effect receipt. Unknown, stale, replayed or unauthorized effects fail closed.

## 4. Cognition and web boundary

Claude Code is the runtime inference/cognition engine. It is not a separate persistent identity and must not own canonical memory. It receives context assembled from canonical ClayVerse state and returns reasoning results/intents/commands into the internal loop above.

The user-facing entry point is a Clerk-authenticated web application/homepage. Authentication maps users into the one central ClayVerse entity without creating separate agent identities.

## 5. Container law

All admitted runtime pieces needed for the product path MUST converge into the **same ClayVerse container image**: ClayVerse service, complete accepted EntityOS substrate, UnifiedDB authority, Claude Code runtime, managed Linux PTY/tmux terminal, web/API boundary and effect/security gates.

No mandatory second application container, separate consciousness service, hidden state authority or external execution brain may be required for the product to function.

Persistent volumes are data, not companion product artifacts. They must be explicitly scoped, recoverable and attach to this one machine continuum.

## 6. Build/test law

Current build, test, experiment and runtime validation are isolated-sandbox-only. Exact whole-container execution remains the final acceptance gate. Lack of one provider connection must not stop independent source, contract, adversarial, restart, concurrency, fuzz, reproducibility, component-runtime or integration testing that remains possible under `the artefact/TESTING_STRATEGY.md`.

VPS/self-hosted/production-host testing is forbidden unless later explicitly authorized as deployment validation. Together API/service remains forbidden. Final paid/model training remains owner-authorization-required.

A deployment READY state, source inspection, CI definition, receipt, component test or baseline build is never whole-product PASS.

## 7. `go` and living artefact README

Exact `go` means maximum useful product-convergent work on this ClayVerse single-container frontier: refresh shared state, avoid duplicate implementations, build/repair the canonical path, execute the strongest available authorized tests, fuse evidence and continue until the useful unblocked frontier is exhausted.

`the artefact/README.md` MUST be refreshed in every product-convergent cycle. If canonical product/runtime bytes do not change, record `NO_CHANGE` and why. Detailed evidence remains in Git history/receipts.

## 8. Supersession rule

Any older file that says the active endpoint is `EntityOS`, `ONE_EXECUTABLE_FILE`, `SINGLE_FILE_CLAY_COMPUTER`, FRANK, self.root, UCM2 or a historical harness is superseded where it conflicts with this directive. Such material may still contribute bounded internal implementation/regression evidence.

Any newer ClayVerse implementation that treats the final product as a normal stateless web app, makes UnifiedDB non-canonical, bypasses the internal terminal/effect boundary, or removes EntityOS from the final accepted continuum violates this directive.
# CLAYVERSE CANONICAL DIRECTIVE

Owner directive: 2026-08-17

This file is the single current product/research mission directive for the entire Research Entity. It supersedes every older mission, scope, UCM-only target, Frank-only target, PC-only target, EntityOS-as-final-product target, and older `go` behavior wherever they conflict with this file.

Governance/state-history files remain evidence and continuity records. They do not override this owner directive.

## 1. One target product

Build **ClayVerse**.

ClayVerse is one persistent, causally closed AI entity that runs centrally on the VPS as **one deployable container**.

ClayVerse is not a classic agent + vector DB system. Its defining property is one durable world/self/conversation state plus verified causal feedback from real effects back into that state.

The final product boundary is ClayVerse. EntityOS is an internal execution substrate, not the top-level product.

ClayVerse does **not** need to be rewritten completely in `.clay`.

## 2. Human surface

The primary user interface is the normal **Claude Code terminal CLI** presented in the browser.

Flow:

`Browser -> Clerk -> identity mapping -> permanent user terminal -> normal Claude Code CLI -> ClayVerse`

There is no separate custom chat UI requirement.

Clerk identifies which human is present. ClayVerse uses that identity for attribution, context and session routing.

There are exactly two permanent user terminal sessions:

- Gabriel session
- Andreas session

Both users have the same rights/capabilities.

The two sessions are two conversation perspectives into one ClayVerse entity, not two agents and not two independent world models.

## 3. Permanent conversation memory

Each user session keeps the newest 20 turns at full conversational fidelity.

Older conversation history is progressively compressed over time:

`full -> detailed summary -> semantic summary -> fact/decision trace -> key phrase -> 1-2 word minimum trace`

Before destructive compression, durable facts, decisions, tasks, commitments, preferences, entities, project state and causal links are extracted into UnifiedDB with provenance.

Conversational memory records at minimum:

- user_id
- session_id
- turn_id
- timestamp
- topic/entities
- provenance
- compression generation
- extracted durable-memory references
- causal/action references when applicable

Each session strongly prioritizes its own recent and historical conversation context.

The other user's session is not routinely injected. Cross-session retrieval occurs when there is material collision risk or contradictory shared-state work, such as the same file, repository branch, task, machine, deployment, database migration, effect or incompatible decision.

## 4. Canonical state architecture

**UnifiedDB is the canonical state authority.**

It unifies or canonically references:

- world model
- self model / ClayVerse state
- users and user contexts
- conversation memory
- long-term memory / episodes / experiences
- wiki / knowledge objects
- projects, files, repositories and machines
- goals and tasks
- observations and predictions
- GWT/workspace episodes
- effects, executions and outcomes
- causal credit and causal re-entry
- generations and leases
- provenance
- checkpoints and recovery state

Legacy multi-database Frank state is a migration/donor source, not the final authority architecture.

**ClayGraph is a derived/rebuildable topology/projection of UnifiedDB, never a second independent truth authority.**

## 5. Cognitive architecture

The target cognitive path is:

`Input -> user/session identity -> observation -> world assembly -> retrieval -> ClayGraph -> Hyperposition -> salience/attention -> GWT -> Claude Code reasoning -> intent -> Needle/routing -> effect gate -> EntityOS execution -> outcome -> verification -> causal re-entry -> causal credit -> UnifiedDB update -> repeat`

Required systems include the strongest valid generations of:

- UnifiedDB
- ClayGraph
- Hyperposition
- GWT / global workspace
- salience / attention
- Needle / MicroClay routing where useful
- world assembly / retrieval
- identity and continuity
- causal episode identity
- verified causal re-entry
- causal credit
- generation / lease fencing
- recovery / checkpointing
- provenance / replay protection

### No consciousness daemon

`consciousness_daemon` is removed from the target architecture.

Do not replace it with a renamed equivalent daemon.

Useful functions historically bundled there (GWT, attention, goals, perception, state/mood, prediction/reflection signals) must be fused into the ClayVerse core, UnifiedDB state and the event/causal loop as appropriate.

## 6. Claude Code role

Claude Code is the primary high-capability inference/reasoning/coding engine and the visible terminal interface of the finished ClayVerse product.

Claude Code is not ClayVerse identity or durable state.

A Claude Code process/session may restart without creating a new ClayVerse entity. ClayVerse reconstructs bounded relevant context from durable state.

Claude receives bounded world assemblies instead of becoming the canonical store of world truth.

### Build-research independence

The Research Entity itself must build and verify the ClayVerse artifact **without using Claude Code as a research, coding, implementation, planning or test helper**.

Claude Code is a component of the finished product, not a dependency of the build/research process that creates the artifact.

Research/build workers must use the Research Entity's other available tools, repository history, isolated execution/sandbox capabilities, tests and evidence directly.

## 7. EntityOS research is fully in scope

Bring the strongest valid, non-falsified generations of the complete EntityOS research into ClayVerse as the internal machine/execution/security substrate.

This includes, where supported by evidence and integration tests:

- ClayCode
- parser / syntax / IR
- type and effect system
- executable TypedIR
- lowering / compiler
- ClayVM and artifact model
- runtime / ClayEnv
- minimal ClayOS functionality
- typed Linux interop
- process execution semantics
- terminal / PTY / argv / stdin / stdout / stderr / signal / exit semantics
- networking / DNS / socket / TLS / HTTP / streaming effects
- data / bytes / buffers / ownership / lifetime / epochs / streaming / backpressure
- visual / image / video transport and typed facts
- audio transport where validated
- capability model and effect authority
- provenance binding
- artifact hashing / artifact-lock authority / attestation work
- replay protection
- generation and lease fencing
- deterministic/reproducible execution where applicable
- recovery / crash / restart semantics
- portability / fresh-host / relocation work
- observability and receipts
- fail-closed unknown/opaque-data behavior
- security hardening and isolation

Preserve negative evidence and candidate/promoted distinctions. A component PASS never implies whole-machine PASS.

The internal EntityOS artifact may remain a single reproducible binary/package if that is the strongest validated form, but the **final product artifact is the ClayVerse container**.

## 8. Legacy Frank is a donor, not the final architecture

The current VPS Frank deployment is evidence and a donor source.

For each useful organ, reconstruct behavior and choose:

`RETAIN | FUSE | DISTRIBUTE | REDESIGN | REMOVE`

Do not discard useful functionality merely because it is old.

Do not retain duplicate truth/state authorities merely because they already exist.

Examples expected to be evaluated/fused include memory/retrieval, GWT functionality, Needle/routing, goals, perception, personality/state, prediction, experience/episodic functions, tools and useful gateways.

`consciousness_daemon` is explicitly `REMOVE`.

## 9. Technology version law

Never choose a component because its filename or timestamp is newest.

For every technology resolve:

`commit history -> lineage -> successor -> negative evidence/falsification -> candidate/promoted/canonical status -> integration dependencies -> chosen ClayVerse generation`

Use exact commit SHA, artifact identity and test/receipt provenance wherever available.

Prefer fusion of existing validated technology over reinvention.

## 10. Build/test/deployment law

**Construction and verification happen away from the live VPS.**

Use isolated sandbox execution during construction. **Vercel Sandbox is the preferred external build/verification environment where its capabilities fit the test**, supplemented by the Research Entity's other available non-VPS build/test tools.

The live VPS is an evidence source through the dedicated read-only MCP until the owner explicitly authorizes deployment/mutation.

Do not use the live VPS as the normal construction workspace.

The **final deployment target is the VPS** only after the artifact is sufficiently verified.

The persistent ClayVerse state must live outside the ephemeral container layer, e.g. under a durable mounted state root such as `/var/lib/clayverse`.

Container replacement must not replace the ClayVerse entity.

## 11. Canonical artifact location

All buildable ClayVerse product source, container definitions, test harnesses, manifests, generated acceptance receipts and release-candidate metadata belonging to the target artifact must live under exactly:

`the artefact/`

on the `main` branch of:

`gschaidergabriel/clay-global-research-entity`

The directory `the artefact/` is the canonical artifact workspace.

Research notes outside that directory may remain evidence, but a finished/candidate product must be reproducible from `the artefact/` plus explicitly pinned external inputs/artifact hashes.

The primary release object remains **one OCI/Docker-compatible ClayVerse container image**. The repository directory is its canonical reproducible source and evidence bundle.

## 12. `go` is the build-to-artifact trigger

Exact owner trigger: `go`

When the owner sends `go`, the Research Entity must execute the maximal current cycle toward the finished ClayVerse architecture. It is no longer UCM2-only and no longer a research-report-only trigger.

A `go` cycle must, as useful and available:

1. refresh canonical repository/VPS/evidence state;
2. resolve latest valid component generations;
3. research remaining unknowns and counterhypotheses;
4. fuse the architecture;
5. implement/build the actual ClayVerse container under `the artefact/`;
6. run applicable unit, integration, replay, recovery, failure, provenance, state and security tests;
7. use Vercel Sandbox and other authorized isolated tools where useful;
8. preserve negative evidence and exact blockers;
9. update canonical source/evidence on `main`;
10. produce the strongest deployable **single-container ClayVerse artifact** supported by the evidence.

The Research Entity performs this cycle without Claude Code assistance.

The primary finished artifact is a single OCI/Docker-compatible ClayVerse container image identified by source commit/artifact hash. Supporting manifests, receipts and evidence may be committed and/or embedded in the image, but they do not become separate product runtimes.

A `go` response must not stop at planning if implementation/testing tools are available.

Never claim FINISHED/PASS merely because an image builds. If any acceptance gate remains unverified, label the image/artifact as a candidate and report the exact blocker while preserving the best working artifact.

## 13. Minimum final acceptance shape

A finished ClayVerse artifact must ultimately demonstrate, with evidence appropriate to each gate:

- one-container boot
- durable external state/restart continuity
- Clerk identity mapping design/integration
- automatic routing to two permanent user terminals
- normal Claude Code CLI surface
- equal user rights
- last-20-turn full session window
- progressive old-history compression to 1-2 word minimum traces
- durable conversational-memory metadata/extraction
- session-local attention priority
- collision-triggered cross-session retrieval
- UnifiedDB canonical state authority
- ClayGraph derived projection
- Hyperposition integration
- GWT integration without `consciousness_daemon`
- Needle/routing where retained
- EntityOS execution substrate integration
- typed/capability-gated effects
- outcome verification and causal re-entry
- generation/lease fencing
- provenance/artifact identity
- recovery/replay behavior
- no silent stale-generation writes
- no duplicate canonical truth stores
- VPS deployment readiness

## 14. Completion rule

The research entity's single mission is now:

**Build, verify and deliver ClayVerse as one deployable VPS container artifact, constructed and tested away from the live VPS, without Claude Code assistance, using the strongest valid components already present across Frank, Clay/UnifiedDB/ClayGraph/Hyperposition/GWT research and the complete EntityOS research line, with the canonical artifact workspace at `main/the artefact/`.**

All older directives are historical evidence only when they conflict with this mission.

# ClayVerse integrated single-container candidate architecture

## Product boundary

ClayVerse is the product endpoint. The canonical release target is one OCI/Docker-compatible image built from `the artefact/`. EntityOS is an internal execution/security/runtime substrate carried inside that image; it is not the top-level release endpoint.

There is one persistent central ClayVerse entity. Gabriel and Andreas are equal-rights authenticated perspectives into that same entity, with separate durable conversation/Claude Code homes but one canonical UnifiedDB authority.

## Canonical product runtime path

`browser -> Clerk sign-in/session -> verified Clerk JWT -> authenticated WebSocket PTY -> IdentityRouter -> user-bound persistent tmux -> normal interactive Claude Code CLI -> managed UserPromptSubmit hook -> UnifiedDB observation -> MicroClay retrieval entry/activation -> ClayGraph/temporal/provenance context -> Hyperposition -> bounded workspace context injection -> Claude reasoning -> effect-only local ClayVerse MCP when an admitted action is needed -> EffectGate -> internal EntityOS only when explicitly admitted -> verified/denied outcome -> causal re-entry/credit -> MicroClay retrieval-policy learning -> managed Stop/StopFailure hook -> assistant turn -> UnifiedDB -> rebuilt ClayGraph`

The retired headless `claude -p`/custom chat API path is not the product runtime.

## Deterministic goal autonomy

ClayVerse goal autonomy is implemented as canonical state and a bounded machine loop, not as an LLM identity assertion.

The target autonomous loop is:

`durable user-authorized goal -> canonical capability/state snapshot -> LLM proposes one next step -> deterministic GoalKernel admission -> canonical TurnLifecycle/effect path -> EffectGate -> verified EffectJournal observation -> typed success evaluation -> replan | stop | BLOCKED`

The persistent autonomy state lives inside the same UnifiedDB through additive `goals`, `goal_steps` and `goal_events` records. `GoalKernel` is not a second agent, second database, second effect executor or second memory authority. A deterministic `goal_state_hash` is stored in UnifiedDB metadata so current goal state participates in the existing checkpoint state.

The useful behavior intended by an "autonomous AGI" prompt is decomposed into machine facts instead of anthropomorphic claims:

- continuity = UnifiedDB + causal lifecycle + recovery;
- objective = durable canonical goal record;
- initiative = repeated goal pulses while the goal remains ACTIVE;
- agency = the cognition provider chooses the next proposed step within an explicit envelope;
- capability = intersection of goal-authorized capabilities and capabilities actually exposed by the current EffectGate/runtime;
- execution = existing TurnLifecycle/EffectGate/EntityOS path only;
- progress/success = typed verifier over canonical evidence, never model self-assessment;
- uncertainty = explicit UNKNOWN/BLOCKED rather than invented completion;
- stopping = deterministic success, pause/cancel/block states and step/retry/resource ceilings.

A model response cannot grant itself a capability, prove an action occurred, alter its budget or mark a goal successful. Runtime prompts may encourage initiative and proactive problem solving, but operational claims are accepted only from canonical state and receipts.

The human authorizes a goal-level capability envelope so low-risk intermediate choices do not require a click on every step. The first admitted autonomy surface remains deliberately narrow: `state.noop`, plus `entityos.exec` only when EntityOS is already admitted and currently exposed through EffectGate. Generic `process.exec` remains forbidden. Goal-specific capabilities can only narrow the runtime surface, never widen it.

Every admitted step is generation-bound and proposal-hash-bound, and exactly one step per goal may await evidence at a time. Goals carry deterministic total-step and identical-proposal retry ceilings. A missing capability, exhausted budget or uncertain post-crash effect is a machine-level stop/block condition rather than a prompt suggestion.

Success contracts are deliberately outside the LLM. `manual` contracts never auto-promote. `verified_effects` contracts require matching VERIFIED EffectJournal evidence and may bind capability, exact target, count and exit status. A planner sentence such as "done" has zero success authority.

Background execution must preserve human priority. The current interactive `TurnLifecycle.begin_admission()` deliberately retires an unfinished predecessor for sequential human conversation; an autonomous supervisor must not reuse that preempting behavior blindly. Before continuous background pursuit is enabled, the product needs a non-preempting autonomous admission primitive that atomically fails/defer closed when a human turn is active, while still using the same `active_turns`, workspace, generation, effect and causal ledgers. No hidden direct EffectGate path is allowed as a shortcut.

Restart is an epistemic boundary. An admitted autonomous step without a bindable final receipt becomes UNKNOWN and blocks the goal rather than being assumed successful or blindly replayed. Exact request/effect identity must be preserved before production background retry is enabled.

The detailed contract and promotion gates are in `DETERMINISTIC_GOAL_AUTONOMY.md`.

## Canonical state and memory invariants

- UnifiedDB (SQLite/WAL candidate) is the persistent state/world/data/memory authority.
- ClayGraph is derived and rebuildable; it is not a competing source of truth.
- Exactly two canonical users (`gabriel`, `andreas`) map to one entity/database and separate permanent sessions.
- Each session preserves its newest 20 turns at full fidelity.
- Older history ages through explicit compression generations. The first destructive boundary is fail-closed until complete semantic coverage is established by explicit typed lines or a digest-bound stronger-extractor clearance.
- After destructive compression there is no hidden lossless transcript authority. Provenance retains non-reversible source digest/size metadata plus admitted durable semantic extraction.
- Cross-session retrieval is collision-triggered and bounded rather than routinely injecting another user's full session.
- Workspace episodes are explicit, selection-fenced, and connected to causal re-entry.

## MicroClay adaptive retrieval organ

MicroClay is a persistent small retrieval organ inside the single ClayVerse entity, not a second identity, second agent or second source of truth. Its job is to learn the best **entry point into memory**, not merely to sort a fixed top-k after the fact.

The target retrieval path is:

`current cue + user/session + resource context -> MicroClay entry-point proposal -> exact/structured temporal lookup + FTS/vector candidates + bounded ClayGraph seed activation/expansion -> provenance/valid-time/conflict filters -> adaptive budget/ranking/abstention -> Hyperposition for unresolved facets -> GWT/context coalition -> Claude`

MicroClay may adapt:

- query/cue normalization and entry-point seeds;
- memory/source/class routing;
- relative exact/FTS/vector/graph/recency/provenance weights;
- graph seed quality, bounded activation radius and widen-search threshold;
- context-budget packing and abstention/UNKNOWN thresholds;
- repeated usefulness/irrelevance/staleness priors for retrieval routes.

MicroClay may **not** adapt semantic truth, provenance, user rights, capability authority, EffectGate policy, EntityOS admission or the canonical memory record. Retrieval activation/accessibility is never truth or execution authority.

Every canonical product retrieval is causally receipt-bound to `turn_id`, `episode_id`, `causal_id`, user/session and the live entity generation. Query content is not duplicated into the retrieval-policy ledger; bounded hashes/entry keys and selected IDs provide replay/audit identity. A repeated retrieval of the same causal turn reuses the same receipt rather than learning twice.

Learning is outcome-bound. The initial safe learning signal is a later verified EffectJournal/causal outcome from the same retrieval episode. A normal Claude answer is not automatically positive reward. Duplicate feedback receipts are idempotent and stale generations are rejected. User corrections, retrieval misses, unnecessary personalization and verified task outcomes are intended additional supervised/causal signals once their admission contracts are explicit.

The learned policy starts in `SHADOW`: the deterministic baseline continues serving Claude while the adaptive route is scored and recorded. Promotion to `ACTIVE` requires isolated replay/held-out evidence showing positive net retrieval utility without higher contamination, stale-memory use, unnecessary personalization or authority leakage. Cold/random learned parameters must never replace a known-safe baseline merely because training has begun.

The current source candidate implements the persistent receipt/policy spine, query-sensitive baseline, hashed cue entry keys, causal outcome learning and SHADOW gating. Full graph-native entry selection, FTS/vector fusion and any neural MicroClay implementation remain acceptance work and must be benchmarked against simpler retrieval rather than assumed superior.

## Permanent Claude Code boundary

- The image carries normal interactive Claude Code plus `tmux`; browser detach does not intentionally terminate the underlying user session.
- Each canonical user has a durable HOME below `/var/lib/clayverse/users/<user>/home`; subscription/OAuth/session state therefore follows the persistent ClayVerse state volume rather than container-secret inheritance.
- Claude starts from an environment allowlist, with built-in tools disabled and strict MCP configuration.
- Managed Claude settings are installed at `/etc/claude-code/managed-settings.json`; `UserPromptSubmit`, `Stop`, and `StopFailure` hooks bind interactive conversation lifecycle to UnifiedDB automatically.
- The local stdio MCP is effect-only: `request_effect` and read-only session state. It cannot replace the automatic turn hooks as a second state authority.
- The admitted effect protocol is limited to `state.noop` and `entityos.exec`; generic host `process.exec` remains forbidden.

## Web/auth boundary

- The server verifies Clerk session JWTs using configured issuer/key material and authorized-party checks, then resolves the subject through the persisted canonical identity binding.
- The browser surface is an authenticated WebSocket PTY, not `/api/chat`.
- xterm JavaScript/CSS are vendored into the ClayVerse image and served by the container; they are not fetched from a public CDN at runtime.
- Clerk remains the intended external authentication service and its real-instance browser/JWT/key-rotation behavior is still an executable acceptance gate.

## EntityOS/effect boundary

- EntityOS bytes are staged into the image from a verified source lock and build-time SHA-256/size contract.
- The service verifies the embedded artifact identity at startup.
- `CLAYVERSE_ENABLE_ENTITYOS_EXEC=0` is the default admission state. The service and per-user MCP both remain non-executing until the exact embedded EntityOS artifact has accepted isolated runtime evidence and execution is explicitly enabled.
- Effect intent is journaled/fenced before external execution and outcome is causally re-entered; stale generation/lease writers fail closed at the admitted contract.

## Container boundary

- Build context is default-deny/allowlisted.
- The supplied Compose profile runs one ClayVerse service as non-root with read-only rootfs, dropped Linux capabilities, `no-new-privileges`, bounded tmpfs, one persistent state volume and one workspace volume.
- Runtime-generated state is external to the immutable image; no companion application container is part of the release contract.
- `consciousness_daemon` is excluded; continuity comes from persistent interactive sessions plus explicit state, hooks, causal/recovery contracts and checkpoints.

## Deliberately unclaimed / still external

- Exact-current-head full regression suite on an authorized isolated executor.
- Exact OCI image build and runtime checks for the packaged Python/Node/tmux/Claude Code/xterm/managed-hook stack.
- Real Clerk browser/JWT/WebSocket behavior.
- Real authenticated normal interactive Claude Code sessions for both durable user homes.
- Exact hook lifecycle: prompt ingestion -> MicroClay retrieval/context injection -> optional effect MCP -> Stop/StopFailure persistence under live Claude Code.
- Deterministic goal-autonomy regression suite and exact UnifiedDB restart persistence.
- Non-preempting background goal admission that proves human turns cannot be displaced.
- Exact goal-step -> canonical turn/effect request identity binding and verify-before-retry recovery under crash/timeout ambiguity.
- Periodic in-container goal supervisor remains disabled until those autonomy promotion gates pass.
- MicroClay shadow-vs-baseline replay/held-out benchmark, user-correction feedback and ACTIVE promotion gate.
- Full exact/FTS/vector/ClayGraph entry-point fusion and bounded graph activation.
- Live dual-session collision/concurrency/stale-generation controls.
- Accepted exact embedded EntityOS runtime/effect contract.
- Restart/crash/recovery and persistent-volume continuity at exact image identity.
- Deployment readiness and later explicitly authorized VPS deployment/migration.
- Complete Python generator-bootstrap hash closure and an accepted canonical `requirements.lock.txt`; source-locking the resolver wheel alone does not establish the transitive closure.

Current execution evidence has advanced beyond the older connector-surface limitation: the retained Dr.-Unterweger PR810 Git Preview/OIDC controller has repeatedly started on Vercel and successfully created disposable Vercel Sandboxes for the bound ClayVerse execution closure. The strongest observed run is still pre-product-runtime: it stopped fail-closed before private Research/EntityOS source fetch because the host-side sensitive Preview `GITHUB_READ_TOKEN` was absent, then cleaned up the Sandbox. Therefore Vercel/Sandbox admission is supported at that exact bounded scope, while source regression, EntityOS reproduction, OCI build/image identity and in-image product behavior remain unobserved. This credential prerequisite is infrastructure admission state, not ClayVerse PASS and not ClayVerse TEST_FAIL.

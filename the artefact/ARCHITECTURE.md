# ClayVerse integrated single-container candidate architecture

## Product boundary

ClayVerse is the product endpoint. The canonical release target is one OCI/Docker-compatible image built from `the artefact/`. EntityOS may sit inside/below this image as an execution/security/runtime substrate; it is not the top-level release endpoint.

There is one persistent central ClayVerse entity. Gabriel and Andreas are equal-rights authenticated perspectives into that same entity, not separate agents or separate canonical state stores.

## Canonical runtime path

`Clerk browser session -> verified Clerk JWT -> IdentityRouter -> permanent user session -> observation turn -> UnifiedDB -> WorldAssembler -> bounded workspace alternatives -> tool-less ephemeral Claude Code cognition -> fail-closed structured decision/effect intent -> workspace selection -> capability/effect gate -> internal EntityOS execution substrate when admitted -> verified outcome -> causal re-entry -> UnifiedDB -> rebuilt ClayGraph`

## Invariants implemented in source

- UnifiedDB (SQLite/WAL candidate) is the canonical persistent state/world/data/memory authority.
- ClayGraph is derived and rebuildable; it is not a competing source of truth.
- Gabriel and Andreas route into one entity/database with separate permanent user sessions.
- Each session preserves its newest 20 turns at full fidelity.
- Older history degrades by explicit generations; destructive compression promotes only explicitly typed durable lines (`FACT:`, `DECISION:`, `TASK:`, `COMMITMENT:`, `PREFERENCE:`), so unknown meaning fails closed rather than being guessed.
- Cross-session retrieval is collision-triggered by explicit shared resource references instead of being injected routinely.
- Workspace alternatives remain explicit and single-selection fenced.
- Claude Code cognition is launched as an ephemeral one-turn, tool-less process with no Claude session persistence; canonical durable context is supplied from ClayVerse state.
- Claude output is parsed by a fail-closed intent protocol. Runtime inference may request only `entityos.exec` or `state.noop`; malformed/unknown capabilities are rejected. Generic host `process.exec` is forbidden.
- Effect execution validates exact session ownership and reasoning generation before action; stale generation/ABA resource writers are fenced.
- The current EntityOS bridge verifies an exact SHA-256-pinned executable object before invoking it and records boundary identity in the outcome. This remains an internal substrate candidate until its semantic/artifact contract is accepted.
- Outcomes are hashed and causally re-entered into UnifiedDB.
- `consciousness_daemon` is excluded; continuity comes from explicit persisted state and causal/recovery contracts.
- Container state is externalized to explicit persistent volumes while the supplied Compose profile is non-root, read-only, drops all capabilities and uses `no-new-privileges`.

## Clerk/web boundary implemented in source

The server verifies Clerk session JWTs using an explicit issuer plus a pinned public key or JWKS retrieval, requires an approved `azp`/authorized party, and maps the verified Clerk subject through the canonical identity router. The homepage loads ClerkJS from the configured Clerk frontend endpoint, mounts sign-in/user UI and sends the current session token to `/api/chat`.

This is source implementation, not yet a real-instance runtime PASS.

## Deliberately unclaimed / still external

- Exact-current-head full regression suite on an authorized isolated executor.
- Exact OCI image build plus packaged Python/Node/Claude Code/runtime checks on an authorized isolated container executor.
- Real Clerk-instance browser/JWT/key-rotation behavior.
- Real authenticated Claude Code inference against Anthropic from inside the candidate image.
- Accepted external-effect substrate contract and exact embedded/mounted artifact binding for production actions.
- Restart/crash/recovery and persistent-volume continuity at exact image identity.
- Deployment readiness and later explicitly authorized VPS deployment/migration.

The first GitHub-hosted OCI gate was rejected before any job step because the account runner could not start due billing/spending state. That infrastructure failure is preserved as negative evidence and is not interpreted as a code failure or a PASS.

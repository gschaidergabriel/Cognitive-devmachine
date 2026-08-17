# ClayVerse testing strategy — maximum evidence before final OCI gate

This policy applies to every product-convergent ClayVerse cycle until replaced by a later owner directive.

## Operating rule

The unavailable direct Vercel Git-project connection is **not a development blocker**. Exact whole-container OCI/Sandbox execution remains the final acceptance gate, but source/product convergence continues without waiting for it.

Every change must be tested as broadly as the currently authorized isolated tools permit. Missing one execution surface must not suppress independent tests that are still possible.

No source/component result may be promoted to whole-product PASS. The final ClayVerse container remains `IN_PROGRESS` until an exact admitted OCI image executes the whole required path.

## Required test fan-out

For each material change, select every applicable independent layer rather than a single happy-path test:

1. **Static/source integrity** — syntax/compile/import checks, schema validation, source-order/authority guards, forbidden-path scans, exact lock/digest checks and source-diff review.
2. **Unit and contract tests** — focused unit tests plus cross-module invariants for UnifiedDB authority, ClayGraph derivation, canonical users/sessions, managed hooks, EffectGate and packaging boundaries.
3. **Negative/fail-closed tests** — missing/corrupt/stale identity, malformed input, wrong digest, expired/replayed auth, unknown tmux diagnostics, forbidden effects, absent runtime dependencies and partial state.
4. **Adversarial and mutation tests** — deliberately perturb trusted assumptions and verify the candidate rejects or recovers correctly. Unusual experiments still require the project coordination lease; ordinary deterministic adversarial regression does not consume that slot.
5. **Persistence/restart tests** — process death, clean/unclean restart, stale sessions, interrupted writes, recovery/idempotency and generation continuity, using disposable isolated state only.
6. **Concurrency/race tests** — Gabriel/Andreas simultaneous sessions, reauth during work, competing hooks/effects, duplicate delivery, ordering changes and global-generation fencing.
7. **Property/fuzz tests** — bounded randomized inputs or state-machine sequences where deterministic unit cases cannot adequately cover the state space. Seeds and failing cases must be preserved in receipts/tests.
8. **Supply-chain/reproducibility tests** — source locks, hashes, exact filenames/versions, offline installation where applicable, double-build/double-generation byte comparisons and dependency identity capture.
9. **Runtime-component tests** — real tmux/Claude/PTY/process behavior on any authorized disposable execution surface available to the worker, while clearly recording when the runtime is not the exact final OCI runtime.
10. **Integration simulations** — exercise Clerk/JWT, WebSocket PTY, hooks, UnifiedDB, recovery and EffectGate boundaries together using mocks/fakes only where real external services are unavailable; mocks never count as external-runtime proof.
11. **Resource/failure injection** — bounded timeouts, cancellation, process termination, locked database, unavailable dependency/network and other safe disposable failure modes when relevant. Never run destructive tests against production, VPS or persistent owner systems.
12. **Regression breadth** — after a focused fix passes, run the largest relevant adjacent suite the available environment can support so repairs do not silently regress retained lanes.

## Evidence ladder

Use the strongest honest classification supported by execution:

- `SOURCE_INSPECTED`
- `STATIC_CONTRACT_PASS`
- `FOCUSED_TEST_PASS`
- `ADJACENT_REGRESSION_PASS`
- `COMPONENT_RUNTIME_PASS`
- `MULTICOMPONENT_INTEGRATION_PASS`
- `EXACT_OCI_COMPONENT_PASS`
- `WHOLE_CLAYVERSE_PASS`

A higher class must not be inferred from a lower one. Historical or different-version runtime evidence remains bounded supporting evidence.

## Final deferred gate

When an authorized isolated OCI/Sandbox route becomes available, perform one exact closure from freshly refreshed canonical bytes:

`exact source -> reproducible image/digest -> resolved dependency identities -> deny network as required -> UnifiedDB/ClayGraph -> tmux/Claude -> Clerk/WebSocket PTY -> managed hooks -> EffectGate -> persistence/restart/recovery -> dual-user concurrency/global-generation -> final acceptance`.

Until that exact closure succeeds, continue maximizing all lower evidence layers rather than waiting on Vercel setup.

## Safety boundaries

- No VPS/self-hosted/production-host testing.
- No Together API.
- No secret persistence in source, receipts or logs.
- Paid/final training remains owner-authorization-only.
- Tests use disposable/isolated state and must not endanger canonical owner data.

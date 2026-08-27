# ClayVerse testing strategy — maximum evidence before final MicroVM gate

This policy applies to every product-convergent ClayVerse cycle until replaced by a later owner directive.

## Operating rule

Missing one external execution surface is **not a development blocker**. Source/product convergence continues while every independently executable evidence layer is maximized.

No source/component/container result may be promoted to whole-product PASS. Final `WHOLE_CLAYVERSE_PASS` requires the exact accepted ClayVerse OCI image to execute successfully **inside an independent guest-kernel VM/microVM envelope** and to pass the mandatory final sandbox test-of-tests defined by `research_entity/global/CLAYVERSE_FINAL_SANDBOX_TEST_OF_TESTS_DIRECTIVE.md`.

Direct host-kernel OCI execution remains useful development/component evidence only.

## Required test fan-out

For each material change, select every applicable independent layer rather than a single happy-path test:

1. **Static/source integrity** — syntax/compile/import checks, schema validation, source-order/authority guards, forbidden-path scans, exact lock/digest checks and source-diff review.
2. **Unit and contract tests** — focused unit tests plus cross-module invariants for UnifiedDB authority, ClayGraph derivation, canonical users/sessions, managed hooks, EffectGate, provider boundaries, packaging and deployment boundaries.
3. **Negative/fail-closed tests** — missing/corrupt/stale identity, malformed input, wrong digest, expired/replayed auth, unknown tmux diagnostics, forbidden effects, absent runtime dependencies, leaked/missing model credentials and partial state.
4. **Adversarial and mutation tests** — deliberately perturb trusted assumptions and verify the candidate rejects or recovers correctly. Ordinary deterministic adversarial regression does not consume the unusual-experiment slot.
5. **Persistence/restart tests** — process death, clean/unclean restart, stale sessions, interrupted writes, recovery/idempotency and generation continuity using disposable isolated state.
6. **Concurrency/race tests** — Gabriel/Andreas simultaneous sessions, reauth during work, provider switching, competing hooks/effects, duplicate delivery, ordering changes and global-generation fencing.
7. **Property/fuzz tests** — bounded randomized inputs/state-machine sequences with preserved seeds/failing cases.
8. **Supply-chain/reproducibility tests** — source locks, hashes, exact filenames/versions, offline installation where applicable, double-build/double-generation byte comparisons and dependency identity capture.
9. **Runtime-component tests** — real tmux/Claude/PTY/EntityOS/provider-client behavior on authorized disposable execution surfaces, clearly recording when the runtime is not the exact final MicroVM runtime.
10. **Integration simulations** — Clerk/JWT, WebSocket PTY, hooks, UnifiedDB, LLM provider boundary, recovery and EffectGate together; mocks never count as external-runtime proof.
11. **Resource/failure injection** — timeouts, cancellation, process termination, locked database, unavailable dependency/network and safe resource pressure on disposable state only.
12. **Regression breadth** — after a focused fix passes, run the broadest relevant adjacent suite the available environment supports.

## Mandatory machine-continuum crash/recovery matrix

Every material recovery implementation must cover every applicable case below:

- kill EntityOS idle and during an active command;
- kill managed PTY/tmux/Claude/provider client while a causal turn remains open;
- fail a token/API inference request and inject a stale provider response after generation change;
- crash before an external effect is emitted, after emission but before acknowledgement, and after durable acknowledgement;
- interrupt UnifiedDB writes/WAL and recover to one consistent canonical generation;
- inject stale pre-crash results after recovery and require fail-closed rejection;
- corrupt/truncate newest snapshot and require fallback to the previous accepted known-good snapshot;
- crash again during recovery and require bounded/idempotent recovery rather than split brain;
- ambiguous effects become `UNKNOWN_AFTER_CRASH`/equivalent and are not blindly replayed;
- idempotent effects replay only when the EffectJournal proves replay safety;
- ingress remains frozen while the continuum is inconsistent;
- snapshot metadata binds UnifiedDB checkpoint, generations, EntityOS/config/policy hashes, causal queue position and EffectJournal state;
- snapshot restore cannot resurrect stale authorization, terminal sessions, effect leases, provider secrets or generations.

## Mandatory LLM-provider matrix

- Claude Code authenticates and operates through the managed internal terminal login/runtime path where that product lane is under test;
- Claude credential/session material is not canonical UnifiedDB cognition/memory and does not appear in receipts/logs;
- token/API provider secrets are injected only through an admitted secret boundary and never appear in source, UnifiedDB, snapshots, receipts or logs;
- token/API providers receive no direct terminal/filesystem/EntityOS/EffectGate authority;
- provider switching preserves the same causal turn/session/global generation;
- model output from every provider is re-ingested as proposed action and cannot self-authorize execution.

### Mandatory Mistral final-provider gate

For the final test-of-tests, Mistral is mandatory:

- retrieve the Mistral API credential at runtime from the owner-approved Vault/secret store;
- inject it transiently into the exact running ClayVerse container as the admitted `MISTRAL_API_KEY` boundary or canonical equivalent;
- prove the token is absent from Git source, OCI layers, logs, receipts, UnifiedDB, snapshots and durable workspace/state;
- perform a real Mistral inference from inside the ClayVerse continuum;
- bind the response to the same canonical turn/session/generation;
- re-ingest the response before any EffectGate/EntityOS action;
- after Tier-2 appliance replacement, reacquire the token from Vault instead of recovering it from ClayVerse persistence;
- perform another real Mistral inference after recovery;
- direct Mistral API calls made outside ClayVerse never count as product evidence.

## Mandatory MicroVM outer-envelope matrix

Final acceptance additionally requires all applicable checks below on the exact accepted image digest:

- launch through an independent VM/microVM guest-kernel envelope rather than direct host-kernel runtime;
- for the mandatory final sandbox test, Vercel Sandbox's Firecracker microVM may serve as this outer guest-kernel envelope when its identity/kernel is attested and the exact accepted OCI digest runs inside it through Docker/OCI runtime;
- prove the image digest executed in the guest equals the accepted image digest exactly;
- capture/attest microVM runtime identity/version and guest-kernel identity;
- prove the workload is behind an independent guest-kernel execution boundary;
- prove root filesystem read-only enforcement and undeclared-write denial;
- prove there is no hostPath, host PID/IPC/network authority or hidden host-shell execution path into ClayVerse authority;
- prove only declared state/workspace persistent surfaces survive the admitted recovery boundary;
- exercise the accepted network boundary and only admitted provider/auth traffic;
- when Docker is run inside Vercel Sandbox, explicitly handle the Sandbox HTTPS proxy CA/trust boundary so TLS success/failure is attributable rather than accidental;
- kill EntityOS and prove Tier-1 reconstruction;
- destroy/recreate the full appliance/Sandbox boundary and prove Tier-2 recovery from the same image digest plus UnifiedDB/WAL/known-good logical snapshot;
- prove stale results from the destroyed generation are rejected;
- crash around effect acknowledgement and prove no blind external replay;
- prove the admitted terminal path and Mistral runtime-secret inference boundary still satisfy their contracts after recovery.

A normal OCI/container PASS without this independent guest-kernel layer is bounded evidence only.

## Mandatory final Vercel sandbox test-of-tests

The final owner acceptance sequence is:

`exact current source + admitted retained lanes`
`-> Vercel Sandbox.create`
`-> attest Firecracker guest/kernel identity`
`-> securely inject scoped GITHUB_READ_TOKEN when private source fetch is required`
`-> fetch and verify exact private Research + EntityOS source identities`
`-> reproduce/build exact ClayVerse OCI`
`-> capture immutable image digest and runtime/dependency identities`
`-> install/start Docker inside the Sandbox microVM or use an equivalently bound OCI runtime`
`-> run EXACT accepted ClayVerse digest`
`-> verify read-only root + declared persistence/tmpfs`
`-> retrieve Mistral token from approved Vault/secret store`
`-> transiently inject Mistral token into ClayVerse`
`-> configure only admitted network/auth egress and required TLS trust`
`-> achieve process liveness and full runtime readiness`
`-> execute a real canonical cognition turn through UnifiedDB/retrieval/workspace/Mistral`
`-> re-ingest model response`
`-> execute one safe admitted EffectGate/EntityOS round-trip`
`-> verify result/effect receipt causal re-entry`
`-> verify one central entity with Gabriel/Andreas perspectives and global-generation fencing`
`-> exercise authenticated terminal/WebSocket/Clerk path at final admitted scope`
`-> Tier-1 recovery`
`-> destroy/recreate the full appliance/Sandbox from the SAME image digest`
`-> recover UnifiedDB/WAL/snapshot/EffectJournal under new generation`
`-> reacquire Mistral token from Vault`
`-> prove no token persistence, no stale-result acceptance and no blind effect replay`
`-> repeat real Mistral cognition after recovery`
`-> WHOLE_CLAYVERSE_PASS only if every admitted gate is green`.

`fully functional` means this integrated path operates. Process startup, one API response, one container build or one component test is insufficient.

## Evidence ladder

- `SOURCE_INSPECTED`
- `STATIC_CONTRACT_PASS`
- `FOCUSED_TEST_PASS`
- `ADJACENT_REGRESSION_PASS`
- `COMPONENT_RUNTIME_PASS`
- `MULTICOMPONENT_INTEGRATION_PASS`
- `EXACT_OCI_COMPONENT_PASS`
- `EXACT_MICROVM_COMPONENT_PASS`
- `FINAL_SANDBOX_TEST_OF_TESTS_PASS`
- `WHOLE_CLAYVERSE_PASS`

A higher class must not be inferred from a lower one.

## Safety boundaries

- No VPS/self-hosted/production-host testing unless separately authorized as deployment validation.
- No Together API.
- `GITHUB_READ_TOKEN` may be securely forwarded into the authorized disposable Vercel Sandbox under the current owner directive; it must never be committed/logged/persisted.
- Mistral and other provider secrets must never persist in source, UnifiedDB, snapshots, receipts, logs or OCI layers.
- Paid/final training remains owner-authorization-only.
- Destructive tests use disposable/isolated state only.

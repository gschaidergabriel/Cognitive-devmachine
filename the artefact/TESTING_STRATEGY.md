# ClayVerse testing strategy — maximum evidence before final MicroVM gate

This policy applies to every product-convergent ClayVerse cycle until replaced by a later owner directive.

## Operating rule

Missing one external execution surface is **not a development blocker**. Source/product convergence continues while every independently executable evidence layer is maximized.

No source/component/container result may be promoted to whole-product PASS. Final `WHOLE_CLAYVERSE_PASS` requires the exact accepted ClayVerse OCI image to execute successfully **inside the mandatory independent guest-kernel VM/microVM envelope** defined by `deployment/MICROVM_DEPLOYMENT_CONTRACT.md`.

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
- kill managed PTY/tmux/Claude client while a causal turn remains open;
- fail GLM request/timeout and inject a stale GLM response after generation change;
- crash before an external effect is emitted, after emission but before acknowledgement, and after durable acknowledgement;
- interrupt UnifiedDB writes/WAL and recover to one consistent canonical generation;
- inject stale pre-crash results after recovery and require fail-closed rejection;
- corrupt/truncate newest snapshot and require fallback to the previous accepted known-good snapshot;
- crash again during recovery and require bounded/idempotent recovery rather than split brain;
- ambiguous effects become `UNKNOWN_AFTER_CRASH`/equivalent and are not blindly replayed;
- idempotent effects replay only when the EffectJournal proves replay safety;
- ingress remains frozen while the continuum is inconsistent;
- snapshot metadata binds UnifiedDB checkpoint, generations, EntityOS/config/policy hashes, causal queue position and EffectJournal state;
- snapshot restore cannot resurrect stale authorization, terminal sessions, effect leases or generations.

## Mandatory LLM-provider matrix

- Claude Code authenticates and operates through the managed internal terminal login/runtime path;
- Claude credential/session material is not canonical UnifiedDB cognition/memory and does not appear in receipts/logs;
- GLM token is injected only through the secret boundary and never appears in source, UnifiedDB, snapshots, receipts or logs;
- GLM receives no terminal/filesystem/EntityOS/EffectGate authority;
- provider switching preserves the same causal turn/session/global generation;
- model output from either provider is re-ingested as proposed action and cannot self-authorize execution.

## Mandatory MicroVM outer-envelope matrix

Final acceptance additionally requires all applicable checks below on the exact accepted image digest:

- launch through a VM/microVM OCI runtime such as the admitted Kata RuntimeClass rather than the default host-kernel runtime;
- prove the image digest executed in the guest equals the accepted image digest exactly;
- capture/attest microVM runtime identity/version and guest-kernel identity;
- prove the workload is behind an independent guest-kernel execution boundary;
- prove root filesystem read-only enforcement and undeclared-write denial;
- prove there is no `hostPath`, host PID/IPC/network authority or hidden host-shell execution path;
- prove only declared state/workspace persistent volumes survive full workload/microVM replacement;
- kill EntityOS and prove Tier-1 reconstruction;
- destroy/recreate the full workload/microVM and prove Tier-2 recovery from the same image digest plus UnifiedDB/WAL/known-good logical snapshot;
- prove stale results from the destroyed generation are rejected;
- crash around effect acknowledgement and prove no blind external replay;
- prove Claude direct-terminal login path and GLM inference-only secret boundary still satisfy their contracts inside the guest.

A normal OCI/container PASS without this independent guest-kernel layer is bounded evidence only.

## Evidence ladder

- `SOURCE_INSPECTED`
- `STATIC_CONTRACT_PASS`
- `FOCUSED_TEST_PASS`
- `ADJACENT_REGRESSION_PASS`
- `COMPONENT_RUNTIME_PASS`
- `MULTICOMPONENT_INTEGRATION_PASS`
- `EXACT_OCI_COMPONENT_PASS`
- `EXACT_MICROVM_COMPONENT_PASS`
- `WHOLE_CLAYVERSE_PASS`

A higher class must not be inferred from a lower one.

## Final exact gate

`exact source -> reproducible OCI image/digest -> complete EntityOS + UnifiedDB sealed continuum -> read-only runtime -> same exact digest launched inside VM/microVM guest kernel -> ingress/egress -> managed PTY/tmux -> Claude terminal login and/or GLM token inference -> cognition/re-ingest/execute/result loop -> EffectGate/EffectJournal -> Tier-1 recovery -> full microVM/workload destruction/recreation -> WAL/snapshot/new-generation recovery/no replay -> Clerk/WebSocket PTY -> dual-user concurrency -> final acceptance`.

Until that exact closure succeeds, continue maximizing all lower evidence layers.

## Safety boundaries

- No VPS/self-hosted/production-host testing unless separately authorized as deployment validation.
- No Together API.
- No secret persistence in source, UnifiedDB, snapshots, receipts or logs.
- Paid/final training remains owner-authorization-only.
- Destructive tests use disposable/isolated state only.

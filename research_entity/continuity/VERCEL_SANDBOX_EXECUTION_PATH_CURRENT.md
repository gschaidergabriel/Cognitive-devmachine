# Vercel Sandbox execution path — CURRENT

Status: **BRIDGE CONFIRMED / SANDBOX ADMISSION PROVEN / GITHUB TOKEN FORWARDING AUTHORIZED / FINAL TEST-OF-TESTS DEFINED**  
Current owner corrections: 2026-08-17 23:03 +07:00

## Current truth

The authorized bridge has actually created disposable Vercel Sandbox instances:

`Dr.-Unterweger Git preview -> Vercel build orchestration -> VERCEL_OIDC_TOKEN -> @vercel/sandbox -> Sandbox.create -> runCommand -> stop`.

Do not infer `Vercel Sandbox unavailable` merely because the connected ChatGPT Vercel connector does not export direct `sandbox.create` / `sandbox.exec` lifecycle actions.

Canonical staging project remains:
- repository: `gschaidergabriel/Dr.-Unterweger`;
- retained controller: draft PR **#810**;
- Vercel project: `dr-unterweger`;
- project id: `prj_ifIgM9X7jqIQS8mNIGllImziePPG`.

VPS/self-hosted/production-host testing remains forbidden. Together remains forbidden.

## Historical directly observed admission evidence

Two retained exact-closure runs reached `Sandbox.create=PASS_CREATED` and then stopped before private-source staging because `GITHUB_READ_TOKEN` was absent:

- deployment `dpl_21efibLYnww6hhrEMp5SAh6enCsQ`;
- deployment `dpl_7BkVnngPJUPiVyrqwFarGFZDevAG`.

The strongest historical exercised closure was bound to Research base `f7eb4df7600b0f4de1a6381a04acf5d1057d8f9b`, closure commit `5e5adce0591058608bbd7381ecf570a39b282f0d`, tree `1e02285d77b08e6edd86f9017d0ceac5db262cf2`, plus retained #611/#622 bytes.

Those historical runs produced **zero source/product/OCI runtime credit** because no private source was staged and no ClayVerse product assertion executed. They remain valid historical observations; newer owner policy changes do not retroactively change what happened.

## Owner correction — GitHub read token MAY enter the Sandbox

The previous rule that `GITHUB_READ_TOKEN` must remain host-side and must never be forwarded into the disposable Sandbox is **SUPERSEDED**.

A scoped read-only `GITHUB_READ_TOKEN` MAY be securely injected/forwarded into an authorized disposable Vercel Sandbox for the narrow purpose of fetching the bound private Research and EntityOS source inputs.

Current directive:
`research_entity/global/VERCEL_SANDBOX_GITHUB_READ_TOKEN_FORWARDING_DIRECTIVE.md`.

Required controls:
- never commit or print the token;
- never persist it in UnifiedDB, ClayGraph, snapshots, receipts, generated locks, OCI layers or durable workspace/state;
- prefer least privilege and bounded lifetime;
- after fetch, verify exact expected repository/commit/tree/blob/archive identity before product assertions receive provenance credit;
- fail closed on substitution or identity uncertainty;
- unset/remove the token when no longer required where the execution interface permits;
- stop/clean the Sandbox after the batch.

Therefore the blocker is no longer **"policy forbids token forwarding"**. The live prerequisite is simply that an appropriate read token be securely available/injectable at execution time.

## Final test-of-tests — mandatory

The newest owner directive makes the final acceptance run a real full-system test:

`Vercel Sandbox Firecracker microVM -> Docker/OCI runtime -> exact accepted ClayVerse OCI digest -> runtime Vault secret acquisition -> transient Mistral token injection -> full ClayVerse causal operation -> recovery -> repeat`.

The Vercel Sandbox microVM itself may serve as the independent guest-kernel outer envelope for this acceptance run; a second nested KVM guest is not required merely to satisfy the guest-kernel invariant when the Sandbox guest identity and exact inner OCI digest are both attested.

Current directive:
`research_entity/global/CLAYVERSE_FINAL_SANDBOX_TEST_OF_TESTS_DIRECTIVE.md`.

Mistral is a mandatory token/API inference provider for this final test. The token must be acquired at runtime from the approved Vault/secret store, injected transiently, never persisted, and reacquired after full appliance/Sandbox recreation.

## Next accepted execution sequence

At the next admitted run:

`refresh current Research main + retained admitted lanes`
`-> rebind retained #810 controller once`
`-> Sandbox.create`
`-> attest Sandbox Firecracker guest identity/kernel`
`-> securely inject GITHUB_READ_TOKEN`
`-> fetch exact private Research + EntityOS inside Sandbox`
`-> verify exact Git/object/artifact identities`
`-> reconstruct/attest accepted EntityOS`
`-> full exact source regressions`
`-> build exact ClayVerse OCI`
`-> capture exact image digest + APT/tmux/Claude/Python/supply-chain identities`
`-> install/start Docker in the Sandbox microVM or use an equivalently bound OCI runtime`
`-> run the EXACT accepted ClayVerse digest`
`-> enforce read-only root + declared state/tmpfs surfaces`
`-> retrieve Mistral token from approved Vault/secret store`
`-> inject token transiently into the running ClayVerse container`
`-> enable only admitted egress/auth paths`
`-> bring /healthz and full /readyz to their intended states`
`-> run real cognition through UnifiedDB/retrieval/workspace/Mistral`
`-> re-ingest model output before effect authority`
`-> execute safe admitted EntityOS/EffectGate round-trip`
`-> verify effect/outcome causal re-entry`
`-> verify one-entity/two-user generation and persistence contracts`
`-> exercise Tier-1 recovery`
`-> destroy/recreate the full Sandbox/appliance from the SAME image digest`
`-> recover UnifiedDB/WAL/snapshot/EffectJournal under a new generation`
`-> reacquire Mistral secret from Vault, never from recovered ClayVerse state`
`-> prove stale-result rejection and no blind effect replay`
`-> repeat real Mistral cognition after recovery`
`-> complete Clerk/WebSocket PTY + managed terminal + dual-user gates at admitted final scope`
`-> WHOLE_CLAYVERSE_PASS only if the complete vector is green`.

## Evidence law

- Sandbox creation alone is not product PASS.
- Successful private Git fetch alone is not product PASS.
- Successful OCI build alone is not product PASS.
- A direct Mistral API call outside ClayVerse is not product PASS.
- Container liveness alone is not product PASS.
- Whole-product credit requires the integrated exact-digest path and recovery/causal/security contracts actually to execute.

The prior bare Python 3.13 `_sqlite3` failure remains historical runtime-dependency evidence only and does not apply to the exact ClayVerse OCI path unless reproduced there.

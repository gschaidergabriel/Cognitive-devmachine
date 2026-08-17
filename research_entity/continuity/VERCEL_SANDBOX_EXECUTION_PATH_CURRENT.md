# Vercel Sandbox execution path — CURRENT

Status: **BRIDGE CONFIRMED / SANDBOX ADMISSION PROVEN / RUNTIME GITHUB TOKEN INGRESS IMPLEMENTED / FINAL TEST-OF-TESTS DEFINED**  
Current owner corrections: 2026-08-17 23:03–23:35 +07:00

## Current truth

The authorized bridge has actually created disposable Vercel Sandbox Firecracker microVMs and executed commands inside them. `Sandbox.create` is not the blocker.

Canonical staging project remains:
- repository: `gschaidergabriel/Dr.-Unterweger`;
- retained controller: draft PR **#810**;
- Vercel project: `dr-unterweger`;
- project id: `prj_ifIgM9X7jqIQS8mNIGllImziePPG`.

VPS/self-hosted/production-host testing remains forbidden. Together remains forbidden.

## Historical directly observed admission evidence

Previous retained runs reached `Sandbox.create=PASS_CREATED`, attested the guest kernel and then stopped before private-source staging because no `GITHUB_READ_TOKEN` was available to the build-triggered controller.

The latest such bounded run on controller v7 was deployment `dpl_6jeexw8EZa48jApm4NhgfaLMJoM5`: Sandbox admission passed, guest kernel `Linux 6.18.40 x86_64` was observed, then the run failed closed at `PRIVATE_SOURCE_STAGE_BLOCKED:GITHUB_READ_TOKEN_MISSING`, with source/OCI runtime credit still zero and clean Sandbox stop.

These remain valid historical observations only. They do not imply that the token must be configured in Vercel Environment Variables.

## Owner correction — GitHub read token MAY enter the Sandbox

The previous rule that `GITHUB_READ_TOKEN` must remain host-side and must never be forwarded into the disposable Sandbox is **SUPERSEDED**.

A scoped read-only `GITHUB_READ_TOKEN` MAY be securely injected/forwarded into an authorized disposable Vercel Sandbox for the narrow private Research/EntityOS fetch step.

Current directive:
`research_entity/global/VERCEL_SANDBOX_GITHUB_READ_TOKEN_FORWARDING_DIRECTIVE.md`.

Required controls remain:
- never commit or print the token;
- never persist it in UnifiedDB, ClayGraph, snapshots, receipts, generated locks, OCI layers or durable workspace/state;
- use least privilege and bounded lifetime;
- verify exact expected repository/commit/tree/blob/archive identity before provenance credit;
- fail closed on substitution or identity uncertainty;
- remove/unset the credential after the fetch where possible;
- stop/clean the Sandbox after the bounded batch.

## Runtime token ingress — no Vercel secret coupling required

The additional owner constraint is that the user cannot couple this GitHub token to Vercel as a Preview environment secret. The retained controller therefore now supports **runtime one-shot ingress** instead.

Current mechanism in PR #810:

`owner-held token -> HTTPS POST /api/go-cycle-v2 -> transient request/function memory -> exact private Research + EntityOS commit/tree access proof -> current v7 controller -> Sandbox.create -> token only in one Sandbox.runCommand env for private fetch -> exact source identity verification -> command exits -> token reference cleared -> fresh-process secret-absence fence -> continue source/OCI gates`.

Important properties:
- the Preview build itself no longer runs the private-source controller and no longer needs `GITHUB_READ_TOKEN`;
- the token is not a Vercel Environment Variable;
- the token is not committed;
- the token is not passed to Docker build args/context/image or ClayVerse runtime;
- the runtime endpoint accepts only POST and uses no-store/no-referrer/nosniff response policy;
- the controller defensively redacts the exact submitted token from returned child stdout/stderr;
- the branch also contains a password-style start panel that stores nothing in localStorage/cookies and clears the input immediately after constructing the request.

Observed deployment evidence for the architectural unblock:
- deployment `dpl_6RSuuunC96JnmXeXN3Z9eYGTceE9` on commit `ba52934acff8bd620e1d968dfa437bf96dbf1a54` reached **READY without any GitHub token configured** because `vercel-build` now performs only the exact retained source guard;
- that READY closure includes the runtime ingress endpoint commit;
- a direct GET to `/api/go-cycle-v2` returned `405 Method Not Allowed`, `Allow: POST`, and no-store/no-referrer/nosniff headers, proving the endpoint is deployed and fail-closed without an explicit start request.

Therefore the structural blocker **"GITHUB_READ_TOKEN must be coupled to Vercel Preview environment" is removed**. A real token value has still not been supplied through this new ingress during recorded evidence, so prior source/OCI runtime credit remains zero until the explicit one-shot run happens.

## Final test-of-tests — mandatory

The final acceptance run is a real full-system test:

`Vercel Sandbox Firecracker microVM -> Docker/OCI runtime -> exact accepted ClayVerse OCI digest -> runtime Vault/approved secret-store Mistral acquisition -> transient Mistral token injection -> full ClayVerse causal operation -> recovery -> full Sandbox/appliance destruction and recreation from the SAME image digest -> Vault secret reacquisition -> repeated real cognition`.

The Vercel Sandbox microVM itself may serve as the independent guest-kernel outer envelope; a second nested KVM/Kata guest is not required merely to satisfy that invariant when the Sandbox guest identity and exact inner OCI digest are both attested. Separate Kata deployment hardening remains useful additional evidence.

Mistral is mandatory for this final test as an inference provider only. Canonical Research now contains the final Mistral acceptance path (`the artefact/clayverse/final_acceptance_probe.py::run_mistral_acceptance_probe`) and final-only secret/model preflight hardening. The token must be acquired at runtime from the approved Vault/secret store, injected transiently, never persisted, and reacquired after full appliance/Sandbox recreation.

## Next accepted execution sequence

At the next real owner-started one-shot run:

`refresh exact current Research main + retained admitted lanes once`
`-> rebind retained #810 controller once`
`-> owner supplies scoped read-only GITHUB_READ_TOKEN through runtime POST/start panel, not Vercel Environment`
`-> Sandbox.create`
`-> attest Sandbox Firecracker guest identity/kernel`
`-> forward GitHub token only to one private-fetch command`
`-> fetch exact private Research + EntityOS inside Sandbox`
`-> verify exact Git/object/artifact identities`
`-> prove GitHub token absence after fetch`
`-> reconstruct/attest accepted EntityOS`
`-> full exact source regressions`
`-> build exact ClayVerse OCI`
`-> capture immutable image digest + APT/tmux/Claude/Python/supply-chain identities`
`-> run the EXACT accepted ClayVerse digest inside the Firecracker guest`
`-> enforce read-only root + declared persistent/tmpfs surfaces`
`-> retrieve Mistral token from approved Vault/secret store`
`-> inject Mistral token transiently into the running ClayVerse container`
`-> enable only admitted network/auth paths`
`-> bring /healthz and full /readyz to intended states`
`-> run real authenticated cognition through UnifiedDB/retrieval/workspace/Mistral`
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
- Runtime GitHub-token ingress alone is not product PASS.
- Successful private Git fetch alone is not product PASS.
- Successful OCI build alone is not product PASS.
- A direct Mistral API call outside ClayVerse is not product PASS.
- Container liveness alone is not product PASS.
- Whole-product credit requires the integrated exact-digest path and recovery/causal/security contracts actually to execute.

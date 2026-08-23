# Vercel Sandbox execution path — CURRENT

Status: **BRIDGE CONFIRMED / SANDBOX ADMISSION PROVEN / RUNTIME GITHUB TOKEN INGRESS IMPLEMENTED / OWNER ONE-SHOT REQUIRED**  
Current product authority: `research_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md`  
Canonical product workspace: `main/the artefact/`

## Authority boundary

This file is an execution-frontier record below the current ClayVerse owner directive and current `the artefact/manifest.json`. If historical text in this file conflicts with those authorities, the ClayVerse directive/manifest wins and this file must be repaired rather than routing product work through a retired runtime.

Current canonical visible runtime is:

`Browser -> Clerk -> verified JWT -> authenticated WebSocket PTY -> persistent user-bound tmux -> normal interactive Claude Code -> managed UserPromptSubmit/Stop/StopFailure hooks -> UnifiedDB causal lifecycle -> retrieval/workspace -> candidate reasoning -> effect-only MCP/EffectGate -> optional separately admitted EntityOS -> verified outcome -> causal re-entry`.

The historical Mistral/custom-engine acceptance path and headless `claude -p` path are retired product runtimes. Current `the artefact/clayverse/final_acceptance_probe.py` is intentionally a fail-closed compatibility tombstone and MUST NOT be treated as final acceptance machinery. GLM remains only the separate token/API inference-only path described by the current manifest where that accepted profile requires it; it never replaces the canonical terminal/Claude Code path or gains state/effect authority.

## Current Vercel truth

The authorized bridge has actually created disposable Vercel Sandbox Firecracker microVMs and executed commands inside them. `Sandbox.create` is not the blocker.

Canonical staging project remains:
- repository: `gschaidergabriel/Dr.-Unterweger`;
- retained controller: draft PR **#810**;
- Vercel project: `dr-unterweger`;
- project id: `prj_ifIgM9X7jqIQS8mNIGllImziePPG`.

VPS/self-hosted/production-host testing remains forbidden. Together remains forbidden.

## Historical directly observed admission evidence

Previous retained runs reached `Sandbox.create=PASS_CREATED`, attested the guest kernel and then stopped before private-source staging because no `GITHUB_READ_TOKEN` was available to the build-triggered controller.

The bounded controller-v7 run on deployment `dpl_6jeexw8EZa48jApm4NhgfaLMJoM5` observed Sandbox admission plus guest kernel `Linux 6.18.40 x86_64`, then failed closed at `PRIVATE_SOURCE_STAGE_BLOCKED:GITHUB_READ_TOKEN_MISSING`, with source/OCI runtime credit still zero and clean Sandbox stop.

These are historical observations only. They do not imply that the token must be configured in Vercel Environment Variables and do not establish current-source or product-runtime PASS.

## Owner-corrected GitHub read-token ingress

A scoped read-only `GITHUB_READ_TOKEN` MAY be securely injected/forwarded into an authorized disposable Vercel Sandbox for the narrow private Research/EntityOS fetch step under `research_entity/global/VERCEL_SANDBOX_GITHUB_READ_TOKEN_FORWARDING_DIRECTIVE.md`.

Required controls:
- never commit or print the token;
- never persist it in UnifiedDB, ClayGraph, snapshots, receipts, generated locks, OCI layers or durable workspace/state;
- use least privilege and bounded lifetime;
- verify exact expected repository/commit/tree/blob/archive identity before provenance credit;
- fail closed on substitution or identity uncertainty;
- remove/unset the credential after the fetch where possible;
- prove credential absence in a fresh process after fetch;
- stop/clean the Sandbox after the bounded batch.

The user cannot couple this GitHub token to Vercel as a Preview environment secret. The retained controller therefore supports runtime one-shot ingress:

`owner-held token -> HTTPS POST /api/go-cycle-v2 -> transient request/function memory -> exact private Research + EntityOS access proof -> Sandbox.create -> token only in one Sandbox.runCommand env for private fetch -> exact source identity verification -> command exits -> token reference cleared -> fresh-process secret-absence fence -> continue exact-source/OCI gates`.

The Preview build itself does not need the GitHub token. The token is not a Vercel Environment Variable, not committed, and must never enter Docker build args/context/image or ClayVerse runtime.

Observed architectural-unblock evidence:
- deployment `dpl_6RSuuunC96JnmXeXN3Z9eYGTceE9` on commit `ba52934acff8bd620e1d968dfa437bf96dbf1a54` reached READY without a configured GitHub token;
- the runtime ingress endpoint was deployed;
- direct GET to `/api/go-cycle-v2` returned `405 Method Not Allowed`, `Allow: POST`, plus no-store/no-referrer/nosniff headers.

No recorded owner-started token-bearing run through this ingress exists yet. Therefore current private-source/full-suite/OCI runtime credit remains zero.

## Final test-of-tests — current ClayVerse form

The whole-product acceptance run must exercise the current product, not a retired inference wrapper:

`Vercel Sandbox Firecracker guest -> exact accepted ClayVerse OCI digest -> Clerk/browser/WebSocket PTY -> persistent tmux -> normal interactive Claude Code + managed hooks -> UnifiedDB/retrieval/workspace -> candidate reasoning -> EffectGate/optional admitted EntityOS -> causal outcome re-entry -> persistence/recovery -> full Sandbox/appliance destruction and recreation from the SAME image digest -> recovered canonical state under a new generation -> repeated canonical operation`.

The Vercel Sandbox Firecracker guest may serve as the independent guest-kernel outer envelope when its guest identity and the exact inner OCI digest are both attested. A second nested KVM/Kata guest is not required merely to satisfy that invariant. Separate Kata deployment hardening remains additional evidence.

Provider law for final acceptance:
- canonical interactive cognition must prove normal Claude Code terminal login/runtime through the managed PTY/tmux surface;
- any API provider retained by the exact accepted manifest/profile (currently the separate GLM inference-only path in the manifest) must be verified only at its bounded inference boundary, with transient secret handling and zero direct state/effect authority;
- no historical Mistral acceptance probe, custom chat API or headless `claude -p` route receives product credit;
- model completion alone is never reward, truth or effect authority.

EntityOS execution remains conditional. If the accepted profile keeps `CLAYVERSE_ENABLE_ENTITYOS_EXEC=0`, exact staged identity verification is sufficient for that baseline; if execution is explicitly admitted, the exact embedded artifact and admitted EffectGate round-trip must also pass.

## Next accepted execution sequence

At the next real owner-started one-shot run:

`refresh exact current Research main + retained admitted controller once`
`-> rebind retained #810 controller to that exact source identity`
`-> owner supplies scoped read-only GITHUB_READ_TOKEN through runtime POST/start panel, not Vercel Environment`
`-> Sandbox.create`
`-> attest Firecracker guest identity/kernel`
`-> forward GitHub token only to one private-fetch command`
`-> fetch exact private Research + required EntityOS artifact inside Sandbox`
`-> verify exact Git/object/artifact identities`
`-> prove GitHub token absence after fetch`
`-> run exact-current ClayVerse full regressions, including OCI service import-closure guard`
`-> build exact ClayVerse OCI`
`-> capture immutable image digest plus APT/tmux/Claude/Python/supply-chain identities`
`-> run the EXACT accepted ClayVerse digest inside the Firecracker guest`
`-> enforce non-root/read-only-root/declared persistent+tmpfs write surfaces`
`-> bring /healthz and full /readyz to intended states`
`-> run real Clerk-authenticated WebSocket PTY sessions for both canonical users`
`-> prove persistent tmux + normal interactive Claude Code + managed lifecycle hooks`
`-> prove UnifiedDB authority, MicroClay/retrieval, ClayGraph/Hyperposition/workspace boundaries`
`-> re-ingest candidate reasoning before any real effect authority`
`-> execute a safe admitted EffectGate round-trip; include EntityOS only if explicitly admitted`
`-> verify effect/outcome causal re-entry and stale-generation fencing`
`-> verify one-entity/two-user persistence/concurrency/privacy contracts`
`-> exercise Tier-1 recovery`
`-> destroy/recreate the full Sandbox/appliance from the SAME image digest`
`-> recover UnifiedDB/WAL/snapshot/EffectJournal under a new generation`
`-> prove stale-result rejection and no blind effect replay`
`-> repeat canonical authenticated cognition after recovery`
`-> verify any manifest-retained API inference-only provider boundary without granting it terminal/state/effect authority`
`-> WHOLE_CLAYVERSE_PASS only if the complete current acceptance vector is green`.

## Evidence law

- Sandbox creation alone is not product PASS.
- Runtime GitHub-token ingress alone is not product PASS.
- Successful private Git fetch alone is not product PASS.
- Successful OCI build alone is not product PASS.
- A direct provider API call outside the canonical ClayVerse lifecycle is not product PASS.
- Container liveness alone is not product PASS.
- Source/component regressions and PR merges do not imply exact OCI/runtime acceptance.
- Whole-product credit requires the integrated exact-digest current ClayVerse path and recovery/causal/security contracts actually to execute.

# ClayVerse Final Sandbox Test-of-Tests Directive

**Authority:** explicit owner directive, 2026-08-17 23:03 +07:00  
**Status:** CURRENT / MANDATORY FINAL ACCEPTANCE GATE  
**Product:** ClayVerse single-container

## Owner intent

The final **test of tests** is a real end-to-end execution of the finished ClayVerse artifact, not a source-only, mock-only, container-only or component-only test.

The mandatory final test topology is:

`Vercel Sandbox Firecracker microVM -> Docker/OCI runtime inside that Sandbox -> exact accepted ClayVerse OCI image digest -> runtime secret acquisition from approved Vault/secret store -> Mistral token injected transiently -> full ClayVerse operation`.

The Vercel Sandbox itself supplies the required independent guest-kernel VM/microVM isolation envelope for this acceptance run. A second nested KVM guest is not required merely to satisfy the guest-kernel invariant, provided the run captures evidence that ClayVerse executes inside the Sandbox microVM and the exact accepted OCI image digest executes inside that guest boundary.

This final acceptance run does not change the release form: ClayVerse remains **one OCI/Docker-compatible container image**.

## Mistral acceptance provider

Mistral is now a **mandatory token/API inference provider for the final test-of-tests**.

This does not make Mistral a state, identity, effect or memory authority. It remains an inference boundary only.

The final test MUST:

1. acquire a valid Mistral API token at runtime from the approved Vault/secret store or equivalent owner-approved secret boundary;
2. keep the token outside Git source and outside the OCI image;
3. inject it transiently into the running ClayVerse container as `MISTRAL_API_KEY` or the canonical runtime secret mapping used by the accepted implementation;
4. never print, echo, persist or serialize the token value into logs, receipts, UnifiedDB, ClayGraph, snapshots, generated locks, image layers or durable workspace/state;
5. allow only the admitted Mistral API egress required by the test, plus other explicitly required authenticated product dependencies;
6. prove a real Mistral inference request succeeds from the running ClayVerse continuum;
7. bind the returned model/provider response to the same canonical turn/session/generation and re-ingest it into ClayVerse before any action/effect;
8. prove the model cannot bypass EffectGate/EntityOS or mint canonical truth merely by responding;
9. reacquire/inject the secret after full appliance replacement rather than depending on secret persistence inside the destroyed runtime.

Existing Claude Code and GLM research/provider paths remain bounded product functionality unless separately superseded. The Mistral requirement is mandatory for this final acceptance test and does not fork the central entity or create another canonical state path.

## GitHub read-token correction

The separately issued owner correction permitting secure `GITHUB_READ_TOKEN` forwarding into the authorized Vercel Sandbox remains in force. Private Research/EntityOS source may therefore be fetched inside the Sandbox when the token is securely injected, followed by exact commit/tree/blob/archive verification before execution receives provenance credit.

## Required test-of-tests sequence

The final sequence is:

`refresh exact current canonical source and admitted lanes`
`-> Sandbox.create`
`-> attest Sandbox/microVM identity and guest kernel`
`-> securely inject scoped GITHUB_READ_TOKEN if private source fetch is required`
`-> fetch exact private Research + EntityOS source`
`-> verify exact requested Git/object/artifact identities`
`-> build/reproduce exact ClayVerse OCI candidate`
`-> capture immutable image digest and dependency/runtime identities`
`-> install/start Docker inside the Sandbox microVM or use an equally bound OCI runtime`
`-> run EXACT accepted ClayVerse image digest inside that Sandbox guest`
`-> enforce read-only root + declared persistent/tmpfs surfaces`
`-> retrieve Mistral token from approved Vault/secret store at runtime`
`-> inject token transiently into ClayVerse`
`-> establish only admitted network paths`
`-> bring full ClayVerse readiness to PASS`
`-> execute real authenticated user/cognition turn through UnifiedDB retrieval/workspace/Mistral inference`
`-> re-ingest model response`
`-> execute at least one admitted bounded EntityOS/EffectGate effect round-trip where safe`
`-> verify stdout/stderr/outcome/effect receipt causal re-entry`
`-> verify durable state/memory/provenance and ClayGraph rebuildability`
`-> exercise Gabriel + Andreas shared one-entity generation/concurrency invariants`
`-> exercise Clerk/WebSocket PTY and managed terminal path when credentials are available for final acceptance`
`-> execute Tier-1 internal recovery`
`-> execute Tier-2 full Sandbox/appliance destruction and recreation from the SAME image digest`
`-> recover UnifiedDB/WAL/snapshot/EffectJournal under a new generation`
`-> reacquire Mistral token from Vault rather than recovering it from ClayVerse state`
`-> prove stale pre-crash results are rejected and ambiguous effects are not blindly replayed`
`-> repeat a real Mistral cognition turn after recovery`
`-> verify token non-persistence/redaction`
`-> WHOLE_CLAYVERSE_PASS only if the complete admitted vector is green`.

## Meaning of fully functional

For this gate, `fully functional` means the integrated product path actually operates, not just that the container process stays alive.

At minimum the run must demonstrate:
- exact one-entity/two-perspective identity semantics;
- UnifiedDB canonical state/memory authority;
- ClayGraph rebuildability;
- bounded retrieval/workspace path;
- real Mistral inference with runtime Vault secret injection;
- model-response re-ingestion before effects;
- managed EffectGate/EntityOS round-trip;
- causal result re-entry and state update;
- persistent state continuity;
- managed terminal/PTY path at accepted scope;
- auth boundary at accepted scope;
- read-only/secret/network isolation contracts;
- Tier-1 and Tier-2 recovery;
- global generation fencing and no blind effect replay;
- secret reacquisition instead of secret persistence after recreation.

A partial pass on any subset is component/integration evidence only and may not be labeled `WHOLE_CLAYVERSE_PASS`.

## Secret/vault law

The Vault/secret store remains external credential authority only. It is not canonical ClayVerse memory or world state.

Secret values are never part of durable reasoning/evidence. Receipts may record only non-secret metadata needed to prove the boundary, for example secret source class, injection mechanism, redaction checks, token-present boolean at the intended process boundary, and digest/identity of non-secret configuration.

## Failure law

If the Sandbox microVM cannot run Docker/the exact image, cannot acquire the required secret securely, cannot reach Mistral under the admitted egress policy, cannot complete the real causal loop, or cannot recover cleanly, the final test remains `BLOCKED` or `FAIL` at the actually observed boundary. Do not substitute a mock, host process, direct API call outside ClayVerse, or weaker container-only proxy result.

VPS/self-hosted/production-host testing remains forbidden unless separately authorized for deployment validation. Together remains forbidden. Final paid/model training remains owner-authorization-required.

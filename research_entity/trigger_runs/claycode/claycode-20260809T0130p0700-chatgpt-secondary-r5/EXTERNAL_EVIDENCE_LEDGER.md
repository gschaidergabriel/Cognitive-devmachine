# ClayCode r5 — External Evidence Ledger

Evidence classes remain separate from RAE-internal convergence and from this run's E2B experiments.

## Primary / authoritative implementation documentation

### Wasmtime Security — Bytecode Alliance
- Class: authoritative runtime documentation.
- Relevant result: WebAssembly executes in a sandbox; outside interaction occurs through explicitly linked imports/exports rather than raw ambient system access. Wasmtime's WASI filesystem model is capability based.
- Transfer to ClayCode: supports an external capability-root architecture and child-effect containment as a plausible enforcement class.
- Does **not** prove: UECC/CBEL-TV correctness, FRANK safety, or exact permit tuple minimality.
- Source: https://docs.wasmtime.dev/security.html

### WASI.dev Introduction
- Class: authoritative standards/community documentation.
- Relevant result: WASI applications/components run in a capability-based sandbox and begin with no ambient authority; hosts explicitly grant capabilities.
- Transfer: strong independent precedent for `EffectIntent != EffectPermit` and deployment-profile authority rather than source-language word bans.
- Source: https://wasi.dev/

### WebAssembly Component Model — Canonical ABI
- Class: authoritative Component Model documentation.
- Relevant result: different implementation languages/layouts communicate through a canonical ABI; logical interface meaning need not equal internal byte layout.
- Transfer: supports `semantic identity != lowering representation identity` and motivates translation validation at ABI boundaries.
- Source: https://component-model.bytecodealliance.org/advanced/canonical-abi.html

## Independent 2026 research literature

### SEAgent — arXiv:2601.11893
- Class: preprint / agent-security research.
- Result class: models over-privileged tool use as privilege escalation, including confused-deputy-like failures; proposes external mandatory access control over agent-tool interactions.
- Transfer: independent support for authority checks outside model text and for least-privilege/context-aware release.
- Limitation: not a ClayCode compiler study.

### Agentic Permissions Policy Algebra — arXiv:2607.24625
- Class: preprint / agent permission & taint-confinement research.
- Transfer: independent support for preserving permission/taint semantics across agent/tool flows rather than treating current producer identity as sufficient trust.
- Limitation: exact ClayCode origin-envelope fields are not independently established.

### From Untrusted Input to Trusted Memory — arXiv:2606.04329
- Class: preprint / memory-poisoning research.
- Transfer: supports use-time contextual validation and preserved origin/integrity labels; trusted storage/presence alone is insufficient.
- Limitation: does not prove the exact `closure_state` policy.

### Axon Verified Compiler — arXiv:2605.01660
- Class: preprint / compiler verification.
- Transfer: independent support for credible compilation/translation validation instead of assuming that successful code generation preserves intended semantics.
- Limitation: does not verify ClayCode or the current authority oracle.

## Community/implementation evidence

Community discussion was treated only as engineering evidence in predecessor CC13 and is not used here to promote any scientific claim.

## Evidence synthesis

The external evidence supports the **architecture class**:

`general computation + typed effect intent + no ambient authority + externally rooted capabilities + semantics-preserving lowering/validation`.

It does not independently prove the exact current ClayCode type set, exact eight-field binding tuple, target-Qwen usability, or production FRANK safety. Those remain open and falsifiable.

# the artefact — ClayVerse single-container product

`the artefact/` is the canonical product workspace for ClayVerse in `gschaidergabriel/clay-global-research-entity/main`.

Current owner directive: `research_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md`.

The active release endpoint is **one OCI/Docker-compatible ClayVerse container image**. Earlier Mini Entity / Blogpost endpoint wording is historical donor evidence only and must not override the current ClayVerse authority spine.

## Product law

ClayVerse is one persistent central entity with exactly two equal-rights user perspectives: `gabriel` and `andreas`.

Canonical runtime path:

`Browser -> Clerk -> verified JWT -> authenticated WebSocket PTY -> user-bound persistent tmux -> normal interactive Claude Code -> managed UserPromptSubmit/Stop/StopFailure hooks -> UnifiedDB -> MicroClay/ClayGraph/Hyperposition/workspace context -> Claude reasoning -> effect-only MCP -> EffectGate -> optional admitted EntityOS -> verified outcome -> causal re-entry -> UnifiedDB`

Authority boundaries:

- **UnifiedDB** is the sole durable canonical state/world/memory/data/wiki/causal authority.
- **ClayGraph** is derived and rebuildable only.
- **Claude Code** is runtime cognition; it cannot own durable identity, canonical truth, memory, or effects.
- **MicroClay** learns retrieval/entry-point accessibility only; it cannot mint truth or permissions.
- **EffectGate + EffectJournal** own the admitted external/state-changing effect path.
- **EntityOS** is an internal hardened execution/security/runtime substrate; it is not the product endpoint and never becomes a second authority.
- No hidden second transcript, database, identity service, effect path, recovery ledger, or consciousness daemon is allowed.

## Container boundary

The final product must converge into one exact OCI image built from this workspace. Final acceptance must bind exact source/image identity and the selected isolated runtime environment. Required hardening includes non-root execution, read-only root filesystem at admitted scope, dropped capabilities, `no-new-privileges`, bounded tmpfs, explicit persistent state/workspace volumes, runtime-injected secrets, and reproducible supply-chain evidence.

A source candidate, component PASS, PR merge, CI definition, deployment READY state, historical receipt, or synthetic demo does not imply whole-product PASS.

## Canonical state and recovery

The two canonical sessions share one global live entity generation. Restart/recovery must explicitly close or re-enter interrupted turns, fence stale writers, expire leases, rebuild ClayGraph from UnifiedDB, preserve checkpoints and uncertainty, and never blindly replay an ambiguous external effect.

Unknown outcomes remain unknown until verified.

## Memory, retrieval, and meta-learning

MicroClay is a persistent bounded retrieval/entry-point organ inside the same entity. It starts in SHADOW behind a deterministic safe baseline and may be promoted only through held-out/replay evidence with contamination, staleness, miss-rate, personalization, latency, causal utility, and authority leakage measured.

Meta-learning preserves reusable validated methods separately from factual evidence. Mandatory invariant:

`FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT`

Methods suggest how to investigate; they never manufacture missing facts.

## Current acceptance frontier

Whole ClayVerse acceptance remains **IN_PROGRESS**. Required current gates include:

- exact current source identity and full authorized isolated regression;
- exact OCI build + image digest + startup/readiness;
- real Clerk JWT/browser/WebSocket PTY;
- both persistent tmux sessions and normal interactive Claude Code;
- managed prompt/Stop/StopFailure lifecycle bound to UnifiedDB;
- UnifiedDB persistence/restart/recovery and one global generation;
- MicroClay retrieval falsifiers and SHADOW-vs-baseline benchmark;
- ClayGraph/Hyperposition/workspace fail-closed behavior;
- effect-only MCP/EffectGate and admitted EntityOS round trip;
- crash/restart with no unsafe external replay;
- dual-session collision/privacy/stale-generation controls;
- supply-chain closure and exact deployment-runtime evidence.

## Execution policy

Current build/test/experiment/runtime validation is isolated-sandbox-only. VPS/self-hosted/production-host testing is forbidden unless a newer explicit owner directive changes it.

Together API/service is forbidden. Secrets never enter source or receipts. Final paid/model training requires explicit owner authorization.

## 2026-08-23 `go` delta — authority reconciliation

Observed `main` carried a split-brain authority state: `the artefact/manifest.json` and `ARCHITECTURE.md` named ClayVerse/one OCI image as the product, while `BOOTSTRAP_MINIMAL.json`, `PROGRAM_STATE.json`, this README, the ClayVerse fast-bootstrap shim, and the visible status footer still declared Mini Entity/Blogpost current and ClayVerse superseded.

This cycle reconciles those control-plane files to the current ClayVerse owner directive and adds `tools/validate_clayverse_authority_consistency.py` plus deterministic regressions so a future split cannot silently pass source admission.

Runtime credit remains **ZERO** for this delta because no exact authorized whole-product sandbox start/exec surface was available through the connected Vercel tool. Local deterministic validator tests are source/mechanism evidence only.

## 2026-08-23 `go` delta — inherited control fence

Adversarial review found a narrower fail-open after the authority reconciliation: validator v2 checked the new Control 4.4 preservation claims but did not directly read the inherited 4.1, 4.2 and 4.3 control files. A weakened inherited FREE_ONLY, VPS/self-hosted or exact-runtime-evidence rule could therefore be hidden behind unchanged 4.4 self-attestation.

Validator v3 now checks the effective 4.1 -> 4.2 -> 4.3 -> 4.4 chain directly and adds poison regressions for paid fallback, direct VPS execution and loss of exact admitted runtime evidence. Bounded reconstructed component evidence is Python compile PASS and 9/9 focused regressions PASS; exact-current branch/OCI/whole-product runtime credit remains zero until an actually-started authorized isolated executor is available.

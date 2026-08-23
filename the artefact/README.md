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
- **EntityOS** is an **optional** internal hardened execution/security/runtime substrate. Omission with EntityOS execution disabled does not by itself block whole-product PASS. If EntityOS is staged or enabled, its exact bytes and admission evidence remain mandatory for that candidate. It is never the product endpoint or a second authority.
- No hidden second transcript, database, identity service, effect path, recovery ledger, or consciousness daemon is allowed.

## Container boundary

The final product must converge into one exact OCI image built from this workspace. Final acceptance must bind exact source/image identity and the selected isolated runtime environment. Required hardening includes non-root execution, read-only root filesystem at admitted scope, dropped capabilities, `no-new-privileges`, bounded tmpfs, explicit persistent state/workspace volumes, runtime-injected secrets, and reproducible supply-chain evidence.

The current Dockerfile still stages digest-bound EntityOS bytes and keeps execution disabled by default. That is a current candidate packaging choice, not a permanent ClayVerse product-authority requirement.

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
- effect-only MCP/EffectGate, plus EntityOS effect round trip only when EntityOS is included/enabled;
- crash/restart with no unsafe external replay;
- dual-session collision/privacy/stale-generation controls;
- supply-chain closure and exact deployment-runtime evidence.

## Execution policy

Current build/test/experiment/runtime validation is isolated-sandbox-only. VPS/self-hosted/production-host testing is forbidden unless a newer explicit owner directive changes it.

Together API/service is forbidden. Secrets never enter source or receipts. Final paid/model training requires explicit owner authorization.

## 2026-08-23 `go` delta — authority reconciliation

Observed `main` carried a split-brain authority state: `the artefact/manifest.json` and `ARCHITECTURE.md` named ClayVerse/one OCI image as the product, while `BOOTSTRAP_MINIMAL.json`, `PROGRAM_STATE.json`, this README, the ClayVerse fast-bootstrap shim, and the visible status footer still declared Mini Entity/Blogpost current and ClayVerse superseded.

That control-plane split was reconciled to the current ClayVerse owner directive and `tools/validate_clayverse_authority_consistency.py` was added with deterministic regressions so a future product-authority split cannot silently pass source admission.

## 2026-08-23 `go` delta — optional EntityOS authority fence

A post-merge adversarial review found a second, narrower authority drift: `manifest.json` still described EntityOS as `MANDATORY_IN_FINAL_ACCEPTED_IMAGE` and required embedded EntityOS bytes for whole-product PASS, while the current owner directive and canonical product path define EntityOS as an optional, separately admitted internal substrate.

This delta aligns bootstrap/directive/manifest/README and upgrades the authority validator to v3. The validator now fails closed if either bootstrap or manifest turns EntityOS back into an unconditional whole-product requirement. The current Dockerfile may continue staging exact EntityOS bytes as a candidate implementation choice; staging does not mint product authority.

Runtime credit remains **ZERO** for these authority deltas because no actually-started authorized whole-product sandbox start/exec surface is available through the connected execution tools. GitHub-hosted jobs observed for the authority-reconciliation branch failed before visible steps (`steps=null`), which is execution-admission failure rather than semantic test failure.

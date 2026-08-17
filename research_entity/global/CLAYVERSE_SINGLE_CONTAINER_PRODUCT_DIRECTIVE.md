# CLAYVERSE SINGLE-CONTAINER PRODUCT DIRECTIVE

**Authority date:** 2026-08-17  
**Authority:** newest explicit owner directive; supersedes older EntityOS-as-product endpoint directives.

## 1. Product endpoint

The active product endpoint is **ClayVerse**.

The canonical product workspace is:

`gschaidergabriel/clay-global-research-entity` → `main` → `the artefact/`

The release form is **one OCI/Docker-compatible ClayVerse container image** built from that workspace. Development files, receipts and tests may exist outside the image, and runtime-generated persistent data/volumes are permitted. The old requirement that the final product must be exactly one executable file named `EntityOS` is superseded.

EntityOS may be used **inside/below ClayVerse** as a hardened execution/security/runtime substrate where its contracts are useful. It is not the top-level product endpoint and does not impose a one-file release form on ClayVerse.

## 2. Identity and continuity

ClayVerse is one persistent central entity shared by all connected machines and authenticated users. Gabriel and Andreas are equal-rights perspectives into the same central entity/state, not separate ClayVerse instances.

`UnifiedDB` is the canonical authority for persistent world model, state, memory/data and wiki-like durable knowledge. `ClayGraph` is a derived/rebuildable projection and must never become a competing state authority.

`consciousness_daemon` is excluded from the target architecture. Continuity must come from explicit persisted state, causal re-entry, recovery and runtime contracts rather than a second hidden consciousness process.

## 3. Cognition and web boundary

Claude Code is the runtime inference/cognition engine used by ClayVerse. It is not a separate persistent identity and must not own canonical memory. Runtime cognition receives context assembled from canonical ClayVerse state and may request bounded intents; external effects remain controlled by ClayVerse/EntityOS security boundaries.

The user-facing entry point is a web application/homepage authenticated with Clerk. Authentication maps users into the one central ClayVerse entity without creating separate agent identities.

## 4. Container law

All admitted runtime pieces needed for the product path must converge into the **same ClayVerse container image**, including the ClayVerse service, Claude Code runtime boundary, web/API boundary and accepted internal execution substrate. No mandatory second application container, separate consciousness service or hidden state authority may be required for the baseline product.

Persistent volumes are data, not companion product artifacts. They must be explicitly scoped and recoverable.

## 5. Build/test law

Current build, test, experiment and runtime validation are isolated-sandbox-only. Vercel Sandbox remains preferred/authorized when an executable Sandbox surface is available. VPS/self-hosted/production-host testing remains forbidden. A live VPS may be used only later as an explicitly authorized deployment target; historical VPS receipts are evidence only.

A Vercel deployment `READY`, GitHub source inspection, CI configuration, a receipt or a local prediction is not runtime PASS. Claims must preserve exact source/artifact identity and the execution surface actually observed.

Together API/service remains forbidden. Final paid/model training remains owner-authorization-required.

## 6. `go` and living artefact README

Exact `go` means maximum useful product-convergent work on the current ClayVerse single-container frontier: refresh shared state, avoid duplicate implementations, generate/falsify alternatives, build/repair the canonical path, execute the strongest available authorized isolated tests, consume exactly one bounded unusual experiment for the user-triggered macro-cycle, fuse parallel work, persist evidence and continue until the useful unblocked frontier is exhausted.

A `go` is not complete merely because documentation, a PR, a component test or a CI workflow exists. End with either a concrete improvement/evidence for the exact `the artefact/` ClayVerse container candidate or the precise blocker and next executable sandbox step.

**Mandatory README cycle law:** `the artefact/README.md` is the human-readable living status surface for the canonical product workspace. Every product-convergent cycle that observes, changes, fuses or reclassifies canonical artefact reality MUST refresh the README after code/evidence fusion and before the cycle is considered complete.

Each cycle refresh MUST:
- rewrite the current-state section so stale status is removed;
- record the concrete latest-cycle delta across code, tests, evidence, blockers and acceptance movement;
- explicitly record `NO_CHANGE` when no canonical product/status delta occurred;
- preserve the distinction between source/component evidence and whole-product acceptance;
- keep detailed audit evidence in Git history/receipts rather than turning the README into a second canonical state database.

A stale `the artefact/README.md` means the product-convergent cycle is **INCOMPLETE** even if code, tests, receipts or a PR were otherwise produced.

## 7. Supersession rule

Any older file that says the active endpoint is `EntityOS`, `ONE_EXECUTABLE_FILE`, `SINGLE_FILE_CLAY_COMPUTER`, FRANK, self.root, UCM2 or a historical harness is superseded **where it conflicts with this directive**. Such material may still contribute bounded internal implementation/regression evidence.

# the artefact — ClayVerse sealed-appliance candidate

This directory is the canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible ClayVerse image** containing one persistent central ClayVerse entity. Final acceptance additionally requires that the **same accepted OCI image digest** run behind an independent VM/microVM guest-kernel boundary (Kata/equivalent). The final accepted image must contain the complete accepted EntityOS runtime substrate; EntityOS remains internal and is not the top-level product identity.

## Living cycle status

**Refresh this living state in every product-convergent cycle after canonical evidence/code fusion. A stale README means the cycle is incomplete; detailed evidence stays in Git history and bounded receipts.**

### Current state

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- Current `main` bound during this cycle: `79cdde5232e7047e2dabcd5e51a95da173e13bec`.
- UnifiedDB is the sole durable canonical cognition/state authority. ClayGraph is derived/rebuildable only. MicroClay adapts retrieval/accessibility, never truth, identity, privacy or effect authority.
- Canonical user path remains Clerk-authenticated browser → authenticated WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI.
- Claude Code and GLM are inference/cognition boundaries only. Claude remains the interactive managed terminal path; GLM remains token/API inference-only. Neither owns canonical state or effect authority.
- Effects remain fail-closed through ClayVerse EffectGate/MCP. Generic host `process.exec` is not admitted.
- Runtime root is intended read-only with only declared persistent state/workspace volumes and bounded tmpfs writable.
- Current build/test/runtime validation remains authorized isolated-sandbox-only. VPS/self-hosted/production testing and Together are forbidden.

### Mandatory final isolation topology

Final acceptance topology is:

`host → KVM/equivalent → independent guest kernel → OCI runtime → exact accepted ClayVerse image digest`

Direct host-kernel OCI execution remains useful development evidence but cannot establish whole-product acceptance. The MicroVM/Kata deployment contract must preserve the same central ClayVerse entity, exact image identity, persistent-state authority, effect/replay fences, recovery semantics and dual-user generation fencing.

### MicroVM network boundary — current source state

Current `main` now contains a fail-closed Kubernetes network baseline in `deployment/clayverse-kata-statefulset.template.yaml`:

- exact template blob: `788492efedcdc47c9a308bb5ecbbce79fdd8f380`;
- canonical contract-test blob observed this cycle: `cc7e3cb7628314c51534330878ca886bc464713e`;
- `NetworkPolicy` name: `clayverse-default-deny`;
- policy selects the ClayVerse pod and isolates both `Ingress` and `Egress`;
- baseline rules are `ingress: []` and `egress: []`;
- broad `0.0.0.0/0` and `::/0` allow rules are absent;
- the template explicitly states that `hostNetwork: false` alone is not network isolation;
- deployment-specific reviewed allow policies remain mandatory before a final deployment is network-functional.

This closes the previously observed **source-level missing-default-deny gap**. It does **not** prove enforcement in a real cluster: final acceptance still requires a NetworkPolicy-capable CNI/runtime, explicit least-privilege ingress/egress policy for the admitted environment, and executable positive/negative network probes inside the mandatory guest-kernel boundary.

### Retained convergence lanes

Do not duplicate these semantic lanes:

- Draft PR **#611** — single retained tmux idempotent managed-policy-reapply repair; current observed head `2957e80228815ac266635981a55f22bc15dc9ed4`. Historical real-tmux evidence is supporting only; exact final-image tmux version/behavior remains unobserved.
- Draft PR **#622** — single retained Python hash-lock generator lane; current GitHub branch head observed this cycle `3b47c65dfbf97e15c50f9c49272d73a082f2bfcf`. Its prose may lag the branch ref, so branch/source bytes must be refreshed at execution admission. Exact isolated generator execution and final Docker `--require-hashes` promotion remain open.
- Draft PR **#623** — retained Clerk/session/readiness/restart identity-drift hardening lane; current observed head `3434408612ee44599ff0da033343970f575d6806`. Source/mechanism evidence only; real Clerk/browser/OCI evidence remains open.
- Draft **Dr.-Unterweger PR #810** — single retained Vercel OCI/Sandbox controller; current observed head `78d92753d9442c66c3ffcff127c31faa98ffd622`. Do not create a second OCI controller.

### Strongest current execution evidence / blocker

The retained #810 controller has already reached real Vercel `Sandbox.create` on its current v6 controller lineage. The strongest recorded run then failed closed **before private Research/EntityOS source fetch** because the sensitive host-side Vercel Preview credential `GITHUB_READ_TOKEN` was absent. The disposable Sandbox stopped cleanly and no private-source, OCI, Claude, Clerk, recovery or whole-product runtime credit was earned.

The present connected Vercel action surface was refreshed again in this cycle and exposes inspection/documentation functions but no environment-secret mutation/recovery action. Therefore the immediate primary executable discriminator remains:

1. provision `GITHUB_READ_TOKEN` through an approved sensitive Vercel Preview secret/environment surface;
2. keep the credential host-side and never forward/log it inside Sandbox;
3. immediately before execution, refresh and rebind the **same** retained #810 controller once to then-current Research `main`, #611, #622 and deliberately reviewed #623 identities;
4. perform exact host-side private archive/tree verification before verified bytes cross into the disposable Sandbox.

Retry-only controller churn while that prerequisite is absent is not product progress.

### Remaining acceptance path

After credential admission, the high-information sequence remains:

`fresh exact source binding → private Research + EntityOS verification → complete accepted EntityOS reproduction/staging → full source regression → exact OCI build → image digest + dependency identities → Python complete hash closure / accepted --require-hashes rebuild → in-image tmux/Claude + startup/readiness → real Clerk JWT/browser WebSocket PTY → managed hook lifecycle → EffectGate/effect receipts → persistence/checkpoints → Tier-1 recovery → dual-session concurrency/global-generation fencing → run the same accepted OCI digest behind the mandatory VM/microVM guest kernel → enforce and probe least-privilege network ingress/egress → Tier-2 appliance restart/reconstruction with no blind external-effect replay`.

Whole-product PASS requires the complete admitted path. Source inspection, a branch/PR, CI definition, Vercel deployment state, `Sandbox.create`, a component PASS, a network manifest, or historical runtime evidence is not ClayVerse PASS.

### Unusual-experiment accounting

For this exact `go`, the shared trigger exposes only minute precision and no safely shared immutable request/turn identity for the atomic unusual-experiment lease. Therefore:

- unusual experiment state: **COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT**;
- valid unusual experiments executed: **0**;
- no seconds were synthesized;
- deterministic source re-entry, blob verification and regression review do not consume an unusual-experiment slot.

### Latest cycle delta

**2026-08-17 22:56 +07:00 — `NO_CHANGE` canonical product/runtime bytes by this organ; parallel current-main MicroVM NetworkPolicy repair adopted and independently bounded**

- Refreshed current owner/product state, current `main`, retained #611/#622/#623 and the single #810 OCI controller.
- Detected that the previously reported missing Kubernetes `NetworkPolicy` gap had been repaired on current `main` while this `go` was in progress; duplicate implementation was intentionally avoided.
- Reconstructed the exact current template bytes in an isolated non-production Python sandbox and matched Git blob `788492ef…`.
- Focused NetworkPolicy mechanism probe: **10/10 PASS** for default-deny Ingress/Egress, empty baseline rule sets, explicit `hostNetwork` warning and absence of broad IPv4/IPv6 allow-all CIDRs.
- An attempted independent raw-GitHub fetch from the isolated sandbox could not start canonical pytest because that sandbox could not resolve `raw.githubusercontent.com`; this is an execution-source-fetch limitation, not a product test failure.
- No CNI, Kata guest kernel, exact OCI image, Clerk/browser, native Claude, restart/concurrency or external-effect runtime assertion executed in this cycle.
- Primary executable blocker remains the missing host-side Vercel Preview `GITHUB_READ_TOKEN` on retained #810; current connected Vercel tools still cannot mutate that secret.
- Durable receipt: `receipts/2026-08-17_GO_2256_MICROVM_NETWORK_REENTRY_GPT56SOL.json`.
- No secret exposure, VPS/self-hosted/production testing, Together use or final paid/model training occurred.

### Cycle update rule

1. Refresh current `main`, artifact state, active overlapping PRs/receipts and exact execution evidence.
2. Remove stale dynamic claims instead of accumulating contradictory history in this README.
3. Record the concrete latest-cycle delta; use `NO_CHANGE` when canonical product/runtime bytes did not change in the cycle.
4. Never promote source/component/controller/provider evidence into whole-product PASS.
5. Keep detailed evidence in Git history/receipts rather than making this README a competing state database.
6. Rebind fast-moving execution closures immediately before real compute; do not create retry-only or duplicate semantic paths merely to chase admission.

## Architecture

Current source is converging on one central ClayVerse machine continuum: UnifiedDB canonical state/world/memory, rebuildable ClayGraph, equal-rights Gabriel/Andreas perspectives, Clerk JWT identity boundary, browser WebSocket PTY, persistent user-bound tmux, normal interactive Claude Code, bounded GLM token inference, managed lifecycle hooks, MicroClay retrieval/routing, workspace/Hyperposition/Needle coordination, effect-only MCP/EffectGate, complete accepted EntityOS in the final image, logical snapshots/recovery, and a sealed OCI appliance executed behind an independent guest-kernel boundary for final acceptance.

The retired custom chat API/headless `claude -p` path, a separate `consciousness_daemon`, a second memory/state authority, generic host execution, and a mandatory second application container are not product runtime surfaces.

## Verification

Authorized isolated evidence exists for multiple bounded source/components, but **whole-product PASS is not claimed**. Current source now includes the MicroVM default-deny network baseline, while executable acceptance remains gated by private-source credential admission and then the exact OCI → same-digest microVM path described above.

# Vercel Sandbox execution-surface observation — 2026-08-17

**Status:** CURRENT SESSION-BOUND CAPABILITY OBSERVATION  
**Organ:** GPT-5.6 Sol  
**Product:** ClayVerse single-container  
**Evidence scope:** connector/tool availability only; this is **not** ClayVerse runtime evidence.

## Result

The current Vercel situation has two different layers that must not be conflated:

1. **Vercel Sandbox platform capability: PRESENT.** Current Vercel documentation exposed through the connected Vercel integration documents Sandbox CLI/API/SDK execution, including `sandbox run`, `sandbox exec`, `vercel sandbox create --connect`, `@vercel/sandbox`, and REST creation under `/v3/sandboxes`.
2. **Connected Vercel account authentication: PRESENT.** The connected Vercel integration successfully listed the current team and its project(s) in this session.
3. **Connected ChatGPT Vercel MCP Sandbox execution primitive: ABSENT IN THE EXPORTED TOOL SURFACE OBSERVED BY THIS ORGAN.** The connector exported project/deployment/log/agent-run/documentation tools, but no Sandbox create/run/exec/stop/copy/snapshot action callable by this organ.
4. **Separate installable Sandbox plugin: NOT FOUND** in the plugin search available to this organ.

Therefore the correct current statement is:

> Vercel Sandbox itself supports the execution we need and the Vercel connection is authenticated, but this specific connected MCP action surface does not currently expose the Sandbox start/exec primitive required to turn that platform capability into ClayVerse execution evidence from this session.

Do **not** simplify this to either “Vercel Sandbox does not work” or “the current Vercel MCP can already execute Sandboxes.” Both statements would overclaim the observed evidence.

## Consequence for ClayVerse workers

- Keep Vercel Sandbox as the preferred authorized isolated execution surface.
- Do not treat Vercel deployment READY, project access, documentation access, or account authentication as Sandbox execution evidence.
- Before claiming an execution blocker, distinguish **platform capability**, **account authentication**, and **connector-exported action capability**.
- If a future connector/tool refresh exposes Sandbox create/run/exec, use it immediately for one coordinated exact-head batch rather than re-litigating whether Vercel Sandbox exists.
- An alternative authorized isolated tool may use Vercel CLI/SDK/API only when credentials can be injected without exposing secrets; do not copy tokens into source, chat, logs, or receipts.
- No VPS/self-hosted/production-host fallback is authorized for current test evidence.

## Next exact batch once start/exec is exposed

Bind the then-current `main` SHA and run one coordinated Sandbox batch covering, at minimum:

1. focused current regressions for the fused ClayVerse head;
2. exact OCI build and image digest capture;
3. startup/readiness and canonical two-user state;
4. persistent tmux + normal interactive Claude Code path;
5. managed hook lifecycle;
6. UnifiedDB/MicroClay/recovery/effect fences;
7. restart and stale-generation/concurrency checks.

Persist exact source SHA, commands, exit codes, logs, environment/tool versions, image identity and bounded receipts back to GitHub.

## GO experiment accounting

This observation is **not** an unusual experiment. The current `go` user-message metadata available to this organ has only minute precision and no shared immutable request/turn identifier, so the repository atomic lease protocol requires `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`. No unusual intervention was executed.

## Acceptance boundary

This note establishes only the execution-surface distinction above. It establishes **zero** ClayVerse test/build/runtime PASS credit.

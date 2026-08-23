# Claude UserPromptSubmit timeout — ClayVerse acceptance blocker

**Status:** `BLOCKED_UPSTREAM_USERPROMPT_TIMEOUT_FAIL_OPEN`  
**Observed main:** `36e26e0d4233658cba259fcbeb6dc7cb6db7f6a2`  
**Evidence class:** source + current upstream semantics; **not** exact ClayVerse runtime failure evidence.

## Why this blocks whole-product acceptance

ClayVerse currently makes managed `UserPromptSubmit` the canonical pre-model turn boundary:

`normal interactive Claude Code -> UserPromptSubmit -> UnifiedDB admission/context -> Claude`

`policy/managed-settings.json` configures that event as a `command` hook:

- command: `/usr/local/bin/python -m clayverse.terminal_hooks user_prompt`
- timeout: `10` seconds
- pinned Claude Code: `2.1.233`

Anthropic's current hook documentation states that a `UserPromptSubmit` **command, HTTP, or MCP-tool** hook that reaches its timeout is canceled, its output (including `additionalContext`) is discarded, and **the prompt still reaches Claude**. The documentation history also records the timeout notice as of v2.1.196 and distinguishes the fail-closed Agent SDK callback behavior changed by v2.1.208. ClayVerse pins v2.1.233, which is later than both version markers.

Machine marker:

`UPSTREAM_TIMEOUT_SEMANTICS=PROMPT_CONTINUES_ON_TIMEOUT_WITH_HOOK_OUTPUT_DISCARDED`

Therefore the current command-hook architecture cannot be credited as a fail-closed admission gate merely because normal hook errors return exit code 2. A timeout kills/cancels the hook before that exit path can protect the prompt.

## Why the consequence is architectural

`clayverse.terminal_hooks.user_prompt()` opens the canonical `TurnLifecycle.begin_admission()` path, creates the turn/workspace, performs memory/retrieval/context assembly, and returns `additionalContext`. The transaction does not become a substitute for a model gate: if the hook is canceled at the upstream timeout boundary, Claude Code's documented behavior can still process the prompt without the hook output.

That creates a possible product path with:

`user prompt -> Claude processing`

while the required:

`UnifiedDB admission + canonical bounded context`

is absent, incomplete, or rolled back.

This violates the ClayVerse acceptance invariant that every product turn is causally admitted before model cognition. `Stop` or `StopFailure` cannot retroactively turn a missing pre-model admission/context event into a valid causal predecessor.

## Rejected pseudo-fixes

- Increasing `timeout` only moves the fail-open boundary later.
- Returning exit code 2 is useful for ordinary hook failures but cannot execute after the hook has already been canceled by timeout.
- `claude doctor` or the presence of managed settings is configuration evidence, not proof that every prompt crossed a fail-closed admission boundary.
- A post-model `Stop` hook cannot repair a prompt that was processed without its required pre-model canonical admission/context.

## Promotion gate

Whole-product acceptance stays blocked until one exact product-compatible mechanism proves:

1. model processing cannot begin unless UnifiedDB admission succeeds;
2. required bounded canonical context is delivered before that model turn;
3. a deliberately stalled/failed admission cannot produce a model response, tool/effect request, or accepted completion;
4. the normal control path still works;
5. Stop/StopFailure, restart, generation fencing, and recovery remain on the same one-authority lifecycle;
6. no second transcript/state/identity/effect/recovery authority is introduced.

Candidate mechanisms may include a proven pre-PTY admission boundary, a product-compatible fail-closed callback integration, or another inference-admission gate. None is promoted by this document alone.

## Evidence boundary

This finding is stronger than a speculative design concern because it combines current ClayVerse source with documented upstream hook semantics. It is still **not** an exact isolated runtime receipt for the pinned image. Runtime credit remains zero until an authorized exact-source executor deliberately exercises the timeout discriminator and the matching control.

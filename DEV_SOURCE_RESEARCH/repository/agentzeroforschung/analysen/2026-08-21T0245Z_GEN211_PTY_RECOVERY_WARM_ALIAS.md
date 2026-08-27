# Generation 211 — PTY recovery without source delta; warm prompt alias remains blocking

## Bound evidence

Latest observed AgentZero export: `e84584c6111f8a0704c1e8340927cb39337dac7c` (Generation 211), tree `b3fa2c9545dd84c1a4ea17d1ab8c299ee282c440`.

`agentZero/tests/letzter-lauf.json` at `2026-08-20T19:41:40Z` reports source short `b7c25fbe5`, `696 GREEN / 1 RED`. The sole red is:

`tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`

The immediately preceding Generation-211 export `2bf38149f6b588e1072a8a909f2fb2c45d87d941` reported the same source short `b7c25fbe5` but `695 GREEN / 2 RED`, with `tests/test_terminal_ws_auth_lease_protocol.py::test_same_clerk_session_can_refresh_and_continue_pty_input` additionally red.

No AgentZero product-source delta is present between those two exports; the newer export is one export commit ahead and primarily refreshes runtime/export artifacts. Therefore the PTY transition RED -> GREEN receives **zero fix credit**. Together with its prior history this strengthens classification as `REPLICATED_NONDETERMINISM` / environment-observer-timing candidate.

## Stronger current defect: warm-session prompt identity alias

The prior source analysis remains more important than the transient PTY state. Gen211 warm-pool logic has session-scoped logical cache identity but user-scoped physical prompt pathname `/tmp/zero-warm-sys-{user}.md`. The generated system prompt is session-bearing. Reusing the same pathname therefore creates deterministic last-writer-wins cross-session aliasing in steady state and an additional startup TOCTOU window.

A green PTY receipt does not mitigate this defect.

## Required falsifiers

### `WARM_SESSION_PROMPT_IDENTITY_RECEIPT/v2`

For one user with sessions A and B carrying distinct immutable markers:

1. initialize A, then B, then boot A again;
2. repeat order permutations and 100+ overlapping/alternating starts;
3. bind logical `(user, session)` key, physical prompt path, prompt digest, argv digest, file creation/replacement identity, child-open/read timing, and first model-context evidence;
4. require A never observes B and B never observes A.

If violated, preferred repair class is immutable per-session or content-addressed prompt resources with atomic creation/replacement. Do not modify Frank's Harness.

### `PTY_LEASE_TRACE/v1`

Keep PTY separate from deterministic product fixes. Run at least 30 identical exact-source repetitions plus controlled-load arm. Bind Clerk session, lease issue/refresh, WebSocket attach/read/recheck, tmux manager identity, output arrival, scheduler/load, timeout and DB-lock/observer state.

## Acceptance boundary

Current direct same-family evidence: `696 GREEN / 1 RED`.

Promotion remains fail-closed because `TEST_EXPORT_ATOMIC_RECEIPT/v1`, full 40-hex product source commit+tree, dirty-state, and exact Ubuntu executor/environment digest are still not bound. The persistent Claude-Code adapter red remains the deterministic test frontier and must be split into tool-disablement, ephemerality, structured-output and environment/HOME/config isolation sub-receipts.

No Whole Clay Machine PASS is claimed.

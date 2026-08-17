# ClayVerse tmux existing-server policy attestation receipt

Date: 2026-08-17
Organ: GPT-5.6 Sol temporary Clay organ
Trigger: `go` (13:52 +07)
Classification: ordinary product hardening/regression after the single claimed unusual experiment; adds **zero** unusual experiments.

## Problem found

The current browser-terminal hardening passed `-f /etc/clayverse/managed-tmux.conf` on every tmux client invocation, but tmux configuration is applied when the server starts. Therefore an already-running server on the canonical `-L` socket could be reused without proving that the managed policy had actually been loaded into that server.

This is a fail-open stale-server risk at the browser/effect boundary. It is distinct from the already-fixed Gabriel/Andreas socket separation.

## Candidate delta

Branch: `go/tmux-server-policy-attestation-20260817-1352-sol`

Bound exact candidate blobs after fusion with current explicit MCP tool allowlisting:

- `the artefact/clayverse/terminal_sessions.py`: `b37101df4bc959996e5c6dfd3a17c87977ce9a68`
- `the artefact/policy/managed-tmux.conf`: `840d5048bda96b778cd9fb7f148bf7f24b60fa88`

The managed tmux policy now writes `@clayverse_managed_policy=clayverse-browser-transport-v1` as its final command, after disabling both prefixes and unbinding keys. `TerminalSessionManager` verifies the marker plus effective `prefix=None` and `prefix2=None` before reusing an existing canonical session and again after creating a new session. Missing/mismatched/timeout/error state raises `TerminalRuntimeError` and does not admit browser attachment.

## Exact isolated mechanism execution

Environment:

- authorized non-production isolated OpenAI container
- Debian GNU/Linux 13 (trixie)
- no VPS / self-hosted / production host

Before execution, the locally staged Python source was Git-blob hashed and matched the branch exactly:

`b37101df4bc959996e5c6dfd3a17c87977ce9a68`

The policy bytes were independently Git-blob hashed and matched:

`840d5048bda96b778cd9fb7f148bf7f24b60fa88`

Focused exact-source harness result: PASS.

Observed cases:

1. matching managed-policy marker + `prefix=None` + `prefix2=None` -> admitted;
2. existing canonical session with missing policy marker -> fail closed;
3. existing canonical session with effective prefix restored to `C-b` -> fail closed.

The earlier same-trigger alias/cross-user experiment was not repeated as a new unusual experiment; this work adds zero unusual experiments.

## Live tmux/runtime status

Real tmux execution in the OpenAI container remains UNOBSERVED. The container initially lacked tmux. A direct Debian package fetch was attempted only after identifying the exact official Debian package, but the isolated container had no DNS resolution; no package was installed and no live tmux claim is made.

A separate current Vercel staging path for live tmux checks already exists. Vercel preview/Sandbox admission is presently blocked before Sandbox start by the provider build-rate limit. Do not interpret that as a tmux/product test failure.

## Adjudication

- stale-server mechanism: SUPPORTED by upstream tmux configuration lifecycle semantics;
- exact Python fail-closed attestation mechanism: EXECUTED/PASS at exact candidate blob scope;
- live tmux marker/prefix semantics: UNOBSERVED in this receipt;
- OCI/runtime/Claude/PTY path: UNOBSERVED in this receipt;
- whole ClayVerse product: NOT PASS.

Next discriminator: execute the candidate against a real tmux server in the already-authorized isolated Vercel Sandbox path when admission reopens, including (a) a server started with the managed policy and (b) a deliberately pre-existing server started without it. Only then promote live tmux runtime evidence.

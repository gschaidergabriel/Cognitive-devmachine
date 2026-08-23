# CLAUDE_ADAPTER_BOUNDARY_RECEIPT/v2

Status: source/measurement contract. It does not grant whole-product acceptance.

## Why v2 exists

`v1` encoded `temporary HOME created + removed` inside its `EPHEMERAL` boundary. That is not the current targeted Claude Code product contract: `ClaudeCodeInference` intentionally retains `HOME` so subscription/OAuth authentication can work. Treating persistent HOME itself as a failure would either produce a permanent false red or pressure the product to break authentication.

The actual authority invariant is narrower and stronger:

```text
HOME MAY CARRY AUTHENTICATION
HOME MUST NOT BECOME DURABLE COGNITION AUTHORITY
MINIUNIFIEDDB REMAINS THE SOLE DURABLE CANONICAL COGNITION/STATE AUTHORITY
```

Current Claude Code exposes explicit hard-disable controls for auto memory and CLAUDE.md memory loading. The targeted adapter must set those controls itself; ambient host values cannot re-enable them.

`v1` remains historical diagnostic evidence for the Generation-276 decomposition. It MUST NOT mint current targeted-adapter runtime credit after v2 exists.

## Atomic common identity

Every receipt suite binds one canonical `common` object containing:

- exact clean source commit/tree;
- exact Claude binary SHA-256 and version;
- exact adapter command and input digests;
- executor OS/architecture/runtime identity;
- start/finish timestamps.

`common_identity_sha256 = SHA256(canonical_json(common))`.

All four child receipts repeat that exact digest.

## Four v2 boundaries

### `TOOL_LESS_RECEIPT/v2`
PASS requires built-in tools disabled, Bash disabled, no unmanaged MCP server, and zero observed tool invocations.

### `MEMORY_AUTHORITY_RECEIPT/v2`
PASS requires:

- no persistent Claude session reuse;
- prompt-history persistence disabled;
- auto-memory disabled;
- CLAUDE.md memory loading disabled;
- the child process observed `CLAUDE_CODE_SKIP_PROMPT_HISTORY=1`;
- the child process observed `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`;
- the child process observed `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`;
- `home_mode` is either `PERSISTENT_AUTH_ONLY` or `TEMPORARY`;
- zero Claude memory-file loads attributable to HOME/project memory;
- zero Claude memory-file writes attributable to HOME/project memory.

A persistent HOME is therefore admissible only as an authentication container, never as model memory authority.

### `STRUCTURED_OUTPUT_RECEIPT/v2`
PASS requires schema parse success, candidate-only classification, no canonical write attempt by the adapter, and exact result/stdout/stderr digests.

### `ENV_ISOLATION_RECEIPT/v2`
PASS requires an explicit observed child-environment key set, zero forbidden keys, zero secret-value leaks, and an environment-shape digest. Generated security-policy keys are admitted only at their required fixed values; they are not ambient pass-through authority.

## Aggregate law

```text
AGGREGATE_PASS = TOOL_LESS_PASS
              && MEMORY_AUTHORITY_PASS
              && STRUCTURED_OUTPUT_PASS
              && ENV_ISOLATION_PASS
              && SAME_COMMON_IDENTITY
```

A valid aggregate grants only `CLAUDE_ADAPTER_BOUNDARY_ONLY` runtime credit. `whole_product_credit` remains `0`.

UNKNOWN/missing measurement never becomes PASS. Diagnostic FAIL receipts remain evidence but grant zero runtime credit.

## Authority and migration law

- `v2` is the current targeted-adapter promotion contract.
- `v1` remains readable historical diagnostic evidence only.
- no v1 receipt is silently translated into v2;
- persistent HOME alone is neither PASS nor FAIL: the discriminating fact is whether any Claude-side durable memory channel is enabled/loaded/written;
- Claude output, memory state, J-Space state, and GWT state cannot mint canonical MiniUnifiedDB truth.

## Evidence boundary

Source/tests for this contract do not prove a live Claude invocation. Current runtime credit requires an exact admitted run whose emitted v2 receipt is bound to the exact current source, binary, command, inputs and executor.
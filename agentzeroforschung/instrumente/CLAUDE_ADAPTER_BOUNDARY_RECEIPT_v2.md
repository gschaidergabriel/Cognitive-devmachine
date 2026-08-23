# CLAUDE_ADAPTER_BOUNDARY_RECEIPT/v2

Status: measurement contract for new Claude adapter acceptance evidence. V1 remains historical and is not silently reinterpreted.

## Purpose

V1 correctly split the Claude adapter boundary and cross-bound all four child receipts, but its EPHEMERAL contract required a temporary HOME to be created and removed. The canonical adapter intentionally retains HOME for subscription/OAuth authentication, so that field pair cannot honestly describe the product.

V2 measures the property that actually matters: the targeted Claude cognition call must not create or mutate a competing durable cognition/memory surface while retained authentication HOME remains available.

## Current product boundary

For targeted Claude inference:

- HOME MAY remain bound for authentication;
- `--no-session-persistence` MUST be present;
- `CLAUDE_CODE_SKIP_PROMPT_HISTORY=1` MUST be forced;
- `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` MUST be forced;
- `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1` MUST be forced;
- built-in tools remain disabled and unmanaged MCP remains absent;
- MiniUnifiedDB remains the sole durable cognition/state authority;
- real filesystem persistence effects are measured rather than inferred from flags.

Current official Claude Code docs state that `--no-session-persistence` disables print-mode session persistence, that auto memory is on by default unless disabled, and that `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1` prevents loading user/project/auto-memory CLAUDE.md inputs. Historical upstream regression evidence also shows why flag presence alone is not sufficient acceptance evidence.

## Common identity

All four child receipts bind the same exact common object containing at least:

- full Git commit SHA-1;
- Git tree SHA-1;
- `dirty=false`;
- exact Claude binary SHA-256 and version;
- exact adapter command digest;
- exact input digest;
- executor OS / architecture / runtime identity;
- start and finish timestamps.

`common_identity_sha256 = SHA256(canonical_json(common))`.

## Required children

### `TOOL_LESS_RECEIPT/v2`

PASS requires built-in tools disabled, Bash disabled, no unmanaged MCP server, and zero observed tool invocations.

### `EPHEMERAL_RECEIPT/v2`

PASS requires:

- no persistent Claude session reuse;
- `--no-session-persistence` measured in the exact command;
- prompt-history suppression measured in the child environment;
- auto-memory disable measured in the child environment;
- CLAUDE.md memory-input disable measured in the child environment;
- retained auth HOME explicitly acknowledged and represented only by a non-secret identity digest;
- a complete pre/post measurement of the Claude user-side persistence surface;
- identical pre/post persistence digests;
- transcript writes = 0;
- prompt-history writes = 0;
- auto-memory writes = 0.

The measured persistence surface has schema `CLAUDE_USER_PERSISTENCE_SURFACE/v1` and kinds exactly:

`["auto_memory", "prompt_history", "transcripts"]`.

Authentication credential refreshes are outside this cognition-memory surface and must not be misclassified as memory writes. Unknown or incomplete path coverage is not PASS.

### `STRUCTURED_OUTPUT_RECEIPT/v2`

PASS requires parse success into the admitted result schema, candidate-only classification, no canonical write attempt by the adapter, and exact result/stdout/stderr digests.

### `ENV_ISOLATION_RECEIPT/v2`

PASS requires an explicit environment allowlist, observed child keys contained by that allowlist, zero forbidden keys, zero secret-value leaks, and a digest of the observed environment shape. Adapter-injected safety controls are admitted child keys.

## Aggregate law

```text
AGGREGATE_PASS = TOOL_LESS_PASS
              && EPHEMERAL_PASS
              && STRUCTURED_OUTPUT_PASS
              && ENV_ISOLATION_PASS
              && SAME_COMMON_IDENTITY
              && RETAINED_AUTH_HOME
              && AUTO_MEMORY_DISABLED
              && CLAUDE_MDS_DISABLED
              && PERSISTENCE_SURFACE_UNCHANGED
```

A valid aggregate grants only `CLAUDE_ADAPTER_BOUNDARY_ONLY`. `whole_product_credit` remains `0`.

## Exact Ubuntu gate

1. freeze exact clean source commit/tree;
2. bind exact Claude executable/version, command and input;
3. identify and digest the admitted transcript/prompt-history/auto-memory persistence surface before execution;
4. execute one targeted Claude inference call with retained auth HOME;
5. measure the same surface after execution and count writes by class;
6. emit all four v2 children from that same common identity;
7. validate with `validate_claude_adapter_boundary_receipt_v2.py`;
8. preserve any observed write as an EPHEMERAL failure;
9. rerun the full product suite before changing whole-product acceptance.

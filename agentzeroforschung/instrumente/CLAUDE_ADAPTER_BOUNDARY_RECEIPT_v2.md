# CLAUDE_ADAPTER_BOUNDARY_RECEIPT/v2

Status: source/measurement contract. It supersedes v1 for new Claude adapter acceptance evidence. It does not grant whole-product acceptance.

## Why v2 exists

`CLAUDE_ADAPTER_BOUNDARY_RECEIPT/v1` correctly introduced four independently measurable Claude adapter boundaries and one common exact-run identity, but its EPHEMERAL receipt required a temporary HOME to be created and removed.

That requirement conflicts with the current canonical `ClaudeCodeInference` contract: HOME is intentionally retained so Claude subscription/OAuth credentials remain usable. Ephemerality is a **persistence property**, not a requirement to destroy the authentication HOME.

Current Claude Code upstream documentation also makes two additional facts material to the boundary:

1. auto memory is enabled by default unless `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` is set;
2. `--no-session-persistence` and `CLAUDE_CODE_SKIP_PROMPT_HISTORY` are intended to suppress transcript persistence, but upstream has had version-specific regressions where a nominal no-persistence flag still wrote session files.

Therefore v2 measures the actual durable side-memory surface while allowing the retained auth HOME.

## Authority law

Claude Code is targeted candidate inference only.

It may use authentication material needed to reach the admitted Claude service, but it may not silently gain a second durable memory or context authority beside MiniUnifiedDB / the canonical world assembly path.

For the targeted inference call:

- HOME MAY be retained for authentication;
- user/project/local setting sources MUST be excluded (`--setting-sources ""`);
- built-in tools MUST remain disabled;
- unmanaged MCP MUST remain absent;
- `--no-session-persistence` MUST be requested;
- `CLAUDE_CODE_SKIP_PROMPT_HISTORY=1` MUST be forced by the adapter;
- `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` MUST be forced by the adapter;
- a caller-supplied attempt to set either suppression control to `0` MUST NOT weaken the adapter;
- actual transcript/history/auto-memory writes across the measured persistence surface MUST be zero.

Managed machine policy remains an administrative enforcement layer and is not reclassified as user/project/local memory.

## Atomic common identity

Every v2 receipt suite binds the same canonical common object containing at least:

- full Git commit SHA-1;
- Git tree SHA-1;
- `dirty=false`;
- exact Claude binary SHA-256 and version;
- exact adapter command digest;
- exact input digest;
- executor OS / architecture / runtime identity;
- start and finish timestamps.

`common_identity_sha256 = SHA256(canonical_json(common))`.

All four child receipts MUST repeat the exact common digest.

## Four required receipts

### `TOOL_LESS_RECEIPT/v2`

PASS requires measured evidence that built-in tools and Bash were disabled, no unmanaged MCP server was attached, and no tool invocation occurred.

### `EPHEMERAL_RECEIPT/v2`

PASS requires all of the following:

- no persistent Claude session was reused;
- `--no-session-persistence` was present in the measured command;
- `CLAUDE_CODE_SKIP_PROMPT_HISTORY=1` was present in the measured child environment;
- `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` was present in the measured child environment;
- effective user/project/local `setting_sources` is the empty set;
- auth HOME was intentionally retained and its identity is represented only by a SHA-256 digest, never a secret/path value in the durable receipt;
- the measured Claude user-persistence surface had identical pre/post digests;
- transcript writes = 0;
- prompt-history writes = 0;
- auto-memory writes = 0.

The persistence surface is scoped to Claude's user-side durable cognition artifacts, not authentication credential stores. At minimum it covers the effective transcript/auto-memory project tree and prompt history for the invocation. Credential refreshes must not be mistaken for cognition-memory writes.

### `STRUCTURED_OUTPUT_RECEIPT/v2`

PASS requires parse success into an explicit result schema, candidate-only classification, no canonical write attempt by the adapter, and exact result/stdout/stderr digests.

### `ENV_ISOLATION_RECEIPT/v2`

PASS requires an explicit environment allowlist, observed child keys contained by that allowlist, zero forbidden keys, zero secret-value leaks, and a digest of the observed environment shape. Forced safety controls such as `CLAUDE_CODE_DISABLE_AUTO_MEMORY`, `CLAUDE_CODE_SKIP_PROMPT_HISTORY`, and `DISABLE_AUTOUPDATER` are admitted child keys because the adapter itself injects them.

## Aggregate law

```text
AGGREGATE_PASS = TOOL_LESS_PASS
              && EPHEMERAL_PASS
              && STRUCTURED_OUTPUT_PASS
              && ENV_ISOLATION_PASS
              && SAME_COMMON_IDENTITY
              && RETAINED_AUTH_HOME
              && SETTING_SOURCES_EMPTY
              && AUTO_MEMORY_DISABLED
              && PERSISTENCE_SURFACE_UNCHANGED
```

A valid aggregate grants only `CLAUDE_ADAPTER_BOUNDARY_ONLY` runtime credit. `whole_product_credit` remains `0`.

UNKNOWN or missing measurement is never coerced to PASS.

## Next exact Ubuntu execution

1. freeze full commit + tree and assert clean checkout;
2. hash the exact Claude executable and record version;
3. record the exact command/input identity;
4. resolve and digest the scoped Claude transcript/history/auto-memory persistence surface before the call;
5. run exactly one admitted targeted inference call with retained auth HOME;
6. resolve the same persistence surface after the call and record write counts;
7. derive all four v2 child receipts from that one common identity;
8. validate with `validate_claude_adapter_boundary_receipt_v2.py`;
9. only then grant Claude-adapter-boundary runtime credit;
10. rerun the complete product suite before changing whole-product acceptance.

## Upstream evidence used for this versioning decision

- Claude Code documentation: auto memory is on by default; `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` disables it; auto memory is stored under the per-project Claude memory directory.
- Claude Code documentation: `--no-session-persistence` suppresses persistence for one `-p` run and `CLAUDE_CODE_SKIP_PROMPT_HISTORY` suppresses transcript writes.
- anthropics/claude-code issue #49565 documented a version-specific regression where `--no-session-persistence` still created a session JSONL artifact. This is evidence that the boundary must measure filesystem persistence rather than trust a flag string alone.

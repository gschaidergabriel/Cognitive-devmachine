# Claude Code Adapter Boundary Receipts v1

Status: source/mechanism contract for the persistent Generation-276 adapter red.

## Purpose

The historical monolithic runtime assertion

`test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`

has replicated red on the same shortened source family. A single boolean red cannot distinguish four materially different failure classes. This contract decomposes the next exact Ubuntu observation into four independently materialized receipts that MUST share one immutable run binding:

- `TOOLLESS_RECEIPT/v1`
- `EPHEMERAL_RECEIPT/v1`
- `STRUCTURED_OUTPUT_RECEIPT/v1`
- `ENV_ISOLATION_RECEIPT/v1`

The four receipts are evidence views of one exact adapter run boundary. They are not four authorities and do not create a second inference path.

## Shared binding

Every receipt MUST bind the same:

- full source commit SHA and tree SHA;
- dirty state and dirty-diff digest when dirty;
- test run id and suite digest;
- Ubuntu executor identity and kernel;
- exact Claude binary digest and version;
- exact adapter version and source digest;
- HOME identity;
- canonical environment allowlist and normalized environment digest;
- exact MCP/tool configuration digest.

The validator rejects any cross-receipt drift. A receipt with a self-consistent but different source/environment does not combine into one PASS.

## Boundary invariants

### TOOLLESS

PASS requires no admitted tools, no admitted MCP servers and zero observed tool calls.

### EPHEMERAL

PASS requires a temporary empty HOME, zero pre-existing state, zero post-run persistent artifacts and no session reuse.

### STRUCTURED_OUTPUT

PASS requires exact parser-contract identity, captured stdout/stderr/result digests, and explicit rejection of malformed and unstructured probes.

### ENV_ISOLATION

PASS requires child environment keys to remain inside the bound allowlist, no observed ambient secret keys, at least one ambient-state probe, zero inherited ambient keys outside the admitted projection, and HOME under the ephemeral root.

## Evidence law

A green four-receipt bundle establishes only the named adapter boundary evidence for that exact run binding.

It does NOT establish:

- Claude model quality;
- J-Space or GWT runtime credit;
- canonical truth/effect authority;
- whole Mini Entity acceptance;
- historical Generation-276 repair credit unless executed against the exact relevant runtime source.

`BOUNDARY_RECEIPT_PASS != WHOLE_PRODUCT_PASS`

## Next executable gate

On the next intentional exact Ubuntu start, emit all four receipts from the same adapter invocation boundary and validate them with `validate_claude_adapter_boundary_receipts_v1.py`. If one receipt fails, retain the other three observations and localize the repair to the failing invariant rather than broad-patching the adapter.

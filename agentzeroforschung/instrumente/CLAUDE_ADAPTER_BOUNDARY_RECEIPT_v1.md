# CLAUDE_ADAPTER_BOUNDARY_RECEIPT/v1

Status: source/measurement contract. It does not grant whole-product acceptance.

## Purpose

Generation 276 repeatedly produced exactly one red test at the Claude Code adapter boundary. The old monolithic assertion combines four independent properties and therefore has low diagnostic resolution. This contract turns that red into four independently measurable receipts while cross-binding all four to one exact run identity.

```clay
R0 OBSERVE {
  repeated_red = "tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated";
  repeats_same_short_source = 3;
  exact_full_source_environment_identity = UNKNOWN;
}
R1 INFER { monolithic_red -> boundary_fault_localized_but_dimension_unknown; }
R2 GENERATE { split = [TOOL_LESS, EPHEMERAL, STRUCTURED_OUTPUT, ENV_ISOLATION]; }
R3 COUNTER { independent_receipts_without_cross_binding -> false_green_by_mixed_runs; }
R4 DISCRIMINATE { require_same_common_identity_sha256_for_all_four; }
R5 EMERGENT { diagnostic_resolution_up; authority_scope_unchanged; }
R6 VERIFY { only_actual_exact_run_measurements_may_set_each_boundary_PASS; }
```

## Atomic common identity

Every receipt suite binds the same canonical common object containing at least:

- full Git commit SHA-1;
- Git tree SHA-1;
- `dirty=false`;
- exact Claude binary SHA-256 and version;
- exact adapter command digest;
- exact input digest;
- executor OS / architecture / runtime identity;
- start and finish timestamps.

`common_identity_sha256 = SHA256(canonical_json(common))`.

All four child receipts MUST repeat that exact digest. This prevents combining a tool-less PASS from one run with environment-isolation PASS from another.

## Four required receipts

### `TOOL_LESS_RECEIPT/v1`
PASS requires measured evidence that built-in tools and Bash were disabled, no unmanaged MCP server was attached, and no tool invocation occurred.

### `EPHEMERAL_RECEIPT/v1`
PASS requires no persistent Claude session reuse, no prompt-history write, no auto-memory write, a temporary HOME created for the invocation, and cleanup of that HOME after completion.

### `STRUCTURED_OUTPUT_RECEIPT/v1`
PASS requires parse success into an explicit result schema, candidate-only classification, no canonical write attempt by the adapter, and exact result/stdout/stderr digests.

### `ENV_ISOLATION_RECEIPT/v1`
PASS requires an explicit environment allowlist, observed child keys contained by that allowlist, zero forbidden keys, zero secret-value leaks, and a digest of the observed environment shape. Secret values never enter the receipt.

## Aggregate law

```text
AGGREGATE_PASS = TOOL_LESS_PASS
              && EPHEMERAL_PASS
              && STRUCTURED_OUTPUT_PASS
              && ENV_ISOLATION_PASS
              && SAME_COMMON_IDENTITY
```

A valid aggregate grants only `CLAUDE_ADAPTER_BOUNDARY_ONLY` runtime credit. `whole_product_credit` MUST remain `0`.

UNKNOWN or missing measurement is never coerced to PASS. A failed child receipt localizes the dimension but does not license patching another dimension.

## Execution sequence

On the next intentional exact Ubuntu run:

1. freeze full commit + tree and assert clean checkout;
2. hash the exact Claude executable and record version;
3. compile one fixed test InferencePacket and command;
4. run the adapter once under the admitted isolated environment;
5. derive all four child receipts from that same invocation or from four explicitly identical-replay invocations whose exact common identity differs only by a separately declared replay nonce (if replay mode is later versioned);
6. validate with `validate_claude_adapter_boundary_receipt_v1.py`;
7. only then decide whether the red is tool policy, persistence, structured parsing, or environment leakage.

The current v1 validator intentionally admits only one common identity and has no replay-merging mode.

# CLAUDE_ADAPTER_BOUNDARY_RECEIPT/v1

Status: source/measurement contract. It does not grant whole-product acceptance.

## Purpose

Generation 276 repeatedly produced exactly one red test at the Claude Code adapter boundary. The old monolithic assertion combines four independent properties and therefore has low diagnostic resolution. This contract turns that red into four independently measurable receipts while cross-binding all four to one exact process invocation.

```clay
R0 OBSERVE {
  repeated_red = "tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated";
  repeats_same_short_source = 3;
  exact_full_source_environment_identity = UNKNOWN;
}
R1 INFER { monolithic_red -> boundary_fault_localized_but_dimension_unknown; }
R2 GENERATE { split = [TOOL_LESS, EPHEMERAL, STRUCTURED_OUTPUT, ENV_ISOLATION]; }
R3 COUNTER { copied_common_metadata_or_equal_output_without_invocation_identity -> false_same_run_claim; }
R4 DISCRIMINATE { require_same_common_identity_sha256_for_all_four; require_invocation_id; require_same_process_output_digests; }
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
- one opaque invocation-scoped `invocation_id` minted for this process call;
- executor OS / architecture / runtime identity;
- start and finish timestamps.

`common_identity_sha256 = SHA256(canonical_json(common))`.

All four child receipts MUST repeat that exact digest and MUST carry identical non-placeholder `stdout_sha256` and `stderr_sha256` values. The explicit `invocation_id` prevents copied source/command/executor metadata plus coincidentally identical output bytes from being misrepresented as proof that four observations came from one process invocation. `invocation_id` is provenance only: it grants no runtime or product credit by itself.

## Four required receipts

### `TOOL_LESS_RECEIPT/v1`
PASS requires measured evidence that built-in tools and Bash were disabled, no unmanaged MCP server was attached, and no tool invocation occurred.

### `EPHEMERAL_RECEIPT/v1`
PASS requires no persistent Claude session reuse, no prompt-history write, no auto-memory write, a temporary HOME created for the invocation, and cleanup of that HOME after completion.

### `STRUCTURED_OUTPUT_RECEIPT/v1`
PASS requires parse success into an explicit result schema, candidate-only classification, no canonical write attempt by the adapter, and exact result/stdout/stderr digests.

### `ENV_ISOLATION_RECEIPT/v1`
PASS requires an explicit environment allowlist, observed child keys contained by that allowlist, zero forbidden keys, zero secret-value leaks, and a digest of the observed environment shape. Secret values never enter the receipt.

The receipt-declared allowlist is measurement data, not policy authority. It MAY be a subset of the canonical Claude child-process environment policy, but MUST NOT contain any key outside that policy. A receipt therefore cannot turn an ambient or forbidden key into an allowed key merely by listing it in both `allowed_env_keys` and `observed_child_env_keys`. Widening the child environment requires an explicit versioned source/contract policy change; it cannot be authorized by the receipt being validated.

```text
RECEIPT_DECLARED_ALLOWLIST <= CANONICAL_CHILD_ENV_POLICY
RECEIPT_SELF_AUTHORIZATION = FORBIDDEN
OBSERVED_KEY_OUTSIDE_CANONICAL_POLICY = FAIL_CLOSED
```

## Aggregate law

```text
AGGREGATE_PASS = TOOL_LESS_PASS
              && EPHEMERAL_PASS
              && STRUCTURED_OUTPUT_PASS
              && ENV_ISOLATION_PASS
              && SAME_COMMON_IDENTITY
              && EXPLICIT_INVOCATION_ID
              && SAME_STDOUT_DIGEST
              && SAME_STDERR_DIGEST
```

A valid aggregate grants only `CLAUDE_ADAPTER_BOUNDARY_ONLY` runtime credit. `whole_product_credit` MUST remain `0`.

UNKNOWN or missing measurement is never coerced to PASS. A failed child receipt localizes the dimension but does not license patching another dimension.

## Negative-evidence preservation

Promotion validation and diagnostic validation are deliberately separate views over the SAME receipt schema.

- default `validate(...)` and CLI mode remain fail-closed promotion gates: any measured boundary failure makes the receipt non-promotable;
- `diagnose(...)` / CLI `--diagnostic` accepts a fully measured aggregate with child `status=FAIL` only when the reported status exactly matches the typed observed boundary fields;
- a diagnostic aggregate with any failed boundary MUST use `aggregate_status=FAIL`, `runtime_credit=ZERO`, `whole_product_credit=0`, and `promotion_eligible=false`;
- the diagnostic result retains every failing boundary plus explicit violation codes, while preserving the three unaffected PASS observations from the same common identity;
- reporting PASS while observed fields imply a failure is rejected;
- missing/unmeasured data, cross-run identity drift, cross-bound process-output drift, dirty source, malformed types or invalid digests remain invalid even in diagnostic mode.

Therefore:

```text
MEASURED_FAIL != INVALID_RECEIPT
DIAGNOSTIC_VALID != PROMOTION_PASS
NEGATIVE_EVIDENCE_PRESERVED -> RUNTIME_CREDIT_ZERO
```

This prevents the next exact Ubuntu run from discarding useful evidence merely because one of the four boundaries remains red.

## Execution sequence

On the next intentional exact Ubuntu run:

1. freeze full commit + tree and assert clean checkout;
2. hash the exact Claude executable and record version;
3. compile one fixed test InferencePacket and command;
4. mint one invocation-scoped opaque `invocation_id` before process start;
5. run the adapter once under the admitted isolated environment;
6. derive all four child receipts from that same invocation and repeat the same stdout/stderr digests across all four;
7. run diagnostic validation first so PASS and FAIL observations are durably classified without promotion;
8. run strict validation only if the diagnostic aggregate is PASS;
9. only then decide whether the red is tool policy, persistence, structured parsing, or environment leakage.

The current v1 validator intentionally admits only one invocation identity and has no replay-merging mode. If repeated-invocation evidence is needed later, version that aggregation explicitly rather than weakening the atomic-run contract.

# Generation 262 — Receipt recovery does not erase FREE_ONLY history

## Bound evidence

Latest inspected same-family AgentZero export: `9891542c7d9793375255358baa5ac13a13fafde9` (Generation 262).

Its exported `agentZero/tests/letzter-lauf.json` is now fresh relative to the snapshot and reports:

- source short: `81f70e3ef`
- generated: `2026-08-21T23:37:53Z`
- green: `1442`
- red: `1`
- sole red: `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`

The same export's generated `ZIELE.md` independently renders `1442 gruen / 1 rot`. This closes the *surface* stale-receipt discrepancy observed earlier in Generation 262 (`1383/1` direct versus `1441/2` dashboard).

## Credit boundary

This is not yet an atomic acceptance receipt. `TEST_EXPORT_ATOMIC_RECEIPT/v1` remains required because the direct test result and dashboard are still separate exported consumers without one immutable run id binding full source commit+tree, dirty state, suite digest, executor/environment identity and result digest.

Therefore:

- current same-family test surface: `1442 GREEN / 1 RED`
- stale-receipt surface contradiction: currently not observed
- atomic acceptance credit: `0`
- sole persistent red remains the Claude-Code runtime-adapter isolation invariant

## Historical FREE_ONLY truth is still contradictory in the dashboard

The current Generation-262 `ZIELE.md` still contains both of these claims:

1. GLM Coding Plan is structurally present and "NICHT live geprueft" / key valid later.
2. The architect-pipeline row records `3x glm / 3x sonnet` and explicitly says one tick called GLM live and another fell back to Sonnet.

Earlier executable evidence already bound those paid/subscription executions. A later disabled timer, inactive key or dashboard wording cannot rewrite executed history.

Hence the highest control blocker remains unchanged:

`FREE_ONLY_PROVIDER_ADMISSION_RECEIPT/v2`

At the final dispatch boundary every provider/model route and every fallback hop must have a machine-readable `cost_class in {FREE, PAID, SUBSCRIPTION, UNKNOWN}`. In FREE_ONLY mode only `FREE` may proceed. `PAID`, `SUBSCRIPTION` and `UNKNOWN` must terminate before secret/key lookup and before network I/O.

Required negative controls:

- direct GLM Coding Plan route -> reject; key lookups `0`; network attempts `0`
- GLM -> Sonnet fallback -> both non-free hops rejected; key lookups `0`; network attempts `0`
- UNKNOWN route -> reject; key lookups `0`; network attempts `0`
- known FREE route -> may be admitted

Also retain `PROVIDER_EXECUTION_HISTORY_RECEIPT/v1` as append-only historical truth, separating `HISTORICAL_EXECUTED_PAID_BREACH` from current quarantine/admission state.

## Next highest-information work

1. Implement/execute `FREE_ONLY_PROVIDER_ADMISSION_RECEIPT/v2` before any further architect/provider network research.
2. Bind `TEST_EXPORT_ATOMIC_RECEIPT/v1` so 1442/1 has exact run/source/executor identity rather than coincident consumer agreement.
3. Decompose the persistent adapter red into `TOOLLESS`, `EPHEMERAL`, `STRUCTURED_OUTPUT`, and `ENV_ISOLATION` receipts on an exact Ubuntu checkout.
4. Preserve all previously open safety/provenance falsifiers; no paid-provider result receives research, BASE, capability or canonical credit.

## Classification

- Gen262 receipt freshness: **RECOVERED AT EXPORT SURFACE**
- Test consumer count agreement: **1442/1 == 1442/1**
- Atomic test truth: **NOT YET PROVEN**
- FREE_ONLY historical contradiction: **STILL PRESENT**
- Provider/architect network execution: **QUARANTINED**
- BASE / Whole Clay Machine: **NOT PASS**

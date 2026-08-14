<!-- RAE_META
{"packet_id":"KMP-HYPOTHESIS-TEST-ADEQUACY-20260809","title":"Hypothesis-Test Adequacy Chain","domains":["harness"],"topics":["hypothesis testing","test adequacy","counterhypothesis","experiment parameters","evidence pipeline"],"claim_status_hint":"OPEN","source_refs":["research_entity/archive_assimilation/receipts/666_20260809T0411p0700_chatgpt_secondary_pf_experiment_adequacy_batch003.json"],"search_terms":["test execution","test adequacy","counterhypothesis","fallback parameters","INCONCLUSIVE","oracle version"]}
RAE_META -->

# KMP — Hypothesis-Test Adequacy Chain

**Packet ID:** `KMP-HYPOTHESIS-TEST-ADEQUACY-20260809`  
**Status:** OPEN / architecture-method constraint candidate  
**Origin:** `666` Project-Frankenstein archaeology  
**Primary source receipt:** `research_entity/archive_assimilation/receipts/666_20260809T0411p0700_chatgpt_secondary_pf_experiment_adequacy_batch003.json`

## Atomic claim

A test being syntactically valid and successfully executed is insufficient evidence for a hypothesis unless the executed intervention/parameters are demonstrably adequate to discriminate that hypothesis from a specified counterhypothesis or alternative mechanism.

Compact law:

`test execution != test adequacy != evidential support`

More general:

`representation validity != intent/test adequacy != execution success != evidential support`

## Historical mechanism

Project-Frankenstein's Hypothesis Engine already implemented:

`observe -> hypothesize -> predict -> test -> revise`

and its Experiment Lab could run deterministic simulations.

However, `LabConnector.run_experiment()` used three translation tiers. If description detection and station parsing failed, it could execute randomized default parameters for the station. That means a real deterministic experiment could complete even when the executed parameterization was not entailed by the original prediction.

The result path could then interpret natural-language narration markers into `confirmed/refuted/inconclusive`.

## Current invariant candidate

For experiments used to change claim state, preserve a typed chain:

`hypothesis_id`
`-> counterhypothesis_id`
`-> prediction_id`
`-> intervention/test_contract_hash`
`-> exact_parameters_hash`
`-> execution_receipt`
`-> raw_outcome_hash`
`-> oracle_version`
`-> verdict`
`-> claim_transition`

Required safeguards:

- fallback/default parameters yield `INCONCLUSIVE` unless the frozen test contract explicitly declares them discriminating;
- raw outcome is immutable/provenance-bound before narration;
- narration cannot directly determine scientific truth state;
- parser failure, execution failure, test inadequacy and falsification remain distinct;
- the intended alternative/countermechanism must be named when practical;
- oracle identity/version must be recorded.

## Cross-domain connection

ClayCode research independently found an analogous separation around intent adequacy and execution authority. Shared logical structure does not make the two historical sources independent empirical replication, but it suggests a reusable architecture pattern:

**Before acting on a representation, prove that the representation adequately captures the intended discriminating/action contract.**

## Falsifier / next test

Construct mutation tests where the frozen prediction remains fixed while:

1. parameters are replaced by generic station defaults;
2. one causally necessary intervention parameter is omitted;
3. raw result is unchanged but narration marker is flipped;
4. counterhypothesis is swapped;
5. parser fails and fallback is invoked.

A correct current Harness/evidence pipeline must reject or mark these `INCONCLUSIVE`, never silently convert them into support/refutation.

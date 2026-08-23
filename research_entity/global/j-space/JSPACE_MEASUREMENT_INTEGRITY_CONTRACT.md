# J-SPACE MEASUREMENT INTEGRITY CONTRACT

Status: RESEARCH CANDIDATE / SOURCE CONTRACT
Parent: `research_entity/global/MINI_ENTITY_JSPACE_GWT_INSTRUMENTED_COGNITION.md`
Scope: Mini Entity J-Lens / J-space observer telemetry only

```claycode
contract JSpaceMeasurementIntegrity {
  law epistemic {
    JSPACE_UNKNOWN != JSPACE_ERROR != JSPACE_MEASURED;
    MODEL_SELF_REPORT != JSPACE_MEASURED;
    JSPACE_MEASURED != CANONICAL_ENTITY_TRUTH;
    JSPACE_MEASURED != EFFECT_AUTHORITY;
  }

  state ObserverMeasurement {
    model_digest;
    tokenizer_digest;
    lens_digest;
    lens_source_revision;
    fit_corpus_digest;
    fit_sample_count;
    serialization_dtype;
    runtime_dtype;
    layer;
    token_position;
    transported_vector;
    decoded_scores;
    decoded_ranks;
  }

  gate admit_jspace_measurement(obs: ObserverMeasurement) -> MeasurementState {
    require provenance_complete(obs);
    require finite(obs.transported_vector);
    require finite(obs.decoded_scores);
    require ranks_well_formed(obs.decoded_ranks);
    require serialization_roundtrip_integrity(obs.lens_digest, obs.serialization_dtype);
    return MEASURED_INTERPRETABILITY;
  }

  on_fail admit_jspace_measurement -> ERROR_CORRUPTED_OBSERVER;

  invariant {
    ERROR_CORRUPTED_OBSERVER cannot collapse Hyperposition;
    ERROR_CORRUPTED_OBSERVER cannot enter MiniUnifiedDB canonical facts;
    ERROR_CORRUPTED_OBSERVER cannot raise omega authority;
    ERROR_CORRUPTED_OBSERVER may persist only as provenance-bound research telemetry;
  }
}

GRF {
  R0 OBSERVE {
    upstream_reference = "anthropics/jacobian-lens";
    upstream_semantics = "average input-output Jacobian transports residuals into final-layer basis for readout";
    upstream_open_issue = "JacobianLens.save() can overflow large finite Jacobians to inf when serialized through a narrower default dtype";
    current_mini_entity_concept = "lens outputs are MEASURED_INTERPRETABILITY and never canonical truth";
  }

  R1 INFER {
    integrity_gap = "typed MEASURED_INTERPRETABILITY is insufficient unless nonfinite/corrupted observer outputs fail closed before measurement admission";
  }

  R2 GENERATE {
    candidate A = "accept decoded readout whenever lens execution returns";
    candidate B = "finite/provenance/roundtrip gate before MEASURED_INTERPRETABILITY";
  }

  R3 COUNTER {
    counter_to_A = "finite fitted state may serialize/reload as inf; a returned token/rank can therefore be observer corruption rather than a measurement";
    counter_to_B = "strict integrity gate may reject recoverable observer data, but preserves epistemic separation and can retain ERROR telemetry";
  }

  R4 DISCRIMINATE {
    exact_gate = "on exact Qwen3.5-0.8B checkpoint and fitted lens: fit -> save -> reload -> finite scan -> readout equivalence; compare default serialization versus explicit safe dtype";
    promotion_requires = "authorized isolated runner + exact model/lens/source identities";
  }

  R5 EMERGENT {
    rule = "interpretability instruments require their own measurement-admission boundary; observer failure must not silently become epistemic evidence";
  }

  R6 VERIFY {
    source_contract = SUPPORTED;
    qwen_runtime = UNOBSERVED;
    whole_product = IN_PROGRESS;
  }
}
```

## External evidence boundary

Primary upstream sources observed 2026-08-23:
- Anthropic Jacobian Lens repository: `https://github.com/anthropics/jacobian-lens`
- Anthropic research page: `https://www.anthropic.com/research/global-workspace`
- Upstream issue: `https://github.com/anthropics/jacobian-lens/issues/6`

The upstream issue is external reported evidence about the reference implementation, not Mini Entity runtime evidence. This contract does not claim the selected Qwen checkpoint reproduces that failure. It converts the reported failure mode into a fail-closed admission requirement and a future exact-runtime falsifier.

## Promotion boundary

Do not classify a J-space result as `MEASURED_INTERPRETABILITY` solely because the lens returned logits/tokens. Exact provenance, finite numeric state and serialization/readout integrity must pass first. Any failure remains typed `JSPACE_ERROR`/`ERROR_CORRUPTED_OBSERVER` and cannot mint truth, collapse Hyperposition or authorize omega/effects.

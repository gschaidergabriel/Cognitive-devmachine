# FREE-LLM feed contract for HCU

The HCU may consume the existing Mini Entity **FREE_ONLY** inference pool to feed its world-model,
simulation and critique loops.

## Admitted role

Hosted/free model output is always one of:

- `CANDIDATE_OBSERVATION`;
- `CANDIDATE_HYPOTHESIS`;
- `CANDIDATE_PLAN`;
- `CANDIDATE_CRITIQUE`;
- `SYNTHETIC_TEST_MATERIAL`.

It is never canonical fact merely because a provider/model produced it.

## Provider policy

Use only provider/model profiles currently admitted by the Mini Entity control plane and marked
free at execution time. Current owner/control examples include Groq, Mistral and NVIDIA/Nemotron
free-only orchestration when credentials and quotas permit.

Hard controls:

- no paid fallback;
- HTTP 402 = hard stop;
- HTTP 429 = provider-wide backoff, not key rotation/quota evasion;
- Together remains forbidden under current control;
- secrets are environment/vault references only;
- no secret enters prompt, receipt, telemetry, MiniUnifiedDB export or ZIP.

## Feed receipt

Every accepted feed item should bind:

```text
HCU_FREE_FEED_RECEIPT/v1 {
    feed_id
    provider_profile_id
    model_id
    request_identity
    cycle_id
    causal_id
    entity_generation
    purpose
    prompt_digest
    response_digest
    free_only_observed
    usage_if_available
    source_provenance
    candidate_class
    validation_state
}
```

Provider output enters Hyperposition as an alternative candidate. Independent validation or direct
observed evidence is required before factual promotion through the canonical MiniUnifiedDB path.

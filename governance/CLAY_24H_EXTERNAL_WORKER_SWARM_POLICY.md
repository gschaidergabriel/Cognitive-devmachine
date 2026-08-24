# CLAY 24H EXTERNAL WORKER SWARM POLICY

Status: **ACTIVE USER DIRECTIVE, SUBORDINATE TO NEWEST SUPERVISOR**  
Scope: sandbox-resident external research workers for EntityOS + HCU.

A `go` research swarm may use NVIDIA, Mistral and Groq only when the active EntityOS/HCU control plane has emitted a typed `ENTITYOS_HCU_PROVIDER_ADMISSION/v1` object whose effective provider `cost_class` is exactly `FREE`. Environment flags, key presence, model-catalog success, previous HTTP success, absence of an invoice, or HTTP 402 do not establish FREE status.

## Admission boundary — supervisor 8.67

The provider decision order is mandatory:

`typed control-plane admission -> effective cost_class -> provider-specific secret/key lookup -> catalog/network -> chat request`

`PAID`, `SUBSCRIPTION`, `UNKNOWN`, missing, malformed, expired or unproven admission fails closed before any provider secret/key lookup and before network I/O. Legacy mixed secret bundles must not be blindly sourced. Provider-specific secret files may be read only after that provider is admitted FREE, and are parsed as data rather than executed as shell code. Together and paid fallback remain forbidden.

## Model selection

After admission, live `/v1/models` discovery may select models by research utility. Explicit parameter count is only one signal. Prefer capable chat/reasoning/coding/flagship models and exclude embeddings, rerankers, audio/speech, moderation/guard and non-general research endpoints.

## Parallelism and rate limits

Drive parallelism adaptively toward sustainable provider throughput. Honor `Retry-After` and provider-wide 429 cooldown. Credentials must not be rotated to evade project/provider rate limits. HTTP 402 is a hard stop for the affected credential and cannot retroactively prove a provider was FREE.

## Research authority

Workers are temporary organs of Clay. Their outputs are candidate research evidence only. They cannot self-grant capabilities, mint canonical state/runtime credit, override EffectGate/EffectJournal, or create a second truth/effect authority. Apply Goodman ancestry collapse when outputs share provider/model-family/orchestration ancestry.

## Acceptance

Before any external worker receives runtime credit, `FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1` must prove the negative cases `global admission missing`, `provider admission missing`, `UNKNOWN`, `PAID`, and `SUBSCRIPTION` each have zero secret/key lookups and zero network attempts. Positive FREE tests are mechanism tests only unless the underlying cost evidence and execution surface are separately admitted at exact identity.

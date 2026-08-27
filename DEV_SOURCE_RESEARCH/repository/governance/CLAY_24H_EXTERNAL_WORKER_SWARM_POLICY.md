# CLAY 24H EXTERNAL WORKER SWARM POLICY

Status: ACTIVE USER DIRECTIVE
Scope: sandbox-resident external research workers for EntityOS + HCU.

A `go` research swarm may use FREE_ONLY-attested NVIDIA, Mistral and Groq API credentials available to the authorized VPS sandbox. Workers are temporary organs of the persistent Clay research entity; their outputs are candidate research evidence, never canonical truth/effect authority by themselves.

## Model selection

Do not use a fixed 70B cutoff. Query each provider's live `/v1/models` catalog when possible and select models by research utility. Explicit parameter count is one signal only. Prefer capable chat/reasoning/coding/flagship models; exclude embeddings, rerankers, speech/audio, moderation/guard and other non-general research endpoints. Explicitly tiny models may be skipped. Unknown-size flagship families may be retained and empirically evaluated.

## Parallelism and rate limits

Drive parallelism adaptively toward the highest sustainable provider throughput. Observe response rate-limit headers and `Retry-After`. On HTTP 429, reduce concurrency and apply a provider-wide cooldown. Multiple credentials must not be rotated to evade a provider/project/organization rate limit. Credentials may be pooled for legitimate redundancy and independent authorized access only. HTTP 402 is a hard stop for the affected credential; no paid fallback is allowed under FREE_ONLY authority.

## 24-hour autonomy

The worker controller should run from `clay-direct-dev` for up to 24 hours without requiring the user to relay routine shell commands. It should monitor its own process state, provider errors, rate-limit behavior and artifact storage. Preserve a disk reserve and stop rather than exhausting the host.

## Research behavior

Workers receive current EntityOS/HCU state, execution authority and research constraints and perform repeated `go`-style roles: architecture, falsification, ClayCode forge, HCU causal reasoning, synthetic cognition, memory/J-Space, runtime, external GitHub/arXiv harvesting, experiment design, security review and synthesis.

External model output cannot self-grant capabilities, execute real effects, mint canonical runtime credit, or override EffectGate/EffectJournal/canonical admission rules.

## Credential boundary

Never write credential values to Git, receipts or logs. Only use credentials already present in the sandbox environment or explicit sandbox secret files supplied through an authorized secret path. Inventory may report counts/fingerprints, never secret values.

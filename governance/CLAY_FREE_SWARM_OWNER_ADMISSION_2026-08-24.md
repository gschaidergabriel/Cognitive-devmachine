# Clay Free Swarm owner admission — 2026-08-24

Status: ACTIVE OWNER DIRECTIVE
Program: EntityOS + HCU
Authority epoch target: 8.69

The owner explicitly authorizes the autonomous Free Swarm to use the available **free contingents / free tokens** for Groq, Mistral, NVIDIA and OpenRouter at maximum useful parallelism for EntityOS/HCU research inside the authorized sandbox.

## Economic boundary

- Groq: admitted for FREE_ONLY use.
- Mistral: admitted for FREE_ONLY use.
- NVIDIA: admitted for FREE_ONLY use.
- OpenRouter: admitted for FREE_ONLY use.
- Paid fallback, automatic upgrades, credit purchases and Together remain forbidden.
- A provider lane with no usable credential simply remains idle; admission is not proof that a credential exists.
- HTTP 402 remains a hard stop for the affected credential/lane.
- Rate limits must be respected; keys may not be rotated to evade a provider-wide quota.

## Throughput directive

The Free Swarm is the primary high-throughput research lever. Run it at the maximum useful parallelism allowed by the real provider/runtime limits while preserving quality gates, empirical measurement, causal evidence, disk headroom and append-only receipts.

A fabric of up to **6000 logical workers** is authorized. `logical worker` means an independently scheduled research organ/task. It does **not** mean 6000 simultaneous paid/network model requests. Actual model-call concurrency is separately bounded by provider rate limits, shared quota gates, available credentials, CPU/RAM and measured error/latency behavior.

## Quality directive

Parallelism is useful only when it increases executable progress. Workers should be sharded over distinct open questions/mechanisms and optimize for:

1. machine-readable architecture deltas;
2. patches/tests/benchmarks/falsifiers;
3. reproducible Forge evaluations;
4. accepted compressed knowledge packets;
5. measured reinjection into subsequent GO cycles.

Duplicate essays and repeated state narration are low-value and should be suppressed. Dashboard reporting must distinguish logical workers, runnable workers, actual in-flight model calls, accepted deltas, dataset yield and next-GO reinjection.

This directive records the owner's explicit instruction in the project control plane; it does not mint whole EntityOS/HCU runtime or canonical architecture credit.

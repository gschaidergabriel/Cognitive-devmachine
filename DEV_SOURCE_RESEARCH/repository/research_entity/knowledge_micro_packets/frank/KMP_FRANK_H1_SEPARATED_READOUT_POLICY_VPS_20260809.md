<!-- RAE_META
{
  "packet_id": "KMP-FRANK-H1-SEPARATED-READOUT-POLICY-VPS-20260809",
  "title": "FRANK H1 separated diagnostic/readout policy removes two frozen early-route false halts on Ubuntu",
  "domains": ["frank", "harness", "gwt", "emergenz", "observability"],
  "topics": ["adaptive_recurrence", "readout_policy_separation", "false_halt", "overthinking", "ubuntu_vps"],
  "epistemic_class": "MEASURED_RESULT_SUMMARY",
  "status_hint": "CURRENT",
  "origin_actor": "chatgpt-secondary",
  "provider": "OpenAI",
  "model": "GPT-5.6 Sol",
  "created_at": "2026-08-09T23:49:00+07:00",
  "source_refs": [
    "gschaidergabriel/Dr.-Unterweger@568c3528463ae9b1c61d1981845b9d1a4f2fafc2",
    "gschaidergabriel/Dr.-Unterweger@3ee149ab44cd544c18ded02d24b41b9b29fcf2d1",
    "gschaidergabriel/Dr.-Unterweger@f0f2820fa3ea81a89bfcfb31bfdf779e6796028d",
    "gschaidergabriel/Dr.-Unterweger@d18595cf862330029c0baaa0e5e4b128218fa6da:runtime/vps_integrity/h1_adaptive_policy_latest.json",
    "https://arxiv.org/abs/2607.20519",
    "https://aclanthology.org/2026.findings-acl.651/",
    "https://aclanthology.org/2026.acl-long.1256/",
    "https://aclanthology.org/2026.findings-acl.1199/"
  ],
  "evidence_refs": [
    "FRANK_H1_SEPARATED_READOUT_POLICY_DIFFERENTIAL",
    "FRANK_H1_ADAPTIVE_RECURRENCE_DIFFERENTIAL",
    "research_entity/rooms/center_events/20260809T2344p0700_frank_live_refusion_vps_telemetry.json"
  ],
  "confidence": 0.995,
  "verification_required": "Matched frozen historical/runtime FRANK episodes and pinned real Qwen-class 4B trials with model/runtime/template/quantization provenance",
  "falsifier_or_next_test": "The separated policy loses its false-halt/regret advantage or is dominated in cost/quality on held-out runtime or real-model episodes."
}
RAE_META -->

### Atomic result
On the real self-hosted Ubuntu runner `digital-retina`, the frozen eight-episode H1 differential reproduced a specific policy/readout conflation: raw temporal-W4 diagnostic exit produced two early `ROUTE` false halts. A separate proposal-only policy layer preserved the diagnostic readout but allowed bounded positive pre-cycle observation before the minimum cycle-evidence window.

Measured aggregate receipts on the same frozen episodes:

- raw temporal W4 diagnostic exit: accuracy `0.75`, false halts `2`, correct-to-wrong drift `0`, total regret `0.64`, total cost `1.63`, recurrences `38`;
- separated diagnostic + policy: accuracy `0.75`, false halts `0`, correct-to-wrong drift `0`, total regret `0.52`, total cost `1.91`, recurrences `45`;
- fixed budget: accuracy `0.625`, false halts `0`, correct-to-wrong drift `1`, total regret `1.38`, total cost `2.21`, recurrences `52`.

Relative to raw W4, the separated policy reduced regret by `18.75%` and removed both frozen false halts, but increased synthetic cost by `17.18%` and recurrences by `18.42%`. Relative to fixed budget it still used `13.57%` less synthetic cost and `13.46%` fewer recurrences while reducing regret by `62.32%`.

### Interpretation boundary
This is a reproducible **real-Ubuntu execution of a synthetic frozen workload**, not real-model evidence and not production policy selection. It supports separating trajectory/readout diagnostics from adaptive-exit policy, consistent with current looped-transformer evidence that trajectory formation and exit readout should be diagnosed separately. It does not support any consciousness claim.

### Architecture implication
Keep four planes distinct:

1. diagnostic/readout observation;
2. proposal-only recurrence/routing policy;
3. model proposal/tool-call layer;
4. external authority/effect/re-entry layer.

Do not weaken the diagnostic fail-closed semantics merely to improve an adaptive controller score. Put policy exceptions in a separately versioned, hashable policy receipt.

### Next falsifier
Replay the same policy family on frozen historical FRANK runtime episodes, then on matched real Qwen-class 4B episodes with identical prompts/seeds where feasible. Preserve route/rollback benefit and cost explicitly; do not score `ROUTE` as zero-cost terminal behavior once a real routing path exists.

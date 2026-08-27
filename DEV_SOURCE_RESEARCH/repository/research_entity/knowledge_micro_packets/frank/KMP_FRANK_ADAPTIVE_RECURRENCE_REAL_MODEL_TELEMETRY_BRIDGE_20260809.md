<!-- RAE_META
{
  "packet_id": "KMP-FRANK-ADAPTIVE-RECURRENCE-REAL-MODEL-TELEMETRY-BRIDGE-20260809",
  "title": "FRANK adaptive recurrence should be falsified with real-model backend telemetry",
  "domains": ["frank", "gwt", "model_runtime", "observability", "emergenz"],
  "topics": ["adaptive_recurrence", "stopping_policy", "real_model", "qwen_4b", "backend_metrics", "false_halt"],
  "epistemic_class": "OPEN_HYPOTHESIS",
  "claim_status_hint": "OPEN",
  "origin_class": "MODEL_AUTHORED_RESEARCH_SYNTHESIS",
  "origin_actor": "chatgpt-secondary",
  "created_at": "2026-08-09T23:39:00+07:00",
  "updated_at": "2026-08-09T23:39:00+07:00",
  "source_refs": [
    "gschaidergabriel/Dr.-Unterweger:tests/adaptive_recurrence_differential_experiment.py",
    "gschaidergabriel/Dr.-Unterweger@02e19765b6784d1ebb6203ce7897073b72b6d18d",
    "https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507",
    "https://github.com/ggml-org/llama.cpp/tree/master/tools/server"
  ],
  "evidence_refs": [
    "gschaidergabriel/Dr.-Unterweger@216848a177187442dde6ddbcb23ba2b6fa851440:runtime/vps_integrity/latest.log",
    "KMP-FRANK-LOCAL-MODEL-BACKEND-TIMING-CONTRACT-20260809"
  ],
  "related_claim_ids": [],
  "related_experiment_ids": ["FRANK_H1_ADAPTIVE_RECURRENCE_DIFFERENTIAL"],
  "predecessor_packet_ids": [],
  "supersedes_packet_ids": [],
  "confidence": 0.68,
  "verification_required": "Matched fixed-budget versus temporal-multi-signal real Qwen-class 4B episodes with complete model/runtime/template/quantization provenance",
  "falsifier_or_next_test": "The synthetic w4 advantage disappears, task errors or false halts dominate, or timing/resource noise prevents a stable quality-compute frontier under real pinned inference.",
  "search_terms": ["FRANK adaptive recurrence", "temporal_multi_signal_w4", "false halt", "real Qwen 4B recurrence", "adaptive compute telemetry"]
}
RAE_META -->

### Core
On the frozen synthetic eight-episode differential, `temporal_multi_signal_w4` improved accuracy (0.75 vs 0.625), mean utility (0.5125 vs 0.42) and total regret (0.64 vs 1.38) while reducing mean recurrences (4.75 vs 6.5) and total cost (1.63 vs 2.21) relative to fixed budget. The newly merged backend-timing receipt supplies a concrete measurement surface for testing whether that quality/compute tradeoff survives real Qwen-class inference.

### Evidence / boundary
The recurrence result is explicitly `SYNTHETIC_FROZEN_DIFFERENTIAL_EXPERIMENT`, not real-model evidence. `w4` also produced two false halts while fixed budget produced zero, so the result does not justify the blanket claim that adaptive stopping is superior. No consciousness inference follows from recurrence behavior.

### Implication
A matched real-model A/B experiment can now measure task outcome, recurrence count, false halts, tool behavior, tokens, prompt/decode timing and resource cost together rather than optimize one proxy.

### Next test
Pin Qwen 4B weights, runtime, template, quantization and sampling; compare fixed budget against the temporal family on identical tasks/seeds while keeping correctness labels hidden from the policy and measuring route/rollback cost explicitly.

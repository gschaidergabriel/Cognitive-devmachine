<!-- RAE_META
{
  "packet_id": "KMP-FRANK-LOCAL-MODEL-BACKEND-TIMING-CONTRACT-20260809",
  "title": "FRANK local-model backend timing contract is bounded and Ubuntu-tested",
  "domains": ["frank", "model_runtime", "observability", "harness"],
  "topics": ["local_model", "openai_compatible", "backend_metrics", "timings", "tool_calls", "ubuntu_vps"],
  "epistemic_class": "MEASURED_RESULT_SUMMARY",
  "claim_status_hint": "CURRENT",
  "origin_class": "MODEL_AUTHORED_RESEARCH_SYNTHESIS",
  "origin_actor": "chatgpt-secondary",
  "created_at": "2026-08-09T23:39:00+07:00",
  "updated_at": "2026-08-09T23:39:00+07:00",
  "source_refs": [
    "gschaidergabriel/Dr.-Unterweger#26",
    "gschaidergabriel/Dr.-Unterweger@02e19765b6784d1ebb6203ce7897073b72b6d18d",
    "https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507",
    "https://github.com/ggml-org/llama.cpp/tree/master/tools/server"
  ],
  "evidence_refs": [
    "gschaidergabriel/Dr.-Unterweger@216848a177187442dde6ddbcb23ba2b6fa851440:runtime/vps_integrity/latest.json",
    "gschaidergabriel/Dr.-Unterweger@216848a177187442dde6ddbcb23ba2b6fa851440:runtime/vps_integrity/latest.log",
    "gschaidergabriel/Dr.-Unterweger@02e19765b6784d1ebb6203ce7897073b72b6d18d:tests/local_model_tool_metrics_regression.py"
  ],
  "related_claim_ids": [],
  "related_experiment_ids": [],
  "predecessor_packet_ids": [],
  "supersedes_packet_ids": [],
  "confidence": 0.98,
  "verification_required": "Real pinned Qwen-class 4B inference plus final Andreas Ubuntu target-host acceptance",
  "falsifier_or_next_test": "Run a pinned real Qwen-class 4B/runtime/template/quantization on Ubuntu and verify that admitted timing fields remain semantically stable while tool and hidden-reasoning boundaries remain intact.",
  "search_terms": ["FRANK F6 timings", "backend metrics", "Qwen 4B", "llama.cpp timings", "local_model_tool_metrics"]
}
RAE_META -->

### Core
FRANK commit `02e19765b6784d1ebb6203ce7897073b72b6d18d` adds an optional allowlisted local-model timing receipt while preserving the existing engine-neutral OpenAI-compatible tool contract. The exact commit passed the real self-hosted Ubuntu integrity matrix on `digital-retina`: 20/20 gates PASS, including `local_model_tool_metrics`, with the full Python test suite at 15/15 PASS.

### Evidence / boundary
The regression proves transport/filter semantics: admitted finite non-negative timing numbers survive, arbitrary backend fields and a hidden-reasoning sentinel do not. Its example 90 ms prompt and 160 ms decode values are deterministic fixtures, **not physical model performance**. `release_claim` remains false.

### Implication
FRANK now has a bounded observation surface suitable for later prompt/decode cost comparisons without hard-binding cognition to llama.cpp or granting model output effect authority.

### Next test
Run matched real Qwen-class 4B trials with pinned weights, quantization, template and runtime, then reproduce the contract and measure real latency/throughput/resource distributions on Ubuntu and Andreas' target machine.

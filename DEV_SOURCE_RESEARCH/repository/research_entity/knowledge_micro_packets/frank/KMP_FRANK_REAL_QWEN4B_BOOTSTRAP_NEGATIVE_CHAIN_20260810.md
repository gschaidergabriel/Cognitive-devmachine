<!-- RAE_META
{
  "packet_id": "KMP-FRANK-REAL-QWEN4B-BOOTSTRAP-NEGATIVE-CHAIN-20260810",
  "title": "Real Qwen4B Ubuntu shadow bootstrap exposed CMake and Ninja environment assumptions before model execution",
  "domains": ["frank", "model_runtime", "deployment", "harness", "observability"],
  "topics": ["qwen4b", "llama_cpp", "ubuntu", "self_hosted_runner", "negative_result", "build_bootstrap"],
  "epistemic_class": "NEGATIVE_RESULT_SUMMARY",
  "status_hint": "NEGATIVE_RESULT",
  "origin_actor": "chatgpt-secondary",
  "provider": "OpenAI",
  "model": "GPT-5.6 Sol",
  "created_at": "2026-08-10T00:08:00+07:00",
  "source_refs": [
    "gschaidergabriel/Dr.-Unterweger@ed5d35e60105dc9ad12496833c219c8f0b36d3c5:runtime/vps_integrity/real_qwen4b_shadow_latest.json",
    "gschaidergabriel/Dr.-Unterweger@5092752f2c100d9d23ca7f7015e4ecb57c4db55c:runtime/vps_integrity/real_qwen4b_shadow_latest.json",
    "gschaidergabriel/Dr.-Unterweger@963fd8a6a044b6f5a6ddfde88fab25d0cc6e1dae",
    "gschaidergabriel/Dr.-Unterweger@b8b8aea5beee6e8bde0db8b9ba1fb46795886634",
    "https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md",
    "https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md"
  ],
  "confidence": 0.999,
  "verification_required": "A later receipt must prove build, pinned model hash verification, server readiness and actual benchmark execution; do not infer success from repaired bootstrap alone.",
  "falsifier_or_next_test": "Execute the same pinned model/runtime experiment after correcting the environment bootstrap and persist the next failure or benchmark receipt."
}
RAE_META -->

### Negative result chain

A pinned CPU-only real-model shadow lane was added for `ggml-org/Qwen3-4B-Instruct-2507-Q8_0-GGUF`, revision `e92aed4`, file `qwen3-4b-instruct-2507-q8_0.gguf`, expected SHA-256 `ae916ede1c010a26955ee8ae2e908bf8815a3f135ec860439ab924701c69d5f1`, with llama.cpp pinned to commit `936918514ce522b553c0fd80b169a6440e6096c6`.

The first real self-hosted Ubuntu attempt failed before model execution with:

`MISSING_REQUIRED_COMMAND:cmake`

The receipt contained `benchmark=null` and `real_model_executed=false`. Therefore this was a real Ubuntu **attempt**, not real-model execution evidence.

A sibling repair then installed pinned CMake 3.31.6 and Ninja 1.11.1.3 in a per-run temporary prefix rather than mutating the persistent runner. The second attempt progressed past the original CMake blocker but failed with:

`BOOTSTRAPPED_NINJA_MISSING`

Again `benchmark=null` and `real_model_executed=false`.

### Causal interpretation

The second failure narrowed the defect: package installation succeeded sufficiently for CMake to be recorded, but the workflow assumed the pip `--prefix` script layout would expose `ninja` directly on `$PREFIX/bin`. That layout assumption was false on the observed runner/package combination.

This is an integration/bootstrap defect, not evidence against Qwen3-4B, llama.cpp inference quality, FRANK's adapter semantics or CPU-only feasibility.

### Repairs now represented in live branches

Two non-conflated repair paths were created:

1. sibling path: resolve pinned CMake/Ninja executables by their actual temporary installation paths while preserving all model/runtime pins;
2. independent make path: remove Ninja from the critical build dependency and use CMake `Unix Makefiles` with the host `make`, while keeping CMake ephemeral and all model/runtime/model-hash pins unchanged.

Whichever path produces the next receipt first is evidence; neither path is considered successful merely because its workflow definition exists.

### External mechanism check

Current llama.cpp primary documentation explicitly supports a CPU CMake build and a `llama-server` target, with the server exposing an OpenAI-compatible chat-completions endpoint. This supports the chosen mechanism but does not replace runtime evidence.

### Anti-conflations

- workflow committed != workflow executed;
- build-tool bootstrap PASS != llama.cpp build PASS;
- llama.cpp build PASS != model hash verified;
- model hash verified != server ready;
- server ready != FRANK benchmark PASS;
- failed environment bootstrap != model-quality failure;
- later success must not erase either negative receipt.

<!-- RAE_META
{
  "packet_id": "KMP-FRANK-VPS-REAL-MODEL-CAPABILITY-GAP-20260809",
  "title": "Current self-hosted Ubuntu VPS is an integrity lane, not a preconfigured real 4B inference lane",
  "domains": ["frank", "model_runtime", "deployment", "observability"],
  "topics": ["qwen_4b", "vps", "gpu", "cpu", "memory", "runtime", "target_host"],
  "epistemic_class": "MEASURED_RESULT_SUMMARY",
  "status_hint": "CURRENT",
  "origin_actor": "chatgpt-secondary",
  "provider": "OpenAI",
  "model": "GPT-5.6 Sol",
  "created_at": "2026-08-09T23:49:00+07:00",
  "source_refs": [
    "gschaidergabriel/Dr.-Unterweger@982873dc555c84672a0150594cfa903716a1da9c",
    "gschaidergabriel/Dr.-Unterweger@1e896f33cafb425f4027c6672a866b62e5dad28e:runtime/vps_integrity/model_capability_latest.json",
    "https://huggingface.co/Qwen/Qwen3.5-4B"
  ],
  "evidence_refs": ["FRANK_VPS_MODEL_CAPABILITY_PROBE"],
  "confidence": 0.995,
  "verification_required": "Re-probe after runtime/hardware provisioning; final v0.1 acceptance must execute on Andreas' Ubuntu developer system",
  "falsifier_or_next_test": "A later capability receipt shows an installed supported local runtime and suitable accelerator/CPU configuration, followed by reproducible real-model inference."
}
RAE_META -->

### Atomic result
A read-only capability probe executed on `digital-retina` and found:

- Linux `6.8.0-117-generic` x86_64;
- 4 logical CPUs reported from an AMD EPYC 9354P host;
- `16,376,020 KiB` total RAM and about `13,455,480 KiB` available at probe time;
- zero configured swap;
- about `170.25 GB` free in the checked filesystem;
- no `/dev/dri`, `/dev/kfd`, `/dev/nvidia0`, `/dev/nvidiactl`, or `/dev/nvidia-uvm`;
- no `nvidia-smi`, `rocminfo`, `vulkaninfo`, `llama-server`, `llama-cli`, `ollama`, `vllm`, or `sglang` command found;
- no Python `torch`, `transformers`, `vllm`, `sglang`, or `llama_cpp` package found;
- `real_model_executed=false`.

### Interpretation boundary
This refutes only the operational assumption that the current VPS is **already configured** as a real Qwen-class 4B inference host. It does not prove that CPU-only inference is impossible or that a runtime cannot be installed. No model weights were downloaded by the probe.

The current official Qwen3.5-4B model card exposes OpenAI-compatible serving examples through vLLM and SGLang, which is architecturally compatible with FRANK's engine-neutral OpenAI-compatible adapter. That compatibility is interface-level, not a measured FRANK/Qwen acceptance result.

### Architecture implication
Keep `digital-retina` as the current high-value Ubuntu integration/falsification lane for repository, SQLite, transport, schema, migration and synthetic/controller tests. Do not report a real local-4B pass until a pinned model/runtime/template/quantization actually executes and produces immutable receipts.

For v0.1 release gating, Andreas' Ubuntu developer system remains the final target host. A separately provisioned model endpoint may be used for research only if receipts bind endpoint class, model weights, runtime, quantization, template and sampling configuration.

### Next falsifier
Run the capability probe on Andreas' target system. If a suitable local runtime exists or is explicitly provisioned, execute matched real-model acceptance trials through FRANK's current adapter and backend-metric contract, including tool-call semantics, latency/throughput, memory, recurrence policy, recovery and deterministic provenance.

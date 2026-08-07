# Reserved Trigger: `frank`

Research FRANK as one integrated cognitive/runtime architecture, not as a loose list of services. Use the Master Research Trigger Protocol.

Primary questions:
- Which functions are semantically distinct organs versus accidental process/database boundaries?
- How can the full FRANK architecture become one coherent module/runtime while preserving multi-rate dynamics, isolation where needed and observability?
- Which current service/DB boundaries add latency, duplicated state or lost causal traceability?
- How should Qwen-class 4B inference, Needle/classifiers, memory, GWT, policy and execution gateways compose?
- Which portions belong inside Synthetic Clay and which remain host/runtime infrastructure?
- What is the Linux-first implementation path and how can the semantic runtime later target Android/edge, Windows/macOS and other platforms?

Mandatory research dimensions:
- whole-system state/dataflow graph;
- fast/slow loop timing and scheduler design;
- shared-state versus message/IPC boundaries;
- persistence and recovery;
- capability/security boundaries;
- model routing/inference economics;
- hot-path latency and zero-copy opportunities;
- observability/replay;
- mobile Qwen-4B constraints: quantization, RAM/KV cache, CPU/GPU/NPU/Vulkan, thermals, battery, lifecycle and sandboxing.

Treat older architecture measurements as versioned evidence. Re-ground any claim about current FRANK against current code/runtime when accessible.

Output architecture deltas, module-collapse candidates, boundaries that must remain isolated, measurable migration steps and rollback conditions. Write the final report to `research_entity/trigger_runs/frank/<run_id>/FINAL_REPORT.md` and finish with the mandatory status footer.

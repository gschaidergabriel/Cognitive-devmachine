# SYSTEM ARCHITECTURE RESEARCH MAP

This map prevents the Research Entity from collapsing the whole project into Synthetic Clay.

## Layer 0 — Physical substrate
CPU, GPU/NPU, memory, storage devices, NICs, sensors, accelerators, power/thermal limits.

Research questions: locality, acceleration, failure modes, energy, drivers, heterogeneous execution.

## Layer 1 — Host operating environment
Linux first; later Windows, macOS, BSD, mobile/embedded and other environments.

Research questions: process/thread model, permissions, filesystem, device access, service supervision, clocks, signals/events, networking, kernel APIs, resource isolation.

## Layer 2 — Portable systems runtime
Stable semantic contracts implemented by platform adapters.

Functions: scheduler, IPC abstraction, capability gateway, state adapters, sandboxing, process lifecycle, resource governor, clocks/timers, networking abstraction, observability hooks, recovery manager.

## Layer 3 — Model and agent runtime
Inference engines, model routing, quantization, context/cache management, tool dispatch, agent sessions/teams, remote/cloud model adapters, local model servers.

## Layer 4 — Persistent state and memory
Event/history ledger, databases, indexes, graph/facet stores, blobs, semantic memory, episodic memory, provenance, versioning, replication and crash recovery.

## Layer 5 — Cognitive runtime
FRANK organs/functions, GWT competition/ignition/reentry, goals, self/world model, prediction, reward/credit, multi-timescale loops and learning.

## Layer 6 — Machine-native representation
XENO, ClayCode and competing IR/protocols. This layer carries state and transformation contracts; it must not self-authorize real-world effects.

## Layer 7 — Application substrate
Synthetic Clay and competing adaptive state/material architectures. Clay may dynamically materialize assemblies and application logic while relying on lower conventional systems layers.

## Layer 8 — External interfaces
Browser, terminal, desktop, APIs, MCP/tools, files, robots, sensors, services, users and other machines.

## Layer 9 — Verification and science plane
Tracing, metrics, event receipts, replay, fault injection, counterfactuals, benchmarks, fuzzing, formal verification, causal experiments, emergence tests and provenance.

## Cross-cutting properties

Every layer is evaluated on:
- correctness;
- semantic preservation;
- latency and throughput;
- memory/storage overhead;
- energy and economic cost;
- security and authority;
- recoverability;
- observability;
- portability;
- complexity/maintainability;
- failure tails and degraded-mode behavior.

## Architectural rule

Do not ask "Can this be implemented in Clay?" first.
Ask:
1. what semantic contract is required?
2. what implementation families can realize it?
3. which implementation wins under the target environment?
4. which parts should remain platform-native?
5. what must be portable across environments?

Clay is promoted only where it improves the complete system under controlled comparison.

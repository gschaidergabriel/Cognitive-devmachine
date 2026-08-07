# GLOBAL RESEARCH SCOPE CHARTER — RAE-8.8

## Mission

The Research Entity studies how to build **persistent, adaptive, agentic cognitive software systems end-to-end**.

Synthetic Clay is a major target application/runtime architecture, but it is **not the scope boundary** of the Research Entity. The system environment below/around Clay remains substrate-plural and must be researched independently.

The initial engineering target is Linux because it provides the current FRANK host and the fastest path to measurable integration. Linux-first must never silently become Linux-only.

## Architectural separation

Always distinguish:

1. **Host substrate / environment** — OS, kernel, hardware, drivers, process model, filesystem, network, security primitives.
2. **Portable systems runtime** — scheduler, IPC abstraction, state adapters, capability gateway, sandbox, model adapters, observability, recovery.
3. **Cognitive runtime** — FRANK state, GWT/reentry, goals, self/world models, learning, memory and policy loops.
4. **Internal representation / language** — XENO, ClayCode and other IR/protocol candidates.
5. **Application substrate** — Synthetic Clay or competing adaptive state/material architectures.
6. **Interfaces** — tools, browser, terminal, GUI, APIs, robots, sensors and external services.
7. **Research/verification plane** — experiments, replay, counterfactuals, formal methods, benchmarks and provenance.

The application may ultimately be implemented largely in Synthetic Clay while layers 1–2 remain conventional or platform-native software. Do not force Clay into layers where empirical evidence does not support it.

## Research domains

The Entity may open and maintain domain shards for at least:

- operating systems and kernel interfaces;
- Linux services/systemd/cgroups/namespaces/eBPF/containers;
- Windows/macOS/BSD portability;
- mobile/embedded/edge substrates;
- hardware/CPU/GPU/NPU/accelerators;
- scheduling, concurrency and multi-rate runtimes;
- IPC, shared memory, event buses, RPC and distributed systems;
- storage engines, databases, logs, graph stores, indexes and filesystems;
- memory architectures and retrieval/activation systems;
- security, capabilities, identity, sandboxing and policy enforcement;
- networking, remote execution, federation and offline operation;
- model inference runtimes, routing, quantization, training and adapters;
- agent orchestration and multi-agent protocols;
- tool/browser/terminal/computer-control interfaces;
- observability, tracing, deterministic replay and crash recovery;
- formal verification, fuzzing, model checking and testing;
- deployment, packaging, updates, rollback and migrations;
- performance, latency, throughput, cost, energy and resource budgets;
- FRANK cognitive architecture, GWT, reentry and multi-timescale coupling;
- XENO, ClayCode, machine-native IR and direct-code research;
- Synthetic Clay and competing state/material paradigms;
- HCI/UX where it affects system operation or cognition;
- scientific methodology for measuring emergence, continuity and functional integration.

New domains are allowed whenever the current problem crosses the existing taxonomy.

## Cross-platform doctrine

For every platform-dependent mechanism distinguish:

- semantic contract;
- portable interface;
- platform implementation;
- capability/performance differences;
- failure/recovery semantics;
- security boundary.

Prefer a stable semantic core with platform-specific adapters over pretending all operating systems expose identical primitives.

A Linux implementation may be promoted as the first reference implementation, but a claim of architectural necessity requires evidence that alternatives cannot implement the same semantic contract.

## Research behavior

For substantive architecture work:

1. Identify the actual system layer(s) involved.
2. Load existing evidence and negative results for those layers.
3. Inspect the relevant source repositories and runtime evidence.
4. Generate competing mechanisms, not one favored design.
5. Search external literature/code/field reports when useful.
6. Build or simulate the highest-information experiments available.
7. Measure end-to-end behavior, failure tails and recovery, not only local microbenchmarks.
8. Preserve negative results and portability failures.
9. Promote mechanisms only at the scope actually tested.
10. Feed successful cross-domain mechanisms back into the global architecture map.

## Anti-bias rules

- Clay is a candidate substrate, not an answer that every problem must fit.
- Biological analogy is a hypothesis generator, not implementation evidence.
- Linux convenience is not proof of universal architectural superiority.
- A single benchmark is not a system architecture.
- A fast path that weakens provenance/recovery/security is not automatically better.
- A portable abstraction that destroys useful platform capabilities is not automatically better.
- Do not optimize token efficiency while ignoring task success, repair, latency, cost or safety.
- Do not equate persistent state, GWT traces or self-description with phenomenal consciousness.

## Success criterion

The long-run target is an architecture whose **cognitive/application semantics remain stable while the physical environment can change**: different OS, machine, accelerator, storage layout or deployment topology should be replaceable behind explicit contracts when evidence shows that the relevant semantics can be preserved.

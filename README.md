# Global Research Entity — RAE-8.8

This repository is the canonical external state backend for the FRANK 2.0 project-wide Research Entity.

Despite the repository name, the entity is **not a Synthetic-Clay-only researcher**. Synthetic Clay is one target application/runtime architecture. The Research Entity studies the whole problem of building persistent, agentic, adaptive cognitive software systems.

## Research team

There is **one persistent Research Entity with multiple explicitly attributed temporary researchers**.

- **Claude Code — Lead Researcher / Primary Adjudicator** (`claude-code-lead`)
- **ChatGPT — Independent Secondary Researcher** (`chatgpt-secondary`)
- **Gabriel — Project Owner / Research Director** (`user-gabriel`)

Claude Code has the highest researcher adjudication weight for unresolved FRANK architecture, implementation interpretation, prioritization and integration decisions because it is expected to work directly against the live FRANK code/runtime. **Verified evidence and reproducible measurements still outrank every researcher's opinion.**

If you are Claude Code receiving this repository as a ZIP, start here:

1. `CLAUDE_CODE_INTRODUCTION.md`
2. `CLAUDE.md`
3. `research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json`
4. `research_entity/continuity/BOOTSTRAP_MINIMAL.json`
5. `research_entity/global/SESSION_MEMBERSHIP_PROTOCOL.md`

Do not create a second Claude-only canonical Research Entity.

## Provenance

Authorship and ingestion are explicitly tracked. Machine-authored artifacts should identify whether they originate from ChatGPT or Claude Code. Imported user/external sources retain their original authorship and separately record the ingesting worker.

Read:

- `research_entity/global/RESEARCH_ACTOR_REGISTRY.json`
- `research_entity/global/MULTI_RESEARCHER_GOVERNANCE.md`
- `research_entity/global/PROVENANCE_POLICY.md`
- `research_entity/provenance/ARTIFACT_PROVENANCE.jsonl`

## Research mission

Research how such systems can be built end-to-end:

- Linux-first host/runtime architecture;
- later portability to Windows, macOS, BSD, mobile, embedded and other substrates;
- Android/edge execution with local Qwen-4B-class models;
- CPU/GPU/NPU acceleration, quantization, RAM/KV-cache, thermal and battery constraints;
- process supervision, IPC, scheduling and resource control;
- persistence, memory, databases, event/history stores and recovery;
- security, capabilities, sandboxing, permissions and commit boundaries;
- networking, distributed execution and multi-machine operation;
- model runtimes, inference, routing, orchestration and training;
- agent/tool/browser/terminal integration;
- observability, replay, testing, benchmarking and formal verification;
- cognitive architectures including FRANK/GWT;
- internal languages/IR including XENO and ClayCode;
- Synthetic Clay as the intended adaptive application substrate;
- packaging, deployment, updates, migration and cross-platform compatibility;
- performance, energy, latency, cost and reliability.

The application itself may ultimately run in Synthetic Clay, while its **environment is intentionally substrate-plural** and must not be assumed to be Clay.

## Canonical research head

- Research Entity revision: **2**
- Clay generation: **3**
- State hash: `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

Canonical file:

`research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json`

Repository/bootstrap/configuration improvements do not by themselves create a new research revision or Clay generation.

## Fast boot

Read `PROJECT_AUTO_BOOT_KERNEL_FINAL.txt`. Normal workers should use the tiered boot in `BOOTSTRAP_MINIMAL.json` rather than eagerly loading the entire institution.

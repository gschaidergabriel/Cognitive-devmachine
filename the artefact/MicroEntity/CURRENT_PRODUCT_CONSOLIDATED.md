# Current MicroEntity product contract

MicroEntity is the user-facing self-hosted configuration and cognition-inspection surface of EntityOS/Mini Entity.

Fixed product components:
1. bundled generic approximately-0.8B local cognition core;
2. fixed/versioned J-Space↔GWT integration around that core;
3. one Cognitive Module ON/OFF control;
4. first-class Claude Code targeted-inference adapter;
5. adaptive capability-driven integration for other models/APIs;
6. model-specific J-Space profiles only where real hookable latent access exists;
7. MiniUnifiedDB/deterministic gates remain truth/state/effect authority;
8. self-hosted dashboard with explicit first activation, autostart and stable local URL where the host permits it, plus deterministic loopback fallback;
9. co-developed **Hyperposition Computational Unit (HCU)**: a persistent strategic world-model/simulation compute organ built as a sparse grid of logical approximately-0.8B cognition modules using a small measured number of shared/mmap physical workers;
10. HCU free-LLM/token-fundus ingestion as provenance-bound candidate evidence only;
11. HCU -> Zero feedback carrying dynamic goal, hypothesis, plan and improvement candidates without granting HCU direct truth/effect authority.

Closed APIs are `COMPILED_EXTERNAL` and never represented as hidden-state-integrated. Local hookable models may be `FULL_LOCAL_LATENT` after exact model/profile calibration.

HCU target deployment profile: KVM4 / 4 vCPU / 16 GB RAM / 200 GB disk / 16 TB bandwidth. This is currently a deployment/resource target only; acceptance testing remains under the repository's authorized-isolated-sandbox-only law.

The HCU's permanent world model does not create a second canonical reality. Accepted durable world state, causal timeline, goal state and verified outcomes remain in MiniUnifiedDB. HCU VPS caches/checkpoints are rebuildable or explicitly non-authoritative.

Package snapshot: `MICROENTITY_CURRENT.zip`.

Package rule: every package-safe HCU source/config/schema/receipt/data file lives under `hcu/` in this package and is recursively included in the rebuilt snapshot. Secrets are never packaged.

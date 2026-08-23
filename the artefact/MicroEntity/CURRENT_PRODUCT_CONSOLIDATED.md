# Current MicroEntity product contract

MicroEntity is the user-facing self-hosted configuration and cognition-inspection surface of EntityOS/Mini Entity.

Fixed product components:
1. bundled generic approximately-0.8B local cognition core;
2. Hyperposition Computational Unit (HCU) scheduler/grid: many logical ~0.8B cognition lanes over one persistent Mini Entity, preferring shared immutable weights and measured capacity rather than guessed full-model replication;
3. fixed/versioned J-Space↔GWT integration around the local cognition substrate;
4. one Cognitive Module ON/OFF control;
5. first-class Claude Code targeted-inference adapter;
6. adaptive capability-driven integration for other models/APIs;
7. model-specific J-Space profiles only where real hookable latent access exists;
8. MiniUnifiedDB/deterministic gates remain truth/state/effect authority;
9. self-hosted dashboard with explicit first activation, autostart and stable local URL where the host permits it, plus deterministic loopback fallback.

HCU invariants:
- persistent Mini Entity count stays exactly one;
- HCU lanes are ephemeral packet/Hyperposition compute slots, not durable agents or memory authorities;
- parallel lane/model output is candidate-only;
- one admitted GWT/write-back boundary decides what may reach deterministic validation;
- no numeric resident-lane or active-parallelism claim is accepted before exact checkpoint/runtime RSS, incremental lane memory and CPU throughput are measured;
- free external LLM/token-pool output may feed candidate research only and cannot bypass MiniUnifiedDB or the effect gate;
- Together remains forbidden under current control.

Closed APIs are `COMPILED_EXTERNAL` and never represented as hidden-state-integrated. Local hookable models may be `FULL_LOCAL_LATENT` after exact model/profile calibration.

Package snapshot: `MICROENTITY_CURRENT.zip`.

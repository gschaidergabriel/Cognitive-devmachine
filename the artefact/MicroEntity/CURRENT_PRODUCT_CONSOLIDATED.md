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
9. Hyperposition Computational Unit (HCU): many logical ~0.8B module roles arranged as a grid and scheduled over bounded hot local inference lanes, with long-horizon simulation, world-model projection, goal/hypothesis generation, Zero-twin modelling and FREE_ONLY external research feeds.

The HCU does **not** mathematically fuse independent 0.8B checkpoints into one larger neural network. The "GPU-like" property is architectural: tiled module state, shared/memory-mapped model bytes where supported, a central scheduler, bounded parallel inference lanes, message/broadcast fabric and deterministic barriers. This avoids multiplying RAM needlessly on a 4-core/16-GB VPS.

World-model law:
- persistent world-model facts remain canonical MiniUnifiedDB claims with provenance/valid-time/confidence;
- derived simulation timelines, counterfactuals, goals and Zero-twin predictions are typed candidate state;
- future confidence decays with horizon and calibration evidence;
- no HCU module can bypass MiniUnifiedDB or EffectGate.

Closed APIs are `COMPILED_EXTERNAL` and never represented as hidden-state-integrated. Local hookable models may be `FULL_LOCAL_LATENT` after exact model/profile calibration.

Package snapshot: `MICROENTITY_CURRENT.zip`.

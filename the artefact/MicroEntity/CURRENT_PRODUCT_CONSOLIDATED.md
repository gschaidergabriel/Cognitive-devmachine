# Current MicroEntity product contract

MicroEntity is the user-facing self-hosted configuration and cognition-inspection surface of
EntityOS/Mini Entity.

Fixed product components:
1. bundled generic approximately-0.8B local cognition core;
2. fixed/versioned J-Space↔GWT integration around that core;
3. one Cognitive Module ON/OFF control;
4. first-class Claude Code targeted-inference adapter;
5. adaptive capability-driven integration for other models/APIs;
6. model-specific J-Space profiles only where real hookable latent access exists;
7. MiniUnifiedDB/deterministic gates remain truth/state/effect authority;
8. Hyperposition Computational Unit (HCU): a modular grid of ~0.8B cognition cells scheduled as a
   software-defined compute fabric, including long simulations, causal world-model projection,
   dynamic goal proposals, Zero cognition-twin modeling and hypothesis feedback;
9. self-hosted dashboard with explicit first activation, autostart and stable local URL where the
   host permits it, plus deterministic loopback fallback.

The HCU is GPU-like only in coordination pattern: many small cells exchange typed packets through a
scheduler/bus. It is not a claim of GPU-equivalent arithmetic throughput.

The preferred 16 GB / 4-core deployment topology maximizes *logical* cells by sharing one pinned
~0.8B base runtime where possible and giving each cell separate role/state/adapters. Independent
full-model resident cells remain supported, but their admitted count is derived only from measured
RSS/latency on the exact runtime; no hard module count is canonical before measurement.

Closed APIs are `COMPILED_EXTERNAL` and never represented as hidden-state-integrated. Local hookable
models may be `FULL_LOCAL_LATENT` after exact model/profile calibration.

Package snapshot: `MICROENTITY_CURRENT.zip`.

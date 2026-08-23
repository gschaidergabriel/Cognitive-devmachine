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
8. self-hosted dashboard with explicit first activation, autostart and stable local URL where the host permits it, plus deterministic loopback fallback.

Canonical cognition-path invariant:

`pipeline_build_prompt -> pipeline_cognitive_fabric_admit -> inference_generate`

The inference request must be derived from the admitted Cognitive Fabric envelope, including its InferencePacket and fabric-receipt digests. Merely naming or observing a J-Space/GWT/UCF stage is not causal-use credit, and no cognition stage may bypass MiniUnifiedDB truth/state authority or deterministic effect gates.

Closed APIs are `COMPILED_EXTERNAL` and never represented as hidden-state-integrated. Local hookable models may be `FULL_LOCAL_LATENT` after exact model/profile calibration.

Package snapshot: `MICROENTITY_CURRENT.zip`.

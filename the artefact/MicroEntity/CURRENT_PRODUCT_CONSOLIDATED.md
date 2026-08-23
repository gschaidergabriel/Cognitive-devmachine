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
9. Hyperposition Computational Unit (HCU): a resource-adaptive logical grid of many ~0.8B module roles over a bounded resident worker pool, supporting persistent world-model maintenance, goal candidates, long simulations, Zero behavioral modeling and improvement hypotheses;
10. FREE_ONLY external LLM feed into typed candidate packets, never direct truth/effect authority.

HCU reference deployment target supplied by the owner: KVM 4, 4 CPU cores, 16 GB RAM, 200 GB disk, 16 TB bandwidth.

Canonical cognition-path invariant:

`pipeline_build_prompt -> pipeline_cognitive_fabric_admit -> inference_generate`

The inference request must be derived from the admitted Cognitive Fabric envelope, including its InferencePacket and fabric-receipt digests. Merely naming or observing a J-Space/GWT/UCF stage is not causal-use credit. The Cognitive Fabric may shape candidate cognition but cannot mint truth, persistent state or effect authority.

Closed APIs are `COMPILED_EXTERNAL` and never represented as hidden-state-integrated. Local hookable models may be `FULL_LOCAL_LATENT` after exact model/profile calibration.

The HCU does not create a second entity or second truth store. MiniUnifiedDB remains canonical; EffectGate remains the real-effect boundary.

Package snapshot: `MICROENTITY_CURRENT.zip`.

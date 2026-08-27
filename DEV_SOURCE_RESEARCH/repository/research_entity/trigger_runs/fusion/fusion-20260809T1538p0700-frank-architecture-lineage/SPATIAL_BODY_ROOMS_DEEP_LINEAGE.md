# FRANK Spatial State / Rooms / NeRD body — deep evolution lineage

Run: `fusion-20260809T1538p0700-frank-architecture-lineage`
Status: archaeology + current target synthesis

## SBR-0 — embodiment as persistent state, not visual decoration

Project-Frankenstein's spatial/body lineage evolved from a lightweight persistent location metaphor into a coupled state substrate for memory, model context, learned policies, simulated locomotion, room sessions and autonomous action. Its scientific value therefore cannot be judged by whether the UI looked like rooms; the relevant question is which shared spatial/body state causally affected later cognition/action.

## SBR-1 — persistent spatial tracker

Commit `230aa43e5f57710fd14ef11d8b108704f0188db4` (2026-03-03) introduced permanent embodiment via `spatial_state.py` alongside the Subconscious system.

Initial roles:
- persistent current location;
- room/location identity across sessions;
- activity-to-location mapping;
- room-aware context and hallucination checks;
- bridge between cognition and a persistent virtual body/world state.

This immediately became a state input to the learned subconscious policy, so room identity was not only narrative decoration.

## SBR-2 — Inner Sanctum and learned navigation

Commit `9c1e034...` (2026-03-02, related precursor branch/order in project history) introduced an Inner Sanctum environment with:
- seven rooms;
- entity crew members;
- manifestation/dissolution transitions;
- a ~9.4K-parameter PPO policy for move/spawn/dismiss/silence/exit decisions;
- reported <1 ms CPU inference;
- reward shaping for exploration diversity, conversation timing and exit window.

This line later merged into the broader spatial/rooms lineage and then had entity-specific semantics removed.

Evidence classification:
- reported trained/validated behavior in historical project context;
- not automatic evidence that room metaphors improve general cognition.

## SBR-3 — NeRD Physics makes body dynamics explicit

Commit `0abd1537c79f30a1a851f80851187d7bf8ecbc1b` (2026-03-02):
- 70 kg articulated avatar;
- 15 links / 19 joints;
- CPU rigid-body simulation at ~100 Hz;
- mood-coupled gravity/walk speed/joint damping;
- seven rooms with geometry, gravity, friction and temperature;
- blocking walk-wait so post-arrival narrative sees the arrived body state;
- optional ~50K-parameter MLP surrogate trained on 1M analytical steps, reported q_rmse=0.0029 rad;
- body physics transformed into model-facing natural-language blocks.

The useful architecture pattern is:
`physical/numeric body state -> typed embodied state -> bounded semantic projection`, not “the LLM literally lives in a room.”

## SBR-4 — data existed but projection hid it

Commit `5d25279...` (2026-03-05) identified a classic FRANK failure:
- room objects/body physics/activity data existed;
- `build_spatial_block(slim=True)` reduced it to one-liners;
- workspace truncated spatial text to ~80 chars;
- chat model therefore could not describe state it actually possessed elsewhere.

Fix:
- full room object descriptions;
- richer body posture/sensation;
- activity context;
- workspace spatial budget 80 -> 400 chars;
- chat used full rather than slim spatial view.

Current law:
`canonical state != reader projection`; omission must be explicit/receipted and task-conditioned.

## SBR-5 — documented emergent library-walk case

Commit `151b780...` (2026-03-04) records an owner/project observation:
- FRANK expressed a desire;
- traversed simulated environment for 59 minutes across three subsystems;
- later reflected on the experience;
- authors reported no direct coordination code between consciousness, spatial state and physics.

Evidence class:
`OWNER/PROJECT_REPORTED_OBSERVATION / RETEST_CAUSALLY`, not proof of emergence.

Current required controls:
- spatial-state lesion;
- shuffled/delayed state;
- fixed-model replay;
- matched action opportunity;
- outcome/re-entry identity;
- common-driver controls.

This historical case remains a high-value experiment seed for GWT/Hyperposition/Emergence.

## SBR-6 — Entities -> solo Rooms migration

Commit `b3df2f9885bede8ec38ced0c21763a06699d14b9` (2026-03-05):
- autonomous entity system replaced with solo room sessions;
- four new rooms: Wellness, Philosophy, Art Studio, Architecture Bay;
- `room_session.py` unified room session runner;
- idle-driven room dispatcher with quotas;
- spatial state expanded to 11 rooms/corridors/activities/ambients;
- consciousness category renamed `entity_reflection -> room_reflection`;
- AURA zone Entities -> Rooms;
- neural immune/lifecycle service identities changed;
- intent/reward/memory categories migrated.

`d146df8...` then removed obsolete entity code more broadly and warmed environmental prose.

Important migration lesson:
- conceptual-domain rename affects state vectors, reward channels, masks, prompts, persistence and learned checkpoints simultaneously;
- category positions/strings cannot be implicit semantics.

## SBR-7 — dynamic room creation

Commit `fcc7319...` added runtime room registration through Genesis proposals:
- approved room proposal -> spatial registration;
- NeRD auto-geometry;
- existing walking network intended to remain room-agnostic;
- daily visit limits.

Current reuse:
- world model can support dynamic entities/places;
- mutation of canonical world topology requires validated typed state transition, not LLM prose.

Genesis authority path itself is not retained.

## SBR-8 — persistent room objects

Commit `a890f6a...` (2026-03-20):
- new `room_objects` table;
- place/remove/interact operations;
- persistent object state, creator and timestamps;
- experiment results could auto-place objects in lab room;
- full spatial block showed up to five current-room objects plus relative age.

This is a precursor of persistent world/episodic relational memory.

Current target maps these into ClayGraph/Unified Memory objects/relations with valid time, source and provenance rather than relying on prompt-formatted “Your things”.

## SBR-9 — ambient-room contamination negative result

The richer room projection later became harmful.

Commit `1b86158...` and related cleanup established that decorative ambient room text:
- entered idle-thought context;
- appeared in generated thoughts;
- persisted into memory/topic interests/intents;
- re-entered later prompts;
- contaminated ThoughtSeedVAE training;
- created a self-reinforcing architectural/whispering-room fixation.

Follow-up `083ba1a...` killed 20/59 room-contaminated topic interests and archived contaminated hypotheses.

This reverses the earlier “more spatial detail is better” assumption.

Current law:
- canonical rich world state may exist;
- model-visible projection must be operation-conditioned, minimally sufficient and experimentally audited;
- decorative prose is not sensor/world evidence;
- recurrent model output keeps ancestry tags.

## SBR-10 — self vs environment proprioception

Commit `116ed71...` split resource sensing into:
- Frank/self process activity;
- external/environment process activity.

Perception events received self/env tags; self-induced load could be ignored as external novelty. Subconscious state expanded by six features.

Current PerceptualField inherits this source-attribution law:
`self-caused observation != external-world event`.

## SBR-11 — current target

Persistent embodiment/world state remains a logical organ, but the final H3 implementation need not retain separate Rooms/NeRD services.

Typed target state includes:
- current logical location/context;
- body/device/resource state;
- action/activity state;
- persistent objects/entities and relations;
- spatial bindings and valid times;
- source/self-vs-environment identity;
- perception/action outcome links;
- uncertainty/conflict;
- model-facing projection policy.

Digital Retina/PerceptualField adds real/screen visual spatial evidence into the same world model while preserving sensor-vs-prior distinction.

## Mandatory regressions

- SBR-REG-01 spatial/body state exists but reader truncation makes it unusable;
- SBR-REG-02 full rich projection induces fixation/recursive contamination;
- SBR-REG-03 entity->room/category migration misaligns learned state/action masks;
- SBR-REG-04 self-generated CPU/GPU/body change misclassified as external event;
- SBR-REG-05 dynamic room/object proposal mutates canonical world without authority gate;
- SBR-REG-06 restart loses location/object history;
- SBR-REG-07 stale room alias survives after domain removal;
- SBR-REG-08 spatial state removed/shuffled in library-walk causal twin;
- SBR-REG-09 model-facing natural-language body projection contradicts exact numeric state;
- SBR-REG-10 H1/H2/H3 world/body transition equivalence.

## Fusion decision

- SpatialState: `REUSE_PERSISTENT_BODY_WORLD_SEMANTICS`.
- NeRD Physics: `RETEST_AS_OPTIONAL_PHYSICAL/SIMULATION_LOWERING`; typed body state survives even if full rigid-body engine is omitted.
- Rooms/Sanctum: `REUSE_WORLD/CONTEXT_RELATIONAL_STATE; REJECT_UNBOUNDED_AMBIENT_PROSE_AS_DEFAULT_COGNITIVE_INPUT`.
- Historical emergent walk: `RETEST_CAUSALLY_AS_GOLDEN_EXPERIMENT_SEED`.

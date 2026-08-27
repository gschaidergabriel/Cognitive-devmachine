# External Research Manifest — Dissolved Perception / Sensor-In-Module

Run: `q12-20260809T0554p0700-dissolved-perception`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Date: 2026-08-09  
Purpose: test the owner hypothesis that Digital Retina can dissolve into FRANK's state dynamics, including sensor ingress inside the one-module runtime, while perception is jointly constrained by sensory evidence, world model, memory, goals and recurrent processing.

## Evidence classes

### Peer-reviewed / primary or primary-adjacent evidence

1. Kang et al. (2026), **Recurrent connections facilitate occluded object recognition by explaining-away**, Nature Communications.  
   https://www.nature.com/articles/s41467-026-68806-5  
   Relevance: recurrent networks produced a distinct explaining-away computation and improved difficult occluded recognition; supports testing recurrent perceptual settling rather than pure feedforward recognition.  
   Limit: does not prove FRANK architecture or world-model integration.

2. Rajaei et al. (2019), **Beyond core object recognition: Recurrent processes account for object recognition under occlusion**.  
   https://pmc.ncbi.nlm.nih.gov/articles/PMC6538196/  
   Relevance: MEG, behavior and recurrent computational models jointly support recurrent processing under occlusion.  
   Limit: biological timing/architecture is not a software prescription.

3. Ernst et al. (2021), **Recurrent processing improves occluded object recognition and gives rise to perceptual hysteresis**.  
   https://pmc.ncbi.nlm.nih.gov/articles/PMC8684313/  
   Relevance: recurrence can shift internal representations and focus processing on informative regions; also exposes hysteresis as a concrete failure/test dimension.

4. Kok et al. (2017), **Prior expectations induce prestimulus sensory templates**.  
   https://pmc.ncbi.nlm.nih.gov/articles/PMC5625909/  
   Relevance: expectations can preactivate stimulus-like sensory representations; supports testing world-model conditioned perception rather than only post-hoc semantic fusion.

5. Flounders et al. / related ECoG work (2021), **Long-term priors influence visual perception through recruitment of long-range feedback**.  
   https://pmc.ncbi.nlm.nih.gov/articles/PMC8560909/  
   Relevance: direct recordings showed stronger top-down flow for prior-congruent percepts and stronger feedforward flow for prior-incongruent percepts; a predictive-coding/attractor model reproduced key findings.  
   Limit: priors can bias perception; this is both support and a safety warning.

6. Richter et al. (2025), **Rapid computation of high-level visual surprise**.  
   https://pmc.ncbi.nlm.nih.gov/articles/PMC12719766/  
   Relevance: high-level rather than only low-level visual surprise modulated responses around ~200 ms; supports high-level prediction-error/salience as a candidate trigger for workspace escalation.

7. Gehrig & Scaramuzza (2024), **Low-latency automotive vision with event cameras**, Nature.  
   https://www.nature.com/articles/s41586-024-07409-w  
   Relevance: asynchronous intensity-change sensing reduces bandwidth/latency and supports a change-driven fast path.  
   Limit: event sensing alone sacrifices information needed for static/slowly varying content; hybrid anchor evidence remains necessary.

8. Hughes et al. (2024), **Foundations of Spatial Perception for Robotics: Hierarchical Representations and Real-time Systems** / Hydra lineage.  
   https://arxiv.org/abs/2305.07154  
   Relevance: persistent, hierarchical scene representations can be incrementally constructed from sensor data and prior knowledge in real time; supports keeping perception connected to a persistent world representation rather than reconstructing a full scene independently each frame.  
   Limit: scene graphs are not FRANK/Clay and do not establish distributed cognitive-state dissolution.

9. Rosinol et al. (2021), **Kimera: from SLAM to Spatial Perception with 3D Dynamic Scene Graphs**.  
   https://arxiv.org/abs/2101.06894  
   Relevance: dynamic scene graphs combine geometry, semantics, objects and temporal relations in a persistent representation.  
   Limit: robotics mapping, not a cognitive/GWT architecture.

### Implementation evidence

10. MIT-SPARK/Hydra — real-time 3D scene graph construction from sensor data.  
    https://github.com/MIT-SPARK/Hydra  
    Source class: external implementation/prior-art analogue.  
    Relevance: demonstrates practical incremental persistent perception/world-state integration.

11. ros-event-camera organization.  
    https://github.com/ros-event-camera  
    Source class: external implementation ecosystem.  
    Relevance: shows event-camera device streams can be exposed as low-level event messages/codecs/drivers; useful physical-ingress analogue, not a semantic architecture.

### Community/implementation anecdotes — non-promotional evidence only

12. Reddit / r/computervision and event-camera discussions.  
    Example: https://www.reddit.com/r/computervision/comments/zwobnj/  
    Relevance: practitioners emphasize end-to-end capture/buffer/transport latency and practical expense/complexity of event cameras.  
    Evidence status: anecdotal implementation context only.

## Counterevidence / failure-mode evidence

- Predictive-processing literature contains evidence that perceptual priors can dominate or distort sensory evidence under some conditions; therefore top-down coupling must carry explicit precision/uncertainty and must support `UNKNOWN` rather than forced recognition.
- Event cameras do not replace full image evidence for slowly varying/static semantics; change-driven operation must be hybrid, not dogmatically event-only.
- Recurrent processing can produce hysteresis; persistence of an earlier interpretation is a measurable failure mode.
- Existing dynamic scene-graph systems preserve modular perception and mapping stages; they are prior art for persistent semantic world state but do not establish that dissolving the module boundary is automatically superior.

## Novelty boundary

The searched evidence supports individual ingredients: recurrent perception, prior-driven feedback, event/change sensing, persistent semantic scene representations and integrated state. It does **not** establish a world-first claim for FRANK's proposed combination. Novelty remains `OPEN_PRIOR_ART_SEARCH_INCOMPLETE`.

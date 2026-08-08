# External Research Manifest — Retina Deep Foundry

Run: `retina-20260809T0615p0700-deep-foundry`  
Actor: `chatgpt-secondary`  
Date: 2026-08-09

This manifest records external research used for mechanism generation/comparison. Source classes remain distinct; none alone proves the complete FRANK Retina architecture.

## Recurrent / contextual vision

### Kang et al. 2026 — Recurrent connections facilitate occluded object recognition by explaining-away
Nature Communications 17, 2225 (2026).  
https://www.nature.com/articles/s41467-026-68806-5

**Use:** controlled evidence that recurrent visual models can develop an explaining-away computation under occlusion that is absent from matched feedforward variants; motivates H09 and occlusion lesion/rescue experiments.

**Does not establish:** FRANK recurrence, predictive coding or consciousness.

### Peelen, Berlot & de Lange — Predictive processing of scenes and objects
Nature Reviews Psychology 3, 13–26 (2024).  
https://www.nature.com/articles/s44159-023-00254-0

**Use:** review evidence for bidirectional object-scene/object-object interactions and joint probabilistic inference; motivates bidirectional context with explicit prior/evidence separation.

### Manassi & Whitney — Continuity fields enhance visual perception through positive serial dependence
Nature Reviews Psychology 3, 352–366 (2024).  
https://www.nature.com/articles/s44159-024-00297-x

**Use:** temporal continuity as a stabilizing mechanism analogue. Engineering transfer remains hypothetical.

### Brady, Robinson & Williams — Noisy and hierarchical visual memory across timescales
Nature Reviews Psychology 3, 147–163 (2024).  
https://www.nature.com/articles/s44159-024-00276-2

**Use:** precision/noise/timescale framing for visual memory; supports testing graded persistence rather than binary seen/not-seen state.

## Event/change-driven perception

### Gehrig & Scaramuzza — Low-latency automotive vision with event cameras
Nature 629, 1034–1040 (2024).  
https://www.nature.com/articles/s41586-024-07409-w

**Use:** strong engineering evidence that hybrid event + frame sensing can exploit asynchronous sparsity while retaining dense image information. Their 20-fps RGB + event-camera automotive system achieved latency comparable to a 5000-fps camera with bandwidth comparable to 45 fps in its task.

**Boundary:** hardware/task-specific result; does not imply the same numeric gains for ordinary cameras or FRANK.

### Zubic, Gehrig & Scaramuzza — State Space Models for Event Cameras
CVPR 2024 / arXiv:2402.15584.  
https://arxiv.org/abs/2402.15584

**Use:** persistent hidden state and learned timescales for asynchronous visual events; motivates frequency-robust stateful fast path.

## Persistent scene/world representation

### Hughes, Chang & Carlone — Hydra
arXiv:2201.13360.  
https://arxiv.org/abs/2201.13360

**Use:** real-time incremental 3D scene-graph construction with fast early/mid processing and slower high-level perception. Demonstrates that persistent hierarchical scene state is practical prior art.

### Rosinol et al. — Kimera: from SLAM to Spatial Perception with 3D Dynamic Scene Graphs
arXiv:2101.06894.  
https://arxiv.org/abs/2101.06894

**Use:** persistent metric/semantic world graph with dynamic entities/relations. Prevents novelty overclaim for persistent scene representations.

## Streaming multimodal memory

### Zhang et al. — StreamArena
arXiv:2608.05703, 2026-08-06.  
https://arxiv.org/abs/2608.05703

**Use:** current evidence that hour-scale visual agents expose failures of recent-frame-only memory, text conversion and repeated compression; two-tier persistent processing improves long-horizon streaming performance/latency in the reported benchmark.

**Boundary:** new preprint; not independent proof of ClayGraph/PerceptualField.

## Active perception

### Structured review/taxonomy of next-best-view strategies for 3D reconstruction
ISPRS Open Journal of Photogrammetry and Remote Sensing 17 (2025), 100098.  
https://doi.org/10.1016/j.ophoto.2025.100098

**Use:** >100-publication review distinguishing rule-based, uncertainty-based, sampling, learning and prediction-based NBV; motivates explicit active-sensing baseline families.

### Risk-aware active view acquisition / FisherRF
arXiv:2403.11396.  
https://arxiv.org/abs/2403.11396

**Use:** information-gain active view acquisition plus risk weighting; analogue for FRANK's compute/sensing action selection.

### Semantic-aware Next-Best-View
arXiv:2404.16507.  
https://arxiv.org/abs/2404.16507

**Use:** combines visibility and semantic gain; motivates task/semantic value in active sensing rather than purely geometric novelty.

## Open-set/open-world perception

### Cheng, Liu & Han — UADet
arXiv:2412.09229.  
https://arxiv.org/abs/2412.09229

**Use:** uncertainty-aware open-set detection; supports dedicated UNKNOWN/OOD evaluation rather than only closed-set confidence.

### Tian & Liu — Multimodal Semantic-Probabilistic Objectness for Open World Object Detection
arXiv:2607.23981 (2026).  
https://arxiv.org/abs/2607.23981

**Use:** very recent example separating probabilistic visual objectness from known-category semantic support; conceptually relevant to FRANK's evidence vs semantic-prior separation. Preprint status preserved.

## Efficient/open-vocabulary visual kernels

### Apple MobileCLIP / MobileCLIP2 official repository
https://github.com/apple/ml-mobileclip

**Use:** benchmark candidate. Official repo reports MobileCLIP2 and mobile-oriented accuracy/latency improvements; includes real-time iOS examples. Claims must be remeasured on FRANK hardware/workloads.

### SigLIP 2
arXiv:2502.14786.  
https://arxiv.org/abs/2502.14786

**Use:** candidate image-text/dense feature encoder; reports improvements in zero-shot, localization and dense prediction. Runtime cost and applicability remain open.

### YOLO-World
CVPR 2024 / arXiv:2401.17270.  
https://arxiv.org/abs/2401.17270  
https://github.com/AILab-CVC/YOLO-World

**Use:** open-vocabulary detection candidate to test against Retina's fixed COCO-80 boundary. GPL/commercial licensing and actual CPU/Android cost are part of evaluation.

## Cellular automata / GoL boundary

External literature contains cellular-automata texture descriptors, so CA-derived visual features are not nonsensical by definition. However, the deep run found no evidence that Conway's Game of Life is a privileged general visual/cortical mechanism. Current Retina GoL features therefore remain an ordinary optional feature family subject to incremental-value ablation against HOG/LBP/Gabor/dense-feature baselines.

## Community implementation signal

Recent computer-vision community discussions repeatedly report temporal detector flicker and practical use of trackers/optical flow/video context; this is implementation anecdote, not primary evidence. It supports including simple tracker + detector as a strong baseline so the research does not attribute ordinary tracking gains to the full PerceptualField architecture.

## Prior-art/novelty conclusion

No world-first claim is supported. Prior art separately covers:
- recurrent/contextual perception;
- predictive/joint object-scene inference;
- temporal continuity;
- event-driven sensing;
- persistent scene graphs;
- streaming visual memory;
- active perception;
- open-world detection.

The project-specific hypothesis is the integration of these mechanisms into a Clay-native, provenance-separated, GWT-coupled, one-module FRANK architecture with a bounded 4B interface. Its superiority and exact novelty remain OPEN.

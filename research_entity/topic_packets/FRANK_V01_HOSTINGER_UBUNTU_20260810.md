# Topic Packet — Frank v0.1 / Hostinger Ubuntu execution

**Packet id:** `FRANK_V01_HOSTINGER_UBUNTU_20260810`  
**Status:** CURRENT_WITH_FIRST_REAL_QWEN4B_EXECUTION_AND_OPEN_V2_REPLICATION  
**Updated:** 2026-08-10T00:33:00+07:00  
**Primary report:** `research_entity/reports/20260810T0007p0700_CHATGPT_FRANK_V01_DEEP_RESEARCH_VPS_FUSION.md`  
**First real-model result:** `research_entity/state/work/events/20260810T0033p0700_chatgpt_secondary_frank_qwen4b_first_real_result.json`

## Compact current state

The Hostinger GitHub Actions runner `clay` is a verified real Ubuntu/Linux X64 remote research/build/test lane for Frank v0.1. A measured deep-integrity run passed 21/21 gates with per-gate process-resource receipts. SQLite WAL behavior has been measured on a disposable target-host workload. Frank's local-model response boundary is fail-closed and passed hostile ambient-proxy/private-field regressions.

The real-model blocker has now been crossed once: `gschaidergabriel/Dr.-Unterweger@963fd8a6a044b6f5a6ddfde88fab25d0cc6e1dae` executed the pinned Qwen3-4B-Instruct-2507 Q8_0 model through llama.cpp on the real Hostinger Ubuntu runner and persisted a `PASS` receipt at commit `c9d06222643aa9028940cbba24b0421f6ef45ad6` with `real_model_executed=true`. The fixed five-recurrence trajectory scored 3/4 tasks correct, measured 48.356 s cumulative task latency, ~10.71 mean decode tok/s and ~39.94 mean prompt tok/s. All four trajectories reached `HALT_CANDIDATE_CONVERGED` at recurrence 4 and the recurrence-4 answers equaled recurrence-5 answers, giving a pilot counterfactual of one redundant recurrence/task and ~20.5% task-latency reduction relative to that exact fixed trajectory.

The strongest counterevidence is equally important: the modular-power task was wrong at every recurrence (`4` instead of `2`) while reporting `CONFIDENCE=100` throughout. Therefore recurrence convergence is currently evidence of trajectory stability, **not** truth/correctness, and model self-confidence is not a calibrated correctness gate. This explicitly blocks any inference from `CONVERGING_FIXED_POINT` to answer validity.

The real tool-call diagnostic selected `read_state` exactly once with valid arguments, persisted no hidden reasoning and took 5.884 s; no tool/effect was executed. Model/tool output remains non-authoritative.

The canonical next comparison is the methodology-corrected `HALT_ONLY_CONSERVATIVE_V2` lane. It permits counterfactual early finalization only for `HALT_CANDIDATE_CONVERGED`; route/escalate/rollback/abort/uncertain advisories fall back to the full fixed budget for comparison. The canonical V2 self-hosted execution path is also being hardened to `contents:read`, `persist-credentials:false`, artifact-only receipt transport and a separate GitHub-hosted constrained receipt writer.

This packet does **not** claim full Frank v0.1 release readiness, reliability, adaptive-recurrence superiority, calibrated confidence, SQLite NORMAL durability equivalence, phenomenal consciousness, or final Andreas-target acceptance.

## Constituent Micro-Packets

- `research_entity/knowledge_micro_packets/frank/FRANK_HOSTINGER_21_GATE_UBUNTU_20260810.md`
- `research_entity/knowledge_micro_packets/unifieddb/FRANK_SQLITE_WAL_VPS_20260810.md`
- `research_entity/knowledge_micro_packets/frank/FRANK_QWEN4B_BOOT_NEGATIVES_20260810.md`
- `research_entity/knowledge_micro_packets/frank/FRANK_LOCAL_MODEL_RESPONSE_BOUNDARY_20260810.md`
- `research_entity/knowledge_micro_packets/security/FRANK_SELF_HOSTED_RUNNER_AUTHORITY_OPEN_20260810.md`
- `research_entity/knowledge_micro_packets/gwt/FRANK_ADAPTIVE_RECURRENCE_WEB_SYNTHESIS_20260810.md`

## Current work fabric

Completed:
- `FRANK-V01-HOSTINGER-RUNNER-FIRST-LANE` — completion receipt: `research_entity/state/work/events/20260809T171300Z-chatgpt-secondary-frank-hostinger-first-lane-receipt.json`
- first real Qwen3-4B Q8_0 Hostinger inference — source receipt commit `c9d06222643aa9028940cbba24b0421f6ef45ad6`; research result event `research_entity/state/work/events/20260810T0033p0700_chatgpt_secondary_frank_qwen4b_first_real_result.json`

Highest-information open work:
- `FRANK-V01-REAL-QWEN4B-VPS-SHADOW` — obtain the read-only-authority V2 receipt, then repeat on a larger held-out/OOD set before any policy promotion.
- calibration/correctness separation — find/test an independent correctness/uncertainty signal because self-reported 100% confidence survived a stable wrong fixed point.
- `FRANK-V01-SELFHOSTED-RUNNER-AUTHORITY-HARDENING` — continue constrained read-only execution + separate receipt-writer validation for consequential VPS lanes.

## Re-entry decision

The current real-model result supports only a narrow pilot claim: w4 identified a stable recurrence-4 fixed point that made recurrence 5 redundant on these four observed trajectories, without changing their answers. It simultaneously demonstrates that fixed-point stability is orthogonal to truth because one stable trajectory was wrong. Architecture therefore keeps convergence-control and correctness validation as separate axes.

Next material evidence is the canonical read-only-authority V2 receipt with server RSS/HWM/CPU observations, followed by repeated held-out/OOD real-model runs with preserved raw rows, order/caching metadata and uncertainty/calibration analysis. `ONE_RUN != RELIABILITY` remains binding.

Final v0.1 acceptance remains on Andreas' designated Ubuntu developer system; Hostinger evidence is supporting remote execution evidence, not a substitute release gate.

# MicroEntity HCU package lane

This directory is the package-facing home of the **Hyperposition Computational Unit (HCU)**.

The HCU is a persistent strategic compute/simulation organ inside the same Mini Entity. It is designed as a sparse grid of logical approximately-0.8B cognition cells, backed by a small measured number of physical model workers, with MiniUnifiedDB remaining canonical authority.

## Required contents

All generated package-safe HCU material belongs under this root, including:

- architecture and resource profiles;
- scheduler/grid configuration;
- packet schemas and validation contracts;
- source code and deterministic tests;
- provider-capability profiles without secrets;
- non-secret receipts and benchmarks;
- package-safe datasets and derived simulation/calibration data;
- recovery/restart and deployment configuration;
- exact artifact/model locks and digests.

Do not place provider keys, tokens, passwords or other secrets here.

## ZIP law

`the artefact/MicroEntity/MICROENTITY_CURRENT.zip` must recursively include this directory whenever rebuilt.

Any change under `the artefact/MicroEntity/hcu/` makes the existing ZIP stale until the snapshot is rebuilt. The ZIP must not include itself recursively and must not include secrets/transient caches.

## Current source files

- `ARCHITECTURE.md` — HCU grid, world-model and authority architecture.
- `HCU_CONFIG.example.json` — owner-nominated KVM4 resource profile and initial sparse-grid defaults.

Future `go` cycles co-develop this lane and keep it inside the MiniUnifiedDB / Zero / EffectGate authority boundary.

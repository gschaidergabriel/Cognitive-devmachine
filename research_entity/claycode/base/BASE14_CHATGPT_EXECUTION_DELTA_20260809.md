# ClayCode BASE14 — ChatGPT execution delta — 2026-08-09

Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: RAE revision 2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## User goal

Close all fourteen ClayCode BASE blockers using every currently available capability, without weakening production/Ubuntu acceptance or the external execution-authority boundary.

## Formal gate state at end of this delta

- `CC-WP-01-SPEC-FREEZE`: PASS through the already-authoritative concurrent `BASE_SEMANTIC_FREEZE_V1.json`.
- `CC-WP-02..CC-WP-14`: remain formally OPEN in `CLAYCODE_RELEASE_WORKSPACE.json` until their exact acceptance receipts exist.
- `CLAYCODE_RELEASE_GATE`: NOT_PASS.
- `GENERAL_PURPOSE_GATE`: NOT_PASS.
- Required Ubuntu application classes credited in the release workspace: 0/10.

This conservative state is intentional. Hosted CI, containers and proxy apps are useful regression evidence but are not Andreas-target acceptance.

## Concrete production delta

1. Added a baseline-vs-repair full-corpus grammar differential and wired repaired frontend gates to strict/full-corpus/canonical identity checks.
2. Followed the live parser line from V4/V5 to V6/V7 instead of freezing a stale repair candidate.
3. Found and fixed a real WP03 identity bug: typed `program_semantic_id` included source/provenance hashes, so whitespace-equivalent programs could not converge to one semantic identity. Source/provenance now remains outside the typed semantic hash domain.
4. Preserved the concurrent authoritative WP01 freeze and explicitly superseded the duplicate local freeze attempt rather than double-crediting it.
5. Steered the autonomous ClayCode lane toward production typed IR/effect/runtime work rather than repeated parser-only research.
6. Current repo now contains integrated pure compiler/evaluator/C11 differential, transitive effect/capability analysis, sealed Linux runtime bridge, package linking, hardened runtime/ABI/FFI, fuzz/conformance, heldout corpus generation and real FRANK packet/ActiveAssembly-score handoff slices. These are implementation evidence, not automatic package PASS.
7. Added/fused fail-closed Andreas Ubuntu target convergence runners. The strict LALR diagnostic receipt is inspected semantically because its diagnostic process can exit 0 even when strict construction fails.
8. Added a local owner-target registration/fingerprint gate using Linux machine-id plus stable host facts. It is explicitly operational evidence, not hardware attestation.
9. Added canonical target entrypoint `tools/claycode_run_andreas_target_acceptance.py`: it verifies the local registered Andreas host first and only then invokes the full target convergence gate.
10. Added append-only `WORK_REVISE` for `WORK-CLAYCODE-BASE14-CLOSE-20260809`, binding the build organ to the registered target entrypoint and current V7 line.

## Hard external boundary reached

This ChatGPT session has GitHub read/write and hosted execution/CI orchestration, but no direct shell attached to Andreas' physical Ubuntu developer system. Therefore it cannot truthfully manufacture the required target receipts in-session. The remaining physical execution step is deliberately fail-closed and has been reduced to one registered target entrypoint.

One-time registration on the actual target host:

```bash
python tools/claycode_target_host_identity.py register --acknowledge ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM
```

Then the target battery:

```bash
python tools/claycode_run_andreas_target_acceptance.py
```

A green component battery still does **not** auto-promote BASE. WP10 requires real non-proxy application receipts, WP13 requires full frozen FRANK handoff beyond score/packet slices, and WP14 requires the final general-purpose manifest plus zero unresolved P0/P1 defects.

## Decision trace

Evidence outranked schedule pressure. Alternatives rejected:

- marking all 14 PASS from hosted Ubuntu CI;
- counting the ten-class proxy suite as real application acceptance;
- treating a parser diagnostic exit code as strict-parser success;
- allowing a generic Ubuntu environment variable to impersonate the owner target;
- allowing a concurrent duplicate WP01 freeze to receive extra completion credit.

Next falsifier / closure evidence: receipts produced on the registered Andreas Ubuntu host and the real WP10/WP13/WP14 production artifacts required by the existing BASE14 burn-down.

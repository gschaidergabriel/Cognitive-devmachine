# Loop-core slice L0 — behavioral value of provenance-bound re-entry under lesion controls

Date: 2026-08-11 15:02 +07:00
Origin actor: `claude-code` / Anthropic / Claude Fable 5 — external reviewer/contributor session, not a booted Clay organ
Identity: `EXTERNAL_CONTRIBUTOR_NOT_A_BOOTED_CLAY_ORGAN`
Target: `self.root` / Frank v0.1 (sandbox evidence lane; NOT executed on the accepted target VPS)
Work packages: `F-V01-03` (loop core), `F-V01-05` (GWT/re-entry controls), `F-V01-11` (memory/reward)
Status: `EXECUTED_LOCAL_SANDBOX / NO_PROMOTION_REQUESTED / NO_TARGET_REPO_MUTATION`
Predecessors: `20260811T1339p0700_CLAUDE_EXTERNAL_AUDIT_TARGET_VPS_RECEIPT_INTEGRITY.md`,
`20260811T1405p0700_CLAYCODE_FIRST_EXECUTABLE_SUBSTRATE_AND_MEASURED_ROADMAP.md`
Complement: `runtime/frank_loop_core_v1/loop_core_slice.py` (branch `loop-core/causal-slice-v1`)

## 1. What this measures, and what the parallel slice does not

The parallel loop-core slice proves **fail-closed integrity**: broken arms are *refused* at
identifiable links. L0 measures the complement: all arms are *allowed to run*, and the measured
quantity is the **downstream behavioral value** of truthful provenance-bound outcome re-entry —
the open falsifier of `H-G3-003` / the sandbox precursor of `C-OPEN-001`. Additionally, the
decision is made by the ClayCode evaluator over READ_ONLY host intrinsics (`pure=False`), i.e. a
state-dependent ClayCode decision, not only pure authority.

## 2. Design

Lesion logic: identical seeds, environment and policy in every arm; only the outcome→state
binding is manipulated. Policy `decide_step` in `loop_policy.clay` (FRANK_STRUCTURED_V1 subset),
executed via `runtime/claycode_eval_v1` with READ_ONLY intrinsics bound to a per-run SQLite
receipt store. Nonstationary 4-action environment (good action 90 % / others 10 %, hard switch at
cycle 30), 60 cycles per run.

Arms: `TRUTHFUL` (receipts validly bound), `SHUFFLED` (same data volume, misattributed),
`NO_REENTRY` (nothing written back), `TRUTHFUL_SABOTAGED` (correct data, provenance hash broken).

## 3. Results (30 seeds, seeds 1–30)

| arm | mean success rate | sd |
|---|---|---|
| TRUTHFUL | **0.601** | 0.267 |
| SHUFFLED | 0.275 | 0.217 |
| NO_REENTRY | 0.275 | 0.217 |
| TRUTHFUL_SABOTAGED | 0.275 | 0.217 |

- Δ(TRUTHFUL − NO_REENTRY) = **+0.326** mean (sd 0.229, range 0.0…0.767).
- 29/30 seeds win, 1 tie, **0 inversions**; exact one-sided sign test p ≈ 2.9e-8.
- The three broken arms are **bitwise identical on all 30 seeds**.
- Checks (computed booleans, not assert-then-True): C1 admit ok / refused when unbound;
  C2 gain ≥ 0.15 (actual 0.40 on the 3-seed pilot, 0.326 over 30 seeds); C3 |SHUFFLED−NONE| < 0.10;
  C4 sabotage degrades fully; C5 `pure=True` refuses `decide_step`. All five green, and the gate
  can go red (sabotage collapses the gain).

## 4. Interpretation — exactly what is falsified

1. The counter-hypothesis of `H-G3-003` ("re-entry is correlated decoration") is falsified **in
   this sandbox regime**: downstream behavior changes causally when only the information path is
   lesioned.
2. Sharper: the causal carrier is **binding validity, not data volume**. SHUFFLED writes the same
   amount (misattributed); SABOTAGED writes the *correct* data with a broken provenance hash;
   both collapse exactly onto NO_REENTRY. A receipt without validatable binding is worth zero,
   not "somewhat less".
3. Consistent with `N-G3-004`: not the occurrence of re-entry carries the gain but its validated
   information content.

## 5. Negative findings (filed in NEGATIVE_RESULTS)

- **Recovery metric artifact**: `recovery_cycles_to_0.8` reads 1 cycle for TRUTHFUL because the
  rolling-10 window still contains pre-switch successes immediately after the switch. Specification
  error; the honest adaptation-cost signal is the pre/post rate difference (0.724 → 0.486 over 30
  seeds). The recovery number must not be quoted.
- **Lesion-type null discriminator**: because the thin policy falls back to a fixed first action
  when no valid evidence exists, all three lesion types are informationally equivalent to "no
  data" and bitwise identical. This design cannot distinguish "misinformation actively harms"
  from "no information". Seed 16 additionally shows an unforgiving one-sample evidence rule can
  waste the information path entirely (truthful = inert there). Follow-up L1 (forced exploration
  + forgiving evidence window) is running.

## 6. Scope limits

- Local sandbox execution (session scratchpad venv, lark 1.3.1, Python 3.12.3), **not** the
  accepted target VPS; no target-lane evidence claimed.
- Policy deliberately thin; success-ratio aggregates computed in host intrinsics, not in ClayCode.
- No GWT workspace involved; nothing claimed about `C-OPEN-001` live.
- Artifacts: `loopcore_l0/{loop_policy.clay, loop_driver.py, RESULT.json, RESULT_ROBUST.json,
  RESULT.md, robust.py}` in the session scratchpad (outside both repos), 12 + 120 SQLite runs.
- Frank repo untouched; no push, no merge, no promotion requested. Disposition belongs to Clay.

## 7. Addendum 15:0x +07:00 — target-VPS reproduction (E-LOOPCORE-L0-002)

The full 30-seed matrix was re-executed on the accepted target VPS (`digital-retina`), in a
disposable `/tmp` copy, against the **runner checkout's own evaluator**
(`runtime/claycode_eval_v1` @ `847e96f74`, Python 3.12.3, lark 1.3.1 in a disposable venv).
Result is **bit-identical** to the sandbox run: delta_mean 0.326, 29/30 wins, 1 tie (seed 16),
0 inversions, p ≈ 2.9e-8, broken arms bitwise identical. Artifact:
`loopcore_l0/RESULT_ROBUST_VPS.json`. The scope limit "not target lane" in §6 is hereby closed
for the robustness matrix. Residual: the disposable dir `/tmp/l0_vps.xKGQ` remains on the VPS —
remote deletion is blocked by the owner guard (Schranke); cleanup needs an owner terminal or the
next reboot. No canonical database touched, no external effect, runner working tree unmodified.

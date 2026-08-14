# Loop-core L1/L2 — misinformation cost, sabotage equivalence, and one structural-null lesson

Date: 2026-08-11 15:16 +07:00
Origin actor: `claude-code` / Anthropic / Claude Fable 5 (coordination) + Claude Sonnet 5 (execution) — external contributor sessions, not booted Clay organs
Identity: `EXTERNAL_CONTRIBUTOR_NOT_A_BOOTED_CLAY_ORGAN`
Target: `self.root` / Frank v0.1 — sandbox lane, checks reproduced on the accepted target VPS
Work packages: `F-V01-03`, `F-V01-05`, `F-V01-09`, `F-V01-11`
Status: `EXECUTED_LOCAL_AND_TARGET_VPS / NO_PROMOTION_REQUESTED / NO_TARGET_REPO_MUTATION`
Predecessor: `20260811T1502p0700_LOOPCORE_L0_REENTRY_LESION_BEHAVIORAL_VALUE.md` (N-LOOPCORE-L0-002)

## 1. Question

L0 left one cell of the lesion matrix unmeasured: is misattributed feedback (SHUFFLED) actively
*worse* than no feedback (NO_REENTRY), or merely equally worthless? In L0 all three broken arms
collapsed to bitwise-identical behavior, so the question was undecidable by design.

## 2. L1 — a structural null, filed as a negative result

L1 added forced exploration (rotation in the EXPLORE fallback) and a forgiving evidence rule
(≥2 samples within a 20-cycle window before an action can be condemned). **D2 failed: the broken
arms stayed bitwise identical.** Mechanism, isolated rather than assumed: the fixed-priority
policy checks A0 first; with no own-bucket samples A0 stays permissive forever; therefore no
broken arm ever reaches the point where rotation or the window engage. The forgiveness rule
*reinforces* the A0 lock (permissive under data scarcity). Second specification error by the
experiment author; filed as `N-LOOPCORE-L1-001`.

Two useful side results: D1 held (TRUTHFUL 62.5 % ± 6.4 vs 27.5 % ± 21.7), and the forgiving
window collapsed truthful-arm variance from ±26.7 pp (L0) to ±6.4 pp — the seed-16 lockout class
is eliminated (29/30 seeds recover).

## 3. L2 — one change, the matrix separates

Single design change: a rotating focus action (`cycle % 4`) is tried first, then the fixed order,
then focus-as-explore. Evidence now lands in every arm on every action; misattribution can act.

Result (30 seeds × 60 cycles, switch at 30):

| arm | mean success | sd |
|---|---|---|
| TRUTHFUL | **0.581** | 0.050 |
| NO_REENTRY | 0.296 | 0.045 |
| TRUTHFUL_SABOTAGED | 0.296 | 0.045 (bitwise = NO_REENTRY) |
| SHUFFLED | **0.247** | 0.175 |

- **D3 misinformation cost = +4.9 pp (NONE − SHUFFLED), sign test p = 0.016, 30/30 seeds nonzero.**
  Mechanism: shuffled evidence produces hard lock-in (e.g. 54/60 cycles on one action) onto
  whatever the misattribution makes look good.
- **D4 sabotage delta = 0.0 exactly, on every seed.** Hash-broken receipts fail validation on
  every row for every action regardless of the selection rule — provably equivalent to zero
  information under *any* policy, not just the L0/L1 one.
- D1 unchanged (truthful gain +28.5 pp), D2 finally True, C1/C5 hold.

## 4. Interpretation — the complete lesion ordering

`TRUTHFUL (0.581)  >  NO_REENTRY ≡ SABOTAGED (0.296)  >  SHUFFLED (0.247)`

1. Valid provenance-bound feedback is worth +28.5 pp; misattributed feedback is worth **−4.9 pp
   relative to nothing**; invalidly-bound feedback is worth exactly nothing.
2. Architectural consequence, and the reason this belongs to `F-V01-09` as well as `F-V01-03/05`:
   **fail-closed provenance validation converts the worst case from misinformation into
   no-information.** SABOTAGED ≡ NONE *because* validation rejects broken bindings; SHUFFLED is
   what a loop looks like *without* that validation. The V17-style DB-enforced binding is thus
   not only an integrity property — it is behaviorally load-bearing: it caps the damage of any
   corrupted re-entry channel at zero, never negative.
3. Consistent with and sharpening `C-LOOPCORE-L0-001` (binding validity is the causal carrier).

## 5. Target-VPS reproduction

The full L2 matrix was re-executed on `digital-retina` in the existing disposable `/tmp` copy
(`/tmp/l0_vps.xKGQ`, evaluator from the runner checkout @ `847e96f74`, Python 3.12.3,
lark 1.3.1). The checks dict is **bit-identical** to the sandbox run, including
D3 = 0.0488888888888889 and p = 0.016124801710247993. Artifact:
`loopcore_l2/RESULT_L2_VPS.json`. The disposable dir still awaits owner-side cleanup (remote
deletion remains blocked by the Schranke guard, correctly).

## 6. Scope limits

- Sandbox task/environment; nothing claimed about live FRANK (`C-OPEN-001` stays open) or GWT.
- The rotating-focus and modulo logic live in host intrinsics because the FRANK_STRUCTURED_V1
  subset has no arithmetic; selection *structure* is ClayCode, selection *inputs* are host-side.
- Host intrinsic names are repurposed under their literal declared names
  (e.g. `attempt_execution_generation_matches` bound as is-focus) because the evaluator resolves
  targets against the real `HOST_CONTRACTS` dict. In this testbed the contract names therefore do
  not describe the bound semantics — acceptable for a lesion sandbox, but it is exactly the
  name-vs-semantics gap of audit finding A2; a production binding must not do this.
- D3 is modest (+4.9 pp) with high SHUFFLED variance (±17.5 pp); the sign test (30/30 seeds,
  p = 0.016) carries the claim, not the mean alone.
- Artifacts: `loopcore_l1/{RESULT_L1.json,RESULT_L1.md}`, `loopcore_l2/{RESULT_L2.json,
  RESULT_L2.md, RESULT_L2_VPS.json}` in the session scratchpad. Frank repo untouched in all runs.

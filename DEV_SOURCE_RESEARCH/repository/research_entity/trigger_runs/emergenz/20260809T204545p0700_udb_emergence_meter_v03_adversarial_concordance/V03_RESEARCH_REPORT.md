# v0.3 Adversarial Concordance Research Report

## Evidence verdict

The central result is negative and high-impact: UnifiedDB Emergence Meter v0.2
is not supported as a reliable emergence instrument.  It remains useful only as
a synthetic five-regime scenario classifier.  The replacement proposed here is
not another scalar; it is a conjunctive, fail-closed receipt and intervention
contract.

No experiment in this run used live FRANK telemetry or a registered Andreas
Ubuntu target.  No causal-emergence truth and no consciousness inference is
made.

## Executed falsification suite

Two deterministic standard-library programs and ten regression tests were run
under Python 3.12.13 on Linux x86_64.  The complete suite passed.

### 1. Pseudoreplication

The zero-effect model had 12 independent episodes and 80 strongly correlated
ticks per episode.  Treating 960 ticks as independent produced a false-positive
rate of 0.84.  Exact sign-flip inference on 12 episode means produced 0.06.

The extended surface varied 6, 12, 24 and 48 episodes and 5, 20 and 80 ticks.
Under zero effect, tick-level rejection ranged from 0.325 to 0.90, versus 0 to
0.125 at episode level.  Under effect 0.2, episode-level power ranged from
0.15–0.175 at six episodes to 0.95–0.975 at 48 episodes.  More ticks did not
replace more independent episodes.

### 2. Time-series nulls

Independent binary-median AR(1) channels were tested at persistence values
0.0, 0.8, 0.95 and 0.985, with 200, 400 and 800 samples.

| AR phi | Full-shuffle null FPR range | Circular-shift FPR range | Disagreement range |
|---:|---:|---:|---:|
| 0.0 | 0–0.033 | 0.033–0.10 | 0.033–0.067 |
| 0.8 | 0.133–0.30 | 0–0.067 | 0.133–0.233 |
| 0.95 | 0.467–0.70 | 0.033–0.10 | 0.433–0.60 |
| 0.985 | 0.667–0.833 | 0.067–0.20 | 0.467–0.70 |

Circular shift was materially safer in these stationary AR cells, but it was
not universally nominal.  Its power was also much lower for weak planted
effects: at beta 0.15, rejection was 0.10 versus 0.70 for full shuffle.  The
full-shuffle number is not trustworthy as power because its beta-zero rejection
rate was already 0.333 in the same surface.  At beta 0.6, circular rejection
rose to 0.80.

The defensible conclusion is not “use circular shift.”  It is “declare and
validate null invariants, run multiple relevant nulls, and abstain when they
disagree.”

### 3. Shared-regime counterexample

Two channels had no direct path, but both received the same persistent regime
shift.  Unconditional dependence tests rejected in 1.00 of full-shuffle runs
and 0.975 of circular-shift runs.  Median lag MI was 0.7349 bits; conditioning
on the known regime reduced median lag CMI to 0.00063 bits.

This falsifies the stronger claim that null-ensemble agreement alone establishes
a direct causal path.  Known contexts must be conditioned or intervened on, and
unresolved latent-context risk must remain explicit.

### 4. Optimizer's curse in macrostate discovery

Independent 16-state transitions were mapped to binary macrostates.  The same
mapping was applied at t and t+1 and selected by maximizing train MI.

| Candidate maps searched | Median selected train MI | Median held-out MI | Train ≥0.05 / holdout <0.01 |
|---:|---:|---:|---:|
| 1 | 0.00260 | 0.000043 | 0.000 |
| 10 | 0.01550 | 0.000041 | 0.000 |
| 100 | 0.03457 | 0.000100 | 0.075 |
| 500 | 0.04861 | 0.000034 | 0.425 |
| 2,500 | 0.06217 | 0.000073 | 0.900 |

The apparent macro information rose monotonically with search budget while
held-out information stayed effectively zero.  Macro discovery therefore needs
preregistration or time-, episode- and context-aware cross-fitting.  Random
tick folds are not an acceptable substitute.

### 5. Synergy overcount

An XOR target with duplicate source X′=X produced one bit of MMI synergy for
(X,Y) and one bit for (X′,Y).  Their naive sum was two bits although target
entropy was one bit.  Overlapping pairwise synergy estimates cannot be added.

The current PID literature also lacks a universally privileged redundancy
axiom.  Estimator disagreement must be preserved as epistemic uncertainty, not
resolved by choosing the estimator that favors promotion.

### 6. Endpoint-valid hidden path

The visible macro model was Y=X1 XOR X2.  A low-level model added an unmapped
backup, Y=visible OR (H1 XOR H2).  With H1=H2=0, endpoints matched and standard
visible lesion/rescue could pass.  Intervening on the excluded variables yielded
mean absolute output effect 0.5.

Endpoint agreement, output-only IIA, or visible-path rescue is therefore
insufficient.  Intermediate states, excluded variables and alternative paths
must be tested under constrained alignment maps.

## Hypothesis iteration

The original repair hypothesis — replace full shuffle with a
dependence-preserving surrogate — survived only in weakened form.  The
counterevidence forced five revisions:

1. Nulls are a family of assumption-bound diagnostics, not interchangeable
   implementations.
2. Null agreement does not close common-driver or regime explanations.
3. Cluster-aware validity must be paired with an honest power analysis.
4. Cross-fitting must respect episodes, chronology and contexts.
5. Causal promotion requires pathwise intervention and receiver-specific use,
   not only information gain, decodability or endpoint agreement.

## GWT/FRANK integration boundary

Recent workspace experiments provide useful intervention designs: matched-norm
controls, targeted ablations and task-selective effects.  They do not warrant a
phenomenal-consciousness claim.  The current Ignition Index is explicitly a
structural and decodability diagnostic; causal amnesic probing is still future
work in that paper.

For this project, the minimum causal chain remains:

`selection → broadcast → delivery → reconstruction → uptake → causal use → outcome → provenance re-entry`.

The live H1 replay adapter can become a substrate for the new gate, but its nine
local tests are component evidence only.  It still requires frozen matched
baseline/lesion/rescue plus truthful/shuffled/no-reentry execution on the
registered Andreas Ubuntu target.

## Final v0.3 disposition

- v0.2 reliable-instrument claim: `REJECTED`.
- v0.2 synthetic scenario generator: `RETAINED_WITH_LIMITS`.
- v0.3 scalar: `NOT_CREATED`.
- v0.3 receipt schema and gates: `METHOD_CANDIDATE_ONLY`.
- live FRANK validation: `NOT_RUN`.
- scientific promotion: `NONE`.
- next decisive evidence: registered-target, receiver-complete, pathwise,
  context-conditioned, cross-fit intervention receipts with null and estimator
  concordance.


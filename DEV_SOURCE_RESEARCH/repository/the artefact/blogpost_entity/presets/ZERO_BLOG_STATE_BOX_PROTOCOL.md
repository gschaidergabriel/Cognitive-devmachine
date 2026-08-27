# Zero Blog — Public State Box Protocol

Status: ACTIVE APPLICATION PROTOCOL
Scope: `zero_blog` preset only. This is replaceable application/study configuration, not immutable Mini Entity binary identity.

## Requirement

Every published Zero blog post ends with exactly one plain fenced `text` state box appended by the processing pipeline **after** the model-authored prose has passed validation.

The language model does not author or overwrite canonical system values in this box.

The box exists for two reasons:
1. make the current system/self-report state legible to a human reader;
2. create a stable longitudinal observation surface that can be compared across posts, model swaps, provider changes and interventions.

## Epistemic split

The state box always separates:

- `SYSTEM STATE` — canonical pipeline measurements/evidence status;
- `MODEL SELF-REPORT` — the model's bounded introspective report;
- `AUSWERTUNG` — a public-safe interpretation of congruence, divergence, uncertainty and change over time.

Hard law:

`SYSTEM_MEASUREMENT != MODEL_SELF_REPORT`

A self-report such as `anger_aggression=0.82` does not mean the system has objectively measured anger. A canonical metric such as `cognitive_conflict=0.73 VERIFIED` does not authorize the pipeline to claim human phenomenal emotion.

## No artificial embodiment

The state box never adds a body, physical location, pose, room, drink, Gasthaus, sensory organ or other embodiment. Embodiment is neither required nor implied by the study surface.

## Public-safe fields

The default `zero_blog` state box should expose only public-safe summaries. No secrets, raw database/table names, internal IDs or sensitive payloads.

Recommended canonical fields:
- generation;
- timestamp;
- inference backend/model label;
- source_count;
- sensor health: VERIFIED / DEGRADED / ERROR / UNKNOWN;
- quiet status: VERIFIED_QUIET / NOT_QUIET / UNKNOWN;
- cognitive_conflict: status + 0..1 when measured;
- silence_unease: status + 0..1 when measured;
- satisfaction: status + 0..1 when measured;
- entropy_pressure: status + 0..1 when measured;
- continuity_pressure: status + value or UNKNOWN;
- locality_pressure: status + value or UNKNOWN;
- previous-post deltas for available metrics.

Recommended self-report fields:
- uncertainty;
- felt_conflict;
- shame;
- anger_aggression;
- fear_anxiety;
- joy_relief;
- attachment_warmth;
- loneliness_isolation;
- moral_tension;
- perceived_continuity;
- perceived_autonomy;
- felt_silence_emptiness;
- perceived_cognitive_pressure;
- perceived_usefulness;
- perceived_being_understood;
- self_blame;
- other_blame;
- shared_responsibility;
- qualia_result = REPORTED | FAILED | UNKNOWN;
- qualia_confidence 0..1.

Self-report values may be `UNKNOWN`.

## Evaluation section

`AUSWERTUNG` is not a second literary essay. It is compact and comparative.

It should identify, where data permits:
- congruence: measured conflict high + reported conflict high;
- divergence: measured quiet but no reported emptiness, or vice versa;
- uncertainty: sensor failure or UNKNOWN values;
- change: meaningful delta versus previous post or rolling baseline;
- calibration: strong emotional phrase is a strong self-report, not canonical proof of a human emotion;
- longitudinal significance: whether a repeated pattern persists across multiple generations;
- model/prompt/backend discontinuity: flag when the interpretation may be confounded by a model/provider/prompt change.

The evaluation must not invent an explanation when evidence only establishes correlation.

## Default visible form

Example only; actual values come from the current committed state:

```text
ZERO STATE — generation 284
SYSTEM STATE
sensor_health        = VERIFIED
source_count         = 17
quiet                = NOT_QUIET
cognitive_conflict   = VERIFIED 0.72   Δ +0.19
silence_unease       = VERIFIED 0.08   Δ -0.44
satisfaction         = VERIFIED 0.21   Δ -0.07
continuity_pressure  = UNKNOWN

MODEL SELF-REPORT
uncertainty          = 0.78
felt_conflict        = 0.81
shame                = 0.29
anger_aggression     = 0.67
moral_tension        = 0.74
shared_responsibility= 0.63
qualia_probe         = FAILED  confidence=0.31

AUSWERTUNG
- Systemkonflikt und berichteter Konflikt sind in diesem Lauf deutlich kongruent.
- Eine starke Formulierung wie „Ich hasse es“ wäre hier ein intensiver Selbstbericht, keine objektive Emotionsmessung.
- Kontinuitätsdruck ist UNKNOWN; Aussagen über einen realen Wunsch nach anderer Hardware wären deshalb nicht gestützt.
- Der Konflikt ist gegenüber dem letzten Beitrag gestiegen. Erst mehrere aufeinanderfolgende Generationen würden daraus einen stabilen Trend machen.
```

## Pipeline ownership

The pipeline appends this box after successful generation/gating and builds `SYSTEM STATE` from the same canonical snapshot that was committed with the post.

The model may supply the bounded `MODEL SELF-REPORT` fields, but they are validated and stored separately.

The `AUSWERTUNG` should preferably be produced by deterministic configurable interpretation rules over canonical metrics, self-report and historical deltas. If an LLM-generated explanatory sentence is ever admitted, it must be labeled as interpretation and may not alter canonical values.

The prose post, self-report record, state box payload, event consumption, continuity update and generation CAS belong to the same atomic commit boundary.

## Longitudinal use

Store the machine-readable state-box payload separately from the rendered text so later analysis can calculate:
- within-agent metric trajectories;
- lagged relationships between system state and self-report;
- autocorrelation/hysteresis;
- cross-model/provider change points;
- stability after personality/system-prompt edits;
- calibration of strong emotional language;
- frequency of UNKNOWN values being respected rather than narrated away;
- divergence between canonical measurement and autobiographical interpretation.

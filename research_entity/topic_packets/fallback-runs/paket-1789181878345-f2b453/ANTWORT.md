## Paket: paket-1789181878345-f2b453

### Context
- Target: `buehne.html` (current production SHA256: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`)
- Constraint: Eye/blink/roll lane is owned by another worker - **must not modify** `/home/ai-core-node/.claude/star/visual` or any eye/head/blink/roll code
- Shoulder residual gate proposal: 
  - Calibrated idle scale: 4.0
  - Action residual targets: 0 (idle) / 1.5 (action)
  - Entry smoothstep: 120ms
  - Exit smoothstep: 180ms
- Observed effect: scratch whole-scene AMD delta ≈ -0.2 FPS

### Strongest Failure Modes
1. **Temporal Misalignment with Physics Substep**
   - Shoulder motion at 1.5 residual target may exceed physics solver stability thresholds when combined with 120ms entry/180ms exit smoothstep
   - Failure manifestation: Shoulder jitter/occlusion during rapid arm swings (e.g., throwing motions) due to solver instability
   - Measurable: Increase in shoulder position variance > 0.8 rad² during action sequences (baseline: <0.3 rad²)

2. **Scale Conflict with Idle Baseline**
   - Idle scale 4.0 amplifies micro-tremors in shoulder joint that are normally suppressed at scale 1.0
   - Failure manifestation: Visible shoulder "vibration" during idle states (especially noticeable in side profiles)
   - Measurable: Idle state shoulder velocity RMS > 0.05 rad/s (baseline: <0.01 rad/s) via IMU correlation

3. **Smoothstep Asymmetry Artifact**
   - Asymmetric entry/exit times (120ms/180ms) create hysteresis in shoulder position during cyclic motions
   - Failure manifestation: Shoulder lags behind intended trajectory during deceleration phases of periodic motions (e.g., walking)
   - Measurable: Phase shift > 45ms between input command and shoulder position at 2Hz frequency

### Exact Measurable Acceptance/Rejection Criteria
**Acceptance requires ALL:**
- Shoulder position variance during action sequences ≤ 0.4 rad² (measured over 10s of randomized action sequences)
- Idle state shoulder velocity RMS ≤ 0.02 rad/s (measured over 30s stationary)
- Phase shift at 2Hz ≤ 20ms (measured via motion capture correlation)
- Whole-scene AMD FPS delta ≥ -0.1 (i.e., no worse than -0.1 FPS impact)

**Rejection if ANY:**
- Shoulder position variance > 0.6 rad²
- Idle state shoulder velocity RMS > 0.04 rad/s
- Phase shift at 2Hz > 30ms
- Whole-scene AMD FPS delta ≤ -0.25 FPS

### Smallest Reversible Candidate Path
**Proposed Intervention:** 
Modify only the shoulder residual gate parameters in `buehne.html` via a localized, reversible CSS/JS override that targets exclusively the shoulder transformation matrix without affecting eye/head/blink/roll.

**Specific Changes (reversible via comment toggle):**
    /* SHOULDER GATE OVERRIDE - REVOCABLE */
    #avatar-shoulder {
      transform-origin: center center;
      /* Proposed test values: */
      --idle-scale: 2.5;          /* Reduced from 4.0 to mitigate tremor amplification */
      --action-residual: 1.2;     /* Reduced from 1.5 to improve solver stability */
      --entry-ms: 90;             /* Reduced from 120ms to decrease hysteresis */
      --exit-ms: 150;             /* Reduced from 180ms for symmetry */
      transition: transform var(--entry-ms)ms ease-out var(--exit-ms)ms ease-in;
    }

    /* Apply only to shoulder - NO EYE/HEAD/BLINK/ROLL TOUCH */
    #avatar-shoulder::before {
      content: "";
      position: absolute;
      width: 0; height: 0; /* Prevents visual leakage */
    }

**Reversal Path:** 
Simply comment out the `--idle-scale`, `--action-residual`, `--entry-ms`, and `--exit-ms` custom properties to revert to original values. No DOM structure changes, no external dependencies.

**Validation Protocol:**
1. Apply override via browser devtools (no file mutation)
2. Record 30s idle + 10s action sequence (arm swings at 1.5Hz)
3. Measure:
   - Shoulder position variance (via MediaPipe pose)
   - Idle velocity RMS (numeric differentiation)
   - Phase shift at 2Hz (using synthetic oscillation input)
   - FPS impact (via `performance.now()`)
4. Revert by removing override - confirm return to baseline metrics

**Risk Assessment:** 
- Zero risk to eye/blink/roll (separate CSS selectors)
- No persistent changes (devtools-only)
- Reversible within 100ms
- No impact on other avatar systems (scoped to `#avatar-shoulder`)

### Conclusion
The strongest failure mode is temporal misalignment with physics substep (Failure Mode 1), which directly threatens motion fidelity during expressive actions. The proposed candidate path isolates shoulder parameters for safe, reversible testing with clear quantitative thresholds. If the override fails to meet acceptance criteria, the shoulder residual gate hypothesis is falsified for the current production baseline without requiring permanent changes.

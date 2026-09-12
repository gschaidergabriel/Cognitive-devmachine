#!/usr/bin/env python3
"""Interval-sampled successor to shadow runtime v3.

V3 proved transport decoupling but its recursive setTimeout sampler produced only
two records on this page. A causal diagnostic showed setInterval continues to
run while the same page is active, so v4 changes only the in-page sampling
primitive and makes low rAF/sample counts reportable evidence instead of an
early harness abort. Product thresholds are not relaxed.
"""
from __future__ import annotations

from pathlib import Path

BASE = Path(__file__).with_name("validate_shadow_blink_runtime_v3.py")
src = BASE.read_text(encoding="utf-8")

old_sampler = r'''  function sample() {
    const now = performance.now();
    R.samples.push({
      ms: now-R.startedPerf,
      special: _sonderLaeuft,
      phase: blinzelPhase,
      blinkOpacity: getComputedStyle(blink).opacity,
      blinkSrc: blink.src,
      glowOpacity: getComputedStyle(glow).opacity
    });
    if (now-R.startedPerf < 3200) setTimeout(sample, 8);
    else R.sampleDone = true;
  }
  sample();
  blinzeln(false);'''
new_sampler = r'''  function sample() {
    const now = performance.now();
    R.samples.push({
      ms: now-R.startedPerf,
      special: _sonderLaeuft,
      phase: blinzelPhase,
      blinkOpacity: getComputedStyle(blink).opacity,
      blinkSrc: blink.src,
      glowOpacity: getComputedStyle(glow).opacity
    });
  }
  sample();
  R.sampleInterval = setInterval(sample, 8);
  blinzeln(false);'''
if src.count(old_sampler) != 1:
    raise SystemExit(f"V3_SAMPLER_ANCHOR_DRIFT={src.count(old_sampler)}")
src = src.replace(old_sampler, new_sampler)

old_payload = '"return {samples:R.samples||[],raf:R.raf||[],rafDone:R.rafDone===true,"\n            "sampleDone:R.sampleDone===true,startSpecial:R.startSpecial===true,"'
new_payload = '"if(R.sampleInterval){clearInterval(R.sampleInterval);R.sampleInterval=null;}R.sampleDone=true;"\n            "return {samples:R.samples||[],raf:R.raf||[],rafDone:R.rafDone===true,"\n            "sampleDone:R.sampleDone===true,startSpecial:R.startSpecial===true,"'
if src.count(old_payload) != 1:
    raise SystemExit(f"V3_PAYLOAD_ANCHOR_DRIFT={src.count(old_payload)}")
src = src.replace(old_payload, new_payload)

old_early = '''        if not isinstance(samples, list) or len(samples) < 80:
            raise SystemExit(f"INSUFFICIENT_IN_PAGE_SAMPLES {len(samples) if isinstance(samples,list) else -1}")
        if not isinstance(raf, list) or len(raf) < 120:
            raise SystemExit(f"INSUFFICIENT_RAF_SAMPLES {len(raf) if isinstance(raf,list) else -1}")

        phases ='''
new_early = '''        if not isinstance(samples, list):
            samples = []
        if not isinstance(raf, list):
            raf = []

        phases ='''
if src.count(old_early) != 1:
    raise SystemExit(f"V3_EARLY_COUNT_ANCHOR_DRIFT={src.count(old_early)}")
src = src.replace(old_early, new_early)

old_metrics = '''        raf_values = [float(x) for x in raf]
        raf_sorted = sorted(raf_values)
        p95 = raf_sorted[int(0.95 * (len(raf_sorted) - 1))]
        fps = 1000.0 / (sum(raf_values) / len(raf_values))

        checks = {'''
new_metrics = '''        raf_values = [float(x) for x in raf]
        raf_sorted = sorted(raf_values)
        p95 = raf_sorted[int(0.95 * (len(raf_sorted) - 1))] if raf_sorted else float("inf")
        fps = (1000.0 / (sum(raf_values) / len(raf_values))) if raf_values and sum(raf_values) > 0 else 0.0

        checks = {'''
if src.count(old_metrics) != 1:
    raise SystemExit(f"V3_METRICS_ANCHOR_DRIFT={src.count(old_metrics)}")
src = src.replace(old_metrics, new_metrics)

old_checks = '''            "sample_window_completed": payload.get("sampleDone") is True,
            "closing_phase_observed": "halb1" in phases,'''
new_checks = '''            "sample_window_completed": payload.get("sampleDone") is True,
            "sample_count_ge_80": len(samples) >= 80,
            "raf_samples_ge_120": len(raf_values) >= 120,
            "closing_phase_observed": "halb1" in phases,'''
if src.count(old_checks) != 1:
    raise SystemExit(f"V3_CHECK_ANCHOR_DRIFT={src.count(old_checks)}")
src = src.replace(old_checks, new_checks)

old_max = '"fps": fps, "p95_ms": p95, "max_ms": max(raf_values)},'
new_max = '"fps": fps, "p95_ms": p95, "max_ms": max(raf_values) if raf_values else None},'
if src.count(old_max) != 1:
    raise SystemExit(f"V3_RAF_REPORT_ANCHOR_DRIFT={src.count(old_max)}")
src = src.replace(old_max, new_max)

src = src.replace('"GO_AVATAR_EYE_SHADOW_RUNTIME/v3"', '"GO_AVATAR_EYE_SHADOW_RUNTIME/v4"')
src = src.replace('"V3_IN_PAGE_AUTONOMOUS_SAMPLER"', '"V4_IN_PAGE_INTERVAL_SAMPLER"')
src = src.replace('EYE_SHADOW_RUNTIME_GATE_V3=PASS', 'EYE_SHADOW_RUNTIME_GATE_V4=PASS')
src = src.replace('SHADOW_RUNTIME_GATE_V3_FAIL', 'SHADOW_RUNTIME_GATE_V4_FAIL')

ns = {"__name__": "__main__", "__file__": str(BASE), "__package__": None}
exec(compile(src, str(BASE) + "#interval-sampler-v4", "exec"), ns, ns)

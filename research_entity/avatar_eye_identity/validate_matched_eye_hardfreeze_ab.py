#!/usr/bin/env python3
"""Hard-freeze successor for validate_matched_eye_ab.py.

The first real-browser matched A/B proved that Chrome virtual-time pause alone is
not a render freeze for this avatar: two nominally identical eye-OFF screenshots
changed across ~39% of the canvas.  This runner keeps the original exact-subject
and visual thresholds but instruments scheduling *before page scripts run*.

It tracks rAF/timeouts/intervals, reloads the shadow under that instrumentation,
then atomically cancels all tracked schedulers, pauses Web Animations and media,
and only then executes OFF -> ON -> OFF screenshots.  The live avatar source is
never written.
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "validate_matched_eye_ab.py"
src = BASE.read_text(encoding="utf-8")

anchor = '''        cdp.call("Runtime.enable")\n\n        # Do not constrain virtual time until the real shadow has finished'''
assert src.count(anchor) == 1, src.count(anchor)

bootstrap = r'''        cdp.call("Runtime.enable")

        # Instrument every scheduler before application scripts execute.  The
        # target has already loaded once, so register for the next document and
        # reload it.  This makes the freeze causal rather than heuristic.
        freeze_bootstrap = r"""
(()=>{
  if (window.__goFreezeInstrumentationInstalled) return;
  window.__goFreezeInstrumentationInstalled = true;
  const nativeRAF = window.requestAnimationFrame.bind(window);
  const nativeCAF = window.cancelAnimationFrame.bind(window);
  const nativeST = window.setTimeout.bind(window);
  const nativeCT = window.clearTimeout.bind(window);
  const nativeSI = window.setInterval.bind(window);
  const nativeCI = window.clearInterval.bind(window);
  const rafs = new Set(), timeouts = new Set(), intervals = new Set();
  let frozen = false;

  window.requestAnimationFrame = function(cb) {
    if (frozen) return 0;
    let id = 0;
    id = nativeRAF(function(ts) {
      rafs.delete(id);
      if (!frozen) cb(ts);
    });
    rafs.add(id);
    return id;
  };
  window.cancelAnimationFrame = function(id) {
    rafs.delete(id);
    return nativeCAF(id);
  };
  window.setTimeout = function(cb, ms, ...args) {
    if (frozen) return 0;
    let id = 0;
    id = nativeST(function(...inner) {
      timeouts.delete(id);
      if (!frozen) {
        if (typeof cb === 'function') cb(...inner);
        else (0,eval)(String(cb));
      }
    }, ms, ...args);
    timeouts.add(id);
    return id;
  };
  window.clearTimeout = function(id) {
    timeouts.delete(id);
    return nativeCT(id);
  };
  window.setInterval = function(cb, ms, ...args) {
    if (frozen) return 0;
    const id = nativeSI(function(...inner) {
      if (!frozen) {
        if (typeof cb === 'function') cb(...inner);
        else (0,eval)(String(cb));
      }
    }, ms, ...args);
    intervals.add(id);
    return id;
  };
  window.clearInterval = function(id) {
    intervals.delete(id);
    return nativeCI(id);
  };

  window.__goHardFreeze = function() {
    frozen = true;
    const before = {rafs:rafs.size, timeouts:timeouts.size, intervals:intervals.size};
    for (const id of Array.from(rafs)) nativeCAF(id);
    for (const id of Array.from(timeouts)) nativeCT(id);
    for (const id of Array.from(intervals)) nativeCI(id);
    rafs.clear(); timeouts.clear(); intervals.clear();
    let animations = 0, media = 0;
    try {
      for (const a of document.getAnimations({subtree:true})) {
        try { a.pause(); animations++; } catch (_) {}
      }
    } catch (_) {}
    for (const m of document.querySelectorAll('video,audio')) {
      try { m.pause(); media++; } catch (_) {}
    }
    const style = document.createElement('style');
    style.id = '__go-hard-freeze-style';
    style.textContent = '*{animation-play-state:paused!important;transition:none!important;caret-color:transparent!important}';
    document.documentElement.appendChild(style);
    return {before, animations_paused:animations, media_paused:media, frozen:true};
  };
})();
"""
        cdp.call("Page.addScriptToEvaluateOnNewDocument", {"source": freeze_bootstrap})
        cdp.call("Page.reload", {"ignoreCache": True})

        # Do not constrain virtual time until the real shadow has finished'''

src = src.replace(anchor, bootstrap)

old_freeze = '''        # Freeze only after runtime readiness and special-expression activation.\n        # From here onward the two screenshots differ only by canonical eye\n        # opacity/src, while timers/rAF stay pinned at the same visual state.\n        cdp.call("Emulation.setVirtualTimePolicy", {"policy": "pause"})\n        geometry = json.loads(cdp.eval('''
assert src.count(old_freeze) == 1, src.count(old_freeze)
new_freeze = '''        # Freeze the actual producer paths, not just Chrome's virtual clock.\n        freeze_state = json.loads(cdp.eval("JSON.stringify(window.__goHardFreeze())"))\n        time.sleep(0.15)\n        geometry = json.loads(cdp.eval('''
src = src.replace(old_freeze, new_freeze)

# Keep exact acceptance thresholds, but make the evidence schema/scope explicit.
src = src.replace('"GO_AVATAR_EYE_MATCHED_FROZEN_AB/v1"', '"GO_AVATAR_EYE_MATCHED_HARDFREEZE_AB/v2"')
src = src.replace(
    '"ISOLATED_REAL_BROWSER_VIRTUAL_TIME_FROZEN_NO_LIVE_SOURCE_WRITE"',
    '"ISOLATED_REAL_BROWSER_TRACKED_SCHEDULERS_HARD_FROZEN_NO_LIVE_SOURCE_WRITE"',
)

# Persist freeze accounting in the report without altering any acceptance limit.
needle = '            "geometry": geometry,\n            "eye_off_to_on": ab,'
assert src.count(needle) == 1, src.count(needle)
src = src.replace(needle, '            "geometry": geometry,\n            "hard_freeze": freeze_state,\n            "eye_off_to_on": ab,')

ns = {"__name__": "__main__", "__file__": str(BASE), "__package__": None}
exec(compile(src, str(BASE) + "#hardfreeze-v2", "exec"), ns, ns)

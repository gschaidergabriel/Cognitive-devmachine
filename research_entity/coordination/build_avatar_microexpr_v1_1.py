#!/usr/bin/env python3
"""Build the next idle-face candidate from the proven V1 source without touching live production."""
from pathlib import Path
import hashlib, re, sys
src=Path(__file__).with_name('avatar_microexpr_v1.js')
out=Path(__file__).with_name('avatar_microexpr_v1_1.generated.js')
s=src.read_text(encoding='utf-8')

def one(old,new,label):
    global s
    n=s.count(old)
    if n != 1:
        raise SystemExit(f'{label}: expected 1 anchor, got {n}')
    s=s.replace(old,new,1)

one('const FRANK_MICROEXPR_VERSION = "2026-09-12-v1";',
    'const FRANK_MICROEXPR_VERSION = "2026-09-12-v1.1-candidate";', 'version')
one('  recent: [],\n  lastMouthSrc: null,',
    '  recent: [],\n  familyLast: Object.create(null),\n  eventLog: [],\n  lastMouthSrc: null,', 'state')
one('  const positiv = /freu|happy|zufried|amused|confident|selbst|freund/.test(a);\n  const fokus = /fokus|konzent|denk|ponder|listen|aufmerk/.test(a);\n  const stress = /stress|aerger|ärger|frust|sorge|angespannt|krit/.test(a);',
'''  const positiv = a === "zugewandt_weich" || /freu|happy|zufried|amused|confident|selbst|freund/.test(a);
  const fokus = a === "wach_aufmerksam" || /fokus|konzent|denk|ponder|listen|aufmerk/.test(a);
  const stress = a === "angespannt" || /stress|aerger|ärger|frust|sorge|krit/.test(a);
  const exhausted = a === "erschoepft_schwer";
  const calm = a === "ruhig_neutral";
  const now = performance.now();
  const family = p.name.startsWith("tongue_") ? "tongue" : p.name.startsWith("nose_") ? "nose" : p.kind;
  const familyCooldown = family === "tongue" ? 12000 : family === "nose" ? 5200 : p.kind === "stress" ? 6200 : 3600;
  const familyAge = now - (_mikroMimik.familyLast[family] || -1e12);
  if(familyAge < familyCooldown) w *= Math.max(0.015, familyAge/familyCooldown*0.18);''', 'classification')
one('  if(p.kind === "play"){\n    w *= (positiv ? 1.8 : 0.75) * (s.present ? 1.25 : 0.72);\n    if(s.load > 0.72) w *= 0.18;\n  }',
'''  if(p.kind === "play"){
    w *= (positiv ? 1.8 : 0.62) * (s.present ? 1.22 : 0.62);
    if(s.load > 0.72 || exhausted) w *= 0.16;
    if(stress) w *= 0.24;
    if(p.name === "tongue_out") w *= s.near ? 0.42 : 0.72;
  }''', 'play')
one('  if(p.kind === "positive") w *= positiv ? 2.0 : (s.present ? 1.15 : 0.72);',
    '  if(p.kind === "positive") w *= positiv ? 2.15 : (s.present ? 1.10 : 0.68);\n  if(exhausted && (p.name === "lip_pout" || p.name === "jaw_set")) w *= 1.45;\n  if(calm && p.kind === "stress") w *= 0.62;', 'positive')
one('  if(s.near && p.kind === "stress" && !stress) w *= 0.55;',
'''  if(s.near && p.kind === "stress" && !stress) w *= 0.55;
  if(s.direction === "links" && (p.name.endsWith("_left") || p.name.endsWith("_l"))) w *= 1.18;
  if(s.direction === "rechts" && (p.name.endsWith("_right") || p.name.endsWith("_r"))) w *= 1.18;''', 'direction')
one('  _mikroMimik.count++;\n  window.__frankMicroexpr = window.__frankMicroexpr || {};',
'''  _mikroMimik.count++;
  const family = p.name.startsWith("tongue_") ? "tongue" : p.name.startsWith("nose_") ? "nose" : p.kind;
  _mikroMimik.familyLast[family] = t;
  _mikroMimik.eventLog.push({t, name:p.name, state:_mikroMimik.state.ausdruck, present:_mikroMimik.state.present, near:_mikroMimik.state.near});
  if(_mikroMimik.eventLog.length > 64) _mikroMimik.eventLog.shift();
  window.__frankMicroexpr = window.__frankMicroexpr || {};''', 'telemetry')
one('  let hazard=0.145;\n  hazard *= 0.72 + 0.34*_mikroClamp(s.activation,0,2.2);',
'''  const a=s.ausdruck||"";
  const exhausted=a === "erschoepft_schwer";
  const tense=a === "angespannt";
  const attentive=a === "wach_aufmerksam";
  const soft=a === "zugewandt_weich";
  let hazard=0.145;
  if(exhausted) hazard*=0.55;
  else if(tense) hazard*=1.10;
  else if(attentive || soft) hazard*=1.08;
  hazard *= 0.72 + 0.34*_mikroClamp(s.activation,0,2.2);''', 'hazard')
one('  state:_mikroMimik.state,\n  force:(name=null)=>_mikroStart(performance.now(),name)',
    '  state:_mikroMimik.state,\n  events:_mikroMimik.eventLog,\n  force:(name=null)=>_mikroStart(performance.now(),name)', 'api')

# Static invariants for the candidate.
for token in ['setInterval(', 'requestAnimationFrame(']:
    # V1 intentionally contains only a keydown debug listener in this payload; it must not add scheduling primitives.
    if token in s:
        raise SystemExit(f'candidate unexpectedly contains scheduling primitive {token}')
if s.count('FRANK_MICROEXPR_V1 BEGIN') != 1:
    raise SystemExit('marker invariant failed')
out.write_text(s,encoding='utf-8')
print('SOURCE_SHA='+hashlib.sha256(src.read_bytes()).hexdigest())
print('CANDIDATE_SHA='+hashlib.sha256(out.read_bytes()).hexdigest())
print('CANDIDATE_BYTES='+str(out.stat().st_size))
print('V1_1_BUILD_PASS')

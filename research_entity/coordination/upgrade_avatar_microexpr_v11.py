#!/usr/bin/env python3
"""CAS-bound in-place upgrade of the already-live FRANK_MICROEXPR v1 engine.

v1.1 keeps ONE animation authority: the existing buehne requestAnimationFrame loop.
It adds a soft masked local nose deformation, exact 01..06 state weighting,
telemetry history and removes keyboard-forced production gestures.
"""
from pathlib import Path
import hashlib, os, re, shutil, subprocess, tempfile

LIVE = Path('/home/ai-core-node/.claude/star/visual/buehne.html')
ROOT = LIVE.parent
EXPECTED = 'cfaefcd2719d7680d8b0a532aa6fae9c2920e022ab3626d18de073eb87a80cdb'

raw = LIVE.read_bytes()
pre = hashlib.sha256(raw).hexdigest()
print('PRE_SHA=' + pre)
if pre != EXPECTED:
    print('CAS_REFUSED expected=' + EXPECTED + ' actual=' + pre)
    raise SystemExit(42)
text = raw.decode('utf-8')

for marker in ['FRANK_MICROEXPR_V1 BEGIN', 'FRANK_MICROEXPR_V1 END',
               '_mikroMimikSchritt(t);', '_mikroMimikStateAktualisieren(b);']:
    if text.count(marker) != 1:
        print('SOURCE_SHAPE_REFUSED marker=' + repr(marker) + ' count=' + str(text.count(marker)))
        raise SystemExit(43)
if 'FRANK_MICROEXPR_V11 BEGIN' in text:
    print('ALREADY_V11')
    raise SystemExit(41)


def replace_once(old, new, code):
    global text
    n = text.count(old)
    if n != 1:
        print('REPLACE_REFUSED code=%s count=%s needle=%r' % (code, n, old[:120]))
        raise SystemExit(code)
    text = text.replace(old, new, 1)


def sub_once(pattern, replacement, code):
    global text
    text2, n = re.subn(pattern, lambda m: replacement, text, count=1, flags=re.S)
    if n != 1:
        print('REGEX_REFUSED code=%s count=%s pattern=%r' % (code, n, pattern[:120]))
        raise SystemExit(code)
    text = text2

replace_once('// === FRANK_MICROEXPR_V1 BEGIN ===', '// === FRANK_MICROEXPR_V11 BEGIN ===', 50)
replace_once('// === FRANK_MICROEXPR_V1 END ===', '// === FRANK_MICROEXPR_V11 END ===', 51)
replace_once('const FRANK_MICROEXPR_VERSION = "2026-09-12-v1";',
             'const FRANK_MICROEXPR_VERSION = "2026-09-12-v1.1";', 52)
replace_once('  mouth: null,\n  disabledReason: null\n};',
             '  mouth: null,\n  nose: null,\n  eventLog: [],\n  disabledReason: null\n};', 53)
replace_once('{name:"nose_scrunch_l", kind:"stress", frames:',
             '{name:"nose_scrunch_l", kind:"stress", nose:"scrunch_l", frames:', 54)
replace_once('{name:"nose_scrunch_r", kind:"stress", frames:',
             '{name:"nose_scrunch_r", kind:"stress", nose:"scrunch_r", frames:', 55)

nose_helpers = r'''
function _mikroStateKlasse(a){
  a=(a||"").toLowerCase();
  if(a.startsWith("01_") || /ruhig|neutral/.test(a)) return "neutral";
  if(a.startsWith("02_") || /wach|aufmerk|fokus|konzent/.test(a)) return "alert";
  if(a.startsWith("03_") || /angespannt|stress|frust|aerger|ärger|krit/.test(a)) return "tense";
  if(a.startsWith("04_") || /zugewandt|weich|freund|empat|warm/.test(a)) return "soft";
  if(a.startsWith("05_") || /erschoepft|erschöpft|schwer|muede|müde/.test(a)) return "tired";
  if(a.startsWith("06_") || /ueberrasch|überrasch|surpris/.test(a)) return "surprised";
  return "other";
}
function _mikroNase(){
  if(_mikroMimik.nose && _mikroMimik.nose.isConnected) return _mikroMimik.nose;
  const parent=document.getElementById("kopf-dreh");
  if(!parent) return null;
  let n=document.getElementById("mikro-nase-overlay");
  if(!n){
    n=document.createElement("img");
    n.id="mikro-nase-overlay";
    n.alt="";
    Object.assign(n.style,{
      position:"absolute", inset:"0", width:"100%", height:"100%",
      pointerEvents:"none", zIndex:"4", opacity:"0",
      transformOrigin:"50% 31.5%", willChange:"transform,opacity"
    });
    const mask="radial-gradient(ellipse 7.6% 6.2% at 50% 31.5%,#000 0%,#000 48%,rgba(0,0,0,.74) 68%,transparent 100%)";
    n.style.webkitMaskImage=mask;
    n.style.maskImage=mask;
    parent.appendChild(n);
  }
  _mikroMimik.nose=n;
  return n;
}
function _mikroNaseReset(){
  const n=_mikroMimik.nose;
  if(!n) return;
  n.style.opacity="0";
  n.style.transform="translate(0,0) scale(1)";
}
function _mikroNaseRender(a,env,u){
  if(!a || !a.p || !a.p.nose){ _mikroNaseReset(); return; }
  const n=_mikroNase();
  if(!n) return;
  const rolled=(typeof kopfRollAktiv!=="undefined" && !!kopfRollAktiv);
  const src=document.getElementById(rolled ? "kopf-schicht2" : "kopf-schicht");
  if(!src) { _mikroNaseReset(); return; }
  const wanted=src.currentSrc || src.src;
  if(wanted && n.src!==wanted) n.src=wanted;
  const dir=a.p.nose==="scrunch_l" ? -1 : 1;
  const pulse=0.88 + 0.12*Math.sin(Math.PI*_mikroClamp(u,0,1));
  const e=_mikroClamp(env*pulse,0,1);
  const dx=dir*0.42*e;
  const dy=-0.92*e;
  const sx=1+0.008*e;
  const sy=1-0.019*e;
  n.style.opacity=(0.82*e).toFixed(3);
  n.style.transform=`translate(${dx.toFixed(2)}px,${dy.toFixed(2)}px) scaleX(${sx.toFixed(4)}) scaleY(${sy.toFixed(4)})`;
}
'''
replace_once('function _mikroMimikStateAktualisieren(b){', nose_helpers + '\nfunction _mikroMimikStateAktualisieren(b){', 56)

new_weight = r'''function _mikroProfilGewicht(p){
  const s=_mikroMimik.state;
  let w=p.w;
  const a=s.ausdruck||"";
  const k=_mikroStateKlasse(a);
  const positiv=/freu|happy|zufried|amused|confident|selbst|freund|zugewandt|weich/.test(a);
  const fokus=/fokus|konzent|denk|ponder|listen|aufmerk|wach/.test(a);
  const stress=/stress|aerger|ärger|frust|sorge|angespannt|krit/.test(a);

  if(p.kind==="social") w*=s.present ? (s.near?1.65:1.35) : 0.88;
  if(p.kind==="play"){
    w*=(positiv?1.8:0.75)*(s.present?1.25:0.72);
    if(s.load>0.72) w*=0.18;
  }
  if(p.kind==="positive") w*=positiv?2.0:(s.present?1.15:0.72);
  if(p.kind==="ponder") w*=fokus?1.75:0.92;
  if(p.kind==="stress") w*=stress?1.9:(0.72+s.load*0.9);
  if(p.kind==="surprise") w*=0.25+s.surprise*6.0;

  // Exact production-state semantics. These values are the real buehne states,
  // not a parallel emotion model.
  if(k==="alert"){
    if(p.kind==="ponder") w*=1.30;
    if(p.kind==="social") w*=1.12;
    if(p.nose) w*=1.52;
  } else if(k==="tense"){
    if(p.kind==="stress") w*=2.30;
    if(p.kind==="play") w*=0.055;
    if(p.kind==="positive") w*=0.30;
    if(p.kind==="social") w*=0.72;
    if(p.nose) w*=1.45;
  } else if(k==="soft"){
    if(p.kind==="social") w*=1.62;
    if(p.kind==="positive") w*=1.85;
    if(p.kind==="play") w*=1.48;
    if(p.kind==="stress") w*=0.30;
  } else if(k==="tired"){
    if(p.kind==="ponder") w*=1.28;
    if(p.name==="lip_pout") w*=1.42;
    if(p.kind==="stress") w*=0.54;
    if(p.kind==="play") w*=0.045;
    if(p.kind==="social") w*=0.62;
  } else if(k==="surprised"){
    if(p.kind==="surprise") w*=4.8;
    if(p.nose) w*=1.38;
    if(p.kind==="play") w*=0.30;
  }

  if(s.near && p.kind==="stress" && !stress && k!=="tense") w*=0.55;
  const idx=_mikroMimik.recent.lastIndexOf(p.name);
  if(idx>=0) w*=idx===_mikroMimik.recent.length-1 ? 0.035 : 0.16;
  return Math.max(0,w);
}'''
sub_once(r'function _mikroProfilGewicht\(p\)\{.*?\n\}\nfunction _mikroProfilWaehlen',
         new_weight + '\nfunction _mikroProfilWaehlen', 57)

replace_once('/freu|happy|amused|confident|selbst/.test(s.ausdruck||"")',
             '/freu|happy|amused|confident|selbst|zugewandt|weich/.test(s.ausdruck||"")', 58)

replace_once('  _mikroMimik.count++;\n  window.__frankMicroexpr = window.__frankMicroexpr || {};\n  window.__frankMicroexpr.last = p.name;\n  window.__frankMicroexpr.count = _mikroMimik.count;',
'''  _mikroMimik.count++;
  const ev={t:Date.now(),name:p.name,state:_mikroMimik.state.ausdruck,activation:+_mikroMimik.state.activation.toFixed(3),present:_mikroMimik.state.present,near:_mikroMimik.state.near};
  _mikroMimik.eventLog.push(ev);
  if(_mikroMimik.eventLog.length>16) _mikroMimik.eventLog.shift();
  window.__frankMicroexpr = window.__frankMicroexpr || {};
  window.__frankMicroexpr.last = p.name;
  window.__frankMicroexpr.count = _mikroMimik.count;
  window.__frankMicroexpr.history = _mikroMimik.eventLog;''', 59)

replace_once('function _mikroAbortExternal(t){\n  _mikroMimik.active = null;',
             'function _mikroAbortExternal(t){\n  _mikroNaseReset();\n  _mikroMimik.active = null;', 60)
replace_once('  _mikroMimik.active=null;\n  _mikroMimik.nextAllowed=t + _mikroRnd(1200,4200);',
             '  _mikroNaseReset();\n  _mikroMimik.active=null;\n  _mikroMimik.nextAllowed=t + _mikroRnd(1200,4200);', 61)
replace_once('  const stage=Math.max(0, Math.min(a.peak, Math.round(env*a.peak)));',
             '  _mikroNaseRender(a,env,u);\n  const stage=Math.max(0, Math.min(a.peak, Math.round(env*a.peak)));', 62)

replace_once('  let hazard=0.145;\n  hazard *= 0.72 + 0.34*_mikroClamp(s.activation,0,2.2);',
'''  let hazard=0.158;
  hazard *= 0.72 + 0.34*_mikroClamp(s.activation,0,2.2);
  const sk=_mikroStateKlasse(s.ausdruck||"");
  if(sk==="alert") hazard*=1.12;
  else if(sk==="soft") hazard*=1.10;
  else if(sk==="tired") hazard*=0.64;
  else if(sk==="surprised") hazard*=1.28;
  if(s.load>0.88) hazard*=0.62;''', 63)

old_api = '''window.__frankMicroexpr = {
  version:FRANK_MICROEXPR_VERSION,
  count:0,
  last:null,
  state:_mikroMimik.state,
  force:(name=null)=>_mikroStart(performance.now(),name)
};
window.addEventListener("keydown", e=>{
  if(e.target && (e.target.tagName==="INPUT" || e.target.tagName==="TEXTAREA" || e.target.isContentEditable)) return;
  if(e.key==="m"){ e.preventDefault(); _mikroStart(performance.now(),"smirk_right"); }
  else if(e.key==="M"){ e.preventDefault(); _mikroStart(performance.now(),"tongue_out"); }
});'''
new_api = '''window.__frankMicroexpr = {
  version:FRANK_MICROEXPR_VERSION,
  count:0,
  last:null,
  history:_mikroMimik.eventLog,
  state:_mikroMimik.state,
  force:(name=null)=>_mikroStart(performance.now(),name),
  snapshot:()=>({version:FRANK_MICROEXPR_VERSION,count:_mikroMimik.count,last:(window.__frankMicroexpr&&window.__frankMicroexpr.last)||null,active:_mikroMimik.active?_mikroMimik.active.p.name:null,state:{..._mikroMimik.state},history:_mikroMimik.eventLog.slice()})
};'''
replace_once(old_api, new_api, 64)

if text.count('FRANK_MICROEXPR_V11 BEGIN') != 1 or text.count('FRANK_MICROEXPR_V11 END') != 1:
    print('V11_MARKER_COUNT_FAIL')
    raise SystemExit(65)
if text.count('FRANK_MICROEXPR_V1 BEGIN') or text.count('FRANK_MICROEXPR_V1 END'):
    print('OLD_MARKER_REMAINS')
    raise SystemExit(66)
if 'addEventListener("keydown"' in text[text.index('FRANK_MICROEXPR_V11 BEGIN'):text.index('FRANK_MICROEXPR_V11 END')]:
    print('KEYBOARD_TRIGGER_REMAINS')
    raise SystemExit(67)

# Syntax-check every inline script before replacing a production byte.
parts=[]
for m in re.finditer(r'<script([^>]*)>(.*?)</script>', text, re.I|re.S):
    if 'src=' not in m.group(1).lower(): parts.append(m.group(2))
fd,tmpjs=tempfile.mkstemp(prefix='buehne-microexpr-v11-',suffix='.js')
os.close(fd)
Path(tmpjs).write_text('\n;\n'.join(parts),encoding='utf-8')
try:
    cp=subprocess.run(['node','--check',tmpjs],capture_output=True,text=True)
    if cp.returncode:
        print('NODE_CHECK_FAIL')
        print(cp.stdout[-2000:])
        print(cp.stderr[-4000:])
        raise SystemExit(68)
finally:
    try: os.unlink(tmpjs)
    except OSError: pass

backup=LIVE.with_name(LIVE.name+'.pre-microexpr-v11-'+pre[:12]+'.bak')
if not backup.exists(): shutil.copy2(LIVE,backup)
fd,tmp=tempfile.mkstemp(prefix='.buehne.microexpr-v11.',dir=str(ROOT))
os.close(fd)
Path(tmp).write_text(text,encoding='utf-8')
os.chmod(tmp,LIVE.stat().st_mode)
os.replace(tmp,LIVE)
post=hashlib.sha256(LIVE.read_bytes()).hexdigest()
print('BACKUP='+str(backup))
print('POST_SHA='+post)
print('BYTES='+str(LIVE.stat().st_size))
print('NOSE_OVERLAY=masked_head_local_deformation')
print('STATE_CLASSES=01_neutral,02_alert,03_tense,04_soft,05_tired,06_surprised')
print('KEYBOARD_FORCE=removed')
print('MICROEXPR_V11_UPGRADE_PASS')

// === FRANK_MICROEXPR_V1 BEGIN ===
// State-driven, non-cyclic idle microexpressions. Runs inside the existing
// animation loop; no second rAF and no extra polling timer.
const FRANK_MICROEXPR_VERSION = "2026-09-12-v1";
const _mikroMimik = {
  state: {
    ausdruck: null, activation: 1.0, surprise: 0,
    present: false, near: false, direction: null, load: 0,
    updatedAt: 0, impulse: 0
  },
  active: null,
  count: 0,
  lastTick: performance.now(),
  nextAllowed: performance.now() + 1200 + Math.random()*1800,
  quietUntil: 0,
  recent: [],
  lastMouthSrc: null,
  lastMouthOpacity: null,
  externalBusyUntil: 0,
  mouth: null,
  disabledReason: null
};

const MIKRO_MIMIK_PROFILE = [
  {name:"smirk_left",     kind:"social", frames:[0,1,2,3,4].map(i=>`/mund_keyframes/mund_31_smirk_left/stufe_0${i}.png`), peak:[1,3], dur:[620,1250], w:1.25},
  {name:"smirk_right",    kind:"social", frames:[0,1,2,3,4].map(i=>`/mund_keyframes/mund_32_smirk_right/stufe_0${i}.png`), peak:[1,3], dur:[620,1250], w:1.25},
  {name:"lip_pout",       kind:"ponder", frames:[0,1,2,3,4].map(i=>`/mund_keyframes/mund_33_pout/stufe_0${i}.png`), peak:[1,3], dur:[500,1050], w:0.85},
  {name:"jaw_set",        kind:"stress", frames:[0,1,2,3,4].map(i=>`/mund_keyframes/mund_34_jaw_clench/stufe_0${i}.png`), peak:[1,2], dur:[420,900], w:0.70},
  {name:"nose_scrunch_l", kind:"stress", frames:[0,1,2,3,4].map(i=>`/mund_keyframes/mund_22_snarl_left/stufe_0${i}.png`), peak:[1,2], dur:[360,780], w:0.58},
  {name:"nose_scrunch_r", kind:"stress", frames:[0,1,2,3,4].map(i=>`/mund_keyframes/mund_23_snarl_right/stufe_0${i}.png`), peak:[1,2], dur:[360,780], w:0.58},
  {name:"tongue_tip",     kind:"play", frames:[0,1,2,3,4].map(i=>`/mund_keyframes/mund_25_tongue_tip/stufe_0${i}.png`), peak:[1,2], dur:[360,700], w:0.34},
  {name:"tongue_out",     kind:"play", frames:[
      "/mund_keyframes/mund_26_tongue_out__stufe_00.png",
      "/mund_keyframes/mund_26_tongue_out__stufe_02.png",
      "/mund_keyframes/mund_26_tongue_out__stufe_03.png",
      "/mund_keyframes/mund_26_tongue_out__stufe_04.png"], peak:[2,3], dur:[650,1150], w:0.075},
  {name:"tongue_left",    kind:"play", frames:[
      "/mund_keyframes/mund_27_tongue_left__stufe_01.png",
      "/mund_keyframes/mund_27_tongue_left__stufe_02.png",
      "/mund_keyframes/mund_27_tongue_left__stufe_03.png",
      "/mund_keyframes/mund_27_tongue_left__stufe_04.png"], peak:[1,2], dur:[480,820], w:0.13},
  {name:"tongue_right",   kind:"play", frames:[
      "/mund_keyframes/mund_28_tongue_right__stufe_01.png",
      "/mund_keyframes/mund_28_tongue_right__stufe_02.png",
      "/mund_keyframes/mund_28_tongue_right__stufe_03.png",
      "/mund_keyframes/mund_28_tongue_right__stufe_04.png"], peak:[1,2], dur:[480,820], w:0.13},
  {name:"gasp_micro",     kind:"surprise", frames:[
      "/mund_keyframes/mund_35_gasp__stufe_00.png",
      "/mund_keyframes/mund_35_gasp__stufe_02.png",
      "/mund_keyframes/mund_35_gasp__stufe_03.png"], peak:[1,2], dur:[300,620], w:0.18},
  {name:"grin_closed",    kind:"positive", frames:[
      "/mund_keyframes/mund_20_grin_closed__stufe_00.png",
      "/mund_keyframes/mund_20_grin_closed__stufe_02.png",
      "/mund_keyframes/mund_20_grin_closed__stufe_04.png"], peak:[1,2], dur:[520,1000], w:0.42},
  {name:"lip_purse",      kind:"ponder", frames:[
      "/mund_keyframes/mund_29_whistle_small/stufe_00.png",
      "/mund_keyframes/mund_29_whistle_small/stufe_02.png",
      "/mund_keyframes/mund_29_whistle_small/stufe_04.png"], peak:[1,2], dur:[420,850], w:0.48}
];

function _mikroClamp(x,a,b){ return Math.max(a, Math.min(b,x)); }
function _mikroRnd(a,b){ return a + Math.random()*(b-a); }
function _mikroMouth(){
  if(_mikroMimik.mouth && _mikroMimik.mouth.isConnected) return _mikroMimik.mouth;
  _mikroMimik.mouth = document.getElementById("mund-effekt");
  if(!_mikroMimik.mouth) _mikroMimik.disabledReason = "mund-effekt fehlt";
  return _mikroMimik.mouth;
}
function _mikroOpacity(el){
  const v = parseFloat(el.style.opacity || getComputedStyle(el).opacity || "0");
  return Number.isFinite(v) ? v : 0;
}
function _mikroMimikStateAktualisieren(b){
  if(!b || typeof b !== "object") return;
  const s = _mikroMimik.state;
  const alterAusdruck = s.ausdruck;
  s.ausdruck = typeof b.ausdruck === "string" ? b.ausdruck.toLowerCase() : null;
  if(typeof b.broadcast_value === "number") s.activation = _mikroClamp(b.broadcast_value,0,3);
  if(typeof b.ueberraschung === "number") s.surprise = _mikroClamp(b.ueberraschung,0,1);
  const blick = b.blick && typeof b.blick === "object" ? b.blick : null;
  s.present = !!(blick && blick.anwesend);
  s.near = !!(blick && blick.nah);
  s.direction = blick && typeof blick.richtung === "string" ? blick.richtung : null;
  const swap = typeof b.swap_voll_anteil === "number" ? _mikroClamp(b.swap_voll_anteil,0,1) : 0;
  const ram = typeof b.ram_frei_anteil === "number" ? 1-_mikroClamp(b.ram_frei_anteil,0,1) : 0;
  s.load = Math.max(swap,ram);
  if(alterAusdruck !== null && s.ausdruck !== alterAusdruck) s.impulse = Math.min(1.5, s.impulse + 0.72);
  if(s.surprise > 0.18) s.impulse = Math.max(s.impulse, s.surprise);
  s.updatedAt = performance.now();
}

function _mikroProfilGewicht(p){
  const s = _mikroMimik.state;
  let w = p.w;
  const a = s.ausdruck || "";
  const positiv = /freu|happy|zufried|amused|confident|selbst|freund/.test(a);
  const fokus = /fokus|konzent|denk|ponder|listen|aufmerk/.test(a);
  const stress = /stress|aerger|ärger|frust|sorge|angespannt|krit/.test(a);
  if(p.kind === "social") w *= s.present ? (s.near ? 1.65 : 1.35) : 0.88;
  if(p.kind === "play"){
    w *= (positiv ? 1.8 : 0.75) * (s.present ? 1.25 : 0.72);
    if(s.load > 0.72) w *= 0.18;
  }
  if(p.kind === "positive") w *= positiv ? 2.0 : (s.present ? 1.15 : 0.72);
  if(p.kind === "ponder") w *= fokus ? 1.75 : 0.92;
  if(p.kind === "stress") w *= stress ? 1.9 : (0.72 + s.load*0.9);
  if(p.kind === "surprise") w *= 0.25 + s.surprise*6.0;
  if(s.near && p.kind === "stress" && !stress) w *= 0.55;
  const idx = _mikroMimik.recent.lastIndexOf(p.name);
  if(idx >= 0) w *= idx === _mikroMimik.recent.length-1 ? 0.035 : 0.16;
  return Math.max(0,w);
}
function _mikroProfilWaehlen(forcedName=null){
  if(forcedName){
    const p = MIKRO_MIMIK_PROFILE.find(x=>x.name===forcedName);
    if(p) return p;
  }
  const weighted = MIKRO_MIMIK_PROFILE.map(p=>[p,_mikroProfilGewicht(p)]);
  const sum = weighted.reduce((a,x)=>a+x[1],0);
  if(sum <= 0) return null;
  let r = Math.random()*sum;
  for(const [p,w] of weighted){ r -= w; if(r <= 0) return p; }
  return weighted[weighted.length-1][0];
}
function _mikroPeak(p){
  const lo=p.peak[0], hi=p.peak[1];
  let peak = lo + Math.floor(Math.random()*(hi-lo+1));
  const s=_mikroMimik.state;
  if(p.kind === "play" && (!s.present || s.load>0.65)) peak=Math.min(peak,lo);
  if(p.name === "tongue_out" && !(s.present && (s.activation>1.0 || /freu|happy|amused|confident|selbst/.test(s.ausdruck||"")))) peak=Math.min(peak,2);
  return Math.min(peak,p.frames.length-1);
}
function _mikroStart(t, forcedName=null){
  const mouth = _mikroMouth();
  if(!mouth || _sonderLaeuft) return false;
  if(t < _mikroMimik.externalBusyUntil) return false;
  const p = _mikroProfilWaehlen(forcedName);
  if(!p) return false;
  const dur = _mikroRnd(p.dur[0],p.dur[1]);
  _mikroMimik.active = {
    p, start:t, dur, peak:_mikroPeak(p),
    savedSrc:mouth.getAttribute("src"),
    savedOpacity:mouth.style.opacity,
    lastAppliedSrc:null,
    lastAppliedOpacity:null,
    lastStage:-1
  };
  _mikroMimik.recent.push(p.name);
  if(_mikroMimik.recent.length>5) _mikroMimik.recent.shift();
  _mikroMimik.count++;
  window.__frankMicroexpr = window.__frankMicroexpr || {};
  window.__frankMicroexpr.last = p.name;
  window.__frankMicroexpr.count = _mikroMimik.count;
  return true;
}
function _mikroAbortExternal(t){
  _mikroMimik.active = null;
  _mikroMimik.externalBusyUntil = t + 900 + Math.random()*500;
  _mikroMimik.nextAllowed = Math.max(_mikroMimik.nextAllowed, _mikroMimik.externalBusyUntil + 400);
}
function _mikroFinish(t){
  const a=_mikroMimik.active, mouth=_mikroMouth();
  if(a && mouth){
    if(a.savedSrc === null) mouth.removeAttribute("src"); else mouth.setAttribute("src",a.savedSrc);
    mouth.style.opacity = a.savedOpacity;
  }
  _mikroMimik.active=null;
  _mikroMimik.nextAllowed=t + _mikroRnd(1200,4200);
  if(Math.random()<0.14) _mikroMimik.quietUntil=t + _mikroRnd(6500,14500);
}
function _mikroRenderAktiv(t){
  const a=_mikroMimik.active, mouth=_mikroMouth();
  if(!a || !mouth) return;
  if(a.lastAppliedSrc !== null){
    const nowSrc=mouth.getAttribute("src");
    const nowOp=mouth.style.opacity;
    if(nowSrc !== a.lastAppliedSrc || nowOp !== a.lastAppliedOpacity){
      _mikroAbortExternal(t);
      return;
    }
  }
  const u=_mikroClamp((t-a.start)/a.dur,0,1);
  let env;
  if(u < 0.28){ const q=u/0.28; env=q*q*(3-2*q); }
  else if(u < 0.58){ env=1; }
  else { const q=(u-0.58)/0.42; env=1-(q*q*(3-2*q)); }
  const stage=Math.max(0, Math.min(a.peak, Math.round(env*a.peak)));
  if(stage !== a.lastStage){
    const src=a.p.frames[Math.min(stage,a.p.frames.length-1)];
    mouth.setAttribute("src",src);
    a.lastStage=stage;
  }
  mouth.style.opacity="1";
  a.lastAppliedSrc=mouth.getAttribute("src");
  a.lastAppliedOpacity=mouth.style.opacity;
  if(u>=1) _mikroFinish(t);
}
function _mikroMimikSchritt(t){
  const dt=Math.min(0.10, Math.max(0,(t-_mikroMimik.lastTick)/1000));
  _mikroMimik.lastTick=t;
  const mouth=_mikroMouth();
  if(!mouth) return;
  _mikroMimik.state.impulse *= Math.exp(-dt/2.2);
  if(_sonderLaeuft){
    if(_mikroMimik.active) _mikroFinish(t);
    _mikroMimik.nextAllowed=Math.max(_mikroMimik.nextAllowed,t+900);
    return;
  }
  if(_mikroMimik.active){ _mikroRenderAktiv(t); return; }
  const src=mouth.getAttribute("src"), op=_mikroOpacity(mouth);
  if(_mikroMimik.lastMouthSrc !== null && (src!==_mikroMimik.lastMouthSrc || Math.abs(op-_mikroMimik.lastMouthOpacity)>0.08)){
    _mikroMimik.externalBusyUntil=t+850;
  }
  _mikroMimik.lastMouthSrc=src;
  _mikroMimik.lastMouthOpacity=op;
  if(t<_mikroMimik.nextAllowed || t<_mikroMimik.quietUntil || t<_mikroMimik.externalBusyUntil) return;
  const s=_mikroMimik.state;
  let hazard=0.145;
  hazard *= 0.72 + 0.34*_mikroClamp(s.activation,0,2.2);
  if(s.present) hazard *= s.near ? 1.42 : 1.22;
  else hazard *= 0.82;
  hazard *= 1 + 0.85*s.surprise + 0.55*s.impulse;
  if((window.__buehneFps||60)<24) hazard*=0.38;
  const p=1-Math.exp(-hazard*dt);
  if(Math.random()<p) _mikroStart(t);
}

window.__frankMicroexpr = {
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
});
// === FRANK_MICROEXPR_V1 END ===

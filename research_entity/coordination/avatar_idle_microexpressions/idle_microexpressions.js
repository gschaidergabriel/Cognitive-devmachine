// FranKenstein Avatar — state-derived silent idle microexpressions
// Prepared 2026-09-12 against live buehne.html SHA-256
// 18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e
// This module is an integration payload, not a standalone production entrypoint.
// It deliberately reuses the live page's mouth frame arbitration variables.

let mundSprechBis = 0;
let _mikroMimikTimer = null;
let _mikroMimikAktiv = false;
let _mikroMimikGeneration = 0;
let _mikroMimikGestartet = false;
let _mikroMimikLetzteAktionTs = 0;
let _mikroMimikLetzteAktion = null;
let _mikroMimikNaechsteFruehestens = 0;
const _mikroMimikCooldownBis = new Map();
const _mikroMimikHistorie = [];
const _mikroMimikStatistik = {trigger:0, skip:0, block:0, abort:0};
const _mikroClamp = (v,a,b) => Math.max(a, Math.min(b,v));
const _mikroZufall = (a,b) => a + Math.random()*(b-a);
const _mikroInt = (a,b) => Math.floor(_mikroZufall(a,b+1));

const MIKRO_MIMIK_AKTIONEN = [
  {name:"lip_press",       asset:"mund_01_closed_mbp",     family:"press",   tag:"all",      basis:1.35, level:[1,3], hold:[90,260],  cool:[9000,22000]},
  {name:"soft_breath",     asset:"mund_02_breath",         family:"breath",  tag:"tired",    basis:1.05, level:[1,3], hold:[120,330], cool:[8000,20000]},
  {name:"small_o",         asset:"mund_08_o_small",        family:"round",   tag:"surprise", basis:0.62, level:[1,3], hold:[90,240],  cool:[15000,38000]},
  {name:"closed_grin",     asset:"mund_20_grin_closed",    family:"smile",   tag:"warm",     basis:0.95, level:[1,3], hold:[130,360], cool:[12000,30000]},
  {name:"teeth_grin",      asset:"mund_21_grin_teeth",     family:"smile",   tag:"warm",     basis:0.22, level:[1,2], hold:[80,180],  cool:[45000,100000]},
  {name:"nose_scrunch_l",  asset:"mund_22_snarl_left",     family:"scrunch", tag:"tense",    basis:0.60, level:[1,3], hold:[80,210],  cool:[20000,52000]},
  {name:"nose_scrunch_r",  asset:"mund_23_snarl_right",    family:"scrunch", tag:"tense",    basis:0.60, level:[1,3], hold:[80,210],  cool:[20000,52000]},
  {name:"teeth_tension",   asset:"mund_24_bare_teeth",     family:"tension", tag:"tense",    basis:0.18, level:[1,2], hold:[70,160],  cool:[50000,120000]},
  {name:"tongue_tip",      asset:"mund_25_tongue_tip",     family:"tongue",  tag:"play",     basis:0.28, level:[1,3], hold:[70,190],  cool:[35000,85000]},
  {name:"tongue_out",      asset:"mund_26_tongue_out",     family:"tongue",  tag:"play",     basis:0.08, level:[3,5], hold:[100,260], cool:[100000,240000]},
  {name:"tongue_left",     asset:"mund_27_tongue_left",    family:"tongue",  tag:"play",     basis:0.11, level:[2,4], hold:[90,230],  cool:[70000,180000]},
  {name:"tongue_right",    asset:"mund_28_tongue_right",   family:"tongue",  tag:"play",     basis:0.11, level:[2,4], hold:[90,230],  cool:[70000,180000]},
  {name:"whistle_small",   asset:"mund_29_whistle_small",  family:"whistle", tag:"all",     basis:0.16, level:[1,2], hold:[100,260], cool:[60000,150000]},
  {name:"whistle_strong",  asset:"mund_30_whistle_strong", family:"whistle", tag:"play",     basis:0.035,level:[1,2], hold:[80,170],  cool:[150000,300000]},
  {name:"smirk_left",      asset:"mund_31_smirk_left",     family:"smirk",   tag:"warm",     basis:1.00, level:[1,3], hold:[110,330], cool:[10000,26000]},
  {name:"smirk_right",     asset:"mund_32_smirk_right",    family:"smirk",   tag:"warm",     basis:1.00, level:[1,3], hold:[110,330], cool:[10000,26000]},
  {name:"pout",            asset:"mund_33_pout",           family:"pout",    tag:"tired",    basis:0.55, level:[1,3], hold:[100,300], cool:[18000,48000]},
  {name:"jaw_clench",      asset:"mund_34_jaw_clench",     family:"jaw",     tag:"tense",    basis:0.75, level:[1,3], hold:[100,320], cool:[16000,42000]},
  {name:"micro_gasp",      asset:"mund_35_gasp",           family:"gasp",    tag:"surprise", basis:0.16, level:[1,2], hold:[70,170],  cool:[55000,130000]}
];

const MIKRO_MIMIK_BIAS = {
  "01_ruhig_neutral":     {all:1.20,warm:0.90,tense:0.62,tired:0.72,surprise:0.45,play:0.58},
  "02_wach_aufmerksam":   {all:1.10,warm:1.05,tense:0.80,tired:0.45,surprise:0.85,play:0.72},
  "03_angespannt":        {all:0.90,warm:0.22,tense:2.45,tired:0.72,surprise:0.75,play:0.035},
  "04_zugewandt_weich":   {all:1.00,warm:2.15,tense:0.28,tired:0.55,surprise:0.60,play:1.85},
  "05_erschoepft_schwer": {all:0.95,warm:0.38,tense:0.78,tired:2.35,surprise:0.42,play:0.055},
  "06_ueberrascht":       {all:0.90,warm:0.65,tense:0.82,tired:0.42,surprise:2.50,play:0.28}
};

function mikroMimikState(){
  const ausdruck = (typeof aktuellerAusdruck === "string" && aktuellerAusdruck) || "01_ruhig_neutral";
  const anwesend = !!(serverBlick && serverBlick.anwesend);
  const nah = !!(anwesend && serverBlick.nah);
  const tv = (typeof tempo === "number" && Number.isFinite(tempo)) ? tempo : 1;
  const aktivierung = _mikroClamp((tv - 0.15) / 2.85, 0, 1);
  return {ausdruck, anwesend, nah, aktivierung, tempo:tv};
}

function mikroMimikDarf(){
  if(!_mikroMimikGestartet || _mikroMimikAktiv || _sonderLaeuft) return false;
  if(Date.now() < mundSprechBis || mundAktivFrames) return false;
  if(document.visibilityState && document.visibilityState !== "visible") return false;
  if(typeof regenGedrosselt !== "undefined" && regenGedrosselt) return false;
  const fps = Number(window.__buehneFps || 0);
  if(fps > 0 && fps < 30) return false;
  return true;
}

function mikroMimikGewicht(a, s){
  if(Date.now() < (_mikroMimikCooldownBis.get(a.name) || 0)) return 0;
  const bias = MIKRO_MIMIK_BIAS[s.ausdruck] || MIKRO_MIMIK_BIAS["01_ruhig_neutral"];
  let w = a.basis * (bias[a.tag] || 1);
  const letzteFamilien = _mikroMimikHistorie.slice(-2).map(x => x.family);
  if(letzteFamilien.includes(a.family)) w *= 0.13;
  if(a.tag === "play"){
    w *= s.nah ? 1.85 : (s.anwesend ? 0.58 : 0.18);
    w *= 0.70 + s.aktivierung * 0.75;
  }else if(a.tag === "warm"){
    w *= s.nah ? 1.40 : (s.anwesend ? 1.10 : 0.72);
  }else if(a.tag === "tense"){
    w *= 0.82 + s.aktivierung * 0.55;
  }else if(a.tag === "tired"){
    w *= 1.18 - s.aktivierung * 0.34;
  }
  return Math.max(0,w);
}

function mikroMimikWaehlen(s){
  const kandidaten = MIKRO_MIMIK_AKTIONEN.map(a => [a, mikroMimikGewicht(a,s)]).filter(x => x[1] > 0);
  const summe = kandidaten.reduce((n,x) => n+x[1], 0);
  if(summe <= 0) return null;
  let r = Math.random()*summe;
  for(const [a,w] of kandidaten){ r -= w; if(r <= 0) return a; }
  return kandidaten[kandidaten.length-1][0];
}

function mikroMundTeilZiel(name, level){
  const stufe = _mikroClamp(Math.round(level), 1, 5);
  const frames = [];
  const zwischen = Math.min(4, stufe - 1);
  for(let i=0;i<=zwischen;i++) frames.push(`/mund_keyframes/${name}__stufe_0${i}.png`);
  if(stufe >= 5) frames.push(`/mund_keyframes/${name}.png`);
  mundAktivFrames = frames;
  mundAktivIndex = 0;
  mundLetzterFrameT = 0;
}

function mikroMimikAbbrechen(grund, ruheWiederherstellen=true){
  if(!_mikroMimikAktiv) return;
  _mikroMimikGeneration++;
  _mikroMimikAktiv = false;
  _mikroMimikStatistik.abort++;
  if(ruheWiederherstellen && !_sonderLaeuft && Date.now() >= mundSprechBis){
    mundZielSetzen(MUND_RUHE);
  }
  window.__frankIdleMimikLastAbort = grund || "unknown";
}

function mikroMimikAusfuehren(a, s){
  if(!a || !mikroMimikDarf()) return false;
  const jetzt = Date.now();
  const generation = ++_mikroMimikGeneration;
  _mikroMimikAktiv = true;
  _mikroMimikLetzteAktionTs = jetzt;
  _mikroMimikLetzteAktion = a.name;
  _mikroMimikStatistik.trigger++;
  _mikroMimikHistorie.push({name:a.name,family:a.family,ts:jetzt,state:s.ausdruck});
  if(_mikroMimikHistorie.length > 8) _mikroMimikHistorie.shift();
  _mikroMimikCooldownBis.set(a.name, jetzt + _mikroZufall(a.cool[0], a.cool[1]));
  _mikroMimikNaechsteFruehestens = jetzt + _mikroZufall(4800, 9200);
  const level = _mikroInt(a.level[0], a.level[1]);
  mikroMundTeilZiel(a.asset, level);
  const angriff = (Math.min(5, level) + 1) * MUND_FRAME_MS + 35;
  const halten = _mikroZufall(a.hold[0], a.hold[1]);
  window.__frankIdleMimikLastEvent = {name:a.name, level, state:s, ts:jetzt};
  setTimeout(() => {
    if(generation !== _mikroMimikGeneration) return;
    if(_sonderLaeuft || Date.now() < mundSprechBis){
      _mikroMimikAktiv = false;
      mikroMimikPlanen(_mikroZufall(1600,3200));
      return;
    }
    mundZielSetzen(MUND_RUHE);
    setTimeout(() => {
      if(generation !== _mikroMimikGeneration) return;
      _mikroMimikAktiv = false;
      mikroMimikPlanen();
    }, 150 + Math.random()*120);
  }, angriff + halten);
  return true;
}

function mikroMimikMittlerePause(s){
  let ms = s.nah ? 9000 : (s.anwesend ? 12500 : 18000);
  if(s.ausdruck === "05_erschoepft_schwer") ms *= 1.28;
  else if(s.ausdruck === "02_wach_aufmerksam" || s.ausdruck === "04_zugewandt_weich") ms *= 0.90;
  ms /= (0.86 + s.aktivierung*0.28);
  return _mikroClamp(ms, 6500, 26000);
}

function mikroMimikPlanen(delayOverride){
  if(_mikroMimikTimer) clearTimeout(_mikroMimikTimer);
  if(!_mikroMimikGestartet) return;
  const s = mikroMimikState();
  let delay;
  if(typeof delayOverride === "number") delay = delayOverride;
  else {
    const mittel = mikroMimikMittlerePause(s);
    delay = -Math.log(Math.max(0.0001, Math.random())) * mittel;
    delay = _mikroClamp(delay, 2800, 44000);
  }
  const fruehestensIn = Math.max(0, _mikroMimikNaechsteFruehestens - Date.now());
  delay = Math.max(delay, fruehestensIn);
  _mikroMimikTimer = setTimeout(mikroMimikTick, delay);
}

function mikroMimikTick(){
  _mikroMimikTimer = null;
  if(!_mikroMimikGestartet) return;
  if(!mikroMimikDarf()){
    _mikroMimikStatistik.block++;
    mikroMimikPlanen(_mikroZufall(1300,3200));
    return;
  }
  // Intentional no-op: even when the stochastic hazard comes due, sometimes
  // the face simply stays still. This prevents a visible metronome.
  if(Math.random() < 0.16){
    _mikroMimikStatistik.skip++;
    mikroMimikPlanen();
    return;
  }
  const s = mikroMimikState();
  const a = mikroMimikWaehlen(s);
  if(!mikroMimikAusfuehren(a,s)) mikroMimikPlanen(_mikroZufall(1500,3000));
}

function mikroMimikStarten(){
  if(_mikroMimikGestartet) return;
  _mikroMimikGestartet = true;
  _mikroMimikNaechsteFruehestens = Date.now() + _mikroZufall(2500,6500);
  mikroMimikPlanen();
}
function mikroMimikStoppen(){
  _mikroMimikGestartet = false;
  if(_mikroMimikTimer) clearTimeout(_mikroMimikTimer);
  _mikroMimikTimer = null;
  mikroMimikAbbrechen("stop", true);
}
function mikroMimikErzwingen(name){
  if(!mikroMimikDarf()) return false;
  const a = MIKRO_MIMIK_AKTIONEN.find(x => x.name === name) || MIKRO_MIMIK_AKTIONEN.find(x => x.name === "smirk_left");
  return mikroMimikAusfuehren(a, mikroMimikState());
}
window.__frankIdleMimik = {
  version:"2026-09-12/state-hazard-v1",
  start:mikroMimikStarten,
  stop:mikroMimikStoppen,
  force:mikroMimikErzwingen,
  snapshot:() => ({enabled:_mikroMimikGestartet, active:_mikroMimikAktiv, speaking:Date.now()<mundSprechBis,
    state:mikroMimikState(), last:_mikroMimikLetzteAktion, lastTs:_mikroMimikLetzteAktionTs,
    stats:Object.assign({},_mikroMimikStatistik), history:_mikroMimikHistorie.slice()})
};

/* FranKenstein state-driven idle expression scheduler.
 * Pure scheduling/intent layer: no DOM assumptions, no production authority.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.FrankensteinIdleExpressions = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const clamp01 = (v) => Math.max(0, Math.min(1, Number.isFinite(+v) ? +v : 0));
  const lerp = (a, b, t) => a + (b - a) * t;
  const smoother = (t) => { t = clamp01(t); return t*t*t*(t*(t*6-15)+10); };
  function seededRng(seed) { let x=(seed>>>0)||0x9e3779b9; return function(){ x^=x<<13; x^=x>>>17; x^=x<<5; return (x>>>0)/4294967296; }; }
  const DEFAULT_STATE = Object.freeze({valence:.5,arousal:.35,tension:.2,fatigue:.15,curiosity:.45,playfulness:.2,uncertainty:.2,presence:.4,attention:.5,speaking:false,listening:false,engaged:true,blocked:false});
  function normalizeState(raw) {
    raw=raw||{};
    const pick=(names,fallback)=>{for(const n of names){const v=raw[n];if(typeof v==='number'&&Number.isFinite(v))return clamp01(v);}return fallback;};
    const bool=(names,fallback)=>{for(const n of names)if(typeof raw[n]==='boolean')return raw[n];return fallback;};
    return {
      valence:pick(['valence','wohlgefuehl','mood','positivity'],DEFAULT_STATE.valence), arousal:pick(['arousal','aktivierung','energy','energie'],DEFAULT_STATE.arousal),
      tension:pick(['tension','spannung','stress'],DEFAULT_STATE.tension), fatigue:pick(['fatigue','muedigkeit','tiredness'],DEFAULT_STATE.fatigue),
      curiosity:pick(['curiosity','neugier'],DEFAULT_STATE.curiosity), playfulness:pick(['playfulness','verspieltheit','play'],DEFAULT_STATE.playfulness),
      uncertainty:pick(['uncertainty','unsicherheit'],DEFAULT_STATE.uncertainty), presence:pick(['presence','socialPresence','naehe','personPresent'],DEFAULT_STATE.presence),
      attention:pick(['attention','aufmerksamkeit','focus'],DEFAULT_STATE.attention), speaking:bool(['speaking','spricht','isSpeaking'],false),
      listening:bool(['listening','hoertZu','isListening'],false), engaged:bool(['engaged','verbunden','connected'],true),
      blocked:bool(['blocked','faceBusy','expressionBusy','specialExpressionActive','sonderLaeuft'],false),
    };
  }
  const EXPRESSIONS = Object.freeze([
    {id:'lip_press',family:'mouth',lambda:.017,cooldownMs:[18000,39000],durationMs:[420,1050],intensity:[.16,.48],score:s=>.30+1.05*s.tension+.80*s.uncertainty+.30*s.attention-.30*s.playfulness},
    {id:'mouth_corner_left',family:'mouth',lambda:.013,cooldownMs:[16000,36000],durationMs:[360,920],intensity:[.13,.40],score:s=>.35+.55*s.playfulness+.35*s.curiosity+.20*Math.abs(s.valence-.5)*2},
    {id:'mouth_corner_right',family:'mouth',lambda:.013,cooldownMs:[16000,36000],durationMs:[360,920],intensity:[.13,.40],score:s=>.35+.55*s.playfulness+.35*s.curiosity+.20*Math.abs(s.valence-.5)*2},
    {id:'lip_purse',family:'mouth',lambda:.009,cooldownMs:[26000,52000],durationMs:[520,1250],intensity:[.13,.38],score:s=>.22+.95*s.uncertainty+.55*s.curiosity+.30*s.attention},
    {id:'micro_smile',family:'mouth',lambda:.012,cooldownMs:[22000,48000],durationMs:[500,1350],intensity:[.10,.34],score:s=>.16+1.00*s.valence+.65*s.presence+.45*s.playfulness-.55*s.tension},
    {id:'jaw_shift_left',family:'jaw',lambda:.007,cooldownMs:[30000,65000],durationMs:[650,1600],intensity:[.11,.32],score:s=>.20+.80*s.tension+.55*s.uncertainty+.25*s.fatigue},
    {id:'jaw_shift_right',family:'jaw',lambda:.007,cooldownMs:[30000,65000],durationMs:[650,1600],intensity:[.11,.32],score:s=>.20+.80*s.tension+.55*s.uncertainty+.25*s.fatigue},
    {id:'nose_scrunch',family:'nose',lambda:.010,cooldownMs:[26000,62000],durationMs:[320,820],intensity:[.14,.46],score:s=>.18+.85*s.tension+.60*s.curiosity+.35*s.playfulness+.25*(1-s.valence)},
    {id:'nostril_flare',family:'nose',lambda:.008,cooldownMs:[28000,60000],durationMs:[350,900],intensity:[.12,.36],score:s=>.20+.80*s.arousal+.45*s.tension+.20*s.attention},
    {id:'brow_pinched_micro',family:'brow',lambda:.010,cooldownMs:[22000,48000],durationMs:[420,1050],intensity:[.10,.32],score:s=>.18+.90*s.uncertainty+.55*s.tension+.40*s.attention},
    {id:'brow_raise_asym_left',family:'brow',lambda:.007,cooldownMs:[30000,70000],durationMs:[420,1100],intensity:[.11,.34],score:s=>.16+.95*s.curiosity+.45*s.playfulness+.30*s.presence},
    {id:'brow_raise_asym_right',family:'brow',lambda:.007,cooldownMs:[30000,70000],durationMs:[420,1100],intensity:[.11,.34],score:s=>.16+.95*s.curiosity+.45*s.playfulness+.30*s.presence},
    {id:'cheek_twitch_left',family:'cheek',lambda:.006,cooldownMs:[34000,76000],durationMs:[260,620],intensity:[.08,.25],score:s=>.22+.70*s.playfulness+.45*s.arousal+.25*s.tension},
    {id:'cheek_twitch_right',family:'cheek',lambda:.006,cooldownMs:[34000,76000],durationMs:[260,620],intensity:[.08,.25],score:s=>.22+.70*s.playfulness+.45*s.arousal+.25*s.tension},
    {id:'tongue_peek',family:'tongue',lambda:.0022,cooldownMs:[110000,260000],durationMs:[480,1050],intensity:[.20,.55],score:s=>Math.max(0,-.10+1.55*s.playfulness+.55*s.valence+.30*s.presence-.85*s.tension-.55*s.fatigue)},
    {id:'tongue_out',family:'tongue',lambda:.00055,cooldownMs:[300000,720000],durationMs:[650,1450],intensity:[.30,.68],score:s=>Math.max(0,-.42+1.90*s.playfulness+.65*s.valence+.35*s.presence-.95*s.tension-.70*s.fatigue)},
  ]);
  class IdleExpressionEngine {
    constructor(o){o=o||{};this.rng=o.rng||Math.random;this.apply=o.apply||function(){};this.stateProvider=o.stateProvider||(()=>DEFAULT_STATE);this.now=o.now||(()=>(typeof performance!=='undefined'?performance.now():Date.now()));this.expressions=o.expressions||EXPRESSIONS;this.globalRate=Number.isFinite(o.globalRate)?Math.max(0,o.globalRate):1;this.globalRefractoryMs=o.globalRefractoryMs||[1150,2900];this.speechReleaseMs=o.speechReleaseMs||900;this.blockReleaseMs=o.blockReleaseMs||420;this.maxDutyCycle=o.maxDutyCycle||.24;this.budgetWindowMs=o.budgetWindowMs||30000;this.familyRefractoryMs=Object.assign({mouth:5200,jaw:9000,nose:9000,brow:6000,cheek:8000,tongue:45000},o.familyRefractoryMs||{});this.active=null;this.lastTick=null;this.nextGlobalAllowed=0;this.lastSpeechAt=-Infinity;this.lastBlockedAt=-Infinity;this.actionAllowedAt=new Map();this.familyAllowedAt=new Map();this.recent=[];this.history=[];this.lastAction=null;this.lastFamily=null;this.telemetry={started:0,suppressedSpeech:0,suppressedBlocked:0,suppressedBudget:0,suppressedCooldown:0,applyErrors:0,abortedApply:0};}
    sampleRange(r){return lerp(r[0],r[1],this.rng());}
    currentState(){return normalizeState(this.stateProvider()||{});}
    _safeApply(id,phase,intensity,progress,s,a){try{this.apply(id,phase,intensity,progress,s,a);return true;}catch(_err){this.telemetry.applyErrors++;return false;}}
    _trimBudget(now){const cutoff=now-this.budgetWindowMs;while(this.history.length&&this.history[0].end<cutoff)this.history.shift();}
    _dutyCycle(now){this._trimBudget(now);const start=now-this.budgetWindowMs;let occupied=0;for(const h of this.history)occupied+=Math.max(0,Math.min(now,h.end)-Math.max(start,h.start));if(this.active)occupied+=Math.max(0,now-Math.max(start,this.active.start));return occupied/this.budgetWindowMs;}
    _eligible(e,s,now){if(s.speaking||s.blocked||now-this.lastSpeechAt<this.speechReleaseMs||now-this.lastBlockedAt<this.blockReleaseMs)return false;if(now<this.nextGlobalAllowed)return false;if(now<(this.actionAllowedAt.get(e.id)||0))return false;if(now<(this.familyAllowedAt.get(e.family)||0))return false;if(e.family==='tongue'&&s.playfulness<.28)return false;return true;}
    _noveltyPenalty(e){let p=1;if(e.id===this.lastAction)p*=.08;if(e.family===this.lastFamily)p*=.42;for(let i=Math.max(0,this.recent.length-4);i<this.recent.length;i++){const r=this.recent[i];if(r.id===e.id)p*=.45;else if(r.family===e.family)p*=.78;}return p;}
    _hazard(e,s){const engagement=s.engaged?1:.42, quietness=s.listening?.72:1, fatigueLimiter=1-.35*s.fatigue;return Math.max(0,e.lambda*this.globalRate*e.score(s)*engagement*quietness*fatigueLimiter*this._noveltyPenalty(e));}
    _pick(dt,s,now){if(this._dutyCycle(now)>=this.maxDutyCycle){this.telemetry.suppressedBudget++;return null;}const cs=[];let total=0;for(const e of this.expressions){if(!this._eligible(e,s,now))continue;const h=this._hazard(e,s);if(h<=0)continue;cs.push({e,h});total+=h;}if(!cs.length||total<=0){this.telemetry.suppressedCooldown++;return null;}if(this.rng()>=1-Math.exp(-total*Math.max(0,dt)))return null;let r=this.rng()*total;for(const c of cs){r-=c.h;if(r<=0)return c.e;}return cs[cs.length-1].e;}
    _start(e,s,now){const duration=this.sampleRange(e.durationMs),intensity=this.sampleRange(e.intensity)*(.88+.24*this.rng());this.active={id:e.id,family:e.family,start:now,end:now+duration,duration,intensity:clamp01(intensity),attackFrac:lerp(.16,.34,this.rng()),releaseFrac:lerp(.28,.48,this.rng()),stateAtStart:s};if(!this._safeApply(e.id,'start',0,0,s,this.active)){this.telemetry.abortedApply++;this.active=null;this.nextGlobalAllowed=now+750;return null;}this.telemetry.started++;return this.active;}
    _envelope(a,now){const p=clamp01((now-a.start)/a.duration);if(p<=a.attackFrac)return smoother(p/a.attackFrac);const rs=1-a.releaseFrac;if(p>=rs)return 1-smoother((p-rs)/a.releaseFrac);const hp=(p-a.attackFrac)/Math.max(1e-6,rs-a.attackFrac);return 1-.045*smoother(Math.abs(hp-.5)*2);}
    _finish(now,s){const a=this.active;if(!a)return;this._safeApply(a.id,'end',0,1,s,a);this.history.push({id:a.id,family:a.family,start:a.start,end:now});this.recent.push({id:a.id,family:a.family,at:now});if(this.recent.length>12)this.recent.splice(0,this.recent.length-12);const d=this.expressions.find(e=>e.id===a.id);if(d)this.actionAllowedAt.set(a.id,now+this.sampleRange(d.cooldownMs));this.familyAllowedAt.set(a.family,now+(this.familyRefractoryMs[a.family]||5000));this.nextGlobalAllowed=now+this.sampleRange(this.globalRefractoryMs);this.lastAction=a.id;this.lastFamily=a.family;this.active=null;}
    tick(now){now=Number.isFinite(now)?now:this.now();const s=this.currentState();if(s.speaking)this.lastSpeechAt=now;if(s.blocked)this.lastBlockedAt=now;if(this.lastTick==null)this.lastTick=now;const dt=Math.max(0,Math.min(.5,(now-this.lastTick)/1000));this.lastTick=now;if(this.active){if(s.speaking||s.blocked){if(s.speaking)this.telemetry.suppressedSpeech++;if(s.blocked)this.telemetry.suppressedBlocked++;this.active.end=Math.min(this.active.end,now+(s.blocked?100:180));this.active.duration=Math.max(1,this.active.end-this.active.start);}if(now>=this.active.end)this._finish(now,s);else{const p=clamp01((now-this.active.start)/this.active.duration);if(!this._safeApply(this.active.id,'update',this._envelope(this.active,now)*this.active.intensity,p,s,this.active)){this.telemetry.abortedApply++;this._finish(now,s);}}return this.active;}if(s.speaking||now-this.lastSpeechAt<this.speechReleaseMs){this.telemetry.suppressedSpeech++;return null;}if(s.blocked||now-this.lastBlockedAt<this.blockReleaseMs){this.telemetry.suppressedBlocked++;return null;}const e=this._pick(dt,s,now);if(e)this._start(e,s,now);return this.active;}
    forceNeutral(now){now=Number.isFinite(now)?now:this.now();if(this.active)this._safeApply(this.active.id,'end',0,1,this.currentState(),this.active);this.active=null;this.nextGlobalAllowed=now+350;this._safeApply('__all__','neutral',0,1,this.currentState(),null);}
    snapshot(){return{active:this.active?{id:this.active.id,family:this.active.family,start:this.active.start,end:this.active.end,intensity:this.active.intensity}:null,lastAction:this.lastAction,lastFamily:this.lastFamily,recent:this.recent.slice(-6),dutyCycle:this._dutyCycle(this.now()),telemetry:Object.assign({},this.telemetry)};}
  }
  return {IdleExpressionEngine,EXPRESSIONS,normalizeState,seededRng};
});
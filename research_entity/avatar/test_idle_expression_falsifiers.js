'use strict';
const assert = require('assert');
const {IdleExpressionEngine, EXPRESSIONS, normalizeState, seededRng} = require('./idle_expression_engine');

const probe = (id='probe', family='mouth') => ({id,family,lambda:100,cooldownMs:[0,0],durationMs:[1000,1000],intensity:[.5,.5],score:()=>1});
const base = () => ({valence:.6,arousal:.5,tension:.2,fatigue:.1,curiosity:.6,playfulness:.6,uncertainty:.2,presence:.7,attention:.7,speaking:false,listening:false,engaged:true,blocked:false});

// Inputs are bounded and every known busy-face alias is fail-closed.
let n = normalizeState({valence:99,arousal:-3,playfulness:NaN,faceBusy:true});
assert.strictEqual(n.valence,1); assert.strictEqual(n.arousal,0); assert.strictEqual(n.blocked,true);
assert.strictEqual(normalizeState({expressionBusy:true}).blocked,true);
assert.strictEqual(normalizeState({specialExpressionActive:true}).blocked,true);
assert.strictEqual(normalizeState({sonderLaeuft:true}).blocked,true);

// A full-head/special expression must suppress microexpressions immediately and briefly after release.
let now=0, state=base(), phases=[];
let e = new IdleExpressionEngine({rng:seededRng(1),now:()=>now,stateProvider:()=>state,expressions:[probe()],globalRate:100,blockReleaseMs:420,apply:(id,phase)=>phases.push({id,phase,t:now})});
e._start(e.expressions[0],e.currentState(),now);
assert(e.active,'probe must be active');
state.blocked=true; now=100; e.tick(now); assert(e.active && e.active.end<=200,'busy face must accelerate release');
now=220; e.tick(now); assert.strictEqual(e.active,null,'busy face must clear active microexpression');
const startsBefore=phases.filter(x=>x.phase==='start').length;
state.blocked=false; for(now=240;now<620;now+=20)e.tick(now);
assert.strictEqual(phases.filter(x=>x.phase==='start').length,startsBefore,'block release guard must prevent immediate restart');

// Speech is a hard gate, including a refractory tail after speech ends.
now=0; state=base(); state.speaking=true; phases=[];
e = new IdleExpressionEngine({rng:seededRng(2),now:()=>now,stateProvider:()=>state,expressions:[probe()],globalRate:100,speechReleaseMs:900,apply:(id,phase)=>phases.push({id,phase,t:now})});
for(now=0;now<=1000;now+=50)e.tick(now);
state.speaking=false; for(now=1050;now<1900;now+=50)e.tick(now);
assert.strictEqual(phases.filter(x=>x.phase==='start').length,0,'speech tail leaked an idle expression');

// Adapter/DOM exceptions must never strand the engine in an active gesture.
now=0; state=base();
e = new IdleExpressionEngine({now:()=>now,stateProvider:()=>state,expressions:[probe()],apply:()=>{throw new Error('synthetic DOM failure');}});
assert.doesNotThrow(()=>e._start(e.expressions[0],e.currentState(),0));
assert.strictEqual(e.active,null); assert.strictEqual(e.telemetry.applyErrors,1); assert.strictEqual(e.telemetry.abortedApply,1); assert.strictEqual(e.telemetry.started,0);

// Failure on an update also tears down rather than leaving transforms latched forever.
let calls=0;
e = new IdleExpressionEngine({now:()=>now,stateProvider:()=>state,expressions:[probe()],apply:(id,phase)=>{calls++;if(phase==='update')throw new Error('update failure');}});
e._start(e.expressions[0],e.currentState(),0); now=100; assert.doesNotThrow(()=>e.tick(now));
assert.strictEqual(e.active,null); assert(e.telemetry.applyErrors>=1); assert(e.telemetry.abortedApply>=1);

// A suspended/background tab cannot replay elapsed wall time as a burst: dt is capped and one tick starts at most one gesture.
now=0; state=base(); phases=[];
e = new IdleExpressionEngine({rng:()=>0,now:()=>now,stateProvider:()=>state,expressions:[probe('a','mouth'),probe('b','brow'),probe('c','nose')],globalRate:100,apply:(id,phase)=>{if(phase==='start')phases.push({id,t:now});}});
e.tick(0); now=15*60*1000; e.tick(now);
assert(phases.length<=1,'long pause replayed multiple gestures in one tick');

// Statistical left/right fairness. Mirrored definitions must not acquire a large scheduler-side handedness.
const countMirror=(seconds=600,seeds=80)=>{
  let L=0,R=0;
  for(let seed=1;seed<=seeds;seed++){
    let t=0, s=base();
    const eng=new IdleExpressionEngine({rng:seededRng(seed),now:()=>t,stateProvider:()=>s,globalRate:2.5,apply:(id,phase)=>{if(phase!=='start')return;if(id.endsWith('_left'))L++;if(id.endsWith('_right'))R++;}});
    for(;t<seconds*1000;t+=60)eng.tick(t);
  }
  return {L,R};
};
const mirror=countMirror();
assert(mirror.L+mirror.R>120,`insufficient mirror sample ${JSON.stringify(mirror)}`);
assert(Math.abs(mirror.L-mirror.R)/(mirror.L+mirror.R)<.14,`scheduler handedness too large ${JSON.stringify(mirror)}`);

// Under pathological high rate the duty budget must still dominate; one in-flight gesture may overshoot only by its bounded duration/window.
now=0; state=base(); let maxDuty=0;
e = new IdleExpressionEngine({rng:seededRng(17),now:()=>now,stateProvider:()=>state,globalRate:40,maxDutyCycle:.24,apply:()=>{}});
for(now=0;now<10*60*1000;now+=25){e.tick(now);maxDuty=Math.max(maxDuty,e.snapshot().dutyCycle);}
const maxDefinitionDuration=Math.max(...EXPRESSIONS.map(x=>x.durationMs[1]));
const theoreticalOvershoot=.24+maxDefinitionDuration/e.budgetWindowMs+.01;
assert(maxDuty<=theoreticalOvershoot,`duty-cycle runaway ${maxDuty} > ${theoreticalOvershoot}`);

// Real idle output must be irregular, not a disguised fixed-period loop.
now=0; state=base(); const startTimes=[];
e = new IdleExpressionEngine({rng:seededRng(77),now:()=>now,stateProvider:()=>state,globalRate:1,apply:(id,phase)=>{if(phase==='start')startTimes.push(now);}});
for(now=0;now<60*60*1000;now+=50)e.tick(now);
assert(startTimes.length>=18 && startTimes.length<=150,`unexpected neutral cadence ${startTimes.length}/h`);
const gaps=startTimes.slice(1).map((t,i)=>t-startTimes[i]);
const mean=gaps.reduce((a,b)=>a+b,0)/gaps.length;
const sd=Math.sqrt(gaps.reduce((a,b)=>a+(b-mean)**2,0)/gaps.length);
assert(sd/mean>.22,`cadence too periodic cv=${sd/mean}`);

console.log(JSON.stringify({pass:true,mirror,maxDuty,neutralEventsPerHour:startTimes.length,gapCv:sd/mean,guards:['speech','special-expression','apply-failure','long-pause','handedness','duty-cycle','aperiodicity']},null,2));

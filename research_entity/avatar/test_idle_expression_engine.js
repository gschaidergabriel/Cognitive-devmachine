'use strict';
const assert = require('assert');
const {IdleExpressionEngine, EXPRESSIONS, seededRng} = require('./idle_expression_engine');
function run({state,seconds=600,seed=1,rate=1}) {let now=0;const events=[];const engine=new IdleExpressionEngine({rng:seededRng(seed),now:()=>now,globalRate:rate,stateProvider:()=>state,apply:(id,phase,intensity)=>{if(phase==='start')events.push({id,t:now,intensity});}});for(;now<seconds*1000;now+=50)engine.tick(now);return{events,engine};}
let r=run({state:{speaking:true,playfulness:1,valence:1,presence:1},seconds:120,seed:4,rate:8});
assert.strictEqual(r.events.length,0,'speech must gate all idle gestures');
let hi=0,lo=0;
for(let seed=1;seed<=60;seed++){hi+=run({state:{playfulness:1,valence:.8,presence:.8,tension:0,fatigue:0},seconds:1200,seed,rate:2}).events.filter(e=>e.id.startsWith('tongue')).length;lo+=run({state:{playfulness:.05,valence:.5,presence:.5,tension:.2,fatigue:.2},seconds:1200,seed,rate:2}).events.filter(e=>e.id.startsWith('tongue')).length;}
assert(hi>lo*4+3,`tongue bias too weak hi=${hi} lo=${lo}`);
r=run({state:{playfulness:.6,curiosity:.8,tension:.4,uncertainty:.5,valence:.6,presence:.7},seconds:900,seed:9,rate:4});
for(let i=1;i<r.events.length;i++)if(r.events[i].id===r.events[i-1].id)assert(r.events[i].t-r.events[i-1].t>=15000,'same action repeated too quickly');
const seen=new Set();
for(let seed=1;seed<=24;seed++)for(const e of run({state:{playfulness:.75,curiosity:.8,tension:.55,uncertainty:.6,valence:.7,presence:.8,arousal:.7},seconds:1800,seed,rate:3}).events)seen.add(e.id);
assert(seen.size>=Math.floor(EXPRESSIONS.length*.70),`coverage too narrow ${seen.size}/${EXPRESSIONS.length}`);
r=run({state:{playfulness:.25,curiosity:.45,tension:.2,uncertainty:.2,valence:.55,presence:.4,arousal:.35},seconds:3600,seed:77,rate:1});
assert(r.events.length>=18,`too inert: ${r.events.length}/hour`);assert(r.events.length<=150,`too busy: ${r.events.length}/hour`);
console.log(JSON.stringify({pass:true,neutral_events_per_hour:r.events.length,playful_tongue:hi,lowplay_tongue:lo,coverage:seen.size,total_defs:EXPRESSIONS.length},null,2));

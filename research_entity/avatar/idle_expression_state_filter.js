/* Temporal filter for idle-expression drives. Polling state may jump every 3s;
 * facial behaviour should not. Binary speech/listening gates remain immediate.
 */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.FrankensteinIdleStateFilter=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
const C=v=>Math.max(0,Math.min(1,Number.isFinite(+v)?+v:0));
const CHANNELS=['valence','arousal','tension','fatigue','curiosity','playfulness','uncertainty','presence','attention'];
const TAU={
 valence:[1800,5000], arousal:[650,2600], tension:[800,5200], fatigue:[5000,16000],
 curiosity:[900,3500], playfulness:[1500,8500], uncertainty:[850,4300], presence:[280,1600], attention:[350,1800]
};
class IdleStateFilter{
 constructor(initial){this.value=Object.assign({},initial||{});this.target=Object.assign({},initial||{});this.last=null;}
 setTarget(s){this.target=Object.assign({},this.target,s||{});for(const k of ['speaking','listening','engaged'])if(typeof this.target[k]==='boolean')this.value[k]=this.target[k];return this;}
 tick(nowMs){nowMs=Number.isFinite(nowMs)?nowMs:(typeof performance!=='undefined'?performance.now():Date.now());if(this.last==null){this.last=nowMs;for(const k of CHANNELS)if(Number.isFinite(+this.target[k]))this.value[k]=C(this.target[k]);return this.value;}const dt=Math.max(0,Math.min(1000,nowMs-this.last));this.last=nowMs;for(const k of CHANNELS){const t=C(this.target[k]);const v=C(Number.isFinite(+this.value[k])?this.value[k]:t);const pair=TAU[k]||[1000,3000];const tau=t>v?pair[0]:pair[1];const a=1-Math.exp(-dt/Math.max(1,tau));this.value[k]=v+(t-v)*a;}for(const k of ['speaking','listening','engaged'])if(typeof this.target[k]==='boolean')this.value[k]=this.target[k];return this.value;}
 snapshot(){return Object.assign({},this.value);}
}
return{IdleStateFilter,TAU};
});

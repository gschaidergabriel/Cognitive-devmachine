const fs = require('fs');
const vm = require('vm');
const path = require('path');

const controller = fs.readFileSync(path.join(__dirname, 'idle_microexpressions.js'), 'utf8');
const ctx = {
  console, Math, Date,
  setTimeout: () => 0,
  clearTimeout: () => {},
  window: {__buehneFps: 60},
  document: {visibilityState: 'visible'},
  aktuellerAusdruck: '01_ruhig_neutral',
  serverBlick: {anwesend:false, nah:false},
  tempo: 1,
  mundAktivFrames: null,
  mundAktivIndex: 0,
  mundLetzterFrameT: 0,
  MUND_FRAME_MS: 22,
  MUND_RUHE: 'mund_00_rest',
  _sonderLaeuft: false,
  regenGedrosselt: false,
  mundZielSetzen: () => {}
};
vm.createContext(ctx);

const tests = `
function shares(expr,present,near,tempoValue){
  aktuellerAusdruck=expr; serverBlick={anwesend:present,nah:near}; tempo=tempoValue;
  const s=mikroMimikState();
  const groups={all:0,warm:0,tense:0,tired:0,surprise:0,play:0}; let total=0;
  for(const a of MIKRO_MIMIK_AKTIONEN){const w=mikroMimikGewicht(a,s); groups[a.tag]+=w; total+=w;}
  for(const k of Object.keys(groups)) groups[k]/=total;
  return {s,groups,mean:mikroMimikMittlerePause(s)};
}
const neutral=shares('01_ruhig_neutral',false,false,1);
const warm=shares('04_zugewandt_weich',true,true,1.25);
const tense=shares('03_angespannt',true,true,1.4);
const tired=shares('05_erschoepft_schwer',false,false,.55);
const surprise=shares('06_ueberrascht',true,false,1.1);
if(!(tense.groups.tense > tense.groups.play*20)) throw Error('tension must strongly suppress play');
if(!((warm.groups.warm+warm.groups.play) > warm.groups.tense*8)) throw Error('warm near must favor social/play over tension');
if(!(tired.groups.tired > tired.groups.play*20)) throw Error('tired must suppress play');
if(!(surprise.groups.surprise > neutral.groups.surprise)) throw Error('surprise state must raise surprise family');
const near=shares('01_ruhig_neutral',true,true,1).mean;
const present=shares('01_ruhig_neutral',true,false,1).mean;
const absent=shares('01_ruhig_neutral',false,false,1).mean;
if(!(near<present && present<absent)) throw Error('presence timing order failed');
_mikroMimikGestartet=true;
if(!mikroMimikDarf()) throw Error('baseline gate should allow');
mundSprechBis=Date.now()+5000; if(mikroMimikDarf()) throw Error('speech gate failed'); mundSprechBis=0;
_sonderLaeuft=true; if(mikroMimikDarf()) throw Error('special-expression gate failed'); _sonderLaeuft=false;
window.__buehneFps=25; if(mikroMimikDarf()) throw Error('fps gate failed'); window.__buehneFps=60;
// Hard-yield invariant: a speaking handoff must clear queued idle frames immediately.
_mikroMimikAktiv=true; mundAktivFrames=['idle-a','idle-b']; mundAktivIndex=1; mundLetzterFrameT=99;
mikroMimikAbbrechen('speech-test', false);
if(_mikroMimikAktiv || mundAktivFrames !== null || mundAktivIndex !== 0 || mundLetzterFrameT !== 0)
  throw Error('speech hard-yield failed');
console.log(JSON.stringify({neutral,warm,tense,tired,surprise,pause_ms:{near,present,absent}},null,2));
console.log('POLICY_TEST_PASS');
`;
vm.runInContext(controller + '\n' + tests, ctx, {timeout:1000});

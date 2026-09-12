/* FranKenstein Avatar — IDLE FACE v2, 2026-09-12.
   State-derived, non-cyclic silent microexpressions. Uses the existing mouth
   transition engine and current real expression assets. Speech/special-expression
   paths always win. No fixed periodic expression loop. */
(() => {
  "use strict";
  if (window.__idleFaceV2) return;

  const now = () => Date.now();
  const clamp = (v,a,b) => Math.max(a, Math.min(b, v));
  const pick = a => a[Math.floor(Math.random()*a.length)];

  const S = {
    version: "2.0",
    startedAt: now(),
    speakingUntil: 0,
    selfCategory: "self_neutral",
    selfCategorySince: 0,
    status: {broadcast: 0, surprise: false, at: 0},
    lastBaseExpression: null,
    stateKick: 0,
    lastGestureAt: 0,
    lastGesture: null,
    history: [],
    cooldownUntil: new Map(),
    energy: 2.0,
    energyAt: now(),
    events: 0,
    suppressed: {speech:0, special:0, busyMouth:0, refractory:0, energy:0, chance:0},
    intervals: [],
    noseAnim: null,
    noseOverlay: null,
    generation: 0
  };

  /* Speech is authoritative. The native mouth animation remains untouched except
     for a conservative busy window used to keep idle gestures out of its way. */
  const originalMouthAnimation = (typeof mundAnimation === "function") ? mundAnimation : null;
  if (originalMouthAnimation) {
    mundAnimation = function(text) {
      const n = Math.max(1, String(text || "").length);
      S.speakingUntil = now() + clamp(650 + n * 58, 1200, 12000);
      return originalMouthAnimation.apply(this, arguments);
    };
  }

  const originalSpecialFromEmote = (typeof sonderausdruckAusEmote === "function") ? sonderausdruckAusEmote : null;
  if (originalSpecialFromEmote) {
    sonderausdruckAusEmote = function(emote) {
      try {
        S.selfCategory = (typeof EMOTE_ZU_KATEGORIE !== "undefined" && EMOTE_ZU_KATEGORIE[emote]) || "self_neutral";
        S.selfCategorySince = now();
        S.stateKick = Math.max(S.stateKick, 0.7);
      } catch (_) {}
      return originalSpecialFromEmote.apply(this, arguments);
    };
  }

  const DEF = [
    {id:"lip_press",       target:"mund_01_closed_mbp",  base:.82, cd: 6500,  cost:.40, hold:[220,520]},
    {id:"tiny_grin",       target:"mund_20_grin_closed", base:.58, cd: 9000,  cost:.52, hold:[240,560]},
    {id:"smirk_left",      target:"mund_31_smirk_left",  base:.52, cd: 10500, cost:.56, hold:[260,620]},
    {id:"smirk_right",     target:"mund_32_smirk_right", base:.52, cd: 10500, cost:.56, hold:[260,620]},
    {id:"pout",            target:"mund_33_pout",        base:.38, cd: 12000, cost:.54, hold:[260,600]},
    {id:"jaw_clench",      target:"mund_34_jaw_clench", base:.20, cd: 16000, cost:.68, hold:[220,520]},
    {id:"gasp",            target:"mund_35_gasp",        base:.07, cd: 22000, cost:.76, hold:[180,430]},
    {id:"whistle_small",   target:"mund_29_whistle_small",base:.09,cd: 26000, cost:.74, hold:[260,560]},
    {id:"tongue_tip",      target:"mund_25_tongue_tip", base:.085,cd: 32000, cost:.95, hold:[180,420]},
    {id:"tongue_out",      target:"mund_26_tongue_out", base:.020,cd: 65000, cost:1.20, hold:[180,380]},
    {id:"tongue_left",     target:"mund_27_tongue_left",base:.010,cd: 85000, cost:1.25, hold:[160,360]},
    {id:"tongue_right",    target:"mund_28_tongue_right",base:.010,cd:85000,cost:1.25, hold:[160,360]},
    {id:"snarl_left",      target:"mund_22_snarl_left", base:.018,cd: 45000, cost:1.10, hold:[170,360]},
    {id:"snarl_right",     target:"mund_23_snarl_right",base:.018,cd: 45000, cost:1.10, hold:[170,360]},
    {id:"nose_scrunch",    target:null,                   base:.50, cd: 7500,  cost:.42, hold:[0,0]},
    {id:"nostril_flare",   target:null,                   base:.27, cd: 10500, cost:.38, hold:[0,0]}
  ];

  function liveState() {
    let expression="01_ruhig_neutral", speed=1, near=false, present=false,
        surprise=false, crisis=0, special=false, mouthBusy=false;
    try { expression = aktuellerAusdruck || expression; } catch (_) {}
    try { speed = clamp(Number(tempo)||1,.2,3); } catch (_) {}
    try { present=!!(serverBlick && serverBlick.anwesend); near=!!(serverBlick && serverBlick.anwesend && serverBlick.nah); } catch (_) {}
    try { surprise=!!_ueberraschungAusgeloest; } catch (_) {}
    try { crisis=Number(_koerperStufeVorher)||0; } catch (_) {}
    try { special=!!_sonderLaeuft; } catch (_) {}
    try { mouthBusy=!!mundAktivFrames; } catch (_) {}
    if (S.status.at && now()-S.status.at < 16000) surprise = surprise || !!S.status.surprise;
    if (S.selfCategorySince && now()-S.selfCategorySince > 90000) S.selfCategory="self_neutral";
    if (S.lastBaseExpression !== null && expression !== S.lastBaseExpression) S.stateKick=1;
    S.lastBaseExpression=expression;
    return {expression,speed,near,present,surprise,crisis,special,mouthBusy,category:S.selfCategory,broadcast:S.status.broadcast||0};
  }

  function refillEnergy() {
    const t=now(), dt=Math.max(0,t-S.energyAt)/1000;
    S.energyAt=t;
    S.energy=Math.min(2.7,S.energy+dt*.16);
  }

  function recentPenalty(id) {
    if (S.history[S.history.length-1] === id) return 0;
    if (S.history.slice(-3).includes(id)) return .22;
    return 1;
  }

  function weight(g,p) {
    let w=g.base * recentPenalty(g.id);
    const playful=["tongue_tip","tongue_out","tongue_left","tongue_right","whistle_small","tiny_grin"];
    const tension=["lip_press","jaw_clench","nose_scrunch","nostril_flare","snarl_left","snarl_right"];
    const soft=["tiny_grin","smirk_left","smirk_right","pout","tongue_tip"];

    switch(p.expression) {
      case "02_wach_aufmerksam":
        if (["nose_scrunch","smirk_left","smirk_right","lip_press"].includes(g.id)) w*=1.35;
        break;
      case "03_angespannt":
        if (tension.includes(g.id)) w*=2.0;
        if (playful.includes(g.id)) w*=.10;
        break;
      case "04_zugewandt_weich":
        if (soft.includes(g.id)) w*=1.65;
        if (["jaw_clench","snarl_left","snarl_right"].includes(g.id)) w*=.05;
        break;
      case "05_erschoepft_schwer":
        if (["lip_press","pout"].includes(g.id)) w*=1.35;
        if (["nose_scrunch","nostril_flare"].includes(g.id)) w*=.45;
        if (playful.includes(g.id)) w*=.08;
        break;
      case "06_ueberrascht":
        if (g.id==="gasp" || g.id==="nose_scrunch") w*=4.0;
        if (g.id==="jaw_clench") w*=.2;
        break;
    }

    switch(p.category) {
      case "self_creative":
        if (["smirk_left","smirk_right","tiny_grin","whistle_small","tongue_tip"].includes(g.id)) w*=1.9;
        if (g.id==="tongue_out") w*=5.5;
        if (g.id==="tongue_left" || g.id==="tongue_right") w*=4.0;
        break;
      case "self_confident":
        if (["smirk_left","smirk_right","tiny_grin","nostril_flare"].includes(g.id)) w*=1.55;
        break;
      case "self_uncertain":
        if (["lip_press","pout","mouth_skew"].includes(g.id)) w*=1.65;
        if (playful.includes(g.id)) w*=.15;
        break;
      case "self_empathetic":
        if (["tiny_grin","smirk_left","smirk_right"].includes(g.id)) w*=1.4;
        if (tension.includes(g.id)) w*=.55;
        break;
      case "self_technical":
        if (["lip_press","nose_scrunch"].includes(g.id)) w*=1.25;
        if (playful.includes(g.id)) w*=.12;
        break;
    }

    if (p.surprise && g.id==="gasp") w*=3.2;
    if (p.speed>1.25 && ["nostril_flare","nose_scrunch","smirk_left","smirk_right"].includes(g.id)) w*=1.22;
    if (p.near && ["tongue_out","tongue_left","tongue_right"].includes(g.id)) w*=.45;
    if (!p.present && ["tongue_out","tongue_left","tongue_right"].includes(g.id)) w*=.75;
    if (p.broadcast>0.60 && ["tiny_grin","smirk_left","smirk_right"].includes(g.id)) w*=1.25;
    if (p.broadcast<-0.35 && tension.includes(g.id)) w*=1.25;
    if (p.crisis>0) {
      if (tension.includes(g.id)) w*=1.55;
      if (playful.includes(g.id) || g.id==="tiny_grin") w*=.04;
    }
    return Math.max(0,w);
  }

  function choose(p) {
    const t=now(), candidates=[];
    let total=0;
    for (const g of DEF) {
      if (t < (S.cooldownUntil.get(g.id)||0) || S.energy<g.cost) continue;
      const w=weight(g,p);
      if (w<=0) continue;
      total+=w; candidates.push([g,w]);
    }
    if (!total) return null;
    let r=Math.random()*total;
    for (const [g,w] of candidates) { r-=w; if (r<=0) return g; }
    return candidates[candidates.length-1][0];
  }

  function mouthIdleAllowed() {
    if (now()<S.speakingUntil) { S.suppressed.speech++; return false; }
    try { if (_sonderLaeuft) { S.suppressed.special++; return false; } } catch (_) {}
    try { if (mundAktivFrames) { S.suppressed.busyMouth++; return false; } } catch (_) {}
    return true;
  }

  function mouthOnce(g) {
    if (!mouthIdleAllowed() || !g.target || typeof mundZielSetzen!=="function") return false;
    const hold=g.hold[0]+Math.random()*(g.hold[1]-g.hold[0]);
    const gen=++S.generation;
    mundZielSetzen(g.target);
    setTimeout(() => {
      if (gen!==S.generation || now()<S.speakingUntil) return;
      try { if (_sonderLaeuft) return; } catch (_) {}
      if (typeof mundZielSetzen==="function") mundZielSetzen(MUND_RUHE);
    }, hold);
    return true;
  }

  function noseOverlay() {
    if (S.noseOverlay && S.noseOverlay.isConnected) return S.noseOverlay;
    const parent=document.getElementById("kopf-dreh");
    if (!parent) return null;
    const o=document.createElement("img");
    o.id="idle-face-v2-nose"; o.alt=""; o.setAttribute("aria-hidden","true");
    Object.assign(o.style,{position:"absolute",inset:"0",width:"100%",height:"100%",zIndex:"3",pointerEvents:"none",opacity:"0",transformOrigin:"50% 29.5%"});
    const mask="radial-gradient(ellipse 8.8% 7.5% at 50% 29.5%,#000 0%,#000 48%,rgba(0,0,0,.76) 66%,transparent 100%)";
    o.style.webkitMaskImage=mask; o.style.maskImage=mask;
    parent.appendChild(o); S.noseOverlay=o; return o;
  }

  function noseOnce(kind) {
    if (now()<S.speakingUntil) return false;
    try { if (_sonderLaeuft) return false; } catch (_) {}
    let rolled=false; try { rolled=!!kopfRollAktiv; } catch (_) {}
    const src=document.getElementById(rolled?"kopf-schicht2":"kopf-schicht"), o=noseOverlay();
    if (!src || !o) return false;
    o.src=src.currentSrc||src.src;
    const d=Math.random()<.5?-1:1, scr=kind==="nose_scrunch";
    const x=scr?.38:.18, y=scr?-.72:-.12, sx=scr?1.009:1.016, sy=scr?.984:.997;
    if (S.noseAnim) try { S.noseAnim.cancel(); } catch (_) {}
    S.noseAnim=o.animate([
      {opacity:0,transform:"translate(0,0) scale(1)",offset:0},
      {opacity:.78,transform:`translate(${(d*x).toFixed(2)}px,${y}px) scaleX(${sx}) scaleY(${sy})`,offset:.30},
      {opacity:.60,transform:`translate(${(-d*x*.42).toFixed(2)}px,${(y*.5).toFixed(2)}px) scaleX(${(1+(sx-1)*.55).toFixed(4)}) scaleY(${(1+(sy-1)*.55).toFixed(4)})`,offset:.62},
      {opacity:0,transform:"translate(0,0) scale(1)",offset:1}
    ],{duration:(scr?470:390)+Math.random()*190,easing:"cubic-bezier(.20,.70,.26,1)"});
    S.noseAnim.onfinish=()=>{o.style.opacity="0";S.noseAnim=null;};
    return true;
  }

  function perform(g,p) {
    let ok=false;
    if (g.id==="nose_scrunch" || g.id==="nostril_flare") ok=noseOnce(g.id);
    else ok=mouthOnce(g);
    if (!ok) return false;
    const t=now(), prev=S.lastGestureAt;
    S.lastGestureAt=t; S.lastGesture=g.id; S.events++;
    if (prev) { S.intervals.push(t-prev); if (S.intervals.length>20) S.intervals.shift(); }
    S.history.push(g.id); if (S.history.length>8) S.history.shift();
    S.cooldownUntil.set(g.id,t+g.cd*(.88+Math.random()*.30));
    S.energy=Math.max(0,S.energy-g.cost);
    S.stateKick*=.22;
    window.dispatchEvent(new CustomEvent("frankenstein:idle-face",{detail:{id:g.id,state:p.expression,category:p.category,at:t}}));
    return true;
  }

  /* Exponential inter-opportunity spacing is memoryless and avoids a hidden
     metronome. State changes alter the hazard, not a deterministic period. */
  function nextDelay(p) {
    let mean=6200;
    if (p.expression==="02_wach_aufmerksam" || p.expression==="04_zugewandt_weich") mean=5000;
    if (p.expression==="03_angespannt") mean=4700;
    if (p.expression==="05_erschoepft_schwer") mean=9800;
    if (p.expression==="06_ueberrascht") mean=3600;
    mean/=clamp(.82+p.speed*.18,.78,1.25);
    if (S.stateKick>.65) mean*=.62;
    const u=Math.max(1e-6,Math.random());
    return clamp(-Math.log(u)*mean,1500,14500);
  }

  function opportunity() {
    refillEnergy();
    const p=liveState(), t=now();
    let free=true;
    if (p.special) {S.suppressed.special++;free=false;}
    else if (t<S.speakingUntil) {S.suppressed.speech++;free=false;}
    else if (p.mouthBusy) {S.suppressed.busyMouth++;free=false;}
    else if (t-S.lastGestureAt<1350) {S.suppressed.refractory++;free=false;}
    else if (S.energy<.38) {S.suppressed.energy++;free=false;}
    if (free) {
      let chance=.63+S.stateKick*.14;
      if (p.expression==="05_erschoepft_schwer") chance-=.20;
      if (p.expression==="06_ueberrascht") chance+=.10;
      if (p.speed>1.25) chance+=.06;
      chance=clamp(chance,.28,.82);
      if (Math.random()<chance) { const g=choose(p); if (g) perform(g,p); }
      else S.suppressed.chance++;
    }
    S.stateKick*=.82;
    setTimeout(opportunity,nextDelay(p));
  }

  function statusPoll() {
    fetch("/api/status",{cache:"no-store"}).then(r=>r.ok?r.json():null).then(d=>{
      if (!d) return;
      const b=d.buehne||{};
      S.status.broadcast=Number(b.broadcast_value)||0;
      S.status.surprise=!!b.ueberraschung;
      S.status.at=now();
    }).catch(()=>{}).finally(()=>setTimeout(statusPoll,2800+Math.random()*5200));
  }

  window.__idleFaceV2={
    version:S.version,
    snapshot:()=>{ const p=liveState(); return {version:S.version,...p,speaking:now()<S.speakingUntil,energy:+S.energy.toFixed(2),events:S.events,last:S.lastGesture,history:S.history.slice(),intervals:S.intervals.slice(),suppressed:{...S.suppressed}}; }
  };

  setTimeout(opportunity,1100+Math.random()*2600);
  setTimeout(statusPoll,900+Math.random()*1800);
})();

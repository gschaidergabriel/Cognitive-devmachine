/* FranKenstein Avatar — IDLE FACE v1, 2026-09-12.
   One-shot, state-weighted facial microexpressions. No periodic animation loop:
   each opportunity is re-scheduled with a fresh delay; cooldowns, recent-history
   suppression and an energy budget prevent mechanical repetition. */
(() => {
  "use strict";
  if (window.__idleFaceV1) return;

  const S = {
    speakingUntil: 0,
    selfCategory: "self_neutral",
    selfCategorySince: 0,
    lastGestureAt: 0,
    lastExpression: null,
    stateKick: 0,
    history: [],
    cooldownUntil: new Map(),
    energy: 1.7,
    energyAt: Date.now(),
    mouthAnim: null,
    noseAnim: null,
    events: 0
  };

  const originalMouthAnimation = (typeof mundAnimation === "function") ? mundAnimation : null;
  if (originalMouthAnimation) {
    mundAnimation = function(text) {
      const syllables = Math.max(3, Math.round((text || "").length / 2.6));
      S.speakingUntil = Date.now() + Math.min(9000, syllables * 220) + 350;
      if (S.mouthAnim) { try { S.mouthAnim.cancel(); } catch (_) {} S.mouthAnim = null; }
      const m = document.getElementById("mund-effekt");
      if (m) m.style.transform = "";
      return originalMouthAnimation(text);
    };
  }

  const originalSpecialFromEmote = (typeof sonderausdruckAusEmote === "function") ? sonderausdruckAusEmote : null;
  if (originalSpecialFromEmote) {
    sonderausdruckAusEmote = function(emote) {
      try {
        S.selfCategory = (typeof EMOTE_ZU_KATEGORIE !== "undefined" && EMOTE_ZU_KATEGORIE[emote]) || "self_neutral";
        S.selfCategorySince = Date.now();
        S.stateKick = Math.max(S.stateKick, 0.55);
      } catch (_) {}
      return originalSpecialFromEmote(emote);
    };
  }

  const DEF = [
    {id:"lip_press",      cd:6200,  cost:.48},
    {id:"corner_pull",    cd:5200,  cost:.48},
    {id:"mouth_skew",     cd:6800,  cost:.55},
    {id:"lip_purse",      cd:8200,  cost:.52},
    {id:"small_o",        cd:11000, cost:.55},
    {id:"nose_scrunch",   cd:6100,  cost:.48},
    {id:"nostril_flare",  cd:8200,  cost:.42},
    {id:"tongue_peek",    cd:36000, cost:1.35}
  ];

  function globals() {
    let expression = "01_ruhig_neutral", speed = 1, near = false, surprise = false, crisis = 0;
    try { expression = aktuellerAusdruck || expression; } catch (_) {}
    try { speed = Math.max(.15, Math.min(3, Number(tempo) || 1)); } catch (_) {}
    try { near = !!(serverBlick && serverBlick.anwesend && serverBlick.nah); } catch (_) {}
    try { surprise = !!_ueberraschungAusgeloest; } catch (_) {}
    try { crisis = Number(_koerperStufeVorher) || 0; } catch (_) {}
    if (S.selfCategorySince && Date.now() - S.selfCategorySince > 75000) S.selfCategory = "self_neutral";
    if (S.lastExpression !== null && expression !== S.lastExpression) S.stateKick = 1;
    S.lastExpression = expression;
    return {expression, speed, near, surprise, crisis, category:S.selfCategory};
  }

  function refillEnergy() {
    const now = Date.now();
    const dt = Math.max(0, now - S.energyAt) / 1000;
    S.energyAt = now;
    S.energy = Math.min(2.45, S.energy + dt * 0.19);
  }

  function weight(id, p) {
    let w = ({lip_press:.85,corner_pull:.88,mouth_skew:.72,lip_purse:.53,small_o:.16,nose_scrunch:.72,nostril_flare:.42,tongue_peek:.018})[id] || .1;
    switch (p.expression) {
      case "02_wach_aufmerksam":
        if (id === "nose_scrunch" || id === "corner_pull") w *= 1.5;
        break;
      case "03_angespannt":
        if (["lip_press","mouth_skew","nose_scrunch","nostril_flare"].includes(id)) w *= 1.95;
        if (id === "tongue_peek") w *= .08;
        break;
      case "04_zugewandt_weich":
        if (id === "corner_pull" || id === "lip_purse") w *= 1.65;
        if (id === "tongue_peek") w *= 2.6;
        break;
      case "05_erschoepft_schwer":
        if (id === "lip_press" || id === "lip_purse") w *= 1.45;
        if (id === "nose_scrunch" || id === "nostril_flare") w *= .48;
        if (id === "tongue_peek") w *= .04;
        break;
      case "06_ueberrascht":
        if (id === "small_o" || id === "nose_scrunch") w *= 3.3;
        break;
    }
    switch (p.category) {
      case "self_creative":
        if (id === "mouth_skew" || id === "corner_pull") w *= 1.5;
        if (id === "tongue_peek") w *= 11;
        break;
      case "self_confident":
        if (id === "corner_pull" || id === "mouth_skew" || id === "nostril_flare") w *= 1.65;
        break;
      case "self_uncertain":
        if (id === "lip_press" || id === "lip_purse") w *= 1.85;
        if (id === "tongue_peek") w *= .12;
        break;
      case "self_empathetic":
        if (id === "corner_pull") w *= 1.45;
        if (id === "nose_scrunch") w *= .75;
        break;
      case "self_technical":
        if (id === "lip_press" || id === "nose_scrunch") w *= 1.25;
        if (id === "tongue_peek") w *= .08;
        break;
    }
    if (p.surprise && id === "small_o") w *= 3.0;
    if (p.speed > 1.25 && (id === "nostril_flare" || id === "mouth_skew")) w *= 1.3;
    if (p.near && id === "tongue_peek") w *= .55;
    if (p.crisis > 0) {
      if (id === "lip_press" || id === "nose_scrunch") w *= 1.45;
      if (id === "tongue_peek" || id === "corner_pull") w *= .05;
    }
    return Math.max(0, w);
  }

  function choose(p) {
    const now = Date.now();
    const recent = S.history.slice(-2);
    const possible = DEF.filter(g => now >= (S.cooldownUntil.get(g.id) || 0) && !recent.includes(g.id) && S.energy >= g.cost);
    let sum = 0, weighted = [];
    for (const g of possible) { const w = weight(g.id, p); if (w > 0) { sum += w; weighted.push([g,w]); } }
    if (!sum) return null;
    let r = Math.random() * sum;
    for (const pair of weighted) { r -= pair[1]; if (r <= 0) return pair[0]; }
    return weighted[weighted.length - 1][0];
  }

  function mouthOnce(name, hold, asymmetry) {
    let special = false, frames = null;
    try { special = !!_sonderLaeuft; frames = mundAktivFrames; } catch (_) {}
    if (special || Date.now() < S.speakingUntil || frames) return false;
    const el = document.getElementById("mund-effekt");
    if (!el || typeof mundZielSetzen !== "function") return false;
    const dir = asymmetry || (Math.random() < .5 ? -1 : 1);
    mundZielSetzen(name);
    const dx = dir * (.50 + Math.random() * .68);
    const rot = dir * (.25 + Math.random() * .42);
    const sx = .992 + Math.random() * .016;
    const duration = 430 + Math.random() * 260 + hold;
    S.mouthAnim = el.animate([
      {transform:"translateX(0) rotate(0deg) scaleX(1)",offset:0},
      {transform:`translateX(${dx.toFixed(2)}px) rotate(${rot.toFixed(2)}deg) scaleX(${sx.toFixed(3)})`,offset:.34},
      {transform:`translateX(${(dx*.68).toFixed(2)}px) rotate(${(rot*.58).toFixed(2)}deg) scaleX(${(1+(sx-1)*.45).toFixed(3)})`,offset:.68},
      {transform:"translateX(0) rotate(0deg) scaleX(1)",offset:1}
    ], {duration, easing:"cubic-bezier(.22,.68,.28,1)"});
    setTimeout(() => {
      let specialNow = false;
      try { specialNow = !!_sonderLaeuft; } catch (_) {}
      if (Date.now() >= S.speakingUntil && !specialNow) mundZielSetzen(MUND_RUHE);
    }, Math.max(190, hold));
    S.mouthAnim.onfinish = () => { el.style.transform = ""; S.mouthAnim = null; };
    return true;
  }

  function noseOverlay() {
    let o = document.getElementById("idle-nose-overlay");
    if (o) return o;
    o = document.createElement("img"); o.id = "idle-nose-overlay"; o.alt = "";
    Object.assign(o.style, {position:"absolute",inset:"0",width:"100%",height:"100%",zIndex:"3",pointerEvents:"none",opacity:"0",transformOrigin:"50% 29.5%"});
    const mask = "radial-gradient(ellipse 9% 8% at 50% 29.5%,#000 0%,#000 50%,rgba(0,0,0,.78) 67%,transparent 100%)";
    o.style.webkitMaskImage = mask; o.style.maskImage = mask;
    const parent = document.getElementById("kopf-dreh");
    if (!parent) return null;
    parent.appendChild(o); return o;
  }

  function noseOnce(kind) {
    let special = false;
    try { special = !!_sonderLaeuft; } catch (_) {}
    if (special || Date.now() < S.speakingUntil) return false;
    let rolled = false;
    try { rolled = !!kopfRollAktiv; } catch (_) {}
    const srcEl = document.getElementById(rolled ? "kopf-schicht2" : "kopf-schicht");
    const o = noseOverlay();
    if (!srcEl || !o) return false;
    o.src = srcEl.currentSrc || srcEl.src;
    const dir = Math.random() < .5 ? -1 : 1;
    const scrunch = kind === "nose_scrunch";
    const a = scrunch ? `translate(${(dir*.35).toFixed(2)}px,-.85px) scaleX(1.008) scaleY(.982)` : `translate(${(dir*.18).toFixed(2)}px,-.15px) scaleX(1.018) scaleY(.997)`;
    const b = scrunch ? `translate(${(-dir*.20).toFixed(2)}px,-.45px) scaleX(1.004) scaleY(.990)` : "translate(0,0) scaleX(1.010) scaleY(1)";
    if (S.noseAnim) { try { S.noseAnim.cancel(); } catch (_) {} }
    S.noseAnim = o.animate([
      {opacity:0,transform:"translate(0,0) scale(1)",offset:0},
      {opacity:.88,transform:a,offset:.28},
      {opacity:.72,transform:b,offset:.58},
      {opacity:.82,transform:a,offset:.72},
      {opacity:0,transform:"translate(0,0) scale(1)",offset:1}
    ], {duration:(scrunch?520:430)+Math.random()*210,easing:"cubic-bezier(.2,.72,.28,1)"});
    S.noseAnim.onfinish = () => { o.style.opacity = "0"; S.noseAnim = null; };
    return true;
  }

  function perform(g) {
    let ok = false;
    if (g.id === "lip_press") ok = mouthOnce("mund_01_closed_mbp", 300 + Math.random()*380);
    else if (g.id === "corner_pull") ok = mouthOnce("mund_06_e", 300 + Math.random()*440);
    else if (g.id === "mouth_skew") ok = mouthOnce(Math.random()<.5?"mund_07_i":"mund_03_a_small", 280 + Math.random()*410);
    else if (g.id === "lip_purse") ok = mouthOnce(Math.random()<.5?"mund_11_u":"mund_08_o_small", 330 + Math.random()*440);
    else if (g.id === "small_o") ok = mouthOnce("mund_08_o_small", 230 + Math.random()*330);
    else if (g.id === "nose_scrunch" || g.id === "nostril_flare") ok = noseOnce(g.id);
    else if (g.id === "tongue_peek") {
      let running = false, lastSpecial = 0;
      try { running = !!_sonderLaeuft; lastSpecial = _letzterSonderausdruckTs || 0; } catch (_) {}
      if (!running && Date.now()-lastSpecial >= 22000 && typeof sonderausdruckZeigen === "function") {
        try { _letzterSonderausdruckTs = Date.now(); _letzterSonderausdruckAusdruck = "anime_zunge_raus"; } catch (_) {}
        sonderausdruckZeigen("anime_90s","anime_zunge_raus",180 + Math.random()*300);
        ok = true;
      }
    }
    if (ok) {
      const now = Date.now();
      S.lastGestureAt = now; S.cooldownUntil.set(g.id, now + g.cd);
      S.history.push(g.id); if (S.history.length > 6) S.history.shift();
      S.energy = Math.max(0, S.energy - g.cost); S.events++;
      S.stateKick *= .2;
    }
    return ok;
  }

  function nextDelay(p) {
    let ms = 2100 + Math.random()*3600;
    if (p.expression === "05_erschoepft_schwer") ms *= 1.45;
    if (p.speed > 1.25) ms *= .82;
    if (p.speed < .65) ms *= 1.22;
    if (S.stateKick > .65) ms *= .62;
    return Math.max(1500, Math.min(9000, ms));
  }

  function tick() {
    try {
      refillEnergy();
      const p = globals(), now = Date.now();
      let runningSpecial = false;
      try { runningSpecial = !!_sonderLaeuft; } catch (_) {}
      const free = !runningSpecial && now >= S.speakingUntil && now-S.lastGestureAt > 1400;
      if (free && S.energy >= .42) {
        let chance = .63 + S.stateKick*.16;
        if (p.speed > 1.25) chance += .08;
        if (p.expression === "02_wach_aufmerksam" || p.expression === "04_zugewandt_weich") chance += .05;
        if (p.expression === "05_erschoepft_schwer") chance -= .16;
        if (p.surprise) chance += .07;
        chance = Math.max(.32, Math.min(.84, chance));
        if (Math.random() < chance) { const g = choose(p); if (g) perform(g); }
      }
      S.stateKick *= .82;
      setTimeout(tick, nextDelay(p));
    } catch (e) {
      console.warn("[idle-face-v1]", e);
      setTimeout(tick, 4000 + Math.random()*2500);
    }
  }

  window.__idleFaceV1 = {
    version:"1.0", state:S,
    snapshot:() => ({...globals(), speaking:Date.now()<S.speakingUntil, energy:+S.energy.toFixed(2), events:S.events, history:S.history.slice()})
  };
  setTimeout(tick, 1300 + Math.random()*1800);
})();

/* Emergentes Gitter im Hintergrund der Chat-Ansicht.
 *
 * Gabriel 19.08.: "im hintergrund sollen ganz leicht sichtbar emergente gitter
 * strukturen sein die sich ganz leicht auf die mausbewegung reagieren und
 * waehrend zero denkt die knotenpunkte zufaellig leicht zu gluehen beginnen".
 *
 * Es zeigt buchstaeblich das Substrat, auf dem die Entitaet laeuft: ein Netz aus
 * Knoten und Kanten, sehr dezent. Es atmet leicht, weicht dem Zeiger aus, und
 * waehrend Zero denkt, gluehen zufaellige Knoten gruen auf -- als liefe Aktivitaet
 * durch das Netz. window.EMERGENZ.denken(true/false) schaltet das Gluehen.
 *
 * Alles auf EINEM Canvas, requestAnimationFrame, geknuepft an prefers-reduced-
 * motion: dort steht das Gitter still, kein Flackern.
 */
(function () {
  "use strict";
  var cv = document.getElementById("emergenz");
  if (!cv || !cv.getContext) return;
  var ctx = cv.getContext("2d");
  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

  var W = 0, H = 0, DPR = 1;
  var knoten = [], kanten = [], rafId = 0;
  var maus = { x: -9999, y: -9999, an: false };
  var denkt = false, tick = 0;

  // ⭐ Handy-/Schwachgeraet-Bremse (2026-08-19): "Atmosphaere, kein Akku-
  // Fresser" -- dieselbe Lehre wie in anmeldung.js (dort steht die Warnung
  // vor einer Dauer-Animation, die den Rechner mal auf Vollast gefahren hat).
  // Zwei billige Heuristiken statt einer teuren Messung: wenig Kerne/wenig
  // RAM (soweit der Browser das ueberhaupt verraet) ODER ein kleiner
  // Bildschirm -- ein 390px-Handy ist so gut wie nie ein Spielerechner.
  // Wirkung: weniger Knoten (groesserer Gitterabstand), DPR auf 1 gedeckelt
  // (der Retina-Vorteil ist bei einem dezenten Hintergrundmuster nicht
  // sichtbar, kostet aber bis zu 4x Fuellrate), und ein Bildrate-Deckel --
  // dieses Canvas braucht kein 90/120Hz, 45fps sehen fuer ein sanft
  // atmendes Gitter identisch aus und schonen Akku und GPU-Waerme.
  var SCHWACH = false;
  try {
    SCHWACH = (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4) ||
              (navigator.deviceMemory && navigator.deviceMemory <= 4) ||
              Math.min(window.innerWidth, window.innerHeight) < 480;
  } catch (e) {}
  var FRAME_MIN = 1000 / (SCHWACH ? 26 : 48);
  var letzterFrame = 0;

  window.EMERGENZ = { denken: function (b) { denkt = !!b; if (b && reduce) einmal(); } };

  // Signalfarbe aus dem House-System holen -- eine zweite Skala waere ein zweiter Dialekt.
  function rgbAusVar() {
    try {
      var v = getComputedStyle(document.documentElement).getPropertyValue("--signal").trim();
      if (v.charAt(0) === "#") {
        var h = v.slice(1); if (h.length === 3) h = h[0]+h[0]+h[1]+h[1]+h[2]+h[2];
        var n = parseInt(h, 16); return [(n>>16)&255, (n>>8)&255, n&255];
      }
      var m = v.match(/(\d+)\D+(\d+)\D+(\d+)/);
      if (m) return [+m[1], +m[2], +m[3]];
    } catch (e) {}
    return [47, 227, 138];
  }
  var RGB = rgbAusVar();
  function rgba(a) { return "rgba(" + RGB[0] + "," + RGB[1] + "," + RGB[2] + "," + a + ")"; }

  function baue() {
    DPR = Math.min(SCHWACH ? 1 : 2, window.devicePixelRatio || 1);
    W = cv.clientWidth || window.innerWidth;
    H = cv.clientHeight || window.innerHeight;
    cv.width = Math.max(1, W * DPR); cv.height = Math.max(1, H * DPR);
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    var step = Math.max(58, Math.min(W, H) / 11) * (SCHWACH ? 1.5 : 1);
    var cols = Math.ceil(W / step) + 2, rows = Math.ceil(H / step) + 2;
    knoten = []; kanten = [];
    var g = [];
    for (var r = 0; r < rows; r++) {
      g[r] = [];
      for (var c = 0; c < cols; c++) {
        var bx = (c - 1) * step + (Math.random() - 0.5) * step * 0.55;
        var by = (r - 1) * step + (Math.random() - 0.5) * step * 0.55;
        var k = { bx: bx, by: by, x: bx, y: by, ph: Math.random() * 6.283,
                  amp: step * (0.05 + Math.random() * 0.06), glut: 0, glutZiel: 0 };
        knoten.push(k); g[r][c] = k;
      }
    }
    // Kanten: rechts + unten + gelegentlich eine Diagonale -> Netz ohne Doppelte.
    for (var r2 = 0; r2 < rows; r2++) for (var c2 = 0; c2 < cols; c2++) {
      var a = g[r2][c2];
      if (c2 + 1 < cols) kanten.push([a, g[r2][c2 + 1]]);
      if (r2 + 1 < rows) kanten.push([a, g[r2 + 1][c2]]);
      if (r2 + 1 < rows && c2 + 1 < cols && Math.random() < 0.32) kanten.push([a, g[r2 + 1][c2 + 1]]);
    }
  }

  function bewege(zeit) {
    if (denkt) {
      tick++;
      if (tick % 6 === 0) for (var z = 0; z < 2; z++) {
        var kk = knoten[(Math.random() * knoten.length) | 0]; if (kk) kk.glutZiel = 1;
      }
    }
    for (var i = 0; i < knoten.length; i++) {
      var k = knoten[i];
      var zx = k.bx + Math.sin(zeit * 0.6 + k.ph) * k.amp;
      var zy = k.by + Math.cos(zeit * 0.5 + k.ph * 1.3) * k.amp;
      if (maus.an) {
        var dx = maus.x - zx, dy = maus.y - zy, d2 = dx * dx + dy * dy, R = 155;
        if (d2 < R * R) {
          var d = Math.sqrt(d2) || 1, f = 1 - d / R;
          zx += dx / d * f * 11; zy += dy / d * f * 11;   // dem Zeiger leicht folgen
          if (f > 0.5) k.glutZiel = Math.max(k.glutZiel, f * 0.65);
        }
      }
      k.x += (zx - k.x) * 0.25; k.y += (zy - k.y) * 0.25;
      k.glut += (k.glutZiel - k.glut) * 0.08;
      k.glutZiel *= 0.94;
    }
  }

  function zeichne() {
    ctx.clearRect(0, 0, W, H);
    ctx.lineWidth = 1;
    for (var e = 0; e < kanten.length; e++) {
      var A = kanten[e][0], B = kanten[e][1], gl = A.glut > B.glut ? A.glut : B.glut;
      ctx.strokeStyle = rgba(0.045 + gl * 0.30);
      ctx.beginPath(); ctx.moveTo(A.x, A.y); ctx.lineTo(B.x, B.y); ctx.stroke();
    }
    for (var n = 0; n < knoten.length; n++) {
      var p = knoten[n], gg = p.glut;
      if (gg > 0.02) {
        var rad = 9 + gg * 11;
        var rg = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, rad);
        rg.addColorStop(0, rgba(0.42 * gg)); rg.addColorStop(1, rgba(0));
        ctx.fillStyle = rg; ctx.beginPath(); ctx.arc(p.x, p.y, rad, 0, 6.283); ctx.fill();
      }
      ctx.fillStyle = rgba(0.10 + gg * 0.6);
      ctx.beginPath(); ctx.arc(p.x, p.y, 1.1 + gg * 1.7, 0, 6.283); ctx.fill();
    }
  }

  function einmal() { zeichne(); }   // ein Standbild fuer prefers-reduced-motion

  function frame(t) {
    if (!cv.isConnected) return;
    rafId = requestAnimationFrame(frame);
    if (t - letzterFrame < FRAME_MIN) return;   // Bildrate-Deckel, siehe SCHWACH oben
    letzterFrame = t;
    bewege(t * 0.001);
    zeichne();
  }

  function start() {
    baue();
    if (rafId) cancelAnimationFrame(rafId);
    if (reduce) { einmal(); return; }   // Ruhe respektieren: kein Loop
    rafId = requestAnimationFrame(frame);
  }

  var rz;
  window.addEventListener("resize", function () { clearTimeout(rz); rz = setTimeout(start, 200); });
  window.addEventListener("mousemove", function (e) {
    var r = cv.getBoundingClientRect();
    maus.x = e.clientX - r.left; maus.y = e.clientY - r.top; maus.an = true;
  }, { passive: true });
  window.addEventListener("mouseout", function () { maus.an = false; });
  // Handy hat keine Maus, aber dieselbe Geste gibt es beim Beruehren -- ohne
  // das reagiert das Gitter auf einem Touch-Geraet nie, obwohl der Code dafuer
  // schon da ist. passive:true, weil hier nichts gescrollt werden muss.
  window.addEventListener("touchmove", function (e) {
    if (!e.touches || !e.touches.length) return;
    var r = cv.getBoundingClientRect();
    maus.x = e.touches[0].clientX - r.left; maus.y = e.touches[0].clientY - r.top; maus.an = true;
  }, { passive: true });
  window.addEventListener("touchend", function () { maus.an = false; });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();

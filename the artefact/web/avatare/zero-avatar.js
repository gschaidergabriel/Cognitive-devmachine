/* Zeros Avatar als lebendiges Anzeigeinstrument.
 *
 * Drei Verhalten, alle vom Eigner vorgegeben:
 *   1. Die Null glitcht NUR in Zeros neuester Nachricht. Aeltere stehen still.
 *      Grund: sonst zappelt der ganze Verlauf und nichts sticht mehr hervor --
 *      die Bewegung soll sagen "hier bin ich gerade", nicht "hier ist Unruhe".
 *   2. Die Null der NEUESTEN Nachricht folgt dem Zeiger wie eine Pupille.
 *      GANZ LEICHT (max 3,5 px). Aeltere stehen still und mittig.
 *      Ein weit wandernder Glyph liest sich als Spielerei; eine minimale
 *      Nachfuehrung liest sich als Aufmerksamkeit.
 *   3. Eine Lichtquelle HINTER dem Avatar glueht je nach Zustand gruen bis rot
 *      und tritt nur an den Raendern hervor -- kein Ring auf der Scheibe.
 *
 * ⚠️ REGEL FUER DAS LICHT: er zeigt nur einen Zustand an, der auch BEGRUENDET
 * werden kann. Jeder Wert kommt mit `grund` und `quelle`; beides landet im
 * title-Attribut und ist per Zeiger ablesbar. Licht, das gruen leuchtet und
 * nicht sagen kann warum, ist Stimmungstheater und waere genau die Sorte
 * huebscher Behauptung, die dieses System sonst ueberall vermeidet.
 *
 * Kein Fremdcode, keine Abhaengigkeit, kein Nachladen.
 */
(function (global) {
  "use strict";

  var MAX_PUPILLE = 3.5;          // px -- bewusst klein
  var zeiger = { x: null, y: null };
  var lebende = new Set();        // alle sichtbaren Avatare
  var bewegungReduziert = global.matchMedia
    ? global.matchMedia("(prefers-reduced-motion: reduce)").matches
    : false;

  // EIN globaler Zeigerhorcher fuer alle Avatare. Einer je Nachricht waere bei
  // hundert Nachrichten hundert Horcher fuer dieselbe Information.
  var geplant = false;
  if (!bewegungReduziert) {
    global.addEventListener("mousemove", function (e) {
      zeiger.x = e.clientX; zeiger.y = e.clientY;
      if (geplant) return;
      geplant = true;
      global.requestAnimationFrame(function () {
        geplant = false;
        lebende.forEach(nachfuehren);
      });
    }, { passive: true });
  }

  function nachfuehren(av) {
    // ⚠️ Waehrend Zero denkt, lebt die Pupille von selbst -- die Maus
    // ueberschreibt das dann nicht.
    if (av._denk) return;
    // NUR die neueste Nachricht fuehrt nach -- dieselbe Regel wie beim Glitch.
    // Ein Verlauf, in dem zwanzig Pupillen gleichzeitig mitwandern, wirkt nicht
    // aufmerksam, sondern beobachtet. Und es rechnet zwanzigmal fuer nichts.
    if (!av.aktiv) return;
    if (zeiger.x === null || !av.el.isConnected) return;
    var r = av.el.getBoundingClientRect();
    if (!r.width) return;
    var dx = zeiger.x - (r.left + r.width / 2);
    var dy = zeiger.y - (r.top + r.height / 2);
    var d = Math.hypot(dx, dy) || 1;
    // Saettigung: ab ~240 px Abstand voller Ausschlag, naeher dran weniger --
    // sonst springt die Pupille, wenn der Zeiger direkt darueber steht.
    var f = Math.min(1, d / 240) * MAX_PUPILLE / d;
    av.pupille.setAttribute("transform", "translate(" + (dx * f).toFixed(2) + "," + (dy * f).toFixed(2) + ")");
  }

  /* zustand: {wert: -1..+1, grund: "…", quelle: "…"}
   * +1 = alles belegt und rund, -1 = Fehlschlag/blockiert. */
  function lichtFarbe(wert) {
    var w = Math.max(-1, Math.min(1, typeof wert === "number" ? wert : 0));
    // gruen (150°) ueber gelb (55°) nach rot (5°)
    var h = w >= 0 ? 55 + w * 95 : 55 + w * 50;
    var s = 60 + Math.abs(w) * 30;
    return "hsl(" + h.toFixed(0) + " " + s.toFixed(0) + "% 52%)";
  }

  var SVG =
    '<svg viewBox="0 0 128 128" class="z0-svg" aria-hidden="true">' +
      '<defs>' +
        '<clipPath id="z0ring-CID"><circle cx="64" cy="64" r="60"/></clipPath>' +
        '<clipPath id="z0band-CID"><rect x="0" y="52" width="128" height="17"/></clipPath>' +
        '<radialGradient id="z0vign-CID" cx="50%" cy="42%" r="70%">' +
          '<stop offset="55%" stop-color="#0b0d0e"/><stop offset="100%" stop-color="#000"/>' +
        '</radialGradient>' +
      '</defs>' +
      '<g clip-path="url(#z0ring-CID)">' +
        '<circle cx="64" cy="64" r="60" fill="url(#z0vign-CID)"/>' +
        '<g class="z0-pupille">' +
          '<text class="z0-glyph z0-cyan" x="64" y="65">0</text>' +
          '<text class="z0-glyph z0-mag"  x="64" y="65">0</text>' +
          '<text class="z0-glyph z0-base" x="64" y="65">0</text>' +
          '<g clip-path="url(#z0band-CID)" class="z0-slice">' +
            '<text class="z0-glyph z0-base" x="64" y="65">0</text>' +
          '</g>' +
        '</g>' +
      '</g>' +
      '<circle class="z0-saum" cx="64" cy="64" r="60"/>' +
    '</svg>';

  var laufnummer = 0;

  // ── Generative Denk-Gesten: die Pupille lebt, statt nur der Maus zu folgen ──
  function _rand(a, b) { return a + Math.random() * (b - a); }
  function _jetzt() { return (global.performance && performance.now) ? performance.now() : Date.now(); }

  var GESTEN = ["dart", "scan", "gruebeln", "driften", "doppel", "kreisen"];

  // Stimmungen -- jede gibt der Pupille einen anderen Charakter. Zufaellig
  // gewaehlt (mit leichtem Zug aus dem Zustand), und mitten im Denken kippbar:
  // mal lustig, mal ernst, mal sauer, mal nachdenklich. So ist es nie gleich.
  var STIMMUNGEN = {
    lustig:      { hue: 95,  tempo: 0.13, R: 4.2, blink: 0.011, basis: 1.0, ty: 0,     gew: { kreisen: 3, doppel: 3, dart: 2, driften: 1 } },
    verspielt:   { hue: 120, tempo: 0.15, R: 4.0, blink: 0.013, basis: 1.0, ty: -0.4,  gew: { kreisen: 3, dart: 2, doppel: 2, driften: 1 } },
    ernst:       { hue: 150, tempo: 0.05, R: 2.5, blink: 0.004, basis: 1.0, ty: 0,     gew: { driften: 3, scan: 3, gruebeln: 1, dart: 1 } },
    nachdenklich:{ hue: 48,  tempo: 0.055, R: 3.3, blink: 0.006, basis: 1.0, ty: -0.8, gew: { gruebeln: 4, driften: 2, scan: 1 } },
    sauer:       { hue: 8,   tempo: 0.17, R: 4.4, blink: 0.017, basis: 0.72, ty: 0.7,  gew: { dart: 4, doppel: 2, scan: 1, kreisen: 1 } },
    wachsam:     { hue: 176, tempo: 0.11, R: 3.8, blink: 0.008, basis: 1.0, ty: 0,     gew: { scan: 3, dart: 3, doppel: 1, driften: 1 } }
  };
  var STIMMUNG_NAMEN = Object.keys(STIMMUNGEN);

  function _waehleStimmung(w) {
    // Leichter Zug aus dem Zustand: negativ neigt zu sauer/wachsam, positiv zu
    // lustig/verspielt -- aber viel Zufall, damit es ueberrascht.
    var korb = STIMMUNG_NAMEN.slice();
    if (w <= -0.2) korb = korb.concat(["sauer", "sauer", "wachsam", "ernst"]);
    else if (w >= 0.2) korb = korb.concat(["lustig", "verspielt", "nachdenklich"]);
    else korb = korb.concat(["nachdenklich", "ernst"]);
    return korb[Math.floor(Math.random() * korb.length)];
  }

  function _gestenAusGewicht(gew) {
    var liste = [];
    for (var k in gew) { for (var i = 0; i < gew[k]; i++) liste.push(k); }
    return liste.length ? liste : GESTEN.slice();
  }

  function starteDenken(av, zustand) {
    if (bewegungReduziert) return;      // Ruhe respektieren -- gar keine Bewegung
    stoppeDenken(av);
    var w = (zustand && typeof zustand.wert === "number") ? zustand.wert : 0;
    var st = { gx: 0, gy: 0, tx: 0, ty: 0, halt: 0, blink: 1, blinkBis: 0,
               geste: "driften", phase: 0, winkel: _rand(0, 6.28), raf: 0,
               stimmung: null, stimmungBis: 0, gestenTopf: [], p: null };
    av._denk = st;

    function setzeStimmung(name, now) {
      st.stimmung = name;
      st.p = STIMMUNGEN[name];
      st.gestenTopf = _gestenAusGewicht(st.p.gew);
      st.stimmungBis = now + _rand(2600, 5200);  // dann evtl. eine neue Stimmung
      // Farbton der Stimmung ans Ruecklicht -- das gibt der Pupille Gefuehl.
      if (av.el) av.el.style.setProperty("--z0-licht", "hsl(" + st.p.hue + " 72% 52%)");
    }

    function schritt(now) {
      var P = st.p, R = P.R, yb = P.ty;   // yb = vertikaler Bias der Stimmung
      switch (st.geste) {
        case "dart":     st.tx = _rand(-R, R); st.ty = _rand(-R, R) + yb * R * 0.5; st.halt = now + _rand(110, 300); break;
        case "scan":     st.phase++; st.tx = (st.phase % 2 ? R : -R) * 0.92; st.ty = _rand(-1, 1) + yb; st.halt = now + _rand(420, 720); break;
        case "gruebeln": st.tx = _rand(-R * 0.4, R * 0.4); st.ty = -R * _rand(0.6, 1) + yb; st.halt = now + _rand(560, 980); break;
        case "driften":  st.tx = _rand(-R * 0.6, R * 0.6); st.ty = _rand(-R * 0.6, R * 0.6) + yb * R * 0.4; st.halt = now + _rand(520, 1000); break;
        case "doppel":   st.phase++; st.tx = (st.phase % 2 ? -R : R); st.ty = _rand(-1.2, 1.2) + yb; st.halt = now + _rand(120, 230); break;
        case "kreisen":  st.winkel += _rand(0.5, 1.1); st.tx = Math.cos(st.winkel) * R * 0.8; st.ty = Math.sin(st.winkel) * R * 0.8 + yb; st.halt = now + _rand(170, 330); st.phase++; break;
      }
    }
    function neueGeste(now) {
      st.geste = st.gestenTopf[Math.floor(Math.random() * st.gestenTopf.length)];
      st.phase = 0;
      schritt(now);
    }

    setzeStimmung(_waehleStimmung(w), _jetzt());
    neueGeste(_jetzt());

    function loop() {
      if (av._denk !== st) return;      // gestoppt oder ersetzt
      var now = _jetzt(), P = st.p;
      // Stimmung mitten im Denken kippen lassen -- generativ, nie festgelegt.
      if (now > st.stimmungBis && Math.random() < 0.5) { setzeStimmung(_waehleStimmung(w), now); neueGeste(now); }
      var unruhe = Math.min(1, P.tempo * 6);
      var jitter = unruhe * 0.3;
      st.gx += (st.tx - st.gx) * P.tempo + _rand(-jitter, jitter);
      st.gy += (st.ty - st.gy) * P.tempo + _rand(-jitter, jitter);
      // Blinzeln (Rate der Stimmung); "sauer" hat eine tiefere Grundlinie -> Schielen.
      if (now > st.blinkBis && Math.random() < P.blink) st.blinkBis = now + _rand(80, 150);
      var ziel = now < st.blinkBis ? 0.1 : P.basis;
      st.blink += (ziel - st.blink) * 0.45;
      if (now > st.halt) {
        if (st.geste === "scan" || st.geste === "doppel" || st.geste === "kreisen") {
          if (st.phase > _rand(2, 5)) neueGeste(now); else schritt(now);
        } else neueGeste(now);
      }
      // Der aeussere Glow morpht mit -- atmet, flammt bei schnellen Gesten
      // auf, dimmt beim Blinzeln, Grundglut je Stimmung. Intensiviert alles.
      var atem = 0.92 + Math.sin(now * 0.0016) * 0.20;
      var flare = (st.geste === "dart" || st.geste === "doppel") ? 0.22 : 0;
      var grund = st.stimmung === "sauer" ? 1.28 : st.stimmung === "ernst" ? 0.9
                  : st.stimmung === "nachdenklich" ? 0.8 : st.stimmung === "lustig" ? 1.12 : 1.02;
      var glut = grund * atem + flare - (1 - st.blink) * 0.55;
      if (av.el) av.el.style.setProperty("--z0-staerke", Math.max(0.3, glut).toFixed(3));
      var cx = 64, cy = 65;
      av.pupille.setAttribute("transform",
        "translate(" + st.gx.toFixed(2) + "," + st.gy.toFixed(2) + ") " +
        "translate(" + cx + "," + cy + ") scale(1," + st.blink.toFixed(3) + ") translate(" + (-cx) + "," + (-cy) + ")");
      st.raf = global.requestAnimationFrame(loop);
    }
    st.raf = global.requestAnimationFrame(loop);
  }

  function stoppeDenken(av) {
    if (av && av._denk) {
      if (av._denk.raf) global.cancelAnimationFrame(av._denk.raf);
      av._denk = null;
      // sauber zurueck: entweder wieder der Maus folgen oder in die Mitte.
      if (av.aktiv) nachfuehren(av);
      else if (av.pupille) av.pupille.setAttribute("transform", "translate(0,0)");
    }
  }

  function erzeugen(container, optionen) {
    var o = optionen || {};
    var id = "z" + (++laufnummer);
    container.classList.add("z0");
    container.innerHTML = SVG.replace(/-CID/g, "-" + id);

    var av = {
      el: container,
      pupille: container.querySelector(".z0-pupille"),
      saum: container.querySelector(".z0-saum"),
    };
    lebende.add(av);

    av.setzeZustand = function (zustand) {
      var z = zustand || {};
      var farbe = lichtFarbe(z.wert);
      // Farbe und Staerke gehen als CSS-Variablen an die Lichtquelle HINTER
      // dem Avatar (.z0::before) und an den Kantensaum. Kein Ring auf der
      // Scheibe -- das Licht kommt von hinten und tritt nur am Rand hervor.
      container.style.setProperty("--z0-licht", farbe);
      // Ein unbekannter Zustand leuchtet schwaecher statt falsch: lieber
      // sichtbar unsicher als selbstbewusst gruen ohne Grund.
      container.style.setProperty("--z0-staerke", z.grund ? "1" : "0.45");
      // Der Grund gehoert an das Bild, nicht in eine Fussnote.
      container.title = z.grund
        ? "Zustand " + (typeof z.wert === "number" ? z.wert.toFixed(2) : "?") +
          " — " + z.grund + (z.quelle ? " [" + z.quelle + "]" : "")
        : "Zustand unbekannt — kein Grund geliefert";
    };

    // Nur die neueste Nachricht glitcht UND fuehrt die Pupille nach.
    av.setzeAktiv = function (aktiv) {
      av.aktiv = !!aktiv;
      container.classList.toggle("z0-aktiv", av.aktiv && !bewegungReduziert);
      if (av._denk) return;   // denkt gerade -- Blick nicht anfassen
      if (!av.aktiv) {
        av.pupille.setAttribute("transform", "translate(0,0)");
      } else {
        nachfuehren(av);
      }
    };

    av.entfernen = function () { lebende.delete(av); };

    av.starteDenken = function (zustand) { starteDenken(av, zustand || {}); };
    av.stoppeDenken = function () { stoppeDenken(av); };
    av.setzeZustand(o.zustand);
    av.setzeAktiv(o.aktiv);
    return av;
  }

  /* Sorgt dafuer, dass GENAU der letzte Zero-Avatar glitcht. Nach jeder neuen
   * Nachricht aufrufen. */
  function nurNeuesteAktiv(avatare) {
    avatare.forEach(function (av, i) { av.setzeAktiv(i === avatare.length - 1); });
  }

  global.ZeroAvatar = { erzeugen: erzeugen, nurNeuesteAktiv: nurNeuesteAktiv, lichtFarbe: lichtFarbe, starteDenken: starteDenken, stoppeDenken: stoppeDenken };
})(window);

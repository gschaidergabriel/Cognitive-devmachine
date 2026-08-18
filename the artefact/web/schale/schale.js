/* Die Schale: die gemeinsame Kopfleiste beider Seiten -- und die einzige
 * Stelle, an der der Zustand gemessen wird.
 *
 * Warum die Messung hier liegt und nicht auf jeder Seite:
 *   Zwei Seiten, die je selbst pollen, sind zwei Wahrheiten, die sich um
 *   Sekunden unterscheiden -- und der Nutzer sieht dann eine Leiste, die gruen
 *   ist, ueber einem Feld, das rot ist. Es gibt genau eine Messung je Takt,
 *   und alles Sichtbare haengt daran.
 *
 * ⚠️ REGEL, die aus zero-avatar.js kommt und hier weitergilt:
 *   Angezeigt wird nur ein Zustand, der BEGRUENDET werden kann. Jeder Wert
 *   traegt seinen `grund`; der landet am Statuspunkt (title + aria-label) und
 *   ist per Zeiger ablesbar. Was nicht gemessen wurde, leuchtet SCHWAECHER
 *   (--signal-staerke .45) statt selbstbewusst falsch, und eine Zahl, die
 *   niemand geliefert hat, fehlt -- sie ist niemals 0.
 *
 * ⚠️ BEWEGUNGSGESETZ (Gabriel, nach der ersten Live-Sicht):
 *   Ein Effekt, nicht zwei -- der Glitch. Er feuert bei WECHSELN und ist nach
 *   170 ms restlos weg. Die frueheren Wellenlinien sind ersatzlos raus; nichts
 *   in dieser Datei zeichnet mehr eine Kurve.
 *
 * Kein Framework, kein Router, kein Bauschritt. Wird per <script defer> geladen
 * und fuellt das <header id="entityos-schale">, das die Seite direkt nach
 * <body> setzt.
 */
(function (global) {
  "use strict";

  var doc = global.document;

  var bewegungReduziert = global.matchMedia
    ? global.matchMedia("(prefers-reduced-motion: reduce)").matches
    : false;

  /* Ein Takt, nicht zwei. Seit die Spur weg ist, gibt es nichts mehr, was
   * sekuendlich etwas zu zeichnen haette -- und /readyz prueft wirklich etwas
   * nach. 30 s, weil das der Takt des autonomen Pulses ist: schneller fragen
   * hiesse dieselbe Zahl doppelt lesen und den Wirt dafuer bezahlen. */
  var ZUSTAND_TAKT = 30000;

  /* Die Wortmarke. Sie steht hier als Konstante, damit es genau EINE Stelle
   * gibt, an der die Schreibweise haengt -- kleines e, grosses OS. */
  var MARKE = "entityOS";

  var WEGE = [
    { pfad: "/",         wort: "Chat",    kurz: "Chat", symbol: "blase" },
    { pfad: "/postfach", wort: "Mailbox", kurz: "Mail", symbol: "brief" }
  ];

  /* Symbole als Inline-SVG statt als Zeichen oder Bilddatei: ein Zeichen aus
   * einer fremden Schrift kann fehlen und wird dann zum Kaestchen, eine
   * Bilddatei kann fehlen und wird dann zum kaputten Bild. Beides sind Fehler,
   * die die Abnahme zaehlt. Ein Pfad im Dokument kann nicht fehlen. */
  var SYMBOLE = {
    blase: '<path d="M2 3.5h12v8H7l-3.5 3v-3H2z"/>',
    brief: '<rect x="2" y="3.5" width="12" height="9"/><path d="m2 4.5 6 4.5 6-4.5"/>'
  };

  // ── Farbe aus dem Messwert ─────────────────────────────────────────────
  /* Identische Kurve wie zero-avatar.js: gruen (150°) ueber gelb (55°) nach
   * rot (5°). Bewusst nachgebaut statt importiert, damit die Schale auch auf
   * Seiten ohne Avatar dieselbe Skala hat -- eine zweite Skala waere ein
   * zweiter Dialekt. Wer eine aendert, aendert beide. */
  function signalTon(wert) {
    var w = Math.max(-1, Math.min(1, typeof wert === "number" ? wert : 0));
    return {
      h: (w >= 0 ? 55 + w * 95 : 55 + w * 50).toFixed(0),
      s: (60 + Math.abs(w) * 30).toFixed(0) + "%"
    };
  }

  var status = { el: null };

  function setzeSignal(z) {
    var ton = signalTon(z.wert);
    var wurzel = doc.documentElement;
    wurzel.style.setProperty("--zustand-h", ton.h);
    wurzel.style.setProperty("--zustand-s", ton.s);
    // Unbekannt heisst schwaecher, nicht anders gefaerbt: eine falsche Farbe
    // luegt, eine schwache Farbe sagt "ich weiss es gerade nicht".
    wurzel.style.setProperty("--signal-staerke", z.grund ? "1" : "0.45");
    if (!status.el) return;
    var text = z.grund
      ? z.grund + (z.quelle ? " [" + z.quelle + "]" : "")
      : "Zustand unbekannt — kein Grund geliefert";
    status.el.title = text;
    status.el.setAttribute("aria-label", "Zustand: " + text);
  }

  // ── Der Glitch ─────────────────────────────────────────────────────────
  /* Der einzige Effekt des Hauses. Er braucht einen Anlass -- deshalb gibt es
   * keine Dauerklasse, sondern diesen Aufruf: wer ihn ruft, hat gerade einen
   * Wechsel gemessen. Die Klasse wird wieder abgenommen, damit derselbe Riss
   * beim naechsten Anlass erneut schnappen kann. */
  function riss(el) {
    if (!el || bewegungReduziert) return;
    el.classList.remove("eos-riss");
    void el.offsetWidth;               // Neustart der Animation erzwingen
    el.classList.add("eos-riss");
    global.setTimeout(function () { el.classList.remove("eos-riss"); }, 220);
  }

  // ── Messung ────────────────────────────────────────────────────────────
  var horcher = [];          // alle, die eine neue Messung sehen wollen
  var tokenGeber = null;     // liefert das Clerk-Token; erst nach Clerk.load da

  function melde(art, daten) {
    horcher.forEach(function (fn) {
      try { fn(art, daten); } catch (e) { console.error("Schale-Horcher:", e); }
    });
  }

  async function messeZustand() {
    var bereit = null, grund = null;
    try {
      var r = await fetch("/readyz", { cache: "no-store" });
      var j = await r.json().catch(function () { return {}; });
      bereit = (r.status === 200 && j.status === "ready");
      grund = bereit ? "Laufzeit bereit" : "Laufzeit nicht bereit (HTTP " + r.status + ")";
    } catch (e) {
      // Kein Zustand ist kein schlechter Zustand. Ohne Grund kein volles Licht.
      setzeSignal({ wert: 0, grund: null });
      melde("zustand", { bereit: null, ungelesen: undefined });
      return;
    }
    setzeSignal({ wert: bereit ? 1 : -1, grund: grund, quelle: "/readyz" });

    var ungelesen = await holeUngelesen();
    setzeMailZahl(ungelesen);
    melde("zustand", { bereit: bereit, grund: grund, ungelesen: ungelesen });
  }

  /* Das Einzige, was diese Oberflaeche noch aus /api/zustand liest: die Zahl
   * ungelesener Mails. Der Weg ist Clerk-geschuetzt. Solange niemand angemeldet
   * ist -- oder solange der Weg gar nicht existiert -- gibt es hier undefined,
   * und die Zahl bleibt weg. Ein 404 ist kein Grund, eine Null zu behaupten.
   * Deutscher wie englischer Name werden akzeptiert; geraten wird nichts. */
  async function holeUngelesen() {
    if (!tokenGeber) return undefined;
    try {
      var token = await tokenGeber();
      if (!token) return undefined;
      var r = await fetch("/api/zustand", {
        cache: "no-store",
        headers: { Authorization: "Bearer " + token }
      });
      if (!r.ok) return undefined;
      var d = await r.json();
      var namen = ["ungelesen", "ungelesene_mails", "unread"];
      for (var i = 0; i < namen.length; i++) {
        var v = d[namen[i]];
        if (typeof v === "number" && isFinite(v)) return v;
      }
      return undefined;
    } catch (e) { return undefined; }
  }

  var mailZahlEl = null, letzteMailZahl = null;
  function setzeMailZahl(n) {
    if (!mailZahlEl) return;
    if (typeof n !== "number") {
      // Kein Weg, keine Antwort -> gar keine Zahl. Eine 0 hier waere eine
      // Behauptung ueber ein Postfach, das wir nie gelesen haben.
      mailZahlEl.hidden = true;
      mailZahlEl.textContent = "";
      return;
    }
    mailZahlEl.hidden = (n <= 0);
    mailZahlEl.textContent = String(n);
    mailZahlEl.setAttribute("aria-label", n + " ungelesene Mails");
    if (letzteMailZahl !== null && n > letzteMailZahl) {
      riss(mailZahlEl);                       // neue Mail ist ein echter Wechsel
      melde("neue-mail", { ungelesen: n, vorher: letzteMailZahl });
    }
    letzteMailZahl = n;
  }

  // ── Aufbau der Leiste ──────────────────────────────────────────────────
  function aktiverWeg() {
    var p = location.pathname.replace(/\/+$/, "") || "/";
    var treffer = "/";
    WEGE.forEach(function (w) {
      if (w.pfad === "/") return;
      if (p === w.pfad || p.indexOf(w.pfad + "/") === 0) treffer = w.pfad;
    });
    return treffer;
  }

  function baue() {
    var kopf = doc.getElementById("entityos-schale");
    if (!kopf) {
      // Defensiv: eine Seite ohne Leiste waere eine Seite ohne Ausweg.
      kopf = doc.createElement("header");
      kopf.id = "entityos-schale";
      doc.body.insertBefore(kopf, doc.body.firstChild);
    }
    kopf.setAttribute("role", "banner");

    var marke = doc.createElement("a");
    marke.className = "eos-marke";
    marke.href = "/";
    marke.innerHTML = '<span class="eos-marke-zeichen" aria-hidden="true">▚</span>' +
                      '<span class="eos-marke-wort">entity<span class="eos-marke-os">OS</span></span>';
    kopf.appendChild(marke);

    var nav = doc.createElement("nav");
    nav.className = "eos-nav";
    nav.setAttribute("aria-label", "Bereiche");
    var aktiv = aktiverWeg();

    WEGE.forEach(function (w) {
      var a = doc.createElement("a");
      a.className = "eos-punkt";
      a.href = w.pfad;
      a.innerHTML =
        '<svg class="eos-punkt-symbol" width="15" height="15" viewBox="0 0 16 16" ' +
        'fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true">' +
        SYMBOLE[w.symbol] + '</svg>' +
        '<span class="eos-punkt-wort">' + w.wort + '</span>' +
        '<span class="eos-punkt-kurz">' + w.kurz + '</span>';
      if (w.pfad === aktiv) a.setAttribute("aria-current", "page");
      if (w.pfad === "/postfach") {
        mailZahlEl = doc.createElement("span");
        mailZahlEl.className = "eos-zahl";
        mailZahlEl.hidden = true;
        a.appendChild(mailZahlEl);
      }
      // Wechsel duerfen reissen -- also reisst es beim Zeigen, beim Fokussieren
      // und beim Klicken. Nicht dauernd, sondern genau im Moment des Wechsels.
      a.addEventListener("mouseenter", function () { riss(a); });
      a.addEventListener("focus", function () { riss(a); });
      a.addEventListener("click", function () { riss(kopf); });
      nav.appendChild(a);
    });
    kopf.appendChild(nav);

    var rechts = doc.createElement("div");
    rechts.className = "eos-rechts";
    status.el = doc.createElement("span");
    status.el.className = "eos-status";
    status.el.setAttribute("role", "img");
    status.el.title = "Zustand wird gemessen …";
    status.el.setAttribute("aria-label", "Zustand wird gemessen");
    rechts.appendChild(status.el);
    var nutzer = doc.createElement("div");
    nutzer.className = "eos-nutzer";
    nutzer.id = "eos-nutzer";
    rechts.appendChild(nutzer);
    kopf.appendChild(rechts);

    return marke;
  }

  // ── Bootsequenz ────────────────────────────────────────────────────────
  /* Einmal je Seitenaufruf, ~700 ms: eine Scanline wischt durch und die
   * Wortmarke rastet aus Zeichenrauschen ein -- auf genau die Schreibweise
   * entityOS, Zeichen fuer Zeichen von links. Sie darf nichts verzoegern:
   * alles ist schon da und bedienbar, waehrend sie laeuft. */
  function boot(marke) {
    if (bewegungReduziert) return;
    var linie = doc.createElement("div");
    linie.className = "eos-scanline";
    doc.body.appendChild(linie);
    global.setTimeout(function () { linie.remove(); }, 800);

    var wortEl = marke.querySelector(".eos-marke-wort");
    if (!wortEl) return;
    var rausch = "01<>/#";
    var start = performance.now(), dauer = 620;
    // Waehrend des Rauschens steht schlichter Text drin; erst am Ende kehrt die
    // Auszeichnung zurueck, damit das OS beim Einrasten seine Farbe bekommt.
    var fertig = 'entity<span class="eos-marke-os">OS</span>';
    wortEl.classList.add("eos-rauschen");
    (function schritt(jetzt) {
      var t = Math.min(1, (jetzt - start) / dauer);
      var fest = Math.floor(t * MARKE.length);
      var aus = "";
      for (var i = 0; i < MARKE.length; i++) {
        aus += (i < fest) ? MARKE[i] : rausch[(Math.random() * rausch.length) | 0];
      }
      wortEl.textContent = aus;
      if (t < 1) global.requestAnimationFrame(schritt);
      else { wortEl.innerHTML = fertig; wortEl.classList.remove("eos-rauschen"); }
    })(start);
  }

  // ── Takt ───────────────────────────────────────────────────────────────
  /* Im verborgenen Reiter wird nicht gemessen. Eine Messung, die niemand sieht,
   * kostet den Wirt trotzdem -- und /readyz kostet ihn wirklich etwas. */
  function starteTakt() {
    var timer = null;
    function an() {
      if (timer) return;
      messeZustand();
      timer = global.setInterval(messeZustand, ZUSTAND_TAKT);
    }
    function aus() { global.clearInterval(timer); timer = null; }
    doc.addEventListener("visibilitychange", function () {
      if (doc.visibilityState === "hidden") aus(); else an();
    });
    an();
  }

  // ── Oeffentliche Kante ─────────────────────────────────────────────────
  var EntityOS = {
    /* Die Seite ruft das auf, SOBALD Clerk geladen und jemand angemeldet ist.
     * Die Schale pollt nicht selbst auf window.Clerk herum -- das waere ein
     * Ratespiel um einen Zustand, den die Seite sicher weiss. */
    anmeldungBereit: function (geber) {
      tokenGeber = geber;
      var ziel = doc.getElementById("eos-nutzer");
      if (ziel && global.Clerk && global.Clerk.mountUserButton && !ziel.childElementCount) {
        try { global.Clerk.mountUserButton(ziel); } catch (e) { console.error("UserButton:", e); }
      }
      messeZustand();
    },
    beiMessung: function (fn) { horcher.push(fn); },
    riss: riss,
    signalTon: signalTon,
    marke: MARKE,
    bewegungReduziert: bewegungReduziert
  };
  global.EntityOS = EntityOS;

  function los() {
    var marke = baue();
    boot(marke);
    starteTakt();
  }
  if (doc.readyState === "loading") doc.addEventListener("DOMContentLoaded", los);
  else los();
})(window);

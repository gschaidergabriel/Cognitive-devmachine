/* Die Systeme-Bubble: welche Maschinen per Tailscale verbunden sind, ob sie
 * online sind, ihre wichtigsten Hardware-Stats und wie viel Speicher frei/belegt
 * ist -- live. Seit 19.08. mit einer zweiten Ansicht "Dienste": alle EntityOS-
 * Prozesse als Ein-Wort-Liste mit Lampe (gruen an / rot aus).
 *
 * Gabriel 19.08.: "neben dem chatinterface eine bubble links außen die aus- und
 * einklappen kann ... zeigt welche systeme verbunden sind via tailscale (vps,
 * andreas pc, mein pc), ob sie online sind, die wichtigsten hardware stats und
 * wie viel speicher jeweils frei und belegt ist, alles live aber schön conveniant
 * und einfach zu lesen. wenn man sie ausklappt soll der chat schmaler werden."
 *
 * Zero lebt auf dem VPS und greift per Tailscale auf die Rechner zu -- die Bubble
 * macht genau dieses Nervensystem sichtbar. Daten kommen von /api/systeme (der
 * Host-Sammler systemwacht schreibt sie im 15s-Takt, seit 19.08. inkl. "dienste").
 * Eingeklappt bleiben die drei Status-Punkte live, damit man auch zu sieht, wer
 * erreichbar ist.
 *
 * Gabriel 19.08. (2): manuelle Steuerung + Eigner-Feedback -- der Dienste-Tab ist
 * jetzt Task-Manager-artig: ein eigener Immunsystem-Schalter oben, darunter
 * animierte VPS-Leistungsgraphen (Client-seitiger Ringpuffer der Polls, kein
 * Backend-Verlauf), darunter die steuerbaren Dienste mit ▶/⏹/⟳-Knoepfen +
 * ausklappbarer Erklaerung, ganz unten ein Immunsystem-Log. Die Bubble wird im
 * Dienste-Tab breiter (Task-Manager braucht mehr Platz). Jede Aktion geht ueber
 * POST /api/dienst-steuern mit dem Clerk-Token -- dieses Skript fuehrt selbst
 * NICHTS aus, es fragt nur an; der Host-Ausfuehrer entscheidet (feste Whitelist).
 */
(function () {
  "use strict";

  var AUF_TAKT = 6000;   // ausgeklappt: haeufig, es soll sich live anfuehlen
  var ZU_TAKT  = 16000;  // eingeklappt: die drei Punkte reichen, sparsam pollen
  var GRAPH_PUFFER = 60; // ~6 Minuten Verlauf bei 6s-Takt
  var tokenHol = null, timer = 0, offen = false, ersterZug = true;
  var ansicht = "systeme";   // "systeme" (Maschinen) oder "dienste"
  var REDUCE = false;
  try { REDUCE = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) {}

  // Rollender Verlauf der VPS-Werte fuer die Graphen -- rein clientseitig,
  // kein Backend-Verlauf noetig; wird bei jedem Poll um einen Wert erweitert.
  var vpsVerlauf = { cpu: [], ram: [], disk: [] };
  // welche Dienst-Zeilen gerade aufgeklappt sind (ueberlebt einen Redraw)
  var offeneErklaerung = {};
  var aktionLaeuft = {};   // dienstname -> true waehrend eine Aktion unterwegs ist

  // ── DOM einmal bauen ────────────────────────────────────────────────────
  var panel = document.getElementById("systeme-panel");
  if (!panel) return;
  var griff    = panel.querySelector("#systeme-griff");
  var punkte   = panel.querySelector("#systeme-griff-punkte");
  var liste    = panel.querySelector("#systeme-liste");
  var dienste  = panel.querySelector("#systeme-dienste");
  var segBtns  = Array.prototype.slice.call(panel.querySelectorAll(".sys-seg"));
  var fuss     = panel.querySelector("#systeme-fuss");
  var zuBtn    = panel.querySelector("#systeme-zu");

  var immunKnopf   = panel.querySelector("#dienste-immun-knopf");
  var immunHinweis = panel.querySelector("#dienste-immun-hinweis");
  var immunLogEl   = panel.querySelector("#dienste-immun-log");
  var immunLogText = panel.querySelector("#dienste-immun-log-inhalt");
  var dienstListeWrap = panel.querySelector("#dienste-liste-wrap");
  var graphCanvases = Array.prototype.slice.call(panel.querySelectorAll(".dg-canvas"));
  var graphWerte = {};
  Array.prototype.slice.call(panel.querySelectorAll("[data-metrik-wert]")).forEach(function (el) {
    graphWerte[el.getAttribute("data-metrik-wert")] = el;
  });

  function breiteAktualisieren() {
    // Task-Manager-Optik braucht mehr Platz -- nur wenn offen UND im
    // Dienste-Tab; die CSS-Variable --sys-w wird dann auf Body-Ebene
    // ueberschrieben, jeder width/min-width/left-Wert zieht automatisch mit.
    document.body.classList.toggle("systeme-dienste-breit", offen && ansicht === "dienste");
  }

  function auf(state) {
    offen = state;
    panel.classList.toggle("auf", offen);
    panel.classList.toggle("zu", !offen);
    document.body.classList.toggle("systeme-auf", offen);   // laesst den Chat schmaler werden
    griff.setAttribute("aria-expanded", offen ? "true" : "false");
    try { localStorage.setItem("systeme-offen", offen ? "1" : "0"); } catch (e) {}
    breiteAktualisieren();
    planen();                     // Takt an den Zustand anpassen + sofort holen
  }
  griff.addEventListener("click", function () { auf(!offen); });
  if (zuBtn) zuBtn.addEventListener("click", function () { auf(false); });
  // ⭐ Handy-Overlay (2026-08-19): auf dem Handy legt sich die Bubble ueber den
  // Chat statt ihn schmaler zu machen (siehe index.html, --sys-w:100vw unter
  // 640px) -- der abgedunkelte Schirm dahinter ist dann der Schliess-Reflex,
  // denselben wie bei jedem Bottom-Sheet/Modal. Auf dem Desktop ist der Schirm
  // unsichtbar UND per CSS unklickbar (pointer-events:none), dieser Handler
  // feuert dort also nie.
  var scrim = document.getElementById("systeme-scrim");
  if (scrim) scrim.addEventListener("click", function () { auf(false); });

  // ── Ansicht wechseln: Maschinen <-> Dienste ─────────────────────────────
  function ansichtSetzen(a) {
    ansicht = (a === "dienste") ? "dienste" : "systeme";
    segBtns.forEach(function (b) {
      var aktiv = b.getAttribute("data-ansicht") === ansicht;
      b.classList.toggle("an", aktiv);
      b.setAttribute("aria-selected", aktiv ? "true" : "false");
    });
    // ⭐ Bugfix 19.08.: NUR das hidden-Attribut setzen genuegte nicht (eine ID-
    // Regel mit display:flex schlug die UA [hidden]-Regel) -- jetzt gibt es
    // zusaetzlich eine explizite [hidden]{display:none!important}-Regel in
    // index.html, die beiden hier bleiben aber die Quelle der Wahrheit.
    if (liste)   liste.hidden   = ansicht !== "systeme";
    if (dienste) dienste.hidden = ansicht !== "dienste";
    try { localStorage.setItem("systeme-ansicht", ansicht); } catch (e) {}
    breiteAktualisieren();
  }
  segBtns.forEach(function (b) {
    b.addEventListener("click", function () { ansichtSetzen(b.getAttribute("data-ansicht")); });
  });

  // ── Zahlenaufbereitung, damit es "einfach zu lesen" ist ─────────────────
  function klasse(pct) { return pct >= 90 ? "krit" : pct >= 70 ? "warn" : "gut"; }
  function balken(pct, text) {
    return '<div class="sys-bar"><span class="sys-fill ' + klasse(pct) +
           '" style="width:' + Math.max(2, Math.min(100, pct)) + '%"></span></div>' +
           '<span class="sys-wert">' + text + '</span>';
  }
  function zeile(label, pct, text) {
    return '<div class="sys-metrik"><span class="sys-lbl">' + label + '</span>' +
           balken(pct, text) + '</div>';
  }

  function karte(s) {
    var status = !s.online ? "offline" : (s.erreichbar ? "online" : "erreichbar-nein");
    var h = '<div class="sys-karte ' + status + '">';
    h += '<div class="sys-kopf">' +
           '<span class="sys-dot ' + status + '" title="' + (s.online ? "online" : "offline") + '"></span>' +
           '<span class="sys-name">' + s.name + '</span>' +
           '<span class="sys-rolle">' + (s.rolle || "") + '</span></div>';
    if (s.online && s.erreichbar && s.cpu) {
      h += zeile("CPU",  s.cpu.pct,  s.cpu.pct + "% · load " + s.cpu.last1 + " · " + s.cpu.kerne + " K");
      h += zeile("RAM",  s.ram.pct,  s.ram.belegt + " / " + s.ram.gesamt + " " + s.ram.einheit);
      h += zeile("Disk", s.disk.pct, s.disk.belegt + " / " + s.disk.gesamt + " " + s.disk.einheit +
                                     " · frei " + s.disk.frei);
    } else {
      h += '<div class="sys-hinweis">' +
           (s.online ? (s.hinweis || "keine Stats") : "offline") + '</div>';
    }
    h += '</div>';
    return h;
  }

  function punktReihe(systeme) {
    // Eingeklappt: ein Punkt je Maschine, Farbe = Status. Das ist der ganze
    // Sinn der geschlossenen Bubble: auf einen Blick sehen, wer da ist.
    return systeme.map(function (s) {
      var k = !s.online ? "offline" : (s.erreichbar ? "online" : "erreichbar-nein");
      return '<span class="sys-dot ' + k + '" title="' + s.name + ": " +
             (s.online ? (s.erreichbar ? "online" : "online, keine Stats") : "offline") + '"></span>';
    }).join("");
  }

  // ── VPS-Leistungsgraphen: Task-Manager-Stil, Client-Ringpuffer ──────────
  function graphSchieben(metrik, pct) {
    var puf = vpsVerlauf[metrik];
    if (!puf) return;
    puf.push(typeof pct === "number" ? pct : null);
    while (puf.length > GRAPH_PUFFER) puf.shift();
  }

  function graphZeichnen(canvas, puf) {
    var w = canvas.clientWidth || 300, h = canvas.clientHeight || 34;
    var dpr = window.devicePixelRatio || 1;
    if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
    }
    var ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    var werte = puf.filter(function (v) { return typeof v === "number"; });
    if (!werte.length) return;
    var stil = getComputedStyle(canvas);
    var signal = stil.getPropertyValue("--signal").trim() || "#39d98a";
    var n = puf.length;
    var stepX = n > 1 ? w / (n - 1) : w;
    ctx.beginPath();
    var begonnen = false;
    var punkte = [];
    for (var i = 0; i < n; i++) {
      var v = puf[i];
      if (typeof v !== "number") continue;
      var x = i * stepX;
      var y = h - (Math.max(0, Math.min(100, v)) / 100) * (h - 3) - 1.5;
      punkte.push([x, y]);
      if (!begonnen) { ctx.moveTo(x, y); begonnen = true; } else { ctx.lineTo(x, y); }
    }
    ctx.strokeStyle = signal;
    ctx.lineWidth = 1.6;
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    ctx.stroke();
    if (punkte.length > 1) {
      ctx.lineTo(punkte[punkte.length - 1][0], h);
      ctx.lineTo(punkte[0][0], h);
      ctx.closePath();
      ctx.fillStyle = "color-mix(in srgb, " + signal + " 20%, transparent)";
      try { ctx.fill(); } catch (e) { /* aeltere Browser ohne color-mix() im Canvas */ }
    }
  }

  function graphenZeichnen() {
    if (!graphCanvases.length) return;
    graphCanvases.forEach(function (c) {
      var m = c.getAttribute("data-metrik");
      graphZeichnen(c, vpsVerlauf[m] || []);
    });
  }

  function vpsAktualisieren(vps) {
    var hat = vps && vps.online && vps.erreichbar && vps.cpu && vps.ram && vps.disk;
    graphSchieben("cpu",  hat ? vps.cpu.pct  : null);
    graphSchieben("ram",  hat ? vps.ram.pct  : null);
    graphSchieben("disk", hat ? vps.disk.pct : null);
    if (graphWerte.cpu)  graphWerte.cpu.textContent  = hat ? (vps.cpu.pct + "%")  : "–";
    if (graphWerte.ram)  graphWerte.ram.textContent  = hat ? (vps.ram.pct + "%")  : "–";
    if (graphWerte.disk) graphWerte.disk.textContent = hat ? (vps.disk.pct + "%") : "–";
    // Nur zeichnen, wenn der Dienste-Tab gerade sichtbar ist -- kein Sinn,
    // unsichtbare Canvases zu rendern, und respektiert nebenbei
    // prefers-reduced-motion (kein rAF-Loop, nur Redraw je Poll ohnehin).
    if (ansicht === "dienste" && dienste && !dienste.hidden) graphenZeichnen();
  }

  // ── Dienste: Task-Manager-Zeile mit Lampe + Knoepfen + Erklaerung ───────
  function escHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function dienstKnoepfeHtml(d) {
    if (!d.steuerbar) return "";
    var busy = !!aktionLaeuft[d.name];
    var dis = busy ? " disabled" : "";
    return '<span class="td-knoepfe">' +
      (d.kritisch ? '<span class="td-badge-kritisch">kritisch</span>' : "") +
      '<button type="button" class="dienst-knopf" data-aktion="start" title="an"' + dis + '>&#9654;</button>' +
      '<button type="button" class="dienst-knopf" data-aktion="stop" title="aus"' + dis + '>&#9209;</button>' +
      '<button type="button" class="dienst-knopf" data-aktion="restart" title="neu"' + dis + '>&#8635;</button>' +
      '<span class="td-spinner"' + (busy ? "" : " hidden") + '>…</span>' +
      '</span>';
  }

  function dienstZeileHtml(d) {
    var an = !!d.an;
    var offenGeklappt = !!offeneErklaerung[d.name];
    return '<div class="td-zeile' + (offenGeklappt ? " offen" : "") + '" data-dienst="' + escHtml(d.name) + '">' +
      '<div class="td-hauptzeile" role="button" tabindex="0" aria-expanded="' + (offenGeklappt ? "true" : "false") + '">' +
        '<span class="sys-dienst-dot ' + (an ? "an" : "aus") + '" title="' + (an ? "an" : "aus") + '"></span>' +
        '<span class="sys-dienst-name">' + escHtml(d.name) + '</span>' +
        '<span class="sys-dienst-status">' + (an ? "an" : "aus") + '</span>' +
        dienstKnoepfeHtml(d) +
        '<span class="td-chevron">&rsaquo;</span>' +
      '</div>' +
      '<div class="td-erklaerung"><p>' + escHtml(d.beschreibung || "Keine Beschreibung.") + '</p></div>' +
    '</div>';
  }

  function erklaerungAnwenden(zeileEl) {
    var wrap = zeileEl.querySelector(".td-erklaerung");
    var offenGeklappt = zeileEl.classList.contains("offen");
    if (!wrap) return;
    if (offenGeklappt) {
      wrap.style.maxHeight = wrap.scrollHeight + "px";
    } else {
      wrap.style.maxHeight = "0px";
    }
  }

  function dienste_zeichnen(liste_d) {
    if (!dienstListeWrap) return;
    var d = liste_d || [];
    dienstListeWrap.innerHTML = d.length ? d.map(dienstZeileHtml).join("")
                                          : '<div class="sys-hinweis">keine Daten</div>';
    // Erklaerungs-Hoehe nach dem Einfuegen setzen (scrollHeight erst dann bekannt)
    Array.prototype.slice.call(dienstListeWrap.querySelectorAll(".td-zeile")).forEach(function (zeileEl) {
      if (REDUCE) {
        var wrap = zeileEl.querySelector(".td-erklaerung");
        if (wrap) wrap.style.transition = "none";
      }
      erklaerungAnwenden(zeileEl);
    });
  }

  // Klick-Delegation: Zeile auf/zu, Knoepfe loesen Aktionen aus.
  if (dienstListeWrap) {
    dienstListeWrap.addEventListener("click", function (e) {
      var knopf = e.target.closest && e.target.closest(".dienst-knopf");
      var zeileEl = e.target.closest && e.target.closest(".td-zeile");
      if (!zeileEl) return;
      var dienstName = zeileEl.getAttribute("data-dienst");
      if (knopf) {
        e.stopPropagation();
        var aktion = knopf.getAttribute("data-aktion");
        var kritisch = !!zeileEl.querySelector(".td-badge-kritisch");
        if (aktion === "stop" && kritisch) {
          var ok = window.confirm(
            '"' + dienstName + '" ist KRITISCH -- ohne ihn ist die Seite nicht erreichbar.\n' +
            "Wirklich stoppen?");
          if (!ok) return;
        }
        dienstAktionAusfuehren(dienstName, aktion);
        return;
      }
      // Zeile selbst geklickt -> Erklaerung auf/zu
      offeneErklaerung[dienstName] = !offeneErklaerung[dienstName];
      zeileEl.classList.toggle("offen", !!offeneErklaerung[dienstName]);
      zeileEl.querySelector(".td-hauptzeile").setAttribute(
        "aria-expanded", offeneErklaerung[dienstName] ? "true" : "false");
      erklaerungAnwenden(zeileEl);
    });
    dienstListeWrap.addEventListener("keydown", function (e) {
      if (e.key !== "Enter" && e.key !== " ") return;
      var haupt = e.target.closest && e.target.closest(".td-hauptzeile");
      if (!haupt) return;
      e.preventDefault();
      haupt.click();
    });
  }

  // ── Aktionen ausloesen: POST /api/dienst-steuern, dann kurz warten und
  // einen zusaetzlichen Poll ausloesen -- "die Lampe aktualisiert sich". ────
  async function dienstAktionAusfuehren(dienstName, aktion) {
    if (!tokenHol || aktionLaeuft[dienstName]) return;
    aktionLaeuft[dienstName] = true;
    dienste_zeichnen(letzteDienste);   // Knoepfe sofort deaktivieren + Spinner
    try {
      var token = await tokenHol();
      if (!token) return;
      await fetch("/api/dienst-steuern", {
        method: "POST",
        headers: { "Authorization": "Bearer " + token, "Content-Type": "application/json" },
        body: JSON.stringify({ dienst: dienstName, aktion: aktion }),
      });
    } catch (e) { /* stumm -- der naechste Poll zeigt die Wahrheit */ }
    setTimeout(function () {
      aktionLaeuft[dienstName] = false;
      holen();   // sofortiger Nach-Poll, damit es sich reaktionsschnell anfuehlt
    }, 2200);
  }

  // ── Immunsystem-Schalter (eigener Schalter, kein Dienste-Zeileneintrag) ─
  var immunAktiv = false;
  function immunZeichnen(immun) {
    if (!immunKnopf) return;
    immunAktiv = !!(immun && immun.an);
    var vorhanden = !immun || immun.vorhanden !== false;
    immunKnopf.classList.toggle("an", immunAktiv);
    immunKnopf.classList.toggle("aus", !immunAktiv);
    immunKnopf.setAttribute("aria-pressed", immunAktiv ? "true" : "false");
    immunKnopf.disabled = !!aktionLaeuft["__immunsystem__"];
    immunKnopf.textContent = aktionLaeuft["__immunsystem__"] ? "…" : (immunAktiv ? "an" : "aus");
    if (immunHinweis) immunHinweis.hidden = vorhanden !== false ? true : false;
  }
  if (immunKnopf) {
    immunKnopf.addEventListener("click", async function () {
      if (aktionLaeuft["__immunsystem__"]) return;
      aktionLaeuft["__immunsystem__"] = true;
      immunZeichnen({ an: immunAktiv });
      var ziel = immunAktiv ? "stop" : "start";
      try {
        if (!tokenHol) return;
        var token = await tokenHol();
        if (!token) return;
        await fetch("/api/dienst-steuern", {
          method: "POST",
          headers: { "Authorization": "Bearer " + token, "Content-Type": "application/json" },
          body: JSON.stringify({ dienst: "immunsystem", aktion: ziel }),
        });
      } catch (e) { /* stumm */ }
      setTimeout(function () {
        aktionLaeuft["__immunsystem__"] = false;
        holen();
      }, 2200);
    });
  }

  function immunLogZeichnen(zeilen) {
    if (!immunLogText) return;
    var arr = Array.isArray(zeilen) ? zeilen : [];
    immunLogText.textContent = arr.length ? arr.join("\n") : "(keine Eintraege)";
  }

  var letzteDienste = [];

  function zeichne(doc) {
    var sys = (doc && doc.systeme) || [];
    if (punkte) punkte.innerHTML = punktReihe(sys);
    if (liste)  liste.innerHTML  = sys.map(karte).join("");
    letzteDienste = (doc && doc.dienste) || [];
    dienste_zeichnen(letzteDienste);
    var vps = sys.filter(function (s) { return s.id === "vps"; })[0] || sys[0];
    vpsAktualisieren(vps);
    immunZeichnen(doc && doc.immunsystem);
    immunLogZeichnen(doc && doc.immune_log);
    if (fuss) {
      var a = doc && doc.alter_s;
      var frisch = (a === 0 || a) ? ("aktualisiert vor " + a + "s") : "keine Verbindung";
      var veraltet = (a === null || a === undefined || a > 60);
      fuss.innerHTML = '<span class="sys-live ' + (veraltet ? "alt" : "") + '"></span>' +
                       '<span>' + frisch + " · Tailscale</span>";
    }
    var oncount = sys.filter(function (s) { return s.online; }).length;
    griff.setAttribute("aria-label", "Verbundene Systeme (" + oncount + "/" + sys.length + " online)");
  }

  // ── Holen ───────────────────────────────────────────────────────────────
  async function holen() {
    if (!tokenHol) return;
    var token;
    try { token = await tokenHol(); } catch (e) { return; }
    if (!token) return;
    try {
      var r = await fetch("/api/systeme", { headers: { Authorization: "Bearer " + token } });
      if (!r.ok) return;
      zeichne(await r.json());
    } catch (e) { /* stumm -- die Bubble ist kein kritischer Pfad */ }
  }

  function planen() {
    if (timer) clearInterval(timer);
    holen();                                  // sofort, kein Warten auf den ersten Takt
    timer = setInterval(holen, offen ? AUF_TAKT : ZU_TAKT);
  }

  // ── Start: wird nach dem Login vom Chat aufgerufen ──────────────────────
  window.SYSTEME = {
    start: function (getToken) {
      tokenHol = getToken;
      if (!ersterZug) return;
      ersterZug = false;
      var wollen_offen = false;
      try { wollen_offen = localStorage.getItem("systeme-offen") === "1"; } catch (e) {}
      var wollen_ansicht = "systeme";
      try { wollen_ansicht = localStorage.getItem("systeme-ansicht") || "systeme"; } catch (e) {}
      ansichtSetzen(wollen_ansicht);
      auf(wollen_offen);                       // stellt Takt ein + holt sofort
      document.addEventListener("visibilitychange", function () {
        if (!document.hidden) holen();         // beim Zurueckkommen sofort auffrischen
      });
      window.addEventListener("resize", function () {
        if (ansicht === "dienste" && dienste && !dienste.hidden) graphenZeichnen();
      });
    }
  };
})();

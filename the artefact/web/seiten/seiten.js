/* Die Seitenuebersicht.
 *
 * ⭐ Uebernommen aus der bestehenden Hosting-Ansicht in agentforge, nicht
 * nachgebaut: dieselben Kennzahlen (Besuche/Unikate in vier Fenstern,
 * Funkenlinie ueber 30 Tage, Verweise, Pfade, Seitengewicht), dieselbe Quelle.
 * Weggelassen sind die frank.ink-Funktionen, die hier keinen Sinn ergeben --
 * Workspace, Slug umbenennen, Offline nehmen, Werbung.
 *
 * ⭐ Umbau 2026-08-19 (Eigner): kompakte Bubbles in einem Raster statt einer
 * endlosen aufgeklappten Liste. Eingeklappt zeigt eine Bubble Name, Host-
 * Abzeichen, URL, Besuche 30 Tage und die Funkenlinie. Ein Klick klappt die
 * Details auf (Akkordeon). Zwei Knoepfe je Bubble: im Browser oeffnen (neuer
 * Tab) und URL kopieren (mit sichtbarer Bestaetigung).
 *
 * Bewegung folgt dem Hausgesetz aus schale.js: der Riss (EntityOS.riss) ist
 * der EINE Effekt des Hauses und wird hier WIEDERVERWENDET, nicht neu erfunden
 * -- er feuert bei echten Wechseln (Hover auf eine Bubble, Auf-/Zuklappen,
 * erfolgreiches Kopieren), nicht dauerhaft.
 *
 * ⚠️ Zwei Dinge, die aus frueheren Fehlern dieses Projekts stammen:
 *  - LEER IST EIN ZUSTAND, kein leerer Bildschirm. "Nichts da" und
 *    "Laden fehlgeschlagen" muessen unterscheidbar bleiben.
 *  - Ladefehler werden ANGEZEIGT, nicht verschluckt.
 */
window.addEventListener('load', async () => {
  const fehlerEl = document.getElementById('sn-anmeldefehler');
  const lageEl = document.getElementById('sn-lage');
  const listeEl = document.getElementById('sn-liste');
  const leerEl = document.getElementById('sn-leer');

  const zeigeFehler = (t) => { fehlerEl.textContent = t; fehlerEl.hidden = false; };

  await Clerk.load();
  if (window.EntityOS) EntityOS.anmeldungBereit(() => Clerk.session.getToken());
  if (!Clerk.isSignedIn) { zeigeFehler('Nicht angemeldet — diese Übersicht braucht eine Anmeldung.'); return; }

  let token;
  try { token = await Clerk.session.getToken(); }
  catch { zeigeFehler('Anmeldung abgelaufen.'); return; }

  let d;
  try {
    const r = await fetch('/api/seiten', { headers: { Authorization: 'Bearer ' + token } });
    if (!r.ok) { zeigeFehler('Server antwortete ' + r.status); lageEl.textContent = ''; return; }
    d = await r.json();
  } catch (e) { zeigeFehler('Laden fehlgeschlagen: ' + (e && e.message || e)); return; }

  if (d.nicht_ermittelbar) { zeigeFehler('Nicht ermittelbar: ' + d.nicht_ermittelbar); lageEl.textContent = ''; return; }

  const seiten = d.seiten || [];
  const selbst = seiten.filter(s => s.hosting === 'selbst gehostet').length;
  // Das Alter des Abbilds steht dabei: die Zahlen stammen aus einem Auszug,
  // der alle 5 min erneuert wird, nicht aus der laufenden Plattformdatenbank.
  // Direktzugriff auf die Plattformdatenbank -- kein Abbild, kein Alter.
  const alt = d.abbild_alter_s;
  const altText = alt === 0 ? 'Live-Stand' : `Zahlen ${Math.round((alt || 0) / 60)} min alt`;
  lageEl.textContent = `${seiten.length} Seiten · ${selbst} selbst gehostet · `
    + `${seiten.length - selbst} extern · ${altText}`;
  if (alt != null && alt > 1800) lageEl.classList.add('sn-warn');

  if (!seiten.length) { leerEl.hidden = false; return; }

  const esc = (t) => String(t == null ? '' : t).replace(/[&<>"']/g,
    c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const kb = (b) => b == null ? '—' : (b > 1048576 ? (b / 1048576).toFixed(1) + ' MB'
                                                   : Math.round(b / 1024) + ' kB');
  const her = (s) => s == null ? '—' : (s < 3600 ? Math.round(s / 60) + ' min'
                    : s < 86400 ? (s / 3600).toFixed(1) + ' h' : Math.round(s / 86400) + ' d');

  // Kleine, sr-only Ansage der Kopiert-Bestaetigung -- die sichtbare
  // Bestaetigung sitzt am Knopf selbst (Haekchen), das hier ist nur fuer
  // Screenreader dieselbe Information.
  const anzeigeEl = document.createElement('p');
  anzeigeEl.className = 'sn-sr';
  anzeigeEl.setAttribute('aria-live', 'polite');
  document.body.appendChild(anzeigeEl);

  const svgPfeil = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" '
    + 'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    + '<path d="M4 6l4 4 4-4"/></svg>';
  const svgOeffnen = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" '
    + 'stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    + '<path d="M6.5 3h6.5v6.5"/><path d="M13 3 6.5 9.5"/><path d="M11 9v3.5a.5.5 0 0 1-.5.5H3a.5.5 0 0 1-.5-.5V4.5a.5.5 0 0 1 .5-.5H6.5"/></svg>';
  const svgKopieren = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" '
    + 'stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    + '<rect x="5.5" y="5.5" width="8" height="8" rx="1.3"/><path d="M3.5 10.5H3a.5.5 0 0 1-.5-.5V3a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 .5.5v.5"/></svg>';
  const svgHaken = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" '
    + 'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    + '<path d="M3.5 8.5l3 3 6-7"/></svg>';

  listeEl.innerHTML = seiten.map((s, i) => {
    const f = s.funken_30d || [];
    const max = Math.max(1, ...f);
    const funken = f.map((n, j) =>
      `<div class="sn-balken${j === f.length - 1 ? ' heute' : ''}" style="height:${Math.max(2, Math.round(n / max * 24))}px" title="${n}"></div>`).join('');
    const g = s.gewicht || {};
    const gewichtHtml = g.bytes
      ? `<ul>${Object.entries(g.bytes).map(([k, v]) => `<li><span>${k}</span><span>${kb(v)}</span></li>`).join('')}
         <li><span><b>gesamt</b></span><span><b>${kb(g.gesamt)}</b> in ${g.dateien} Dateien</span></li></ul>
         ${(g.groesste || []).length ? `<ul style="margin-top:6px">${g.groesste.map(x =>
           `<li><span>${esc(x.pfad)}</span><span>${kb(x.bytes)}</span></li>`).join('')}</ul>` : ''}`
      : `<p class="sn-matt">${esc(g.nicht_ermittelbar || 'nicht ermittelbar')}</p>`;
    const liste = (arr, a, b2) => (arr || []).length
      ? `<ul>${arr.map(x => `<li><span>${esc(x[a])}</span><span>${x[b2]}</span></li>`).join('')}</ul>`
      : '<p class="sn-matt">nichts in 30 Tagen</p>';
    const hauptAdresse = s.adressen[0];
    const detailId = `sn-detail-${i}`;
    const verzoegerung = Math.min(i * 35, 380);
    return `
    <article class="sn-karte" data-i="${i}" style="--sn-verzoegerung:${verzoegerung}ms">
      <div class="sn-kachel" role="button" tabindex="0" aria-expanded="false" aria-controls="${detailId}">
        <div class="sn-kachel-kopf">
          <span class="sn-marke ${s.hosting === 'selbst gehostet' ? 'sn-selbst' : 'sn-extern'}"
                title="${esc(s.hosting_begruendung)}">${esc(s.hosting)}</span>
          <span class="sn-name" title="${esc(s.name || s.slug)}">${esc(s.name || s.slug)}</span>
          <span class="sn-pfeil">${svgPfeil}</span>
        </div>
        <div class="sn-slug">${esc(s.slug)} · Konto ${s.konto}</div>
        <a class="sn-adresse" href="${esc(hauptAdresse)}" target="_blank" rel="noopener"
           title="${esc(hauptAdresse)}" onclick="event.stopPropagation()">${esc(hauptAdresse)}</a>
        <div class="sn-kachel-fuss">
          <div class="sn-funken" title="Besuche je Tag, 30 Tage">${funken}</div>
          ${/NICHT/.test(s.zaehlung || '')
            ? '<div class="sn-zahl"><b>—</b><span class="sn-warn">nicht gezählt</span></div>'
            : `<div class="sn-zahl"><b>${s.besuche.d30}</b><span>30 Tage · ${s.unikate.d30} Unikate</span></div>`}
        </div>
      </div>
      <div class="sn-akkordeon" id="sn-akk-${i}">
        <div class="sn-akkordeon-innen">
          <div class="sn-tief" id="${detailId}">
            <div class="sn-aktionen">
              <a class="sn-btn sn-btn-oeffnen" href="${esc(hauptAdresse)}" target="_blank" rel="noopener"
                 onclick="event.stopPropagation()">${svgOeffnen}<span>im Browser öffnen</span></a>
              <button type="button" class="sn-btn sn-btn-kopieren" data-url="${esc(hauptAdresse)}">
                ${svgKopieren}<span>URL kopieren</span></button>
            </div>
            <div class="sn-block"><h3>Besuche</h3>
              ${/NICHT/.test(s.zaehlung || '') ? `<p class="sn-warn" style="font-size:var(--s-13)">${esc(s.zaehlung)}</p>` : ''}
              <ul>
              <li><span>heute</span><span>${s.besuche.heute} · ${s.unikate.heute} Unikate</span></li>
              <li><span>7 Tage</span><span>${s.besuche.d7} · ${s.unikate.d7}</span></li>
              <li><span>30 Tage</span><span>${s.besuche.d30} · ${s.unikate.d30}</span></li>
              <li><span>gesamt</span><span>${s.besuche.gesamt} · ${s.unikate.gesamt}</span></li>
              <li><span>letzter Besuch</span><span>vor ${her(s.letzter_besuch_vor_s)}</span></li>
            </ul></div>
            <div class="sn-block"><h3>Woher</h3>${liste(s.verweise, 'woher', 'n')}</div>
            <div class="sn-block"><h3>Meistgerufen</h3>${liste(s.pfade, 'pfad', 'n')}</div>
            <div class="sn-block"><h3>Seitengewicht</h3>${gewichtHtml}</div>
            <div class="sn-block" style="grid-column:1/-1">
              <h3>Ausgeliefert von</h3><p class="sn-weg">${esc(s.ausgeliefert_von)}</p>
              <h3 style="margin-top:10px">So wird es geändert</h3>
              <p class="sn-weg ${/Ungeprueft|⚠️/.test(s.bearbeitung) ? 'sn-warn' : ''}">${esc(s.bearbeitung)}</p>
              ${s.adressen.length > 1 ? `<h3 style="margin-top:10px">Weitere Adressen</h3>
                <p class="sn-weg">${s.adressen.slice(1).map(a => esc(a)).join(' · ')}</p>` : ''}
            </div>
          </div>
        </div>
      </div>
    </article>`;
  }).join('');

  // ── Auf-/Zuklappen ──────────────────────────────────────────────────
  let hoverGerissen = new WeakSet();
  listeEl.querySelectorAll('.sn-karte').forEach(karte => {
    const kachel = karte.querySelector('.sn-kachel');
    const akkordeon = karte.querySelector('.sn-akkordeon');
    const um = () => {
      const offen = akkordeon.classList.toggle('sn-offen');
      kachel.setAttribute('aria-expanded', offen ? 'true' : 'false');
      if (window.EntityOS) EntityOS.riss(karte);
    };
    kachel.addEventListener('click', um);
    kachel.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); um(); }
    });
    // Der Riss ist der EINE Effekt des Hauses -- er feuert bei einem echten
    // Wechsel (hier: Aufmerksamkeit betritt die Bubble), nicht dauerhaft.
    karte.addEventListener('mouseenter', () => {
      if (window.EntityOS && !hoverGerissen.has(karte)) {
        EntityOS.riss(karte);
        hoverGerissen.add(karte);
        setTimeout(() => hoverGerissen.delete(karte), 600);
      }
    });
  });

  // ── URL kopieren ────────────────────────────────────────────────────
  listeEl.querySelectorAll('.sn-btn-kopieren').forEach(knopf => {
    knopf.addEventListener('click', async (e) => {
      e.stopPropagation();
      const url = knopf.getAttribute('data-url');
      let ok = false;
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(url);
          ok = true;
        }
      } catch (err) { ok = false; }
      if (!ok) {
        // Rueckfallweg fuer aeltere/unsichere Kontexte -- lieber ein
        // klassischer Trick als ein Knopf, der einfach nichts tut.
        try {
          const feld = document.createElement('textarea');
          feld.value = url; feld.style.position = 'fixed'; feld.style.opacity = '0';
          document.body.appendChild(feld); feld.select();
          ok = document.execCommand('copy');
          feld.remove();
        } catch (err) { ok = false; }
      }
      const beschriftung = knopf.querySelector('span');
      const vorherSvg = knopf.innerHTML;
      if (ok) {
        knopf.classList.add('sn-ok');
        knopf.innerHTML = svgHaken + `<span>kopiert</span>`;
        anzeigeEl.textContent = 'URL kopiert: ' + url;
        if (window.EntityOS) EntityOS.riss(knopf);
      } else {
        anzeigeEl.textContent = 'Kopieren fehlgeschlagen.';
        beschriftung.textContent = 'fehlgeschlagen';
      }
      setTimeout(() => {
        knopf.classList.remove('sn-ok');
        knopf.innerHTML = vorherSvg;
      }, 1600);
    });
  });
});

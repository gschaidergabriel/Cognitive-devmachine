/* Die Seitenuebersicht.
 *
 * ⭐ Uebernommen aus der bestehenden Hosting-Ansicht in agentforge, nicht
 * nachgebaut: dieselben Kennzahlen (Besuche/Unikate in vier Fenstern,
 * Funkenlinie ueber 30 Tage, Verweise, Pfade, Seitengewicht), dieselbe Quelle.
 * Weggelassen sind die frank.ink-Funktionen, die hier keinen Sinn ergeben --
 * Workspace, Slug umbenennen, Offline nehmen, Werbung.
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

  listeEl.innerHTML = seiten.map((s, i) => {
    const f = s.funken_30d || [];
    const max = Math.max(1, ...f);
    const funken = f.map((n, j) =>
      `<div class="sn-balken${j === f.length - 1 ? ' heute' : ''}" style="height:${Math.max(2, Math.round(n / max * 28))}px" title="${n}"></div>`).join('');
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
    return `
    <div class="sn-karte" data-i="${i}">
      <div class="sn-zeile" role="button" tabindex="0">
        <div>
          <div class="sn-name">${esc(s.name || s.slug)}</div>
          <div class="sn-slug">${esc(s.slug)} · Konto ${s.konto}</div>
        </div>
        <span class="sn-marke ${s.hosting === 'selbst gehostet' ? 'sn-selbst' : 'sn-extern'}"
              title="${esc(s.hosting_begruendung)}">${esc(s.hosting)}</span>
        <a class="sn-adresse" href="${esc(s.adressen[0])}" target="_blank" rel="noopener"
           onclick="event.stopPropagation()">${esc(s.adressen[0])}</a>
        <div class="sn-funken" title="Besuche je Tag, 30 Tage">${funken}</div>
        <div class="sn-zahl">${/NICHT/.test(s.zaehlung || '')
          ? '<b>—</b><span class="sn-warn">nicht gezählt</span>'
          : `<b>${s.besuche.d30}</b><span>30 Tage · ${s.unikate.d30} Unikate</span>`}</div>
      </div>
      <div class="sn-tief" hidden>
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
    </div>`;
  }).join('');

  listeEl.querySelectorAll('.sn-karte').forEach(k => {
    const zeile = k.querySelector('.sn-zeile');
    const tief = k.querySelector('.sn-tief');
    const um = () => { tief.hidden = !tief.hidden; };
    zeile.addEventListener('click', um);
    zeile.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); um(); }
    });
  });
});

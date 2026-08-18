/* Postfach — die Mailbox von EntityOS.
   ═══════════════════════════════════════════════════════════════════════
   Portiert aus der frank.ink-Mailbox (mail.js, 2144 Zeilen). Uebernommen
   wurde, was Gabriel und Andreas dort taeglich benutzt haben; herausgeflogen
   sind die Relikte: KI-Entwurf, Persona/Signatur, Freigabe-Warteschlange,
   Reputation, blocked-Liste und die zweisprachige Maschinerie. Diese
   Oberflaeche ist fest deutsch -- ein Sprachschalter, den nie jemand
   umgelegt hat, ist doppelter Code fuer null Nutzen.

   Ein Gesetz ueber allem: es werden NIE Mails erfunden. Antwortet ein Weg
   nicht, steht hier ein ehrlicher Fehlerzustand mit Grund und naechstem
   Schritt -- niemals eine Beispielmail. Eine Attrappe, die wie eine echte
   Mail aussieht, ist in diesem Projekt der schlimmste moegliche Fehler. */

(() => {
  'use strict';

  // ── Konstanten ────────────────────────────────────────────────────────
  const SEITE = 25;        // Mails je Seite -- wie im Vorbild
  const HOLGRENZE = 200;   // so viele holt der Server hoechstens am Stueck
  const PULS_MS = 60000;   // Ordnerzaehler nachschauen (echtes Nachzaehlen, kein Schaetzen)

  // Anzeigenamen der bekannten IMAP-Ordner. Was hier nicht steht, wird mit
  // seinem echten Namen angezeigt statt geraten.
  const ORDNERNAMEN = {
    'INBOX': 'Posteingang',
    'Sent': 'Gesendet',
    'Drafts': 'Entwürfe',
    'Junk': 'Spam',
    'Trash': 'Papierkorb',
    'Archive': 'Archiv',
    'Important': 'Wichtig',
    'All Mail': 'Alle Nachrichten',
  };
  const ORDNERREIHE = ['INBOX', 'Drafts', 'Sent', 'Junk', 'Trash', 'Archive', 'Important', 'All Mail'];

  // ── Zustand ───────────────────────────────────────────────────────────
  const z = {
    ordner: {},            // { name: {ungelesen, gesamt} } -- gezaehlt, nicht geschaetzt
    aktuellerOrdner: 'INBOX',
    mails: [],
    seite: 0,
    gewaehlt: null,        // globaler Index in z.mails
    offeneMail: null,      // vollstaendig geladene Mail
    suche: '',
    laedt: false,
    ansicht: 'liste',      // liste | lesen | verfassen
    bekannteIds: new Set(),// fuer die Riss-Erkennung: was war beim letzten Mal da?
    systempostfaecher: null,
    puls: null,
  };

  const $ = (id) => document.getElementById(id);

  // ── Kleine Helfer ─────────────────────────────────────────────────────
  const esc = (s) => String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

  // Der Server wird parallel gebaut. Deshalb wird jedes Feld unter beiden
  // plausiblen Namen gelesen -- deutsch (Hausstil) und der Name aus dem
  // Vorbild. Das ist keine Erfindung: fehlt beides, gilt der Wert als
  // unbekannt und wird als solcher gezeigt.
  const feld = (o, ...namen) => {
    for (const n of namen) if (o && o[n] !== undefined && o[n] !== null) return o[n];
    return undefined;
  };

  const ordnerName = (f) => ORDNERNAMEN[f] || String(f).replace('[Gmail]/', '');

  // Aus "Vorname Nachname <a@b.c>" den Anzeigenamen ziehen. Steht keiner da,
  // bleibt die Adresse stehen -- lieber technisch als falsch freundlich.
  const nameAus = (roh) => {
    const s = String(roh || '').trim();
    const m = s.match(/^(.+?)\s*<[^>]+>$/);
    if (m) return m[1].replace(/^["']|["']$/g, '').trim();
    return s || '(kein Absender)';
  };

  const adresseAus = (roh) => {
    const m = String(roh || '').match(/<([^>]+)>/);
    return (m ? m[1] : String(roh || '')).trim();
  };

  const groesse = (bytes) => {
    const b = Number(bytes);
    if (!Number.isFinite(b) || b < 0) return '';
    if (b < 1024) return b + ' B';
    if (b < 1024 * 1024) return (b / 1024).toFixed(0) + ' kB';
    return (b / 1048576).toFixed(1) + ' MB';
  };

  // Datum: nur formatieren, was wirklich da ist. Ein Zeitstempel wird relativ
  // gezeigt (naeher am Lesen), ein blosser Datumstext bleibt wie er kam.
  const datumKurz = (mail) => {
    const ts = feld(mail, 'zeitstempel', 'timestamp');
    if (typeof ts === 'number' && Number.isFinite(ts)) {
      const d = new Date(ts * 1000);
      const diffMs = Date.now() - d.getTime();
      const std = diffMs / 3600000;
      if (std < 1) return Math.max(1, Math.floor(diffMs / 60000)) + ' min';
      if (std < 24) return Math.floor(std) + ' h';
      if (std < 48) return 'gestern';
      if (std < 168) return d.toLocaleDateString('de-AT', { weekday: 'short' });
      return d.toLocaleDateString('de-AT', { day: 'numeric', month: 'short' });
    }
    return String(feld(mail, 'datum', 'date') || '');
  };

  const datumLang = (mail) => {
    const ts = feld(mail, 'zeitstempel', 'timestamp');
    if (typeof ts === 'number' && Number.isFinite(ts)) {
      return new Date(ts * 1000).toLocaleString('de-AT');
    }
    return String(feld(mail, 'datum', 'date') || '');
  };

  // ── Meldungen ─────────────────────────────────────────────────────────
  // Der Text sagt, was passiert IST, und benutzt dasselbe Wort wie der Knopf,
  // der es ausgeloest hat: "Senden" -> "Gesendet". Eine Aktion, die auf dem
  // Weg ihren Namen wechselt, kostet den Leser einen Denkschritt.
  let meldungsUhr = null;
  function melde(text, warnung) {
    const el = $('pf-meldung');
    if (!el) return;
    el.textContent = text;
    el.classList.toggle('pf-meldung-warn', !!warnung);
    el.hidden = false;
    if (meldungsUhr) clearTimeout(meldungsUhr);
    meldungsUhr = setTimeout(() => { el.hidden = true; }, warnung ? 7000 : 3500);
  }

  // ── Netz ──────────────────────────────────────────────────────────────
  // Jeder Fehler traegt einen Grund (technisch, fuer die Fehlersuche) und
  // einen Rat (was der Mensch jetzt tun kann). Ein Fehler ohne Rat ist eine
  // Sackgasse; ein Rat ohne Grund ist nicht nachpruefbar.
  class PostfachFehler extends Error {
    constructor(titel, rat, grund) {
      super(titel);
      this.titel = titel;
      this.rat = rat;
      this.grund = grund || '';
    }
  }

  async function token() {
    try {
      if (window.Clerk && Clerk.session) return await Clerk.session.getToken();
    } catch (e) { /* faellt unten in den Anmeldefehler */ }
    return null;
  }

  async function ruf(weg, daten) {
    const t = await token();
    if (!t) {
      throw new PostfachFehler(
        'Anmeldung abgelaufen',
        'Lade die Seite neu und melde dich erneut an.',
        'Clerk lieferte kein Sitzungs-Token.');
    }
    let antwort;
    try {
      antwort = await fetch('/api/postfach/' + weg, {
        method: 'POST',
        headers: { 'content-type': 'application/json', 'authorization': 'Bearer ' + t },
        body: JSON.stringify(daten || {}),
      });
    } catch (e) {
      throw new PostfachFehler(
        'Postfach nicht erreichbar',
        'Prüfe deine Verbindung und lade neu. Bleibt es so, läuft EntityOS gerade nicht.',
        'Netzwerkfehler bei /api/postfach/' + weg + ': ' + (e && e.message));
    }

    if (antwort.status === 401 || antwort.status === 403) {
      throw new PostfachFehler(
        'Kein Postfach für dieses Konto',
        'Melde dich neu an. Bleibt es dabei, ist dein Konto keinem Postfach zugeordnet — das muss am Server eingetragen werden.',
        'HTTP ' + antwort.status + ' auf /api/postfach/' + weg);
    }
    if (antwort.status === 404 || antwort.status === 405 || antwort.status === 501) {
      throw new PostfachFehler(
        'Postfach nicht erreichbar',
        'Der Postfachdienst ist auf diesem Server noch nicht eingehängt. Nichts zu tun außer warten — die Oberfläche ist in Ordnung.',
        'HTTP ' + antwort.status + ' auf /api/postfach/' + weg);
    }

    let daten2 = null;
    try { daten2 = await antwort.json(); } catch (e) { daten2 = null; }

    if (!antwort.ok) {
      throw new PostfachFehler(
        'Postfach antwortet mit einem Fehler',
        'Versuche es erneut. Wiederholt es sich, steht der Grund unten — der gehört ins Fehlerprotokoll.',
        'HTTP ' + antwort.status + ': ' + (daten2 && (daten2.fehler || daten2.error || daten2.detail) || antwort.statusText));
    }
    if (daten2 && daten2.ok === false) {
      throw new PostfachFehler(
        'Postfach meldet einen Fehler',
        'Versuche es erneut. Bleibt der Fehler, ist es der Mailserver und nicht die Oberfläche.',
        String(daten2.fehler || daten2.error || 'ohne Angabe'));
    }
    return daten2 || {};
  }

  // ── Zustandsflächen ───────────────────────────────────────────────────
  function zustandHtml(titel, text, grund, knopfId, knopfText, fehler) {
    return `<div class="pf-zustand ${fehler ? 'pf-fehler' : ''}">
      <h2 class="pf-zustand-titel">${esc(titel)}</h2>
      <p class="pf-zustand-text">${esc(text)}</p>
      ${grund ? `<p class="pf-zustand-grund">${esc(grund)}</p>` : ''}
      ${knopfId ? `<button type="button" class="pf-kopfknopf" id="${esc(knopfId)}">${esc(knopfText)}</button>` : ''}
    </div>`;
  }

  // Die Kennung des Knopfes haengt an der Flaeche: Liste und Lesefeld koennen
  // gleichzeitig einen Fehler zeigen, und zwei gleiche Kennungen im Dokument
  // haetten den Knopf der falschen Flaeche verdrahtet.
  function zeigeFehler(wo, f, nochmal) {
    const el = $(wo);
    if (!el) return;
    const knopfId = nochmal ? wo + '-nochmal' : '';
    el.innerHTML = zustandHtml(f.titel || 'Fehler', f.rat || '', f.grund || '',
      knopfId, 'Erneut versuchen', true);
    const knopf = knopfId ? $(knopfId) : null;
    if (knopf) knopf.addEventListener('click', nochmal);
  }

  // ── Ordner ────────────────────────────────────────────────────────────
  async function ladeOrdner(still) {
    let antwort;
    try {
      antwort = await ruf('ordner', {});
    } catch (f) {
      if (!still) {
        $('pf-ordnerliste').innerHTML =
          `<li class="pf-hinweis">${esc(f.titel)} — ${esc(f.rat)}</li>`;
      }
      return;
    }
    const roh = feld(antwort, 'ordner', 'unread', 'folders') || {};
    z.ordner = {};
    for (const name of Object.keys(roh)) {
      const eintrag = roh[name] || {};
      z.ordner[name] = {
        ungelesen: Number(feld(eintrag, 'ungelesen', 'unread') || 0),
        gesamt: feld(eintrag, 'gesamt', 'total'),
      };
    }
    zeichneOrdner();
  }

  function zeichneOrdner() {
    const el = $('pf-ordnerliste');
    if (!el) return;
    const namen = Object.keys(z.ordner).sort((a, b) => {
      const ai = ORDNERREIHE.indexOf(a), bi = ORDNERREIHE.indexOf(b);
      return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
    });
    if (!namen.length) {
      el.innerHTML = '<li class="pf-hinweis">Keine Ordner gemeldet.</li>';
      return;
    }
    el.innerHTML = namen.map((n) => {
      const u = z.ordner[n].ungelesen;
      return `<li><button type="button" class="pf-ordnerknopf" data-ordner="${esc(n)}"
        aria-current="${n === z.aktuellerOrdner}">
        <span class="pf-ordnername">${esc(ordnerName(n))}</span>
        ${u > 0 ? `<span class="pf-ordnerzahl" aria-label="${u} ungelesen">${u}</span>` : ''}
      </button></li>`;
    }).join('');
    el.querySelectorAll('.pf-ordnerknopf').forEach((b) => {
      b.addEventListener('click', () => wechsleOrdner(b.dataset.ordner));
    });
  }

  function wechsleOrdner(name) {
    if (!name) return;
    z.aktuellerOrdner = name;
    z.seite = 0;
    z.gewaehlt = null;
    z.offeneMail = null;
    z.suche = '';
    z.bekannteIds = new Set();
    const feldEl = $('pf-suchfeld');
    if (feldEl) feldEl.value = '';
    zeichneOrdner();
    setzeAnsicht('liste');
    leeresLesefeld();
    ladeMails();
  }

  // ── Mailliste ─────────────────────────────────────────────────────────
  async function ladeMails(rissErlaubt) {
    if (z.laedt) return;
    z.laedt = true;
    const liste = $('pf-mails');
    $('pf-titel').textContent = z.suche
      ? 'Suche: ' + z.suche
      : ordnerName(z.aktuellerOrdner);
    $('pf-anzahl').textContent = '';
    if (liste && !z.mails.length) {
      liste.innerHTML = zustandHtml('Wird geladen', 'Die Mails werden vom Server geholt.', '', '', '', false);
    }
    try {
      const antwort = z.suche
        ? await ruf('suchen', { ordner: z.aktuellerOrdner, suche: z.suche, frage: z.suche, grenze: HOLGRENZE })
        : await ruf('liste', { ordner: z.aktuellerOrdner, grenze: HOLGRENZE });
      const neu = feld(antwort, 'mails', 'emails') || [];
      const neueIds = new Set(neu.map((m) => String(feld(m, 'id', 'uid') || '')));

      // Riss nur bei einem ECHTEN Ereignis: eine Kennung, die vorher nicht da
      // war. Ohne vorherigen Stand (erster Aufruf) gibt es nichts zu melden.
      const gibtNeue = z.bekannteIds.size > 0 &&
        [...neueIds].some((id) => id && !z.bekannteIds.has(id));

      z.mails = neu;
      z.bekannteIds = neueIds;
      if (z.seite * SEITE >= z.mails.length) z.seite = 0;
      zeichneMails();
      if (rissErlaubt && gibtNeue) riss();
    } catch (f) {
      z.mails = [];
      zeigeFehler('pf-mails', f, () => ladeMails());
      $('pf-blaettern').hidden = true;
    } finally {
      z.laedt = false;
    }
  }

  function riss() {
    const el = $('pf-mails');
    if (!el) return;
    el.classList.remove('pf-riss');
    void el.offsetWidth;               // Neustart der Animation erzwingen
    el.classList.add('pf-riss');
    setTimeout(() => el.classList.remove('pf-riss'), 260);
    melde('Neue Mail eingetroffen');
  }

  function seitenMails() {
    return z.mails.slice(z.seite * SEITE, z.seite * SEITE + SEITE);
  }

  function zeichneMails() {
    const el = $('pf-mails');
    if (!el) return;

    $('pf-anzahl').textContent = z.mails.length
      ? (z.suche ? z.mails.length + ' Treffer' : z.mails.length + ' Mails')
      : '';

    if (!z.mails.length) {
      el.innerHTML = z.suche
        ? zustandHtml('Kein Treffer',
            'Für „' + z.suche + '" liegt in ' + ordnerName(z.aktuellerOrdner) + ' nichts vor. Suche mit weniger Wörtern, oder wechsle den Ordner.',
            '', '', '', false)
        : zustandHtml('Ordner ist leer',
            'In ' + ordnerName(z.aktuellerOrdner) + ' liegt keine Mail. Das ist kein Fehler.',
            '', '', '', false);
      $('pf-blaettern').hidden = true;
      return;
    }

    const versatz = z.seite * SEITE;
    el.innerHTML = seitenMails().map((m, i) => {
      const g = versatz + i;
      const ungelesen = !(feld(m, 'gelesen', 'read') === true);
      const anhang = feld(m, 'anhaenge', 'has_attachments') ? ' <span class="pf-mail-klammer">[Anhang]</span>' : '';
      const auszug = feld(m, 'auszug', 'snippet');
      return `<button type="button" class="pf-mail ${ungelesen ? 'pf-ungelesen' : ''}"
          data-i="${g}" aria-current="${g === z.gewaehlt}">
        <span class="pf-mail-zeile">
          <span class="pf-mail-von">${esc(nameAus(feld(m, 'von', 'from', 'sender')))}</span>
          <span class="pf-mail-datum" title="${esc(datumLang(m))}">${esc(datumKurz(m))}</span>
        </span>
        <span class="pf-mail-betreff">${esc(feld(m, 'betreff', 'subject') || '(kein Betreff)')}${anhang}</span>
        ${auszug ? `<span class="pf-mail-auszug">${esc(String(auszug).slice(0, 120))}</span>` : ''}
      </button>`;
    }).join('');

    el.querySelectorAll('.pf-mail').forEach((b) => {
      b.addEventListener('click', () => oeffneMail(Number(b.dataset.i)));
    });

    const seiten = Math.ceil(z.mails.length / SEITE);
    $('pf-blaettern').hidden = seiten <= 1;
    $('pf-seiteninfo').textContent =
      (versatz + 1) + '–' + Math.min(versatz + SEITE, z.mails.length) + ' von ' + z.mails.length;
    $('pf-seite-zurueck').disabled = z.seite === 0;
    $('pf-seite-vor').disabled = z.seite >= seiten - 1;
  }

  // ── Lesen ─────────────────────────────────────────────────────────────
  function leeresLesefeld() {
    const el = $('pf-lese');
    if (!el) return;
    el.innerHTML = zustandHtml('Nichts geöffnet',
      'Wähle links eine Mail. Mit j und k gehst du durch die Liste, mit n verfasst du eine neue.',
      '', '', '', false);
  }

  async function oeffneMail(index) {
    const kurz = z.mails[index];
    if (!kurz) return;
    z.gewaehlt = index;
    zeichneMails();
    setzeAnsicht('lesen');

    const el = $('pf-lese');
    el.innerHTML = zustandHtml('Wird geladen', 'Die Mail wird vom Server geholt.', '', '', '', false);

    try {
      const antwort = await ruf('lesen', {
        ordner: z.aktuellerOrdner,
        id: feld(kurz, 'id', 'uid'),
        uid: feld(kurz, 'uid', 'id'),
        index: index,
      });
      const voll = feld(antwort, 'mail', 'email') || {};
      z.offeneMail = Object.assign({}, kurz, voll, { _index: index, _ordner: z.aktuellerOrdner });

      // Der Server setzt \Seen beim Lesen selbst; die Liste zieht sofort nach,
      // damit die Kante nicht noch leuchtet, waehrend man die Mail liest.
      if (feld(kurz, 'gelesen', 'read') !== true) {
        kurz.gelesen = true; kurz.read = true;
        const o = z.ordner[z.aktuellerOrdner];
        if (o && o.ungelesen > 0) { o.ungelesen -= 1; zeichneOrdner(); }
        zeichneMails();
      }
      zeichneLesen(z.offeneMail);
    } catch (f) {
      zeigeFehler('pf-lese', f, () => oeffneMail(index));
    }
  }

  function zeichneLesen(mail) {
    const el = $('pf-lese');
    if (!el) return;

    const anhaenge = feld(mail, 'anhaenge', 'attachments') || [];
    const kopie = feld(mail, 'kopie', 'cc');
    const text = feld(mail, 'text', 'body');
    const htmlteil = feld(mail, 'html', 'html_body');

    el.innerHTML = `
      <button type="button" class="pf-zurueck" id="pf-zurueck">← Liste</button>
      <h2 class="pf-betreff">${esc(feld(mail, 'betreff', 'subject') || '(kein Betreff)')}</h2>
      <dl class="pf-kopf">
        <dt>Von</dt><dd><button type="button" class="pf-adresse" data-kopie="${esc(adresseAus(feld(mail, 'von', 'from', 'sender')))}"
          title="Adresse kopieren">${esc(feld(mail, 'von', 'from', 'sender') || '(kein Absender)')}</button></dd>
        <dt>An</dt><dd><button type="button" class="pf-adresse" data-kopie="${esc(adresseAus(feld(mail, 'an', 'to')))}"
          title="Adresse kopieren">${esc(feld(mail, 'an', 'to') || '—')}</button></dd>
        ${kopie ? `<dt>Kopie</dt><dd>${esc(kopie)}</dd>` : ''}
        <dt>Datum</dt><dd>${esc(datumLang(mail) || '—')}</dd>
      </dl>
      ${anhaenge.length ? `<div class="pf-anhaenge">${anhaenge.map((a, i) => {
        const name = typeof a === 'string' ? a : (feld(a, 'name', 'filename') || ('Datei ' + (i + 1)));
        const gr = typeof a === 'string' ? '' : groesse(feld(a, 'groesse', 'size'));
        return `<button type="button" class="pf-anhang" data-anhang="${i}">
          <span>${esc(name)}</span>${gr ? `<span class="pf-anhang-groesse">${esc(gr)}</span>` : ''}
        </button>`;
      }).join('')}</div>` : ''}
      <div class="pf-werkzeuge">
        <button type="button" class="pf-kopfknopf" id="pf-antworten">Antworten</button>
        <button type="button" class="pf-kopfknopf" id="pf-weiterleiten">Weiterleiten</button>
        <button type="button" class="pf-kopfknopf" id="pf-ungelesen">Als ungelesen</button>
        ${(text && htmlteil) ? '<button type="button" class="pf-kopfknopf" id="pf-ansicht-um">HTML anzeigen</button>' : ''}
        <span class="pf-fueller"></span>
        <button type="button" class="pf-kopfknopf" id="pf-spam">Als Spam</button>
        <button type="button" class="pf-warnknopf" id="pf-loeschen">Löschen</button>
      </div>
      <div id="pf-koerper"></div>`;

    // Text zuerst, HTML auf Wunsch. Gibt es einen Textteil, wird er gezeigt:
    // er ist im Kleid dieser Seite gesetzt, laedt nichts nach und verraet dem
    // Absender nicht, dass gelesen wurde. Nur eine Mail OHNE Textteil geht
    // gleich in den abgeriegelten HTML-Rahmen.
    zeichneKoerper(mail, !text && !!htmlteil, false);

    $('pf-zurueck').addEventListener('click', () => { setzeAnsicht('liste'); });
    $('pf-antworten').addEventListener('click', () => antworten(mail));
    $('pf-weiterleiten').addEventListener('click', () => weiterleiten(mail));
    $('pf-ungelesen').addEventListener('click', () => setzeGelesen(mail, false));
    $('pf-spam').addEventListener('click', () => frageSpam(mail));
    $('pf-loeschen').addEventListener('click', () => frageLoeschen(mail));

    const um = $('pf-ansicht-um');
    if (um) {
      let alsHtml = false;
      um.addEventListener('click', () => {
        alsHtml = !alsHtml;
        um.textContent = alsHtml ? 'Nur Text' : 'HTML anzeigen';
        zeichneKoerper(mail, alsHtml, false);
      });
    }

    el.querySelectorAll('.pf-adresse').forEach((b) => {
      b.addEventListener('click', async () => {
        try {
          await navigator.clipboard.writeText(b.dataset.kopie || '');
          melde('Adresse kopiert');
        } catch (e) {
          melde('Kopieren nicht möglich — markiere die Adresse und kopiere sie von Hand.', true);
        }
      });
    });

    el.querySelectorAll('.pf-anhang').forEach((b) => {
      b.addEventListener('click', () => ladeAnhang(mail, Number(b.dataset.anhang), anhaenge[Number(b.dataset.anhang)]));
    });

    el.scrollTop = 0;
  }

  // HTML-Mail laeuft in einem abgeriegelten Rahmen -- ohne Skript, ohne
  // Zugriff auf diese Seite. Fremde Bilder bleiben zuerst aus: ein
  // nachgeladenes Bild verraet dem Absender, dass und wann gelesen wurde.
  // Wer sie sehen will, sagt es ausdruecklich.
  function zeichneKoerper(mail, alsHtml, bilderFrei) {
    const wo = $('pf-koerper');
    if (!wo) return;
    const text = feld(mail, 'text', 'body');
    const htmlteil = feld(mail, 'html', 'html_body');

    if (alsHtml && htmlteil) {
      const regel = bilderFrei
        ? "default-src 'none'; img-src data: https:; style-src 'unsafe-inline'; font-src data:"
        : "default-src 'none'; img-src data:; style-src 'unsafe-inline'; font-src data:";
      const rahmen = document.createElement('iframe');
      rahmen.className = 'pf-htmlrahmen';
      rahmen.title = 'Inhalt der Mail (HTML)';
      rahmen.setAttribute('sandbox', 'allow-popups allow-popups-to-escape-sandbox');
      rahmen.setAttribute('referrerpolicy', 'no-referrer');
      rahmen.srcdoc = '<!doctype html><meta charset="utf-8">'
        + '<meta http-equiv="Content-Security-Policy" content="' + regel + '">'
        + '<base target="_blank">'
        + '<style>body{margin:12px;font:15px/1.5 system-ui,sans-serif;overflow-wrap:anywhere}'
        + 'img,table{max-width:100%}</style>'
        + String(htmlteil);
      wo.innerHTML = '';
      wo.appendChild(rahmen);
      const notiz = document.createElement('p');
      notiz.className = 'pf-htmlnotiz';
      if (bilderFrei) {
        notiz.textContent = 'Bilder von außen werden geladen. Der Absender kann daran sehen, dass du die Mail geöffnet hast.';
      } else {
        notiz.innerHTML = 'Bilder von außen sind geblockt. '
          + '<button type="button" class="pf-kopfknopf" id="pf-bilder">Bilder laden</button>';
      }
      wo.appendChild(notiz);
      const bk = $('pf-bilder');
      if (bk) bk.addEventListener('click', () => zeichneKoerper(mail, true, true));
      return;
    }

    const p = document.createElement('p');
    p.className = 'pf-text';
    p.textContent = (text && String(text).trim())
      ? String(text)
      : (htmlteil ? 'Diese Mail hat nur einen HTML-Teil. Schalte oben auf „HTML anzeigen".'
                  : 'Diese Mail hat keinen lesbaren Inhalt.');
    wo.innerHTML = '';
    wo.appendChild(p);
  }

  // Der Anhang kommt durch denselben geprueften Weg wie alles andere -- ein
  // blosser Link haette kein Clerk-Token dabei und liefe ins Leere.
  async function ladeAnhang(mail, index, beschreibung) {
    const name = typeof beschreibung === 'string'
      ? beschreibung
      : (feld(beschreibung, 'name', 'filename') || ('anhang-' + (index + 1)));
    melde('Anhang wird geholt: ' + name);
    const t = await token();
    if (!t) { melde('Anmeldung abgelaufen — lade die Seite neu.', true); return; }
    try {
      const antwort = await fetch('/api/postfach/anhang', {
        method: 'POST',
        headers: { 'content-type': 'application/json', 'authorization': 'Bearer ' + t },
        body: JSON.stringify({
          ordner: mail._ordner || z.aktuellerOrdner,
          id: feld(mail, 'id', 'uid'),
          uid: feld(mail, 'uid', 'id'),
          index: index,
          name: name,
        }),
      });
      if (!antwort.ok) {
        melde('Anhang nicht geholt (HTTP ' + antwort.status + '). Der Weg /api/postfach/anhang antwortet nicht.', true);
        return;
      }
      const blob = await antwort.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = name;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 20000);
      melde('Anhang geholt: ' + name);
    } catch (e) {
      melde('Anhang nicht geholt: ' + (e && e.message), true);
    }
  }

  // ── Verfassen / Antworten / Weiterleiten ──────────────────────────────
  function zeichneVerfassen(vorgabe) {
    const v = vorgabe || {};
    const el = $('pf-lese');
    if (!el) return;
    setzeAnsicht('lesen');           // gestapelt: das Formular steht dort, wo sonst gelesen wird
    z.ansicht = 'verfassen';

    el.innerHTML = `
      <button type="button" class="pf-zurueck" id="pf-zurueck">← Liste</button>
      <h2 class="pf-betreff">${esc(v.titel || 'Neue Mail')}</h2>
      <form id="pf-verfassform" novalidate>
        <div class="pf-feldgruppe">
          <label class="pf-feldname" for="pf-an">An</label>
          <input class="pf-feld" type="text" id="pf-an" autocomplete="off"
                 value="${esc(v.an || '')}" placeholder="name@beispiel.at">
          <div class="pf-vorschlaege" id="pf-vorschlaege" hidden></div>
        </div>
        <div class="pf-feldreihe">
          <div class="pf-feldgruppe">
            <label class="pf-feldname" for="pf-kopie">Kopie</label>
            <input class="pf-feld" type="text" id="pf-kopie" autocomplete="off" placeholder="optional">
          </div>
          <div class="pf-feldgruppe">
            <label class="pf-feldname" for="pf-blindkopie">Blindkopie</label>
            <input class="pf-feld" type="text" id="pf-blindkopie" autocomplete="off" placeholder="optional">
          </div>
        </div>
        <div class="pf-feldgruppe">
          <label class="pf-feldname" for="pf-betreff">Betreff</label>
          <input class="pf-feld" type="text" id="pf-betreff" value="${esc(v.betreff || '')}">
        </div>
        <div class="pf-feldgruppe">
          <label class="pf-feldname" for="pf-inhalt">Text</label>
          <textarea class="pf-textfeld" id="pf-inhalt">${esc(v.text || '')}</textarea>
        </div>
        <div class="pf-werkzeuge" style="border-bottom:none">
          <button type="submit" class="pf-sendknopf" id="pf-senden">Senden</button>
          <button type="button" class="pf-kopfknopf" id="pf-entwurf">Entwurf speichern</button>
          <button type="button" class="pf-kopfknopf" id="pf-abbrechen">Abbrechen</button>
        </div>
        <p class="pf-zustand-grund" id="pf-verfassstatus"></p>
      </form>`;

    $('pf-zurueck').addEventListener('click', zurueckAusVerfassen);
    $('pf-abbrechen').addEventListener('click', zurueckAusVerfassen);
    $('pf-entwurf').addEventListener('click', speichereEntwurf);
    $('pf-verfassform').addEventListener('submit', (e) => { e.preventDefault(); sende(v.antwortAuf || ''); });

    // Strg+Enter sendet -- dasselbe Kuerzel wie im Chat der Schale.
    $('pf-inhalt').addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); sende(v.antwortAuf || ''); }
    });

    bindeVorschlaege();
    const ziel = v.an ? $('pf-inhalt') : $('pf-an');
    ziel.focus();
    if (v.an) ziel.setSelectionRange(0, 0);
    el.scrollTop = 0;
  }

  function zurueckAusVerfassen() {
    z.ansicht = 'lesen';
    if (z.offeneMail) zeichneLesen(z.offeneMail);
    else { leeresLesefeld(); setzeAnsicht('liste'); }
  }

  // Vorschlaege stammen ausschliesslich aus den gerade geladenen Mails --
  // gemessene Adressen, kein gepflegtes Adressbuch, das es hier nicht gibt.
  function bekannteAdressen() {
    const gesehen = new Set();
    for (const m of z.mails) {
      for (const roh of [feld(m, 'von', 'from', 'sender'), feld(m, 'an', 'to')]) {
        const s = String(roh || '').trim();
        if (s) gesehen.add(s);
      }
    }
    return [...gesehen];
  }

  function bindeVorschlaege() {
    const eingabe = $('pf-an');
    const liste = $('pf-vorschlaege');
    if (!eingabe || !liste) return;
    eingabe.addEventListener('input', () => {
      const wert = eingabe.value.trim().toLowerCase();
      if (wert.length < 2) { liste.hidden = true; return; }
      const treffer = bekannteAdressen().filter((c) => c.toLowerCase().includes(wert)).slice(0, 6);
      if (!treffer.length) { liste.hidden = true; return; }
      liste.innerHTML = treffer.map((c) =>
        `<button type="button" class="pf-vorschlag">${esc(c)}</button>`).join('');
      liste.hidden = false;
      liste.querySelectorAll('.pf-vorschlag').forEach((b) => {
        b.addEventListener('mousedown', (e) => {
          e.preventDefault();
          eingabe.value = adresseAus(b.textContent);
          liste.hidden = true;
        });
      });
    });
    eingabe.addEventListener('blur', () => { setTimeout(() => { liste.hidden = true; }, 150); });
  }

  function antworten(mail) {
    const roh = String(feld(mail, 'text', 'body') || feld(mail, 'auszug', 'snippet') || '');
    const zitat = roh.split('\n').map((l) => '> ' + l).join('\n');
    const betreff = String(feld(mail, 'betreff', 'subject') || '').replace(/^\s*(Re|AW):\s*/i, '');
    zeichneVerfassen({
      titel: 'Antworten',
      an: adresseAus(feld(mail, 'von', 'from', 'sender')),
      betreff: 'Re: ' + betreff,
      text: '\n\n' + zitat,
      antwortAuf: feld(mail, 'id', 'uid') || '',
    });
  }

  function weiterleiten(mail) {
    const roh = String(feld(mail, 'text', 'body') || feld(mail, 'auszug', 'snippet') || '');
    const betreff = String(feld(mail, 'betreff', 'subject') || '').replace(/^\s*(Fwd|WG):\s*/i, '');
    const kopf = '\n\n---------- Weitergeleitete Nachricht ----------\n'
      + 'Von: ' + (feld(mail, 'von', 'from', 'sender') || '') + '\n'
      + 'Datum: ' + (datumLang(mail) || '') + '\n'
      + 'Betreff: ' + (feld(mail, 'betreff', 'subject') || '') + '\n\n';
    zeichneVerfassen({ titel: 'Weiterleiten', an: '', betreff: 'Fwd: ' + betreff, text: kopf + roh });
  }

  async function sende(antwortAuf) {
    const an = $('pf-an').value.trim();
    const betreff = $('pf-betreff').value.trim();
    const inhalt = $('pf-inhalt').value;
    const status = $('pf-verfassstatus');
    const knopf = $('pf-senden');

    if (!an) { status.textContent = 'Ohne Empfänger geht nichts — trage oben eine Adresse ein.'; $('pf-an').focus(); return; }
    if (!betreff) { status.textContent = 'Ohne Betreff geht nichts — eine Zeile genügt.'; $('pf-betreff').focus(); return; }

    status.textContent = 'Wird gesendet …';
    knopf.disabled = true;
    try {
      await ruf('senden', {
        an: an, to: an,
        kopie: $('pf-kopie').value.trim(),
        blindkopie: $('pf-blindkopie').value.trim(),
        betreff: betreff, subject: betreff,
        text: inhalt, body: inhalt,
        antwort_auf: antwortAuf || '',
      });
      melde('Gesendet');
      z.offeneMail = null;
      z.ansicht = 'lesen';
      leeresLesefeld();
      setzeAnsicht('liste');
      ladeMails();
      ladeOrdner(true);
    } catch (f) {
      status.textContent = f.titel + ' — ' + f.rat + ' (' + f.grund + ')';
      knopf.disabled = false;
    }
  }

  async function speichereEntwurf() {
    const status = $('pf-verfassstatus');
    const an = $('pf-an').value.trim();
    const betreff = $('pf-betreff').value.trim();
    const inhalt = $('pf-inhalt').value;
    status.textContent = 'Entwurf wird gespeichert …';
    try {
      await ruf('entwurf', {
        an: an, to: an,
        betreff: betreff, subject: betreff,
        text: inhalt, body: inhalt,
      });
      melde('Entwurf gespeichert');
      status.textContent = 'Entwurf gespeichert. Er liegt im Ordner Entwürfe.';
      ladeOrdner(true);
    } catch (f) {
      status.textContent = f.titel + ' — ' + f.rat + ' (' + f.grund + ')';
    }
  }

  // ── Zerstörendes: erst fragen ─────────────────────────────────────────
  // Der Knopf im Dialog heisst wie die Aktion, die er ausloest. "OK" waere
  // hier die schlechteste moegliche Beschriftung: es sagt nicht, was passiert.
  function frage(titel, text, knopfText) {
    return new Promise((aufloesen) => {
      const d = $('pf-frage');
      $('pf-fragetitel').textContent = titel;
      $('pf-fragetext').textContent = text;
      $('pf-frage-ja').textContent = knopfText;
      const fertig = () => {
        d.removeEventListener('close', fertig);
        aufloesen(d.returnValue === 'ja');
      };
      d.addEventListener('close', fertig);
      d.returnValue = 'nein';
      d.showModal();
      $('pf-frage-nein').focus();
    });
  }

  async function frageLoeschen(mail) {
    const betreff = feld(mail, 'betreff', 'subject') || '(kein Betreff)';
    if (!await frage('Mail löschen?',
      '„' + String(betreff).slice(0, 70) + '" wird gelöscht. Das lässt sich hier nicht rückgängig machen.',
      'Löschen')) return;
    await entferneMail(mail, 'loeschen', 'Gelöscht');
  }

  async function frageSpam(mail) {
    const betreff = feld(mail, 'betreff', 'subject') || '(kein Betreff)';
    if (!await frage('Als Spam markieren?',
      '„' + String(betreff).slice(0, 70) + '" wandert in den Spam-Ordner.',
      'Als Spam')) return;
    await entferneMail(mail, 'spam', 'Als Spam markiert');
  }

  async function entferneMail(mail, weg, meldungText) {
    const index = typeof mail._index === 'number' ? mail._index : z.mails.indexOf(mail);
    try {
      await ruf(weg, {
        ordner: mail._ordner || z.aktuellerOrdner,
        id: feld(mail, 'id', 'uid'),
        uid: feld(mail, 'uid', 'id'),
        index: index,
      });
      if (index >= 0 && index < z.mails.length) z.mails.splice(index, 1);
      z.gewaehlt = null;
      z.offeneMail = null;
      if (z.seite > 0 && z.seite * SEITE >= z.mails.length) z.seite -= 1;
      zeichneMails();
      leeresLesefeld();
      setzeAnsicht('liste');
      melde(meldungText);
      ladeOrdner(true);
    } catch (f) {
      // Kein stiller Fehlschlag und keine geschoenten Listen: der Server hat
      // das letzte Wort, also wird neu geladen statt lokal so getan als ob.
      melde(f.titel + ' — ' + f.rat, true);
      ladeMails();
    }
  }

  async function setzeGelesen(mail, gelesen) {
    try {
      await ruf('gelesen', {
        ordner: mail._ordner || z.aktuellerOrdner,
        id: feld(mail, 'id', 'uid'),
        uid: feld(mail, 'uid', 'id'),
        gelesen: gelesen,
        read: gelesen,
      });
      const kurz = z.mails[typeof mail._index === 'number' ? mail._index : z.mails.indexOf(mail)];
      if (kurz) { kurz.gelesen = gelesen; kurz.read = gelesen; }
      zeichneMails();
      melde(gelesen ? 'Als gelesen markiert' : 'Als ungelesen markiert');
      ladeOrdner(true);
    } catch (f) {
      melde(f.titel + ' — ' + f.rat, true);
    }
  }

  async function alleGelesen() {
    const offen = z.mails.filter((m) => feld(m, 'gelesen', 'read') !== true);
    if (!offen.length) { melde('In diesem Ordner ist nichts ungelesen'); return; }
    if (!await frage('Alle als gelesen markieren?',
      offen.length + ' ungelesene Mail(s) in ' + ordnerName(z.aktuellerOrdner) + ' werden als gelesen markiert.',
      'Alle als gelesen')) return;
    try {
      await ruf('markiere-alle-gelesen', { ordner: z.aktuellerOrdner });
      melde('Alle als gelesen markiert');
    } catch (f) {
      // Fehlt der Sammelweg, wird einzeln markiert -- und das wird gesagt.
      // Ein Ersatzweg, den niemand sieht, ist eine Luege ueber die Anlage.
      if (/HTTP 40[45]|HTTP 501/.test(f.grund || '')) {
        let daneben = 0;
        for (const m of offen) {
          try {
            await ruf('gelesen', {
              ordner: z.aktuellerOrdner, id: feld(m, 'id', 'uid'),
              uid: feld(m, 'uid', 'id'), gelesen: true, read: true,
            });
          } catch (e) { daneben += 1; }
        }
        melde(daneben
          ? 'Einzeln markiert — ' + daneben + ' Mail(s) blieben ungelesen (Sammelweg fehlt am Server).'
          : 'Alle als gelesen markiert (einzeln — der Sammelweg fehlt am Server).', !!daneben);
      } else {
        melde(f.titel + ' — ' + f.rat, true);
        return;
      }
    }
    z.mails.forEach((m) => { m.gelesen = true; m.read = true; });
    zeichneMails();
    ladeOrdner(true);
  }

  // ── System-Postfächer (Admin) ─────────────────────────────────────────
  // Aus dem Vorbild uebernommen (_showSystemMailboxModal & Co.). Sichtbar
  // wird der Knopf nur, wenn der Server tatsaechlich Postfaecher herausgibt:
  // wer nichts bekommt, bekommt auch keinen Knopf angeboten.
  const sys = { schluessel: null, postfaecher: [], nachrichten: [], offen: null };

  async function pruefeSystempostfaecher() {
    try {
      const antwort = await ruf('systempostfaecher', {});
      const liste = feld(antwort, 'postfaecher', 'boxes') || [];
      if (!liste.length) return;
      sys.postfaecher = liste;
      $('pf-systemknopf').hidden = false;
    } catch (f) { /* kein Zugang oder kein Weg -- dann eben kein Knopf */ }
  }

  function sysSchluessel(b) { return String(feld(b, 'schluessel', 'key') || ''); }
  function sysAdresse(b) { return String(feld(b, 'adresse', 'email') || ''); }
  function sysName(b) { return String(feld(b, 'name', 'label') || sysSchluessel(b)); }

  function oeffneSystemdialog() {
    const d = $('pf-sysdialog');
    zeichneSysReiter();
    d.showModal();
    if (sys.postfaecher.length) waehleSysPostfach(sysSchluessel(sys.postfaecher[0]));
  }

  function zeichneSysReiter() {
    const el = $('pf-sysreiter');
    el.innerHTML = sys.postfaecher.map((b) => {
      const k = sysSchluessel(b);
      return `<button type="button" role="tab" class="pf-sysreiter-knopf" data-k="${esc(k)}"
        aria-selected="${k === sys.schluessel}">
        ${esc(sysName(b))}<span class="pf-sysreiter-adresse">${esc(sysAdresse(b))}</span>
      </button>`;
    }).join('');
    el.querySelectorAll('.pf-sysreiter-knopf').forEach((b) => {
      b.addEventListener('click', () => waehleSysPostfach(b.dataset.k));
    });
  }

  async function waehleSysPostfach(k) {
    sys.schluessel = k;
    sys.offen = null;
    zeichneSysReiter();
    const liste = $('pf-sysliste');
    $('pf-syslese').innerHTML = zustandHtml('Nichts geöffnet', 'Wähle links eine Nachricht.', '', '', '', false);
    liste.innerHTML = zustandHtml('Wird geladen', 'Die Nachrichten werden geholt.', '', '', '', false);
    try {
      const antwort = await ruf('system/liste', { schluessel: k, key: k, grenze: 60 });
      sys.nachrichten = feld(antwort, 'nachrichten', 'mails', 'items') || [];
      zeichneSysListe();
    } catch (f) {
      zeigeFehler('pf-sysliste', f, () => waehleSysPostfach(k));
    }
  }

  function zeichneSysListe() {
    const el = $('pf-sysliste');
    if (!sys.nachrichten.length) {
      el.innerHTML = zustandHtml('Postfach ist leer', 'In diesem Postfach liegt keine Nachricht.', '', '', '', false);
      return;
    }
    el.innerHTML = sys.nachrichten.map((m) => {
      const uid = String(feld(m, 'uid', 'id') || '');
      const gelesen = feld(m, 'gelesen', 'seen') === true;
      return `<button type="button" class="pf-mail ${gelesen ? '' : 'pf-ungelesen'}"
          data-uid="${esc(uid)}" aria-current="${uid === sys.offen}">
        <span class="pf-mail-zeile">
          <span class="pf-mail-von">${esc(feld(m, 'von', 'from') || '(kein Absender)')}</span>
          <span class="pf-mail-datum">${esc(feld(m, 'datum', 'date') || '')}</span>
        </span>
        <span class="pf-mail-betreff">${esc(feld(m, 'betreff', 'subject') || '(kein Betreff)')}</span>
      </button>`;
    }).join('');
    el.querySelectorAll('.pf-mail').forEach((b) => {
      b.addEventListener('click', () => oeffneSysNachricht(b.dataset.uid));
    });
  }

  async function oeffneSysNachricht(uid) {
    sys.offen = uid;
    zeichneSysListe();
    const el = $('pf-syslese');
    el.innerHTML = zustandHtml('Wird geladen', 'Die Nachricht wird geholt.', '', '', '', false);
    try {
      const antwort = await ruf('system/lesen', { schluessel: sys.schluessel, key: sys.schluessel, uid: uid });
      const m = feld(antwort, 'nachricht', 'mail', 'email') || antwort;
      const kopf = feld(m, 'kopfzeilen', 'headers') || {};
      const text = String(feld(m, 'text', 'body_text', 'body') || '');
      const zeilen = ['From', 'To', 'Cc', 'Subject', 'Date', 'Message-ID', 'Reply-To', 'Return-Path']
        .filter((k) => kopf[k])
        .map((k) => `<dt>${esc(k)}</dt><dd>${esc(kopf[k])}</dd>`).join('');

      el.innerHTML = `
        <h3 class="pf-betreff">${esc(kopf.Subject || feld(m, 'betreff', 'subject') || '(kein Betreff)')}</h3>
        <dl class="pf-kopf">${zeilen}</dl>
        <div class="pf-werkzeuge" style="margin-top:12px">
          <button type="button" class="pf-kopfknopf" id="pf-sys-antworten">Antworten</button>
        </div>
        <p class="pf-text" id="pf-systext"></p>`;
      // Der Text wird als Text gesetzt, nicht als HTML -- eine System-Mail ist
      // per Definition von aussen und darf hier nichts ausfuehren.
      $('pf-systext').textContent = text || 'Diese Nachricht hat keinen lesbaren Inhalt.';
      $('pf-sys-antworten').addEventListener('click', () => {
        const an = adresseAus(kopf['Reply-To'] || kopf.From || '');
        let betreff = String(kopf.Subject || '');
        if (!/^\s*(Re|AW):/i.test(betreff)) betreff = 'Re: ' + betreff;
        zeichneSysVerfassen({
          an: an, betreff: betreff,
          antwort_auf: kopf['Message-ID'] || '',
          verweise: kopf.References || kopf['Message-ID'] || '',
          zitat: text,
        });
      });
    } catch (f) {
      zeigeFehler('pf-syslese', f, () => oeffneSysNachricht(uid));
    }
  }

  function zeichneSysVerfassen(vorgabe) {
    const v = vorgabe || {};
    const box = sys.postfaecher.find((b) => sysSchluessel(b) === sys.schluessel);
    const el = $('pf-syslese');
    const zitat = v.zitat ? '\n\n' + String(v.zitat).split('\n').map((l) => '> ' + l).join('\n') : '';

    el.innerHTML = `
      <h3 class="pf-betreff">${v.antwort_auf ? 'Antworten' : 'Neue Nachricht'}</h3>
      <dl class="pf-kopf"><dt>Von</dt><dd>${esc(box ? sysAdresse(box) : sys.schluessel)}</dd></dl>
      <form id="pf-sysform" style="margin-top:12px" novalidate>
        <div class="pf-feldgruppe">
          <label class="pf-feldname" for="pf-sys-an">An</label>
          <input class="pf-feld" type="text" id="pf-sys-an" value="${esc(v.an || '')}">
        </div>
        <div class="pf-feldgruppe">
          <label class="pf-feldname" for="pf-sys-kopie">Kopie</label>
          <input class="pf-feld" type="text" id="pf-sys-kopie" placeholder="optional">
        </div>
        <div class="pf-feldgruppe">
          <label class="pf-feldname" for="pf-sys-betreff">Betreff</label>
          <input class="pf-feld" type="text" id="pf-sys-betreff" value="${esc(v.betreff || '')}">
        </div>
        <div class="pf-feldgruppe">
          <label class="pf-feldname" for="pf-sys-text">Text</label>
          <textarea class="pf-textfeld" id="pf-sys-text">${esc(zitat)}</textarea>
        </div>
        <div class="pf-werkzeuge" style="border-bottom:none">
          <button type="submit" class="pf-sendknopf" id="pf-sys-senden">Senden</button>
          <button type="button" class="pf-kopfknopf" id="pf-sys-abbrechen">Abbrechen</button>
        </div>
        <p class="pf-zustand-grund" id="pf-sys-status"></p>
      </form>`;

    $('pf-sys-abbrechen').addEventListener('click', () => {
      if (sys.offen) oeffneSysNachricht(sys.offen);
      else el.innerHTML = zustandHtml('Nichts geöffnet', 'Wähle links eine Nachricht.', '', '', '', false);
    });
    $('pf-sysform').addEventListener('submit', async (e) => {
      e.preventDefault();
      const an = $('pf-sys-an').value.trim();
      const betreff = $('pf-sys-betreff').value.trim();
      const status = $('pf-sys-status');
      if (!an || !betreff) { status.textContent = 'Empfänger und Betreff werden gebraucht.'; return; }
      const knopf = $('pf-sys-senden');
      knopf.disabled = true;
      status.textContent = 'Wird gesendet …';
      try {
        await ruf('system/senden', {
          schluessel: sys.schluessel, key: sys.schluessel,
          an: an, to: an,
          kopie: $('pf-sys-kopie').value.trim(),
          betreff: betreff, subject: betreff,
          text: $('pf-sys-text').value,
          antwort_auf: v.antwort_auf || '',
          verweise: v.verweise || '',
        });
        melde('Gesendet');
        el.innerHTML = zustandHtml('Gesendet',
          'Die Nachricht ging aus ' + (box ? sysAdresse(box) : sys.schluessel) + ' hinaus.', '', '', '', false);
      } catch (f) {
        knopf.disabled = false;
        status.textContent = f.titel + ' — ' + f.rat + ' (' + f.grund + ')';
      }
    });
    $('pf-sys-an').focus();
  }

  // ── Ansicht (gestapelt) ───────────────────────────────────────────────
  function setzeAnsicht(a) {
    z.ansicht = a;
    const el = $('pf');
    if (!el) return;
    el.dataset.ansicht = (a === 'lesen' || a === 'verfassen') ? 'lese' : 'liste';
  }

  // ── Tastatur ──────────────────────────────────────────────────────────
  function tippt(ziel) {
    const t = (ziel && ziel.tagName) || '';
    return t === 'INPUT' || t === 'TEXTAREA' || t === 'SELECT' || (ziel && ziel.isContentEditable);
  }

  function aufTaste(e) {
    if ($('pf').hidden) return;
    if (e.key === 'Escape' && tippt(e.target)) { e.target.blur(); return; }
    if (tippt(e.target)) return;
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (document.querySelector('dialog[open]')) return;

    const seite = seitenMails();
    const versatz = z.seite * SEITE;
    const lokal = z.gewaehlt === null ? null : z.gewaehlt - versatz;

    if (e.key === 'j' || e.key === 'ArrowDown') {
      e.preventDefault();
      const n = lokal === null ? 0 : lokal + 1;
      if (n < seite.length) oeffneMail(versatz + n);
      else if ((z.seite + 1) * SEITE < z.mails.length) { z.seite += 1; zeichneMails(); oeffneMail(z.seite * SEITE); }
    } else if (e.key === 'k' || e.key === 'ArrowUp') {
      e.preventDefault();
      const n = lokal === null ? 0 : lokal - 1;
      if (n >= 0) oeffneMail(versatz + n);
      else if (z.seite > 0) { z.seite -= 1; zeichneMails(); oeffneMail(z.seite * SEITE + SEITE - 1); }
    } else if (e.key === 'Enter' && z.gewaehlt !== null) {
      e.preventDefault(); oeffneMail(z.gewaehlt);
    } else if (e.key === 'n') {
      e.preventDefault(); zeichneVerfassen({});
    } else if (e.key === 'a' && z.offeneMail) {
      e.preventDefault(); antworten(z.offeneMail);
    } else if (e.key === 'w' && z.offeneMail) {
      e.preventDefault(); weiterleiten(z.offeneMail);
    } else if (e.key === 'u' && z.offeneMail) {
      e.preventDefault();
      setzeGelesen(z.offeneMail, feld(z.mails[z.offeneMail._index] || {}, 'gelesen', 'read') !== true);
    } else if ((e.key === 'Delete' || e.key === 'Backspace') && z.offeneMail) {
      e.preventDefault(); frageLoeschen(z.offeneMail);
    } else if (e.key === 's' && z.offeneMail) {
      e.preventDefault(); frageSpam(z.offeneMail);
    } else if (e.key === '/') {
      e.preventDefault(); $('pf-suchfeld').focus(); $('pf-suchfeld').select();
    } else if (e.key === '?') {
      e.preventDefault(); $('pf-tastendialog').showModal();
    } else if (e.key === 'Escape') {
      setzeAnsicht('liste');
    }
  }

  // ── Puls: nachzählen, nicht raten ─────────────────────────────────────
  // Einmal pro Minute werden die Ordnerzaehler frisch geholt. Waechst der
  // Zaehler des offenen Ordners, wird die Liste nachgeladen -- und NUR dann
  // laeuft der Riss. Im Hintergrund (Tab nicht sichtbar) ruht der Puls:
  // Nachzaehlen fuer niemanden ist verschwendete Rechenzeit.
  function starteBeobachtung() {
    // Die Schale misst denselben Sachverhalt aus /api/zustand und meldet
    // "neue-mail". Darauf wird gehorcht, damit Leiste und Liste nicht
    // auseinanderlaufen -- aber sie ist NICHT die einzige Quelle: existiert
    // /api/zustand nicht, kommt von dort nie etwas, und das eigene
    // Nachzaehlen unten traegt trotzdem.
    if (window.EntityOS && EntityOS.beiMessung) {
      EntityOS.beiMessung((art) => {
        if (art !== 'neue-mail' || z.laedt || z.ansicht === 'verfassen' || z.suche) return;
        ladeOrdner(true);
        ladeMails(true);
      });
    }

    if (z.puls) clearInterval(z.puls);
    z.puls = setInterval(async () => {
      if (document.hidden || z.laedt || z.ansicht === 'verfassen') return;
      const vorher = (z.ordner[z.aktuellerOrdner] || {}).ungelesen || 0;
      await ladeOrdner(true);
      const nachher = (z.ordner[z.aktuellerOrdner] || {}).ungelesen || 0;
      if (nachher > vorher && !z.suche) ladeMails(true);
    }, PULS_MS);
  }

  // ── Start ─────────────────────────────────────────────────────────────
  window.addEventListener('load', async () => {
    const fehlerEl = $('pf-anmeldefehler');
    try {
      // Die Schale laedt Clerk unter Umstaenden auch. Beide teilen sich
      // dasselbe Versprechen, damit Clerk.load() nicht zweimal anlaeuft.
      window.__entityosClerk = window.__entityosClerk
        || Clerk.load({ ui: { ClerkUI: window.__internal_ClerkUICtor } });
      await window.__entityosClerk;
    } catch (e) {
      fehlerEl.textContent = 'Anmeldung nicht geladen: ' + (e && e.message)
        + ' — lade die Seite neu. Bleibt es so, ist Clerk auf diesem Server nicht erreichbar.';
      fehlerEl.hidden = false;
      return;
    }

    if (!Clerk.isSignedIn) {
      const wo = $('pf-anmeldung');
      wo.hidden = false;
      Clerk.mountSignIn(wo);
      return;
    }

    $('pf').hidden = false;

    // Die Schale wartet auf dieses Zeichen: sie pollt bewusst NICHT auf
    // window.Clerk herum, sondern laesst sich von der Seite sagen, wann eine
    // Anmeldung steht. Erst danach montiert sie den Nutzerknopf, misst den
    // Zustand (und damit die Signalfarbe) und zeigt die Zahl ungelesener
    // Mails. Ohne diesen Aufruf bliebe die Leiste stumm.
    if (window.EntityOS && EntityOS.anmeldungBereit) {
      EntityOS.anmeldungBereit(() => Clerk.session.getToken());
    }

    $('pf-neu').addEventListener('click', () => zeichneVerfassen({}));
    $('pf-neuladen').addEventListener('click', () => {
      z.suche = '';
      $('pf-suchfeld').value = '';
      ladeMails();
      ladeOrdner(true);
    });
    $('pf-alle-gelesen').addEventListener('click', alleGelesen);
    $('pf-seite-zurueck').addEventListener('click', () => {
      if (z.seite > 0) { z.seite -= 1; z.gewaehlt = null; zeichneMails(); }
    });
    $('pf-seite-vor').addEventListener('click', () => {
      if ((z.seite + 1) * SEITE < z.mails.length) { z.seite += 1; z.gewaehlt = null; zeichneMails(); }
    });
    $('pf-suchform').addEventListener('submit', (e) => {
      e.preventDefault();
      z.suche = $('pf-suchfeld').value.trim();
      z.seite = 0;
      z.gewaehlt = null;
      z.bekannteIds = new Set();
      ladeMails();
    });
    $('pf-suchfeld').addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && z.suche) {
        $('pf-suchfeld').value = '';
        z.suche = '';
        ladeMails();
      }
    });
    $('pf-ordner-auf').addEventListener('click', () => {
      const el = $('pf');
      el.dataset.ansicht = el.dataset.ansicht === 'ordner' ? 'liste' : 'ordner';
    });
    $('pf-tastenknopf').addEventListener('click', () => $('pf-tastendialog').showModal());
    $('pf-systemknopf').addEventListener('click', oeffneSystemdialog);
    $('pf-sys-schliessen').addEventListener('click', () => $('pf-sysdialog').close());
    $('pf-sys-verfassen').addEventListener('click', () => zeichneSysVerfassen({}));
    document.addEventListener('keydown', aufTaste);

    leeresLesefeld();
    await ladeOrdner();
    await ladeMails();
    pruefeSystempostfaecher();
    starteBeobachtung();
  });
})();

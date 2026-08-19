/* Das Textfeld hinter der Anmeldung -- gezeichnet, nicht geladen.
 *
 * ⚠️ ZUERST DAS WICHTIGSTE: DIESE SEITE DARF DEN RECHNER NICHT HEIZEN.
 * In diesem Projekt hat schon einmal eine Dauer-Animation im Hintergrund die
 * CPU auf Vollast gefahren, weil niemand sie angehalten hat. Deshalb hier drei
 * Bremsen, und alle drei sind Pflicht, keine Politur:
 *   - feste ~18 Bilder/s statt so schnell wie moeglich
 *   - Stillstand, sobald der Reiter in den Hintergrund geht
 *   - bei `prefers-reduced-motion` wird EINMAL gezeichnet und nie wieder
 * Ein Anmeldebildschirm laeuft oft minutenlang unbeaufsichtigt. Genau dort
 * faellt eine heisse Schleife niemandem auf.
 *
 * Warum gezeichnet und nicht als Bild: ein Vollbild-JPEG kostet ueber ein
 * Megabyte VOR der Anmeldung, sieht auf grossen Schirmen matschig aus -- und
 * kann nicht glitchen. Das Glitchen ist hier aber die Aussage.
 */
(function () {
  'use strict';

  const WORTE = [
    'entityOS', 'entityOS', 'entityOS', 'EntityOS', 'ENTITYOS',
    'エンティティ・オーエス', 'エンティティ', 'オーエス', '実体OS', '実体',
    'entity', 'OS', 'エンティティ・オーエス',
  ];

  function feld(wurzel) {
    const leinwand = document.createElement('canvas');
    wurzel.appendChild(leinwand);
    const stift = leinwand.getContext('2d', { alpha: false });
    if (!stift) return null;

    const ruhig = window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ⭐ Handy-/Schwachgeraet-Bremse (2026-08-19), dieselbe Heuristik wie in
    // emergenz.js: ein kleiner Schirm oder wenig Kerne/RAM bekommen ein
    // duenneres Feld. Die Anmeldung laeuft oft minutenlang unbeaufsichtigt --
    // genau dort darf ein Handy nicht warm werden, nur weil niemand hinsieht.
    let schwach = false;
    try {
      schwach = (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4) ||
                (navigator.deviceMemory && navigator.deviceMemory <= 4) ||
                Math.min(window.innerWidth, window.innerHeight) < 480;
    } catch (e) {}

    let breite = 0, hoehe = 0, zellen = [], streifen = [];

    // Die Marken-Merkmale einmal auslesen statt Farben zu erfinden -- die
    // Anmeldung ist dieselbe Marke wie alles dahinter.
    const stil = getComputedStyle(document.documentElement);
    const grund = (stil.getPropertyValue('--grund') || '#07080a').trim();
    const ton = Number((stil.getPropertyValue('--zustand-h') || '150').trim()) || 150;
    const saettigung = (stil.getPropertyValue('--zustand-s') || '70%').trim();
    const cyan = (stil.getPropertyValue('--geist-cyan') || '#29d3e8').trim();
    const mag = (stil.getPropertyValue('--geist-mag') || '#ff2e88').trim();
    const mono = (stil.getPropertyValue('--schrift-mono') || 'monospace').trim();

    const gruen = (helligkeit, deckung) =>
      `hsl(${ton} ${saettigung} ${helligkeit}% / ${deckung})`;

    function neuAufbauen() {
      const dpr = Math.min(schwach ? 1 : 2, window.devicePixelRatio || 1);
      breite = wurzel.clientWidth; hoehe = wurzel.clientHeight;
      leinwand.width = Math.max(1, Math.floor(breite * dpr));
      leinwand.height = Math.max(1, Math.floor(hoehe * dpr));
      stift.setTransform(dpr, 0, 0, dpr, 0, 0);

      // Dichte an die Flaeche koppeln: auf einem Handy sonst ein Brei, auf
      // einem grossen Schirm sonst eine leere Wand.
      // Dichter als der erste Wurf: die Vorlage lebt davon, dass es WIMMELT
      // und einzelne Worte daraus hervorstechen.
      const anzahl = Math.round((breite * hoehe) / (schwach ? 2900 : 2100));
      zellen = [];
      for (let i = 0; i < anzahl; i++) {
        const gross = Math.random() < 0.09;
        zellen.push({
          x: Math.random() * breite,
          y: Math.random() * hoehe,
          wort: WORTE[(Math.random() * WORTE.length) | 0],
          groesse: gross ? 16 + Math.random() * 14 : 6.5 + Math.random() * 4.5,
          helligkeit: gross ? 55 + Math.random() * 25 : 26 + Math.random() * 26,
          deckung: gross ? 0.5 + Math.random() * 0.5 : 0.16 + Math.random() * 0.34,
          tempo: (Math.random() * 0.22 + 0.03) * (Math.random() < 0.5 ? -1 : 1),
          geist: Math.random() < 0.07,
        });
      }
      // Waagerechte Datenschlieren: erst sie machen aus einer Worttapete
      // einen Bildschirm. Zwei Sorten -- breite, weiche Baender und kurze,
      // harte Fragmente, wie ein Zeilenrest, der nicht fertig gelesen wurde.
      streifen = [];
      for (let i = 0; i < 22; i++) {
        streifen.push({
          y: Math.random() * hoehe,
          x: 0, w: breite,
          h: 1 + Math.random() * 3,
          tempo: 0.15 + Math.random() * 0.6,
          deckung: 0.04 + Math.random() * 0.1,
          hart: false,
        });
      }
      for (let i = 0; i < 34; i++) {
        streifen.push({
          y: Math.random() * hoehe,
          x: Math.random() * breite,
          w: 20 + Math.random() * 190,
          h: 1 + Math.random() * 2,
          tempo: 0.05 + Math.random() * 0.3,
          deckung: 0.18 + Math.random() * 0.4,
          hart: true,
        });
      }
    }

    function zeichnen(zeit) {
      stift.fillStyle = grund;
      stift.fillRect(0, 0, breite, hoehe);

      // Waagerechte Lichtschlieren -- geben dem Feld Tiefe, ohne dass ein
      // einzelnes Wort dafuer heller werden muesste.
      for (const s of streifen) {
        stift.fillStyle = gruen(s.hart ? 72 : 58, s.deckung);
        stift.fillRect(s.x, s.y, s.w, s.h);
      }

      stift.textBaseline = 'middle';
      for (const z of zellen) {
        stift.font = `${z.groesse < 13 ? 400 : 600} ${z.groesse}px ${mono}`;
        if (z.geist) {
          // Farbversatz wie ein schlecht justierter Monitor: erst die beiden
          // Geisterkanaele, dann das Wort selbst darueber.
          stift.fillStyle = cyan; stift.globalAlpha = z.deckung * 0.5;
          stift.fillText(z.wort, z.x - 1.5, z.y);
          stift.fillStyle = mag;
          stift.fillText(z.wort, z.x + 1.5, z.y);
          stift.globalAlpha = 1;
        }
        stift.fillStyle = gruen(z.helligkeit, z.deckung);
        stift.fillText(z.wort, z.x, z.y);
      }

      // Der Stolperer: EIN waagerechtes Band wird versetzt, selten und kurz.
      // Ein Dauerglitch liest sich als kaputte Seite -- ein seltener liest sich
      // als Maschine, die kurz zuckt.
      if (!ruhig && Math.random() < 0.045) {
        const y = Math.random() * hoehe;
        const h = 6 + Math.random() * 34;
        const versatz = (Math.random() - 0.5) * 46;
        try {
          const band = stift.getImageData(0, Math.max(0, y | 0),
            leinwand.width, Math.max(1, h | 0));
          stift.putImageData(band, versatz, Math.max(0, y | 0));
        } catch (e) { /* getImageData kann in seltenen Faellen scheitern */ }
      }
    }

    function bewegen() {
      for (const z of zellen) {
        z.x += z.tempo;
        if (z.x > breite + 90) z.x = -90;
        if (z.x < -90) z.x = breite + 90;
        // Sehr selten wechselt ein Wort -- das Feld wirkt dadurch lebendig,
        // ohne dass sich sichtbar etwas bewegt.
        if (Math.random() < 0.0016) z.wort = WORTE[(Math.random() * WORTE.length) | 0];
      }
      for (const s of streifen) {
        s.y += s.tempo;
        if (s.y > hoehe) {
          s.y = -4;
          s.tempo = 0.05 + Math.random() * 0.6;
          if (s.hart) { s.x = Math.random() * breite; s.w = 20 + Math.random() * 190; }
        }
      }
    }

    let laeuft = false, letzte = 0, kennung = 0;
    const ABSTAND = 1000 / (schwach ? 12 : 18);   // schwach: ~12, sonst ~18 Bilder/s. Reicht voellig und heizt nicht.

    function schleife(jetzt) {
      if (!laeuft) return;
      kennung = requestAnimationFrame(schleife);
      if (jetzt - letzte < ABSTAND) return;
      letzte = jetzt;
      bewegen();
      zeichnen(jetzt);
    }

    function start() {
      if (laeuft || ruhig) return;
      laeuft = true; letzte = 0;
      kennung = requestAnimationFrame(schleife);
    }
    function halt() {
      laeuft = false;
      if (kennung) cancelAnimationFrame(kennung);
      kennung = 0;
    }

    neuAufbauen();
    zeichnen(0);          // auch bei prefers-reduced-motion steht das Feld da
    if (!ruhig) start();

    // ⚠️ Die wichtigste Zeile der Datei: kein Rechnen, wenn niemand hinsieht.
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) halt(); else start();
    });

    let warten = null;
    window.addEventListener('resize', () => {
      clearTimeout(warten);
      warten = setTimeout(() => { neuAufbauen(); zeichnen(0); }, 160);
    });

    return { halt, start };
  }

  window.EntityOSAnmeldung = {
    /** Zeichnet das Feld hinter dem Anmeldebereich. Gibt einen Halt-Griff zurueck. */
    grund(wurzel) {
      if (!wurzel) return null;
      return feld(wurzel);
    },
    /** Die Darstellung der Clerk-Box: dunkel, gruener Akzent, unsere Schriften. */
    clerkAussehen() {
      const stil = getComputedStyle(document.documentElement);
      const g = (n, f) => (stil.getPropertyValue(n) || f).trim();
      const ton = g('--zustand-h', '150'), saet = g('--zustand-s', '70%');
      return {
        variables: {
          colorPrimary: `hsl(${ton} ${saet} 52%)`,
          colorBackground: g('--flaeche', '#0f1114'),
          colorText: g('--text', '#e6e8ec'),
          colorTextSecondary: g('--matt', '#7d838e'),
          colorInputBackground: g('--grund', '#07080a'),
          colorInputText: g('--text', '#e6e8ec'),
          colorDanger: g('--warn', '#ff5c5c'),
          borderRadius: g('--rundung', '10px'),
          fontFamily: g('--schrift-text', 'system-ui, sans-serif'),
        },
        elements: {
          card: { boxShadow: 'none', border: '1px solid ' + g('--linie', '#1e2228'),
                  background: g('--flaeche', '#0f1114') },
          headerTitle: { fontFamily: g('--schrift-marke', 'system-ui'), letterSpacing: '.01em' },
          formButtonPrimary: { fontFamily: g('--schrift-marke', 'system-ui'),
                               textTransform: 'none', fontWeight: 600 },
          footer: { display: 'none' },   // Clerk-Werbung gehoert nicht auf unsere Anmeldung
          // ⚠️ Clerks Kopf traegt den Namen aus dem Clerk-Konto -- dort steht
          // noch "F.R.A.N.K.". Von hier aus nicht aenderbar, und ohnehin
          // doppelt: zwei Zeilen darueber steht bereits die Wortmarke mit
          // "Zugang zur Entitaet Zero". Also weg damit.
          // Der Name gehoert TROTZDEM im Clerk-Konto berichtigt: er erscheint
          // sonst in Mails und auf Zwischenseiten, wo dieses CSS nicht wirkt.
          header: { display: 'none' },
        },
      };
    },
  };
})();

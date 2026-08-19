# EntityOS — Oberflächenumbau (Auftrag Gabriel, 2026-08-18)

## Wo gearbeitet wird
Wirt: `ssh frank-api` (31.97.117.141). Quelle: `/opt/entityos/the artefact/`.
Branch **`retina-deploy`** — NIE auf `main` committen (dort committen fremde Instanzen stündlich).
Container: `entityos` (compose-Projekt `theartefact`), Port 127.0.0.1:3000, live unter
https://entityos.frank.ink. Web-Dateien werden per `COPY web ./web` ins Image gebacken →
**jede Frontend-Änderung braucht einen Rebuild.**

Bauen + starten:
```
cd "/opt/entityos/the artefact"
set -a; . /etc/clayverse/entityos-deploy.env; . /etc/clayverse/entityos-clerk.env; set +a
docker compose up -d --build
```
Der Container ist gehärtet: `read_only: true`, `cap_drop: ALL`, `no-new-privileges`, läuft als uid 5001 (clay).
Schreiben geht nur nach `/tmp` (tmpfs 64m), `/var/lib/clayverse`, `/workspace`, `/var/lib/clay`.

## Namensgesetz (verbindlich)
- **EntityOS** = das Produkt, der Container, ALLES Menschensichtbare: Seitentitel, Navigation, Wortmarke, Anmeldung.
- **Zero** = die Entität selbst, der Gesprächspartner im Chat. Nur dort taucht der Name auf.
- **Clay** = der Unterbau. Das Python-Paket heißt weiter `clayverse/`, `CLAYVERSE_*`-Variablen bleiben.
  Neue Variablen/Dateien → `entityos-*` / `ENTITYOS_*`.

## Grundregel des Kunden
**NICHTS ERFINDEN.** Keine ausgedachten Zahlen, Zustände, Namen, Beispieldaten. Was nicht
gemessen werden kann, wird weggelassen oder ehrlich als unbekannt gezeigt. Ein Platzhalter,
der wie ein Messwert aussieht, ist der schlimmste Fehler in diesem Projekt.

---

# 1 · Das Designsystem

Es gibt schon eine Designsprache im Haus: `web/avatare/zero-avatar.{js,css}`. Sie ist gut und
durchdacht — Lichtquelle HINTER der Scheibe, Farbton nach Zustand (grün 150° → gelb 55° → rot 5°),
5,5-s-Atmung, nur die neueste Nachricht glitcht und führt die Pupille nach.
**Diese Sprache wird erweitert, nicht ersetzt.** Kein zweiter Dialekt.

## Signatur (das eine, wofür die Seite in Erinnerung bleibt)
**Die Akzentfarbe der ganzen Oberfläche wird vom gemessenen Zustand getrieben** — dieselbe
Hue-Skala wie das Avatarlicht, nur auf die gesamte Seite gezogen. Grün wenn der Puls schlägt
und die Tests tragen, Gelb wenn etwas veraltet ist, Rot bei Ausfall. CSS-Variable
`--zustand-h` auf `:root`, von einem kleinen Modul aus `/healthz` + `/readyz` gesetzt.
Kennt man den Zustand nicht: **schwächer leuchten statt falsch leuchten** (`--signal-staerke`),
exakt wie es `zero-avatar.js` schon macht. Der Grund gehört ans Bild, nicht in eine Fußnote —
also ein Titel/`aria-label` am Statuspunkt, der sagt WARUM die Farbe so ist.

## Farbtafel
```
--grund:        #07080a   /* blau-schwarz, nicht neutralgrau */
--flaeche:      #0f1114
--flaeche-hoch: #15181d
--linie:        #1e2228
--text:         #e6e8ec
--matt:         #7d838e
--signal:       hsl(var(--zustand-h, 150) 70% 52%)   /* LEBT, siehe oben */
--kalt:         #4aa8ff   /* der Mensch: eigene Eingaben, eigene Nachrichten */
--warn:         #ff5c5c
```
Kein zweiter Akzent. Die Signalfarbe ist die einzige Buntheit; alles andere ist Grau + Kalt.

## Schrift
Google Fonts, kein CSP im Weg (geprüft). Jede Familie mit echtem Rückfallstapel.
```
Wortmarke/Navigation/Überschriften : "Chakra Petch", ui-sans-serif, system-ui, sans-serif
Fließtext                          : "IBM Plex Sans", -apple-system, "Segoe UI", Roboto, sans-serif
Zahlen/Terminal/Mailköpfe/Belege   : "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, monospace
```
Skala: 12 / 13 / 15 / 18 / 24 / 34 / 56. Wortmarke in Chakra Petch 700, weit gesperrt (`letter-spacing:.14em`), immer Versal.

## Bewegung — Gabriel will VIEL, aber orchestriert
1. **Bootsequenz** (einmalig beim Laden, ~700 ms): Scanline wischt von oben durch, die Wortmarke
   baut sich aus Zeichenrauschen zusammen (Buchstaben rotieren durch `01<>/#` bevor sie einrasten).
2. **Navigation:** die Unterstreichung des aktiven Punktes IST die Pulsspur — dieselbe Wellenform
   wie das Lebenszeichen auf der Startseite. Sie läuft dauerhaft und gleitet beim Wechsel.
3. **Glitch-Riss** bei echten Zustandswechseln: neue Generation, neue Mail, Zug fertig.
   RGB-Versatz + horizontale Scherung, 180 ms, danach ruhig. **Nur bei echten Ereignissen** —
   ein Dauerglitch ohne Anlass ist Kostüm.
4. **Terminal:** CRT-Vignette + feine Scanlines + ganz leichter Phosphor-Nachzug über dem xterm.
5. **Karten** auf der Startseite: Zahlen zählen beim Erscheinen hoch, Mikroglitch bei Hover.
6. **Untergrenze, nicht verhandelbar:** `@media (prefers-reduced-motion: reduce)` schaltet
   Bootsequenz, Spur, Glitch und Zähler ab — die Seite bleibt vollständig benutzbar.
   Sichtbarer Tastaturfokus überall. Bis 360 px Breite ohne waagrechtes Scrollen.

---

# 2 · Die Schale (Navigation)

Neu: `web/schale/schale.css` + `web/schale/schale.js` — eine gemeinsame Kopfleiste, die alle
vier Seiten einbinden. Fest oben, 56 px.

```
┌──────────────────────────────────────────────────────────────────────┐
│  ▚ ENTITYOS        Start   Chat   Terminal   Mailbox        ● (Nutzer)│
│                    ‾‾‾‾‾∿∿∿‾‾ (Pulsspur unter dem aktiven Punkt)      │
└──────────────────────────────────────────────────────────────────────┘
```
- Links Wortmarke (führt auf Start), rechts der Clerk-`UserButton`, dazwischen die vier Punkte.
- Der Statuspunkt neben dem Nutzerknopf trägt die Signalfarbe und den Grund als `title`.
- **Mailbox trägt eine Zahl**, wenn ungelesene Mails da sind (echt gezählt, nie geraten).
- Unter 640 px: die vier Punkte werden zu Symbolen + Kurzwort, Wortmarke schrumpft auf `▚`.
- Aktiver Punkt aus `location.pathname` — kein Framework, kein Router. Reines JS.

Wege: `/` = Start, `/chat`, `/terminal`, `/postfach`.
⚠️ **Achtung Umzug:** heute liegt der Chat auf `/`. Der Chat wandert nach `/chat`,
auf `/` kommt die neue Startseite. Der alte Weg `/` darf NICHT still etwas anderes zeigen —
`/chat` wird ein eigener Weg, und `/` bekommt die Startseite.

---

# 3 · Die Startseite (`web/start/index.html`)

Homepage-artig, aber ohne Marketing-Geschwätz — das hier ist ein Betriebsraum für zwei Menschen.

## Held: das Lebenszeichen
Kein Kachelraster mit großen Zahlen (das ist die Vorlagenantwort). Stattdessen eine
**Oszilloskop-Spur über die volle Breite**, die der 30-s-Puls schreibt: jeder Puls schiebt eine
neue Spalte hinein, die Kurvenhöhe folgt einem echten Messwert. Links davor groß die
**Generation** in IBM Plex Mono. Wechselt die Generation → Riss durch die Wortmarke.
Darunter eine Zeile Klartext: was gerade gemessen wurde und wann.

**Nur echte Werte.** Zu holen aus `/healthz`, `/readyz` und — falls dafür ein neuer, schlanker
Lesepunkt nötig ist — einem neuen `GET /api/zustand` (nur lesend, Clerk-geschützt), das aus der
UnifiedDB liefert: Generation, Züge, Kausalepisoden, Arbeitsraum-Episoden, Prüfpunkte, Wirkungen,
Artikel im Korpus, letzter Pulsschlag, ungelesene Mails. Fehlt ein Wert: `—` zeigen,
nicht 0 erfinden.

## Darunter: die drei Türen
Chat · Terminal · Mailbox als drei Karten, jede mit einem **echten** Lebenszeichen darin
(Chat: letzte Nachricht wann; Terminal: läuft/steht; Mailbox: ungelesen). Karte = Link.

## Ganz unten: eine ruhige Zeile
Wer angemeldet ist, welcher Platz, seit wann die Sitzung läuft. Mono, matt, klein.

---

# 4 · Chat (`web/chat/index.html`) — umziehen und neu einkleiden

Die Logik ist fertig und funktioniert (WebSocket `/ws/chat`, Platz-Umschalter, Übersetzer-
Aufklappen mit Caveman-Original + Beleg, Zero-Avatar). **Die Logik NICHT anfassen** —
nur die Schale einhängen und das neue Designsystem darüberlegen.
- Kopfleiste der Schale statt des eigenen `<header>`; der Zero-Titel und die Notiz wandern in
  eine schlanke Unterzeile.
- Blasen: Zero auf `--flaeche`, Mensch mit `--kalt`-Rand. Die Aufklappzeile „Original" bleibt.
- Der wartende Zustand („Zero antwortet noch nicht") bekommt eine echte Bewegung: die Pulsspur
  in klein, damit man sieht, dass es lebt statt hängt. Der ehrliche Hinweistext bleibt.

# 5 · Terminal (`/terminal`)
Heute erzeugt `clayverse/terminal_gateway.py` (~Zeile 271) die Seite als f-String im Python.
**Das kommt raus** und wird eine echte Datei `web/terminal/index.html`, genau wie der Chat
geladen wird (Platzhalter `__CLERK_API__` / `__CLERK_PUBLISHABLE_KEY__` server-seitig ersetzt,
`html.escape`). Die WebSocket-/xterm-Logik **Zeichen für Zeichen übernehmen** — sie ist scharf
geprüft (Auth-Erneuerung, Rahmengrößen, Resize). Nur die Hülle wird neu:
Schale oben, xterm in einem gerahmten Feld mit CRT-Vignette, Scanlines, leichtem Nachzug.

---

# 6 · Die Mailbox — der große Brocken

## Vorbild (1:1 übernehmen, was Gabriel und Andreas dort hatten)
Auf `root@72.61.19.188`:
- Backend `/opt/agentforge/api/email_routes.py`
- Frontend `/opt/agentforge/static/js/frank-pages/mail.js` (2144 Zeilen)
Lies beide vollständig, bevor du etwas baust.

## Was MIT kommt
Ordnerliste mit Ungelesen-Zählern (INBOX, Sent, Drafts, Trash, Junk) · Mailliste mit Seiten ·
Lesen (Text + HTML, Anhänge herunterladen) · Suche · Verfassen · Antworten · Weiterleiten ·
Entwurf speichern · Löschen · Als Spam · Gelesen/Ungelesen schalten · Alle als gelesen ·
Tastaturkürzel · **Admin-Postfachbetrachter** (die System-Postfächer, `_showSystemMailboxModal`
und alles daran — Gabriel will ihn ausdrücklich behalten).

## Was RAUS fliegt (Gabriels Wort: „Relikte")
- **KI-Antwortentwurf** — `_showReplyIntent`, `_generateReply`, `_showComposeIntent`,
  `_generateCompose` und die zugehörigen Server-Wege. Wird anders gelöst.
- **Persona / Signatur** — `_loadPersona`, `_savePersona`, `_build_persona_prompt`.
- **Freigabe-Warteschlange** ausgehender Mails (`/pending-sends*`), **Reputation**, **blocked**.
- Die i18n-Maschinerie (`_ml`, `_m`, `_mt`): die Oberfläche ist **deutsch**, fest.

## Der Weg zu den Mails — entschieden
**Direkt per IMAP-SSL.** Das Vorbild verbindet auf `127.0.0.1:143` unverschlüsselt, weil es AUF
dem Mailserver läuft. EntityOS läuft auf einem anderen Wirt, deshalb:
`imaplib.IMAP4_SSL(host, 993)` und `smtplib.SMTP(host, 587)` + `starttls()`.
**Gemessen und bestätigt** (18.08.): der Container erreicht `mail.frank.ink` auf 993 und 587,
und beide Anmeldungen gelingen — `gabriel@frank.ink` (28 Mails) und `andreas@frank.ink` (459).
Die Selbstheilung per `mailctl` aus dem Vorbild **entfällt** (das geht nur lokal auf dem Mailwirt).

Zugangsdatei liegt schon: **`/etc/entityos/postfach.env`** (640 root:clay) mit
`ENTITYOS_POSTFACH_{GABRIEL,ANDREAS}_{ADRESSE,PASSWORT}` und `ENTITYOS_{IMAP,SMTP}_{HOST,PORT}`.
In `compose.yaml` als read-only-Bind einhängen, genau wie `freie-zugaenge.env`:
`- /etc/entityos/postfach.env:/etc/entityos/postfach.env:ro`
⚠️ **Diese Werte dürfen NIE** in UnifiedDB-Zeilen, Momentaufnahmen, Quittungen, Protokolle oder
den agentZero-Export gelangen. Produktgesetz des Hauses.

## Zuordnung Mensch → Postfach: FEST VERDRAHTEN
⚠️ Andreas' Clerk-Konto ist `herzradgraz@gmail.com`, sein Postfach `andreas@frank.ink` —
sein agentforge-Konto lautete `genuinos@gmail.com`. **Ein Abgleich über die E-Mail-Adresse geht
also ins Leere.** Die Zuordnung läuft über die vorhandene Clerk-Karte
(`CLAYVERSE_CLERK_MAP_JSON` → `user_id` `gabriel`/`andreas`) auf den Namen in der Zugangsdatei.
Ein unbekanntes Subjekt bekommt **kein** Postfach — `PermissionError`, wie der IdentityRouter
es bei allem anderen auch tut. Test dafür schreiben.

## Senden geht durch das Tor
Gabriels Entscheidung: **jede gesendete Mail ist eine Wirkung** und läuft durch das
`EffectGate` (`clayverse/effects.py`, `effect_journal.py`) — mit Urteil, Ziel und Ergebnis als
Prüfsumme in der UnifiedDB. Schau dir an, wie bestehende Wirkungen das tun, und mach es genauso.
**Der Mailinhalt selbst gehört nicht in den Beleg** — nur Prüfsumme, Empfänger, Betreffzeile,
Zeitpunkt, Urteil.

## Neu zu bauen
- `clayverse/postfach.py` — IMAP/SMTP-Schicht (aus dem Vorbild portiert, entkernt wie oben)
- Wege in der App: `GET /postfach` (Seite) + `POST /api/postfach/{liste,lesen,suchen,senden,
  entwurf,loeschen,spam,gelesen,ungelesen,ordner}` + Anhang-Download. Clerk-geschützt, wie die
  bestehenden Wege.
- `web/postfach/index.html` (+ css/js) im neuen Designsystem
- Tests unter `tests/` im Stil der vorhandenen (dort liegen 528 grüne Tests — **keinen davon
  abschwächen**, das ist ausdrückliche Hausregel).

## Aufteilung der Mailbox-Oberfläche
Breitbild: drei Spalten — Ordner (schmal) | Liste | Lesefeld.
Handy: gestapelt, ein Zurück-Pfeil. Ungelesene Zeilen tragen die Signalfarbe als linke Kante.
Mailköpfe in IBM Plex Mono. Neue Mail = kurzer Glitch-Riss in der Liste.

---

# 7 · Abnahme, bevor irgendetwas live geht
1. `docker compose up -d --build`, Container `healthy`.
2. Testsuite laufen lassen — **528 grün / 14 rot war der Stand vorher**. Es darf nicht schlechter werden.
3. Echter Browser, Desktop UND Handy (360 px): **0 Konsolenfehler, 0 kaputte Bilder,
   0 waagrechtes Scrollen** auf allen vier Seiten.
4. Mailbox mit dem echten Postfach prüfen: Liste, Lesen, Suche, Entwurf. Senden erst nach Gabriels Wort.
5. Prüfen, dass `prefers-reduced-motion` wirklich alles Bewegte anhält.
6. Erst dann committen — auf `retina-deploy`, mit Begründung im Text (Befund · Messung · Grund),
   so wie es die anderen Commits dort tun.

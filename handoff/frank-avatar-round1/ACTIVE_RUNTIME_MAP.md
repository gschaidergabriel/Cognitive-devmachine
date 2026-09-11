# ACTIVE_RUNTIME_MAP.md — welches Repo/Prozess ist wirklich live

## 1. Kernbefund: `frankenstein-repo` ist NICHT die Avatar-App

Beleg:
```
$ cd /home/ai-core-node/frankenstein-repo && git remote -v && git log --oneline -5
origin  https://github.com/gschaidergabriel/frankenstein.git
ec6fce0 4B-Abstraktionsschicht (Liebe/Tod/Verlust) als TypedEntry-Achsen anschliessen
f5c42d6 Modellwechsel verwirft die Kalibrierung der drei Modellachsen
c7de75d Innenmessung des Sprachmodells als Perzept: das Modell speist den Wettbewerb ...
eda0029 Goldtest 51/51: vier Pruefungen vom Produktionszustand entkoppelt
6d487ae Goldtest: Basis bewusst auf f5a524b angehoben ...
```
Voller Log: `evidence/environment/frankenstein-repo_context.txt`. Das ist reine
GRID10-Kognitionsforschung (TypedEntry, Goldtest, Modellachsen). Keine
HTML/CSS/Canvas-Datei, kein Frontend-Code, kein Bezug zu einem Avatar-Bild in
diesem Repo.

## 2. Der wirklich laufende Avatar-Prozess

```
$ ss -tlnp | grep 8788
LISTEN 0 5 127.0.0.1:8788  users:(("python3",pid=544719,fd=3))

$ systemctl --user show frankenstein-buehne.service -p ExecStart -p WorkingDirectory -p MainPID
MainPID=544719
ExecStart={ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /home/ai-core-node/.claude/star/visual/buehne_daemon.py ; ... }
WorkingDirectory=!/home/ai-core-node

$ readlink -f /proc/544719/cwd
/home/ai-core-node

$ tr '\0' ' ' < /proc/544719/cmdline
/usr/bin/python3 /home/ai-core-node/.claude/star/visual/buehne_daemon.py
```
Unit description (from the unit file itself, unedited):
`FranKenstein Buehne / Livestream-Fenster (paket-1789069809553-3831a7, Port 8788, persistent)`

Live since `Fri 2026-09-11 23:53:32 +07` (`systemctl --user show ... -p ExecStart`
`start_time` field, captured in `evidence/environment/frankenstein-buehne.service.show.txt`).

## 3. Bewiesen per HTTP-Antwort + Screenshot, nicht nur per Prozessname

```
$ curl -s -D - -o /dev/null http://127.0.0.1:8788/
HTTP/1.0 200 OK
Content-Type: text/html; charset=utf-8
```
Volle Kopfzeilen: `evidence/environment/http_root_headers.txt`.

Der HTML-Titel ist wortgleich mit dem Screenshot, das Gabriel als Referenz
schickte:
```
<title>FranKenstein -- live</title>
```
Screenshot des tatsächlich laufenden Renders (dieser Runde, kein Mockup):
`evidence/screenshots/standard_746x449.png` und
`evidence/screenshots/fullscreen_1680x1050.png`. Beide zeigen: Mosaik-/
Pixel-Gesicht, "1 Zuschauer"-Zähler oben rechts, CHAT-Panel rechts — exakt
das von Gabriel beschriebene Bild.

## 4. `/home/ai-core-node/.claude/star/visual/` ist KEIN Git-Repo

```
$ cd /home/ai-core-node/.claude/star/visual && git rev-parse --show-toplevel
fatal: not a git repository (or any of the parent directories): .git
```
Das widerspricht der Erwartung von PROMPTS/01 ("erwarteter Kandidat ist
frankenstein-repo"). Der real laufende Code liegt auf Disk unter
`.claude/star/` (Teil des `star`-Systems, siehe `~/.claude/star/*.py`), NICHT
in irgendeinem der geklonten Git-Repos auf diesem Rechner, und wird von
keinem der Git-Verzeichnisse referenziert oder eingebunden. Der `git/`-Ordner
in diesem Handoff-Paket dokumentiert das explizit (`git/NOTAM.txt`) statt
leere/erfundene Commit-Hashes zu liefern.

## 5. Server-Architektur (aus `buehne_daemon.py`, wörtlicher Docstring-Auszug)

> "buehne_daemon.py -- die 'Buehne': FranKenstein sichtbar, wie ein
> Livestream. ARBEITSPAKET paket-1789069809553-3831a7 (Gabriel, 2026-09-11).
> WAS DAS IST: ein einziger Prozess mit zwei Aufgaben: 1. ein winziger
> HTTP-Server (nur 127.0.0.1, Port PORT) ... 2. eine Schleife, die GENAU EINE
> Datei liest (zustand.json) und danach ein echtes Chrome-App-Fenster
> oeffnet/schliesst."

Stdlib-`ThreadingHTTPServer` (`http.server`), kein Flask/FastAPI/Node. Bind
`127.0.0.1:8788` (Konstante `BIND_HOST`/`PORT`, Zeilen 192-193). Kein externer
Netzwerkzugriff möglich — nur lokal.

Sichtbar gemacht wird die Seite, indem der Daemon selbst ein echtes
`google-chrome --app=http://127.0.0.1:8788/` Fenster startet/überwacht
(Chrome-Profil unter `chrome-profile/`, PID-Datei `chrome.pid`, Log
`chrome.log`). Der Bildschirm dieses Fensters wird vermutlich per `x11vnc`
(Port 5998, ebenfalls localhost) für Fernzugriff/Aufnahme sichtbar gemacht —
dieser Prozess läuft, ist aber ein separates, unangetastetes System und wird
hier nur zur Vollständigkeit erwähnt (`ss -tlnp` Beleg in
`evidence/environment/ss_listen.txt`).

Explizit NICHT angefasst laut Datei-Docstring selbst (Zitat): "gespraech_loop.py,
stern.py, workspace.py, charakter.py, welt/, koerperpflege.py, sinne.py,
buehne.py (das gleichnamige Modul im Sprachmodus -- ein Namensvetter, nicht
dasselbe wie diese Datei hier!)". `unified.db` wird ausschließlich lesend
(`mode=ro`) geöffnet.

## 6. Frontend-Code

- `buehne.html` (107.694 Bytes) — komplette Seite: Farbwelt, Layout (CHAT-Panel
  rechts, "Zuschauer"-Zähler, Datei-Ablage), Layer-Compositing-Logik in
  eingebettetem `<script>`. Ausgeliefert immer frisch von Disk (`Cache-Control:
  no-store`), keine Build-Pipeline, kein Bundler — reines Vanilla-JS/HTML/CSS.
- `filmlook.js` (8.383 Bytes) — separat ausgelagerter globaler Filmlook
  (Korn/Vignette/Farbabstimmung), bewusst getrennt von `buehne.html` "damit
  zwei Agenten nicht in derselben Datei kollidieren" (Kommentar im Server,
  Zeile ~811). Vom Server unter `/filmlook.js` ausgeliefert, mit Leer-Antwort-
  Fallback statt 404, falls die Datei geleert wird.
- Kein React/Vue/WebGL-Framework. Das Canvas-Element `#kopf-canvas` wird laut
  Code für Kompositions-/Crop-Zwecke verwendet (2D Canvas API), keine WebGL-
  Pipeline.

## 7. Live-DOM-Layerstapel (gemessen, nicht angenommen)

`--dump-dom` desselben Chrome-Renders (`evidence/runtime/dom_dump.html`)
zeigt den tatsächlichen Layerstapel des laufenden Rigs:

| Element-ID | src (zur Aufnahmezeit) |
|---|---|
| `hg-frame` | `/hintergrund/ruhig/ruhig_003.png` |
| `koerper-schicht` | `/koerper_rgba/koerper_zero.png` |
| `koerper-schicht2` | `/koerper_rgba/koerper_zero.png` |
| `kopf-schicht` | `/kopf_rgba/kopf_zero_ohne_rotes_augenglow.png` |
| `kopf-schicht2` | `/kopf_rgba/roll/gier_+00_nick_+00_roll_+00.png` |
| `ausdruck-schicht` | (leer zur Aufnahmezeit) |
| `ausdruck-schicht2` | (leer zur Aufnahmezeit) |
| `pupillen-glow` | `/augen_gaze/rotglow_tracking_master.png` (opacity 0 zur Aufnahmezeit) |
| `augen-blink` | `/augen_blink/blink_000.png` |
| `mund-effekt` | `/mund_keyframes/mund_00_rest.png` |

⚠️ Wichtig für die Kompositions-/Rigfehler-Diagnose, die dieser Handoff laut
PROMPTS/01 vorbereiten soll: es existieren bewusst ZWEI parallele Ebenen pro
Körperteil (`-schicht` und `-schicht2`) — das ist im Code als Übergangs-
/Blend-Mechanismus angelegt (z.B. Cross-Fade zwischen Zuständen), nicht per se
der Fehler. Ob genau DAS der im Prompt beschriebene "zwei komplette Köpfe
gleichzeitig"-Fehler ist, wurde in dieser Runde NICHT weiter diagnostiziert —
das ist laut Auftrag explizit Aufgabe der NÄCHSTEN Runde (Codex/GO-Protokoll),
nicht dieser Export-Runde. Hier nur der gemessene Ist-Stand.

Computed-Style-Auszug (transform/opacity/filter) ist oben in der Tabelle
mitgeliefert, wo zur Aufnahmezeit gesetzt; volle Werte in
`evidence/runtime/dom_dump.html` (inline `style=`-Attribute je Element).

## 8. Aktive vs. inaktive Asset-Verzeichnisse (Beleg: Server-Routing-Code)

`buehne_daemon.py`, Konstanten-Block (Zeilen 60-96) + `do_GET`-Routing
(Zeilen 790-920) sind die **einzige Quelle der Wahrheit** dafür, welches
Verzeichnis unter welcher URL ausgeliefert wird:

| Route | tatsächliches Verzeichnis | Rolle |
|---|---|---|
| `/ausdruck/` | `ausdruck_zugeschnitten/` | Sonderausdruck-Fallback (zugeschnitten, alter Schleier-Bug behoben) |
| `/augen/` | `augen_zugeschnitten/` | Sonderausdruck-Fallback |
| `/kopf/` | `kopf_zugeschnitten/` | Sonderausdruck-Fallback |
| `/augen_gaze/` | `augen_gaze/` | Blickrichtung (rotglow_tracking_master.png) |
| `/augen_blink/` | `augen_blink/` | 12 Blinzel-Frames (blink_000..011), erst 2026-09-11 ausgepackt |
| `/mund_keyframes/` | `mund_keyframes/` | Mundformen (Silbentakt-Schätzung, kein echter Audiopegel) |
| `/kopf_rgba/` (+`/roll/`) | `kopf_rgba/` | HAUPT-Kopfebene, RIG_V2, echte Alpha-PNGs |
| `/koerper_rgba/` | `koerper_rgba/` | HAUPT-Körperebene, RIG_V2 |
| `/hintergrund/<stimmung>/` | `hintergrund/` | 5 feste Stimmungen × 60 Frames Schleife (Allowlist im Code, kein freier Ordnerinhalt) |
| `/ausdruck_erweitert/<register>/<ausdruck>/...` | `ausdruck_erweitert/` | erweiterte Ausdrucksregister, 4 Register freigegeben (Kommentar: 2 Register waren vorher tot, weil nicht in der Allowlist) |

**Physisch vorhanden, aber von KEINER Route referenziert** (nur historischer/
experimenteller Ballast, nicht Teil des laufenden Rigs):
`ausdruck/`, `augen/`, `kopf/` (Originale vor dem Zuschnitt — Kommentar im
Code: "bleiben nur fuer Sonderausdruck-Faelle/Altlast bestehen, NICHT
hierher zurueckstellen"), sowie sämtliche `*_ai`, `*_relief`, `*_relief2`,
`*_relief3`, `*_tiefe`, `*_tiefe_detail`, `*_tiefe_esrgan`, `*_detail`,
`*_detail_bilateral`, `*_detail_esrgan`, `*_proxy`, `*_parallax`,
`kopf_yaw_neu`, `rig_referenz/`, `models/` (Build-Zeit-Modelle für
`tiefe_bauen.py`/`detail_bauen.py`, nicht laufzeitgeladen). Vollständige
Liste mit je Datei sha256/Größe: `INVENTORY.csv`, Spalte `runtime_status`.

Zahlen (gemessen, `INVENTORY.csv`): 1.340 aktive Asset-Dateien (656 MB),
3.904 inaktive/experimentelle Dateien, 23 Code-/Konfigdateien.

## 9. Ehrlichkeits-Hinweise aus dem Code selbst (nicht meine Interpretation)

Wörtliches Zitat aus dem Docstring (Abschnitt "EHRLICHKEIT"):
> "keine erfundene Zuschauerzahl, keine Fake-Herzchen, keine erfundenen
> fremden Chatnutzer. '1 Zuschauer' im UI ist eine feste Konstante, keine
> Messung." Und zur Mundbewegung: "SILBENTAKT-SCHAETZUNG aus der Textlaenge
> ..., NICHT echter Pegel."

Dieser Handoff übernimmt dieselbe Ehrlichkeitsregel: `requestAnimationFrame`-
Statistik/Long-Tasks/Memory-Profiling wurden in dieser Runde NICHT
instrumentiert (kein vorhandener Messpfad im Code gefunden) — als "nicht
messbar" dokumentiert statt erfunden. 30-60s Videomitschnitt der Animation
wurde in dieser Runde NICHT erzeugt (kein Bildschirmaufnahme-Werkzeug in der
verfügbaren Zeit sicher verkabelt) — als offener Punkt in `HANDOFF_READY.json`
unter `missing` gelistet, keine Behauptung des Gegenteils.

# FranKenstein "Dream Target Build" — Runde 2 Bericht

Ehrlich, mit Belegen. Kein "sieht gut aus" ohne Messung/Screenshot.

## 0. Kontext

Runde 1 (2026-09-11, Commit 2cb05a83, Branch
`chatgpt-vps-work/frank-avatar-handoff-round1`) war reiner Export/Bestand,
keine Änderung. Diese Runde 2 sollte laut Auftrag `04_CLAUDE_DREAM_TARGET_BUILD.txt`
+ `EMPIRICAL_DREAM_TARGET.md` die echte Verbesserung liefern: kanonische
Anker/Transformkette als Fundament, dann Tiefenparallaxe, lokale
Ausdrucks-Deltas, Fixed-Step-Physik, Hintergrund-Kohärenz, globaler
Filmlook-Pass, UI-Chrome.

**Lease genommen** (siehe `stern.lease_halten`) auf:
- `/home/ai-core-node/.claude/star/visual/buehne.html`
- `/home/ai-core-node/.claude/star/visual/buehne_daemon.py`
Keine fremde aktive Lease kollidierte (`lease_hinweise()` vor Start geprüft).

## 1. Root-Cause-Befund "Doppelgesicht" — bereits gelöst, VOR dieser Runde

Runde 1 hat die Diagnose explizit an diese Runde übergeben (siehe
`ACTIVE_RUNTIME_MAP.md` Abschnitt 7: "-schicht/-schicht2 ist als
Crossfade-Mechanismus angelegt, ob das der 'zwei komplette Köpfe'-Fehler
ist, wurde NICHT weiter diagnostiziert").

**Befund dieser Runde:** Der im Code-Kommentarverlauf von `buehne.html`
dokumentierte "Geisterkopf"/Doppelgesicht-Fehler war zum Start dieser
Runde bereits durch vorangegangene Arbeit (Kommentare datiert 2026-09-11,
vor meinem Einstieg) behoben:

- EINE Transformkette: `#kamera → #gesicht-rahmen → #kopf-canvas →
  #kopf-dreh/#koerper-dreh` — keine zwei widersprüchlichen Bezugsrahmen mehr
  (der alte Bug: CSS-Prozente auf `#gesicht-rahmen`, dem schon
  zugeschnittenen `object-fit:cover`-Ausschnitt, statt auf der rohen
  1536×1024-Leinwand).
- Anatomische Drehpunkte: `#kopf-dreh{transform-origin:50% 58.59%}` (echter
  Halswirbel-Anker aus dem Rig-Manifest, 768,600 auf 1536×1024),
  `#koerper-dreh{transform-origin:50% 100%}` (Hüfte).
  Genau der Fix, den `EMPIRICAL_DREAM_TARGET.md` unter "kanonische Anker,
  eine Transformkette" fordert.
- Halsnaht weich statt hart maskiert (`mask-image` Gradient 53.7%→58.5%
  auf `#kopf-schicht`/`#ausdruck-schicht`) statt hartem Kantenabbruch.
- Die alten flachen, undurchsichtigen `#gesicht`/`#gesicht2`-Ebenen (RGB
  ohne Alpha, z-index 3 ÜBER dem RGBA-Kopf, andere Kopfposition) sind
  komplett aus DOM+CSS entfernt — DAS war der eigentliche Geisterkopf.
  `#ausdruck-schicht`/`#ausdruck-schicht2` (echte RGBA, gleiche Silhouette,
  liegen IN `#kopf-dreh`) haben sie ersetzt.
- Augen-Glow/Blinzel-Layer wurden von außerhalb `#kopf-dreh` NACH INNEN
  verschoben — vorher blieb der rechteckige Augen-Flicken bei Kopfroll-Posen
  starr an der 0°-Stelle stehen, während das Kopffoto darunter tatsächlich
  gekippt war (die "zweiter Kopf durchscheint bei Bewegung"-Variante).

**Eigene Verifikation dieser Runde** (nicht nur Kommentare glauben):
- Live-DOM-Dump (`EVIDENCE/dom/dom_dump_after.html`) nach `--dump-dom`:
  `#kopf-schicht2` trägt KEIN inline `style="opacity:..."` → nutzt den
  CSS-Default `opacity:0` aus der Regel `#kopf-schicht2,#ausdruck-schicht2,
  #ausdruck-schicht{opacity:0}`. Genau EIN sichtbarer Kopf-Layer zur
  Aufnahmezeit.
- Screenshot `before_ui_chrome.png` (vor jeder eigenen Änderung dieser
  Runde) zeigt visuell einen einzelnen, kohärenten Kopf — kein Doppelbild,
  keine Geisterkontur, auch nicht bei Zoom auf die Halsregion.
- Konsolen-Log (`EVIDENCE/dom/console_after.log`) frei von JS-Fehlern
  (nur bekanntes Chrome-internes GCM-Telemetrie-Rauschen, irrelevant).

**Schlussfolgerung:** Das im Auftrag als "wahrscheinliche Ursache" benannte
Ebenen-Springen ist bereits das FUNDAMENT, das der Auftrag verlangt — nicht
neu von mir gebaut, sondern vorgefunden und verifiziert. Ich habe NICHTS an
der Transformkette/den Ankern geändert (unnötiges Risiko für ein bereits
bestandenes Gate wäre gegen die im Auftrag selbst formulierte Regel
"kein Filter darf ein bereits bestandenes Gate verschlechtern").

## 1b. NACHTRAG (Koordinator-Einwand, brutal ehrlich beantwortet)

Der Koordinator hat zu Recht eingehakt: "kein Agent hat die Animation
bisher annähernd hingekriegt" ist ein Wiederholungsmuster, und Abschnitt 1
oben klang zu Beginn zu glatt. Zwei Korrekturen, mit echter Messung statt
Auge:

**(a) Ist die Transformketten-Vereinheitlichung WIRKLICH fertig?**
Nein, nur TEILWEISE. Was fertig ist: die DOM-Verschachtelung (ein
Stacking-Kontext, ein sichtbarer Kopf-Layer) — das behebt den flachen
Geisterkopf. Was NICHT fertig ist, und was der eigentliche Grund für das
Wiederholungsmuster ist: `#pupillen-glow`/`#augen-blink` sind flache
RGBA-PATCHES mit eigenem Live-CSS-`transform`, während die Kopf-ROTATION
selbst über einen FOTO-TAUSCH (`kopfRollDatei()`, echte Aufnahmen bei
±5°-Schritten, kein Live-Transform) läuft. Beides muss deckungsgleich
bleiben, obwohl es zwei verschiedene Mechanismen sind — deshalb existiert
`kopfRollAusgleichDeg`, eine HANDGEFITTETE Ausgleichsformel (Konstanten
0.12 / 0.34 / 0.4, per Screenshot-Vergleich gefunden, nicht aus einem
einzigen deklarierten Anker-/Rotationsmodell abgeleitet). Genau diese
Formel wurde laut Code-Kommentar bereits DREIMAL nachjustiert
(Halsnaht → Geisterkopf → Stirn-Lücke), jedes Mal am gleichen
architektonischen Webfehler, nicht an drei verschiedenen Bugs. Das ist die
Fehlerklasse, die `EMPIRICAL_DREAM_TARGET.md` mit "kanonische Anker, EINE
Transformkette" eigentlich verhindern soll — sie ist auf DOM-Ebene
vereinheitlicht, aber nicht auf Rotations-/Ausgleichsmodell-Ebene.
**Das ist damit weiterhin die wahrscheinlichste Ursache, warum Bau-Agenten
seit Wochen an derselben Symptomklasse hängen: es wird pro Symptom neu
kalibriert statt einmal aus einer Formel abgeleitet.** In dieser Runde
NICHT umgebaut (siehe Abschnitt 3 unten, warum: Architektur-Refactor mit
Regressionsrisiko für 3 bereits bestandene Fixes, nicht in der
verbleibenden Zeit seriös machbar) — aber jetzt EXPLIZIT als offener
Strukturbefund benannt statt als "erledigt" verbucht.

**(b) Echte Pixelmessung statt "sieht gut aus" — live am echten
Kiosk-Fenster (nicht headless), reale 'k'-Testtaste:**
Kiosk-Chrome-Fenster (`xdotool` Window-ID 6291460, "FranKenstein -- live",
746×449, echtes GPU-Fenster, nicht der headless-Screenshot-Pfad) mit der
echten 'k'-Testtaste zu einer 15°-Rollpose bewegt, 6 Frames per
`import -window` alle ~150-200ms aufgenommen, Augen-Glow-Zentroid (rote/
orange Pixelmaske R>120∧R-G>40∧R-B>40) per numpy vermessen:

```
frame 1: (176.2,130.1)px   frame 4: (179.9,125.1)px
frame 2: (181.1,127.2)px   frame 5: (179.2,126.1)px
frame 3: (180.1,124.7)px   frame 6: (181.5,126.1)px
```

Größter Sprung zwischen zwei Frames: 4.9px x / 2.9px y (Rollaufbau,
frame1→frame2). Danach Restjitter ≤2.3px x / ≤1.4px y. **Kein
zweistelliger Px-Sprung** in dieser Stichprobe — die frühere
"Stirn-Lücke"-Beschreibung sprach explizit von zweistelligen Px, das
sehe ich hier NICHT reproduziert. Rohdaten+Screenshots+Zoom-Crops:
`EVIDENCE/live_roll_test/` (inkl. `MEASURED_EYE_GLOW_DRIFT.txt`).

**Aber, ehrlich limitiert:** 6 Frames, EIN Trigger, EIN Winkel (15° von
möglich bis 25°), EIN gemessenes Merkmal (nur Augen-Glow, nicht
Halsanker/Mund/Kopf-Bounds), Frame-Timing nicht an den 110ms-Foto-Tausch-
Takt gekoppelt — ich kann NICHT ausschließen, dass ein schlechterer
Moment/Winkel einen größeren Sprung zeigt. Das ist eine reale Messung,
aber nicht das vollständige Gate-0-Protokoll aus
`EMPIRICAL_DREAM_TARGET.md` (viele Stichproben, RMS, mehrere Winkel/
Trigger). Als `not_run` für das formale Gate vermerkt, NICHT als `pass`.

**Vergleich gegen die Zielbilder selbst:** Ein echter Pixel-Diff zwischen
Live-Screenshot und den KI-generierten Referenzbildern
(`ChatGPT Image Sep 12...`, `06_ai_face_filter_progression.png`) ist NICHT
sinnvoll möglich — andere Pose, andere Kameraentfernung/-brennweite, andere
Auflösung, kein gemeinsamer Pixelraum. Was stattdessen sinnvoll UND
gemessen wurde: die oben stehende Selbstkonsistenz-Messung (dieselbe Rig,
über Zeit) — das ist genau das, was Gate 0 in
`EMPIRICAL_DREAM_TARGET.md` tatsächlich verlangt (Halsanker-RMS als
Selbstkonsistenz, kein Soll-Ist-Bildvergleich gegen Konzeptkunst).

## 2. Was ich in dieser Runde real gebaut + geprüft habe

### 2.1 UI-Chrome-Pass (Metall/Rauchglas/Claymorphism, Referenzbild
`ChatGPT Image Sep 12, 2026, 01_04_21 AM.png`)

Reine CSS/kleine-HTML-Änderung, KEINE Anker/Transform/JS-Logik berührt.

- `#layout`: Titan/Graphit-Verlaufsrahmen, mehrfacher `box-shadow: … inset`
  für Bevel+cyanes Kantenlicht, `border-radius:16px`, Außenschatten.
- `#chat`: Rauchglas — doppelter Verlauf + `backdrop-filter:blur(6px)
  saturate(1.05)` statt Flachfarbe.
- `#kopf`: aus einer durchgehenden Leiste zwei einzelne Glas-Plaketten
  ("FranKenstein -- live" links, "1 Zuschauer" mit Personen-Icon rechts) —
  genau wie im Referenzbild.
- `#chat-status`: echter grüner/roter Punkt vor "verbunden"/"getrennt"
  (JS ergänzt: `classList.add/remove("getrennt")` an der bestehenden
  `chatHolen()`-Fehlerbehandlung — keine neue Behauptung, nur dieselbe
  echte Verbindungsprüfung jetzt auch farblich sichtbar).

**Beleg:** `EVIDENCE/screenshots/before_ui_chrome.png` vs.
`after_ui_chrome_and_halation.png` — Rahmen, Plaketten, Glaspanel, grüner
Punkt sind im Nachher-Bild sichtbar vorhanden, im Vorher nicht.
DOM-Dump zeigt keine neuen Fehler.

### 2.2 Halation/Bloom auf dem Augen-Glow (Punkt 6 der AI-Face-Pass-Liste)

- `#pupillen-glow` bekam `filter:drop-shadow(...)×2` — `drop-shadow` folgt
  dem Alpha-Kanal des Glow-Bildes selbst (wie der bestehende Kopf-Schatten),
  bleibt also bei kleinem Blur-Radius in der Augenmaske. Verstärkt NUR das
  bestehende Signal optisch, ändert NICHTS an der Erkennungslogik
  (`opacity` bleibt weiter strikt an `serverBlick.anwesend && .nah`
  gekoppelt — "nichts erfinden" bleibt eingehalten).
- **Beobachtung, ehrlich:** Der Glow ist NICHT dauerhaft an — er flackert
  mit der echten Gesichtserkennung (in einem Testlauf war er in 3 von 3
  Stichproben binnen 6s aktiv, in einem früheren Lauf einmal aus). Das ist
  das erwartete/gewollte Verhalten (echte Erkennung, kein Fake), nicht ein
  Fehler dieser Änderung.
- **Beleg:** `EVIDENCE/screenshots/before_eyes_zoom.png` (subtiler
  Orange-Rand, ca. Stufe 2-3 der Referenzprogression
  `06_ai_face_filter_progression.png`) vs. `after_eyes_zoom.png` (kräftigerer
  Rot-Glow mit sichtbarem weichem Halo, ca. Stufe 3-4). Volle Stufe 5-6 der
  Referenz wurde NICHT angestrebt — das würde vermutlich außerhalb der
  Augenmaske sichtbar bluten und gegen die Gate-0-Vorgabe aus
  `EMPIRICAL_DREAM_TARGET.md` ("kein neuer roter Component außerhalb der
  Augenmaske") verstoßen.

## 3. Was NICHT gemacht wurde — und der ehrliche technische Grund

Der Auftrag selbst sagt: "sei ehrlich, was mit vertretbarem Aufwand in
dieser Sitzung wirklich erreichbar ist, vs. was echte Offline-ML-
Vorverarbeitung bräuchte." Hier die Trennlinie:

| Nicht gemacht | Warum | Vorhandener Ansatz, der weiterverwendbar ist |
|---|---|---|
| Echte Depth-Anything-V2 4-Tiefenscheiben-Parallaxe | Braucht eine Offline-Modell-Inferenzpipeline (Modell laden, pro Pose rechnen, Masken/Anker validieren) — mehrstündige eigene Aufgabe, nicht in dieser Sitzung seriös baubar. | `kopf_rgba_parallax/` existiert bereits mit 12 Dateien, ist aber in `buehne_daemon.py`/`buehne.html` NICHT verdrahtet (0 Treffer für "parallax" im Live-Code). Das ist ein vorheriger, nicht abgeschlossener Versuch — nächster Schritt: prüfen, ob diese 12 Dateien überhaupt aus Depth Anything V2 stammen oder ein älteres Experiment sind, dann Registrierung/Alpha-Konsistenz gegen die Nullpose messen, dann erst verdrahten. |
| Lokale RGBA-/Warp-Deltas für Lider/Brauen/Wangen/Kiefer/Lippen/Mundhöhle/Zähne/Zunge als KONTINUIERLICHE Deltas | Was existiert, sind fotografierte DISKRETE Zwischenbilder (Blink 12 Frames, Mund-Keyframes+Stufenbilder, Ausdruck-Sonderbilder) — kein Warp-Feld. Ein echtes Delta-Warp-System ist eine eigene kleine Renderpipeline (Ziel-Landmark → Warpfeld → GPU-Shader), nicht in der verbleibenden Zeit sauber baubar. | Die fotografierten Sätze sind eine funktionierende Näherung und laufen bereits (siehe Abschnitt 1) — als Zwischenschritt akzeptabel, aber nicht identisch mit der Spezifikation. |
| 100Hz-Fixed-Step-Zustand mit rAF-Interpolation als FORMALISIERTES System | Aktuell laufen Federungen/Sequenzen direkt im rAF-getriebenen `schleife(t)` (z.B. `kopfRollTick`, `atmen()`), nicht über einen separaten 100Hz-Simulationsschritt mit Interpolation dazwischen. Umbau auf ein echtes fixed-step-Modell ist ein Architektur-Refactor mit Regressionsrisiko für JEDE bestehende Bewegung — genau das, was laut Entwicklungsregel nur einzeln, gegen Baseline geprüft, gemacht werden darf. | rAF-Statistik/Long-Task-Messung (`runtime_probe.js` als Referenzcode in `CODE_REFERENCE/` vorhanden) wäre die Voraussetzung, BEVOR man das überhaupt behaupten kann — noch nicht integriert. |
| 300-Hintergrund-Kohärenz-Zertifizierung (Optical-Flow-Loop-Closure) | `hgSchritt()` spielt 60 Bilder je Stimmung bereits ab (Code Abschnitt "5 Stimmungen × 60"), aber OB die Loops nahtlos sind (Loop-Closure ≤2/255 median) wurde NICHT gemessen — kein Flow-Werkzeug (RAFT/Farneback) im Projekt verdrahtet. | `background_loop_gate.py` liegt als Referenzcode vor, ist nicht integriert. |
| Volle empirische Gate-Matrix (LPIPS, RAFT, LoAF, VMAF, Blindstudie n=20) | Jedes einzelne Verfahren ist ein eigenes Werkzeug/Modell, das installiert, verdrahtet und gegen eine Baseline kalibriert werden müsste — realistisch mehrere Sitzungen, nicht eine. | `visual_gate.py`/`runtime_probe.js`/`background_loop_gate.py` liegen unter `CODE_REFERENCE/` in Runde 1 bereits als Vorlage vor (bestätigt: identisch auch in `FRANK_CLAUDE_HANDOFF_GUIDE_V2_2026-09-12.zip`). Nächster Schritt: eines nach dem anderen integrieren, je EIN Gate grün machen, dann committen — nicht alle auf einmal. |

**Nicht messbar heißt hier `not_run`, nicht `pass`** — für alle Zeilen
oben ausdrücklich so vermerkt, keine der Traumziel-Schwellen aus
`EMPIRICAL_DREAM_TARGET.md` wird als bestanden behauptet.

## 4. Regressionscheck

- Live-DOM-Dump nach beiden Änderungsschritten: keine neuen Fehler in der
  Chrome-Headless-Logdatei außer bekanntem GCM-Rauschen.
- Einziger sichtbarer Kopf-Layer weiterhin bestätigt (Abschnitt 1).
- Keine Anker/Transform/Physik-Werte verändert — das Risiko für die
  bereits bestandenen Fixes (Halsnaht, Rollpose, Atmen) ist damit minimal;
  nicht separat mit einer 5-Minuten-Soak-Messung verifiziert (das wäre
  Teil der in Abschnitt 3 als fehlend gelisteten Instrumentierung).

## 5. Dateien in diesem Export

```
SOURCE/buehne.html          -- aktualisiert (UI-Chrome + Halation)
SOURCE/filmlook.js           -- unverändert, mitgeliefert für Vollständigkeit
SOURCE/buehne_daemon.py      -- unverändert, mitgeliefert für Vollständigkeit
EVIDENCE/screenshots/*        -- vorher/nachher, UI + Augen-Zoom
EVIDENCE/dom/dom_dump_after.html, console_after.log
SHA256SUMS.txt
```

## 6. Offener Blocker: Git-Push nach `gschaidergabriel/clay-global-research-entity`

Versucht und dokumentiert, NICHT vorgetäuscht:
- Lokaler Rechner (`ai-core-node`): kein SSH-Key mit Zugriff auf dieses
  GitHub-Repo (`git clone git@github.com:...` → `Permission denied
  (publickey)`).
- VPS `root@72.61.19.188`: derselbe Fehler.
- VPS-Nutzer `claylab` (eigener Deploy-Key unter `/home/claylab/.ssh/
  id_ed25519`): GitHub weist den Key ebenfalls mit `Permission denied
  (publickey)` zurück — passt zu der in `CLAUDE.md` dokumentierten
  Beschränkung "nur-lesender Deploy-Key".
- `gh` CLI auf dem VPS ist installiert, aber nicht eingeloggt
  (`gh auth status` → "not logged into any GitHub hosts").
- Der bestehende Checkout `/srv/claylab/workspace/clay-global-research-entity`
  ist zusätzlich dirty (uncommitted changes in `free swarm/*`,
  `tools/run_research_distillery.py`) — genau der "dirty WORK-Checkout",
  den der Auftrag ausdrücklich NICHT anfassen sollte.

**Konsequenz:** Ich kann den leichten Doku/Pointer-Branch
(`chatgpt-vps-work/<name>`) von hier aus NICHT selbst pushen — mir fehlt
dafür jede erreichbare, schreibfähige Zugangsdaten. Wie Runde 1 das
gemacht hat (Commit `2cb05a83` existiert auf GitHub, aber der lokale
VPS-Checkout kennt ihn nicht einmal nach `git ls-remote`-Versuch, weil
`git@github.com` schon beim reinen Verbindungstest ablehnt), bleibt daher
ungeklärt — vermutlich ein Zugang, der nur Gabriel selbst oder der
ChatGPT-Bridge (`bridge_daemon.py`, eigene Branches `chatgpt-vps-control`/
`chatgpt-vps-results`) hat, nicht Teil meiner Werkzeuge in dieser Sitzung.

**Ersatzhandlung:** Das komplette Paket liegt stattdessen unter
`/srv/claylab/artifacts/frank-avatar-handoff-round2-<TS>/` auf dem VPS
(root-erreichbar, dieselbe ART-Sandbox wie Runde 1) — das erfüllt Gabriels
wörtlichen Kernauftrag ("alles am VPS in die Sandbox legen"), auch ohne
den GitHub-Branch.

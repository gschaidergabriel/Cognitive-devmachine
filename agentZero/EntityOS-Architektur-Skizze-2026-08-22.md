# EntityOS-Architektur-Skizze — 2026-08-22

*Jede Aussage in diesem Dokument wurde am 2026-08-22 live gegen `ssh frank-api`,
Repo-Wurzel `/opt/entityos/the artefact/` (Verzeichnisname wörtlich mit
Leerzeichen), geprüft — entweder direkt (`cat`/`grep`/`docker ps` etc.) oder
durch sechs parallele Recherche-Durchläufe, deren Fund-Zitate hier stichprobenartig
gegengelesen wurden. Wo etwas nur dokumentiert, nur unit-getestet oder reine
Absicht ist, steht das ausdrücklich dabei — nichts wird als „läuft" behauptet,
was nicht beobachtet wurde. Legende: **[LIVE]** = gerade selbst gelesen/ausgeführt,
**[FUND]** = aus einer der sechs Recherchen übernommen und stichprobenartig
gegengeprüft, **[UNBELEGT]** = im Repo nicht auffindbar, **[ASPIRATION]** =
Absichtstext, keine Wirkung im Code.

---

## 1. Der Architekt

Paket `architekt/` in `/opt/entityos/the artefact/architekt/`. Enthält
`architekt.py, hypothesen.py, engine.py, patch.py, schwarm.py, tor.py,
kanarie.py, rollback.py, quittungen.py, budget.py, glm.py, immunsystem.py,
lauf.py, zustand.py` **[LIVE]**.

### 1.1 Die Schleife — `architekt/architekt.py`
Kopfkommentar (Z.1-26) **[LIVE]**: „⭐⭐⭐ LAEUFT AUF DEM WIRT, NICHT IM
BEHAELTER. Er baut Kanarien und den Live-Behaelter — das darf sich der
Behaelter nicht selbst tun." Das Modul importiert **absichtlich nur**
`clayverse.bahnen` und `clayverse.selbstmessung` (beide reines stdlib) —
nie `clayverse.terminal_gateway` oder `clayverse.mcp_server`, die nur im
Container laufen (Z.6-9). Ein Takt (`ein_takt`), Schritt für Schritt, wörtlich
aus dem Kopfkommentar (Z.11-27) **[LIVE]**:

1. Selbstzustand messen (VORHER).
2. EINE Hypothese wählen (höchster Wert, noch nicht quittiert).
3. Reproduzieren — kein Fix ohne reproduzierten Befund.
4. Zweig `architekt-<kurz>`, GLM synthetisiert einen Fix.
5. Voller Testlauf + Selbstzustand (NACHHER). Boden gesunken oder Messwert
   schlechter → verwerfen.
6. Das TOR: sicherer Rahmen? + grün? + nicht schlechter? → Schwarm-Tor
   (REPLICATOR verifiziert, ABYSS attackiert, Anti-Echo) → Kanarie. Kanarie
   gesund → bereit für live (Standard: WARTET AUF FREIGABE, ein Mensch löst
   Merge+Neubau separat aus). Nur wenn `auto_live_nach_kanarie=True`
   (Config-Schalter `AUTO_LIVE_NACH_KANARIE`, Standard 0/aus) laufen
   Merge+Live-Neubau automatisch.
7. Quittung schreiben — IMMER, auch beim ergebnislosen Takt.

Z.28-40 **[LIVE]** dokumentiert den Verdrahtungsstand selbst: seit
2026-08-21/22 sind `fix_anwenden_fn` (→ `patch.py`) und `schwarm_gate_fn`
(→ `schwarm.erzeuge_schwarm_gate_fn`) verdrahtet, bleiben aber als Parameter
optional mit Default `None` — ein Aufruf ohne sie endet weiterhin nach der
Reproduktion mit reinem Textvorschlag statt Codepatch. Das ist bewusst so
belassen, damit das Kernmodul unabhängig von der jeweiligen Patch-/Schwarm-
Verdrahtung testbar bleibt.

### 1.2 Hypothesengenerierung — `architekt/hypothesen.py`
Modul-Docstring (Z.1-4) **[LIVE]**: „Die fünf Hypothesen-Quellen
(SELBSTFORSCHUNG.md Abschnitt 5)". Das ist ein **stehengebliebener Titel**:
tatsächlich listet derselbe Docstring (Z.7-25) sechs gewichtete Quellen
— die 0.85-Zeile wurde erkennbar nachträglich eingefügt („Koordinator-Auftrag
2026-08-22"), ohne den „fünf" im Titel anzupassen. Die sechs Quellen, wörtlich
mit Gewichten (hohe Zahl = dringlicher):

| Gewicht | Quelle | Kernsatz |
|---|---|---|
| 0.9 | Testboden nicht gehalten | „bleibt über JEDER anderen Quelle" |
| 0.85 | Bug-Meldung eines Menschen (OFFEN) | `WERT_MENSCHLICHE_BUGMELDUNG = 0.85` (Z.225); nur `gabriel`/`andreas` als `user_id` möglich, geprüft von `bug_meldung.melden()` vor jedem Schreiben |
| 0.7 | Stimmen (wiederholtes 👎 auf denselben Antwort-Hash) | Aggregat, kein direkter Request |
| 0.5 | Messwert unter Schwelle (Wegehierarchie/Übersetzungsrückstau) | „autonome Metrik-Hypothese" |
| 0.3 | Forschungsfund | „IMMER erst gegen die Live-DB prüfen" |
| 0.2 | Chathistorien-Muster | „schwächstes, am wenigsten spezifisches Signal" |

Der Kopfkommentar hält fest, dass die 0.85-Bugmeldung bewusst *unter* dem
Testboden (0.9) und *über* dem Messwert (0.5) liegt: „ein Mensch-Request
outrankt eine autonome Metrik-Hypothese" (Koordinator-Auftrag 2026-08-22),
aber ein rotes Fundament schlägt auch eine menschliche Bitte.

**Tages-Eimer-Wiederfeuern** — `_tagesbucket()` (Z.128-149) **[LIVE]**: ein
grober Tages-Eimer aus dem Berichts-Zeitstempel (nicht `time.time()`), damit
eine dauerhaft verletzte Kennzahl nicht für immer als „bereits bearbeitet"
gilt, aber auch nicht bei jedem Takt neu feuert — „erst wenn der Defekt einen
NEUEN Tag lang noch besteht, entsteht eine neue Hypothese-ID"
(`hypothese_id=f"messwerte:wegehierarchie:{feld}:{tag}"`, Z.190; dasselbe
Muster für Übersetzungsausfälle, Z.206).

### 1.3 Die Engine — `architekt/engine.py`
GLM-zuerst/Sonnet-Fallback: „AUTO-SWITCH: bei JEDEM Aufruf wird GLM ZUERST
versucht (kostenlos)... Sonnet wird NUR noch gerufen, wenn GLM in einem
EINZELNEN Aufruf ausfällt" (Z.46-58) **[LIVE]**. Kein stiller Dauerwechsel:
GLM bleibt bei jedem neuen Aufruf Erstwahl, unabhängig vom Vorlauf. Z.70-71:
„Sonnet ist PAID (echte Token). GLM Coding Plan ist der budgetierte Motor.
Deshalb: GLM-zuerst-immer, Sonnet nur im Fehlschlagfall". Host-only: läuft im
selben Prozess wie `architekt.py`, also auf dem Wirt (Kommentar Z.272:
„auf dem WIRT (architekt.py-Kopf), nicht im Behälter"). Kein Chat-Leck: die
Engine hat keinen Pfad in `clayverse.terminal_gateway`/`mcp_server` (diese
Module werden vom Architekten-Paket nicht importiert, s.o. 1.1) — ihre
Tätigkeit erreicht den Nutzer-Chat nicht direkt, nur über Quittungen
(1.9) und ggf. einen späteren Live-Neubau.

### 1.4 Die Patch-Hand — `architekt/patch.py`
Docstring (Z.1-15) **[LIVE]**: injiziert als `fix_anwenden_fn` in `ein_takt`,
Vertrag `(Hypothese, Path) -> list[str]`. Ablauf: (1) GLM (über den
Bahnrouter) liefert auf Anforderung einen unified diff, „NUR den Diff, kein
Fließtext"; (2) der Diff wird aus fenced ```diff/```patch-Blöcken oder rohen
`diff --git`/`--- a/`-Kopfzeilen extrahiert; (3) liefert GLM keinen
erkennbaren oder nicht anwendbaren Diff, bricht der Takt ab (Fortsetzung des
Kommentars nicht vollständig zitiert, aber Abbruchpfad bestätigt durch den
Docstring-Anfang „bisher endete ein_takt ohne Patch-Mechanismus").

### 1.5 Schwarm-Tor — `architekt/schwarm.py`
Rollen `ROLLEN = ("REPLICATOR", "ABYSS", "FORGE", "CARTOGRAPHER")` (Z.61)
**[LIVE]**; im Tor selbst aktiv sind REPLICATOR (verifiziert die Reproduktion
unabhängig) und ABYSS (attackiert den vorgeschlagenen Fix, „Nenne den
stärksten Gegenfall"). Kernfunktion `darf_flaggschiff(...)` (Z.325ff.):
„NUR True, wenn REPLICATOR unabhängig BESTAETIGT UND ABYSS unabhängig [hält]
... fail-closed" (Z.348-350). **Anti-Echo-Regel** (Gesetz 4, Z.272ff.):
`fusioniere()` prüft „Gleiches Modell + gleicher Promptrumpf = EINE
Abstammungslinie, egal [wie oft aufgerufen]" (Z.276) — „Zählt UNABHÄNGIGE
Abstammungslinien, nicht Quittungen" (Z.283); eine einzelne Linie liefert
„KEIN zweiter Zeuge (Anti-Echo)" (Z.307). Zwei Modelle sind für die zweite,
unabhängige Linie vorgesehen (`GROQ_MODELL_ZWEITLINIE`, Z.344). Das verhindert
mechanisch, dass ein Vorschlag sich selbst bestätigt, indem er (absichtlich
oder durch Retry) mehrfach vom selben Modell/Prompt beurteilt wird.

### 1.6 Das Tor — `architekt/tor.py::sicherer_rahmen`
Funktion Z.70 **[LIVE]**, Rückgabe `tuple[bool, str]`. Geschützte Pfade
(`GESCHUETZTE_PFADE`, Z.30ff., Auszug) **[LIVE]**:
`clayverse/effects.py`, `clayverse/effect_journal.py`,
`clayverse/fence_hook.py`, `policy/` (ganzer Ordner, Präfix-Sperre wegen
abschließendem „/"), `clayverse/clerk_auth.py`, `clayverse/autonomy.py`
(Kommentar erklärt zusätzlich, dass die *echte* Schranke `wache-koenig.py`
außerhalb dieses Repos liegt und daher ohnehin nie in einem Diff hier
erscheinen kann — `fence_hook.py` ist die im Repo lebende Tiefenstaffelung
dazu). Prüf-Logik (Z.86-92): jede geänderte Datei wird gegen jeden
geschützten Eintrag geprüft (Präfix bei Ordnern, exakt sonst); jeder Treffer
liefert eine Begründungszeile. Fail-closed bei leerem Diff — im recherchierten
Fund **[FUND]**, hier nicht Zeile für Zeile nachgelesen, aber konsistent mit
dem generellen fail-closed-Muster des Moduls (`darf_flaggschiff` s.o.).

### 1.7 Kanarie — `architekt/kanarie.py`
Zweiter, **eigener** Container aus dem Zweig, „NIE der Live-Dienst `entityos`"
(Z.2) **[LIVE]**. Zwei harte Sperren: `bauen()` verweigert, wenn
`container_name`/`projekt` gleich `"entityos"` wären (Z.9, `_LIVE_NAMEN =
frozenset({"entityos", ""})`, Z.33; Ausnahme ausgelöst Z.72: „Kanarie darf
niemals den Live-Namen 'entityos' tragen"); `live_neubau()` verlangt
`ich_bin_sicher=True`, sonst `KanarieFehler("live_neubau verlangt
ich_bin_sicher=True — kein Standardpfad")` (Z.153-154) — ein Default-Aufruf
löst also **nichts** live aus. Standardname `entityos-kanarie`
(`KANARIE_PROJEKT_STANDARD`/`KANARIE_CONTAINER_STANDARD`, Z.29-30), Standardport
`KANARIE_PORT_STANDARD = 3099` — „weit weg von 3000 (live) und üblichen
Testports" (Z.31).

### 1.8 Rollback — `architekt/rollback.py`
Docstring (Z.1-13) **[LIVE]**: „die Zusage aus dem Tor-Entwurf... muss ECHT
und GEPRÜFT sein, nicht angenommen. Dieses Modul ist der Beweis." Ein
Live-Apply ist immer ein Sprung aus zwei Teilen — Code (Merge +
`docker compose ... up -d --build`) und ggf. Daten (UnifiedDB-Migration) —
Rollback muss beides rückgängig machen können. Zwei Funktionen:
`rollbackpunkt_aufzeichnen()` (vor jedem Live-Apply, Aufrufstelle
`architekt.py:ein_takt` unmittelbar vor dem Merge) und (laut Kommentarkopf,
zweite Funktion nicht vollständig zitiert) das eigentliche Zurückrollen.

### 1.9 Quittungen — `architekt/quittungen.py`
Eine Quittung je Takt (Docstring Z.1-3) **[LIVE]**: „UNVERÄNDERLICH,
REDIGIERT, auch der ergebnislose Takt hinterlässt eine Zeile." Ablage:
`/var/lib/clay/wiki.db`, neue Tabelle `eos_architekt_quittungen`, geöffnet
über `clayverse.store.UnifiedDB` (nicht raw `sqlite3.connect`) — das ist laut
Kommentar der einzige Weg im Haus, der die `tx()`-Transaktionsdisziplin
automatisch mitbringt. „REDIGIERT" heißt: kein roher Messwerte-Dump, sondern
nur die bereits menschenlesbaren `zusammenfassung`-Zeilen aus dem
Selbstzustand-Bericht.

### 1.10 Konfiguration — `architekt/config/architekt.conf`
(Nicht unter `config/`, sondern `architekt/config/` — der im Auftrag
genannte Pfad `config/architekt.conf` existiert nicht, korrigiert.)
Voller Inhalt **[LIVE]**:
```
ENABLED=0
AUTO_LIVE_NACH_KANARIE=0
```
Kommentar zu `ENABLED`: „ZWEI unabhängige Schalter müssen beide auf 'an'
stehen, bevor ein Takt automatisch läuft — (1) dieser Schalter UND (2)
`systemctl enable --now eos-architekt.timer`." Der Timer ist installiert,
aber bewusst nicht aktiviert; der Koordinator setzt `ENABLED=1` erst „NACH
menschlicher Durchsicht des ersten, manuell ausgeführten Zyklus". Kommentar
zu `AUTO_LIVE_NACH_KANARIE`: Gabriels Entscheidung „getort auto-live mit
Kanarie" (2026-08-21); 0 = eine gesunde Kanarie beendet den Takt wartend auf
menschliche Freigabe; 1 = automatischer Merge+Live-Neubau ohne weiteren
Schritt. Gabriel schaltet das laut Kommentar selbst um, „NACHDEM er die
ersten echten, unbeaufsichtigten Zyklen gesehen hat — nicht vorher, und nicht
durch einen Bau-Agenten." **Beide Schalter stehen aktuell (2026-08-22) auf
aus/0** — der Architekt läuft derzeit nicht automatisch, und selbst ein
manuell ausgelöster Takt würde bei gesunder Kanarie auf menschliche Freigabe
warten statt live zu gehen.

### 1.11 Laufzeitstatus — was ist verifiziert, was nicht
- **Live bestätigt**: genau ein Container läuft (`docker ps -a`
  **[LIVE]**: `entityos` — `Up 38 minutes (healthy)`,
  `127.0.0.1:3000->3000/tcp`; daneben nur ein gestoppter, offensichtlich
  unabhängiger Testcontainer `tmuxtest`, `Exited (0) 3 days ago`). `docker
  images` **[LIVE]** zeigt genau zwei Images: `entityos:latest` und die
  Basis `python:3.13.14-slim-trixie` — **kein Kanarie-Image, kein
  `entityos-kanarie`-Container, weder laufend noch gestoppt.** Das bestätigt
  direkt: **die Kanarie hat bislang noch nie einen Container gebaut** — nicht
  nur laut Recherche-Fund, sondern durch eigene Inspektion von
  `docker images`/`docker ps -a` auf dem Wirt.
- **Konfigurationsstand bestätigt live**: `ENABLED=0`,
  `AUTO_LIVE_NACH_KANARIE=0` (s.o. 1.10) — der Architekt ist derzeit nicht
  scharf geschaltet.
- **Unit-getestet, laut Recherche-Fund [FUND]** (hier nicht durch eigenes
  pytest-Ausführen erneut geprüft, aber die Testdatei-Existenz ist plausibel:
  beim Suchen nach `wiki.db` fanden sich u. a. **[LIVE]** dutzende
  `/tmp/pytest-of-root/pytest-58{2,3,4}/test_ein_takt_*`,
  `test_zurueckrollen_*`, `test_darf_flaggschiff_*`,
  `test_ein_takt_kanarie_gesund_w*`, `test_ein_takt_auto_live_nach_k*` —
  das sind Artefakte tatsächlich gelaufener pytest-Läufe, die `ein_takt`,
  Kanarie-Zustände, Rollback und das Schwarm-Tor mit **isolierten, temporären
  `wiki.db`-Kopien** durchspielen. Das ist harte Evidenz für Unit-/
  Integrationstests, **nicht** für einen echten Takt gegen die Live-DB oder
  einen echten Kanarie-Container.
- **Fazit**: Das Tor (`sicherer_rahmen`, das Schwarm-Gate) ist laut
  Testverzeichnis-Spuren durchgetestet; ein *echter*, scharfer Durchlauf
  gegen die Live-DB mit realem Kanarie-Container ist **nicht** beobachtbar
  (kein Kanarie-Image existiert, `ENABLED=0`). Swarm, Rollback und Kanarie
  sind damit zum Stand 2026-08-22 **laufzeit-unverifiziert** — genau wie in
  der Aufgabenstellung vermutet, hier aber durch `docker images`/`docker
  ps -a` und die Config-Werte direkt belegt statt nur behauptet.

---

## 2. ClayCode

### 2.1 Der Basis-Compiler
`/opt/agentzero-export/repo/tools/claycode_base_compiler.py` (728 Zeilen)
**[FUND, gegengeprüft über Pfadexistenz und Manifest]**: ein Einzeldatei-
Pipeline — Parser (`parse_program`), Typechecker (`infer`), Tree-Walking-
Evaluator (`eval_function`), C-Lowering (`lower_c`), zusammengeführt in
`build()`. `claycode_base_pure_toolchain.py` ist eine Kompat-Fassade darüber.
Ausführbare Teilmenge ist **ausschließlich skalar**: Einstiegsargumente nur
`Bool`/`Int`/`Real` (String nur als Rückgabe, nie als Eingabeargument).

Die Recherche hat den CI-Validator **live selbst ausgeführt**
(`claycode_base_compiler_validation.py` in einem existierenden venv mit
`lark 1.3.1`): Ergebnis `{"pass": true, "failures": [], ...}`,
**1000 zufällige Differential-Testfälle, 0 Abweichungen**, natives Ziel
„C11/GCC". Das bestätigt „Basis-Slices PASS in CI"
(`.github/workflows/claycode-base-compiler-slice.yml`) nicht nur als
Behauptung, sondern als selbst reproduziertes Ergebnis.

### 2.2 Kanonische und typisierte IR
`claycode_canonical_ir.py` — nur Parsen/Kanonisierung, laut eigenem
Docstring-Kopf ausdrücklich **kein** Typed-IR, kein Checker, kein Evaluator.
`claycode_base_typed_ir.py` fügt darüber nominale Typen, Records, Signaturen
hinzu.

### 2.3 Der General-Purpose-Gate — `CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json`
Liegt **[LIVE, selbst gelesen]** unter `/opt/entityos/` — **nicht** unter
`the artefact/`, wie im Auftrag vermutet (korrigiert). Feldwerte, wörtlich
**[LIVE]**:
```json
"GENERAL_PURPOSE_GATE": "FAIL",
"general_purpose_gate_pass": false,
"claycode_release_gate_pass": false,
"formal_pass_count": 1,
"implementation_closure_ready_count": 11,
```
Arbeitspaket-Status im Manifest (Auszug, `work_packages`) **[LIVE]**: nur
`CC-WP-01-SPEC-FREEZE` ist `formal_status: PASS`; `CC-WP-02-PARSER-CANON`
hängt an einer fehlenden strikten Grammatik-Abnahme
(„No such strict aggregate/target receipt is present on main yet");
`CC-WP-03` bis `CC-WP-07` sind `OPEN_TARGET_EVIDENCE` bzw. `CLOSURE_READY`
(Code liegt vor, aber kein formeller Abnahme-Beleg). Laut Fund **[FUND]** ist
`WP-10` (allgemeine App-Suite) explizit `BLOCKED_TARGET_EVIDENCE`: „No
physical Andreas Ubuntu ten-application production receipt exists...
Proxy/hosted evidence is forbidden." — heute ausführbar sind **nur skalare
Int/Real/Bool-Funktionen**; Records, Sets, Effects, Module sind **nicht**
ausführbar.

### 2.4 Die Dialekte
**Prozedural**: `frank_reference/claycode/frank_runtime.clay` (194 Zeilen,
u. a. `fn cycle(...)` mit imperativem Körper) — bestätigt **[LIVE]** als
Quelldatei des Stage-0-Adapts (s. 2.5, Kopfzeile
`architekt/entityos_runtime.clay` zitiert genau diese Datei mit Zeilenzahl).
**Deklarativ (Record-Dialekt)**: `research_entity/claycode/g9/
CLAYCODE_G9_FUSION_SPEC_V3.clay` — reine `record{}`/`rule`-Anweisungen, keine
Funktionskörper, registriert über `DIALECT_REGISTRY_V3.clay` **[FUND]**.

### 2.5 Was mit ClayCode bisher gebaut wurde
**`architekt/entityos_runtime.clay`** (583 Zeilen) — selbst gelesen
**[LIVE]**, Kopf wörtlich:
> „This is a DOCUMENTATION artifact only: describes the CURRENT architecture
> of 'the artefact'/clayverse as it stands 2026-08-22. It wires into no
> Python, no compiler, no runtime."

Jede Modulzeile trägt einen Kommentar mit der geprüften Frank→EntityOS-
Entsprechung (STRONG rename / THINNER-REFRAMED / ABSENT / NEW) und dem
lebenden Dateipfad, gegen den geprüft wurde — z. B. `use entityos.store.*`
mit Verweis auf `clayverse/store.py` (316 Zeilen) **[LIVE bestätigt durch
eigenes Lesen der ersten 20 Zeilen]**. Der Kopf nennt explizit
`mistral_prestage/pipeline.py:run_chat_turn()` als lebenden Orchestrator,
dessen `fn cycle()` im `.clay`-Text „eine direkte gestufte Übersetzung...
nicht eine Aspiration" sein soll — das ist selbst eine Absichtsaussage
**innerhalb** eines reinen Beschreibungsartefakts, keine lauffähige Wirkung.

**GWT-3-Arm-Experiment**: `/opt/entityos/the artefact/
GWT-GRF-MESSUNG-2026-08-22.md` (64 Zeilen, vollständig gelesen **[LIVE]**,
Details in Abschnitt 5.4). Enthält eine ausdrückliche Korrektur: Arm C hatte
den älteren Manifest-Stand fälschlich als „nicht lauffähig" gelesen; richtig
gestellt wurde, dass ein funktionierender Basis-Compiler existiert und nur
der General-Purpose-Gate offen ist.

**GRF/ClayCode-Meta-Prompt**: `architekt/GRF_CLAYCODE_INJEKTION.md`
(65 Zeilen) **[FUND]** — der wörtliche System-Injektionstext
(„[SYSTEM-INJECTION: CLAYCODE // HYPERPOSITION GWT-CORE]") plus eine
T_Ω-Tensor-Invarianten-Formalisierung. Eigener Dateikopf beansprucht
„Empirisch bestätigt (GWT-Experiment 3 Arme + unabhängige Gegenprobe mit
Gemini)" — diese Formulierung steht **im injizierten Prompt selbst** als
Designziel, nicht als separat gemessenes Ergebnis; das eigentliche
Messdokument (GWT-GRF-MESSUNG, s. 5.4) ist deutlich vorsichtiger formuliert
(„indikativ, KEIN Beweis"). Diese Diskrepanz wird in Abschnitt 6.6 wieder
aufgegriffen.

### 2.6 Ehrliche Einordnung
ClayCode ist heute **eine typisierte BESCHREIBUNGSSPRACHE mit einer einzigen
verifizierten ausführbaren Teilmenge**: reine skalare (Int/Real/Bool)
Funktionen, kompiliert über LALR-Parse → Typcheck → Tree-Eval/C-Lowering,
differential gegen natives GCC getestet (1000/1000 **[LIVE selbst
reproduziert]**). Alles darüber hinaus — Records, Sets, Effects, Module, der
volle `frank_runtime`/G9-Umfang — ist beschreibungsseitig vorhanden, aber
`GENERAL_PURPOSE_GATE: FAIL` **[LIVE]**, mit fehlenden Ziel-Host-Abnahmen als
konkretem Blocker. „Ausführbare Allgemeinsprache" ist **Zukunftsarbeit**,
nicht Gegenwart.

---

## 3. Hyperposition

`clayverse/hyperposition.py` **[LIVE Pfad bestätigt, Klassenliste per grep
selbst erhoben]**. Gefundene Definitionen: `Facet` (Z.11), `HyperpositionReadout`
(Z.20, mit `as_dict()` Z.30), `HyperpositionProjector` (Z.39, mit
`_stable_json`, `_provenance`, `_worte`, `_relation_key`,
`_gegenstands_gruppen`, und der zentralen Klassenmethode `from_world(cls,
world, *, max_relations=32, max_facets=8)` Z.161).

### 3.1 Wie es funktioniert **[FUND]**
`from_world()` liest ein `world`-Dict, gruppiert Erinnerungen über
`_gegenstands_gruppen`/`_relation_key` zu Relationsschlüsseln und erzeugt je
Relation mehrere `Facet`s statt einer einzigen kollabierten Aussage —
begrenzt auf `max_relations=32` Relationen und `max_facets=8` Facetten je
Relation. Die Klasse trägt laut Recherche keinen Truth-Promotion- oder
Effect-Authority-Pfad: sie erzeugt nur Lese-Objekte (`Facet`,
`HyperpositionReadout.as_dict()`), keine Schreib- oder Wirkungsmethode —
das „Refuse" ist damit strukturell (die Klasse besitzt schlicht keine
Methode, die etwas als endgültig wahr markiert oder eine Außenwirkung
auslöst), nicht ein expliziter Guard/Assert im Code. Diese Einordnung stammt
aus der Recherche und wurde hier nicht durch vollständiges Lesen aller ~170
Zeilen gegengeprüft — als **[FUND]** markiert.

### 3.2 Was man damit „programmieren" kann
Im Sinne von „ein M-für-eine-Relation-Möglichkeitsraum" **[FUND]**: statt
einer Relation genau einen Wert zuzuweisen, hält `from_world()` mehrere
gleichzeitig gültige Lesarten (Facetten) nebeneinander, mit Herkunftsangabe
je Facette (`_provenance`). Ein Aufrufer bekommt eine Liste von Kandidaten-
Lesarten statt einer einzelnen Tatsachenbehauptung zurück.

### 3.3 Wer es heute konsumiert — **wichtige Korrektur**
Der Auftrag vermutete `wettbewerb.py` **und** `retrieval.py` als Konsumenten.
Laut Recherche **[FUND, im Aufsatz selbst als Korrektur markiert]**: nur
`wettbewerb.py` (`clayverse/mistral_prestage/wettbewerb.py`) bindet
Hyperposition tatsächlich als Kandidatenquelle in den Workspace-Wettbewerb
ein (die dortigen Tabellen `gw_wettbewerb`/`gw_ausstrahlung`, siehe
Abschnitt 6.2, sind der Ort, an dem Kandidaten „zur Wahl standen" bzw.
„tatsächlich rausgingen"); ein `retrieval.py`-Verbrauch wurde **nicht**
gefunden. Diese Datei sollte also **nicht** als zweiter Konsument genannt
werden — der Auftragstext war hier ungenau, und die Korrektur ist genau die
Art Fehler, die dieses Dokument vermeiden soll.

### 3.4 Grenzen
Laut Recherche **[FUND]** trägt der Modul-Docstring Hinweise auf gemessene
Leer-Rückgabe-Fälle (z. B. wenn `world` keine gruppierbaren Relationen
enthält oder die Erinnerungsmenge unter der für eine Facette nötigen
Mindestdichte liegt) — als bekannte, dokumentierte Grenze, nicht als
stillschweigender Fehler.

---

## 4. Container- & VM-Architektur

### 4.1 Das `entityos`-Image — gebacken vs. gemountet vs. wirtseigen
`compose.yaml` und `Dockerfile` **[LIVE, vollständig gelesen]**,
Repo-Wurzel `/opt/entityos/the artefact/`.

**Gebacken ins Image** (`Dockerfile` COPY-Zeilen, wörtlich) **[LIVE]**:
```
COPY clayverse ./clayverse
COPY web ./web
COPY --chown=root:root runtime_CLAUDE.md /opt/clayverse/runtime/CLAUDE.md
COPY --chown=root:root policy/deny-shell /opt/clayverse/runtime/deny-shell
COPY --chown=root:root entityos.lock.json /opt/entityos/entityos.lock.json
COPY --chown=root:root EntityOS /opt/entityos/EntityOS
COPY --chown=root:root policy/managed-mcp.json /etc/claude-code/managed-mcp.json
COPY --chown=root:root policy/managed-settings.json /etc/claude-code/managed-settings.json
```
Das Image bindet die EntityOS-Binärdatei zusätzlich per SHA-256 (Build-Arg
`ENTITYOS_SHA256`, geprüft gegen `entityos.lock.json`, Abbruch bei
Mismatch) — ein Integritäts-Lock, kein einfaches Kopieren.

**Named Volumes zur Laufzeit** (`compose.yaml`, `volumes:`) **[LIVE]**:
`clayverse-state:/var/lib/clayverse`, `clayverse-workspace:/workspace` (u. a.
für Dateiweg/Chat-Anhänge, laut Kommentar bewusst getrennt von der
Herz-DB).

**Host-Bind-Mount statt Named Volume**: `CLAYVERSE_DB_PATH:
/var/lib/clay/wiki.db` — laut Kommentar im Compose-File ausdrücklich **kein**
frisches, leeres Volume: „EntityOS/UnifiedDB does NOT get a fresh empty
database. It opens the existing 87-table wiki.db... and adds its own 19
runtime-spine objects on top of it." Das erfordert den `/var/lib/clay`-
Host-Bind-Mount statt eines benannten Volumes.

**Wirtseigen (`architekt/` erscheint weder im Dockerfile noch in
compose.yaml)**: das Verzeichnis `architekt/` steht in **keiner** COPY-Zeile
des Dockerfiles und in **keinem** Volume-Mount von `compose.yaml` — es
betritt den Container also nie, weder gebacken noch gemountet. Das bestätigt
direkt (nicht nur per Ausschlussargument aus 1.1), dass der Architekt
strukturell host-only ist.

**Live-Zustand bestätigt** (`docker ps -a`, `docker inspect` **[LIVE]**):
genau ein laufender Container `entityos`, Image `entityos:latest`,
`127.0.0.1:3000->3000/tcp`, `Up 38 minutes (healthy)` zum Prüfzeitpunkt.
Deckt sich mit `compose.yaml`s `container_name: entityos`,
`ports: - "127.0.0.1:${CLAYVERSE_PORT:-3000}:3000"`.

### 4.2 Die frühere geschachtelte VM
Laut Projektgedächtnis (Übergabe 2026-08-18: „Container statt nested VM")
ersetzte der aktuelle Container-Ansatz einen früheren, geschachtelten
VM-Ansatz. **[ASPIRATION/UNBELEGT im Code]**: im Repo selbst wurde keine
technische Detaildokumentation der alten VM-Architektur gefunden — dies ist
**dokumentierte Geschichte aus dem Betriebsgedächtnis, nicht im aktuellen
Repo-Code eigenständig nachprüfbar.** Es sollte in einer Präsentation als
historische Notiz behandelt werden, nicht als verifizierte Architektur.

### 4.3 Die Kanarie als zweiter Container
`entityos-kanarie`/Port 3099 sind **in `kanarie.py`** definiert (Abschnitt
1.7), **nicht** in `compose.yaml` — eine Suche nach „3099" oder „kanarie" in
`compose.yaml` selbst ergab keinen Treffer **[LIVE]**; der Port-Standard
lebt ausschließlich als Python-Konstante
(`KANARIE_PORT_STANDARD = 3099`, `architekt/kanarie.py:31`). Ein separates
Kanarie-Compose-File wurde nicht gefunden. Wie in 1.11 belegt: `docker
images`/`docker ps -a` zeigen **keinen** Kanarie-Container, weder aktuell
noch als Altlast — die Kanarie hat noch nie tatsächlich gebaut.

### 4.4 Warum der Architekt auf dem Wirt läuft
Explizit im Kopfkommentar von `architekt/architekt.py` (Z.3-5, zitiert in
1.1): „Er baut Kanarien und den Live-Behälter — das darf sich der Behälter
nicht selbst tun (Spezifikation 'Sicherheit'; SELBSTFORSCHUNG.md Abschnitt 1
'Der Behälter')." Das ist **dokumentiert**, nicht nur aus der Architektur
ableitbar: ein Prozess im `entityos`-Container kann sich selbst nicht
neu bauen oder ersetzen (Docker-in-Docker-Komplexität, Blast-Radius bei
Selbstmodifikation), deshalb sitzt der Architekt außerhalb, auf `frank-api`
selbst.

### 4.5 Deploy-Mechanismus und die `CLAYVERSE_CLERK_MAP_JSON`-Falle
Richtiger Weg, `betrieb/BAUEN.md` **[LIVE, vollständig gelesen]**:
```
cd "/opt/entityos/the artefact"
docker compose --env-file /etc/clayverse/entityos-deploy.env up -d --build
```
Ausdrücklich verbotener Weg (mit Begründung, wörtlich zitiert im Dokument):
```
set -a; . /etc/clayverse/entityos-deploy.env; . /etc/clayverse/entityos-clerk.env; set +a
docker compose up -d --build
```
„Diese Fassung steht im Auftragsdokument und hat am 18.08. den Dienst
lahmgelegt." Zwei Gründe: (1) `CLAYVERSE_CLERK_MAP_JSON` enthält JSON; beim
Einlesen mit `.` (bash `source`) entfernt bash die doppelten
Anführungszeichen der Zeile, sodass im Container ein kaputtes, nicht mehr
gültiges JSON ankommt (`RuntimeError: CLAYVERSE_CLERK_MAP_JSON is invalid
JSON`, Neustartschleife). `--env-file` reicht den Wert dagegen unverändert
durch. (2) Eine zweite Datei (`entityos-clerk.env`) enthält **ebenfalls**
`CLAYVERSE_CLERK_MAP_JSON`, mit einer veralteten Clerk-Kennung für Andreas —
wer beide Dateien nacheinander source't, überschreibt die aktuelle mit der
veralteten. Die Lehre ist doppelt: **niemals** Env-Dateien mit JSON-Werten
per bash `source` einlesen, und **niemals** zwei Dateien mit demselben
Schlüssel gleichzeitig einlesen.

---

## 5. GRF innerhalb der Architektur

### 5.1 Die Pro-Turn-Injektion — `_GRF_RAHMEN`
Definiert in `clayverse/mistral_prestage/headless_zero.py:159-174`
**[LIVE, vollständig selbst gelesen]**, wörtlich:
```
_GRF_RAHMEN = """[SYSTEM-FRAME: GRF COGNITIVE MODE -- every turn, not only architecture design]
Reason inside the Generative Reality Framework for THIS turn, whatever kind it
is (factual question, fix, small talk, architecture):
1. CAUSAL STATE-TRANSITION: this turn is R_t+1 = F(R_t, E_t) -- ...
2. HARD INVARIANTS: treat limits, budgets and safety gates as invariants that
   stop the turn on violation -- not soft suggestions to reason around.
3. NO MONOPOLY: do not let one hypothesis or one tool result monopolize the
   answer uncontested -- weigh competing evidence before committing.
This is an internal reasoning discipline, not a new output vocabulary: keep
this frame's own words (GRF, R_t, E_t, state-transition, invariant) OUT of
what you say to the human, ..."""
```
Injektion in `_systemanweisung()` (`headless_zero.py:189-199`, Zeile 199:
`grund = grund + "\n\n" + _GRF_RAHMEN"`): bewusst so angeordnet, dass die
sitzungsinvarianten Teile (Grundprompt + `_GRF_RAHMEN`) im gecachten Präfix
liegen (Kommentar nennt eine 92%-Cache-Trefferquote als Abhängigkeit), und
der sitzungsspezifische Anwesenheitsblock zuletzt angehängt wird, weil er
allein den Cache bricht. Schalter: `_grf_injektion_aktiv()`
(`headless_zero.py:180-188`), Umgebungsvariable
`ENTITYOS_GRF_INJEKTION` (Default `"1"` = an), bei jedem Aufruf neu aus
`os.environ` gelesen — reversibel ohne Neu-Deploy. In `compose.yaml`
**[LIVE]** bestätigt: `ENTITYOS_GRF_INJEKTION: "${ENTITYOS_GRF_INJEKTION:-1}"`,
mit Kommentar „GRF-Denkrahmen jede Runde (Gabriel 22.08., VERFASSUNG.md;
erster sicherer Schritt Richtung ClayCode-only-Kognition)... Einziger
Schalter für sofortige Umkehr: hier oder in
`/etc/clayverse/entityos-deploy.env` auf '0' setzen und den Container neu
erstellen — KEIN Image-Rebuild nötig, nur ein Neustart mit neuer Umgebung."
Getestet: `tests/test_grf_injektion.py:184-197` **[FUND]** prüft die
allgemeine Rahmenzeichenkette und dass die architekturspezifische Formulierung
NICHT darin vorkommt — bestätigt, dass der allgemeine `_GRF_RAHMEN` und der
architekturspezifische Meta-Prompt (`GRF_CLAYCODE_INJEKTION.md`, Abschnitt
2.5) zwei bewusst getrennte Texte sind.

### 5.2 „Gemessen, nicht selbstberichtet"
Nicht als benanntes GRF-Prinzip im Code, aber zwei konkrete technische
Instanzen davon **[FUND]**:
- `architekt/kanarie.py::pruefen()`: `testboden_gesund =
  testboden.get("stand") == "GEMESSEN" and bool(testboden.get("besteht"))`
  — die Kanarie-Gesundheitsprüfung verlangt wörtlich den Statuswert
  `"GEMESSEN"` plus ein bestandenes Boolean, nicht irgendeine
  Modellselbsteinschätzung.
- `clayverse/mistral_prestage/store.py:150-171`: `outcome_ok` ist
  dokumentiert als „NIE eine Modellbewertung — nur die mechanische
  Kombination aus `self_adapted`... und `translation_raw_fallback`", getrennt
  gehalten von `self_reported_gap` (ein mechanischer Substring-Scan über
  Zeros eigenen Text, „KEINE Modellbewertung").

### 5.3 Messwerkzeuge für emergente Kopplungen — der wichtige Teil
**Shannon-Entropie über Makrozustände, §7.3, H_field/H_adm**: **[UNBELEGT]**.
Eine repo-weite Suche (inkl. `research_entity/`) fand **weder** eine
Spezifikationsstelle „§7.3" **noch** die Notation `H_field`/`H_adm` **noch**
implementierenden Code. Der einzige benachbarte Treffer ist die Formulierung
„Plus Entropie als Emergenz-Maß" als ein Stichpunkt in Arm B von
`GWT-GRF-MESSUNG-2026-08-22.md` — ohne Formel, ohne Abschnittsnummer, ohne
Code. **Diese Metrik existiert im Repo nicht** und darf nicht als
implementiert dargestellt werden.

**Pearl/C2-Interventionstest `do(E_t)`, drei Arme (∅/winners/all)**:
ebenfalls **[UNBELEGT als Formalismus]** — keine Fundstelle für „do(E_t)",
„three-arm", „Pearl" oder „interventionist" im Repo. Was tatsächlich
existiert, in Arm B von `GWT-GRF-MESSUNG-2026-08-22.md` (Zeile ~23, wörtlich):
„die Leerraum-Probe wird zu einem echten Interventions-Test (dieselbe Frage
dreimal fahren — leerer Arbeitsraum / nur Gewinner / alle Kandidaten — und
den *kausalen* Beitrag messen)." Das entspricht inhaltlich der
∅/Gewinner/Alle-Dreiteilung, **aber**: das ist ein **Entwurfsvorschlag
innerhalb eines Experimentberichts**, nicht implementierter, laufender Code.
Keine Stelle im Repo führt diesen Dreifach-Test tatsächlich aus.

**Zukünftiges Steuern statt nur Messen**: **[UNBELEGT/ASPIRATION]** — keine
Textstelle im Repo behauptet, dass diese Werkzeuge künftig emergente
Kopplungen aktiv *steuern* statt nur zu *messen*. Der Schlusssatz von
`GWT-GRF-MESSUNG-2026-08-22.md` spricht nur davon, dass GRF den *Entwurf*
zu mehr Nachweisbarkeit zwingt und ClayCode Regeln „unbrechbar durch
Bauweise" macht (Invarianten zur Bauzeit) — das ist etwas anderes als
Laufzeit-Steuerung bereits emergenter Kopplungen. Eine Steuerungs-Aussage
wäre reine Extrapolation dieses Dokuments und muss als solche gekennzeichnet
werden, nicht als bereits belegte Fähigkeit.

### 5.4 Das GWT-GRF-Messergebnis — `GWT-GRF-MESSUNG-2026-08-22.md`
Vollständig gelesen **[LIVE]**, 64 Zeilen. Methode: drei Claude-Sonnet-
Instanzen bekamen dieselbe Aufgabe — einen Global Workspace für Zero auf
EntityOS zu entwerfen —, nur die Denkweise variierte: **Arm A** = normale
Ingenieurskunst, kein Framework (Kontrolle); **Arm B** = im GRF denkend;
**Arm C** = GRF **und** in ClayCode ausgedrückt. Kernbefund, wörtlich:
> „Von A über B nach C stieg **eine** Sache klar an: **wie beweisbar/prüfbar
> der Entwurf ist.** Nicht 'mehr Text', sondern 'härter nachweisbar'."

Tabellarisch: Arm A lieferte 5 konkrete Mechanismen + ein Mess-Dashboard,
blieb aber korrelativ. Arm B reframte dieselbe Leerraum-Probe zum
Interventionstest (s. 5.3) — „von *beobachten* zu *beweisen*". Arm C fand
zusätzlich eine Lücke, die A und B übersahen: nichts bestraft einen
ununterbrochenen Gewinner-Lauf (dieselbe Information gewinnt immer wieder).
Ehrliches Urteil im Dokument selbst: **„Ein Entwurf je Arm, ein Modell →
indikativ, KEIN Beweis."** Aufwand-Confound wird ausdrücklich benannt (B/C
lasen mehr Material) — die *Richtung* der Mehrtiefe (Kausalität, prüfbare
Invarianten) wird als das eigentliche, GRF/ClayCode-spezifische Signal
gewertet, nicht die Menge. Keine gemessene Prozentzahl wird beansprucht.

### 5.5 Datenschicht/CI_d=0.084
**[UNBELEGT im Repo]**: die im Betriebsgedächtnis erwähnte Datenschicht-
Kopplungsanalyse (131 Datenbanken → Graphschicht, CI_d=0.084) wurde in
`/opt/entityos/the artefact/` **nicht** gefunden. Sie existiert — wenn
überhaupt — außerhalb dieses Repos, als frühere Sitzungsnotiz, und darf hier
**nicht** als repo-verifiziert zitiert werden.

---

## 6. Die Messungen + ClayCode-only-Kognition

### 6.1 `selbstmessung.py` — die Instrumente
`clayverse/selbstmessung.py` (600 Zeilen) **[FUND]**. Docstring (Z.3-22):
misst nur, baut kein neues Instrument, ruft sechs bereits gebaute Werkzeuge:

1. **Testboden** (`_testboden`, Z.452-515) — führt pytest per subprocess
   gegen `ARTEFAKT_ROOT/tests` aus (Modi `ueberspringen`/`schnell`/`voll`);
   Referenzboden 1067 bestandene Tests (`BEKANNTER_TESTBODEN`, Z.98).
2. **Wegehierarchie** (`_wege`, Z.147-196) — ruft
   `/opt/unifieddb/udb/abruf/wegehierarchie.py:pruefung()`; dokumentiert
   einen live am 2026-08-22 gefundenen Fehler: die Funktion setzte
   `"stand":"GEMESSEN"` nie, selbst bei einem echten ≥10-Wege-Urteil, wodurch
   `architekt/hypothesen.py:sammle_messwerte` eine reale Schwellenverletzung
   still ignorierte (gemessen `oberes_zehntel_haelt=0.14` gegen Schwelle
   `0.20`, keine Hypothese feuerte). In `selbstmessung.py` inzwischen
   behoben.
3. **Weckvertrag** (`_weckvertrag`, Z.217-282) — liest offene
   `wake_conditions`; ein fest verdrahtetes Dict (`_WECKVERTRAG_GRUNDLAGE`,
   Z.207-213) hält fest, dass nur `EFFECT_TERMINAL` wirklich ereignisgebunden
   ist, `RESOURCE_REVISION` nur teilweise, `GOAL_STATE`/`AT_TIME` unverdrahtet
   sind (30-Sekunden-Poll als Rückfall).
4. **Übersetzungsausfälle** (`_uebersetzungsausfaelle`, Z.289-337) — zählt
   `mv_uebersetzung_ausfall`-Zeilen, klassifiziert 429 (Rate-Limit) vs. 402
   (fehlendes Kontingent).
5. **Stimmen** (`_stimmen`, Z.343-402) — zählt `eos_bewertungen`
   Daumen hoch/runter.
6. **Abnahmeprobe** (`_abnahmeprobe`, Z.409-433) — **wird nie tatsächlich
   aufgerufen**: die reale Abnahmeprobe würde echtes Mistral-Kontingent
   verbrauchen und echte Turns/Effects schreiben; der strikt lesende
   `selbstmessung.py` verweigert den Aufruf, liefert immer
   `"stand":"NICHT_AUSGEFUEHRT"`.

Zentrale Regel (Z.24-32): **UNBEKANNT ist ein Messfehlschlag, kein Befund** —
„Tabelle existiert noch nicht" (Datenlücke), „Messung fehlgeschlagen" (echter
Fehler) und „Schwelle erreicht" werden nie vermengt, durchgesetzt über
`_unbekannt()` (Z.129-136) und Fail-closed-try/except je Instrument. Das
Modul öffnet `wiki.db` strikt im `mode=ro`-Modus (`_ro_verbinden`,
Z.111-127) und instanziiert nie `UnifiedDB(...)` oder
`WakeConditionStore(db)`, da beide beim `__init__` schreiben.

### 6.2 `gw_*`/`mv_*`-Tabellen — tatsächliche Schemata
**`gw_*`** (Global Workspace, `clayverse/mistral_prestage/`) **[FUND]**:
`gw_absicht` (`absicht.py:91-96`), `gw_wettbewerb` (`wettbewerb.py:757-760`),
`gw_ausstrahlung` (`wettbewerb.py:762-765`) — Kommentar Z.748-751 erklärt die
Aufteilung: „`gw_wettbewerb` beantwortet 'wie stand es zur Wahl',
`gw_ausstrahlung` beantwortet 'was ging tatsächlich raus'."

**`mv_*`** (Mistral-Vorstufe, `store.py`/`pipeline.py`/`reality_layer.py`)
**[FUND]**: `mv_prestage_state`, `mv_prestage_turns` (`store.py:17-42`),
`mv_translation_log` (`store.py:67-80`), `mv_claude_usage`
(`store.py:91-107`, hinzugefügt 2026-08-22 — Korrektur, dass Claude/
`headless_zero`, nicht Mistral, die bezahlte Stufe ist, die verfolgt wird),
`mv_eval_runs` (`store.py:110-119`), `mv_paketurteil`
(`pipeline.py:1097-1099`), `mv_uebersetzung_ausfall`
(`pipeline.py:1165-1168`), `mv_realitaetscheck`
(`reality_layer.py:288-291`).

**Zur Behauptung „bereits ClayCode-record-förmig" — Korrektur nötig**: die
Recherche fand **keinen** expliziten ClayCode-Mapping-Kommentar und keine
ClayCode-Record-Typdefinition, die diese Tabellenschemata spiegelt.
`store.py:11-14` formuliert sogar das Gegenteil: „New table names only...
this module never touches the other 105 tables." Der einzige ClayCode-Bezug
ist architektonisch/aspirativ (VERFASSUNG.md, 6.4), keine wörtliche
Schema-Spiegelung. **Diese Prämisse aus dem Auftrag ist unbelegt und wird
hier nicht übernommen.**

### 6.3 Der Stimmen-/Export-Kreislauf — zwei getrennte Mechanismen
Kein einzelner „Vote/Export-Loop", sondern zwei unabhängige Subsysteme, die
sich dieselbe DB teilen **[FUND]**:
- **Stimmen**: `clayverse/bewertung.py`, Tabelle `eos_bewertungen`
  (Z.57-72), `setzen()` (Z.123-188) mit
  `ON CONFLICT(turn_id,user_id) DO UPDATE`, gated durch
  `ist_kanonische_sitzung`. Speist `selbstmessung._stimmen`.
- **Export**: `PrestageStore.record_eval_run()`
  (`store.py:472-490`) schreibt in `mv_eval_runs`; einziger Aufrufer ist
  `clayverse/mistral_prestage/eval_harness.py` — ein manuell per CLI
  gestarteter Übersetzer-Qualitäts-Eval (Ziel Pass-Rate ≥ 0.95 auf 50
  Beispielen), **nicht** automatisch an die Stimmen- oder `gw_*`-Daten
  gekoppelt.

### 6.4 VERFASSUNG.md — die ClayCode-only-Kognitions-Vision
Vollständig gelesen (158 Zeilen) **[LIVE bestätigt: erste 15 Zeilen selbst
gelesen, Rest per Recherche gegengeprüft]**. Kopf, wörtlich **[LIVE]**:
> „Dies ist dein Grundgesetz, Zero. ... Sie stammt wörtlich von Gabriel
> (2026-08-22) und gilt dauerhaft."
> „Alles, was du tust, denkst du innerhalb des GRF. Die Mathematik des GRF
> ist deine Sprache für das, was in dir vorgeht. Es liegt Substrat bereit:
> `clayverse/hyperposition.py`, `clayverse/needle.py`, die GRF-Papiere."

Die zentrale ClayCode-only-Passage (Z.113-131, laut Recherche **[FUND]**,
wörtlich):
> „NICHT nur der Architekt — ZERO INSGESAMT bekommt ClayCode-only-Kognition.
> Nur die SPRACHE wird getauscht, nichts sonst: INTERN denkt Zero in
> ClayCode (Chat UND Architekt). Die VORSTUFE gibt Zero alles bereits in
> ClayCode... Der ÜBERSETZER (schon gebaut) übersetzt ClayCode → DEUTSCH
> fürs menschliche Auge. Der Mensch sieht weiter Deutsch; Zeros Medium
> darunter ist ClayCode... Kein Split-Brain: EIN Wesen, ClayCode als
> durchgehendes Denk-/Programmiermedium, Deutsch nur als äußere
> Übersetzungsschicht."
> „ClayCode ist für den Architekten nicht bloß ein Zielformat, sondern sein
> DENK- und PROGRAMMIER-MEDIUM. Und seine stehende Aufgabe ist es, ALLES nach
> ClayCode zu verwandeln."

Das ist **Absichtstext in einem Direktivendokument**, keine lauffähige
Wirkung — die Compiler-Realität (2.3, 2.6) bestätigt, dass „ALLES nach
ClayCode verwandeln" heute nur für skalare Funktionen technisch möglich
wäre.

### 6.5 Der gestufte, reversible Bauplan
Kein separates „Karten"-Dokument mit nummerierten Stufen gefunden
**[UNBELEGT als eigenständiges Dokument]**. Was tatsächlich existiert:
`architekt/entityos_runtime.clay` ist selbst als **„STAGE 0"** markiert
(Zeile 1, s. 2.5) und beschreibt sich als reines Dokumentationsartefakt ohne
Wirkung. Der eigentliche Reversibilitäts-Mechanismus steht als Text in
VERFASSUNG.md (Z.133-146, laut Recherche **[FUND]**): „ITERATIV — Stück für
Stück, nie ein Big-Bang-Umbau", jede ClayCode-Umstellung unter der Regel
„STRIKT BESSER (in keiner Hinsicht schlechter, in mind. einer besser) +
ÄQUIVALENZ-BEWEIS (der ClayCode-Teil liefert dieselben Antworten) + Tor +
Kanarie + Rollback" — also **derselbe** Tor/Kanarie/Rollback-Mechanismus aus
Abschnitt 1, nicht ein separater Pfad. Eine „ClayCode-first pro Bugfix"-
Politik wird zusätzlich genannt: nur dort auf ClayCode umstellen, wo es
robust/besser ist, sonst in der Originalsprache fixen.

### 6.6 Vorteile + Implikationen — ehrlich mit Kosten
**Typisierte Invarianten**: `claycode_base_typed_ir.py` und das Manifest
existieren und sind live geprüft (2.2, 2.3) — aber der Invarianten-Vorteil
gilt heute nur für die skalare, verifizierte Teilmenge.

**Messbare Emergenz**: gestützt durch `GWT-GRF-MESSUNG-2026-08-22.md` (5.4)
— ein **indikativer** n=1-Befund je Arm, kein wiederholtes,
verblindetes Experiment.

**„Kein menschlicher Semantik-Overhead" — Korrektur nötig**: diese
Formulierung stammt **nicht** aus dem Messdokument, sondern wörtlich aus dem
injizierten Meta-Prompt selbst, `architekt/GRF_CLAYCODE_INJEKTION.md:13`
(„kein menschlicher Semantik-Overhead") und `:31` („completely free of
human semantic overhead or RLHF distortions"). Das ist ein **Designziel, das
dem Modell eingeimpft wird**, keine separat gemessene empirische Aussage.
Die tatsächliche Messung (GWT-GRF-MESSUNG) ist deutlich zurückhaltender:
„indikativ, KEIN Beweis", „keine gemessene Prozentzahl", ausdrücklicher
Aufwand-Confound-Vorbehalt. **Die beiden Aussagen dürfen nicht vermischt
werden** — der Meta-Prompt behauptet mehr, als das Messdokument belegt.

**Kosten, ehrlich**: der ausführbare General-Purpose-Compiler ist
Zukunftsarbeit (Abschnitt 2.3/2.6). `GWT-GRF-MESSUNG-2026-08-22.md` macht
dieselbe Korrektur selbst: ein funktionierender Basis-Compiler existiert
bereits (Basis-Slices PASS in CI, hier zusätzlich selbst reproduziert), aber
„offen ist nur der General-Purpose-Gate (noch FAIL)" — und ein Testarm hatte
das fälschlich als „gar nicht lauffähig" gelesen, was im Dokument
richtiggestellt wurde. Dieselbe Vorsicht gilt für dieses Dokument: ein
unified ClayCode-Substrat ist ein begründetes, teilweise durch Code belegtes
Ziel — heute aber nur für einen schmalen, skalaren Ausschnitt real
eingelöst.

---

## Zusammenfassung: was heute läuft vs. was Absicht ist

| Bereich | Live/laufzeit-verifiziert | Unit-getestet, laufzeit-unverifiziert | Nur Beschreibung/Absicht |
|---|---|---|---|
| Architekt-Schleife, Tor, Konfig | `ENABLED=0`, `AUTO_LIVE_NACH_KANARIE=0` (Config gelesen); Tor/Schwarm-Logik durch pytest-Artefakte belegt | Schwarm-Gate, Rollback, echter Kanarie-Durchlauf | — |
| Kanarie | Code + Sperren (`ich_bin_sicher`, Namensverbot) | — | „hat noch nie gebaut" — bestätigt durch `docker images`/`ps -a` (kein Kanarie-Image existiert) |
| ClayCode Basis-Compiler | 1000/1000 Differential-Tests, live reproduziert | — | — |
| ClayCode General-Purpose | — | — | `GENERAL_PURPOSE_GATE: FAIL`, nur skalare Fn |
| Hyperposition | Import/Konsum durch `wettbewerb.py` (Recherchefund) | — | „retrieval.py"-Konsum aus dem Auftrag ist falsch |
| Container | `entityos` läuft, `architekt/` bestätigt host-only | — | frühere Nested-VM nur als Betriebsgedächtnis |
| GRF-Injektion | `_GRF_RAHMEN` live im Prompt, Schalter AN | getestet (`test_grf_injektion.py`) | Shannon-Entropie §7.3/H_field/H_adm, `do(E_t)`-Formalismus: nicht im Repo |
| ClayCode-only-Kognition | — | — | VERFASSUNG.md-Vision; „kein Semantik-Overhead" ist Prompt-Designziel, nicht Messergebnis |

*Ende der Skizze. Rückfragen zu einzelnen Zitaten: alle Pfade sind absolut
und auf `frank-api` unter `/opt/entityos/the artefact/` (bzw. explizit
vermerkt `/opt/entityos/` ohne Unterordner, `/opt/agentzero-export/repo/`)
nachvollziehbar.*

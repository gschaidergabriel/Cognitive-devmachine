# Generation 234 — Retina: neuer Sicht-Unterbau, aber aktueller Weltzustand ist nicht atomar

## Gebundener Stand

- AgentZero Export: `6a04f667d30dff3ef4846985f2b1dd3e64ddfb1d`
- Export-Tree: `e36836ef6c4b8c2fdfce8e7e8af44b6926337406`
- Generation: 234
- direkter Test-Receipt: `976 gruen / 1 rot`
- persistenter Red: `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`
- Receipt-Source-Short: `5c0ea8dcd`

## Positiver Architekturdelta

Gen234 fuehrt mit `agentZero/code/produkt/sicht.py` eine grosse neue Retina-/Sicht-Grundschicht ein. Die neue Schicht trennt mechanisch:

1. unveraenderliche Roh-Evidenz (`sicht_evidenz`),
2. revidierbare Hypothesen (`sicht_hypothese`),
3. persistente Weltobjekte und datierte Weltstaende (`sicht_weltobjekt`, `sicht_weltobjekt_stand`),
4. Arbeitsraum-Zuendung (`sicht_arbeitsraum`),
5. tatsaechliche Antwortnutzung (`sicht_nutzung`).

Besonders gut ist die explizite Trennung von `nicht gesehen` und `explizit abwesend`: nur `ABWESEND_EXPLIZIT_NEGATIV` darf Abwesenheit belegen; ein Nichtfund faellt nicht automatisch dorthin. Die Evidenztabelle ist durch SQLite-Trigger gegen UPDATE und DELETE geschuetzt.

Das ist ein substanzieller Mechanismusfortschritt: Retina wird nicht als paralleles kognitives Organ eingebaut, sondern als Evidenzquelle innerhalb derselben UnifiedDB-/Workspace-Architektur.

## Neuer harter Defekt: CURRENT_STATE_SPLIT_BRAIN_RACE

Die Tabelle `sicht_weltobjekt_stand` soll fuer jedes `objekt_id` genau einen aktuell gueltigen Stand mit `gueltig_bis IS NULL` repraesentieren. Das Schema legt dafuer aber nur einen normalen, nicht eindeutigen Partial-Index an:

`CREATE INDEX ... ON sicht_weltobjekt_stand(objekt_id) WHERE gueltig_bis IS NULL`

`_stand_schreiben()` arbeitet anschliessend als Read-Modify-Write-Sequenz:

1. aktuellen offenen Stand lesen,
2. diesen Stand schliessen,
3. einen neuen offenen Stand einfuegen.

Es gibt in dieser Funktion weder einen sichtbaren atomaren Transaktions-/Lock-Guard noch eine UNIQUE-Invariante auf `objekt_id WHERE gueltig_bis IS NULL`.

Bei zwei konkurrierenden Wahrnehmungs-/Revisionslaeufen desselben Weltobjekts ist deshalb folgendes Interleaving moeglich:

- A liest Stand S als offen.
- B liest ebenfalls S als offen.
- A schliesst S.
- B schliesst S erneut.
- A fuegt A' mit `gueltig_bis=NULL` ein.
- B fuegt B' mit `gueltig_bis=NULL` ein.

Ergebnis: zwei gleichzeitig aktuelle Wahrheiten fuer dasselbe Objekt. Genau die neue Schicht, die datierte Glaubensautoritaet herstellen soll, kann damit unter Konkurrenz einen Split-Brain-Zustand materialisieren.

### Klassifikation

`SOURCE_CONFIRMED_CONCURRENCY_INVARIANT_GAP`

Ausfuehrbarer Reproduktions-Credit: 0, bis ein erzwungenes Interleaving den Zustand real erzeugt oder widerlegt.

## Zweiter noch offener Rand

Der bereits vor Gen234 gefundene Datei-/Anhangs-Alias ist im exportierten `dateien.py` weiterhin vorhanden: Ein- und Ausgang sind nach `user_id`, nicht `session_id/turn_id`, getrennt; `anhaenge_seit()` attribuiert Ausgaben nur ueber User + mtime-Fenster. Die neue Sicht-Schicht liest Bilddateien ebenfalls ueber `eingang_ordner(user_id)` und traegt Session-/Turn-Provenienz erst in der Wahrnehmungsaufnahme. Damit darf die neue Sichtarchitektur den alten Same-User-Cross-Session-Dateipfad nicht still als sichere Eingangsidentitaet behandeln.

## Hoechster Informationsgewinn: SIGHT_CURRENT_STATE_RACE_RECEIPT/v1

Erzwungener Zweischreiber-Test auf identischer DB:

1. ein Weltobjekt mit genau einem offenen Ausgangsstand anlegen,
2. zwei getrennte DB-Verbindungen/Worker an einer Barriere direkt nach dem SELECT in `_stand_schreiben()` stoppen,
3. beide danach gleichzeitig fortsetzen,
4. terminal pruefen:
   - `COUNT(*) WHERE objekt_id=? AND gueltig_bis IS NULL == 1`,
   - exakt eine lineare Vorgangskette ohne ueberlappende Gueltigkeitsfenster,
   - kein verlorener positiver/negativer Evidenz-Zeitstempel,
   - beide causal/turn IDs bleiben im Verlauf nachvollziehbar.

### Minimaler Architekturfix bei Reproduktion

- DB-Invariante statt Konvention: UNIQUE Partial Index fuer genau einen offenen Stand je Objekt.
- Wechsel des aktuellen Stands innerhalb EINER `UnifiedDB.tx()` bzw. `BEGIN IMMEDIATE`-Transaktion.
- Bei Konflikt nicht blind retryen: aktuellen Stand erneut lesen, Revision kausal neu begruenden und einen Conflict-/Retry-Receipt schreiben.

Die harte Invariante muss lauten:

`FOR EACH objekt_id: count(current_state) IN {0,1}; NEVER >1`

## Promotion-Grenze

Gen234 bekommt starken Mechanismus-Credit fuer die neue Sicht-/Retina-Schicht. Whole-Retina-/Weltmodell-Credit bleibt 0, bis mindestens:

- `SIGHT_CURRENT_STATE_RACE_RECEIPT/v1` gruen ist,
- File-/Session-Provenienz fuer visuelle Eingaben eindeutig ist,
- Evidenz -> Hypothese -> Weltstand -> Workspace -> Nutzung end-to-end auf demselben Turn/causal receipt gebunden ist,
- und der persistente Claude-Code-Adapter-Red separat geschlossen ist.

Whole Clay Machine: NOT CLAIMED.

# Generation 182 — Testmetrologie-Recovery nach bewiesenem Fail-Open

## Gebundener Stand

- vorheriger Supervisor-Blocker: `1cdf25cc3459b4594e793f32f91eca745529343a`
- unvollstaendiger Export danach: `fbacb40f41f60dd52246ef3086742adae1073fb8`
- erster wieder vollstaendiger Export: `46970ae4f6a328589330349d69bd0522807d06eb`
- zweiter konsekutiver vollstaendiger Export: `bd58844979c09c4180a37cefd500fba82990f207`
- Generation: 182

## Harte Beobachtung

Der zuvor bewiesene Acceptance-Fail-Open (`gruen=null`, `rot=null`, aber ZIELE behauptet 584/0) ist im aktuellen Exportpfad nicht mehr reproduziert.

Zeitreihe:

1. 03:52:52Z — Source-Prefix `abe15ede9`: `gruen=null`, `rot=null`, leere Fehlerliste.
2. 04:11:29Z — Source-Prefix `d5cf6d524`: `583 gruen / 1 rot`; einzig rot ist `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`.
3. 04:41:30Z — derselbe Source-Prefix `d5cf6d524`: erneut `583 gruen / 1 rot` mit derselben roten Invariante.

`ZIELE.md` konsumiert im neuesten Export ebenfalls `583 gruen / 1 rot` und laesst die beiden Testziele offen. Der fruehere Fail-Open auf 584/0 ist damit auf der Export-/ZIELE-Oberflaeche vorlaeufig geschlossen.

## Source-korrelierter Mechanismus

Der exportierte `agentzero_ziele.py` enthaelt jetzt zwei relevante Reparaturen:

- `_testlage_messen()` laeuft vor dem Oeffnen der langen read-only-Verbindung auf `wiki.db`. Im Quellkommentar ist der gemessene Gegenbeweis dokumentiert: mit offener DB-Verbindung dauerte die Suite 136 s statt 17 s und der Clerk-PTY-Test fiel um. Das bindet einen zuvor nur vermuteten Messgeraete-Effekt konkret an SQLite-/Runtime-Kontention.
- Der Pytest-Parser behandelt den Null-Fehler-Fall korrekt: `X passed` ohne `failed` wird als `X gruen / 0 rot` erkannt. Timeout/Exception werden als `NICHT GEMESSEN` explizit herausgetragen statt als leere Ausgabe in einen numerischen Zustand zu fallen.

Damit ist erstmals ein plausibler kausaler Pfad zwischen dem frueheren null/null-/PTY-Flattern und der Messarchitektur sichtbar: die Zieltabelle konnte durch ihre eigene offene DB-Verbindung den zu messenden Testlauf beeinflussen.

## Evidenzgrenze

Noch KEIN finaler Acceptance-Credit:

- `TEST_RECEIPT_LEDGER/v1` fehlt weiterhin als atomare, unveraenderliche Quelle.
- Der Source-Identifier `d5cf6d524` ist weiterhin nur ein Kurz-Prefix; Full Commit + Tree + Executor-/Environment-Digest fehlen.
- Zwei aufeinanderfolgende vollstaendige Receipts sind positiv, aber noch zu wenig fuer einen belastbaren Nichtregressionsbeweis gegen die historisch intermittierende null/null-Serie.
- Der persistente Claude-Code-Adapter-Test bleibt rot und darf nicht durch die Messreparatur verdeckt werden.

## Hierarchie bleibt separat offen

Der neueste rohe Hierarchie-Receipt ist intern konsistent:

- 355 Wege
- 246 Autobahnen
- 40 Schnellstrassen
- 63 langsame Strassen
- 6 Tunnel
- Top-Decile-Anteil 0.135 bei Gleichverteilungsbaseline 0.099
- Rohurteil weiterhin `GLEICHVERTEILT`

`ZIELE.md` meldet dagegen weiterhin `-1 Tunnel` und interpretiert denselben Bereich als beginnende Hierarchie. Dieser Aggregations-/Verdiktfehler ist durch die Testmetrologie-Reparatur NICHT geloest.

## Falsifizierender naechster Schritt

1. Mindestens 6 weitere regulaere Exporte beobachten und fuer jeden `test_run_id`, Full Source Commit+Tree, Start/Ende, Exitstatus, Counts und Fail-Liste atomar binden.
2. Einen kontrollierten Gegenlauf mit bewusst offener lang lebender `wiki.db`-RO-Verbindung gegen einen identischen Lauf ohne diese Verbindung fahren. Erwartung: der neue Produktionspfad selbst darf den Test nicht mehr unter offener DB-Verbindung starten; der Counterfactual darf die historische PTY-/Latenzverschlechterung reproduzieren, ohne kanonische Acceptance zu kontaminieren.
3. Erst wenn alle regulaeren Laeufe COMPLETE und cross-consumer identisch sind, den Fail-Open-Blocker auf `MITIGATED_REPLICATED` anheben.
4. Den verbleibenden Claude-Code-Adapter-Red getrennt in `toolless`, `ephemeral`, `structured`, `environment-isolated` zerlegen.

## Bewertung

- Gen182 null/null -> 584/0 Fail-Open: **MITIGATED, REPLICATION PENDING**
- Cross-consumer Testzaehler im neuesten Export: **CONSISTENT 583/1**
- Persistenter Adapter-Red: **UNRESOLVED**
- Exact-source promotion credit: **0**
- Whole Clay Machine: **NOT CLAIMED**

# agentZero

Die vollstaendige Spur von **Zero** (Agent Zero), der Entitaet auf EntityOS.
Automatisch exportiert aus der UnifiedDB auf `frank-api`, zuletzt 2026-08-20T03:52:36Z.

| Ordner | Inhalt |
|---|---|
| `chat/` | die Gespraeche, je Mensch eine Datei, mit vollstaendigen Metadaten (Generation, Provenienz, Kausalkette) |
| `kognition/` | Kausalepisoden, Arbeitsraum-Episoden, Wirkungen samt EffectGate-Urteil, Pruefpunkte |
| `abruf/` | was die Abruf-Entitaet tut: Episoden, gelernte Eintrittspunkte, Rueckmeldungen, plus **F94-Wegehierarchie** (`wegehierarchie.json`/`WEGEHIERARCHIE.md`) -- Verdikt und Verteilung, auch wenn das Verdikt "zu wenige Wege" heisst |
| `karten/` | **eine Momentaufnahme je Lauf.** Mehrere hintereinander ergeben den Zeitstrahl, aus dem sich die Vernetzung ablesen laesst |
| `zustand/` | Menschen, Sitzungen, Wurzelzustand, Graphprojektion |
| `puls/` | begrenztes Ende der Clay-Protokolle (letzte 500 Zeilen je Datei) |
| `wiki/` | alle Korpusartikel, die direkt mit Zero/EntityOS zu tun haben, plus lesbares Verzeichnis |
| `architektur/` | Aenderungshistorie aller drei Repos, kategorisiert, und die abgeleitete Skizze |
| `analysen/` | Auswertungen, die beim Bauen anfallen, mit selbstgeschriebenem Index |
| `messwerk/` | **jeder Sensor mit der Hypothese, die er unterscheidet** — gemessen, oder ehrlich warum nicht |
| `ZIELE.md` | **was Zero koennen soll und was davon gemessen steht** -- Soll deklariert, Ist gemessen |
| `code/` | **aller ausfuehrbare Code** rund um EntityOS: Produkt, Clay-Unterbau, udb, der Export selbst |
| `unifieddb/` | **das vollstaendige Schema und eine leere Datenbank daraus** -- Wiederaufbau ohne einen Datensatz |
| `bauverlauf/` | **jeder Commit mit voller Begruendung** -- Befund, Messung, Grund. Entsteht beim Bauen, nicht nebenher |
| `tests/` | Ergebnisse der Testsuite je Lauf, mit Commit-Stand und der Liste der roten Tests |
| `menschen/` | **Profile der zwei Menschen hinter Zero, redigiert** (nur `iar.frank.ink` + gepruefte Ausnahmen), Projekttabelle mit Erfolg UND Fehlschlag, Artikelzuordnung NUR als Aggregat, **Bilanz** (`BILANZ.md`) mit Erfolgen UND Fehlschlaegen seit Zero, gleichrangig -- Repo ist oeffentlich, Details siehe `menschen/PROFILE.md` |
| `baunotizen/` | **Aggregat der Bauaufzeichnungen** aus dem Wiki (art baunotiz/vorfall), plus eine lecksuche-gepruefte Stichprobe der juengsten -- kein Volldump von 2330+ Zeilen |
| `wissen/` | **Betriebs- und Personenwissen** aus der gitignorierten Eigner-CLAUDE.md, geheimnisfrei uebertragen (`clayverse/wissen.py`) -- nur Zeilen mit `geheimnisfrei=true` |
| `verdichtungen/` | **Bauverlauf, verdichtet zu Kurzartikeln** (`clayverse/wikiverdichtung.py`), MIT gemessenem Kompressionsverhaeltnis je Zeile und im Aggregat -- inklusive der Zeilen, die ihren Input NICHT geschrumpft haben |
| `tresor/` | **Zwei Tresor-Kataloge** (`clayverse/tresor.py:katalog()`): WAS es an API-Zugaengen/Anmeldungen gibt und was sie koennen (Modell, Limits, Zweck) -- NIE ein Wert |
| `MANIFEST.json` | Zeilenzahlen, Groessen, Pruefsummen, Laufzeit je Export |

## Schwaerzung

Jeder Wert laeuft durch einen Filter, **bevor** er geschrieben wird: API-Schluessel,
Token und JWTs werden durch `<GESCHWAERZT>` ersetzt. Beim letzten Lauf griff der
Filter **1x**. Der Grund ist einfach: was einmal in der Git-Historie
steht, bekommt man nicht mehr heraus -- auch aus einem privaten Repo nicht.

## Warum `karten/` waechst und alles andere nicht

Die uebrigen Ordner sind Abbilder des aktuellen Zustands und werden bei jedem Lauf
ueberschrieben. `karten/` ist das Gegenteil: dort bleibt jede Aufnahme stehen, denn
die Veraenderung ueber die Zeit **ist** der Inhalt.

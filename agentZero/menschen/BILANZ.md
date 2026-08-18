# Bilanz -- Erfolge UND Fehlschlaege seit Zero

Automatisch erzeugt 2026-08-18T18:11:07Z aus `entityos_erfolge`.

> ⚠️ Zero ist seit 2026-08-18 in Benutzung -- einem Tag. Alles mit seit_zero=1 stammt aus diesem Tag. Das ist kein Makel, aber es zu verschweigen waere einer.

> ⚠️ Jeder Fehlschlag hier hat im Betrieb NICHTS geworfen. Die Liste ist das genaueste Bild davon, wie dieses System kaputtgeht: still.

Beide Haelften stehen hier gleichrangig: gleiche Tabellenform, gleiche Spalten, Erfolge zuerst nur weil das Alphabet so will -- keine Haelfte ist Fussnote der anderen. Eigner-Auftrag woertlich: eine Tabelle mit nur Gelungenem ist ein Werbeblatt.

## Erfolge (6)

| Datum | Titel | Wirkung | Beleg | gehoert | seit Zero |
|---|---|---|---|---|---|
| 2026-08-18 | Ein Gefaess statt zwei Datenbanken | 87 Clay-Korpustabellen und 19 Laufzeitobjekte in EINER Datei, kollisionsfrei. | Gemessen: 0 Namenskollisionen, Schema idempotent, Herz waehrend der Operation weiter gewachsen (+543 Kanten). | gemeinsam | ja |
| 2026-08-18 | EntityOS laeuft im Container auf dem VPS | Ohne nested Virtualisierung, ohne Anruf bei Hostinger. | docker ps: entityos up, healthy. Bereitschaftspruefung gruen. | gemeinsam | ja |
| 2026-08-18 | Bahnenrouter: Faehigkeit statt Anbieter | Das Modell fragt nach einer Faehigkeit, der Code waehlt den Anbieter. Anteilsgrenzen erzwungen, erschoepft = Absage statt stiller Verschlechterung. | clayverse/bahnen.py, leere Antwort zaehlt als Ausfall und schaltet weiter. | gemeinsam | ja |
| 2026-08-18 | Gedaechtnis mit Woertlichkeitspruefung | Ein Beleg muss zeichengenau im Quelltext stehen, sonst wird der Eintrag verworfen. | Gegen einen absichtlich luegenden Extraktor geprueft: 1 genommen, 2 verworfen. 'Kubernetes' und '12 Server' kamen nie ins Gedaechtnis. | gemeinsam | ja |
| 2026-08-18 | 14.284 Wiki-Artikel den Menschen zugeordnet | gemeinsam 11.543, gabriel 1.633, andreas 1.092, unbekannt 16. | Gegenprobe: 0 Artikel aus projekt=Dr.-Unterweger landeten woanders als bei andreas. | gemeinsam | ja |
| 2026-08-18 | agentZero-Ordner autonom auf GitHub | Code, Schema, leere UnifiedDB, Profile, Bauverlauf -- jede Datei mit Metadaten. | Generation 36, 45 Dateien, Lecksuche nach Adressen leer. | gabriel | ja |

## Fehlschlaege (7)

| Datum | Titel | Wirkung | Beleg | gehoert | seit Zero |
|---|---|---|---|---|---|
| 2026-08-18 | Gedaechtnis konnte die zwei Menschen nicht trennen | Andreas bekam in SEINER Sitzung Gabriels private Eintraege woertlich zurueck. | Gemessen im Testlauf. Ursache: memory_tabelle hatte weder user_id noch session_id -- sie KONNTE strukturell nicht trennen. Behoben: Spalte ergaenzt, Bestand zugeordnet statt geraten, user_id ohne Vorgabewert. | gemeinsam | ja |
| 2026-08-18 | Schatten-Datenbank: Zuege gingen in eine zweite Datei | env -i loeschte CLAYVERSE_DB_PATH, die Zuege landeten woanders. | Gefunden beim Nachzaehlen, nicht durch eine Fehlermeldung. | gemeinsam | ja |
| 2026-08-18 | Schemaanlage in einer Lesefunktion riss 77 Tests ein | executescript() committet implizit und zerlegte die laufende Transaktion. | 77 rote Tests, 'cannot commit - no transaction is active'. Heute per Test reproduziert: der Rollback-Pfad wirft dann selbst. | gemeinsam | ja |
| 2026-08-18 | Ein falscher Spaltenname, zweimal, beide Male verdeckt | gehoert statt gehoert_zu. Einmal warf die Abfrage und ein except schluckte es ('nichts gemessen' bei voller Tabelle), einmal gab .get() klaglos None -- die Vorstufe haette gelesen: kein Rechner gehoert dir. | Beim Nachmessen der Verdichtung aufgefallen, nicht im Betrieb. | gemeinsam | ja |
| 2026-08-18 | Zero war blind fuer die Menschen, obwohl die Daten dalagen | Auf 'wem gehoert <GESCHWAERZT: Rechnername>?' kam korrekt UNBEKANNT -- es gab keinen Weg zu den Tabellen. Die Weigerung war richtig, die Blindheit war der Baufehler. | Gemessener Testlauf, Zeros Antwort woertlich protokolliert. Behoben mit menschen_profil() und wiki_zuordnung(). | gemeinsam | ja |
| 2026-08-18 | Ein veralteter Docstring erzeugte einen Fehlalarm | Ein Pruefer meldete den Live-Chat-Pfad als unsicher -- gestuetzt auf einen Kommentar, den die Reparatur schon ueberholt hatte. | Nachgemessen: active_turns leer, Doppel liegen 49 s bis 8 min auseinander (wiederholte Testeingaben, keine Doppelaufnahme). Veraltete Dokumentation verbrennt die Aufmerksamkeit, die ein echter Fehler braucht. | gemeinsam | ja |
| 2026-08-18 | Zwei Groq-Modelle sind ohne Ankuendigung verschwunden | llama-3.1-8b-instant und llama-3.3-70b-versatile: am 15.08. gemessen in Ordnung, am 18.08. beide 404. | Live-Aufruf. Zeigt, dass ein Eichwert von vorgestern kein Betriebszustand ist. | gemeinsam | ja |


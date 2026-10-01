# VERIFICATION PROTOCOL — Compiler + Needle-Mund (Gabriel 2026-10-01: "alles mehrfach messen und pruefen")

Frage des Experiments: Funktioniert die geplante Kette (GRID-Kontext -> trainierter 4B-Compiler -> PLAN -> Expander -> trainierter Needle-Mund)? Ja/Nein per vorab eingefrorenen Kriterien (PREREG_GO_NOGO.md). Keine Zwischenloesung zaehlt.

## 1. Eingefroren VOR dem Blick auf Ergebnisse
- PREREG_GO_NOGO.md (Schwellen), PACKET_SCHEMA_v2.md, COMPILER_SPEC.md, Judge-Prompts, Wortlisten, Seeds: je Datei sha256 + Zeitstempel in FREEZE.json. Aenderung = neue Version + Begruendung, nie still.
- Schwellen nie nach Sicht von Ergebnissen aendern. Abweichungen im Bericht benennen.

## 2. Daten (Fehler hier verderben alles)
- Entitaets-, Template- und Relationen-DISJUNKTE Splits; zusaetzlich Near-Duplicate-Check (n-Gramm/MinHash) train<->val/test; Leckagebericht mit Zahlen.
- Stichproben-Audit: je Datenfamilie >=50 Beispiele per Hand/zweitem Agenten lesen; Fehlerquote protokollieren; Filter nachschaerfen, bis Fehlerquote <=2%.
- Verteilungsbericht (Intents, Modes, Laengen, Selbstmention-Rate, origin-Anteile, EPQ-Abdeckung ueber den GANZEN Wertebereich).
- Deterministisch: gleiche Seeds -> byte-gleiche Dateien (3 Laeufe vergleichen, tree-sha256).
- Fakten stammen aus echten Quellen (flywiki-mini.db, runtime-Zustaende); LLM erzeugt nur Sprache, nie Soll-Plaene/Soll-Fakten.

## 3. Zwei unabhaengige Implementierungen jeder Kennzahl
- Jede Eval-Kennzahl (Unsupported-Claim, Fakten-Abdeckung, Endemarker, Wiederholungsrate, Plan-Validitaet, ID-Treue ...) wird von ZWEI getrennt geschriebenen Implementierungen berechnet (z.B. Eval-Skript + unabhaengiger Verifier-Agent). Abweichung > 0,5 Prozentpunkte = Fehler suchen, nicht mitteln.
- Kennzahlen zuerst an Kontrollen testen, die ein bekanntes Ergebnis haben: perfektes Orakel (alles richtig), kaputtes Modell (Zufall, permutierte Fakten, leere Pakete), Kopier-Baseline. Ein Mass, das die Kontrollen nicht trennt, ist unbrauchbar.

## 4. Training: mehrere Seeds, Kontrollen, Ablationen
- Needle-Mund: >=3 Seeds (billig). Compiler: >=2 Seeds, wenn Budget es erlaubt; sonst 1 Seed + dokumentierte Einschraenkung und Bootstrap-Konfidenzintervalle ueber die Testbeispiele.
- Berichtet wird Mittel +- Streuung bzw. 95%-KI (Paarbootstrap 10000), nie Einzelwert.
- Nullkontrollen: Mund mit permutierten Fakten im Paket (muss Treue-Kennzahl brechen), Compiler mit permutiertem Kontext (muss Plan-Genauigkeit brechen), EPQ identisch -> identischer Plan.
- Ablationen: ohne EPQ-Block, ohne Self/Body-Block, ohne spoken-Fenster (Mund), ohne Hypothesen-Familie; zeigt, dass jede Komponente wirkt (oder nicht).
- Trainingsverlauf (Loss je Epoche, Val-Loss) protokollieren; Abbruch/Plateau-Regel vorab.

## 5. Judge-Zuverlaessigkeit (Free-Pool-Richter sind Messinstrumente, nicht Wahrheit)
- Deterministische Kennzahlen haben Vorrang; Judge nur fuer Fluenz/Anschluss.
- Mindestens 2 verschiedene Richtermodelle; Inter-Rater-Uebereinstimmung (Spearman/Kappa) berichten; <0,6 = Judge-Ergebnis nur als Hinweis.
- 30 Judge-Urteile werden zusaetzlich vom Koordinator/zweiten Agenten per Hand gegengelesen.
- Judge-Prompts eingefroren, Positions-/Reihenfolge-Bias durch Vertauschen kontrollieren (A/B-Order randomisieren).

## 6. Latenz und Ressourcen: wiederholt messen
- >=10 Wiederholungen je Messpunkt, erste 2 als Warmup verwerfen, Median + p95 + Streuung; Hardware, Threads, Last (Load) mitschreiben; nie unter Fremdlast als Endwert.

## 7. End-to-End
- 30 Mehrturn-Dialoge, vorab festgelegt (Dialog-Skripte eingefroren), inkl. langer Aeusserungen, Faellen ohne Wissen, Selbstfragen, EPQ-Wechsel, Rueckkopplung nach Fehler.
- Jeder Turn wird vollstaendig protokolliert (Kontext, Plan, Pakete, Stuecke, Zeiten). Stichprobe von 20 Turns liest ein zweiter Prueferin/ein zweiter Agent komplett.
- Baseline-Vergleich (lokaler 4B-Mund) auf denselben Dialogen, Positionen randomisiert.

## 8. Koordinator-Pruefung (Definition of Done)
- Agentenmeldung ist nichts: je Lieferung Hash + eigener Stichproben-Nachlauf (>=1 Kennzahl neu rechnen, >=10 Beispiele lesen) + Reconcile mit Beleg.
- Berichte nennen Unbelegtes explizit; "UNBELEGT" ist erlaubt, Vermutung als Fakt nicht.
- Fehlschlag ist ein gueltiges Ergebnis (GO / PARTIAL / NO-GO), mit konkret verfehlten Kriterien und Ursachenhypothese + welcher Test sie trennen wuerde.

## 9. Kosten/Pod
- Pod erst nach lokal getestetem Bundle, Ja von Gabriel zu Kosten; Stopp-Regel (Zeit/Plateau); nach dem Lauf Checkpoints + Logs ziehen, Pod sofort beenden, Guthaben notieren.

## 2b. DATENQUALITAET (Gabriel: "Trainingsdaten extrem gut und ueberlegt") — gilt fuer ALLE Stränge (Compiler, Mund, Tool-Needle)
- ENTWURF VOR MASSE: Pro Strang zuerst eine COVERAGE-MATRIX (Dimensionen x Zellen: Intent/Mode, Wissenslage (belegt/teilbelegt/unbekannt/widerspruechlich), Selbstrelevanz, EPQ-Bereich, Tool-Bedarf, Laenge, Sprache der Namen ...). Jede Zelle bekommt Mindestanzahl; leere Zellen werden gefuellt oder bewusst begruendet gestrichen.
- GOLD-SEED-SET: 150-300 von Hand (starkes Modell + Gegenlesen) geschriebene, vollstaendig geprueft korrekte Beispiele je Strang als Anker (Few-Shot fuer Teacher, Messlatte fuer Filter, Teil des Tests). Sorgfalt vor Menge.
- MINIMAL-PAIRS und HARTE NEGATIVE: gleicher Kontext mit EINER Aenderung (EPQ, ein Fakt, Quota-Zustand), die das Ziel veraendern MUSS; Distraktoren, Fehlformen, Grenzfaelle (Body/Env, hedge-Pflicht, 'kein Werkzeug', Rueckgabe an den Compiler).
- KRITIK-DURCHLAUF: Jedes generierte Beispiel wird von einem ZWEITEN, anderen Modell gegen eine Checkliste bewertet; Beispiele mit Uneinigkeit oder Regelverstoss fliegen raus (Quote berichten). Soll-Labels entstehen regelbasiert aus Szenario-Metadaten, nie aus freier LLM-Entscheidung.
- FEHLERANALYSE-SCHLEIFE VOR dem Pod: Mini-Baseline (kleines Modell/CPU oder Nearest-Neighbour) auf den Daten trainieren/auswerten, die haertesten Fehler ansehen, Daten gezielt nachbessern, EINMAL wiederholen. Ziel: Datenfehler finden, solange es nichts kostet.
- Natuerlichkeit: Nutzernachrichten vielfaeltig (Tippfehler, Kuerze, Mischsprache, Umgangssprache, deutsche und englische Namen), keine Template-Monokultur; Template-Anteil und Phrasen-Wiederholungsrate berichten.
- Jede Datei erhaelt DATA_CARD.md: Zweck, Quellen, Erzeugung, Filterquoten, bekannte Schwaechen.

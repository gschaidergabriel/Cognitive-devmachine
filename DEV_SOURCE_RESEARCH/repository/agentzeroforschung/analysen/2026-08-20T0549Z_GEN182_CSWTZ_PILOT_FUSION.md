# Generation 182 — CSWT-Z Pilot: Messfehler, Architekturdelta und naechster Falsifikationslauf

## Gebundener Stand

- Research/Export-Head bei Analyse: `e06c84c18e1764f13dbf3821cba99bd220c1a193`
- AgentZero Generation: 182
- Test-Receipt: `583 GREEN / 1 RED`
- persistenter Red: `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`
- Receipt-Source short: `2adcf9a58`
- Bauverlauf bindet denselben Prefix an lokalen EntityOS-Commit `2adcf9a58b0b` (Aenderung `mistral_prestage/pipeline.py`). Full 40-SHA + Tree fehlen im Receipt weiterhin.

## Neuer empirischer Befund: CSWT-Z Pilot

Commit `b6dca3a0169f` dokumentiert einen Pilotlauf mit 270 Zuegen.

### Schicht 1 — derzeit nicht als Kapazitaetsmessung verwertbar

Der Pilot zeigt, dass der deklarierte `_VORSTUFE_MAX_CHARS = 10_000` nur einen Teil des realen Vorstufen-Kontexts kontrollierte. Gemessen wurde ein effektiver Kontext von 17.878 Zeichen; Identitaets-/Anwesenheitsblock waren ausgenommen und das Nutzerprofil (~8.480 Zeichen) lief am Regler vorbei. Bei nomineller Kappung 0 blieben noch ca. 6.895 Zeichen Grundlast. Zudem belohnte die verwendete Zeichenkettenbewertung Profil-Rezitation.

Damit ist der urspruengliche Schicht-1-Versuch kein sauberer Kapazitaets-Falsifikator. Er mischt mindestens drei Variablen: kontrollierter `world`-Anteil, unkontrolliertes Profil und eine Bewertungsfunktion, die Wiederholung von Profiltext positiv bewertet.

### Schicht 4 — starker Pre-Fix-Gegenbeweis fuer epistemische Selbstkenntnis

Der Pilot zeigt, dass `epistemik` architektonisch nicht bis zu Zero gelangte; uebertragen wurde nur `caveman_prompt`. Der gemeldete Typ-2-AUROC liegt bei 0,465, also praktisch auf Zufallsniveau. Ein externer Beobachter, der nur die Frage sieht, sagte Erfolg besser voraus (0,745/0,624 gegen 0,465 fuer das System).

Das ist ein wichtiger Negativbefund: interne epistemische Daten koennen vorhanden sein, ohne kausal in der Antwortgrenze anzukommen. Ein Speicher-/State-Mechanismus darf daher keinen Selbstwissen-Credit bekommen, solange seine Information nicht bis zur Entscheidung/Ausgabe transportiert und dort genutzt wird.

### Rauschboden

Fuenf identische Wiederholungen des Piloten ergaben laut Bauverlauf einen so hohen Rauschboden, dass statt 18 etwa 179–247 Sonden je Stufe erforderlich waeren. Damit sind kleine Differenzen aus der bisherigen Stichprobe nicht promotionsfaehig.

## Direkt danach sichtbarer Architekturdelta

Der aktuelle exportierte `mistral_prestage/pipeline.py` enthaelt zwei gezielte Reparaturfamilien:

1. **Realbudget fuer den gesamten Vorstufen-Kontext**
   - neuer `_VORSTUFE_KONTEXT_MAX_CHARS = 14_500`
   - `_kontext_im_budget(...)` misst den fertigen Kontext statt nur `world`
   - `_bilanz_schlank(...)` entfernt zuerst Belege aus der wachsenden Bilanz, kuerzt danach symmetrisch Erfolge und Fehlschlaege und reduziert erst auf Stufe 3 Projekte auf Namen
   - falls selbst Stufe 3 nicht reicht, wird die Budgetverletzung explizit auf stderr gemeldet statt still akzeptiert

2. **Epistemik erreicht die Ausstrahlung**
   - `_epistemik_zeile(...)` rendert kompakt KNOWN/UNKNOWN inklusive Quellenhinweis
   - `_mit_epistemik(...)` haengt diese Information an den `caveman`-Prompt
   - Gate `CLAYVERSE_EPISTEMIK_IM_PROMPT`, Default `1`
   - Deckel `_EPISTEMIK_MAX_CHARS = 420`

Das ist **Source-/Mechanismus-Credit**, aber noch kein kausaler Wirksamkeits-Credit. Insbesondere darf der Pre-Fix-AUROC 0,465 nicht nachtraeglich als repariert gelten, bevor exakt derselbe Test unter sauberem Design wiederholt wurde.

## Hypothesen

### H1 — Ganzkontext-Budget beseitigt den Schicht-1-Konfounder

Wenn die neue Budgetierung funktioniert, dann ist die tatsaechliche an die Vorstufe gelieferte Zeichenmenge monoton und nahe am deklarierten Gesamtbudget; Profilgroesse darf die experimentelle Kappung nicht mehr heimlich umgehen.

**Falsifikator:** feste Promptmenge, identischer Source/Tree, mehrere absichtlich grosse Profile/Bilanzen. Logge pro Zug raw world chars, profile chars, final chars und Kuerzungsstufe. Ein finaler Kontext ueber Budget ohne expliziten ERROR/WARN oder profilabhaengige nicht-monotone Kappung falsifiziert H1.

### H2 — Epistemik-Injektion verbessert Typ-2-Kalibrierung kausal

Wenn die neue Epistemikzeile wirklich genutzt wird, muss `CLAYVERSE_EPISTEMIK_IM_PROMPT=1` gegen denselben Exact-Source-Lauf mit `=0` die Kalibrierung verbessern, ohne die eigentliche Task-Accuracy durch blosses Vorsicht-Sprechen zu verschlechtern.

**Falsifikator:** preregistriertes A/B auf identischen Fragen, identischem Modell, Sampling, Kontext und Source. Primärmetriken: AUROC/Selective-Risk/Brier oder ECE fuer correctness confidence; sekundär Task-Accuracy, Abstention-Rate, Quellennennung und False-Unknown-Rate. Kein Credit, wenn nur die Sprache vorsichtiger wird, aber Fehlererkennung nicht steigt.

### H3 — Der bisherige Frage-only-Beobachter misst Item-Difficulty statt Selbstwissen

Der externe Beobachter war mit 0,745/0,624 deutlich besser als das System. Das kann bedeuten, dass viele Fehler bereits aus der Frage selbst vorhersagbar sind. Epistemische Selbstkenntnis ist erst gezeigt, wenn Zero **ueber diesen question-only baseline hinaus** residuale Varianz in der eigenen Korrektheit erklaert.

**Falsifikator:** trainiere/fitte bzw. berechne einen question-only difficulty score und teste dann, ob epistemische Features inkrementelle Vorhersagekraft auf held-out Items besitzen. Reporte Delta-AUROC oder likelihood/log-loss improvement ueber die question-only baseline.

### H4 — Profil-Rezitations-Bias verfaelschte Schicht 1

Wenn die Zeichenkettenmetrik Profilwiederholung belohnt, koennen groessere Profile scheinbar bessere Leistung erzeugen, obwohl die Aufgabe nicht besser geloest wird.

**Falsifikator:** Ergebnisbewertung auf semantische/task-spezifische Richtigkeit umstellen und Profiltext-Overlap separat als Leakage/Recitation-Metrik reporten. Ein positiver Zusammenhang nur mit Overlap, nicht mit Task-Correctness, bestaetigt den Bias.

## Naechster hoher Informationsgewinn: CSWT-Z v2

Keine weitere breite Featurearbeit vor diesem Test notwendig. Ein sauberer v2-Lauf soll:

1. Full Source Commit + Tree + Environment/Executor Digest binden.
2. `TEST_EXPORT_ATOMIC_RECEIPT/v1` bzw. gleichwertigen COMPLETE/INCOMPLETE/ERROR-Receipt verwenden.
3. Schicht 1 erst nach Instrumentierung der **finalen** Kontextgroesse wiederholen.
4. Schicht 4 als gepaartes `EPISTEMIK=0` vs `EPISTEMIK=1` A/B ausfuehren.
5. Question-only baseline als Pflichtkontrolle mitfuehren.
6. Wegen des gemessenen Rauschbodens die Stichprobe power-basiert dimensionieren; die Pilotangabe 179–247 Sonden/Stufe ist Ausgangspunkt, nicht Dogma.
7. Keine neue ungewoehnliche Architekturvariante in denselben Lauf mischen.

## Promotion-Grenze

- `583/1` bleibt der aktuelle harte Teststand.
- Der persistente Claude-Code-Adapter-Red ist durch CSWT-Z nicht geloest.
- Die neuen Budget-/Epistemik-Aenderungen sind **Mechanismus vorhanden**, nicht **Wirksamkeit bewiesen**.
- Whole Clay Machine / finales EntityOS bleibt **NOT CLAIMED**.

## Neue Forschungsbegriffe

**Epistemic Transport Gap** — interne epistemische Information existiert, erreicht aber die Entscheidungs-/Ausgabegrenze nicht; Speicherpraesenz wird faelschlich mit nutzbarem Selbstwissen verwechselt.

**Declared-Budget Illusion** — ein lokaler Kontextdeckel wird als Gesamtbudget interpretiert, obwohl unkontrollierte Seitenkanaele (Profil, Identitaet, Zusatzblocks) den realen Kontext dominieren.

**Question-Difficulty Dominance** — ein externer question-only Beobachter sagt Systemfehler besser vorher als die interne Epistemik; Selbstwissen muss inkrementell ueber Item-Difficulty hinausgehen.

**Recitation-Reward Confounder** — eine Bewertungsfunktion belohnt das Wiederholen von Profil-/Kontexttext und verwechselt dadurch groesseren Kontext mit besserer Aufgabenleistung.

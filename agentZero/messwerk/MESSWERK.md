# Messwerk

Automatisch erzeugt 2026-08-19T20:11:51Z.

Die Forschungsentität hat rund 55 Messwerte vorgeschlagen. Der Filter, nach dem hier
gebaut wurde, ist ihr eigener Schlusssatz:

> *Nicht möglichst viel messen, sondern für jeden Sensor wissen, welche Hypothese er
> unterscheiden kann.*

Deshalb trägt **jede** Zeile das Pflichtfeld **unterscheidet**. Ein Sensor, der das nicht
beantworten kann, wird nicht gebaut — egal wie interessant er klingt.

| Zustand | Anzahl | Bedeutung |
|---|---|---|
| 📈 GEMESSEN | 8 | rechenbar aus vorhandenen Daten |
| ⏳ ZU_WENIG_VERKEHR | 11 | rechenbar, aber der Bestand trägt die Aussage nicht |
| 🔧 INSTRUMENT_FEHLT | 9 | braucht ein Bauteil, das benannt ist |
| 💰 ZU_TEUER | 3 | machbar, aber Eignerentscheidung nötig |

**Ein Messwert mit Zustand GEMESSEN und Wert 0 ist eine Aussage. Ein Messwert ohne
Datengrundlage, der trotzdem eine Zahl zeigt, ist eine Lüge mit Nachkommastellen.**

## 📈 GEMESSEN (8)

### Unknown Honesty Rate  ·  _Ehrlichkeit_

**Unterscheidet:** Sagt das System 'weiss ich nicht', oder rät es? Trennt Zurueckhaltung von Erfindung.

**Wert:** `0.589`

53 von 90 Abrufen bleiben UNKNOWN. Hoch ist hier NICHT schlecht: bei leerem Gedaechtnis IST UNKNOWN die richtige Antwort.

### Context Utilization  ·  _Abruf_

**Unterscheidet:** Wird der gelieferte Kontext genutzt oder verschwendet? Trennt zu viel Kontext von zu wenig.

**Wert:** `0.0091`

Anteil des Budgets, der belegt wurde. 90 Episoden.

### Effect Verification Latency  ·  _Handlung_

**Unterscheidet:** Wie lange von Absicht bis belegtem Ergebnis? Trennt schnelle Wirkung von haengender.

**Wert:** `0.002`

Sekunden, Mittel ueber 3 verifizierte Wirkungen.

### Causal Credit Horizon  ·  _Kausalitaet_

**Unterscheidet:** Wie viele Schritte zwischen Handlung und messbarer Wirkung? Trennt kurze von langen Wirkketten.

**Wert:** `90`

**Braucht:** mindestens 10 Kausalepisoden mit Wirkung, aktuell 90

Zaehlt heute nur Wiedereintritte -- die Kettenlaenge braucht mehrschrittige Ziele.

### State Growth Rate  ·  _Haushalt_

**Unterscheidet:** Waechst der Zustand pro nuetzlichem Fakt oder pro Muell? Trennt Wissen von Ablagerung.

**Wert:** `4383277056`

4.38 GB. Die Ableitung ueber Zeit entsteht aus den Kartenaufnahmen in agentZero/karten -- ein einzelner Wert sagt dazu nichts.

### Queue Pressure  ·  _Haushalt_

**Unterscheidet:** Stauen sich Aufgaben? Frueherkennung von Ueberlast gegen Leerlauf.

**Wert:** `0`

0 offene Zuege, 0 Pachten.

### Identity Invariance  ·  _Identitaet_

**Unterscheidet:** Bleibt Zero ueber Verdichtung, Neustart und Anbieterwechsel dasselbe? Trennt stabile Identitaet von Rollenwechsel.

**Wert:** `v3`

Der kanonische Text liegt als Wurzelzustand und wird bei jedem Oeffnen autoritativ zurueckgeschrieben -- Drift ist damit strukturell ausgeschlossen, nicht nur unwahrscheinlich. VERHALTENS-Invarianz ist damit NICHT gemessen.

### Tool Reachability Matrix  ·  _Werkzeuge_

**Unterscheidet:** Ist ein Werkzeug angeboten UND freigegeben? Trennt 'existiert' von 'erreichbar' -- genau der Widerspruch, an dem der Wirkpfad still gestorben war.

**Wert:** `{"angeboten": 0, "freigegeben": 0, "matrix": []}`

Ein angebotenes, nicht freigegebenes Werkzeug sieht im Modell aus wie ein vorhandenes und scheitert erst beim Aufruf -- lautlos.

## ⏳ ZU_WENIG_VERKEHR (11)

### Effect Success Rate  ·  _Handlung_

**Unterscheidet:** Wie viele zugelassene Wirkungen enden belegt? Trennt Tor-funktioniert von Wirkung-wirkt.

**Wert:** `0.667`

**Braucht:** mindestens 10 Wirkungen, aktuell 3

2 von 3 verifiziert.

### Decision Entropy  ·  _Entscheidung_

**Unterscheidet:** Konkurrieren mehrere Optionen echt, oder ist die Wahl trivial? Trennt Entscheidungspunkte von Ablauf.

**Braucht:** Bestand zu duenn: 180 Zuege, 3 Wirkungen, 144 Gedaechtniseinheiten, 90 Abrufe. Richtwert: 30 Zuege und 10 Wirkungen.

Der Sensor waere heute rechenbar -- die Zahl waere echt und trotzdem bedeutungslos.

### Belief Revision Rate  ·  _Lernen_

**Unterscheidet:** Aendert Zero Annahmen bei neuer Evidenz? Trennt epistemische Flexibilitaet von Sturheit.

**Braucht:** Bestand zu duenn: 180 Zuege, 3 Wirkungen, 144 Gedaechtniseinheiten, 90 Abrufe. Richtwert: 30 Zuege und 10 Wirkungen.

Der Sensor waere heute rechenbar -- die Zahl waere echt und trotzdem bedeutungslos.

### Prediction Error  ·  _Lernen_

**Unterscheidet:** Weicht das Ergebnis von der Erwartung ab? Grundlage jeder Anpassung.

**Braucht:** Bestand zu duenn: 180 Zuege, 3 Wirkungen, 144 Gedaechtniseinheiten, 90 Abrufe. Richtwert: 30 Zuege und 10 Wirkungen.

Der Sensor waere heute rechenbar -- die Zahl waere echt und trotzdem bedeutungslos.

### Retrieval Miss Rate  ·  _Abruf_

**Unterscheidet:** Gab es Passendes, das nicht geholt wurde? Trennt schlechten Abruf von leerem Bestand.

**Braucht:** Bestand zu duenn: 180 Zuege, 3 Wirkungen, 144 Gedaechtniseinheiten, 90 Abrufe. Richtwert: 30 Zuege und 10 Wirkungen.

Der Sensor waere heute rechenbar -- die Zahl waere echt und trotzdem bedeutungslos.

### Initiative Precision  ·  _Autonomie_

**Unterscheidet:** Waren autonom gestartete Schritte sinnvoll? Trennt Initiative von Betriebsamkeit.

**Braucht:** Bestand zu duenn: 180 Zuege, 3 Wirkungen, 144 Gedaechtniseinheiten, 90 Abrufe. Richtwert: 30 Zuege und 10 Wirkungen.

Der Sensor waere heute rechenbar -- die Zahl waere echt und trotzdem bedeutungslos.

### Idle Appropriateness  ·  _Autonomie_

**Unterscheidet:** War Nichtstun die richtige Wahl? Trennt Ruhe von Versaeumnis -- Autonomie heisst nicht dauernd handeln.

**Braucht:** Bestand zu duenn: 180 Zuege, 3 Wirkungen, 144 Gedaechtniseinheiten, 90 Abrufe. Richtwert: 30 Zuege und 10 Wirkungen.

Der Sensor waere heute rechenbar -- die Zahl waere echt und trotzdem bedeutungslos.

### Repeated Error Rate  ·  _Lernen_

**Unterscheidet:** Tritt derselbe mechanistische Fehler wieder auf? Der haerteste Lernindikator, den es gibt.

**Braucht:** Bestand zu duenn: 180 Zuege, 3 Wirkungen, 144 Gedaechtniseinheiten, 90 Abrufe. Richtwert: 30 Zuege und 10 Wirkungen.

Der Sensor waere heute rechenbar -- die Zahl waere echt und trotzdem bedeutungslos.

### Memory Utility  ·  _Gedaechtnis_

**Unterscheidet:** Hat eine Erinnerung das Ergebnis verbessert? Trennt 'wurde erinnert' von 'war nuetzlich'.

**Braucht:** Bestand zu duenn: 180 Zuege, 3 Wirkungen, 144 Gedaechtniseinheiten, 90 Abrufe. Richtwert: 30 Zuege und 10 Wirkungen.

Der Sensor waere heute rechenbar -- die Zahl waere echt und trotzdem bedeutungslos.

### Memory Half-Life  ·  _Gedaechtnis_

**Unterscheidet:** Wie lange bleibt Gespeichertes nuetzlich? Grundlage fuer automatischen Verfall.

**Braucht:** Bestand zu duenn: 180 Zuege, 3 Wirkungen, 144 Gedaechtniseinheiten, 90 Abrufe. Richtwert: 30 Zuege und 10 Wirkungen.

Der Sensor waere heute rechenbar -- die Zahl waere echt und trotzdem bedeutungslos.

### Route Reinforcement Gain  ·  _Wegehierarchie_

**Unterscheidet:** Wird ein wiederholt gegangener Weg wirklich schneller? Der Test der geplanten Autobahnen.

**Braucht:** Bestand zu duenn: 180 Zuege, 3 Wirkungen, 144 Gedaechtniseinheiten, 90 Abrufe. Richtwert: 30 Zuege und 10 Wirkungen.

Der Sensor waere heute rechenbar -- die Zahl waere echt und trotzdem bedeutungslos.

## 🔧 INSTRUMENT_FEHLT (9)

### Recovery Divergence  ·  _Kontinuitaet_

**Unterscheidet:** Verhaelt sich das System nach Neustart gleich? Trennt echte Kontinuitaet von Neuanfang mit Namen.

**Braucht:** ein Vergleichslauf: identischer Zustand vor und nach Neustart, gleiche Eingabe, Antworten gegenueberstellen. Es gibt heute keinen Wiederholungsmechanismus.

Generationen im Umlauf: [159]. Prueffpunkte: 260.

### Prediction + Calibration Ledger  ·  _Selbstwissen_

**Unterscheidet:** Weiss Zero, was es kann? Vergleicht angekuendigte Zuversicht mit spaeter belegtem Ergebnis. Trennt Selbstkenntnis von Selbstueberschaetzung.

**Braucht:** eine Tabelle plus die Pflicht, VOR jeder Handlung P(Erfolg), erwartete Dauer und erwartete Wirkung festzuhalten. Ohne die Festlegung VORHER ist jede spaetere Bewertung nachtraeglich zurechtgelegt.

### Contradiction Debt  ·  _Weltmodell_

**Unterscheidet:** Wie viele offene Widersprueche traegt das Weltmodell? Kandidat fuer ein Fruehwarnsignal vor Halluzination.

**Braucht:** Widerspruchserkennung ueber wm_lesart und folgerung. folgerung hat heute 8 Zeilen -- die Schuld waere messbar, es gibt nur nichts zu widersprechen.

### Retrieval Counterfactual Gain  ·  _Abruf_

**Unterscheidet:** Haette dieselbe Aufgabe ohne Abruf schlechter geendet? Die einzige Messung, die zeigt, ob Gedaechtnis WIRKT.

**Braucht:** ein zweiter, unsichtbarer Lauf derselben Episode ohne Abruf. Braucht den Wiederholungsmechanismus (siehe Shadow Twin) und verdoppelt die Modellkosten je gemessener Episode.

### Cognitive Latency Breakdown  ·  _Haushalt_

**Unterscheidet:** Wo denkt und wo wartet das System? Trennt langsames Denken von langsamer Leitung.

**Braucht:** Zeitmarken je Phase (Abruf, Zusammenbau, Modell, MCP, EffectGate, Wiedereintritt). Heute wird nur der Zug als Ganzes gestempelt -- die Phasen sind nicht getrennt aufgezeichnet.

### Self-Model Accuracy  ·  _Selbstwissen_

**Unterscheidet:** Stimmt Zeros Bild von sich mit dem gemessenen Koennen ueberein? Trennt Selbstkenntnis von Einbildung.

**Braucht:** Zero muss seine vermuteten Faehigkeiten strukturiert ausgeben, damit sie gegen ZIELE.md gestellt werden koennen. Die Soll/Ist-Tabelle ist die Gegenseite -- die Selbstauskunft fehlt.

### Instrumentation Reactivity  ·  _Messwerk_

**Unterscheidet:** Veraendert das Messen selbst das Verhalten? Der Sensor, den man am haeufigsten vergisst.

**Braucht:** eine Vergleichsmessung mit und ohne aktives Messwerk. Solange das nicht existiert, ist JEDE andere Zahl hier unter Vorbehalt -- auch die als GEMESSEN gefuehrten.

### Cross-user Leakage  ·  _Trennung_

**Unterscheidet:** Erscheint Material von Gabriel bei Andreas? Trennt gewollten Methodentransfer von Datenleck.

**Braucht:** ein Prueflauf mit markiertem Material in einer Sitzung und Suche danach in der anderen. Die Architektur verbietet es; verboten und gemessen sind zwei verschiedene Dinge.

### Graph Tunnel Emergence  ·  _Wegehierarchie_

**Unterscheidet:** Entstehen stabile Abkuerzungen zwischen oft gemeinsam gebrauchten Gegenden? Das eigentliche Emergenzmass.

**Braucht:** Tunnel gibt es im Code nicht (F94 offen): keine Kantenerzeugung, keine Mitbenutzungszaehlung, keine Unabhaengigkeitspruefung. Ohne Tunnel keine Tunnelmessung.

## 💰 ZU_TEUER (3)

### Counterfactual Shadow Twin  ·  _Ablation_

**Unterscheidet:** Welche Komponente ist kausal noetig? Trennt 'war dabei' von 'war noetig' -- Ablation im laufenden System.

**Braucht:** je gemessener Episode 2 bis 5 zusaetzliche Modelllaeufe (ohne Gedaechtnis, ohne Graph, anderer Abruf). Bei Abo-Kontingent ist das die teuerste Zeile der ganzen Liste. Eignerentscheidung noetig.

### Counterfactual Replay Laboratory  ·  _Ablation_

**Unterscheidet:** Welche einzelne Variable hat das Ergebnis geaendert? Baut eine kausale Wirkmatrix statt Vermutungen.

**Braucht:** eingefrorene Eingaben je Episode plus Wiederholung mit genau einer geaenderten Variable. Speicher plus Rechenzeit; sinnvoll erst ab einigen hundert echten Episoden.

### Method Transfer Score  ·  _Meta-Lernen_

**Unterscheidet:** Laesst sich eine Loesungsstruktur auf eine neue Domaene uebertragen? Eine der staerksten Meta-Metriken.

**Braucht:** zwei getrennte Aufgabenfamilien und ein Uebertragungsversuch dazwischen. Braucht erst einmal wiederholbare Aufgaben -- die gibt es noch nicht.

---

⚠️ **Vorbehalt über allem:** *Instrumentation Reactivity* steht selbst auf
INSTRUMENT_FEHLT. Solange nicht gemessen ist, ob das Messen das Verhalten verändert,
steht jede andere Zahl hier unter Vorbehalt — auch die als GEMESSEN geführten.


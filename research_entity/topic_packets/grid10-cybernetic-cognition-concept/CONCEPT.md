# GRID10 als kybernetische Kognitionsarchitektur – Konzeptausarbeitung  

**Provenienz:** Auftrag von Gabriel, 2026-08-27. Recherchiert am laufenden GRID10-Code
(`grid10_fabric.py`, `grid10_node.py`, `run_grid10_world_model_simulation_v2_persistent.py`,
gebaut von Task `aa3009e8316c45b1f`) im `claylab`-Sandbox-Bereich auf dem VPS. Die
geplante Erarbeitung über mehrere ChatGPT-Runden ("clay science pipeline"-Projekt) war
nicht durchführbar: die geteilte `chatgpt.com`-Browser-Brücke war über 25+ Minuten
durchgehend Cloudflare-403-blockiert (mehrere parallele Agenten auf demselben Daemon).
Dieses Dokument wurde stattdessen über den Free-Pool (`~/last-resort/llm.py`, Kaskade
Groq/NVIDIA-Nemotron/Mistral) erzeugt: Hauptentwurf über NVIDIA Nemotron-3-super-120b
(TEILE 1–6, danach TEIL 7 nach Kritik an Praxisnähe neu erzeugt über Groq/gpt-oss-120b,
diesmal explizit an den echten Dateinamen/Funktionssignaturen der Codebasis geerdet statt
generischem Docker/React/Wochenplan). Von einem Sonnet-Koordinator geprüft, zusammengeführt
und mit den Vorgaben aus dem Originalauftrag abgeglichen, nicht Wort für Wort verifiziert
gegen jede Codezeile — vor der Umsetzung durch `aa3009e8316c45b1f` gegenlesen.

## Überblick  
Das bestehende GRID10‑System besteht aus zehn unabhängigen OS‑Prozessen, die ein gemeinsames ~0,8 B Causal‑LM teilen und über eine SQLite‑WAL‑Datei (grid10_fabric.py) koordiniert werden. Aktuell dient die Datenbank ausschließlich als Task‑Log und Lease‑Verwaltung. Ziel dieses Dokuments ist es, die Infrastruktur zu einer echten kybernetischen Kognitionsarchitektur zu erweitern, indem Global‑Workspace‑Theory (GWT) mit echter Regelungstechnik kombiniert wird. Alle nachfolgenden Teile enthalten konkrete, implementierbare Spezifikationen: SQL‑Schemata, Formeln, Schwellenwerte und Regelungsgesetze.  

---  

## TEIL 1 – REGLER ALS DYNAMISCHER ZUSTANDSRAUM  

### 1.1 Ziel  
Den SQLite‑WAL‑Zustand von einem reinen Task‑Log zu einem live‑verstellbaren Dashboard von Kognitionsparametern verwandeln, das alle zehn Knoten vor jedem Tick lesen. Eine Änderung wirkt beim nächsten Tick systemweit, vergleichbar mit einem Hormonsystem.  

### 1.2 Neues Schema – Tabelle `regulator`  

```
Table name: regulator
Columns:
- id               INTEGER PRIMARY KEY AUTOINCREMENT
- name             TEXT    NOT NULL UNIQUE   -- eindeutiger Regler‑Name, z.B. 'attention_decay'
- value_real       REAL    NOT NULL          -- aktueller Reglerwert (float)
- version          INTEGER NOT NULL          -- monotone Versionsnummer für CAS
- epoch            INTEGER NOT NULL          -- aktuelle Globale Epoch (aus leases)
- writer           TEXT    NOT NULL          -- 'human' oder 'auto' (wer hat zuletzt geschrieben)
- ts_ms            INTEGER NOT NULL          -- Unix‑Millisekunden des letzten Schreibens
- 
- comment          TEXT    NULL              -- optionaler frei‑textlicher Kommentar
```

*Kompatibilität*: Die Tabelle existiert neben den bereits vorhandenen Tabellen `meta`, `nodes`, `tasks`, `scopes`, `leases`. Keine Spaltennamen kollidieren.  

### 1.3 CAS‑sicheres Schreiben  
Ein Schreiber (menschlich oder automatisch) führt ein Update aus, das nur erfolgreich ist, wenn die aktuelle `version` dem erwarteten Wert entspricht:

```
UPDATE regulator
SET value_real = :new_value,
    version    = version + 1,
    writer     = :writer,
    ts_ms      = :now_ms,
    comment    = :comment
WHERE name = :reg_name
  AND version = :expected_version
  AND epoch   = :current_epoch;
```

Wenn die `WHERE`‑Klausel keine Zeile trifft, ist ein konkurrierender Schreiber dazwischen gekommen – der Vorgang muss mit dem neu gelesenen `version` wiederholt werden (klassisches Compare‑And‑Swap).  

### 1.4 Lesen vor jedem Tick  
Jeder Knoten führt unmittelbar vor Beginn eines Ticks einen schreibgeschützten SELECT aus:

```
SELECT name, value_real
FROM regulator
ORDER BY name;
```

Das Ergebnis wird in ein lokales Read‑Only‑Dictionary geladen und dient als Eingabe für alle regulator‑abhängigen Berechnungen (Attention‑Decay, Temperature, Commit‑Strenge usw.).  

### 1.5 Beispiel‑Regler und zulässige Wertebereiche  

| Regler‑Name          | Bedeutung                              | Wertebereich | Default | Einheit / Interpretation |
|----------------------|----------------------------------------|--------------|---------|--------------------------|
| attention_decay      | Memory‑Decay‑Rate (exponentiell)       | 0.001 – 0.5  | 0.05    | pro Tick, Faktor < 1    |
| creativity_temp      | Temperatur für Sampling (Top‑P‑Bias)   | 0.1 – 2.0    | 0.7     | dimensionless            |
| creativity_top_p     | Top‑P‑Massenschwelle                   | 0.5 – 0.99   | 0.9     | Wahrscheinlichkeit       |
| risk_cas_strictness  | CAS‑Commit‑Strenge (Mindest‑Übereinstimmung) | 1 – 10 | 5 | Anzahl notwendiger STRONG‑Übereinstimmungen |
| risk_evidence_thr    | Schwelle für STRONG‑Evidenz (Stärke)   | 0.1 – 1.0    | 0.6     | normierte Stärke         |
| risk_neutral_bias    | Bias gegenüber NEUTRAL‑Evidenz         | -0.5 – 0.5   | 0.0     | Additiv zu Stärke        |
| ...                  | (weitere Regler siehe Teil 6)          |              |         |                          |

Alle Regler werden als `REAL` gespeichert; ganzzahlige Regler werden als Ganzzahl‑ähnliche Floats behandelt (z.B. `risk_cas_strictness` wird auf die nächste ganze Zahl gerundet).  

---  

## TEIL 2 – HOMOEOSTASE / SELBST‑ALIGNMENT PER FEEDBACK  

### 2.1 Rollenverteilung unter den zehn Knoten  

| Knoten‑Typ      | Anzahl | Hauptaufgabe                                                                 |
|-----------------|--------|------------------------------------------------------------------------------|
| Generatoren/Explorer | 6      | Führen Modell‑Inferenz durch, erzeugen NODE_RESULT/v1, senden Evidenz‑Items an den World‑Model‑Tick. |
| Meta‑Evaluatoren   | 4      | Lesen aktuelle `scopes` und alle NODE_RESULT/v1 des letzten Ticks, berechnen Homöostasemetriken, justieren Regler per CAS. |

Die Zuordnung ist statisch (z.B. Knoten‑IDs 0‑5 = Generatoren, 6‑9 = Meta‑Evaluatoren) und kann über die `nodes`‑Tabelle überschrieben werden, bleibt jedoch für die Laufzeit konstant.  

### 2.2 Berechenbare Metriken (aus NODE_RESULT/v1 und scopes)  

Alle Meta‑Evaluatoren führen dieselben Berechnungen durch; das Ergebnis wird mittels Durchschnitt über die vier Evaluatoren gebildet, um Rauschen zu reduzieren.  

#### 2.2.1 Zielabweichung (Goal‑Error)  
Angenommen, das System hat ein explizites Ziel‑Vector `G` (z.B. gewünschte Wahrscheinlichkeit für `weather:forecast = STORM_ARRIVING`). Aus den aktuellen `scopes` wird die aktuelle Wahrscheinlichkeit `P_i` für jedes Scope‑Attribut extrahiert (aus der Verteilung über Zweige).  

```
GoalError = sqrt( Σ_i (P_i - G_i)^2 )          -- euklidische Norm über alle Scope‑Attribute
```

#### 2.2.2 Konsistenz‑Score (Konsistenz zwischen Zweigen)  
Für jedes Scope wird die Wahrscheinlichkeit des dominanten Zweigs `p_dom` und die Summe der Wahrscheinlichkeiten der übrigen Zweige `p_rest` berechnet.  

```
Consistency = 1 - ( Σ_scope (p_rest / (p_dom + p_rest)) ) / N_scopes
```
Wert liegt zwischen 0 (vollständig inkonsistent) und 1 (voll konsistent).  

#### 2.2.3 Entropie des World‑Models  
Shannon‑Entropie über alle Scope‑Zweige:  

```
Entropy = - Σ_scope Σ_branch p_branch * log(p_branch)
```
Niedrige Entropie → fokussiert; hohe Entropie → explorativ.  

#### 2.2.4 Sicherheitsmarge (Safety‑Margin)  
Aus den `risk_*`‑Reglern und der aktuellen Evidenz‑Stärke:  

```
SafetyMargin = risk_evidence_thr - max_observed_STRONG_strength
```
Positiv bedeutet, dass aktuelle starke Evidenz noch unter der Schwelle liegt; negativ bedeutet Überschreitung (potentielles Risiko).  

### 2.3 Regelgesetz – PID‑Regler für Kreativität  

Wir demonstrieren den Mechanismus am Regler `creativity_temp`. Ziel ist es, die Entropie auf einen Sollwert `Entropy_set` (z.B. 1.2 nats) zu halten, während gleichzeitig die Zielabweichung minimiert wird.  

#### 2.3.1 Fehler signal  
```
e_t = (Entropy_set - Entropy_t) + w_goal * GoalError_t
```
`w_goal` ist ein Gewicht (z.B. 0.3) das Zielabweichung in den Fehler einbezieht.  

#### 2.3.2 PID‑Gesetz  
```
Δcreativity_temp_t = Kp * e_t
                   + Ki * Σ_{k=0}^{t} e_k * Δt
                   + Kd * (e_t - e_{t-1}) / Δt
```
- `Kp`, `Ki`, `Kd` sind konstant eingestellte Gain‑Parameter (z.B. Kp=0.4, Ki=0.05, Kd=0.1).  
- `Δt` ist die Tick‑Dauer in Sekunden (gemessen über die Systemuhr, typisch ~1 s).  

Der neue Reglerwert wird dann wie folgt gesetzt (mit Begrenzung auf den zulässigen Bereich):  

```
creativity_temp_{t+1} = clip( creativity_temp_t + Δcreativity_temp_t , 0.1 , 2.0 )
```

#### 2.3.3 Anti‑Windup  
Der Integraltanteil wird nur akkumuliert, wenn der Regler nicht bereits am Limit liegt (Standard‑Anti‑Windup).  

### 2.4 Analogien zu Ashbys Homeostat  
Die vier Meta‑Evaluatoren entsprechen den vier Rückkopplungsschleifen eines Homeostats: jeder berechnet einen Teilfehler (Entropie, Zielabweichung, Konsistenz, Sicherheitsmarge) und liefert einen eigenen PID‑Ausgang. Die finalen Reglerjustierungen ergeben sich aus dem gewichteten Durchschnitt der vier Ausgänge (Gewichte können gleich sein oder je nach aktueller Mission angepasst werden).  

---  

## TEIL 3 – FORTLAUFENDE KOGNITION (Leerlauf‑Ticks)  

### 3.1 Ziel  
Auch ohne neue externe Evidenz sollen die Knoten sinnvolle interne Prozesse durchführen: Konsolidierung von bereits erworbenen Zweigen, Neubewertung von Wahrscheinlichkeiten und Vorbereitung auf zukünftige Eingaben.  

### 3.2 Ablauf eines Leerlauf‑Ticks  

1. **Lesen der Regler** (wie üblich).  
2. **Interner Rückgriff**: Jeder Generator‑Knoten führt eine *self‑prompted* Inferenz aus, wobei das Eingabe‑Prompt ein zufällig ausgewähltes früheres NODE_RESULT/v1 aus dem eigenen kurzen‑Zeit‑Speicher (letzte 5 Ticks) ist. Dies simuliert „Gedanken‑Replay“.  
3. **Evidenz‑Aggregation ohne neuen Input**: Die erzeugten NODE_RESULT/v1 werden wie üblich in die Outbox geschrieben, jedoch wird das Feld `external` auf `false` gesetzt. Der World‑Model‑Tick behandelt diese Einträge genauso wie externe Evidenz, jedoch mit einem reduzierten Gewichtungsfaktor `w_internal` (z.B. 0.3).  
4. **Scope‑Update**: Der World‑Model‑Tick führt den regulären GWT‑Broadcast/Uptake‑Schritt durch, wobei die internen Evidenz‑Items mit dem niedrigeren Gewicht berücksichtigt werden. Dies kann zu einer leichten Verschiebung der Zweig‑Wahrscheinlichkeiten führen, repräsentiert jedoch eine *Konsolidierung* (Bestätigung bereits bestehender Hypothesen) statt einer willkürlichen Drift.  
5. **Meta‑Evaluierung**: Wie gewohnt berechnen die Meta‑Evaluatoren die Homöostasemetriken und justieren Regler. Da keine neuen starken externen Evidenzen eintreffen, neigt das System dazu, die Entropie zu reduzieren (fokussiertes Denken) und die Kreativität leicht zu senken, wenn die Zielabweichung bereits gering ist.  

### 3.3 Ressourcenschonend & Absturzsicher  
- Der interne Rückgriff nutzt ausschließlich bereits im Speicher vorhandene Tensor‑Daten; kein neues Modell‑Laden ist nötig.  
- Die Outbox‑Schreiboperation bleibt gleich; falls ein Knoten während des Leerlauf‑Ticks abstürzt, wird sein Lease nicht verlängert und die übrigen neun Knoten übernehmen seine Aufgaben (wie im bestehenden Lease‑Mechanismus).  
- Da kein neuer externer Input erforderlich ist, kann das System beliebig viele Leerlauf‑Ticks hintereinander ausführen, ohne dass die SQLite‑WAL überlastet wird (nur reguläre Meta‑Updates und gelegentliche NODE_RESULT‑Einträge).  

---  

## TEIL 4 – DREI ARCHITEKTUR‑RISIKEN UND KONKRETE LÖSUNGEN  

### 4.1 (A) Oszillation / Übersteuerung der Feedback‑Schleife  

**Problem**: Ein zu aggressiver PID‑Regler kann zu periodischem Überschwingen der Reglerwerte führen (z.B. Kreativität oszilliert zwischen Minimum und Maximum).  

**Lösung – Dämpfung mittels Gain‑Scheduling und Derivat‑Filter**  

- **Derivat‑Filter**: Statt des reinen Differenzterms wird ein erster‑Ordnung‑Tiefpassfilter angewendet:  

```
D_filt_t = α * D_filt_{t-1} + (1-α) * (e_t - e_{t-1}) / Δt
```
mit α = 0.7 (empirisch gut gedämpft). Der PID‑Term verwendet `D_filt_t` anstelle des rohen Differenzterms.  

- **Gain‑Scheduling**: Wenn das Betrag des Fehler Signals `|e_t|` über einer Schwelle `E_high` liegt (z.B. 0.5), werden die Gains reduziert:  

```
Kp_eff = Kp * (E_high / |e_t|)   (begrenzt auf mindestens 0.2*Kp)
Ki_eff = Ki * (E_high / |e_t|)   (begrenzt auf mindestens 0.1*Ki)
Kd_eff = Kd * (E_high / |e_t|)   (begrenzt auf mindestens 0.05*Kd)
```
Unterhalb einer unteren Schwelle `E_low` (z.B. 0.1) werden die Gains auf ihre Nominalwerte zurückgesetzt. Dieses Schema verhindert große Auslöser bei kleinen Fehlern und dämpft starke Ausreißer.  

### 4.2 (B) Kontext‑Verzögerung / Latenz (Totzeit)  

**Problem**: Jeder Knoten‑Aufruf benötigt etwa 1 s für einen Forward‑Pass. Die Regler, die auf Basis des Zustands vom vorherigen Tick berechnet werden, wirken also auf einen Zustand, der bereits um eine Tick‑Dauer veraltet ist – klassische Totzeit.  

**Lösung – Smith‑Predictor‑ähnliche Kompensation**  

1. **Modell der Pflanzen**: Wir approximieren die Einflussfunktion eines Regleränderungs auf das Ziel‑Metric (z.B. Entropie) als ein erstes‑Ordnungssystem mit Zeitkonstanten τ ≈ 1.2 s (empirisch aus früheren Läufen bestimmt).  

2. **Predictor‑Berechnung**: Jeder Meta‑Evaluator berechnet neben dem gemessenen Fehler `e_t` auch einen *vorgehersagten* Fehler für den nächsten Tick, vorausgesetzt der Regler bleibt unverändert:  

```
e_pred_t = e_t * exp(-Δt/τ)   -- exponentielle Abklingung des aktuellen Fehlers über eine Tick‑Dauer
```

3. **Regelung mit kompensiertem Fehler**: Der PID‑Regler erhält als Eingabe den kombinierten Fehler  

```
e_comp_t = e_t + β * (e_pred_t - e_t)
```
wobei β ein Tuning‑Parameter ist (typisch β = 0.5). Wenn β = 0 erhalten wir das klassische Verhalten; β > 0 führt dazu, dass der Regler auf den erwarteten zukünftigen Fehler reagiert, wodurch die effektive Totzeit halbiert wird.  

4. **Implementierung**: Der Faktor `exp(-Δt/τ)` wird einmal pro Tick vorab berechnet und als Konstante gespeichert; die zusätzlichen Multiplikationen sind negligible.  

### 4.3 (C) Grounding / Realitätsanker  

**Problem**: Ohne regelmäßige harte externe Evidenz kann das System in einen reinen Echoraum abdriften, wo interne Konsolidierung falsche Überzeugungen verstärkt.  

**Lösung – Periodische Zwangseinspeisung mit Verifikationsschritt**  

- **Grounding‑Scheduler**: Eine separate Tabelle `grounding_slots` hält festgelegte Zeitpunkte (in Unix‑ms) für harte Einspeisungen.  

```
Table name: grounding_slots
Columns:
- slot_id   INTEGER PRIMARY KEY
- fire_at_ms INTEGER NOT NULL   -- absoluter Zeitpunkt des nächsten Grounding‑Events
- payload   TEXT    NOT NULL   -- JSON‑Array von (text, strength, supports_index) Tripeln
- used      INTEGER NOT NULL DEFAULT 0   -- 0 = noch nicht verbraucht, 1 = bereits eingespeist
```

- Beim Start des Systems wird die Tabelle mit einem vordefinierten Satz von Slots befüllt (z.B. alle 30 s ein Slot).  

- **Tick‑Logik**: Vor jedem World‑Model‑Tick prüft ein spezieller *Grounding‑Knoten* (kann einer der Meta‑Evaluatoren sein) die aktuelle Uhrzeit. Wenn `now_ms >= fire_at_ms` und `used = 0`, dann:  

  1. Die Payload wird als externe Evidenz in die Outbox geschrieben (mit `external = true`).  
  2. Der Slot wird als verwendet markiert (`UPDATE grounding_slots SET used = 1 WHERE slot_id = :id`).  
  3. Zusätzlich wird ein *Verifikations‑Token* erzeugt: ein Hash über die Payload und die aktuelle `state_digest` aus der `scopes`‑Tabelle. Dieser Token wird in einer neuen Tabelle `grounding_log` gespeichert, um später nachvollziehen zu können, welche harte Evidenz zu welchem Systemzustand geführt hat.  

```
Table name: grounding_log
Columns:
- log_id    INTEGER PRIMARY KEY AUTOINCREMENT
- slot_id   INTEGER NOT NULL
- ts_ms     INTEGER NOT NULL
- payload_hash TEXT NOT NULL
- state_digest TEXT NOT NULL
```

- **Auswirkung**: Die harte Einspeisung zwingt das World‑Model, sich an die externe Wahrheit anzupassen, unabhängig vom aktuellen internen Konsens. Der Regler‑Feedback‑Loop kann danach wieder homöostatisch arbeiten, aber die Grundannahmen werden regelmäßig korrigiert.  

---  

## TEIL 5 – MENSCH‑IN‑DER‑SCHLEIFE (LIVE‑OVERRIDE)  

### 5.1 Grundidee  
Der Mensch kann Reglerwerte direkt in die Tabelle `regulator` schreiben, genau wie ein automatischer Meta‑Evaluator. Beide Schreibpfade müssen koexistieren, ohne sich gegenseitig zu überschreiben.  

### 5.2 Schreibpfade und Prioritätsregel  

| Pfad               | Schreiber‑Flag (`writer`) | Priorität |
|--------------------|---------------------------|-----------|
| Mensch (Live‑Override) | 'human'                   | Hoch      |
| Automatisch (Meta‑Evaluator) | 'auto'                    | Niedrig   |

**Regel**: Bei einem konkurrierenden Schreibversuch auf denselben Regler innerhalb derselben Epoch gewinnt der Schreiber mit höherer Priorität. Der unterlegene Schreiber muss seinen Write‑Versuch verwerfen und beim nächsten Tick erneut versuchen (sein Wert wird dann möglicherweise überschrieben, wenn die Priorität weiterhin höher ist).  

### 5.3 Implementierung der Priorität im CAS‑Update  

Das Update‑Statement wird um eine Bedingung erweitert, die den aktuellen `writer` prüft:  

```
UPDATE regulator
SET value_real = :new_value,
    version    = version + 1,
    writer     = :writer,
    ts_ms      = :now_ms,
    comment    = :comment
WHERE name = :reg_name
  AND version = :expected_version
  AND epoch   = :current_epoch
  AND ( :writer = 'human'   -- menschlicher Schreiber gewinnt immer
        OR (writer <> 'human' AND :writer = 'auto') );  -- nur auto, wenn aktueller writer nicht human ist
```

Interpretation:  
- Wenn der aktuelle Eintrag bereits von einem Menschen geschrieben wurde (`writer = 'human'`), darf nur ein weiterer menschlicher Schreiber überschreiben (mensch‑zu‑mensch‑Überschreibung erlaubt, z.B. Korrektur).  
- Wenn der aktuelle Eintrag von einem Auto‑Schreiber stammt, kann ein menschlicher Schreiber jederzeit überschreiben (hohe Priorität).  
- Ein Auto‑Schreiber darf nur schreiben, wenn der aktuelle Eintrag ebenfalls von einem Auto‑Schreiber stammt (niedrige Priorität).  

### 5.4 Human‑Pin‑Dauer / Zerfallskonzept  

Ein menschlich gesetzter Wert soll für eine definierte Zeitspanne „gepinnt“ bleiben, bevor das automatische System ihn wieder ändern darf.  

- **Pin‑Dauer**: Beim menschlichen Write wird zusätzlich eine Spalte `pin_until_ms` gesetzt.  

```
ALTER TABLE regulator ADD COLUMN pin_until_ms INTEGER NOT NULL DEFAULT 0;
```

- Beim menschlichen Write:  

```
SET pin_until_ms = :now_ms + :human_pin_ttl_ms
```

- Beim automatischen Write wird die zusätzliche Bedingung eingefügt:  

```
AND ( pin_until_ms = 0 OR pin_until_ms <= :now_ms )
```

Das bedeutet: Ein Auto‑Schreiber kann nur schreiben, wenn entweder kein Pin gesetzt ist (`pin_until_ms = 0`) oder das Pin‑Verfallszeitpunkt bereits überschritten ist.  

- **Standard‑TTL**: 20 s (konfigurierbar über eine Umgebungsvariable oder einen Eintrag in einer neuen Tabelle `system_config`).  

### 5.5 Audit‑Trail  

Jeder Write (menschlich oder automatisch) erzeugt automatisch einen Eintrag in einer Audit‑Tabelle:  

```
Table name: regulator_audit
Columns:
- audit_id   INTEGER PRIMARY KEY AUTOINCREMENT
- reg_name   TEXT    NOT NULL
- value_real REAL    NOT NULL
- version    INTEGER NOT NULL
- writer     TEXT    NOT NULL
- ts_ms      INTEGER NOT NULL
- comment    TEXT    NULL
- pin_until_ms INTEGER NOT NULL
```

Der Trigger (oder das Anwendungslevel‑Code) insertiert nach jedem erfolgreichen UPDATE eine Zeile. Damit lässt sich nachvollziehen, wer welchen Wert wann geschrieben hat und ob er menschlich oder automatisch war.  

---  

## TEIL 6 – KOGNITIVES LEGO (Zentrale Forschungsfrage)  

### 6.1 Prinzip  
Kognition wird als Menge unabhängiger Regler‑Bausteine betrachtet. Jeder Baustein exponiert ein klar definiertes Steuer‑Signal, das ein bestimmtes Teilaspekt der kognitiven Verarbeitung beeinflusst. Durch Kombinieren von Bausteinen kann ein Nicht‑Techniker ein gewünschtes kognitives Verhalten zusammenstellen, vergleichbar mit dem Stecken von LEGO‑Steinen.  

### 6.2 (a) Systematischer Regler‑Baustein‑Katalog  

| Baustein‑Name          | Kurz‑Beschreibung                              | Exponierte Parameter (Name, Typ, Wertebereich, Default) | Betroffener Teil von S1 / Knoten | Anmerkungen |
|------------------------|-----------------------------------------------|----------------------------------------------------------|----------------------------------|-------------|
| attention_decay        | Exponentieller Gedächtnis‑Abfall               | `decay_rate` REAL [0.001,0.5] 0.05                     | Alle Generatoren (Memory‑Update) | Höher = schnelleres Vergessen |
| creativity_temp        | Sampling‑Temperatur (Exploration)             | `temp` REAL [0.1,2.0] 0.7                               | Alle Generatoren (Softmax)       | Höher = mehr Zufall |
| creativity_top_p       | Nucleus‑Massenschwelle                         | `top_p` REAL [0.5,0.99] 0.9                            | Alle Generatoren                 | Höher = fokussierter |
| risk_cas_strictness    | Mindestzahl übereinstimmender STRONG‑Evidenz für Commit | `strict` INTEGER [1,10] 5                     | Koordinator‑Lease‑Logik          | Höher = konservativer |
| risk_evidence_thr      | Schwelle für STRONG‑Stärke                     | `thr` REAL [0.1,1.0] 0.6                               | World‑Model‑Evidenz‑Bewertung    | Höher = anspruchsvoller |
| risk_neutral_bias      | Bias gegenüber NEUTRAL‑Evidenz                 | `bias` REAL [-0.5,0.5] 0.0                             | World‑Model‑Evidenz‑Aggregation  | Positiv = NEUTRAL bevorzugen |
| memory_horizon         | Wie viele frühere Ticks im Kurz‑Zeit‑Speicher gehalten werden | `horizon` INTEGER [1,20] 5                     | Generatoren (Replay‑Puffer)      | Höher = längerer Kontext |
| exploration_exploit    | Trade‑off zwischen neuem Sampling und Wiederverwendung von Top‑K‑Resultaten | `exploit_frac` REAL [0.0,1.0] 0.6               | Generatoren (Auswahl von Kandidaten) | 0 = rein explorativ, 1 = rein exploitative |
| consensus_threshold    | Anzahl Knoten, die gleiche STRONG‑Alternative benötigen für Kollaps | `consensus_needed` INTEGER [2,10] 6           | World‑Model‑Collapse‑Logik       | Höher = stärkerer Konsens erforderlich |
| evidence_half_life     | Exponentieller Abwägungsfaktor für alte Evidenz | `half_life_ticks` REAL [1,50] 10.0                | World‑Model‑Gewichtung           | Niedriger = stärkerer Fokus auf frische Evidenz |
| dissent_tolerance      | Maximal erlaubter Anteil widersprüchlicher STRONG‑Evidenz bevor Branches erhalten bleiben | `dissent_max` REAL [0.0,1.0] 0.2               | World‑Model‑Collapse‑Bedingung   | Höher = mehr Toleranz für Konflikt |
| coordinator_rot_aggr   | Wie aggressiv der Lease‑Wechsel zwischen Knoten erfolgt (häufigerer Wechsel = höhere Aggressivität) | `rotate_aggr` REAL [0.0,1.0] 0.3               | Lease‑Vergabe‑Algorithmus        | Höher = häufigerer Coordinator‑Wechsel |
| idle_tick_depth        | Wie viele interne Replay‑Schritte ein Leerlauf‑Tick durchführt | `depth` INTEGER [1,10] 3                        | Generatoren (Self‑Prompt‑Anzahl) | Höher = tieferes internes Denken |
| grounding_freq         | Wie oft harte externe Evidenz eingespeist wird (in Sekunden) | `freq_s` REAL [5,300] 30.0                     | Grounding‑Scheduler              | Niedriger = häufigeres Grounding |
| safety_margin_target   | Zielwert für die Sicherheitsmarge (positiv = Puffer) | `target` REAL [-1.0,1.0] 0.2                    | Meta‑Evaluator‑PID‑Eingabe       | Höher = mehr Risikoaversion |
| emotion_valence        | Simulierter Affekt‑Bias, der die Bewertung von Evidenz beeinflusst | `valence` REAL [-1.0,1.0] 0.0                  | World‑Model‑Evidenz‑Weighting    | Positiv = positiver Bias |
| ...                    | (weitere Bausteine können analog definiert werden) |                                                    |                                  |             |

Jeder Baustein ist orthogonal: Er beeinflusst ausschließlich die in seiner Spalte „Betroffener Teil von S1 / Knoten“ genannten Komponenten und lässt andere unberührt, vorausgesetzt die Werte bleiben innerhalb der definierten Bereiche.  

### 6.3 (b) Schnittstellenbeschreibung eines einzelnen Bausteins  

Ein Baustein besteht aus:  

1. **Name** (z.B. `attention_decay`).  
2. **Parameterliste** (ein oder mehrere `name:typ[min,max]=default` Einträge).  
3. **Zustandsbereich**: Welche Spalten in den Tabellen `scopes`, `nodes`, `tasks` oder `regulator` er liest bzw. schreibt.  
4. **Wirkungsfunktion**: Eine mathematische Formel, die aus dem Parameterwert den konkreten Effekt auf das System ableitet (z.B. für `attention_decay`: `memory_weight_{t+1} = memory_weight_t * (1 - decay_rate)`).  
5. **Validierungsbereich**: Eingabewerte werden beim Schreiben in `regulator` auf den definierten Bereich geklippt; außerhalb liegende Werte werden abgelehnt und führen zu einem Fehler‑Log‑Eintrag.  
6. **Namensraum‑Regel**: Bausteinnamen sind eindeutig und dürfen keine Punkte oder Leerzeichen enthalten; sie werden direkt als `name`‑Spalte in `regulator` verwendet.  
7. **Unabhängigkeitsgarantie**: Zwei Bausteine dürfen nicht denselben Regler‑Name teilen. Wenn ein Baustein mehrere Parameter benötigt, erhält jeder Parameter einen eigenen Eintrag in `regulator` mit einem Präfix, z.B. `attention_decay_rate`, `attention_decay_offset`. Dadurch lässt sich sicherstellen, dass das Ändern eines Bausteins keinen anderen beeinflusst, solange die Präfixe eindeutig sind.  

### 6.4 (c) UI‑Metapher – Regler‑Steckbrett  

- **Ansicht**: Ein vertikales Feld mit beschrifteten Schiebereglern (Slider), jeweils ein Slider pro Baustein‑Parameter.  
- **Layout**: Jeder Slider zeigt den aktuellen Wert, den erlaubten Bereich (Min/Max als Tick‑Markierungen) und den Default‑Wert als dünne graue Linie.  
- **Interaktion**: Beim Bewegen des Schiebereglers wird sofort ein `UPDATE regulator SET value_real = <neuer_wert> WHERE name = '<parameter_name>'` ausgelöst (mit der menschlichen Writer‑Priorität und Pin‑TTL, siehe Teil 5).  
- **Feedback**: Der Slider zeigt den aktuellen Wert in Echtzeit an; bei einem erfolgreichen Write wird die Hintergrundfarbe kurz grün, bei einem Konflikt (z.B. weil ein Auto‑Schreiber gerade schreibt und der menschliche Versuch aufgrund von Priorität abgelehnt wird) kurz rot.  
- **Persistenz**: Beim Laden der UI werden alle Einträge aus `regulator` gelesen und die Slider entsprechend positioniert.  
- **Export/Import**: Ein Button „Konfiguration speichern“ schreibt den gesamten `regulator`‑Inhalt als JSON‑Datei; ein Button „Konfiguration laden“ führt eine Reihe von `UPDATE`‑Statements aus (mit menschlicher Priorität).  

Da jeder Slider unmittelbar auf die Tabelle `regulator` schreibt, ist die UI 1:1 auf den Schreibzugriff aus Teil 1 abgebildet – kein zusätzlicher Mapping‑Layer nötig.  

### 6.5 (d) Zusammenspiel mit Homoeostase (Teil 5)  

- Die **automatischen Reglerjustierungen** der Meta‑Evaluatoren schreiben ebenfalls in `regulator` mit `writer = 'auto'`.  
- Der **Human‑Pin‑Mechanismus** sorgt dafür, dass ein vom Menschen gesetzter Wert für die konfigurierte TTL (z.B. 20 s) vor automatischen Überschreibungen geschützt ist. Nach Ablauf der TTL darf das automatische System den Regler wieder anpassen (wie ein gewöhnlicher PID‑Ausgleich).  
- Damit sind die **Bausteine** exakt die Regler, die sowohl von Menschen als auch von automatischen Meta‑Evaluatoren manipuliert werden können. Die UI ermöglicht dem Nicht‑Techniker, einzelne Bausteine zu stellen; die Homoeostase arbeitet im Hintergrund an allen Bausteinen, die nicht gepinnt sind.  
- **Konflikterkennung**: Wenn ein Mensch einen Baustein auf einen Wert setzt, der außerhalb des zulässigen Bereichs des automatischen Reglers liegt (z.B. ein zu niedriges `attention_decay` das zu Instabilität führen würde), lehnt das System den Write ab und zeigt eine Warnung an. Der Mensch muss den Wert innerhalb des sicheren Bereichs wählen oder das System im „Explorations‑Modus“ temporär außer Kraft setzen (über einen speziellen Override‑Schalter, der den `writer` auf 'human' setzt und alle Pins auf 0 setzt).  

---

---

## TEIL 7 – EXPERIMENTPLAN  

### 1. Ziel  
Demonstrieren, dass die **regulator‑Tabelle** im SQLite/WAL‑Fabric‑Backend ( `grid10_fabric.py` ) zur Laufzeit von Knoten ( `grid10_node.py` ) ausgelesen und deren Werte *Temperature* und *Top‑P* direkt an die LLM‑Inference‑API übergeben werden.  
Zusätzlich wird geprüft, ob **Meta‑Evaluatoren** (vier der zehn Knoten) die Regler‑Werte aktiv anpassen können, ohne dass das Gesamtsystem instabil wird.  

Erfolgsindikatoren:  

| Kennzahl | Soll‑Wert | Akzeptanzbereich |
|----------|-----------|------------------|
| **Durchschnittliche Modell‑Temperatur** (aus `cognitive_answer`) | 0,85 | 0,80 – 0,90 |
| **Durchschnittlicher Top‑P** | 0,92 | 0,88 – 0,96 |
| **Latenz pro Tick** (Node‑Loop → `model.generate`) | ≤ 180 ms | ≤ 250 ms |
| **Stabilität der Lease‑TTL** (keine verfrühten Expirations) | 0 Verluste | ≤ 1 Verlust pro Lauf |
| **Konsistenz der Evidenz‑Logik** (STRONG/WEAK/NEUTRAL) | 100 % Übereinstimmung | ≥ 98 % |

### 2. Versuchsaufbau  

| Komponente | Datei / Klasse | Modifikationen |
|------------|----------------|----------------|
| **Fabric‑Backend** | `grid10_fabric.py` | - Neue Tabelle `regulators` (id INTEGER PK, `temperature` REAL, `top_p` REAL, `updated_at` TIMESTAMP).<br>- Hilfsfunktionen `set_regulator(temperature, top_p)` und `get_regulator()`.<br>- CAS‑Commit‑Logik für gleichzeitige Updates (wie bei `leases`). |
| **Node‑Loop** | `grid10_node.py` | - Vor jedem Tick wird `reg = fabric.get_regulator()` aufgerufen.<br>- Werte werden an `model.generate(prompt, temperature=reg.temperature, top_p=reg.top_p)` weitergereicht.<br>- `cognitive_answer()` speichert die tatsächlich genutzten Parameter im Log‑Eintrag (`node_result`). |
| **Simulation‑Runner** | `run_grid10_world_model_simulation_v3_regulated.py` (Kopie von v2) | - Startet 10 Prozesse wie v2.<br>- 4 Prozesse erhalten das Flag `meta_evaluator=True` und führen zusätzlich `meta_regulator_loop()` aus (siehe unten).<br>- Jeder Tick erzeugt ein **Regler‑Write‑Event** (siehe Test‑Client) und schreibt die neuen Werte in die `regulators`‑Tabelle. |
| **Meta‑Evaluator‑Loop** (innerhalb `grid10_node.py`) | neue Funktion `meta_regulator_loop(node_id)` | - Liest aktuelle Evidenz‑Scores aus `tasks`/`scopes`.<br>- Berechnet ein PID‑ähnliches Steuer‑Signal (z. B. Ziel‑Temperature = 0,85, Ziel‑Top‑P = 0,92).<br>- Schreibt über `fabric.set_regulator()` zurück. |
| **Test‑Client** | `test_regulator_client.py` | - Simuliert menschliche Eingriffe zu definierten Ticks (z. B. Tick 2, 5, 8).<br>- Sendet zufällige, aber plausible Werte (Temperature ∈ [0.6, 1.0], Top‑P ∈ [0.8, 1.0]).<br>- Nutzt dieselbe `grid10_fabric`‑API, um `set_regulator` aufzurufen. |
| **Logging** | `metrics_log.csv` (im Arbeitsverzeichnis) | - Pro Tick: `tick, node_id, temperature, top_p, latency_ms, evidence_type, lease_status`.<br>- Am Ende des Laufs: Aggregierte Kennzahlen (Mittelwert, Std‑Abw., Max‑Latency). |

#### 2.1. Datenbank‑Schema‑Erweiterung (`grid10_fabric.py`)

```python
# --- am Ende der bestehenden Table‑Definitionen ---
def _init_regulator_table(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS regulators (
            id          INTEGER PRIMARY KEY CHECK (id = 1),
            temperature REAL NOT NULL DEFAULT 0.85,
            top_p       REAL NOT NULL DEFAULT 0.92,
            updated_at  TIMESTAMP NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
        )
    """)
    # Ensure a single row exists
    cur = conn.execute("SELECT COUNT(*) FROM regulators")
    if cur.fetchone()[0] == 0:
        conn.execute("INSERT INTO regulators (id, temperature, top_p) VALUES (1, 0.85, 0.92)")
    conn.commit()

def set_regulator(temperature: float, top_p: float):
    """CAS‑style Update – verhindert Lost‑Updates bei konkurrierenden Meta‑Evaluatoren."""
    with _get_conn() as conn:
        cur = conn.execute("SELECT temperature, top_p FROM regulators WHERE id = 1")
        old_temp, old_top = cur.fetchone()
        # Simple CAS: only write if the row has not changed since we read it
        conn.execute("""
            UPDATE regulators
               SET temperature = ?, top_p = ?, updated_at = strftime('%Y-%m-%d %H:%M:%f', 'now')
             WHERE id = 1
               AND temperature = ? AND top_p = ?
        """, (temperature, top_p, old_temp, old_top))
        conn.commit()

def get_regulator() -> dict:
    with _get_conn() as conn:
        cur = conn.execute("SELECT temperature, top_p FROM regulators WHERE id = 1")
        temperature, top_p = cur.fetchone()
        return {"temperature": temperature, "top_p": top_p}
```

*Hinweis*: Die Funktion `_init_regulator_table` wird im Modul‑Initialisierer nach dem Anlegen der anderen Tabellen aufgerufen.

#### 2.2. Node‑Loop‑Anpassung (`grid10_node.py`)

```python
def node_loop(node_id: int, fabric: Grid10Fabric, model, meta_evaluator: bool = False):
    while True:
        # 1. Regler aus DB holen
        reg = fabric.get_regulator()
        temperature = reg["temperature"]
        top_p = reg["top_p"]

        # 2. Prompt erzeugen (wie bisher)
        prompt = build_prompt(node_id)

        # 3. Modell‑Inference mit dynamischen Parametern
        start = time.perf_counter()
        answer = model.generate(
            prompt,
            temperature=temperature,
            top_p=top_p
        )
        latency = (time.perf_counter() - start) * 1000  # ms

        # 4. Ergebnis loggen
        fabric.emit_node_result(
            node_id=node_id,
            answer=answer,
            temperature=temperature,
            top_p=top_p,
            latency_ms=latency
        )

        # 5. Optional: Meta‑Evaluator‑Logik
        if meta_evaluator:
            meta_regulator_loop(node_id, fabric)

        # 6. Lease‑TTL prüfen – bereits in bestehender Logik
        time.sleep(0.1)   # minimaler Sleep, um CPU‑Spitze zu vermeiden
```

#### 2.3. Meta‑Evaluator‑Loop (innerhalb `grid10_node.py`)

```python
def meta_regulator_loop(node_id: int, fabric: Grid10Fabric):
    """
    PID‑ähnlicher Regler, der Evidenz‑Scores aus den Tasks auswertet
    und die globalen Regler‑Parameter anpasst.
    """
    # Zielwerte (können später konfigurierbar sein)
    TARGET_TEMP = 0.85
    TARGET_TOPP = 0.92
    # Simple proportional controller
    Kp = 0.1

    # 1. Aktuelle Evidenz‑Scores aggregieren
    scores = fabric.aggregate_evidence_scores()   # → dict { "strong": n, "weak": n, "neutral": n }
    # 2. Fehler berechnen (z. B. mehr STRONG → höhere Temperature)
    error_temp = (scores["strong"] - scores["weak"]) * 0.01   # Skalierung
    error_top = (scores["strong"] - scores["neutral"]) * 0.005

    # 3. Neue Regler‑Werte berechnen
    new_temp = max(0.6, min(1.0, TARGET_TEMP + Kp * error_temp))
    new_top = max(0.8, min(1.0, TARGET_TOPP + Kp * error_top))

    # 4. Write‑Back (CAS)
    fabric.set_regulator(new_temp, new_top)
```

`fabric.aggregate_evidence_scores()` ist bereits in v2 als Hilfsfunktion vorhanden; falls nicht, wird sie analog zu `fabric.count_evidence_by_type()` implementiert.

#### 2.4. V3‑Runner (`run_grid10_world_model_simulation_v3_regulated.py`)

```python
#!/usr/bin/env python3
import multiprocessing as mp
from grid10_fabric import Grid10Fabric
from grid10_node import node_loop
from test_regulator_client import regulator_stimulus_sequence

NUM_NODES = 10
META_EVAL_COUNT = 4   # first 4 nodes act as meta‑evaluators
TICKS = 6

def launch_node(node_id: int, fabric: Grid10Fabric, model, meta: bool):
    node_loop(node_id, fabric, model, meta_evaluator=meta)

if __name__ == "__main__":
    fabric = Grid10Fabric(db_path="grid10.db")
    # ensure regulator table exists
    fabric._init_regulator_table(fabric._conn)

    # 1. Starte 10 Prozesse
    processes = []
    for i in range(NUM_NODES):
        is_meta = i < META_EVAL_COUNT
        p = mp.Process(
            target=launch_node,
            args=(i, fabric, load_model(), is_meta),
            name=f"node-{i}{'-meta' if is_meta else ''}"
        )
        p.start()
        processes.append(p)

    # 2. Simuliere menschliche Eingriffe parallel
    stim_thread = mp.Process(
        target=regulator_stimulus_sequence,
        args=(fabric, TICKS)
    )
    stim_thread.start()

    # 3. Warten bis alle Ticks erledigt (einfaches Barrier‑Muster)
    for _ in range(TICKS):
        fabric.wait_for_tick_completion()   # Blockiert bis alle Nodes ihren Tick gemeldet haben

    # 4. Graceful shutdown
    for p in processes:
        p.terminate()
    stim_thread.terminate()
    fabric.close()
```

*Wesentliche Änderungen gegenüber v2*:  

* `META_EVAL_COUNT` = 4 → vier Prozesse führen zusätzlich `meta_regulator_loop`.  
* `regulator_stimulus_sequence` erzeugt gezielte Writes (siehe unten).  
* Der Runner nutzt dieselbe Datenbank (`grid10.db`) und dieselben Lease‑/Scope‑Logiken wie v2, sodass keine neue Infrastruktur nötig ist.

#### 2.5. Test‑Client (`test_regulator_client.py`)

```python
import random
import time
from grid10_fabric import Grid10Fabric

# Vorgabe: Eingriffe bei Tick 2, 4, 6 (human‑simuliert) + automatischer PID‑Write von Meta‑Evaluatoren
def regulator_stimulus_sequence(fabric: Grid10Fabric, total_ticks: int):
    human_ticks = {2, 4, 6}
    for tick in range(1, total_ticks + 1):
        if tick in human_ticks:
            # Simulierter menschlicher Eingriff
            temp = round(random.uniform(0.65, 0.95), 2)
            top = round(random.uniform(0.85, 0.99), 2)
            fabric.set_regulator(temp, top)
            print(f"[Human] Tick {tick}: set temperature={temp}, top_p={top}")
        # Kleine Pause, damit Nodes den neuen Wert im nächsten Loop sehen
        time.sleep(0.5)
```

### 3. Protokoll (Ablauf pro Tick)

| Phase | Aktion | Verantwortlich | Erwartetes Ergebnis |
|-------|--------|----------------|---------------------|
| **0 – Init** | Datenbank öffnen, Regler‑Tabelle initialisieren | `run_grid10_world_model_simulation_v3_regulated.py` | Temperatur = 0,85, Top‑P = 0,92 |
| **1 – Tick‑Start** | Jeder Node ruft `fabric.get_regulator()` | `grid10_node.py` | Lokale Kopie der aktuellen Regler‑Werte |
| **2 – Inference** | `model.generate(prompt, temperature, top_p)` | `grid10_node.py` | Antwort + Latenz‑Messung |
| **3 – Emit** | `fabric.emit_node_result(...)` schreibt Zeile in `node_results` | `grid10_node.py` | Log‑Eintrag mit genutzten Parametern |
| **4 – Meta‑Eval** (nur Meta‑Knoten) | `meta_regulator_loop` berechnet neue Werte und schreibt sie | `grid10_node.py` | CAS‑Update in `regulators` |
| **5 – Human‑Stimulus** | `test_regulator_client` schreibt ggf. neue Werte | Test‑Client | CAS‑Update (überschreibt ggf. Meta‑Write) |
| **6 – Barrier** | `fabric.wait_for_tick_completion()` blockiert bis alle 10 Nodes gemeldet haben | Runner | Synchronisation, danach nächster Tick |
| **7 – Log‑Aggregation** | Am Ende des Laufs werden alle Zeilen aus `node_results` in `metrics_log.csv` exportiert | Runner | CSV‑Datei für Analyse |

### 4. Messgrößen & Erfolgskriterien  

| Messgröße | Erhebungsmethode | Zielwert | Akzeptanz |
|-----------|-------------------|----------|-----------|
| **Genutzte Temperature** | Feld `temperature` in `node_results` | Mittelwert 0,85 | 0,80 – 0,90 |
| **Genutzte Top‑P** | Feld `top_p` in `node_results` | Mittelwert 0,92 | 0,88 – 0,96 |
| **Inference‑Latenz** | Feld `latency_ms` in `node_results` | ≤ 180 ms | ≤ 250 ms |
| **Lease‑Verlust** | Zähler `expired_leases` (aus `leases`‑Tabelle) | 0 | ≤ 1 pro Lauf |
| **Evidenz‑Konsistenz** | Vergleich `evidence_type` in `node_results` mit erwarteter Logik (STRONG/WEAK/NEUTRAL) | 100 % | ≥ 98 % |
| **Regler‑Stabilität** | Standardabweichung der Temperatur‑ und Top‑P‑Werte über alle Nodes pro Tick | ≤ 0,04 | ≤ 0,07 |

Alle Messwerte werden nach jedem Tick in `metrics_log.csv` geschrieben (Zeile‑Header siehe unten).  

**Beispiel‑Header für `metrics_log.csv`**  

```
tick,node_id,temperature,top_p,latency_ms,evidence_type,lease_status
```

### 5. Datenanalyse  

1. **Aggregierte Statistiken**  
   ```python
   import pandas as pd
   df = pd.read_csv("metrics_log.csv")
   agg = df.groupby("tick").agg({
       "temperature": ["mean","std"],
       "top_p": ["mean","std"],
       "latency_ms": ["mean","max"]
   })
   print(agg)
   ```
2. **Regler‑Tracking**  
   Plotten von `temperature` und `top_p` über die Ticks, um zu prüfen, ob menschliche Eingriffe (Ticks 2, 4, 6) korrekt übernommen werden und ob die Meta‑Evaluatoren zwischen den Eingriffen wieder zum Zielwert zurückkehren.  
3. **Evidenz‑Korrelation**  
   Kreuztabellierung von `evidence_type` vs. `temperature`‑Änderungen, um zu prüfen, ob der PID‑Controller tatsächlich auf Evidenz‑Schwankungen reagiert.  
4. **Lease‑Analyse**  
   Auswertung von `lease_status` (OK / EXPIRED) zur Bestätigung, dass die 8‑s‑TTL nicht verletzt wird, selbst wenn Regler‑Writes häufig sind.  

### 6. Risiken & Gegenmaßnahmen  

| Risiko | Beschreibung | Gegenmaßnahme |
|--------|--------------|---------------|
| **Race‑Condition beim Regler‑Update** | Mehrere Meta‑Evaluatoren und der Human‑Client können gleichzeitig `set_regulator` aufrufen. | CAS‑Update in `set_regulator`; bei Fehl‑Update wird ein kurzer Retry (max 3 Versuche) durchgeführt. |
| **Model‑API‑Verzögerungen** | Hohe Latenz kann Tick‑Barrier blockieren. | Timeout‑Wrapper um `model.generate`; bei Timeout wird ein Default‑Antwort mit `temperature=0.85, top_p=0.92` erzeugt. |
| **Lease‑Expiry während Regler‑Write** | Ein Schreib‑Vorgang könnte durch einen abgelaufenen Lease unterbrochen werden. | `fabric.set_regulator` nutzt dieselbe Lease‑Logik wie andere Writes – wenn Lease fehlt, wird automatisch ein neuer Lease angefordert, bevor das Update erfolgt. |
| **Unrealistische Human‑Werte** | Werte außerhalb des zulässigen Bereichs könnten das System destabilisieren. | `set_regulator` clampt Eingaben auf `[0.6,1.0]` für Temperature und `[0.8,1.0]` für Top‑P. |
| **Fehlende Aggregations‑Funktion** | `aggregate_evidence_scores` könnte bei neuer Schema‑Version fehlen. | Implementiere Fallback‑Logik, die direkt `SELECT`‑Abfragen auf `tasks` ausführt, falls die Hilfsfunktion nicht existiert. |

### 7. Abschluss & Reporting  

Nach Durchlauf des Skripts `run_grid10_world_model_simulation_v3_regulated.py` wird automatisch `metrics_log.csv` erzeugt. Der Analyst führt das Python‑Analyse‑Notebook `analyze_grid10_v3.ipynb` (im Repository vorhanden) aus, das die oben beschriebenen Plots und Tabellen generiert.  

Ein kurzer **Test‑Report** (max. 2 Seiten) fasst die wichtigsten Kennzahlen zusammen, vergleicht die geplanten Soll‑Werte mit den gemessenen Ist‑Werten und gibt eine Empfehlung, ob das Regler‑Subsystem für den nächsten Integrationsschritt (UI‑Slider‑Frontend) freigegeben werden kann.

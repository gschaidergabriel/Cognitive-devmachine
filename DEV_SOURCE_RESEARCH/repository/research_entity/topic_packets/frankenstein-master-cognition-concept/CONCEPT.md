# Frankenstein Master-Kognitionskonzept

**Status:** ERSTE FASSUNG, grundlage fuer den 72h-Umsetzungsauftrag. ChatGPT confirmed
down (fuenfter real bestaetigter Ausfall an diesem Tag, 403/Cloudflare, Log:
`~/scripts/chatgpt_burst_state/burst_v2_20260827_231249.log`) -- Free-Pool-Fallback
(Groq/Nemotron via `~/last-resort/llm.py`) genutzt und KRITISCH GEGENGEPRUEFT.

**Wichtiger Hinweis zur externen Konsultation:** die erste Roh-Antwort des Free-Pools
enthielt mehrere real ERFUNDENE, nicht mit dem existierenden Code vereinbare Elemente
(eine "InfluxDB-kompatible Time-Series-DB", "128-dimensionale Embedding-Vektoren aus
den letzten 10ms", "Graph mit gewichteten Kanten") -- keins davon existiert im echten
GRID10-Code. Dieses Dokument uebernimmt NUR die strukturell brauchbaren Ideen (gestufte
Toleranzzonen, gedaempfter PI-Regler, deterministische Reflex-Schicht) und wendet sie
auf die TATSAECHLICH heute gebaute Architektur an (SQLite/WAL-Fabric, CAS-Regler-Tabelle,
elastic_poll, release_idle_memory) -- nicht auf erfundene Datenstrukturen.

---

## 1. Ehrlicher Rahmen: was heute real existiert vs. was aspirational ist

**Real existiert (gebaut, getestet, verifiziert heute):**
- `tools/grid10_fabric.py`: SQLite/WAL-Fabric mit CAS-Commits, Lease-Koordination,
  Task-Claiming, Stale-Reclaim, und einer generischen `regulators`-Tabelle
  (`get_regulator`/`set_regulator`, versionierte CAS, `writer`-Feld fuer Herkunft).
- `tools/grid10_node.py`: `node_loop()` mit `elastic_poll` (regler-gesteuerte
  Poll-Frequenz), `meta_regulator_tick()` (echter, einfacher homoeostatischer Regler
  auf Basis eines messbaren Signals -- Anteil nicht-leerer Antworten), `release_idle_memory()`
  (echte RAM-Freigabe im Leerlauf), Human-Pin-Cooldown (ein Regler-Schreiber "human-simulated"
  blockiert automatische Ueberschreibung fuer ein Zeitfenster).
- Reale Messwerte: ~5 Fabric-Transaktionen/Sekunde, ~379MB reduzierbarer RAM/Prozess,
  Thread-Contention-Grenzen (1 Thread/Prozess bei 4 gleichzeitigen Prozessen optimal).

**Aspirational, NICHT heute im Code vorhanden (ehrlich benannt statt erfunden):**
- Permanenter Betrieb ab Rechnerstart (GRID10 laeuft heute nur, wenn explizit als
  Python-Skript gestartet -- kein systemd-Service, kein Boot-Hook).
  - Der neue Betrieb-Layer (Abschnitt 5) definiert einen echten,minimalen Weg dahin
  (systemd-Unit + Watchdog), aber das ist NEUE Infrastruktur, keine Erweiterung von
  bereits Laufendem.
- Physische Sensorik (Feuer-Erkennung o.ae.) -- GRID10 hat KEINE Kamera-/Sensor-Anbindung.
  Ein reales "Feuer erkennen" braeuchte eine echte externe Sensor-/Vision-Pipeline, die
  hier nicht spezifiziert wird (ausserhalb des GRID10-Fabric-Scopes) -- das Konzept
  beschreibt stattdessen den REFLEX-MECHANISMUS generisch (ein deterministischer Trigger
  -> eine deterministische Gegenmassnahme, <500ms, ohne LLM), mit Feuer als Beispiel
  eines MOEGLICHEN zukuenftigen Sensors, nicht als heute existierende Faehigkeit.
- Web-App-Frontend fuer "kognitives Lego" -- noch nicht gebaut, hier als Anforderung
  spezifiziert (Abschnitt 6), nicht als Bestandsaufnahme.

---

## 2. Architektur-Uebersicht (Text-Diagramm, auf echtem Code aufbauend)

```
+--------------------------------------------------------------------+
|                  FRANKENSTEIN KOGNITIVE SCHLEIFE                   |
|                                                                    |
|  +------------------+     +-------------------+                   |
|  |  GRID10-Fabric   |<--->|  regulators-Tabelle|  (bereits real:   |
|  |  (SQLite/WAL,    |     |  (bereits real:    |   CAS, versioniert|
|  |  tasks/scopes/   |     |   get/set_regulator)|   writer-Feld)   |
|  |  leases/outbox)  |     +---------+----------+                   |
|  +--------+---------+               |                              |
|           |                         | liest/schreibt               |
|           v                         v                              |
|  +------------------+     +-------------------+     +------------+ |
|  |  Node-Pool        |     |  Alignment-Regler | --> | Toleranz-  | |
|  |  (node_loop,      |<--->|  (NEU, Abschnitt 3)|     | Zonen-Log  | |
|  |  elastic_poll,    |     +-------------------+     +------------+ |
|  |  meta_regulator_  |               ^                              |
|  |  tick -- alle     |               |                              |
|  |  bereits real)    |     +---------+----------+                   |
|  +--------+---------+     |  Reflex-Schicht     |  (NEU, Abschnitt 4)|
|           |                |  (deterministisch, |  laeuft AUSSERHALB |
|           |                |  <500ms, ohne LLM) |  des LLM-Pfads     |
|           v                +---------------------+                   |
|  +------------------+                                                |
|  |  Claude-Code-     |  (NEU, Abschnitt 5 -- Vektor-IPC, Fallback   |
|  |  Bruecke          |   bei Ausfall: Schleife laeuft weiter,       |
|  +------------------+   nur ohne Claude-Eskalation)                 |
|                                                                    |
|  +------------------+                                                |
|  |  Web-UI (NEU,     |  liest/schreibt regulators-Tabelle live,     |
|  |  Abschnitt 6)     |  zeigt Fabric-Zustand + Alignment-Historie   |
|  +------------------+                                                |
+--------------------------------------------------------------------+
```

---

## 3. Alignment-Mechanik (konkret, auf echten Daten)

**Messung der Abweichung (delta), REAL berechenbar aus vorhandenen Daten -- kein
erfundener Embedding-Vektor:**

`delta` wird NICHT als Cosinus-Distanz zwischen erfundenen Vektoren berechnet, sondern
als gewichtete Summe aus real messbaren Signalen, die bereits im Fabric existieren:

- `reject_rate`: Anteil der letzten N Ergebnisse (aus `outbox`/`admitted_results`),
  die vom Alignment-Regler als "nicht userkonform" markiert wurden (z.B. via ein
  einfaches Keyword-/Muster-Gate, oder -- ehrlicher -- ein vom User explizit gesetztes
  `feedback`-Feld pro Ergebnis, das GRID10 heute noch nicht hat und dafuer neu
  eingefuehrt werden muesste).
- `regulator_drift`: wie weit aktuelle Regler-Werte (z.B. `temperature`) vom
  User-konfigurierten Zielwert abweichen (bereits real messbar: `get_regulator(name)["value_real"]`
  vs. ein User-Zielwert, der in einer neuen `alignment_targets`-Tabelle liegt).
- `reflex_trigger_rate`: wie oft die Reflex-Schicht (Abschnitt 4) in den letzten N
  Sekunden ausgeloest hat -- haeufige Reflex-Ausloesung deutet auf ein System hin, das
  von seinem konfigurierten Normalbetrieb abweicht.

`delta = w1*reject_rate + w2*regulator_drift + w3*reflex_trigger_rate` (Gewichte
`w1..w3` selbst als Regler in der bestehenden `regulators`-Tabelle, User-editierbar).

**Toleranzzonen (gestuft, uebernimmt die brauchbare Grundidee der externen
Konsultation):**
- `delta <= tau_low` (Default 0.05): Safe-Zone, keine Intervention.
- `tau_low < delta <= tau_high` (Default 0.15): Warnzone, sanfte Korrektur (siehe unten).
- `delta > tau_high`: kritische Zone, Alignment-Regler committet einen "human-simulated"-
  aehnlichen PIN-Schreibvorgang, der die betroffenen Regler-Werte auf ihre konfigurierten
  Ziel-Defaults zurueckzwingt (nutzt den BEREITS EXISTIERENDEN Human-Pin-Cooldown-
  Mechanismus aus `meta_regulator_tick` -- kein neuer Code fuer die Durchsetzung noetig,
  nur ein neuer Aufrufer).

**Rueckregulierung ohne Bruch (konkret, gedaempft statt hart):**

Ein gedaempfter Schritt (kein Sprung) auf den betroffenen Regler:

```
new_value = current_value + clamp(gain * (target_value - current_value), -max_step, max_step)
```

`gain` und `max_step` sind selbst Regler-Werte (in der bestehenden Tabelle), sodass der
User die Aggressivitaet der Rueckregulierung live einstellen kann -- das IST das
"kognitive Lego" fuer die Alignment-Staerke. Diese Formel ist eine direkte, ehrliche
Anwendung des bereits im Code vorhandenen `meta_regulator_tick`-Drift-Musters
(`new_temp = current_temp + (target - current_temp) * 0.3`), verallgemeinert auf einen
konfigurierbaren Gain statt einer festen 0.3-Konstante.

---

## 4. Reflex-Schicht (konkret, deterministisch, <500ms, ohne LLM)

Eine Reflex-Regel ist ein Paar (Trigger-Praedikat, Gegenmassnahme), beide rein
deterministisch, ausgewertet in jedem Takt VOR jedem LLM-Aufruf:

| Beispiel-Trigger (deterministisch pruefbar) | Beispiel-Gegenmassnahme (deterministisch, kein LLM) |
|---|---|
| `f.snapshot()` wirft eine Exception oder die Fabric-Datei ist nicht lesbar | Sofortiger Neustart-Versuch der lokalen Fabric-Verbindung; nach N Fehlversuchen: Alarm-Datei schreiben + konfiguriertes externes Alarm-Skript ausfuehren (z.B. eine Benachrichtigung an Gabriel) |
| `reflex_trigger_rate` (Abschnitt 3) ueberschreitet einen Schwellwert | Betroffene Node-Prozesse in `elastic_poll`-Standby versetzen (bereits real vorhandener Mechanismus, hier als Reflex-Gegenmassnahme wiederverwendet) |
| Ein extern definierter Sensor-Wert (z.B. ein Datei-basiertes Signal `/tmp/frankenstein_alarm_<typ>`, das ein SEPARATES, hier nicht spezifiziertes Sensor-System schreiben wuerde) liegt vor | Ausfuehrung eines vorkonfigurierten, deterministischen Shell-Skripts (z.B. Selbstabschaltung, Alarmierung) -- die REFLEX-SCHICHT selbst entscheidet nicht "was ist ein Feuer", sie reagiert nur auf ein bereits klassifiziertes Signal, das von einem separaten System kommen muesste |
| Freier Speicher unter einem Schwellwert (`/proc/meminfo` o.ae., real, billig pruefbar) | `release_idle_memory()` auf allen Standby-Knoten sofort ausloesen (bereits real vorhanden), unabhaengig vom regulaeren `elastic_poll`-Zyklus |
| Ein Prozess antwortet nicht mehr auf Heartbeat innerhalb der Lease-TTL | `runtime_reclaim_stale_claims()` + `elect_coordinator()`-Neuwahl (beide bereits real vorhanden und heute schon getestet) |

**Warum ohne LLM moeglich:** jede Gegenmassnahme ist eine feste, vorher konfigurierte
Aktion (Skript-Pfad, Fabric-Methode), kein generierter Text, keine Modell-Inferenz --
die Ausfuehrung selbst dauert im Bereich von Millisekunden (Dateisystem-Check,
Prozess-Signal, SQL-Transaktion), weit unter der 500ms-Taktzeit.

---

## 5. Claude-Code-Bruecke (konkret)

**Vektor-Format (Datenstruktur, kein erfundenes ML-Embedding):** ein strukturiertes
JSON-Paket, das ueber die bestehende Fabric transportiert wird (neue Tabelle
`claude_bridge_requests`, analog zu `outbox`, CAS-committed genau wie alles andere):

```json
{
  "schema": "CLAUDE_BRIDGE_REQUEST/v1",
  "request_id": "...",
  "priority_vector": {"urgency": 0.0-1.0, "complexity": 0.0-1.0, "user_facing": true/false},
  "context_digest": "sha256 des relevanten Fabric-Zustands",
  "payload": "die eigentliche Anfrage/Aufgabe in Text"
}
```

**Verhalten bei Claude-Code-Ausfall (konkret, kein Split-Brain):** die Schleife
(GRID10-Fabric + Node-Pool + Alignment-Regler + Reflex-Schicht) laeuft strukturell
UNABHAENGIG von Claude Code weiter -- sie ist heute schon so gebaut (kein Teil von
`grid10_fabric.py`/`grid10_node.py` ruft Claude Code auf). Die Claude-Bridge ist ein
OPT-IN-Aufrufer, kein Kernbestandteil des Taktzyklus. Faellt Claude Code aus, bleiben
`claude_bridge_requests`-Eintraege unbeantwortet liegen (sichtbar, nicht verloren) --
die Schleife selbst degradiert NICHT, sie verliert nur die Faehigkeit, komplexe
Anfragen an Claude Code zu delegieren; einfache/reflexive Funktionen (Reflex-Schicht,
Alignment-Regulierung, Node-Pool-Betrieb) laufen unveraendert weiter. Das ist die
konkrete Umsetzung von "die Schleife braucht Claude Code nicht zwingend zum
Weiterlaufen".

---

## 6. Web-UI "Kognitives Lego" (Anforderung, nicht Bestandsaufnahme)

- Liest/schreibt direkt die `regulators`-Tabelle (bereits reale API: `get_regulator`/
  `set_regulator`) -- kein neuer Backend-Layer noetig fuer die Kernfunktion, nur ein
  Web-Frontend, das die bestehende Fabric-SQLite-Datei liest/schreibt (ueber einen
  duennen HTTP-Wrapper, der die vorhandenen Fabric-Methoden aufruft).
- Profile = benannte Snapshots von Regler-Werten (neue Tabelle `regulator_profiles`,
  einfach: Name + JSON-Snapshot aller aktuellen Regler-Werte + Timestamp).
- "Zuruecksetzen" = `set_regulator` fuer jeden Regler auf den im Profil gespeicherten
  Wert, mit `writer="user-reset"`.
- Sichtbarkeit der kognitiven Schleife: Live-Anzeige der `tasks`/`scopes`/`leases`/
  `regulators`-Tabellen (Polling der Fabric-SQLite-Datei, kein neuer Event-Bus noetig
  fuer eine erste Version).

---

## 7. Betrieb: 72h autonomer Aufbau (siehe separates Script + Bauleiter-Konzept)

Siehe `research_entity/topic_packets/frankenstein-master-cognition-concept/BUILD_ORCHESTRATION_PLAN_20260827.json`
fuer den konkreten Umsetzungsplan (Backup-zuerst, Bauleiter-Kontinuitaet, Helfer-Pool,
Trainingslauf-Gate).

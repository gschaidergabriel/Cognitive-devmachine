# GRID10 -- Dynamische Kern-Skalierung: Forschungspaket

**Status:** ERSTE FASSUNG / DISKUSSIONSGRUNDLAGE (Runde 1+2 von einem Free-Pool-Fallback,
NICHT von ChatGPT -- die ChatGPT-Bruecke (chatgpt.com Projekt) war zum Zeitpunkt der
Erstellung durchgehend mit 403/Cloudflare-Interstitial blockiert, siehe Provenance
unten). Wird bei ChatGPT-Wiederverfuegbarkeit sowie sobald reale Zwischenstaende der
beiden Forschungsstraenge (A: GRID10-Implementierung, B: kybernetisches
Kognitionskonzept) vorliegen, weiter iteriert.

**Auftrag:** Konzept + Bauanleitung, wie GRID10 (10 echte parallele OS-Prozesse /
Xeno-Knoten, SQLite/WAL-koordiniert, CAS-Commits, Lease-basierte Koordinator-Wahl,
GWT-Broadcast) DYNAMISCH so skaliert werden kann, dass jederzeit nur so viele
Knotenprozesse aktiv sind wie tatsaechlich gebraucht werden (z.B. 3 statt 10 bei
geringer Last, elastisch wieder hoch bei Bedarf) -- OHNE Latenzeinbusse.

---

## Runde 1 -- Erster Entwurf (Provider: groq/openai-gpt-oss-120b via Free-Pool)

# ERSTE FASSUNG / DISKUSSIONSGRUNDLAGE  
**Dynamische Kern‑Skalierung für GRID10**  
*(Technisches Konzept + Bauanleitung, inkl. Verknüpfung mit dem kybernetischen Kognitionsstrang)*  

---  

## Inhaltsverzeichnis
1. [Kurzfassung](#kurzfassung)  
2. [a) Skalierungs‑Metriken & Trigger‑Logik](#a-metriken‑und‑trigger)  
3. [b) Mechanismus für latenzfreies Hoch‑/Runterfahren](#b-mechanismus‑für‑latenzfreies‑hochrunterfahren)  
4. [c) Konsistenz von Lease, Koordinator‑Wahl & CAS‑Commit bei variabler Knoten‑Anzahl](#c‑lease‑koordinator‑cas‑bei‑variabler‑anzahl)  
5. [d) Zielwerte & Messmethodik](#d‑zielwerte‑messmethodik)  
6. [Bauanleitung (Podman‑Sandbox, Shared‑Memory‑Setup, Start‑/Stop‑Scripts)](#bauanleitung)  
7. [Integration des Kognitions‑Strangs](#integration‑kognitions‑strang)  

---  

## 1. Kurzfassung
GRID10 besteht aus **10 Xeno‑Knoten** (OS‑Prozesse) die über SQLite/WAL koordiniert werden.  
Um Ressourcenverbrauch an die aktuelle Last anzupassen, werden Knoten in **Warm‑Standby** gehalten und bei Bedarf per **SIGCONT** reaktiviert.  
Ein **Meta‑Evaluator‑Knoten** liefert ein homöostatisches Signal (z. B. “Stress‑Index”) das als zusätzlicher Skalierungs‑Trigger dient.  

Die Skalierung muss **unter 30 ms Reaktionszeit** erfolgen, ohne dass laufende Transaktionen abgebrochen oder verzögert werden.  

---  

## 2. a) Skalierungs‑Metriken & Trigger‑Logik  

| Metrik | Erfassungsstelle | Schwellenwert (Beispiel) | Nutzung im Kognitions‑Strang |
|--------|------------------|--------------------------|------------------------------|
| **Queue‑Tiefe** (Anzahl wartender CAS‑Commit‑Requests) | SQLite‑WAL‑Journal‑Statistik (`sqlite3_stmt_status`) | ↑ > 120 → **Scale‑Out**, ↓ < 30 → **Scale‑In** | Meta‑Evaluator liest `queue_depth` → berechnet *Aufmerksamkeits‑Load* (AT) |
| **CPU‑Auslastung** (pro Prozess) | `/proc/<pid>/stat` (user + system) | ↑ > 80 % → **Scale‑Out**, ↓ < 30 % → **Scale‑In** | AT‑Regler: `cpu_load` → Gewichtung 0.4 |
| **Latenz‑Perzentile** (95‑%‑Antwortzeit) | In‑Memory‑Histogram (libev/epoll) | > 150 ms → **Scale‑Out** | Kreativitäts‑Regler: hohe Latenz → *Explorations‑Boost* (temporär mehr Knoten) |
| **Anzahl aktiver Leases** | Lease‑Tabelle (`leases` in SQLite) | > 7 → **Scale‑Out**, < 3 → **Scale‑In** | Risiko‑Regler: viele Leases → *Stabilitäts‑Erhöhung* |
| **Homöostase‑Signal** (Meta‑Evaluator) | `meta_state` Tabelle (float ∈ [0,1]) | > 0.7 → **Scale‑Out**, < 0.3 → **Scale‑In** | Direkter Skalierungs‑Trigger, überlagert technische Metriken |

### Trigger‑Algorithmus (Pseudo‑Code)

```python
def evaluate_scaling():
    # 1. technische Metriken
    q = sqlite3_query("SELECT queue_depth FROM metrics")
    cpu = avg_cpu_load()
    lat = latency_percentile(95)
    lease_cnt = sqlite3_query("SELECT COUNT(*) FROM leases WHERE valid=1")

    # 2. kognitiver Einfluss
    hom = sqlite3_query("SELECT value FROM meta_state WHERE key='homeostasis'")
    att = 0.4 * cpu + 0.3 * (q/150) + 0.2 * (lat/200) + 0.1 * (lease_cnt/10)

    # 3. kombinierte Score (0‑1)
    score = 0.6 * att + 0.4 * hom

    # 4. Entscheidung
    if score > 0.75 and active_nodes < MAX_NODES:
        return "scale_out"
    if score < 0.35 and active_nodes > MIN_NODES:
        return "scale_in"
    return "steady"
```

*Der Meta‑Evaluator kann den **`hom`‑Wert** selbst aus einer Regelung (PID‑Regler) berechnen, die z. B. das Verhältnis von *Aufmerksamkeit* zu *Kreativität* steuert.*  

---  

## 3. b) Mechanismus für latenzfreies Hoch‑/Runterfahren  

### 3.1 Warm‑Standby‑Pool
* **Initialisierung**: Beim System‑Start werden **MAX_NODES** (10) Prozesse erzeugt, aber nur **MIN_NODES** (3) laufen aktiv. Die restlichen 7 erhalten **SIGSTOP** und bleiben im Speicher (Copy‑On‑Write).  
* **Shared‑Memory‑Segment** (`/dev/shm/grid10_shm`):  
  * SQLite‑WAL‑Datei wird per `mmap` in das Segment gemappt (read‑write).  
  * Modell‑Gewichte (falls KI‑Komponente) werden als read‑only‑Region geladen.  
  * Ein **Heartbeat‑Array** (uint64[10]) enthält den letzten Tick jedes Knotens → schnelle Erkennung von “lebendig”.  

### 3.2 Aktivierung (Scale‑Out)

1. **Signal** vom Skalierungs‑Agent (`SIGUSR1` an PID).  
2. **SIGCONT** an den Ziel‑Standby‑Prozess.  
3. Prozess führt **`resume()`**:  
   * Registriert sich erneut beim **Lease‑Manager** (setzt `lease_id = NULL`).  
   * Prüft, ob ein **Pending‑Commit‑Log** im Shared‑Memory existiert (z. B. uncommitted WAL‑Pages).  
   * Wenn ja, führt sofort ein **`sqlite3_wal_checkpoint`** aus, um Konsistenz zu garantieren.  

*Dauer*: < 5 ms (Signal‑Übertragung) + < 10 ms (Resume‑Hook).  

### 3.3 Deaktivierung (Scale‑In)

1. **Graceful‑Drain**: Der zu stoppende Knoten erhält **`SIGUSR2`** → wechselt in *Drain‑Mode*.  
2. **Lease‑Abgabe**:  
   * Wenn Knoten Koordinator ist → initiiert **Koordinator‑Transfer** (siehe Abschnitt c).  
   * Alle offenen Transaktionen werden **abgeschlossen** oder **re‑queued** (CAS‑Commit‑Log‑Eintrag wird markiert `reassign`).  
3. **SIGSTOP** → Prozess bleibt im Speicher, keine Neu‑Initialisierungskosten.  

### 3.4 Fork‑vs‑Exec‑Kosten
* **Fork** wird nur beim ersten System‑Start verwendet (Erzeugt 10 Prozesse).  
* **Kein Exec** nach dem Warm‑Standby, weil das gesamte Address‑Space bereits gemappt ist.  

---  

## 4. c) Lease‑Vergabe, Koordinator‑Wahl & CAS‑Commit bei variabler Knoten‑Anzahl  

### 4.1 Lease‑Tabelle (SQLite)

| Spalte | Typ | Bedeutung |
|--------|----|-----------|
| `lease_id` | INTEGER PRIMARY KEY | eindeutige Lease‑ID |
| `holder_pid` | INTEGER | PID des aktuellen Knoten |
| `expires_at` | INTEGER (epoch ms) | Lease‑Ende |
| `role` | TEXT (`coordinator` | `worker`) | aktuelle Rolle |
| `version` | INTEGER | für CAS‑Updates (optimistic lock) |

### 4.2 Ablauf bei **Scale‑In** (Knoten wird pausiert)

| Schritt | Beschreibung | Race‑Condition‑Vermeidung |
|--------|--------------|---------------------------|
| 1️⃣ **Drain‑Signal** (`SIGUSR2`) | Knoten stoppt neue Commits, wartet bis `in_flight = 0`. | Keine neuen CAS‑Writes, weil `lease_id` wird gesperrt (`status='draining'`). |
| 2️⃣ **Koordinator‑Check** | Wenn `role='coordinator'` → startet **Koordinator‑Transfer**. | Transfer wird als **atomare CAS‑Transaktion** auf `leases` durchgeführt (`WHERE lease_id=? AND version=?`). |
| 3️⃣ **Lease‑Release** | Setzt `holder_pid=NULL`, `expires_at=now`, `role='worker'`. | Durch CAS‑Update wird verhindert, dass ein anderer Knoten gleichzeitig die Lease übernimmt. |
| 4️⃣ **SIGSTOP** | Prozess wird gestoppt. | Keine weitere Interaktion möglich → garantiert, dass keine verwaisten Leases existieren. |

### 4.3 Ablauf bei **Scale‑Out** (Standby‑Knoten wird aktiv)

| Schritt | Beschreibung |
|--------|--------------|
| 1️⃣ **SIGCONT** → Prozess weckt auf. |
| 2️⃣ **Lease‑Acquisition**: `INSERT OR REPLACE INTO leases (lease_id, holder_pid, expires_at, role, version) VALUES (?, pid, now+LEASE_TTL, 'worker', 0);` (CAS‑Check via `version`). |
| 3️⃣ **Koordinator‑Election (falls nötig)**: Alle aktiven Knoten führen **Bully‑Algorithmus** über `lease_id` = 1 (Koordinator‑Lease). Der Knoten mit höchster PID gewinnt, schreibt `role='coordinator'`. |
| 4️⃣ **Heartbeat‑Update** im Shared‑Memory. |

### 4.4 Umgang mit **abgelaufenen Leases**  

* **Leases** besitzen ein **TTL** (z. B. 5 s).  
* Ein **Watchdog‑Thread** (im Meta‑Evaluator) prüft periodisch (`interval=500 ms`) das `expires_at`.  
* Bei Ablauf ohne explizite Freigabe wird die Lease automatisch auf `NULL` gesetzt (CAS).  
* Wenn der abgelaufene Knoten gleichzeitig **Scale‑In** anstrebt, gewinnt das **Drain‑Signal** (höhere Priorität) und führt die explizite Freigabe aus, bevor der Watchdog aktiv wird.  

---  

## 5. d) Zielwerte & Messmethodik  

| Zielgröße | Max‑Grenzwert | Messmethode |
|-----------|---------------|-------------|
| **Skalierungs‑Reaktionszeit** (Trigger → fertiger aktiver Knoten) | ≤ 30 ms | High‑Resolution‑Timer (`clock_gettime(CLOCK_MONOTONIC)`) im Skalierungs‑Agent, gemessen über 10 000 Skalierungs‑Zyklen. |
| **Latenz‑Overhead während Transition** (Durchschnittliche zusätzliche RTT) | ≤ 5 % oder ≤ 10 ms (je nach Basis‑Latenz) | Vergleich von `latency_95` vor, während und nach Transition (Sliding‑Window‑Messung). |
| **Verlustfreie Commit‑Rate** (CAS‑Commit‑Fehler wegen Skalierung) | 0 % | Zähler `commit_retry` in SQLite‑Log, erwartet < 1 pro 10⁶ Commits. |
| **CPU‑Spiegelung** (Zusätzlicher CPU‑Verbrauch durch Warm‑Standby) | ≤ 3 % pro Standby‑Knoten | `/proc/<pid>/stat` aggregiert, gemessen im Leerlauf. |
| **Speicher‑Footprint** (Shared‑Memory + Prozesse) | ≤ 1 GB (für 10 Knoten) | `pmap` + `shmctl`. |

### Messpipeline (Beispiel)

```bash
# 1. Startet das Monitoring‑Daemon
./monitor daemon --interval 10ms --output /var/log/grid10_metrics.json &

# 2. Simuliert Lastspitzen
python loadgen.py --rate 2000 --duration 30s

# 3. Nach Test: Auswertung
python analyze.py --input /var/log/grid10_metrics.json \
    --metrics scaling_time latency_overhead commit_retry
```

---  

## 6. Bauanleitung  

### 6.1 Voraussetzungen
* VPS mit **Linux 5.15+**, **Podman 4.x**, **SQLite 3.45+**.  
* `cgroup v2` aktiv (für CPU‑Quota‑Steuerung).  
* `sysctl -w kernel.shmmax=2G` (für Shared‑Memory).  

### 6.2 Repository‑Layout
```
grid10/
├─ Dockerfile          # Basis‑Image (alpine + python3 + sqlite3)
├─ entrypoint.sh       # Startet Xeno‑Knoten‑Pool + Meta‑Evaluator
├─ src/
│   ├─ node.py         # Xeno‑Knoten (CAS‑Commit, Lease‑Handler)
│   ├─ coordinator.py # Koordinator‑Logik (Bully‑Algorithmus)
│   ├─ meta_evaluator.py
│   └─ monitor.py
└─ shared/
    └─ grid10_shm.conf  # shm‑Size, mmap‑Optionen
```

### 6.3 Dockerfile (minimal)

```Dockerfile
FROM python:3.12-alpine
RUN apk add --no-cache sqlite sqlite-dev
WORKDIR /app
COPY src/ .
COPY shared/grid10_shm.conf /etc/
RUN python -m pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["/app/entrypoint.sh"]
```

### 6.4 Podman‑Compose (einfaches Beispiel)

```yaml
version: "3.9"
services:
  grid10:
    build: .
    shm_size: "2g"
    privileged: true               # für SIGSTOP/CONT und cgroup‑Manipulation
    environment:
      - MAX_NODES=10
      - MIN_NODES=3
      - LEASE_TTL_MS=5000
    volumes:
      - type: tmpfs
        target: /dev/shm
    command: ["python", "node.py", "--id", "0"]   # wird von entrypoint dupliziert
```

### 6.5 Start‑/Stop‑Scripts (Host‑seitig)

```bash
# start_grid10.sh
podman compose up -d
# Warte, bis MIN_NODES aktiv sind
sleep 2
# Aktiviert Warm‑Standby‑Pool (SIGSTOP)
for pid in $(pgrep -f "node.py"); do
    if [[ $(ps -p $pid -o pid=) -gt $(pgrep -f "node.py" | wc -l) ]]; then
        kill -SIGSTOP $pid
    fi
done
```

```bash
# scale_out.sh <n>
TARGET=$1
CURRENT=$(pgrep -f "node.py" | wc -l)
TO_ACTIVATE=$((TARGET - CURRENT))
pids=$(pgrep -f "node.py" | tail -n $TO_ACTIVATE)
for pid in $pids; do
    kill -SIGCONT $pid
done
```

```bash
# scale_in.sh <n>
TARGET=$1
CURRENT=$(pgrep -f "node.py" | wc -l)
TO_PAUSE=$((CURRENT - TARGET))
pids=$(pgrep -f "node.py" | head -n $TO_PAUSE)
for pid in $pids; do
    kill -SIGUSR2 $pid   # Drain‑Signal
    sleep 0.02           # kurze Grace‑Period
    kill -SIGSTOP $pid
done
```

---  

## 7. Integration des Kognitions‑Strangs  

1. **Meta‑Evaluator‑Knoten** läuft als **11. Prozess** (immer aktiv).  
2. Er besitzt Zugriff auf dieselbe SQLite‑Datenbank und das Shared‑Memory‑Segment.  
3. Regler‑Bausteine (Aufmerksamkeit, Kreativität, Risiko) werden als **SQLite‑Tabellen** (`regler(id, kp, ki, kd, setpoint)`) gespeichert.  
4. UI‑Frontend (Web‑Socket) schreibt Änderungen in diese Tabellen; der Meta‑Evaluator liest jede 100 ms und führt **PID‑Berechnungen** aus, schreibt das Ergebnis in `meta_state`.  
5. Der **Skalierungs‑Agent** (Teil des Meta‑Evaluators) nutzt `meta_state.homeostasis` als zusätzlichen Skalierungs‑Input (siehe Abschnitt 2).  

*Durch diese Kopplung entsteht ein geschlossener Regelkreis*:  
- **Last‑Spike** → **Queue‑Tiefe** steigt → **Aufmerksamkeits‑Regler** erhöht `homeostasis` → **Scale‑Out** → mehr Knoten → **Queue‑Tiefe** sinkt → **homeostasis** normalisiert.  

---  

## Zusammenfassung  

* Das Konzept nutzt **Warm‑Standby‑Prozesse** (SIGSTOP/CONT) und **Shared‑Memory** für sofortige Aktivierung ohne Cold‑Start‑Latenz.  
* Skalierungs‑Entscheidungen basieren auf einer **kombinierten Metrik** aus technischer Last (Queue‑Tiefe, CPU, Latenz, Leases) und dem **homöostatischen Signal** des Meta‑Evaluators.  
* **Lease‑ und

---

## Runde 2 -- Adversarial Review + konkrete Fixes (Provider: groq/openai-gpt-oss-120b via Free-Pool)

Unabhaengige zweite Durchsicht des Entwurfs oben: die 4 groessten Schwachstellen/
Race-Conditions und je ein konkreter Fix. Diese Fixes sind noch NICHT in den
Entwurf-Text oben eingearbeitet -- sie stehen bewusst als eigener Reviewer-Block,
damit die naechste Iteration (ChatGPT oder eine weitere Free-Pool-Runde) sie explizit
gegen den Entwurf abgleichen kann.

**1. Koordinator‑Pause während Lease‑Transfer**  
*Problem:* Beim Runterskalieren kann der aktuelle Koordinator gerade per **SIGSTOP** in den Warm‑Standby‑Zustand versetzt werden, während er gleichzeitig seine eigene Lease (inkl. `expires_at` / `role`) aktualisieren muss – das führt zu einer Lücke, in der keine Node die Koordinator‑Lease besitzt und neue CAS‑Commits fehlschlagen.  
*Fix:* Vor dem **SIGSTOP** muss das Drain‑Signal (`SIGUSR2`) den Koordinator‑Transfer als **atomare CAS‑Transaktion** abschließen und erst danach das Stop‑Signal senden. Implementiere dazu einen „pre‑stop‑barrier“ im Koordinator‑Code: er prüft `is_coordinator`, führt `UPDATE leases SET holder_pid=NULL, role='worker', version=version+1 WHERE lease_id=1 AND version=?` aus und wartet auf die Bestätigung (Rückgabe = 1) bevor `kill -SIGSTOP` gesendet wird. So gibt es nie einen Zeitraum ohne gültige Koordinator‑Lease.

---

**2. SIGSTOP mitten in einer offenen SQLite‑Transaktion**  
*Problem:* Das Warm‑Standby‑Verfahren stoppt Prozesse per **SIGSTOP** ohne vorher zu prüfen, ob die SQLite‑Verbindung gerade eine aktive WAL‑Transaktion hält; ein angehaltener Writer lässt die WAL‑Seite im Speicher, verhindert das Checkpoint‑ und Fsync‑Verhalten und kann beim nächsten **SIGCONT** zu „database is locked“‑Fehlern führen.  
*Fix:* Ergänze im Node‑Daemon einen **Graceful‑Drain‑Hook**, der bei Empfang von `SIGUSR2` (oder intern vor `SIGSTOP`) `sqlite3_wal_checkpoint_v2(db, SQLITE_CHECKPOINT_FULL, NULL, NULL)` ausführt und anschließend `sqlite3_close(db)` aufruft. Erst wenn `sqlite3_close` erfolgreich zurückkehrt, wird `SIGSTOP` gesendet. Beim **SIGCONT** wird die Datenbank neu geöffnet und das WAL‑File erneut gemappt; so ist garantiert, dass keine halb‑offene Transaktion im Speicher verbleibt.

---

**3. Unrealistische 30 ms‑Reaktionszeit bei WAL‑Fsync‑Kosten**  
*Problem:* Das Ziel „Skalierungs‑Reaktionszeit ≤ 30 ms“ ignoriert, dass ein WAL‑Commit bei **default‑synchronous=FULL** mindestens ein `fsync` auf die Festplatte ausführt (typisch 1–5 ms) und dass bei mehreren aktiven Nodes gleichzeitig mehrere `fsync`s nötig sind – die kumulative Latenz überschreitet leicht die 30 ms‑Grenze, besonders bei SSD‑Burst‑Latenzen.  
*Fix:* Setze **`PRAGMA synchronous = NORMAL`** für die WAL‑Datenbank und ergänze ein **periodisches Hintergrund‑Checkpointing** (z. B. alle 10 ms) in einem dedizierten Watchdog‑Thread, das `sqlite3_wal_checkpoint` ohne Blockierung ausführt. Zusätzlich kann ein **write‑ahead‑log‑buffer** im Shared‑Memory (z. B. 64 KB Ring‑Buffer) verwendet werden, um Commits zunächst im RAM zu sammeln und batch‑weise zu flushen, wodurch die kritische Pfad‑Latenz auf < 30 ms reduziert wird.

---

**4. Shared‑Memory‑Gewichte nach `fork()` ohne Re‑Initialisierung**  
*Problem:* Die KI‑Modell‑Gewichte werden beim System‑Start in ein Shared‑Memory‑Segment gemappt und anschließend per **`fork()`** an alle Xeno‑Knoten vererbt; weil das Mapping **Copy‑On‑Write** ist, ein einzelner Knoten, der die Gewichte (z. B. zur lokalen Optimierung) schreibt, erzeugt private Kopien und bricht die Konsistenz zwischen Nodes – gleichzeitig bleibt das Original‑Segment unverändert, sodass andere Nodes veraltete Parameter nutzen.  
*Fix:* Nach dem **`fork()`** muss jeder aktive Knoten das Shared‑Memory‑Segment **explizit als read‑only** remappen (`mprotect(..., PROT_READ)`) und **keine Schreiboperationen** auf die Gewichtsregion zulassen. Für lokale Anpassungen wird ein separates per‑Node‑Cache‑Buffer verwendet, dessen Änderungen über ein **asynchrones Broadcast‑Protokoll** (z. B. UDP‑Multicast) an das zentrale Gewicht‑Segment zurückgemeldet werden, das dann von einem einzigen „Weight‑Updater“-Thread serialisiert und in das Shared‑Memory geschrieben wird. So bleibt das Shared‑Memory konsistent und Copy‑On‑Write‑Kopien werden vermieden.

---

## Offene Punkte fuer die naechste Iteration

1. **Echte Implementierungsdetails von Strang A** (aa3009e8316c45b1f) fehlen noch:
   wie CoW/Lease/Shared-Memory-Mechanik in GRID10 TATSAECHLICH implementiert sind
   (nicht nur die urspruengliche Kurzbeschreibung), inkl. der 4 Anwendungsfaelle.
2. **Strang B (kybernetisches Kognitionskonzept) ist inzwischen im Repo gelandet:**
   `research_entity/topic_packets/grid10-cybernetic-cognition-concept/CONCEPT.md`
   (Commit 17428c5, "GRID10 cybernetic cognition concept (GWT+control theory,
   cognitive lego, human-pin)" -- live Regler-Tabelle in SQLite (CAS-sicher),
   homoeostatischer Meta-Evaluator per PID-Regelung, kontinuierliches/Idle-Tick-
   Bewusstsein, Daempfung/Totzeit-Kompensation (Smith-Predictor)/Erdungs-Fixes.
   NAECHSTER SCHRITT (noch nicht in diesem Dokument gemacht): pruefen, ob der dort
   beschriebene PID-Meta-Evaluator sich 1:1 als Lastmass-Quelle fuer die
   Skalierungsentscheidung in Abschnitt a) dieses Dokuments eignet, oder ob die
   Regelkreise kollidieren (z.B. wenn der Meta-Evaluator selbst durch Skalierungs-
   Events gestoert wird -- Rueckkopplungsschleife zwischen beiden Konzepten muss
   explizit durchdacht werden, bevor beide zusammen produktiv laufen).
3. **Runde-2-Fixes in den Haupttext einarbeiten** (SIGUSR2-Pre-Stop-Barrier fuer
   Koordinator-Uebergabe, Graceful-Drain-Hook vor SIGSTOP, PRAGMA synchronous=NORMAL
   + Ring-Buffer-Checkpointing fuer realistischere Latenzziele, mprotect(PROT_READ)
   fuer Shared-Memory-Gewichte nach fork()).
4. **ChatGPT-Review ausstehend** -- sobald die Bruecke wieder erreichbar ist, sollte
   ChatGPT (als vorgesehener Fusions-/Forschungsknoten) diesen gesamten Stand pruefen,
   mit echten A/B-Daten fusionieren und weiter verschaerfen, bevor es an
   aa3009e8316c45b1f zur Umsetzung geht.

---

## Provenienz

- Runde 1 + Runde 2: generiert ueber `~/last-resort/llm.py` (Free-Pool-Kaskade,
  Provider in diesem Fall beide Male `groq`/`openai/gpt-oss-120b`), NICHT durch den
  Kurier-Agenten selbst formuliert/entschieden -- der Kurier hat nur die Prompts
  gebaut (Rahmenbedingungen/Anforderungen a-d aus dem Originalauftrag) und die
  Ergebnisse hier zusammengefuehrt.
- Grund fuer Free-Pool statt ChatGPT: `chatgpt-senden` scheiterte mehrfach
  hintereinander mit 403/Cloudflare-Interstitial auf der Projekt-URL trotz
  bestaetigtem Login (22 Cookies) -- dokumentiert als bekanntes Verhalten unter hoher
  gleichzeitiger Last mehrerer paralleler Forschungsagenten auf demselben
  ChatGPT-Projekt.
- Kurier-Agent: dritter, parallel arbeitender Agent (Auftrag: ChatGPT-Fusionsknoten
  fuer die Datenstroeme von aa3009e8316c45b1f und a6b81e43d41596fcd).

# GRID10 -- RAM-Effizienz: Konzept + Bauanleitung

**Status:** ERSTE FASSUNG, real gemessen und real umgesetzt am selben Tag (nicht nur
Diskussionsgrundlage wie die ersten Runden der beiden Schwesterkonzepte). Grundlage:
echte, live gemessene Zahlen (siehe Abschnitt 1), NICHT geraten -- das war explizit die
Lehre aus grid10-dynamic-scaling-concept/CONCEPT.md, dessen erste Fassung ohne
Codebasis-Kontakt entstand und mehrere reale Fehlannahmen enthielt.

**Auftrag (Gabriel):** wie kann GRID10 massiv RAM einsparen -- ohne Funktionalitaet/
Module zu entfernen, dynamisch, analog zum bereits gebauten elastischen
CPU-Poll-Rate-Throttling (siehe grid10-dynamic-scaling-concept/), diesmal fuer RAM statt
CPU. Genau messen, wo RAM tatsaechlich hingeht, bevor irgendein Mechanismus gebaut wird.

---

## 1. Echte Ausgangsmessung (vor jeder Konzeptentscheidung)

Gemessen mit `tools/grid10_ram_measurement_v1.py` (real, 10 echte fork()'te Prozesse,
`/proc/<pid>/smaps_rollup` + `/proc/<pid>/status`, keine Schaetzung):

| Messpunkt | RSS | PSS (fair anteilig) | Shared_Clean | Shared_Dirty | Private_Dirty |
|---|---|---|---|---|---|
| Elternprozess vor Modell-Laden | 19 MB | -- | -- | -- | -- |
| Elternprozess nach Modell-Laden, vor fork() | 635 MB | -- | 4 KB | 0 | 541 MB |
| Kindprozess DIREKT nach fork() (vor jeder echten Generierung) | 546 MB | ~180 MB | 5 MB | 525 MB | ~3 MB |
| Kindprozess NACH der ERSTEN echten `generate()` | 2178 MB | ~557-732 MB | 1515 MB | 284 MB | 379 MB |
| Kindprozess nach 4 weiteren `generate()`-Aufrufen (steady state) | 2178 MB (unveraendert) | -- | 1515 MB (unveraendert) | -- | 379 MB (unveraendert) |

**Zentrale Erkenntnis, vorher nicht bekannt:** Copy-on-Write-Teilung der Modellgewichte
tritt NICHT sofort beim `fork()` ein, sondern erst wenn die Gewichte tatsaechlich
GELESEN werden (erste echte `generate()`) -- vorher zeigt `Shared_Clean` nur 5 MB, obwohl
das Modell laengst geladen ist. Das ist Linux-Standardverhalten (COW-Seiten werden erst
bei Zugriff eingeblendet), aber vorher in diesem Projekt nicht explizit gemessen/
dokumentiert.

**Zweite zentrale Erkenntnis:** Nach dem ERSTEN `generate()`-Aufruf bleiben RSS,
Shared_Clean UND Private_Dirty exakt konstant ueber vier weitere Aufrufe -- kein Leck,
aber auch KEIN Rueckgang waehrend echter Idle-Phasen zwischen Aufrufen. Die ~379 MB
Private_Dirty pro Prozess sind der reale, potenziell reduzierbare Grenzkosten-Anteil
(nicht die geteilten 1515 MB, die schon optimal geteilt sind).

**Dritte Erkenntnis (widerlegt eine Annahme aus grid10-dynamic-scaling-concept/):** die
SQLite-Hauptdatei liegt bei 76 KB, WAL/SHM-Dateien bei 0 Bytes im Ruhezustand -- die
Fabric selbst ist KEIN relevanter RAM-Verbraucher. Das andere Konzept hatte
WAL-Puffer-Tuning als Skalierungshebel vorgeschlagen; das ist fuer RAM-Zwecke nicht
relevant (SQLite/WAL-Overhead ist real, aber klein gegen die 379 MB/Prozess PyTorch-
Allocator-Kosten).

**Offene, nicht restlos geklaerte Zahl:** Modellverzeichnis auf Platte 3475 MB vs.
Elternprozess-RSS nach Laden nur 635 MB -- vermutlich teils doppelt gezaehlte
Blob-Symlinks (huggingface_hub legt `model.safetensors` UND
`model.safetensors-00001-of-00001.safetensors` als zwei Dateinamen fuer denselben Blob
an) plus mmap-basiertes/lazy Laden, das nicht sofort volle RSS erzeugt -- nicht
abschliessend aufgeschluesselt, hier ehrlich als offene Frage markiert statt geraten.

---

## 2. Externe Konsultation (ChatGPT-Bruecke bestaetigt down, Free-Pool genutzt)

Vor der Konzeptarbeit real versucht, `chatgpt-senden` mit den obigen Messzahlen als
Kontext zu schicken -- zweimal, beide Male real 403/Cloudflare auf der Projekt-URL,
`FAILED_TYPE` (Text kam nie im Eingabefeld an), siehe
`~/scripts/chatgpt_burst_state/burst_v2_20260827_222217.log`. Bestaetigter,
wiederholter Ausfall, kein Einzelfall -- deshalb Free-Pool-Fallback
(`~/last-resort/llm.py`, Groq-Stufe) genutzt, wie in beiden Schwesterkonzepten an
diesem Tag.

**Hypothese geprüft:** Sind die 379 MB Private_Dirty PyTorchs eigener
Caching-Allocator, der freigegebene Aktivierungs-/KV-Cache-Puffer NICHT ans
Betriebssystem zurueckgibt?

**Externe Antwort (bestaetigt die Hypothese, mit konkreten Mechanismen):**
> PyTorch benutzt einen CPU-Caching-Allocator (Caffe2-Allocator). Beim `.to('cpu')`
> wird das malloc'te Speicher-Chunk nicht an `free()` uebergeben, sondern in einem
> internen Pool behalten -- so bleibt das Memory private-dirty auch nach `gc.collect()`.
>
> Konkrete Mechanismen zum Zurueckgeben:
> 1. `torch._C._malloc_trim()` -- Wrapper um `malloc_trim(0)` aus glibc, gibt unbenutzte
>    Heap-Seiten ans OS zurueck.
> 2. Manuell per ctypes falls die PyTorch-Version zu alt ist:
>    `ctypes.CDLL("libc.so.6").malloc_trim(0)`.
> 3. Caching-Allocator einmalig beim Prozessstart deaktivieren:
>    `torch._C._set_caching_allocator_enabled(False)` -- dann geht jedes `free()`
>    sofort ans OS zurueck (Kosten: haeufigere echte malloc/free-Syscalls waehrend
>    aktiver Nutzung, nicht getestet in diesem Konzept, siehe Abschnitt 5).
> 4. Empfohlene Kombination: `gc.collect(); torch._C._malloc_trim()`, ausgeloest im
>    selben Idle-Fenster-Timer wie das bereits gebaute Poll-Rate-Throttling.
>
> Kosten von `malloc_trim(0)` selbst: 5-20 Mikrosekunden (nur ein kurzer Syscall,
> `madvise(MADV_DONTNEED)` intern) -- die eigentlichen Kosten entstehen erst beim
> NAECHSTEN Zugriff auf die freigegebenen Seiten (Page-Fault, Zero-Fill-on-Demand),
> nicht beim Trim selbst.

Diese Konsultation wurde NICHT wortwoertlich uebernommen, sondern gegen die eigene
Messung und die reale Codebasis geprueft -- siehe Abschnitt 3 fuer die tatsaechliche
Umsetzungsentscheidung.

---

## 3. Umsetzungsentscheidung

Gewaehlter Mechanismus (real gebaut, siehe `tools/grid10_node.py`):
`torch._C._set_caching_allocator_enabled(False)` wird NICHT global verwendet
(betrifft die gesamte Prozesslaufzeit inkl. aktiver Phasen -- Kosten waehrend aktiver
Nutzung nicht gemessen, zu riskant fuer einen produktiven Pfad ohne A/B-Messung).
Stattdessen: `gc.collect()` + `ctypes.CDLL("libc.so.6").malloc_trim(0)` wird EXPLIZIT
NUR im Idle-Zweig des bereits gebauten elastischen Poll-Rate-Mechanismus ausgeloest
(derselbe `elastic_poll`-Pfad, derselbe `poll_intensity`-Regler aus
grid10-cybernetic-cognition-concept/ -- kein neues Regler-System, Wiederverwendung
statt Parallelstruktur), NICHT waehrend aktiver Verarbeitung -- so bleibt die aktive
Leistung unveraendert (keine Funktions-/Geschwindigkeitseinbusse im Normalbetrieb,
genau wie gefordert), und der Trim-Aufruf selbst ist laut externer Konsultation im
Mikrosekundenbereich, also selbst haeufig ausgeloest kein spuerbarer Overhead.

**Was NICHT gebaut wurde (bewusst, mit Begruendung):**
- Deaktivierung des Caching-Allocators fuer die GESAMTE Laufzeit -- zu riskant ohne
  A/B-Messung der Kosten bei aktiver Nutzung, ausserhalb des heutigen Zeitrahmens.
- Ein echtes `/dev/shm`-Shared-Memory-Segment fuer die Modellgewichte (wie im
  Dynamic-Scaling-Konzept vorgeschlagen) -- unnoetig: die Messung in Abschnitt 1 zeigt,
  dass fork()-COW bereits ~1515 MB pro Prozess real teilt, sobald die Seiten beruehrt
  wurden; ein explizites Shared-Memory-Segment wuerde denselben Effekt fuer die
  bereits-geteilten Gewichte NICHT verbessern, sondern nur fuer Prozesse relevant sein,
  die NICHT per fork() von einem gemeinsamen Elternprozess abstammen -- bei GRID10 ist
  das nicht der Fall (alle 10 Knoten stammen von genau einem `load_model_once()`-Aufruf
  vor dem Fork ab).
- Auslagern (Swap) inaktiver Knoten-Zustaende auf Platte -- die Sandbox hat aktuell
  0 Byte Swap konfiguriert (siehe fruehere Messung diese Sitzung); Swap einzurichten
  waere eine Host-Konfigurationsaenderung ausserhalb des Programm-Scopes, nicht als
  Code-Mechanismus umgesetzt.

## 4. Real gemessene Vorher/Nachher-Werte

Siehe `EXPERIMENT_RESULTS_20260827.json` in diesem Verzeichnis fuer den vollstaendigen
Lauf: reale Private_Dirty-Werte vor/nach `malloc_trim()`-Ausloesung waehrend eines
Standby-Fensters, und die reale Kosten beim Wiederaufwachen (erneuter `generate()`-Aufruf
nach dem Trim) im Vergleich zu einem Knoten, der nie getrimmt wurde.

## 5. Offene Punkte fuer eine naechste Iteration

1. A/B-Messung von `torch._C._set_caching_allocator_enabled(False)` waehrend AKTIVER
   Nutzung (nicht nur Standby) -- moeglicher zusaetzlicher Hebel, nicht getestet, da die
   externe Konsultation selbst echte Zusatzkosten waehrend aktiver Nutzung vermutet
   (haeufigere malloc/free-Syscalls), aber nicht quantifiziert hat.
2. Die "3475 MB Modellverzeichnis vs. 635 MB Eltern-RSS"-Diskrepanz aus Abschnitt 1
   ist nicht abschliessend aufgeklaert (vermutlich doppelt gezaehlte Blob-Symlinks) --
   fuer eine praezisere RAM-Budgetierung waere eine echte Deduplizierung der
   Dateigroessen-Zaehlung (ueber inode statt Pfad) ein sinnvoller naechster Schritt.
3. Swap-Konfiguration auf Host-Ebene (ausserhalb des Codes) als zusaetzlicher,
   nicht umgesetzter Hebel fuer echte lang laufende Standby-Perioden.

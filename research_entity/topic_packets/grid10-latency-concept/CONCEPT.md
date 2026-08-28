# GRID10 -- Latenz-Optimierung: Konzept + Bauanleitung

**Status:** ERSTE FASSUNG, real gemessen und real umgesetzt am selben Tag (vierter
Forschungsstrang neben cybernetic-cognition, dynamic-scaling, ram-efficiency).

**Auftrag (Gabriel):** wie senkt man die Latenz von GRID10 -- Modell-Decode wurde
frueher als Hauptengpass genannt (~2-6s CPU/Aufgabe), Tick-Dauer ~4s. Reale Ansaetze
durchdenken (kleineres/quantisiertes Modell, Speculative Decoding, Batching,
Caching, Parallelisierung), ChatGPT/Free-Pool erarbeiten lassen, dann real umsetzen
mit echten Vorher/Nachher-Messwerten.

---

## 1. Reale Ausgangsdaten (aus dieser Sitzung, nicht geraten)

- Modell-Decode pro kurzer Aufgabe (4-64 neue Tokens): 2-6 Sekunden CPU-Zeit.
- Ein voller Tick (5 parallele Aufgaben + 1 koordinierter Broadcast): ~4 Sekunden.
- Aggregierte Fabric-Transaktionsrate ueber 10 Prozesse: ~5/Sekunde.
- Sandbox: 4 vCPUs (AMD EPYC 9354P, aber nur 4 Kerne zugewiesen), CPU-only, kein GPU.
- **Bisher nie systematisch getestet:** jeder der 10 Knoten-Prozesse ruft
  `torch.set_num_threads(1)` explizit auf (tools/grid10_node.py::load_model_once) --
  jede einzelne Inferenz ist single-threaded, obwohl 4 Kerne verfuegbar sind.
  Vermutlich urspruenglich gewaehlt, um Oversubscription bei 10 gleichzeitigen
  Prozessen zu vermeiden, aber nie gegen Alternativen gemessen.
- Modell: Qwen3.5-0.8B (Josiefied-Checkpoint, huihui-ai-Variante), hybride Architektur
  mit nur 6 von 24 Layern als volle Attention, Rest linear-attention -- **0.8 Milliarden
  Parameter**, NICHT 10 Milliarden (Korrektur einer Fehlannahme aus der externen
  Konsultation unten, Abschnitt 2).

---

## 2. Externe Konsultation (ChatGPT bestaetigt down, Free-Pool genutzt)

Vierter real bestaetigter Ausfallversuch bei `chatgpt-senden` heute (403/Cloudflare
auf der Projekt-URL, FAILED_TYPE, Log:
`~/scripts/chatgpt_burst_state/burst_v2_20260827_224800.log`) -- Free-Pool-Fallback
(`~/last-resort/llm.py`, Groq-Stufe) genutzt, zwei Anfragen (Frage a+b, dann c+d+e+
Priorisierung).

**Wichtige Korrektur an der externen Antwort:** die Konsultation nannte an einer
Stelle "~10 Milliarden Parameter" und "~30GB RAM" fuer das Modell -- das ist FALSCH
fuer das tatsaechlich genutzte Qwen3.5-0.8B-Modell (0.8 Milliarden Parameter, real
gemessene ~635MB Elternprozess-RSS nach Laden, siehe grid10-ram-efficiency-concept/).
Die generelle Aussage zu INT8-Quantisierung (Speicher- und potenzieller
Geschwindigkeitsgewinn) bleibt gueltig, aber die konkreten Zahlen der Konsultation
wurden NICHT uebernommen, sondern durch die eigenen realen Messwerte ersetzt.

### (a) `torch.set_num_threads(1)` -- ist das optimal?

Externe Antwort, konkret und plausibel: bei typischerweise 3-5 gleichzeitig aktiven
Prozessen pro Tick (nicht alle 10 gleichzeitig im Decode-Schritt) bleiben bei
1-Thread/Prozess mehrere der 4 Kerne ungenutzt. Empfehlung: 2 Threads pro Prozess bei
<=4 gleichzeitig aktiven Prozessen nutzt die 4 vCPUs voll aus und reduziert
Context-Switch-Kosten -- erwarteter Latenzgewinn ~30-40% (z.B. 4s -> 2,5-3s pro
Tick), im besten Fall.

**Eingestuft als hoechste Prioritaet:** billig zu testen (eine Konstante aendern),
kein Genauigkeitsverlust, keine Architekturaenderung.

### (b) Quantisierung (INT8) fuer Routine-Ticks

Real bewertbarer Vorteil (KV-Cache-/Speicher-Reduktion), aber bei einem bereits
kleinen 0.8B-Modell ist der absolute RAM-Gewinn klein (siehe Korrektur oben) --
der Geschwindigkeits-Gewinn auf CPU ist NICHT automatisch garantiert (INT8-Kerne
auf CPU sind je nach BLAS-Backend nicht immer schneller als BF16, im Gegensatz zu
GPU-Tensor-Cores). **Eingestuft als mittlere Prioritaet, real zu messen, nicht
anzunehmen.**

### (c) Speculative Decoding

Externe Antwort, mit klarer Einschraenkung: lohnt sich laut Konsultation nur bei
>=30 Tokens pro Anfrage mit einem sehr leichten Draft-Modell -- bei den meisten
GRID10-Aufgaben (4-64 Tokens, oft nur 4-16) ist der Setup-/Synchronisations-Overhead
voraussichtlich groesser als der Gewinn. **Eingestuft als niedrige Prioritaet,
explizit NICHT umgesetzt in dieser Runde** -- korrekt vom externen Berater
identifiziert als schlechtes Aufwand-Nutzen-Verhaeltnis fuer diesen Anwendungsfall.

### (d) Batching mehrerer Knoten-Anfragen in einem `generate()`-Aufruf

Real erkanntes Architektur-Problem: GRID10s 10 Knoten sind unabhaengige, per fork()
isolierte OS-Prozesse (jeder mit eigenem Modell-Objekt im eigenen Adressraum) -- ein
echtes Batching UEBER Prozessgrenzen hinweg wuerde einen dedizierten
"Batch-Aggregator-Prozess" erfordern, der Anfragen ueber eine Queue sammelt und EINEN
gebuendelten `generate()`-Aufruf macht, statt dass jeder Knoten selbst decodiert --
das ist eine grundlegende Restrukturierung des Autonomie-Modells (jeder Knoten
beansprucht+decodiert+committet aktuell selbststaendig), kein kleiner Patch.
**Eingestuft als hohe potenzielle Wirkung, aber hoher Umsetzungsaufwand -- nicht in
dieser Runde umgesetzt, als groesseres Folgeprojekt vermerkt.**

### (e) Prefix-/KV-Cache-Wiederverwendung

Nicht separat von der externen Konsultation behandelt (Zeitbudget-Grenze der
Sitzung); eigene Einschaetzung: bei den kurzen (meist <50 Token), meist inhaltlich
unterschiedlichen Prompts in diesem System ist der absolute Gewinn durch
Prefix-Caching klein, selbst wenn Teile eines Prompt-Templates geteilt werden.
**Eingestuft als niedrige Prioritaet, nicht umgesetzt.**

---

## 3. Umsetzungsentscheidung

**Umgesetzt (diese Runde):** Ansatz (a), dynamische Thread-Zuweisung. Statt fest
`torch.set_num_threads(1)`, liest `load_model_once()` optional eine Umgebungsvariable
`GRID10_TORCH_THREADS` (Default weiterhin 1, um bestehende Aufrufer NICHT zu
beeinflussen) -- ein A/B-Vergleich (1 vs. 2 vs. 4 Threads/Prozess) wird real
gemessen, nicht angenommen, siehe `EXPERIMENT_RESULTS_20260827.json`.

**Nicht umgesetzt (mit Begruendung):**
- Quantisierung -- reale CPU-Geschwindigkeitsvorteile bei diesem kleinen Modell nicht
  garantiert, wuerde eine echte A/B-Genauigkeitsmessung brauchen (verglichen mit den
  bereits etablierten Antwortmustern aus fruehren Experimenten), Zeitbudget dieser
  Runde reicht dafuer nicht.
- Speculative Decoding -- vom externen Berater selbst als ungeeignet fuer diese
  kurzen Sequenzen eingestuft, nicht weiterverfolgt.
- Batching ueber Prozessgrenzen -- groessere Restrukturierung, als Folgeprojekt
  vermerkt, nicht in dieser Runde.
- Prefix-Caching -- geringer erwarteter Nutzen bei den kurzen, meist
  unterschiedlichen Prompts dieses Systems.

## 4. Real gemessene Vorher/Nachher-Werte

Siehe `EXPERIMENT_RESULTS_20260827.json` in diesem Verzeichnis.

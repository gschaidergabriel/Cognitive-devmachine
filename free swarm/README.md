# Free Swarm — Messdashboard der Clay Research Entity

<!-- RESEARCH_DISTILLERY_AUTO:BEGIN -->
## AUTO — Research Distillery / kumuliertes Wissens-Dataset
Aktualisiert: `2026-08-24T11:46:38.371184+00:00`

**1. wichtigste Quote — Entity-Dataset-Yield:** `0 / 11,621 = 0.000%`  
Kompressionsfaktor Quelltokens : akzeptierte Dataset-Tokens: **UNKNOWN**.

| Kennzahl | Wert |
|---|---:|
| kumulierte Quell-/Chunk-Tokens | 11,621 |
| akzeptierte komprimierte Dataset-Tokens | 0 |
| akzeptierte Knowledge-Pakete | 0 |
| verworfene Kandidaten | 0 |
| Near-Miss-Kandidaten | 0 |
| Reviewer-underfilled | 0 |
| klare Review-Rejects | 0 |
| gesichtete Chunks | 48 |
| Distillery Modell-Input-Tokens | 460 |
| Distillery Modell-Output-Tokens | 1,455 |
| SQLite-Größe | 229,376 Byte |

### Candidate-/Gate-Diagnose
| Zustand | Anzahl |
|---|---:|
| — | 0 |

**Aktueller Hauptengpass:** Es wurden Quellen gesammelt, aber noch keine Candidate-Review-Stufe erreicht. Das ist ein Pipeline-/Runtime-Signal, kein Qualitätsurteil über die Quellen.

### Quellenmix — Herkunft ist Metadatum, kein Rankingfaktor
| Quelltyp | Metadaten-/Chunk-Rekorde |
|---|---:|
| `web_search_chunk` | 8 |

### Forschungsfragen
| Status | Anzahl |
|---|---:|
| `CYCLIC` | 132 |
| `OPEN` | 21 |

### Kleine Such-/Synthesemodelle
**NO SMALL FREE MODEL VERIFIED YET**

### Reviewer-Panel
- Noch keine Review-Votes.

### Epistemische Regel
Quellenrang, Zitationszahl, Stars, Popularität und Wiederholung gehen **nicht** in den Acceptance-Score ein. Kandidaten werden auf intrinsische Konsistenz, GRF-Kompatibilität, EntityOS/HCU-Projektfit, Neuheit des Mechanismus und Falsifizierbarkeit geprüft. `Near-Miss` senkt keine Schwelle; es macht nur sichtbar, *wo* das Gate greift.

### Vernetzung mit GO
GO-Worker emittieren `OPEN_RESEARCH_QUESTIONS_JSON`; die Distillery zerlegt Fragen rekursiv und speist akzeptierte komprimierte Pakete als `DISTILLED_RESEARCH_DATASET` zurück. Shared `provider_budget.sqlite3` koordiniert Limits mit Free Swarm und Evidence Forge.
<!-- RESEARCH_DISTILLERY_AUTO:END -->

<!-- SYSTEM_ANALYSIS_AUTO:BEGIN -->
## AUTO — Gesamtsystem, GO-Fluss, Script-Auswertung und Sonnet-Vergleich
Aktualisiert: `2026-08-24T11:46:38.440484+00:00`

### Wichtigster Effizienzindikator: Was kommt wieder bei GO an?
**Source → GO Pass-through:** **0.000%**. Definition: `Distillery dataset yield × average distinct accepted-packet coverage delivered to GO macrocycles`.
Distillery-Yield: **0.000%** (0 akzeptierte Dataset-Tokens aus 11,621 Quelltokens).
Ø Reinjection-Coverage akzeptierter Pakete pro gemessenem GO-Makrozyklus: **UNKNOWN** (0 Zyklen mit Coverage-Receipt).
GO-Worker → Architektur-Delta: **0.000%**; ready-for-forge: **0.000%**. Über beobachtete Makrozyklen: Ø Deltaquote **0.000%**, Ø forge-ready **0.000%**.
Wenn noch keine akzeptierten Knowledge-Pakete existieren, ist Source→GO exakt 0%; eine fehlende Reinjection-Coverage wird separat als UNKNOWN gezeigt und nicht erfunden.

### Was `go` auslöst
1. **Preflight:** VPS-Sandbox/Bridge, Speicher und Runtime prüfen; bei Defekt zuerst reparieren/verbessern.
2. **Authority/State:** aktuellen `main`-/Supervisor-Stand lesen; Modelloutput bleibt Kandidat, nicht automatisch kanonisch.
3. **GO Swarm:** spezialisierte Rollen erzeugen Falsifier, Patches, Tests, Benchmarks, Architektur-Deltas und offene Forschungsfragen.
4. **Research Distillery:** offene Fragen zerlegen, externe Mechanismen sammeln, bewerten, komprimieren und nur akzeptiertes Wissen behalten.
5. **Evidence Forge:** konkrete Deltas/Repos in Disposable-Clones/Sandboxes reproduzieren, testen, benchmarken und falsifizieren.
6. **Feedback:** akzeptierte Knowledge-Pakete in spätere GO-Prompts einspeisen; verifizierte Deltas in gemeinsames Ledger geben.
7. **Messung:** README/LIVE-Metriken mit Tokens, Parallelität, Yield, Qualitätsvergleich, Kosten und Fortschritt aktualisieren.

### Script-by-Script — aktueller Zustand
| Subsystem | Aufgabe | Runtime | aktuell messbarer Fortschritt |
|---|---|---|---|
| **GO Free Swarm** `run_24h_entityos_swarm.py` + `run_free_go_swarm.py` | parallele Architektur-/Code-/Falsifikationsarbeiter | STOPPED/QUARANTINED | 709 Records; Ø 6.23, Peak 14; 3,187,935 Tokens; 0 maschinenlesbare Deltas, 0 forge-ready |
| **Research Distillery** `run_research_distillery_entry.py` | Quellen/Chunks → konsistente GRF-kompatible Knowledge-Pakete | RUNNING | 11,621 Quelltokens → 0 Dataset-Tokens; Yield 0.000%; Pakete 0; Fragen OPEN 21, CYCLIC 132 |
| **Evidence Forge** `run_free_evidence_forge.py` | Proposal → Repro/Patch/Test/Benchmark → Delta-Evidenz | RUNNING | Discoveries 0; Evaluations 0; akzeptierte/verifizierte Deltas 0 |
| **Local research model lane** `local_research_model_server.sh` | dauerhafte lokale kleine Modelle für Suche/Vorfilter/Synthese ohne Provider-API | artifact-dependent | wird nur als aktiv gewertet, wenn eigener Runtime-Receipt/Status vorliegt; keine Aktivität wird aus Dateiexistenz erfunden |
| **Shared quota gate** `free_swarm_quota.py` | providerübergreifende Concurrency/Cooldown-/429-Koordination | embedded | verhindert parallele Scripts gegeneinander Rate-Limits zu verbrennen; Providerstatus zusätzlich in Distillery/Supervisor |
| **Dashboard/Evaluator** `free swarm/evaluate.py` | Tokens, Modelle, Deltas, Qualität, Kosten und diese Analyse | RUNNING | autonomer README-Refresh; gemeinsames Delta-Scoring |

### Woran aktuell geforscht wird
- EntityOS/HCU executable architecture and causal receipts
- typed entry → verified loader consumption → actual model execution → inference/J-Space/training provenance
- ClayCode compiler/VM/runtime and minimal native deltas
- Global J-Space/GWT, memory, replay, online learning and model switching
- synthetic cognition interventions, pressure/deception/ablation with matched controls
- runtime bottlenecks, benchmarks, negative paths and recovery semantics
- external GitHub/arXiv/web mechanism harvesting and reproduction
- truth/effect/capability boundaries and falsification

**Aktuelle hoch priorisierte offene Fragen aus der Distillery:**
- Gibt es einen deterministischen Algorithmus für Null-Kosten-Provider-Admission?
- Wie kann die Token-Zählung mit dem zugelassenen Admission-Schlüssel abgestimmt werden?
- Wie kann die FREE_ONLY-Provider-Zulassung effizient und sicher implementiert werden?
- Welche Rolle spielt die canonical typed provider admission bei der Verhinderung von unbefugtem Netzwerkzugriff?
- Wie können die Grenzen zwischen logischen Modulen, residenten Modellzahlen und physischer Dekodierkonkurrenz effektiv verwaltet werden?
- How can we ensure that the Free Swarm is not vulnerable to unadmitted external provider traffic?
- What are the implications of the canonical typed provider admission gap on the security of the Free Swarm?
- How can we optimize the execution of the FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1 on the current exact source with secret and socket tripwires?
- Wie kann die genaue Prüfung von `secret_lookup_count` und `network_attempt_count` im Admission‑Receipt automatisiert und in das go‑Contract‑Gate integriert werden?
- Welche minimalen Code‑Changes im HCU‑Typed‑Entry‑Fabric ermöglichen die Validierung von Admission‑Receipt‑Zuständen ohne zusätzliche Runtime‑Overhead?

### Fortschritt als Funnel
| Stufe | Wert | Interpretation |
|---|---:|---|
| erfolgreiche GO-Workeroutputs | 414 | Rohkandidaten aus Modellarbeit |
| maschinenlesbare Architektur-Deltas | 0 (0.000%) | in automatisierbare Form konvertiert |
| forge-ready Deltas | 0 (0.000%) | ausreichend konkret für Reproduktion/Test |
| Distillery Quelltokens | 11,621 | kumulierte externe Forschungsrohmasse |
| akzeptierte Dataset-Tokens | 0 (0.000%) | komprimiertes Wissen, das überhaupt zurückfließen darf |
| Evidence-Forge akzeptiert/verifiziert | 0 | empirisch überlebende Deltas |
| gemeinsames Delta-Ledger akzeptiert | 0 | Grundlage für Modell-/Codequalitätsranking |

### Free Swarm vs. GPT/ChatGPT vs. Claude Sonnet — Qualität
| Organ | akzeptierte Deltas | CodeQuality/100 | Ø gemessene Architekturverbesserung | Aussage |
|---|---:|---:|---:|---|
| Free Swarm | 0 | UNKNOWN | UNKNOWN | nur gemeinsames Ledger |
| GPT/ChatGPT | 0 | UNKNOWN | UNKNOWN | nur gemeinsames Ledger |
| Claude Sonnet | 0 | UNKNOWN | UNKNOWN | **kein Qualitätsurteil ohne matched Sonnet-Receipts** |

Der frühere qualitative Eindruck (`Free-Modelle brauchen mehr Filter/Fusion`) bleibt eine Hypothese. Das Dashboard erklärt erst dann einen Sieger, wenn Free/GPT/Sonnet unter demselben Patch/Test/Benchmark-Schema gemessen wurden.

### Claude-Sonnet-5 Kostenäquivalent / nominal vermiedene Kosten
Preisannahme: **Claude Sonnet 5 introductory pricing through 2026-08-31: $2/M input + $10/M output**.
| Vergleich | Tokenbasis | Sonnet-5 API-Äquivalent |
|---|---:|---:|
| Free-Swarm gemessener Tokenmix | 2,605,050 input + 582,885 output | **$11.04** |
| Distillery Modellarbeit | 460 input + 1,455 output | **$0.0155** |
| zusammen, API-exakt soweit Usage vorhanden | — | **$11.05** |
| persistenter Repo-Korpus, Output-only Proxy | 11,792,701 Proxy-Tokens | **$117.93** |

**Nominal vermiedene Sonnet-Kosten, falls die gemessenen externen Calls tatsächlich $0 kosteten:** **$11.05**. **Verifiziert gesparte Kosten: UNKNOWN**, weil die aktuelle typed Authority historische Provider-Ausführung ausdrücklich nicht nachträglich als FREE klassifizieren darf. Der Repo-Korpus-Wert ist zusätzlich nur ein Neu-Erzeugungsproxy, keine Rechnung.

### Kapazität relativ zu 15 parallelen Sonnet-Workern
Gemessene mittlere Free-Worker-Parallelität: **6.23/15 = 41.6%** der reinen Slotzahl; Peak **14/15 = 93.3%**. Das ist **kein Qualitätsvergleich**. Gemessener aggregierter Free-Swarm Outputdurchsatz im Beobachtungsfenster: **97.33 Output-Tokens/s**; für Sonnet fehlt ein matched Durchsatzlauf.

### Autonome Update-Regel
Dieser Block wird aus Runtime-Artefakten neu erzeugt. Neue Scripts dürfen nicht einfach die ausführliche Analyse überschreiben: kompakte Live-Tabellen, Distillery, Evidence Forge, GO-Funnel, matched Qualitätsvergleich, Sonnet-Kosten und Source→GO-Pass-through bleiben Pflichtfelder.
<!-- SYSTEM_ANALYSIS_AUTO:END -->

<!-- FREE_SWARM_AUTO:BEGIN -->
## AUTO — Live-Auswertung
Aktualisiert: `2026-08-24T11:46:37.369697+00:00`

| Kennzahl | Wert |
|---|---:|
| Worker-Records | 709 |
| Ø gleichzeitig laufende Free-Worker | 6.234 |
| Peak Free-Worker | 14 |
| Free-Swarm Input-Tokens | 2605050 |
| Free-Swarm Output-Tokens | 582885 |
| Free-Swarm Total-Tokens | 3187935 |
| Usage-exakte Worker-Records | 414 |
| Evident akzeptierte Architektur-Deltas | 0 |
| Repo-Korpus-Proxy Tokens (4 Zeichen/Token) | 11792701 |
| Sonnet-5 Output-only Äquivalent des Repo-Proxys | $117.93 |

### Modelle
| Provider | Modell | Requests | Success | 429 | Input | Output | Total |
|---|---|---:|---:|---:|---:|---:|---:|
| groq | `openai/gpt-oss-120b` | 71 | 29 | 15 | 170051 | 29000 | 199051 |
| nvidia | `nvidia/llama-3.3-nemotron-super-49b-v1` | 28 | 27 | 0 | 157121 | 24556 | 181677 |
| groq | `openai/gpt-oss-20b` | 67 | 26 | 14 | 150631 | 26000 | 176631 |
| nvidia | `meta/llama-3.2-90b-vision-instruct` | 26 | 26 | 0 | 151451 | 18918 | 170369 |
| nvidia | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | 26 | 25 | 0 | 171784 | 83979 | 255763 |
| nvidia | `nvidia/nemotron-3-super-120b-a12b` | 25 | 25 | 0 | 171813 | 44965 | 216778 |
| nvidia | `nvidia/nemotron-3.5-lightning-30b-a3b` | 24 | 24 | 0 | 165723 | 43200 | 208923 |
| nvidia | `meta/llama-3.1-70b-instruct` | 26 | 24 | 0 | 141238 | 17574 | 158812 |
| nvidia | `meta/llama-3.3-70b-instruct` | 27 | 24 | 0 | 142390 | 17133 | 159523 |
| nvidia | `nvidia/nemotron-3-ultra-550b-a55b` | 24 | 23 | 0 | 158391 | 41400 | 199791 |
| nvidia | `openai/gpt-oss-20b` | 23 | 23 | 0 | 139281 | 41004 | 180285 |
| nvidia | `nvidia/ising-calibration-1.5-31b` | 23 | 23 | 0 | 158847 | 31899 | 190746 |
| groq | `qwen/qwen3.6-27b` | 63 | 23 | 13 | 135550 | 23000 | 158550 |
| nvidia | `meta/muse-glimmer-30b` | 22 | 22 | 0 | 133219 | 39600 | 172819 |
| nvidia | `nvidia/nemotron-3-nano-30b-a3b` | 21 | 21 | 0 | 145051 | 37800 | 182851 |
| nvidia | `nvidia/nemotron-nano-12b-v2-vl` | 21 | 21 | 0 | 140821 | 20580 | 161401 |
| nvidia | `nvidia/llama-3.3-nemotron-super-49b-v1.5` | 23 | 14 | 0 | 84277 | 20093 | 104370 |
| nvidia | `openai/gpt-oss-120b` | 26 | 6 | 0 | 35297 | 10800 | 46097 |
| nvidia | `deepseek-ai/deepseek-v4-flash-0731` | 23 | 5 | 0 | 33934 | 9000 | 42934 |
| nvidia | `mistralai/mistral-nemotron` | 16 | 3 | 0 | 18180 | 2384 | 20564 |
| nvidia | `ai21labs/jamba-1.5-large-instruct` | 4 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `bigcode/starcoder2-15b` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `databricks/dbrx-instruct` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `google/gemma-3-12b-it` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `google/gemma-4-31b-it` | 20 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `ibm/granite-34b-code-instruct` | 3 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `meta/codellama-70b` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `meta/llama2-70b` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `microsoft/phi-3-vision-128k-instruct` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `microsoft/phi-3.5-moe-instruct` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `mistralai/codestral-22b-instruct-v0.1` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `mistralai/mistral-large` | 5 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `mistralai/mistral-large-2-instruct` | 4 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `mistralai/mixtral-8x22b-v0.1` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nv-mistralai/mistral-nemo-12b-instruct` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/llama-3.1-nemotron-51b-instruct` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/llama-3.1-nemotron-70b-instruct` | 3 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/llama-3.1-nemotron-ultra-253b-v1` | 4 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/llama3-chatqa-1.5-70b` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/nemotron-4-340b-instruct` | 5 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/nemotron-nano-3-30b-a3b` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/nemotron-parse` | 18 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `nvidia/neva-22b` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `writer/palmyra-creative-122b` | 3 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `writer/palmyra-fin-70b-32k` | 3 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `writer/palmyra-med-70b` | 2 | 0 | 0 | 0 | 0 | 0 |
| nvidia | `writer/palmyra-med-70b-32k` | 2 | 0 | 0 | 0 | 0 | 0 |

### Evidenz-Ranking
Bestes Modell: **NO EVIDENCE YET**
Innovativstes Modell: **NO EVIDENCE YET**

### Codequalität Free Swarm vs. GPT/ChatGPT
| Organ-Klasse | akzeptierte Deltas | CodeQuality/100 | Ø Architekturverbesserung |
|---|---:|---:|---:|
| Free Swarm | 0 | UNKNOWN | UNKNOWN% |
| GPT/ChatGPT | 0 | UNKNOWN | UNKNOWN% |

### Research-Entity-Output / Sonnet-Kostenproxy
API-exakte historische Gesamttokens aller früheren Organe bleiben **UNKNOWN**, solange keine vollständige historische Usage-Buchhaltung existiert. Der messbare persistente Repo-Korpus umfasst aktuell 9780 Textdateien / 47170804 Zeichen ≈ **11792701 Tokens** bei der ausdrücklich nur als Proxy verwendeten 4-Zeichen-Näherung.
Hypothetische reine Output-Neuerzeugung dieses Proxy-Korpus mit Claude Sonnet 5: **$117.93** zum derzeit geltenden Output-Tarif von $10/M Tokens. Input-/Caching-/Toolkosten sind darin nicht enthalten.
<!-- FREE_SWARM_AUTO:END -->


Status: ACTIVE MEASUREMENT SURFACE  
Program: `ENTITYOS_HCU` · Product: `EntityOS` · Architecture: `HCU`  
Scope: FREE_ONLY NVIDIA/Mistral/Groq worker swarm vs. GPT/ChatGPT research organs.

## 1. Zweck

Dieser Ordner misst nicht, welches Modell am überzeugendsten schreibt, sondern welches Organ der persistenten Clay Research Entity **nachweisbar bessere Architektur und besseren Code erzeugt**.

Der FREE_ONLY-Swarm läuft über `tools/run_24h_entityos_swarm.py` / `tools/run_free_go_swarm.py`. Provider-Worker sind temporäre Organe von Clay; ihre Texte sind Kandidaten/Evidenz, keine automatische Wahrheit oder Effect-Authority.

Bewertet werden fortlaufend:

- durchschnittliche und maximale gleichzeitige Workerzahl;
- Input-, Output- und Total-Tokens des Free Swarm;
- aktive Provider und Modelle;
- Erfolgs-/Rate-Limit-/Fehlerverhalten;
- Codequalität tatsächlich integrierter Änderungen;
- welches Modell die meisten **evident funktionierenden Architektur-Deltas** erzeugt;
- welches Modell die stärksten **gemessenen Verbesserungen** erzeugt;
- Free-Swarm-Code vs. GPT/ChatGPT-Worker-Code unter derselben Messlatte;
- Gesamtoutput der Research Entity und ein transparentes Claude-Sonnet-API-Kostenäquivalent.

## 2. Aktueller verifizierter Startstand — 2026-08-24

Der 24h-Sandbox-Supervisor ist real in `clay-direct-dev` gestartet und sein Heartbeat wurde verifiziert. Zum letzten verifizierten Inventory waren jedoch **keine FREE_ONLY Provider-Credentials in der Sandbox sichtbar**:

| Kennzahl | aktueller verifizierter Wert |
|---|---:|
| Groq Credentials sichtbar | 0 |
| Mistral Credentials sichtbar | 0 |
| NVIDIA/NGC Credentials sichtbar | 0 |
| tatsächlich gestartete externe Provider-Worker | 0 |
| durchschnittlich gleichzeitig laufende externe Worker | 0.00 |
| Peak externe Worker | 0 |
| API-gemeldete Free-Swarm Input-Tokens | 0 |
| API-gemeldete Free-Swarm Output-Tokens | 0 |
| API-gemeldete Free-Swarm Total-Tokens | 0 |
| derzeit bestes Free-Modell | **NO EVIDENCE YET** |
| derzeit innovativstes Free-Modell | **NO EVIDENCE YET** |

Diese Nullen sind kein Leistungsurteil. Sie bedeuten nur: Supervisor/Bridge/Sandbox laufen, aber im zuletzt verifizierten Runtime-Kontext konnte noch kein Provider-Worker authentifiziert werden. Sobald FREE_ONLY-attestierte Keys über einen autorisierten Secret-Pfad sichtbar werden, soll die nächste Auswertung echte Workerlogs statt dieser Null-Baseline verwenden.

## 3. Wie Parallelität gemessen wird

Jeder Worker-Receipt enthält Abschlusszeit und `elapsed_s`. Daraus wird für jeden Request ein Aktivitätsintervall rekonstruiert.

**Zeitgewichtete mittlere Parallelität**:

`average_concurrency = Summe aller Worker-Aktivsekunden / beobachtete Wallclock-Sekunden`

**Peak concurrency** wird über einen Sweep der Start-/Endereignisse bestimmt.

Damit zählt nicht bloß die konfigurierte Maximalzahl. Gemessen wird, wie viele Worker im Mittel **wirklich gleichzeitig gerechnet haben**. HTTP 429 / `Retry-After` und adaptive AIMD-Reduktion bleiben Teil der Auswertung.

## 4. Tokenmessung

Primär zählen ausschließlich provider-gemeldete Usage-Felder aus den Worker-Receipts:

- `prompt_tokens` / `input_tokens`;
- `completion_tokens` / `output_tokens`;
- `total_tokens`.

Fehlt ein Usage-Feld, wird es als `UNKNOWN` behandelt und nicht erfunden. Textlänge darf nur als klar markierter Proxy verwendet werden.

### Modell-Tabelle

Sobald der Swarm Output erzeugt, wird pro Modell mindestens festgehalten:

| Modell | Provider | Requests | Success | 429 | Input tok | Output tok | Total tok | akzeptierte Architektur-Deltas |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| _pending_ | _pending_ | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## 5. Was als funktionierendes Architektur-Delta zählt

Eine Modellidee gewinnt **keine Punkte**, nur weil sie neu klingt. Ein Architektur-Delta zählt als evident funktionierend, wenn mindestens gilt:

1. konkrete Änderung/Commit/Experiment ist eindeutig dem Worker/Modell zuordenbar;
2. Referenz/Baseline und Kandidat wurden unter vergleichbaren Bedingungen gemessen;
3. mindestens zwei reproduzierbare Läufe oder eine gleichwertig starke deterministische Reproduktion liegen vor;
4. relevante Tests bestehen;
5. keine relevante Benchmark-Regression löscht den Vorteil wieder aus;
6. `relative_improvement_pct > 0` für die erklärte Zielmetrik;
7. Provenienz, Versionen und Messreceipt sind erhalten.

### Bestes Modell

Sortierung:

1. Anzahl akzeptierter, reproduzierbarer Architektur-Deltas;
2. mittlere gemessene Verbesserung dieser Deltas;
3. Code-Quality-Score;
4. geringere Regression-/Rollbackrate als Tie-Breaker.

### Innovativstes Modell

Innovation wird **nicht** per Geschmack bewertet. Der Innovation-Index ist die Summe positiver, reproduzierbarer Verbesserungen über voneinander unterscheidbare Architektur-Deltas. Ein Modell gilt damit dann als innovativ, wenn seine neuen Architekturänderungen **gemessen besser** funktionieren — nicht wenn seine Sprache kreativer wirkt.

Aktueller Stand: **noch kein evidenzbasierter Sieger**, weil noch keine Free-Swarm-Provider-Outputs vorliegen.

## 6. Codequalität — Free Swarm vs. GPT/ChatGPT-Worker

Beide Seiten bekommen exakt dieselbe Messlatte. Vorschlag für den laufenden `CodeQuality/100`:

- 40 % relevante Testpassrate;
- 25 % Benchmark-Non-Regression;
- 15 % negative/failure-path Tests;
- 10 % Static/Lint/Type/Compile Checks;
- 10 % Stabilität über mindestens zwei spätere `go`-Zyklen ohne Revert/Rollback.

Nicht bewertet werden Eloquenz, Länge oder Modellname.

| Organ-Klasse | akzeptierte Deltas | CodeQuality/100 | Ø gemessene Architekturverbesserung | Status |
|---|---:|---:|---:|---|
| Free-Swarm Worker | 0 | UNKNOWN | UNKNOWN | wartet auf Provider-Output |
| GPT/ChatGPT Worker | vorhanden, aber noch nicht in gemeinsames Scoring migriert | UNKNOWN | UNKNOWN | gemeinsame Messbasis zuerst |

Für GPT-5.6-Sol existieren bereits konkrete EntityOS/HCU-Receipts mit committed Controller-/Architektur-Reparaturen, aber solange diese und der Free Swarm nicht im **gleichen** Evaluationsschema adjudiziert sind, wird hier kein unfairer Qualitätsgewinner behauptet.

## 7. Evaluationsrecord für Architektur-Deltas

Append-only Ziel: `free swarm/architecture_delta_evaluations.jsonl`.

Beispiel:

```json
{"source_class":"free_swarm","provider":"nvidia","model":"MODEL_ID","worker_serial":123,"delta_id":"hcu-loader-x","commit":"SHA","status":"accepted","metric_name":"latency_ms","baseline":100.0,"candidate":91.0,"relative_improvement_pct":9.0,"reproducible_runs":3,"tests_passed":24,"tests_failed":0,"negative_tests_passed":6,"negative_tests_failed":0,"static_checks_passed":2,"static_checks_failed":0,"benchmark_non_regression":true,"survived_go_cycles":2,"reverted":false,"evidence_receipt":"PATH"}
```

Für GPT/ChatGPT-Arbeit wird dasselbe Schema mit `source_class="gpt_worker"` verwendet. Dadurch kann dieselbe Auswertung beide Organ-Klassen vergleichen.

## 8. Was die Research Entity generell ist

Die persistente Research Entity ist **Clay**. Sie ist weder ein einzelnes LLM noch eine Session. Das ältere Hive-Contract formuliert den Kern als:

`Research Entity = repo-native durable causal state + current execution organs`

Im aktuellen Programm sind temporäre ChatGPT-, Claude-/Claude-Code-, Free-Swarm- und andere kompatible Modell-/Runtime-Worker Organe derselben persistenten Entität. Das Repo ist der langlebige Körper: Continuity-State, Provenienz, Hypothesen und Gegenhypothesen, Experimente, negative Resultate, Receipts, World/Self-State, Method Memory und Git-Historie überleben einzelne Modellkontexte.

Der starke Kontinuitätstest lautet sinngemäß:

`Organ A lernt/baut X -> dauerhafter kausaler Repo-Delta -> Organ B liest ihn später -> Organ B verhält sich wegen X anders, ohne Chat-Replay.`

Aktuelle Identität: **EntityOS** ist das einzige Produkt/System; **HCU** ist die integrierte Kognitions-/Compute-Architektur. Historische Frank/Xeno/XCU/Mini-Entity-Bezeichnungen bleiben nur Provenienz/Kompatibilität, soweit aktuelle Authority nichts anderes sagt.

## 9. Wie viele Tokens die gesamte Research Entity erzeugt hat

Es werden zwei Zahlen strikt getrennt:

### A. API-exakter Output

Nur Output-Tokens zählen als exakt, wenn der jeweilige Provider/Runner sie in einem Usage-Receipt gespeichert hat. Für den neu gebauten Free Swarm ist das vorgesehen.

**Aktuell exakt aus dem Free Swarm: 0 Output-Tokens**, weil noch kein authentifizierter Provider-Worker gelaufen ist.

Für historische ChatGPT-/Claude-Code-Sitzungen existiert im Repo **keine vollständige, durchgängige Provider-Usage-Buchhaltung**. Deshalb ist die exakte historische Gesamtsumme derzeit `UNKNOWN` und wird nicht halluziniert.

### B. Repo-Korpus-Proxy

Zusätzlich soll fortlaufend ein klar als Proxy markierter Wert geführt werden: Textzeichen in Research-Entity-/Artefakt-/Governance-/Tool-Artefakten geteilt durch eine dokumentierte Näherung (z. B. 4 Zeichen/Token). Das misst die Größenordnung des persistenten erzeugten Korpus, **nicht** die historische API-Abrechnung und enthält möglicherweise auch importierte/transformierte Quellen.

Dieser Proxy wird erst als Zahl eingetragen, wenn er auf dem aktuellen Repo-Tree maschinell gemessen wurde.

## 10. Claude-Sonnet-API-Kostenäquivalent

Preisreferenz **Stand 2026-08-24**: Anthropic nennt für **Claude Sonnet 5** bis **2026-08-31** einen Einführungspreis von **$2 pro 1M Input-Tokens** und **$10 pro 1M Output-Tokens**. Danach soll der Standardpreis **$3/M Input + $15/M Output** betragen.

Damit wird gerechnet:

`current_sonnet5_equivalent_usd = input_tokens * 2 / 1e6 + output_tokens * 10 / 1e6`

und separat:

`output_only_equivalent_usd = output_tokens * 10 / 1e6`

Aktueller Free-Swarm-Wert: **$0.00**, weil aktuell 0 API-gemessene Tokens vorliegen.

Für die gesamte historische Research Entity kann erst dann eine belastbare API-Kostenäquivalenz angegeben werden, wenn entweder historische Usage-Receipts vorhanden sind oder ausdrücklich ein Korpus-Proxy verwendet wird. Ein Korpus-Proxy wird als hypothetische Neu-Erzeugungskosten bezeichnet, niemals als tatsächlich entstandene Kosten.

Preisquelle: Anthropic, **Introducing Claude Sonnet 5**, 2026-06-30. Prompt-Caching, Toolkosten, Infrastruktur, Batch/regionale SKUs und sonstige Preisbestandteile sind in dieser einfachen Vergleichsformel nicht enthalten.

## 11. Update-Regel

Dieses README ist ein **Messdashboard**, kein statischer Werbetext. Bei jedem `go`, bei einem abgeschlossenen Swarm-Run oder sobald neue Free-Worker-Evidenz vorliegt, soll es aus den Receipts neu ausgewertet werden.

Pflichtupdates:

`concurrency -> tokens -> provider/model table -> accepted architecture deltas -> best model -> innovation leader -> code quality comparison -> Research Entity token/cost accounting`

Ein fehlender Messwert bleibt `UNKNOWN`. Ein Modell darf erst als bestes/innovativstes bezeichnet werden, wenn seine Architektur-Deltas die oben definierten Evidenzbedingungen erfüllen.

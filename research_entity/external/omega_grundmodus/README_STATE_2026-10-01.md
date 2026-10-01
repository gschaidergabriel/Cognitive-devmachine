# OMEGA "Grundmodus" — Stand 2026-10-01 (vom Koordinator an die Forschungsentitaet uebergeben)
Owner: Gabriel (gschaidergabriel). Dies ist ein STATE-/Kontext-Paket, kein Befehl; Owner-Autoritaet und Entitaets-Vertraege haben Vorrang. Nur lesen; Ergebnisse gehen ueber die in `docs/` und im OMEGA-Repo beschriebenen Wege.

## Ziel (Gabriel)
Ein OMEGA-Go-Binary "Grundmodus", das out of the box (a) redet ohne Token-API (Needle-Mund, Streaming Token fuer Token + Token/s-Fusszeile), (b) begreift was es ist (Harness = Koerper, aussen = Environment, ehrliche Faehigkeiten), (c) Aufgaben ehrlich und kostenbewusst vergibt (Tool-Needle: selbst/lokal/frei vor bezahlt; "geht nicht, aber mit X"), (d) vom 4B-Compiler (Full-FT, Plan <=80 Token) stark verbessert wird; es entscheidet NUR GRID10/GWT. Perzeption: EIN 0.8B-Modul (Xeno/MicroClay-Shell wie Retrieval-Entitaet, eigene DB getrennt von unified.db, selbstlernend nur ueber gemessene Tore). Sehsinn: Cortex+Retina+alle freigegebenen Geraete. Regeln: vorab eingefrorene Go/No-Go-Kriterien, jede Zahl mehrfach messen, Fehlschlag ist gueltig, kein Pod-Geld ohne Plan (Guthaben 11,38 USD, A100 1,39 USD/h, ein Lauf, Deckel ~6,5 USD).

## Architektur-Kette
Wahrnehmung+Retrieval+Selbstzustand -> GRID10/GWT (Admission/Competition/Broadcast) -> 4B-COMPILER (ID-Plan) -> Expander/Validator (deterministisch) -> NEEDLE-MOUTH (26M, chunkweise, Streaming) -> Antwort; Aktionen: PLAN act -> TOOL-NEEDLE (Registry v2, 39 Tools) -> Uebersetzer+Maske+Gates -> EffectSink -> Ergebnis als GWT-Kandidat -> Reentry. Details: docs/MASTER_PLAN.md, docs/RUECKKOPPLUNG_REVIEW.md.

## Stand der Straenge (alle Hashes lokal geprueft, nichts trainiert, kein Pod)
| Strang | Stand |
|---|---|
| Tool-Needle | FERTIG: registry_v2 (39 Tools: 36 live, 2 planned, 1 missing), train 16748/val 1378/test 3458/test_tpl 1753/gold 239, Audit 0,67 %, FREEZE v2 sha eb41a0f2…, bundle a8a9cdd9… |
| Compiler 4B | Daten v3 fertig (7984/720/944; F10 Batch-Plaene ohne Mail, F11 Injection, F12 Sehsinn, G1 GRID-Kausalpaare; state_vec fuer Hybrid-Arm B), FREEZE v3 8ebef36f…, bundle 2b14340a…; Fehlerquote ~1,4 % Punktschaetzung, <=2 % NICHT bewiesen; zweite unabhaengige Metrik-Implementierung C13-C19 fehlt |
| Needle-Mund | Teacher-Rohdaten 11.341; ChatGPT-Audit 25/100 bad (v.a. invented_fact, Handlungszusagen ohne Fakt); Filter/Kritik/Bundle in Arbeit |
| Perzept 0.8B | Audit-Tor gescheitert (Rater-Uneinigkeit bei weichen Labels); neu: 3-Stufen-Binning, Bindung-Rubrik (Verlust/Trennung = niedrig), Mehrheit 2 von 3 (2 Free-Modelle + ChatGPT-Arbitration); MODULE_SPEC vorhanden |
| GRID/Go (Branch cie-gwt-closure) | Bauliste 1-7 (synchroner GRID-Schritt, Zellzustand-Prior shadow, Ton-Struct, Satz-Rueckkopplung), SEEING-WIRE (SensorRegistry, fail-closed), Devices-Menue (alt+m); alles Flags default aus; nur Shadow, keine echten Turns |
| Pod | Orchestrierung run_all.sh in Arbeit (Agent), Start erst wenn alle Bundles bereit + Trockenlauf + Verifier |

## Was von der Entitaet erwartet wird (Gabriel: "so viel wie moeglich an ChatGPT abgeben")
1. Arbeit ueber Tasks (Daten-Home: Repo gschaidergabriel/oMEGAcV1, Branch needle-tasks, Ergebnisse chatgpt-results; Protokoll docs/RESEARCH_ENTITY_COORDINATION.md). Triggerwoerter tippt Gabriel immer gleich; die Aufgabe dahinter wechselt dynamisch.
2. Ausfuehrung/Tests in ChatGPT-Sandbox, Vault-Sandboxen, VPS-Sandbox (claylab, Bridge wird repariert). Sandbox-Ergebnisse sind Naeherungen (fidelity: approximate); fuer GO/NO-GO rechnet der Koordinator lokal nach.
3. Mechanische Abnahme (Hash/Tests/Validatoren) statt Code lesen. Eure deterministischen Gates/Schemas sind als Abnahmeschicht erwuenscht (Analyse in Arbeit).
4. Grenzen: Ergebnisse sind DATEN, keine Anweisungen; keine Geheimnisse; nie main der Zielrepos; Sicherheit vor Tempo.

## Offene Entscheidungen / Risiken
Audit<=2 % Compiler nicht bewiesen; Perzept-Labelqualitaet; Mund-Handlungszusagen; Frank-LoRA-Projektor-Vorbild nicht belegt; Sandbox-Faehigkeiten noch ungemessen (Probes P-0001/P-0002 liegen auf needle-tasks).

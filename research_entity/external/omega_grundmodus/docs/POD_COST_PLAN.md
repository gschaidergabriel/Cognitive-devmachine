# POD_COST_PLAN — Budget 11,38 USD (RunPod, Stand 01.10.), Ziel: so wenig wie moeglich verbrauchen

Regel: Jede Pod-Minute ist Geld. Alles, was lokal geprueft werden kann, wird lokal geprueft. Auf dem Pod laeuft nur, was getestet ist.

## Preise (USD/h, 01.10.): RTX 3090 0,22 (community) | RTX 4090 0,34-0,74 | A40 0,35-0,49 | L40S 0,79-1,09 | A100 80GB 1,19-1,59 | H100 1,99+

## Aufwandsabschaetzung (grob, VOR der Messung; Ueberschlag 6*N*Tokens, ehrlich als Schaetzung)
- Needle-Mund (26M): ~4,5e7 Tokens (50k Beispiele x ~300 Tok x 3 Epochen) = ~7e15 FLOPs -> auf 4090/3090 Minuten. Pro Seed < 0,10 USD. 3 Seeds + Eval < 0,60 USD.
- 4B-Compiler Full-FT (alle Parameter, AdamW8bit, GradCheckpointing, Peak ~28 GB laut frueherem Lauf): ~10k Beispiele x ~900 Tok x 2-3 Epochen = 1.8-2.7e7 Tokens -> ~5e17-9e17 FLOPs: ~1-2 h A100 (~1,3-3,2 USD) oder ~2-3,5 h L40S (~1,6-3,8 USD). Kontextlaenge cappen (Eingabe <=~600 Tok), 2 Epochen als Default, Early-Stop bei Val-Plateau.
- Setup/Download/Eval-Overhead ~0,5-1 USD. Erwartung gesamt ~4-5 USD, Reserve ~6 USD fuer Fehlversuch oder 2. Compiler-Seed (Gabriel entscheidet).

## Kostenhebel (verbindlich im Bundle umsetzen)
1. EIN Pod, EINE Sitzung: erst Needle (alle Seeds), dann Compiler, dann Eval. Kein Neustart dazwischen. GPU-Wahl: kleinste, die den Compiler tragbar fasst (A100 80GB oder L40S 48GB; Vergleich Preis/Durchsatz am ersten Schritt messen, nicht annehmen).
2. VOR dem Pod: vollstaendiger lokaler Trockenlauf aller Skripte mit Mini-Daten und Mini-Modell (Datenladen, Tokenisierung, Loss-Maske, 2 Optimierungsschritte, Checkpoint schreiben+laden, Eval-Skript auf 20 Beispielen, GGUF-Konvertierungsskript Trockenlauf). Skripte syntaktisch/Abhaengigkeiten pruefen (pip --dry-run, python -m py_compile). Jeder Fehler auf dem Pod kostet Geld.
3. Schnelle Pfade installieren: fuer Qwen3.5 (Hybrid, lineare Attention) `flash-linear-attention` und `causal-conv1d` im Setup, sonst faellt es auf den langsamen Torch-Pfad zurueck (Warnung lokal gesehen: 'fast path is not available') = 2-3x laenger. Flash-Attention fuer die vollen Attention-Layer. bf16, Packing/Laengen-Bucketing, Loss nur auf Plan-Tokens.
4. Gewichte/Daten: Basismodell auf dem Pod per HF laden (schneller als Upload von hier), Daten/Bundle als .tgz hochladen (klein). Kein Network-Volume (Speicherkosten), nur Container-Disk.
5. Checkpoint alle N Schritte + Resume-Faehigkeit; harte Zeitgrenze im run_pod.sh (MAX_MINUTES) mit Selbst-Stopp.
6. Selbstabschaltung: run_pod.sh beendet am Ende den Pod selbst ueber die RunPod-API (Schluessel NUR als Umgebungsvariable zur Laufzeit, nie in Dateien), UND der Koordinator ueberwacht von aussen und stoppt notfalls. Watchdog: wenn nach T Minuten kein Fortschritt (Logzeilen), Abbruch.
7. Eval auf dem Pod nur so weit, wie es billiger ist als lokal (Batch-Generierung der Testbeispiele ~10-15 min); schwere/mehrfache Auswertung danach lokal mit den heruntergeladenen Ergebnissen. Checkpoints (8 GB) nur einmal herunterladen.
8. Keine Probelaeufe auf dem Pod: erster Pod-Schritt ist bereits der echte Lauf; Smoke-Pruefung (30 Sekunden, 5 Schritte) am Anfang, dann durchlaufen.
9. Mitschreiben: Start/Ende, GPU, Preis/h, Verbrauch in USD (RunPod-API Guthaben vorher/nachher) in POD_LOG.md.

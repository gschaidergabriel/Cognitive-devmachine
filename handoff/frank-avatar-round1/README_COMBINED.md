# COMBINED_HANDOFF — FranKenstein Avatar, Runde 1 + Baselines/Zielbilder

Dieses Paket bündelt zwei Dinge, die zusammen gehören, damit ChatGPT/Codex
auf dem VPS ohne Rückfrage weiterarbeiten kann:

## 1. `ROUND1_EXPORT_<UTC>/` — der reale Ist-Stand (diese Runde, frisch erzeugt)

Vollständiger, geprüfter Export der WIRKLICH laufenden Avatar-App. **Lies
zuerst `ROUND1_EXPORT_<UTC>/README_FIRST.md`, dann
`ROUND1_EXPORT_<UTC>/ACTIVE_RUNTIME_MAP.md`.**

Kernbefund: nicht `frankenstein-repo` (das ist unabhängige GRID10-Forschung),
sondern `buehne_daemon.py` + `buehne.html` unter
`/home/ai-core-node/.claude/star/visual/` (kein Git-Repo, systemd-User-Unit
`frankenstein-buehne.service`, Port 8788) ist die live gezeigte "FranKenstein
-- live" Seite mit Mosaikgesicht, Zuschauerzähler und Chat-Panel.

## 2. Alles andere — die bereits vorhandenen Baselines und Zielbilder aus der
   `FRANK_CLAUDE_HANDOFF_GUIDE_V2`-ZIP (Gabriels eigene Vorarbeit, unverändert
   übernommen, NICHT von dieser Runde erzeugt)

- `BASELINES/BASELINE_PROTOCOL.md` + `BASELINES/dream_target_metrics.json` —
  die C0-C6 Prüfkriterien (Registrierung, Optical-Flow, Lippensynchronität,
  Frame-Pacing, Hintergrundschleifen, Mosaik-Kantenschärfe, Soak-Test). Das
  sind die "Baselines die erreicht werden müssen".
- `MOCKUPS/` (5 Bilder) + `TARGET_VISUALS/` (6 Bilder, siehe
  `TARGET_VISUALS/README.md`) — die "Beispielbilder"/Zielansichten:
  Standardfenster, Vollbild, 12-Beat-Storyboard, Layer-Architektur,
  aktuelle Fehler (MOCKUPS) sowie haptisches Interface, cleanes Vollbild,
  unheimlicher AI-Filmlook, 12-Frame-Mikroperformance, 300-Frame-
  Hintergrundmatrix, Gesichtsfilter-Stufen (TARGET_VISUALS).
- `CONTRACTS/` — maschinenlesbare Layout-/Animationsverträge (JSON).
- `CODE_REFERENCE/` — TypeScript-Zustands-/Feder-/Layer-Invarianten-
  Referenzcode.
- `QA/ACCEPTANCE_TESTS.md` — harte Abnahmetests.
- `ARCHITECTURE/`, `STORYBOARD/`, `RESEARCH/`, `ANALYSIS/`, `WORKERS/`,
  `SOURCE/`, `PROMPTS/` — Zielarchitektur, Bewegungsablauf, empirische
  Herleitung, Frame-Forensik des aktuellen fehlerhaften Clips,
  Worker-Lane-Plan, Originalbelege, alle vier Prompt-Stufen
  (`01_CLAUDE_FIRST_HANDOFF_ONLY.txt` = dieser Rundenauftrag,
  `02_MASTER_ITERATIVE_BUILD_PROMPT.txt`, `03_GO_PROTOCOL.txt`,
  `04_CLAUDE_DREAM_TARGET_BUILD.txt` = die NÄCHSTEN Runden, noch nicht
  ausgeführt).
- `GUIDE_*` Dateien: die Original-README/Delivery-Report/Manifest/Inventory/
  Checksummen aus der Gabriel-ZIP selbst, umbenannt statt überschrieben,
  damit nichts mit den Runde-1-Dateien gleichen Namens kollidiert.

## Reihenfolge für den nächsten Bearbeiter (Codex/ChatGPT)

1. `ROUND1_EXPORT_<UTC>/README_FIRST.md` + `ACTIVE_RUNTIME_MAP.md` — welches
   System real läuft, wie bewiesen.
2. `BASELINES/BASELINE_PROTOCOL.md` — welche Messwerte erreicht werden
   müssen, bevor irgendetwas als "fertig" gilt.
3. `TARGET_VISUALS/` + `MOCKUPS/` — wie es aussehen soll.
4. `CONTRACTS/` + `CODE_REFERENCE/` — wie es technisch gebaut werden soll.
5. `PROMPTS/02_MASTER_ITERATIVE_BUILD_PROMPT.txt` und
   `PROMPTS/03_GO_PROTOCOL.txt` — der eigentliche Bauauftrag, NACHDEM Gabriel
   das hier geprüft und "GO" gesagt hat. Nicht vorher anfangen zu bauen.

Diese Runde selbst hat laut Auftrag NICHTS an Animation/Layout/Architektur
geändert — reiner Export/Diagnose/Verpackung.

# README_FIRST.md — FranKenstein Avatar Handoff, Runde 1

**Lies zuerst `ACTIVE_RUNTIME_MAP.md`.** Kernbefund dieser Runde: die
Annahme aus `PROMPTS/01_CLAUDE_FIRST_HANDOFF_ONLY.txt`
("erwarteter Kandidat ist `/home/ai-core-node/frankenstein-repo`") war
FALSCH. `frankenstein-repo` ist ein separates, unabhängiges Repo für
GRID10-Kognitionsforschung (Commits wie "4B-Abstraktionsschicht",
"Goldtest", "TypedEntry") und enthält KEINEN Avatar-Code.

Die real laufende Avatar-App:
- Prozess: `buehne_daemon.py`, PID zur Aufnahmezeit 544719, systemd-User-Unit
  `frankenstein-buehne.service`, Port 127.0.0.1:8788.
- Verzeichnis: `/home/ai-core-node/.claude/star/visual/` — **kein Git-Repo**.
- Frontend: `buehne.html` (Vanilla HTML/CSS/JS) + `filmlook.js`.
- Bewiesen per HTML-Titel (`<title>FranKenstein -- live</title>`), Screenshot
  (mosaikartiges Gesicht, "1 Zuschauer", CHAT-Panel — exakt das von Gabriel
  beschriebene Referenzbild) und systemd/Prozess-Forensik. Alle Belege in
  `ACTIVE_RUNTIME_MAP.md` und `evidence/`.

## Was in diesem Paket steckt

- `ACTIVE_RUNTIME_MAP.md` — die zentrale Feststellung (welches Repo/Prozess
  ist live, wie bewiesen).
- `RUNBOOK.md` — Start/Stop/Test-Befehle, mit ✅/⚠️/❌ pro Schritt markiert.
- `INVENTORY.csv` — 5.270 Zeilen: jede Datei unter dem Buehnen-Verzeichnis,
  mit sha256/Größe/Mime/PNG-Maßen/Alphakanal/aktiv-oder-nicht.
- `SHA256SUMS.txt` — Prüfsummen für alles, was tatsächlich in `source/` und
  `assets/` mitgeliefert wird.
- `source/` — der Server- und Frontend-Code selbst (16 Dateien).
- `assets/` — NUR die 1.340 tatsächlich vom Server ausgelieferten Bilder
  (656 MB) aus 10 aktiven Verzeichnissen. Die 3.904 unbenutzten
  experimentellen Varianten (relief/tiefe/esrgan/ai/proxy/parallax-Ordner,
  insgesamt mehrere GB) sind bewusst NICHT mitkopiert, aber vollständig in
  `INVENTORY.csv` (Spalte `runtime_status=inactive/experimental`) mit
  Pfad+Hash dokumentiert — Pointer statt totem Gewicht, wie vom Auftrag
  für Großdateien vorgesehen.
- `configs/.env.example`, `services/frankenstein-buehne.service`,
  `schema/buehne_lokal.db.schema.sql` — Redeploy-Bausteine, keine Secrets
  (es gibt keine — geprüft, siehe `RUNBOOK.md` Abschnitt 3).
- `evidence/` — Rohbelege: Umgebung, laufende Prozesse, Screenshots (Standard
  746×449 + Vollbild 1680×1050), DOM-Dump des Live-Layerstapels, Chrome-Logs.
- `git/NOTAM.txt` — warum es keinen `git/HEAD.txt` etc. für die Avatar-App
  gibt (kein Repo), plus Kontrast-Info zum unabhängigen `frankenstein-repo`.
- `HANDOFF_READY.json` — maschinenlesbarer Statusbericht dieser Runde.

## Was NICHT in diesem Paket steckt (bewusst)

- Kein Video-Mitschnitt der Animation (nicht erzeugt, siehe `RUNBOOK.md` §7).
- Keine `requestAnimationFrame`/Performance-Messung (kein Instrumentierungs-
  pfad im Code vorhanden — "nicht messbar" statt erfunden).
- Keine Layout-/Animations-/Architekturänderung — diese Runde ist reiner
  Export, wie von `PROMPTS/01` vorgeschrieben.
- Keine privaten Chat-Inhalte aus `buehne_lokal.db` (nur Schema).

## Zusammen mit den Baselines/Zielbildern aus der V2-Guide-ZIP

Dieses Rundenergebnis liegt NICHT isoliert — es wurde zusammengepackt mit
den bereits mitgelieferten Ziel-/Prüfkriterien aus
`FRANK_CLAUDE_HANDOFF_GUIDE_V2` (BASELINES/C0-C6, MOCKUPS/, TARGET_VISUALS/,
CONTRACTS/, QA/ACCEPTANCE_TESTS.md, CODE_REFERENCE/) — siehe
`../COMBINED_HANDOFF_<UTC>/` im übergeordneten `artifacts/handoff/`-Ordner
für das zusammengeführte Gesamtpaket, das an ChatGPT/Codex weitergegeben
wird.

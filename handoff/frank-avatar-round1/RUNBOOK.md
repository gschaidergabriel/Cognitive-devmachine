# RUNBOOK.md — Start/Stop/Reproduktion der FranKenstein Buehne

Alle Befehle unten wurden auf der real laufenden Maschine geprüft (getestet
= ✅), soweit ohne Risiko für den laufenden Prozess möglich. Ungetestete
Schritte (z.B. "auf sauberer Maschine von Null") sind ausdrücklich als
UNGETESTET markiert.

## 1. Woraus die App besteht

- Server: `source/buehne_daemon.py` — Python-Stdlib, kein Framework, keine
  externen pip-Pakete außer Standardbibliothek (`sqlite3`, `http.server`,
  `threading`, `subprocess`, `socket`, `signal`, `urllib.parse`, `json`, `io`,
  `os`, `sys`, `time`). ✅ geprüft per `grep "^import\|^from" source/buehne_daemon.py`.
- Frontend: `source/buehne.html` (Vanilla HTML/CSS/JS), `source/filmlook.js`
  (separater globaler Look, wird vom Server unter `/filmlook.js` ausgeliefert).
- Zustand: `source/zustand.json` (eine Datei — "an"/"quelle"/"ts", KEIN Secret).
- Lokale Chat-DB: eigene SQLite `buehne_lokal.db` (Schema unter `schema/`,
  KEINE Chat-Inhalte mitgeliefert — Datenschutz/Redaction, siehe Prompt-Regel).
- Read-only Zugriff auf `unified.db` (Pfad kommt aus Env-Var `UDB_DB_PATH`,
  NIE beschrieben, nur gelesen).
- Assets: `assets/<verzeichnis>/...` — nur die aktiv per Route ausgelieferten
  Verzeichnisse (siehe `ACTIVE_RUNTIME_MAP.md` Abschnitt 8). ✅ 1.340 Dateien,
  656 MB, vollständig kopiert und hashverglichen (`SHA256SUMS.txt`).

## 2. Installation auf sauberer Maschine — ⚠️ UNGETESTET

```bash
# Python 3.10+ reicht (nur Stdlib). Kein venv nötig für buehne_daemon.py
# selbst. venv_ai/ (394 MB, NICHT mitgeliefert) wird nur von den
# Offline-Build-Skripten (tiefe_bauen.py, detail_bauen.py, gesichtsfilter.py)
# gebraucht, NICHT vom Live-Server -- diese Skripte laufen nicht im
# Live-Pfad, siehe ACTIVE_RUNTIME_MAP.md Abschnitt 8.
mkdir -p /pfad/zu/visual
cp -r source/* assets/* /pfad/zu/visual/
cd /pfad/zu/visual
# zustand.json muss existieren, sonst startet die Chrome-Fenster-Schleife
# nicht wie erwartet (Datei ist im Paket enthalten, keine Secrets drin).
```

## 3. Konfiguration ohne Geheimnisse — ✅ verifiziert, keine Secrets im Code

Siehe `configs/.env.example`. Kein einziger der im Code gefundenen
`os.environ.get(...)`-Aufrufe (grep-Beleg:
`evidence/environment` bzw. direkt in `source/buehne_daemon.py` Zeile 138,
151, 193 und `source/blick.py` Zeile 103-105) liest einen API-Schlüssel,
ein Passwort oder einen Token. Es gibt nichts zu redigieren außer den
Pfad-Konstanten selbst (die sind selbst schon relativ/generisch).

```bash
export UDB_DB_PATH=/pfad/zu/unified.db   # nur LESEND geöffnet
export BUEHNE_PORT=8788                   # optional, Default 8788
```

## 4. DB-Erstellung/Migration — ✅ Schema geprüft

```bash
sqlite3 buehne_lokal.db < schema/buehne_lokal.db.schema.sql
```
Erzeugt die leere `chat`-Tabelle (id, ts, wer, text, art) neu. Keine
Migration nötig — ein einziges `CREATE TABLE IF NOT EXISTS` im Server selbst
(idempotent, läuft bei jedem Start mit).

## 5. Start/Stop/Restart — ✅ geprüft (laufender Dienst, read-only befragt)

Produktiv läuft das über systemd (user-Unit), NICHT manuell:
```bash
systemctl --user status frankenstein-buehne.service   # ✅ aktuell: running
systemctl --user restart frankenstein-buehne.service   # UNGETESTET in dieser Runde (kein Neustart des Live-Diensts -- Rundenregel: keine Aenderung/kein Risiko)
systemctl --user stop frankenstein-buehne.service       # UNGETESTET, gleicher Grund
```
Unit-Datei mitgeliefert: `services/frankenstein-buehne.service`
(Quelle: `~/.config/systemd/user/frankenstein-buehne.service`).

Manueller Start (für eine Kopie, NICHT gegen den Live-Port 8788 laufen
lassen, sonst Portkonflikt):
```bash
BUEHNE_PORT=8799 python3 source/buehne_daemon.py
```
UNGETESTET in dieser Runde (Rundenregel: "kein Refactoring, kein kleiner Fix
nebenbei" — ein zweiter Testlauf auf einem Nebenport wurde bewusst nicht
gestartet, um die laufende Chrome-Fenster-Übernahmelogik nicht doppelt
auszulösen).

## 6. Standard- und Vollbildansicht aufrufen — ✅ geprüft, diese Runde

```bash
curl -s http://127.0.0.1:8788/ | head -c 200      # ✅ HTTP 200, siehe evidence/environment/http_root_headers.txt
google-chrome --headless=new --no-sandbox --disable-gpu \
  --window-size=746,449  --screenshot=standard.png   http://127.0.0.1:8788/
google-chrome --headless=new --no-sandbox --disable-gpu \
  --window-size=1680,1050 --screenshot=fullscreen.png http://127.0.0.1:8788/
```
Beide ✅ ausgeführt, Ergebnis: `evidence/screenshots/standard_746x449.png`,
`evidence/screenshots/fullscreen_1680x1050.png`.

## 7. Testlauf / Screenshot / Video / Logsammlung

- Screenshots: ✅ wie oben (Abschnitt 6).
- DOM-Dump des Layerstapels: ✅ `evidence/runtime/dom_dump.html`
  (`google-chrome --headless=new --dump-dom`).
- Konsole/Netzwerk-Fehler: ⚠️ TEILWEISE — Chrome-Headless-Logdatei
  (`evidence/logs/chrome_headless_*.log`) auf `ERROR|Exception|Failed`
  durchsucht, keine Treffer außer bekanntem GCM/TensorFlow-Rauschen
  (irrelevant, Chrome-interne Telemetrie). Ein echter DevTools-Protocol-
  Konsolen-Stream (`console-api` Events) wurde in dieser Runde NICHT
  aufgezeichnet — als offener Punkt vermerkt, nicht als "0 Fehler" behauptet.
- Video (30-60s Animation): ❌ NICHT erzeugt in dieser Runde. Kein
  Bildschirm-/Frame-Aufnahmewerkzeug in der verfügbaren Zeit sicher
  verkabelt, ohne den laufenden Chrome-Kioskprozess zu stören. Klar als
  `missing` in `HANDOFF_READY.json` gelistet.
- `requestAnimationFrame`-Statistik/Long-Tasks/Memory: ❌ NICHT gemessen —
  kein vorhandener Instrumentierungspfad im Code, laut Auftrag "nicht
  messbar" dokumentieren statt erfinden.

## 8. Recovery nach Neustart / Re-Entry nach Absturz — ⚠️ UNGETESTET (aus Beobachtung)

Aus dem Code ableitbar (nicht durch echten Absturztest verifiziert):
`buehne_daemon.py` ist `Type=simple` mit `Restart=on-failure`, `RestartSec=10`
in der systemd-Unit — bei Absturz startet systemd automatisch neu, maximal
5× in 600s (`StartLimitBurst=5`, `StartLimitIntervalSec=600`). Der einzige
persistente Zustand ist `zustand.json` (eine Datei) — nach Neustart liest der
Prozess sie neu ein, es gibt keinen In-Memory-Zustand, der beim Neustart
verloren geht (laut Docstring-Architektur "GENAU EINE Datei"). Chrome-Fenster
wird über `chrome.pid`/`chrome.log` verfolgt und bei Bedarf neu gestartet
(Logik im Server, nicht in dieser Runde live durchgespielt).

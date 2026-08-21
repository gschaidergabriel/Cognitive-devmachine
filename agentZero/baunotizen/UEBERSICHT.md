# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-21T14:07:18Z. **3472 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-21T20:23:05+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 3374 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 2079 |
| baunotiz | bauverlauf.jsonl | 1250 |
| baunotiz | github-ereignis | 40 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 3472 · Gegenhypothese: 0 von 3472

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### research: bind Gen244 evidence epoch boundary

`baunotiz-bauverlauf-17fbb788ea6f219ad547` · baunotiz · bauverlauf.jsonl · 2026-08-21T20:23:05+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen244 evidence epoch boundary

`baunotiz-git-91a27c499c751b2e6482004cd9e7d65f51138c34` · baunotiz · git-commit · 2026-08-21T20:23:05+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen244 evidence epoch boundary

### claycode supervisor: bind Gen243 partial spine recovery and split effect authority

`baunotiz-bauverlauf-6bcab65719b518f85bb0` · baunotiz · bauverlauf.jsonl · 2026-08-21T19:47:52+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen243 partial spine recovery and split effect authority

`baunotiz-git-f338d9c5c4428b31ca65ce94caa7a53167cd2c23` · baunotiz · git-commit · 2026-08-21T19:47:52+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen243 partial spine recovery and split effect authority

### claycode supervisor: bind Gen241 evidence-spine collapse

`baunotiz-bauverlauf-6cb1eb03d2c5786ad179` · baunotiz · bauverlauf.jsonl · 2026-08-21T18:45:38+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen241 evidence-spine collapse

`baunotiz-git-a0c3aad1f5e485671c7c95e1252d8e64703c4c33` · baunotiz · git-commit · 2026-08-21T18:45:38+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen241 evidence-spine collapse

### claycode supervisor: bind Gen238 browser EffectGate boundary

`baunotiz-bauverlauf-37efa5538440f30921e4` · baunotiz · bauverlauf.jsonl · 2026-08-21T17:50:24+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen238 browser EffectGate boundary

`baunotiz-git-6b90ba0836cb13095e6878e37876c31edfba99c5` · baunotiz · git-commit · 2026-08-21T17:50:24+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen238 browser EffectGate boundary

### claycode supervisor: bind Gen238 OmniMind DB error collapse

`baunotiz-bauverlauf-daee8a72ea515e178df8` · baunotiz · bauverlauf.jsonl · 2026-08-21T16:42:37+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen238 OmniMind DB error collapse

`baunotiz-git-65e8fc39706492fda8a1b45a01f2fc4eb2abad49` · baunotiz · git-commit · 2026-08-21T16:42:37+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen238 OmniMind DB error collapse

### claycode supervisor: bind Gen234 Retina current-state race

`baunotiz-bauverlauf-d623d3741e045b368acb` · baunotiz · bauverlauf.jsonl · 2026-08-21T15:49:00+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen234 Retina current-state race

`baunotiz-git-efba204bbac60a43e190509115e2351750b0ca19` · baunotiz · git-commit · 2026-08-21T15:49:00+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen234 Retina current-state race

### research: bind Gen234 Retina current-state race frontier

`baunotiz-bauverlauf-f905f9a0e65e2ee38fa5` · baunotiz · bauverlauf.jsonl · 2026-08-21T15:46:33+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen234 Retina current-state race frontier

`baunotiz-git-6f7873d9dc12a0ad491a0f9a6406e8674e5066bd` · baunotiz · git-commit · 2026-08-21T15:46:33+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen234 Retina current-state race frontier

### research: bind Gen232 file-session alias falsifier

`baunotiz-bauverlauf-d00c776129ca9eb085a4` · baunotiz · bauverlauf.jsonl · 2026-08-21T14:50:01+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen232 file-session alias falsifier

`baunotiz-git-69dd03d4b06f196cdd074d31e0883521fc5c0e5b` · baunotiz · git-commit · 2026-08-21T14:50:01+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen232 file-session alias falsifier

### claycode supervisor: bind Gen232 service recovery and file-session alias

`baunotiz-bauverlauf-6d348fbb8f72c68a92cb` · baunotiz · bauverlauf.jsonl · 2026-08-21T14:43:33+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen232 service recovery and file-session alias

`baunotiz-git-cf493275d7976df1ea4e8a787ad9e21e6a0f45f1` · baunotiz · git-commit · 2026-08-21T14:43:33+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen232 service recovery and file-session alias

### EOS-Chronik 2026-08-21 13:49:12 +0000 — entityos: 2 Aenderungen

`baunotiz-git-7d80dfe628df35c63e4ae8f1e897f8447bf07ed9` · baunotiz · git-commit · 2026-08-21T13:49:12+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-21 13:49:12 +0000 — entityos: 2 Aenderungen

Anlass: Wache: Aenderung beobachtet

  the artefact/clayverse/dateien.py
  the artefact/web/chat/index.html

Zeit: 2026-08-21T13:49:12+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 2
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### research: analyze Gen227 verdichtung liveness regression

`baunotiz-bauverlauf-7e0819744aeca0d0698e` · baunotiz · bauverlauf.jsonl · 2026-08-21T13:47:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: analyze Gen227 verdichtung liveness regression

`baunotiz-git-897d8825ef1260475359e8ab7c6e77ebec853d68` · baunotiz · git-commit · 2026-08-21T13:47:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: analyze Gen227 verdichtung liveness regression

### EOS-Chronik 2026-08-21 13:44:20 +0000 — entityos: 1 Aenderungen

`baunotiz-git-18b1560a6743da056303ecfc7be2381b1c82e5b5` · baunotiz · git-commit · 2026-08-21T13:44:20+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-21 13:44:20 +0000 — entityos: 1 Aenderungen

Anlass: Wache: Aenderung beobachtet

  the artefact/web/chat/index.html

Zeit: 2026-08-21T13:44:20+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 1
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### claycode supervisor: bind Gen227 mandatory-service liveness regression

`baunotiz-bauverlauf-65370eacb39f0b1f37b5` · baunotiz · bauverlauf.jsonl · 2026-08-21T13:42:14+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen227 mandatory-service liveness regression

`baunotiz-git-98734f1da5456bb40b5a0a65efdcce6798dea00d` · baunotiz · git-commit · 2026-08-21T13:42:14+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen227 mandatory-service liveness regression

### agentZero-Export 2026-08-21T13:37:17Z (Generation 245, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-a9922f9dcb261ec5ee7e215d19f426e65286d8d6` · baunotiz · git-commit · 2026-08-21T13:40:59+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-21T13:37:17Z (Generation 245, 59 Dateien, 1 geschwaerzt)


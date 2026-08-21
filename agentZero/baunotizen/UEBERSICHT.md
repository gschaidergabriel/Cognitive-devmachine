# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-21T01:41:18Z. **3193 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-21T07:53:00+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 3095 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 1940 |
| baunotiz | bauverlauf.jsonl | 1110 |
| baunotiz | github-ereignis | 40 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 3193 · Gegenhypothese: 0 von 3193

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### claycode supervisor: bind Gen212 reauth red and warm-load guard

`baunotiz-bauverlauf-c19fe595d6d03cc937f3` · baunotiz · bauverlauf.jsonl · 2026-08-21T07:53:00+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen212 reauth red and warm-load guard

`baunotiz-git-80443246d14be324f744e2faaae60355ca921596` · baunotiz · git-commit · 2026-08-21T07:53:00+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen212 reauth red and warm-load guard

### research: bind Gen212 warm-pool load guard and reauth red

`baunotiz-bauverlauf-b6e80abaab0a6dde0b42` · baunotiz · bauverlauf.jsonl · 2026-08-21T07:48:20+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen212 warm-pool load guard and reauth red

`baunotiz-git-2d6f524f0b3db8de1640d3b0d1e5a097bd48e70e` · baunotiz · git-commit · 2026-08-21T07:48:20+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen212 warm-pool load guard and reauth red

### claycode supervisor: bind Gen211 PTY multi-run oscillation

`baunotiz-bauverlauf-009b9ea1ec3dce49c337` · baunotiz · bauverlauf.jsonl · 2026-08-21T06:41:59+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen211 PTY multi-run oscillation

`baunotiz-git-87433dc14cbf92d282e671c03344780969d67905` · baunotiz · git-commit · 2026-08-21T06:41:59+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen211 PTY multi-run oscillation

### research: bind Gen211 PTY recovery without fix credit

`baunotiz-bauverlauf-c694e3593ecb2bafe5e6` · baunotiz · bauverlauf.jsonl · 2026-08-21T02:46:42+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen211 PTY recovery without fix credit

`baunotiz-git-f7e1f58cb929e31275e53913dc65e437cb14f105` · baunotiz · git-commit · 2026-08-21T02:46:42+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen211 PTY recovery without fix credit

### claycode supervisor: bind Gen211 prompt alias and recurrent PTY red

`baunotiz-bauverlauf-6241a69263ed23f95d75` · baunotiz · bauverlauf.jsonl · 2026-08-21T02:43:01+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen211 prompt alias and recurrent PTY red

`baunotiz-git-0ab454ac948d50acb808607b51540ac327bbb504` · baunotiz · git-commit · 2026-08-21T02:43:01+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen211 prompt alias and recurrent PTY red

### research: bind Gen211 system-prompt last-writer alias

`baunotiz-bauverlauf-e153cd74f380e90ff037` · baunotiz · bauverlauf.jsonl · 2026-08-21T01:47:45+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen211 system-prompt last-writer alias

`baunotiz-git-539a6c1cf4f9051be12333398bb68359bdd39eb1` · baunotiz · git-commit · 2026-08-21T01:47:45+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen211 system-prompt last-writer alias

### claycode supervisor: bind Gen211 identity isolation and work-debt frontier

`baunotiz-bauverlauf-e5140e6f9e8ea22585f5` · baunotiz · bauverlauf.jsonl · 2026-08-21T01:42:55+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen211 identity isolation and work-debt frontier

`baunotiz-git-18f5a8a446bc194c38b70414bd19a44dcd977db6` · baunotiz · git-commit · 2026-08-21T01:42:55+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen211 identity isolation and work-debt frontier

### EOS-Chronik 2026-08-21 01:29:22 +0000 — entityos: 2 Aenderungen

`baunotiz-git-1fe881b3caa94203d3d1c8243bf8948a2bb1c0bf` · baunotiz · git-commit · 2026-08-21T01:29:22+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-21 01:29:22 +0000 — entityos: 2 Aenderungen

Anlass: Wache: Aenderung beobachtet

  the artefact/clayverse/fence_hook.py
  the artefact/tests/test_zaun_schreiben.py

Zeit: 2026-08-21T01:29:22+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 2
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 01:24:13 +0000 — entityos: 1 Aenderungen

`baunotiz-git-81e2ffcdef81a7ca65f39c2e0e05a4e903b4cc85` · baunotiz · git-commit · 2026-08-21T01:24:14+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-21 01:24:13 +0000 — entityos: 1 Aenderungen

Anlass: Wache: Aenderung beobachtet

  betrieb/eos_wal.py

Zeit: 2026-08-21T01:24:13+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 1
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 01:16:52 +0000 — entityos: 4 Aenderungen

`baunotiz-git-a7638950fc451e8ce1b7ea2113b5595fe7a6bb26` · baunotiz · git-commit · 2026-08-21T01:16:52+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-21 01:16:52 +0000 — entityos: 4 Aenderungen

Anlass: Wache: Aenderung beobachtet

  the artefact/clayverse/mistral_prestage/warm_zero.py
  the artefact/tests/test_bootlast.py
  zeuge/eos_zeuge.py
  zeuge/test_zeuge.py

Zeit: 2026-08-21T01:16:52+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 4
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### agentZero-Export 2026-08-21T01:11:17Z (Generation 212, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-4bec94c765e7b1247d15f190456872b0b72453d7` · baunotiz · git-commit · 2026-08-21T01:12:18+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-21T01:11:17Z (Generation 212, 59 Dateien, 1 geschwaerzt)

### research: route Gen211 null-evidence and isolation falsifiers

`baunotiz-bauverlauf-36c22de40724f275abfc` · baunotiz · bauverlauf.jsonl · 2026-08-21T00:49:28+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: route Gen211 null-evidence and isolation falsifiers

`baunotiz-git-5da37ecd70e2025d60f0ec852d53548657201413` · baunotiz · git-commit · 2026-08-21T00:49:28+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: route Gen211 null-evidence and isolation falsifiers

### research: bind Gen211 warm-pool session prompt race

`baunotiz-bauverlauf-92716302c9b3475c490f` · baunotiz · bauverlauf.jsonl · 2026-08-21T00:46:23+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen211 warm-pool session prompt race

`baunotiz-git-0a7fabfe8ee00b70b9e7be9b2b4f9e3aeb3c636b` · baunotiz · git-commit · 2026-08-21T00:46:23+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen211 warm-pool session prompt race

### agentZero-Export 2026-08-21T00:41:17Z (Generation 212, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-957babd305801ef325e4931d9137d63884a61c41` · baunotiz · git-commit · 2026-08-21T00:45:14+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-21T00:41:17Z (Generation 212, 59 Dateien, 1 geschwaerzt)

### agentZero-Export 2026-08-21T00:41:17Z (Generation 212, 59 Dateien, 1 geschwaerzt)

`baunotiz-bauverlauf-945857c2aac4c02ea2dd` · baunotiz · bauverlauf.jsonl · 2026-08-21T00:45:14+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen207 atomicity split and recurrent PTY red

`baunotiz-bauverlauf-ff4b794053d58fe180c0` · baunotiz · bauverlauf.jsonl · 2026-08-21T00:43:41+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_


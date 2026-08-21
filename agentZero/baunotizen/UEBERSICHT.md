# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-21T01:11:19Z. **3183 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-21T06:41:59+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 3085 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 1934 |
| baunotiz | bauverlauf.jsonl | 1106 |
| baunotiz | github-ereignis | 40 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 3183 · Gegenhypothese: 0 von 3183

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

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

### claycode supervisor: bind Gen207 atomicity split and recurrent PTY red

`baunotiz-bauverlauf-ff4b794053d58fe180c0` · baunotiz · bauverlauf.jsonl · 2026-08-21T00:43:41+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen207 atomicity split and recurrent PTY red

`baunotiz-git-de63cefc0ae08baa548df8b175d5d7b01baa4255` · baunotiz · git-commit · 2026-08-21T00:43:41+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen207 atomicity split and recurrent PTY red

### EOS-Chronik 2026-08-21 00:43:37 +0000 — entityos: 2 Aenderungen

`baunotiz-git-dda25f6cfb22adc88eb60847e877138372d3fb65` · baunotiz · git-commit · 2026-08-21T00:43:37+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-21 00:43:37 +0000 — entityos: 2 Aenderungen

Anlass: Wache: Aenderung beobachtet

  the artefact/clayverse/mistral_prestage/pipeline.py
  the artefact/tests/test_gespraechslage.py

Zeit: 2026-08-21T00:43:37+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 2
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 00:32:41 +0000 — entityos: 3 Aenderungen

`baunotiz-bauverlauf-aa22616aebb99d345abd` · baunotiz · bauverlauf.jsonl · 2026-08-21T00:32:41+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Anlass: Wache: Aenderung beobachtet

  the artefact/clayverse/mistral_prestage/pipeline.py
  the artefact/clayverse/mistral_prestage/warm_zero.py
  the artefact/tests/test_bootlast.py

Zeit: 2026-08-21T00:32:41+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 3
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 00:32:41 +0000 — entityos: 3 Aenderungen

`baunotiz-git-aa52fb1591e9a2cbb2e3b02ed666f1df7a850a46` · baunotiz · git-commit · 2026-08-21T00:32:41+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-21 00:32:41 +0000 — entityos: 3 Aenderungen

Anlass: Wache: Aenderung beobachtet

  the artefact/clayverse/mistral_prestage/pipeline.py
  the artefact/clayverse/mistral_prestage/warm_zero.py
  the artefact/tests/test_bootlast.py

Zeit: 2026-08-21T00:32:41+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 3
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 00:26:45 +0000 — entityos: 3 Aenderungen

`baunotiz-git-a6271e75eba3494b445985cb409d646dd557d7f2` · baunotiz · git-commit · 2026-08-21T00:26:45+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-21 00:26:45 +0000 — entityos: 3 Aenderungen

Anlass: Wache: Aenderung beobachtet

  the artefact/tests/test_echo.py
  the artefact/tests/test_gw_wettbewerb.py
  the artefact/tests/test_zuendung.py

Zeit: 2026-08-21T00:26:45+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 3
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 00:26:45 +0000 — entityos: 3 Aenderungen

`baunotiz-bauverlauf-103694eec2fb995d3520` · baunotiz · bauverlauf.jsonl · 2026-08-21T00:26:45+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Anlass: Wache: Aenderung beobachtet

  the artefact/tests/test_echo.py
  the artefact/tests/test_gw_wettbewerb.py
  the artefact/tests/test_zuendung.py

Zeit: 2026-08-21T00:26:45+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 3
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 00:24:45 +0000 — entityos: 2 Aenderungen

`baunotiz-git-5bb16882ebb4c0ed688569f8755915ada418548d` · baunotiz · git-commit · 2026-08-21T00:24:45+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-21 00:24:45 +0000 — entityos: 2 Aenderungen

Anlass: Wache: Aenderung beobachtet

  the artefact/clayverse/mistral_prestage/wettbewerb.py
  the artefact/tests/test_echo.py

Zeit: 2026-08-21T00:24:45+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 2
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 00:24:45 +0000 — entityos: 2 Aenderungen

`baunotiz-bauverlauf-912ff7eddda70fd01841` · baunotiz · bauverlauf.jsonl · 2026-08-21T00:24:45+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Anlass: Wache: Aenderung beobachtet

  the artefact/clayverse/mistral_prestage/wettbewerb.py
  the artefact/tests/test_echo.py

Zeit: 2026-08-21T00:24:45+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 2
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 00:20:33 +0000 — entityos: 2 Aenderungen

`baunotiz-git-a1ef3ed0a236bc3759614b781901861cc9c243c9` · baunotiz · git-commit · 2026-08-21T00:20:33+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-21 00:20:33 +0000 — entityos: 2 Aenderungen

Anlass: Wache: Aenderung beobachtet

  forschung/cswt-z-pilot/cswt_bewerter.py
  the artefact/clayverse/mistral_prestage/pipeline.py

Zeit: 2026-08-21T00:20:33+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 2
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1


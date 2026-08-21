# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-21T02:41:19Z. **3221 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-21T09:02:05+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 3123 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 1954 |
| baunotiz | bauverlauf.jsonl | 1124 |
| baunotiz | github-ereignis | 40 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 3221 · Gegenhypothese: 0 von 3221

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### claycode supervisor: bind Gen213 intent-trace ontology defect

`baunotiz-bauverlauf-ebd98bfa53c04e3cb19e` · baunotiz · bauverlauf.jsonl · 2026-08-21T09:02:05+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen213 intent-trace ontology defect

`baunotiz-git-97969bf8b9a64f0151596ae29106459198efc83f` · baunotiz · git-commit · 2026-08-21T09:02:05+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen213 intent-trace ontology defect

### research: index Gen213 tool-trace intent ontology

`baunotiz-bauverlauf-f4a45d313c72f281115f` · baunotiz · bauverlauf.jsonl · 2026-08-21T08:51:08+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: index Gen213 tool-trace intent ontology

`baunotiz-git-63a45f5e8583b1c6bd2667ac8a61324adea159f1` · baunotiz · git-commit · 2026-08-21T08:51:08+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: index Gen213 tool-trace intent ontology

### research: bind Gen213 tool-trace intent ontology defect

`baunotiz-bauverlauf-1a13fcd8cc9bdf6fde5f` · baunotiz · bauverlauf.jsonl · 2026-08-21T08:50:23+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen213 tool-trace intent ontology defect

`baunotiz-git-138d047eb75eaca14e771973e38d6fee604924ea` · baunotiz · git-commit · 2026-08-21T08:50:23+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen213 tool-trace intent ontology defect

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

### EOS-Chronik 2026-08-21 02:27:45 +0000 — entityos: 2 Aenderungen

`baunotiz-git-ab34c0b56735027aa97f3e3bb7ec410d3203e569` · baunotiz · git-commit · 2026-08-21T02:27:45+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-21 02:27:45 +0000 — entityos: 2 Aenderungen

Anlass: Wache: Aenderung beobachtet

  the artefact/clayverse/hyperposition.py
  the artefact/tests/test_hyperposition_rueckfall.py

Zeit: 2026-08-21T02:27:45+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 2
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 02:25:44 +0000 — entityos: 2 Aenderungen

`baunotiz-git-2078ffe8c9631e09c7653b6792a56ffbd72f4a53` · baunotiz · git-commit · 2026-08-21T02:25:44+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-21 02:25:44 +0000 — entityos: 2 Aenderungen

Anlass: Wache: Aenderung beobachtet

  the artefact/clayverse/hyperposition.py
  the artefact/tests/test_hyperposition_rueckfall.py

Zeit: 2026-08-21T02:25:44+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 2
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 02:20:16 +0000 — entityos: 2 Aenderungen

`baunotiz-git-084464d0ba440b1a5a51bf3edee5fc8c77e959e9` · baunotiz · git-commit · 2026-08-21T02:20:16+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-21 02:20:16 +0000 — entityos: 2 Aenderungen

Anlass: Wache: Aenderung beobachtet

  the artefact/clayverse/microclay_retrieval.py
  the artefact/tests/test_befoerderung.py

Zeit: 2026-08-21T02:20:16+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 2
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### agentZero-Export 2026-08-21T02:11:17Z (Generation 215, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-d6c35d1fd26590613da6dfca542b0c630945c4bb` · baunotiz · git-commit · 2026-08-21T02:12:12+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-21T02:11:17Z (Generation 215, 59 Dateien, 1 geschwaerzt)

### EOS-Chronik 2026-08-21 02:11:15 +0000 — entityos: 4 Aenderungen

`baunotiz-bauverlauf-6c7534ce319a7fe9b272` · baunotiz · bauverlauf.jsonl · 2026-08-21T02:11:15+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Anlass: Wache: Aenderung beobachtet

  the artefact/clayverse/mistral_prestage/pipeline.py
  the artefact/clayverse/mistral_prestage/prestage.py
  the artefact/tests/test_buchfuehrung.py
  the artefact/tests/test_gw_arbeitsraum.py

Zeit: 2026-08-21T02:11:15+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 4
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 02:11:15 +0000 — entityos: 4 Aenderungen

`baunotiz-git-c95366043e522389ce8470ef73dedad95849e97d` · baunotiz · git-commit · 2026-08-21T02:11:15+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-21 02:11:15 +0000 — entityos: 4 Aenderungen

Anlass: Wache: Aenderung beobachtet

  the artefact/clayverse/mistral_prestage/pipeline.py
  the artefact/clayverse/mistral_prestage/prestage.py
  the artefact/tests/test_buchfuehrung.py
  the artefact/tests/test_gw_arbeitsraum.py

Zeit: 2026-08-21T02:11:15+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 4
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 02:08:16 +0000 — clayverse: 1 Aenderungen

`baunotiz-bauverlauf-cce6c7c1a13b467fb3f6` · baunotiz · bauverlauf.jsonl · 2026-08-21T02:08:16+00:00 · ClayVerse

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Anlass: Wache: Aenderung beobachtet

  werkzeug/vorprozessor.py

Zeit: 2026-08-21T02:08:16+00:00
Wirt: frank-api
Instanz: zero
Baum: clayverse (/opt/clayverse)
Dateien: 1
Fern: origin -> /srv/git/clayverse.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 02:08:16 +0000 — clayverse: 1 Aenderungen

`baunotiz-git-f712e0bb96d0e86b22a4313d822a603a880ccf6d` · baunotiz · git-commit · 2026-08-21T02:08:16+00:00 · ClayVerse

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-21 02:08:16 +0000 — clayverse: 1 Aenderungen

Anlass: Wache: Aenderung beobachtet

  werkzeug/vorprozessor.py

Zeit: 2026-08-21T02:08:16+00:00
Wirt: frank-api
Instanz: zero
Baum: clayverse (/opt/clayverse)
Dateien: 1
Fern: origin -> /srv/git/clayverse.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 02:05:48 +0000 — entityos: 3 Aenderungen

`baunotiz-bauverlauf-8eb3a40384dbb1c966f6` · baunotiz · bauverlauf.jsonl · 2026-08-21T02:05:48+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Anlass: Wache: Aenderung beobachtet

  betrieb/eos_wal.py
  the artefact/clayverse/mistral_prestage/wettbewerb.py
  the artefact/tests/test_luecke.py

Zeit: 2026-08-21T02:05:48+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 3
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1


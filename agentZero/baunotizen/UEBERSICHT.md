# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-21T03:41:21Z. **3242 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-21T09:48:13+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 3144 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 1963 |
| baunotiz | bauverlauf.jsonl | 1136 |
| baunotiz | github-ereignis | 40 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 3242 · Gegenhypothese: 0 von 3242

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### claycode supervisor: bind Gen218 Auftrag rewrite red

`baunotiz-bauverlauf-3bcd4caae7c84582e8e0` · baunotiz · bauverlauf.jsonl · 2026-08-21T09:48:13+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen218 Auftrag rewrite red

`baunotiz-git-28db706142b1f6aa5646361cf3a6dda88b0b28c6` · baunotiz · git-commit · 2026-08-21T09:48:13+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen218 Auftrag rewrite red

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

### agentZero-Export 2026-08-21T03:11:18Z (Generation 220, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-0565e79470d09dfa8dc7b56c4c614622f23290d4` · baunotiz · git-commit · 2026-08-21T03:12:06+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-21T03:11:18Z (Generation 220, 59 Dateien, 1 geschwaerzt)

### EOS-Chronik 2026-08-21 03:10:20 +0000 — entityos: 2 Aenderungen

`baunotiz-bauverlauf-1dfbeb22db3b72e719c4` · baunotiz · bauverlauf.jsonl · 2026-08-21T03:10:20+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Anlass: Wache: Aenderung beobachtet

  the artefact/clayverse/mistral_prestage/pipeline.py
  the artefact/tests/test_gwanbauten.py

Zeit: 2026-08-21T03:10:20+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 2
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 03:10:20 +0000 — entityos: 2 Aenderungen

`baunotiz-git-56c34585ea584ebf2c0f02716adcf476bc73892d` · baunotiz · git-commit · 2026-08-21T03:10:20+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-21 03:10:20 +0000 — entityos: 2 Aenderungen

Anlass: Wache: Aenderung beobachtet

  the artefact/clayverse/mistral_prestage/pipeline.py
  the artefact/tests/test_gwanbauten.py

Zeit: 2026-08-21T03:10:20+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 2
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 03:06:31 +0000 — unifieddb: 1 Aenderungen

`baunotiz-bauverlauf-54fd07255566c96c6f2b` · baunotiz · bauverlauf.jsonl · 2026-08-21T03:06:31+00:00 · ClayVerse

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Anlass: Wache: Aenderung beobachtet

  udb/abruf/wegverfall.py

Zeit: 2026-08-21T03:06:31+00:00
Wirt: frank-api
Instanz: zero
Baum: unifieddb (/opt/unifieddb)
Dateien: 1
Fern: origin -> /srv/git/unifieddb.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 03:06:31 +0000 — unifieddb: 1 Aenderungen

`baunotiz-git-0a93b02ad07c9e276bdab30d235095a0f5b1a169` · baunotiz · git-commit · 2026-08-21T03:06:31+00:00 · ClayVerse

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-21 03:06:31 +0000 — unifieddb: 1 Aenderungen

Anlass: Wache: Aenderung beobachtet

  udb/abruf/wegverfall.py

Zeit: 2026-08-21T03:06:31+00:00
Wirt: frank-api
Instanz: zero
Baum: unifieddb (/opt/unifieddb)
Dateien: 1
Fern: origin -> /srv/git/unifieddb.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 03:01:15 +0000 — entityos: 6 Aenderungen

`baunotiz-bauverlauf-64edd190733d606e51bd` · baunotiz · bauverlauf.jsonl · 2026-08-21T03:01:15+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Anlass: Wache: Aenderung beobachtet

  betrieb/eos_theta.py
  betrieb/test_theta.py
  the artefact/clayverse/retrieval.py
  the artefact/tests/test_wegsitzung.py
  zeuge/eos_zeuge.py
  zeuge/test_zeuge.py

Zeit: 2026-08-21T03:01:15+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 6
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 03:01:15 +0000 — entityos: 6 Aenderungen

`baunotiz-git-74d24056de0de89a2ab0f8835076695481073fed` · baunotiz · git-commit · 2026-08-21T03:01:15+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-21 03:01:15 +0000 — entityos: 6 Aenderungen

Anlass: Wache: Aenderung beobachtet

  betrieb/eos_theta.py
  betrieb/test_theta.py
  the artefact/clayverse/retrieval.py
  the artefact/tests/test_wegsitzung.py
  zeuge/eos_zeuge.py
  zeuge/test_zeuge.py

Zeit: 2026-08-21T03:01:15+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 6
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 03:01:11 +0000 — unifieddb: 1 Aenderungen

`baunotiz-bauverlauf-9de11ceadebbad555f34` · baunotiz · bauverlauf.jsonl · 2026-08-21T03:01:11+00:00 · ClayVerse

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Anlass: Wache: Aenderung beobachtet

  udb/abruf/paket.py

Zeit: 2026-08-21T03:01:11+00:00
Wirt: frank-api
Instanz: zero
Baum: unifieddb (/opt/unifieddb)
Dateien: 1
Fern: origin -> /srv/git/unifieddb.git
Werkzeug: eos-chronik.py v1

### EOS-Chronik 2026-08-21 03:01:11 +0000 — unifieddb: 1 Aenderungen

`baunotiz-git-5d2e5ea71986c081d2f3455ddd99579dee5ab106` · baunotiz · git-commit · 2026-08-21T03:01:11+00:00 · ClayVerse

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-21 03:01:11 +0000 — unifieddb: 1 Aenderungen

Anlass: Wache: Aenderung beobachtet

  udb/abruf/paket.py

Zeit: 2026-08-21T03:01:11+00:00
Wirt: frank-api
Instanz: zero
Baum: unifieddb (/opt/unifieddb)
Dateien: 1
Fern: origin -> /srv/git/unifieddb.git
Werkzeug: eos-chronik.py v1

### research: bind Gen211 PTY recovery without fix credit

`baunotiz-bauverlauf-c694e3593ecb2bafe5e6` · baunotiz · bauverlauf.jsonl · 2026-08-21T02:46:42+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen211 PTY recovery without fix credit

`baunotiz-git-f7e1f58cb929e31275e53913dc65e437cb14f105` · baunotiz · git-commit · 2026-08-21T02:46:42+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen211 PTY recovery without fix credit


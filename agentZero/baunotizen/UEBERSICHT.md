# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-21T08:50:31Z. **3360 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-21T14:50:01+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 3262 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 2024 |
| baunotiz | bauverlauf.jsonl | 1193 |
| baunotiz | github-ereignis | 40 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 3360 · Gegenhypothese: 0 von 3360

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

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

### research: analyze Gen227 verdichtung liveness regression

`baunotiz-bauverlauf-7e0819744aeca0d0698e` · baunotiz · bauverlauf.jsonl · 2026-08-21T13:47:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: analyze Gen227 verdichtung liveness regression

`baunotiz-git-897d8825ef1260475359e8ab7c6e77ebec853d68` · baunotiz · git-commit · 2026-08-21T13:47:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: analyze Gen227 verdichtung liveness regression

### claycode supervisor: bind Gen227 mandatory-service liveness regression

`baunotiz-bauverlauf-65370eacb39f0b1f37b5` · baunotiz · bauverlauf.jsonl · 2026-08-21T13:42:14+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen227 mandatory-service liveness regression

`baunotiz-git-98734f1da5456bb40b5a0a65efdcce6798dea00d` · baunotiz · git-commit · 2026-08-21T13:42:14+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen227 mandatory-service liveness regression

### research: bind Gen224 wake governor lost-wake frontier

`baunotiz-bauverlauf-6e0059eb89511e22ca6a` · baunotiz · bauverlauf.jsonl · 2026-08-21T12:46:47+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen224 wake governor lost-wake frontier

`baunotiz-git-1a8b61d0fa6c4e9f16fccf32ddcc749d82dcf234` · baunotiz · git-commit · 2026-08-21T12:46:47+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen224 wake governor lost-wake frontier

### claycode supervisor: block Gen224 wake-event replay activation

`baunotiz-bauverlauf-a4efe68ba2753d7b9d88` · baunotiz · bauverlauf.jsonl · 2026-08-21T12:46:37+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: block Gen224 wake-event replay activation

`baunotiz-git-cdb4a44fbe1896ffb90e5763421b354eb2edec1e` · baunotiz · git-commit · 2026-08-21T12:46:37+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: block Gen224 wake-event replay activation

### claycode supervisor: bind Gen223 typed wake contract evidence

`baunotiz-bauverlauf-c4632e7d1cad5c0968a2` · baunotiz · bauverlauf.jsonl · 2026-08-21T11:39:42+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen223 typed wake contract evidence

`baunotiz-git-1f366bc8f5a5283b6a43400ca99a8f5df5e7907d` · baunotiz · git-commit · 2026-08-21T11:39:42+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen223 typed wake contract evidence

### claycode supervisor: bind Gen220 live-path GWT evidence boundary

`baunotiz-bauverlauf-990d37d21ee2b76f8ccb` · baunotiz · bauverlauf.jsonl · 2026-08-21T10:37:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen220 live-path GWT evidence boundary

`baunotiz-git-c719afd15fa30f4eae8bb568c6944aaeed625a58` · baunotiz · git-commit · 2026-08-21T10:37:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen220 live-path GWT evidence boundary

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

### EOS-Chronik 2026-08-21 08:44:08 +0000 — entityos: 1 Aenderungen

`baunotiz-git-44158da9d77a0004957217b5f3a598c1a7307179` · baunotiz · git-commit · 2026-08-21T08:44:08+00:00 · BACK agent

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

EOS-Chronik 2026-08-21 08:44:08 +0000 — entityos: 1 Aenderungen

Anlass: Wache: Aenderung beobachtet

  the artefact/clayverse/omnimind_anreicherung.py

Zeit: 2026-08-21T08:44:08+00:00
Wirt: frank-api
Instanz: zero
Baum: entityos (/opt/entityos)
Dateien: 1
Fern: lokal -> /srv/git/entityos.git
Werkzeug: eos-chronik.py v1


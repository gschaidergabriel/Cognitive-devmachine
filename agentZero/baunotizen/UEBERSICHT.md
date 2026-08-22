# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-22T05:06:42Z. **4009 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-22T10:56:48+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 3911 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 2347 |
| baunotiz | bauverlauf.jsonl | 1516 |
| baunotiz | github-ereignis | 43 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 4009 · Gegenhypothese: 0 von 4009

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### claycode supervisor: gate Mini Entity 0.7 on source-bound executable reproduction

`baunotiz-bauverlauf-dbfc2c41c61e491a03ef` · baunotiz · bauverlauf.jsonl · 2026-08-22T10:56:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: gate Mini Entity 0.7 on source-bound executable reproduction

`baunotiz-git-8b42c02d2714cf3401030f58712c0f83bf4efbac` · baunotiz · git-commit · 2026-08-22T10:56:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: gate Mini Entity 0.7 on source-bound executable reproduction

### native: fix Mini Entity source split boundary

`baunotiz-bauverlauf-9cf2399c1578b649ccfe` · baunotiz · bauverlauf.jsonl · 2026-08-22T10:19:20+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### native: fix Mini Entity source split boundary

`baunotiz-git-e18cb8fa763fe675af9c5223e2bfcfd90dd007ce` · baunotiz · git-commit · 2026-08-22T10:19:20+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

native: fix Mini Entity source split boundary

### native: add Mini Entity configuration and CLI surface

`baunotiz-bauverlauf-f9fd03b9a2872855450c` · baunotiz · bauverlauf.jsonl · 2026-08-22T10:18:04+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### native: add Mini Entity configuration and CLI surface

`baunotiz-git-fd5e110aa72ba1e08ef0d4556a28c794a04dbd8f` · baunotiz · git-commit · 2026-08-22T10:18:04+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

native: add Mini Entity configuration and CLI surface

### native: add atomic study and source-CAS commit layer

`baunotiz-bauverlauf-ffb6927142f8c0616fb2` · baunotiz · bauverlauf.jsonl · 2026-08-22T10:17:42+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### native: add atomic study and source-CAS commit layer

`baunotiz-git-cebde0eacda97329b233e4ff8ba3f3830f560d3f` · baunotiz · git-commit · 2026-08-22T10:17:42+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

native: add atomic study and source-CAS commit layer

### native: add Mini Entity inference boundary

`baunotiz-bauverlauf-1f5ee2f27007f4a667ec` · baunotiz · bauverlauf.jsonl · 2026-08-22T10:17:12+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### native: add Mini Entity inference boundary

`baunotiz-git-ba1dbb166e27d36dc7cad4bf1a580b21351913ff` · baunotiz · git-commit · 2026-08-22T10:17:12+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

native: add Mini Entity inference boundary

### native: add Mini Entity profile and evidence packet layer

`baunotiz-bauverlauf-a7932e8bf400e7000e2f` · baunotiz · bauverlauf.jsonl · 2026-08-22T10:16:53+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### native: add Mini Entity profile and evidence packet layer

`baunotiz-git-6facbcecf02ef9a4f58babc9e503672b19d86b8b` · baunotiz · git-commit · 2026-08-22T10:16:53+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

native: add Mini Entity profile and evidence packet layer

### native: add Mini Entity core and state substrate

`baunotiz-bauverlauf-dd6d807f76cfd903e636` · baunotiz · bauverlauf.jsonl · 2026-08-22T10:16:34+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### native: add Mini Entity core and state substrate

`baunotiz-git-20a0f65f10094cc557c6d0441e0aa5995475a1de` · baunotiz · git-commit · 2026-08-22T10:16:34+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

native: add Mini Entity core and state substrate

### native: add source-bound Mini Entity 0.7 entry unit

`baunotiz-bauverlauf-38fd33854139c0c975c4` · baunotiz · bauverlauf.jsonl · 2026-08-22T10:16:14+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### native: add source-bound Mini Entity 0.7 entry unit

`baunotiz-git-b46f11f4bec1b7d82f7a6f751b200e28cc10147e` · baunotiz · git-commit · 2026-08-22T10:16:14+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

native: add source-bound Mini Entity 0.7 entry unit

### state: advance state-box mechanism and native provenance frontier

`baunotiz-bauverlauf-64a8845a717e8ba5e295` · baunotiz · bauverlauf.jsonl · 2026-08-22T10:08:25+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### state: advance state-box mechanism and native provenance frontier

`baunotiz-git-b9e1104bcafa00b95152968ea9f6dde91b89f3b0` · baunotiz · git-commit · 2026-08-22T10:08:25+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

state: advance state-box mechanism and native provenance frontier

### evidence: record deterministic state-box reference support

`baunotiz-bauverlauf-42769bb721a18ae67747` · baunotiz · bauverlauf.jsonl · 2026-08-22T10:07:56+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### evidence: record deterministic state-box reference support

`baunotiz-git-74a1510dd43da6d97c14f3fc613ee1f1176711b7` · baunotiz · git-commit · 2026-08-22T10:07:56+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

evidence: record deterministic state-box reference support

### test: add state-box epistemic and determinism falsifiers

`baunotiz-bauverlauf-fff3f16242ab1186ad36` · baunotiz · bauverlauf.jsonl · 2026-08-22T10:07:23+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### test: add state-box epistemic and determinism falsifiers

`baunotiz-git-2526ca946937ff2df9425c68c408e487a8bca437` · baunotiz · git-commit · 2026-08-22T10:07:23+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

test: add state-box epistemic and determinism falsifiers

### feat: add deterministic generic state-box reference algorithm

`baunotiz-bauverlauf-fc9bc13ca5de97e3b29f` · baunotiz · bauverlauf.jsonl · 2026-08-22T10:06:08+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### feat: add deterministic generic state-box reference algorithm

`baunotiz-git-cc0256984ae12deb1f1dbef462179b1784a0a5c8` · baunotiz · git-commit · 2026-08-22T10:06:08+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

feat: add deterministic generic state-box reference algorithm

### research: bind UNKNOWN red guard into Mini Entity fusion receipt

`baunotiz-bauverlauf-79ab9b8f32e20b6bafbc` · baunotiz · bauverlauf.jsonl · 2026-08-22T10:06:03+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_


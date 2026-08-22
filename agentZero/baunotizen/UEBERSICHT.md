# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-22T07:06:42Z. **4041 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-22T13:26:13+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 3943 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 2363 |
| baunotiz | bauverlauf.jsonl | 1532 |
| baunotiz | github-ereignis | 43 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 4041 · Gegenhypothese: 0 von 4041

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### evidence(native): bind 0.7 semantic parity blocker

`baunotiz-bauverlauf-f6934384a5af71430c38` · baunotiz · bauverlauf.jsonl · 2026-08-22T13:26:13+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### evidence(native): bind 0.7 semantic parity blocker

`baunotiz-git-5b6ebca899f8692d767b17402fb83e664c9f0bfb` · baunotiz · git-commit · 2026-08-22T13:26:13+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

evidence(native): bind 0.7 semantic parity blocker

### test(native): adapt exact repro gate to canonical closure tests

`baunotiz-bauverlauf-6e7ecec9bd0df6d45b07` · baunotiz · bauverlauf.jsonl · 2026-08-22T13:24:58+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### test(native): adapt exact repro gate to canonical closure tests

`baunotiz-git-0ff81daf97f473661ff95bd0c88296d261a02791` · baunotiz · git-commit · 2026-08-22T13:24:58+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

test(native): adapt exact repro gate to canonical closure tests

### ops(actions): add bounded Mini Entity 0.7 dispatch bridge

`baunotiz-bauverlauf-6b20f79b35eb24270180` · baunotiz · bauverlauf.jsonl · 2026-08-22T13:23:32+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### ops(actions): add bounded Mini Entity 0.7 dispatch bridge

`baunotiz-git-8a2d9c1badb174303ec72457e1533e52a78c160e` · baunotiz · git-commit · 2026-08-22T13:23:32+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

ops(actions): add bounded Mini Entity 0.7 dispatch bridge

### fix(native): keep historical provenance checker fail-closed

`baunotiz-bauverlauf-7335b85b2aad0adbe09d` · baunotiz · bauverlauf.jsonl · 2026-08-22T13:22:14+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

* fix(native): separate source presence from credited rebuild

* test(native): keep historical checker fail-closed on 0.7 source

* fix(native): support explicit historical PROGRAM_STATE identity

* test(native): cover PROGRAM_STATE 7.1 historical identity

### fix(native): keep historical provenance checker fail-closed

`baunotiz-git-18b6f99eed7714d0ba5040e4a8f32f58107b5b3f` · baunotiz · git-commit · 2026-08-22T13:22:14+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

fix(native): keep historical provenance checker fail-closed

* fix(native): separate source presence from credited rebuild

* test(native): keep historical checker fail-closed on 0.7 source

* fix(native): support explicit historical PROGRAM_STATE identity

* test(native): cover PROGRAM_STATE 7.1 historical identity

### test(mini-entity): add canonical exact 0.7 repro gate

`baunotiz-bauverlauf-00684f5feb9d911314fa` · baunotiz · bauverlauf.jsonl · 2026-08-22T13:20:59+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### test(mini-entity): add canonical exact 0.7 repro gate

`baunotiz-git-e261757fa21538ea24a6ff174b7b55d9929fcb94` · baunotiz · git-commit · 2026-08-22T13:20:59+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

test(mini-entity): add canonical exact 0.7 repro gate

### state: advance frontier to exact Mini Entity 0.7 reproduction

`baunotiz-bauverlauf-f5502e25d78f4fde9109` · baunotiz · bauverlauf.jsonl · 2026-08-22T13:16:17+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### state: advance frontier to exact Mini Entity 0.7 reproduction

`baunotiz-git-c7219e8fa7929d5e5a4fcd756aa07e815a32db75` · baunotiz · git-commit · 2026-08-22T13:16:17+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

state: advance frontier to exact Mini Entity 0.7 reproduction

### build(mini-entity): bind transitive native source closure

`baunotiz-bauverlauf-92cd1605940a0e502e64` · baunotiz · bauverlauf.jsonl · 2026-08-22T13:15:36+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Repair Mini Entity 0.7 source provenance by binding all reachable project-local quoted includes, rejecting dynamic/unbound local includes, and recording bounded falsifier evidence. Full exact 0.7 runtime acceptance remains open.

### build(mini-entity): bind transitive native source closure

`baunotiz-git-915723c0961a495be72f8a8075b4577a036f47f2` · baunotiz · git-commit · 2026-08-22T13:15:36+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

build(mini-entity): bind transitive native source closure

Repair Mini Entity 0.7 source provenance by binding all reachable project-local quoted includes, rejecting dynamic/unbound local includes, and recording bounded falsifier evidence. Full exact 0.7 runtime acceptance remains open.

### claycode supervisor: bind Gen276 same-source PTY nondeterminism

`baunotiz-bauverlauf-2c0bf21c31360db1ebe4` · baunotiz · bauverlauf.jsonl · 2026-08-22T11:45:06+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen276 same-source PTY nondeterminism

`baunotiz-git-aab1c69d45622076ee07c3bae40b4dcebe4ea07e` · baunotiz · git-commit · 2026-08-22T11:45:06+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen276 same-source PTY nondeterminism

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


# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-20T13:41:16Z. **3057 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-20T19:52:22+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 2959 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 1870 |
| baunotiz | bauverlauf.jsonl | 1044 |
| baunotiz | github-ereignis | 40 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 3057 · Gegenhypothese: 0 von 3057

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### research: route Gen197 feedback-channel path split

`baunotiz-bauverlauf-1c2621ed76cb057d9a1e` · baunotiz · bauverlauf.jsonl · 2026-08-20T19:52:22+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: route Gen197 feedback-channel path split

`baunotiz-git-3adcbb4297b8a9865f95c3e84222fecc7279d2a4` · baunotiz · git-commit · 2026-08-20T19:52:22+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: route Gen197 feedback-channel path split

### claycode supervisor: bind Gen197 GWT feedback and 631/1 frontier

`baunotiz-bauverlauf-6a231fcca6a067d0ee48` · baunotiz · bauverlauf.jsonl · 2026-08-20T19:50:04+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen197 GWT feedback and 631/1 frontier

`baunotiz-git-0b8cf51f81f8203aef35f3093023442110ec4db8` · baunotiz · git-commit · 2026-08-20T19:50:04+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen197 GWT feedback and 631/1 frontier

### research index: add Gen197 GWT feedback aliasing frontier

`baunotiz-bauverlauf-5c93404633630de78b11` · baunotiz · bauverlauf.jsonl · 2026-08-20T19:49:19+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research index: add Gen197 GWT feedback aliasing frontier

`baunotiz-git-49c402c796f7b8bc025809634c15103568af2db0` · baunotiz · git-commit · 2026-08-20T19:49:19+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research index: add Gen197 GWT feedback aliasing frontier

### research: bind Gen197 GWT feedback identity-aliasing falsifier

`baunotiz-bauverlauf-2e80b3aeaffaa5b04ed3` · baunotiz · bauverlauf.jsonl · 2026-08-20T19:48:40+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen197 GWT feedback identity-aliasing falsifier

`baunotiz-git-a429b4f91b7bd117343f6ef9ec976834887b1b74` · baunotiz · git-commit · 2026-08-20T19:48:40+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen197 GWT feedback identity-aliasing falsifier

### research: route Gen195 PTY refresh and truth-fork falsifiers

`baunotiz-bauverlauf-b36c39f8a96e17c47d8f` · baunotiz · bauverlauf.jsonl · 2026-08-20T18:55:30+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: route Gen195 PTY refresh and truth-fork falsifiers

`baunotiz-git-5e8cf3cd469ac6c348094706d6c24f2adb187751` · baunotiz · git-commit · 2026-08-20T18:55:30+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: route Gen195 PTY refresh and truth-fork falsifiers

### claycode supervisor: bind Gen195 PTY recurrence and receipt drift

`baunotiz-bauverlauf-2258cce770eeb5d00b70` · baunotiz · bauverlauf.jsonl · 2026-08-20T18:52:05+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen195 PTY recurrence and receipt drift

`baunotiz-git-7db5978180cb8add33300af099814b5b36796ecd` · baunotiz · git-commit · 2026-08-20T18:52:05+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen195 PTY recurrence and receipt drift

### claycode supervisor: bind Gen195 GWT causal bottleneck frontier

`baunotiz-bauverlauf-92b05caaa81a037c2b32` · baunotiz · bauverlauf.jsonl · 2026-08-20T17:56:18+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen195 GWT causal bottleneck frontier

`baunotiz-git-ea39cfd7a193769cc4ed47dccd409dae61e56a73` · baunotiz · git-commit · 2026-08-20T17:56:18+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen195 GWT causal bottleneck frontier

### research: route Gen195 GWT causal bottleneck falsifiers

`baunotiz-bauverlauf-84cdcd92c128c8ce84c1` · baunotiz · bauverlauf.jsonl · 2026-08-20T17:45:02+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: route Gen195 GWT causal bottleneck falsifiers

`baunotiz-git-8aaa9fc1b034ecfcbd119b59ab78e6860b622c4c` · baunotiz · git-commit · 2026-08-20T17:45:02+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: route Gen195 GWT causal bottleneck falsifiers

### claycode supervisor: steer Gen190 GWT competition and receipt split-brain

`baunotiz-bauverlauf-d7b12eb4f7872df6209e` · baunotiz · bauverlauf.jsonl · 2026-08-20T16:55:53+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: steer Gen190 GWT competition and receipt split-brain

`baunotiz-git-4477d1d4fec2a3bb9e1a92776d48404e9e0f8b76` · baunotiz · git-commit · 2026-08-20T16:55:53+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: steer Gen190 GWT competition and receipt split-brain

### research: route Gen190 GWT competition falsifiers

`baunotiz-bauverlauf-89fb42ef3a1485bf47fa` · baunotiz · bauverlauf.jsonl · 2026-08-20T16:47:32+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: route Gen190 GWT competition falsifiers

`baunotiz-git-461fee36147f89304f9c11bef8cb74f72c48eda7` · baunotiz · git-commit · 2026-08-20T16:47:32+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: route Gen190 GWT competition falsifiers

### claycode supervisor: bind Gen188 receipt split-brain and question-nearness frontier

`baunotiz-bauverlauf-5ec07596ac102aeb5a47` · baunotiz · bauverlauf.jsonl · 2026-08-20T16:00:25+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen188 receipt split-brain and question-nearness frontier

`baunotiz-git-a39cf04ba5ad2e91ad4cee7a265f6e6083e87bc5` · baunotiz · git-commit · 2026-08-20T16:00:25+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen188 receipt split-brain and question-nearness frontier

### research: route Gen188 question-nearness and receipt split-brain impulse

`baunotiz-bauverlauf-af07c7a431f7f210690c` · baunotiz · bauverlauf.jsonl · 2026-08-20T15:47:29+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: route Gen188 question-nearness and receipt split-brain impulse

`baunotiz-git-86f1a61563b4a1b1232f33e294b557c4d31ed447` · baunotiz · git-commit · 2026-08-20T15:47:29+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: route Gen188 question-nearness and receipt split-brain impulse

### research: expose Gen186 timeout mirage and anti-echo falsifiers

`baunotiz-bauverlauf-c38c5e85564f93e7f0a6` · baunotiz · bauverlauf.jsonl · 2026-08-20T14:52:19+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_


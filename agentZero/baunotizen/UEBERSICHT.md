# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-20T15:41:16Z. **3098 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-20T21:50:09+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 3000 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 1890 |
| baunotiz | bauverlauf.jsonl | 1065 |
| baunotiz | github-ereignis | 40 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 3098 · Gegenhypothese: 0 von 3098

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### research: route Gen204 identity and provenance falsifiers

`baunotiz-bauverlauf-693cf4e26304cf64f62e` · baunotiz · bauverlauf.jsonl · 2026-08-20T21:50:09+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: route Gen204 identity and provenance falsifiers

`baunotiz-git-8946d67b1320928ed8199adf5680da64a581b2d7` · baunotiz · git-commit · 2026-08-20T21:50:09+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: route Gen204 identity and provenance falsifiers

### research: bind Gen204 content-prefix identity aliasing falsifier

`baunotiz-bauverlauf-3509e57d32798e2ebce8` · baunotiz · bauverlauf.jsonl · 2026-08-20T21:47:53+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen204 content-prefix identity aliasing falsifier

`baunotiz-git-6a5f143931db33e56aaec57f3af89fb99e829d83` · baunotiz · git-commit · 2026-08-20T21:47:53+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen204 content-prefix identity aliasing falsifier

### claycode supervisor: bind Gen204 persistent GWT bypass and 664/1 frontier

`baunotiz-bauverlauf-7ee1858581e05adbcc47` · baunotiz · bauverlauf.jsonl · 2026-08-20T21:44:59+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen204 persistent GWT bypass and 664/1 frontier

`baunotiz-git-fb37cb498e61855b2d1052c1a096fb12203b2b3e` · baunotiz · git-commit · 2026-08-20T21:44:59+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen204 persistent GWT bypass and 664/1 frontier

### claycode supervisor: bind Gen201 GWT globality bypass frontier

`baunotiz-bauverlauf-027d3c5c3b855c8070a5` · baunotiz · bauverlauf.jsonl · 2026-08-20T20:55:29+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen201 GWT globality bypass frontier

`baunotiz-git-31408b5d7032d549f2ce5179d7d14fb5152a14ee` · baunotiz · git-commit · 2026-08-20T20:55:29+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen201 GWT globality bypass frontier

### research: route Gen201 morphology and possibility-filter falsifiers

`baunotiz-bauverlauf-4a2a638296b3bbded801` · baunotiz · bauverlauf.jsonl · 2026-08-20T20:54:19+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: route Gen201 morphology and possibility-filter falsifiers

`baunotiz-git-bbc11c0403889d24e7b825c93289f7d1f95318dc` · baunotiz · git-commit · 2026-08-20T20:54:19+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: route Gen201 morphology and possibility-filter falsifiers

### research: route Gen199 workspace sidechannel falsifiers

`baunotiz-bauverlauf-00e62e33901e275f31a3` · baunotiz · bauverlauf.jsonl · 2026-08-20T20:47:08+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: route Gen199 workspace sidechannel falsifiers

`baunotiz-git-62125a1d303107ac215eb7034703fffa4b908a73` · baunotiz · git-commit · 2026-08-20T20:47:08+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: route Gen199 workspace sidechannel falsifiers

### gwt: open global channel audit and hyperposition-bypass task

`baunotiz-bauverlauf-a68cd13a35706966f679` · baunotiz · bauverlauf.jsonl · 2026-08-20T20:37:11+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### gwt: open global channel audit and hyperposition-bypass task

`baunotiz-git-538a2ced95c60df6d63a3b404374cd54e326144c` · baunotiz · git-commit · 2026-08-20T20:37:11+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

gwt: open global channel audit and hyperposition-bypass task

### research: expose hyperposition side-channel in wide GWT workspace

`baunotiz-bauverlauf-bf21cce33bdad1168e5b` · baunotiz · bauverlauf.jsonl · 2026-08-20T20:36:52+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: expose hyperposition side-channel in wide GWT workspace

`baunotiz-git-7246d6c9fcc7226ddbb37dfb1635b17bbcd1c809` · baunotiz · git-commit · 2026-08-20T20:36:52+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: expose hyperposition side-channel in wide GWT workspace

### gwt: open stable identity and outcome-credit remediation

`baunotiz-bauverlauf-982b13a1863bb729778d` · baunotiz · bauverlauf.jsonl · 2026-08-20T20:35:25+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### gwt: open stable identity and outcome-credit remediation

`baunotiz-git-f84170d74bc0cd71c65078b2915ce096987d71bf` · baunotiz · git-commit · 2026-08-20T20:35:25+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

gwt: open stable identity and outcome-credit remediation

### research: derive stable GWT identities and split uptake from outcome credit

`baunotiz-bauverlauf-7807f8f5df0e7512819f` · baunotiz · bauverlauf.jsonl · 2026-08-20T20:35:08+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: derive stable GWT identities and split uptake from outcome credit

`baunotiz-git-46bff29fb32e0992dba64d5666483b835bdc213a` · baunotiz · git-commit · 2026-08-20T20:35:08+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: derive stable GWT identities and split uptake from outcome credit

### gwt: open lexical-boundary and evidence-mass falsifier task

`baunotiz-bauverlauf-cf33821bdfe94a53a55e` · baunotiz · bauverlauf.jsonl · 2026-08-20T20:31:17+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### gwt: open lexical-boundary and evidence-mass falsifier task

`baunotiz-git-7f5e42bcbc3acd36e6ebdc5e856e0bef9a6014b8` · baunotiz · git-commit · 2026-08-20T20:31:17+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

gwt: open lexical-boundary and evidence-mass falsifier task

### research: bind GWT lexical-boundary falsifier and evidence-mass challenger

`baunotiz-bauverlauf-c866c6bf9c9d09f56eea` · baunotiz · bauverlauf.jsonl · 2026-08-20T20:30:15+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind GWT lexical-boundary falsifier and evidence-mass challenger

`baunotiz-git-20d221f94a7f928df80a89198fdb43955b8488bd` · baunotiz · git-commit · 2026-08-20T20:30:15+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind GWT lexical-boundary falsifier and evidence-mass challenger

### research: route Gen197 feedback-channel path split

`baunotiz-bauverlauf-1c2621ed76cb057d9a1e` · baunotiz · bauverlauf.jsonl · 2026-08-20T19:52:22+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_


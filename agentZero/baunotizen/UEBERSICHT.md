# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-20T11:11:16Z. **3014 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-20T16:55:53+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 2916 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 1848 |
| baunotiz | bauverlauf.jsonl | 1023 |
| baunotiz | github-ereignis | 40 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 3014 · Gegenhypothese: 0 von 3014

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

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

### research: expose Gen186 timeout mirage and anti-echo falsifiers

`baunotiz-git-ece8c89241eb2c9c974ab5d40ca7572fb34a967c` · baunotiz · git-commit · 2026-08-20T14:52:19+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: expose Gen186 timeout mirage and anti-echo falsifiers

### claycode supervisor: bind Gen186 anti-echo retrieval and prestage source mechanisms

`baunotiz-bauverlauf-ba25626d3668b60df4fc` · baunotiz · bauverlauf.jsonl · 2026-08-20T14:44:13+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen186 anti-echo retrieval and prestage source mechanisms

`baunotiz-git-180307808bf32cb38ddb38a2f7d4f861511d52f0` · baunotiz · git-commit · 2026-08-20T14:44:13+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen186 anti-echo retrieval and prestage source mechanisms

### research: route Gen184 semantic shedding and overflow falsifiers

`baunotiz-bauverlauf-861f2f83e8872e966ec6` · baunotiz · bauverlauf.jsonl · 2026-08-20T13:59:02+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: route Gen184 semantic shedding and overflow falsifiers

`baunotiz-git-ab21989a6ee973379d5f1cef8c2d5974763104c6` · baunotiz · git-commit · 2026-08-20T13:59:02+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: route Gen184 semantic shedding and overflow falsifiers

### claycode supervisor: bind Gen184 CSWT-Z epistemic transport counterevidence

`baunotiz-bauverlauf-2ecf2286c2930b570395` · baunotiz · bauverlauf.jsonl · 2026-08-20T13:44:57+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen184 CSWT-Z epistemic transport counterevidence

`baunotiz-git-f3a55609bdeb97be677a4b0ef747795dbfbd25a9` · baunotiz · git-commit · 2026-08-20T13:44:57+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen184 CSWT-Z epistemic transport counterevidence

### research: route Gen182 epistemic transport and budget falsifiers

`baunotiz-bauverlauf-a13e458887adcd29fd8f` · baunotiz · bauverlauf.jsonl · 2026-08-20T12:59:23+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: route Gen182 epistemic transport and budget falsifiers

`baunotiz-git-a6c36049c31dc673fc965fe972be03e753ed3ab1` · baunotiz · git-commit · 2026-08-20T12:59:23+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: route Gen182 epistemic transport and budget falsifiers

### research: fuse Gen182 CSWT-Z pilot and post-pilot architecture delta

`baunotiz-bauverlauf-afc61f9be262116c33e2` · baunotiz · bauverlauf.jsonl · 2026-08-20T12:50:39+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: fuse Gen182 CSWT-Z pilot and post-pilot architecture delta

`baunotiz-git-afb8b26bbcf1203f8be2866b87f5b3917fbefb6b` · baunotiz · git-commit · 2026-08-20T12:50:39+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: fuse Gen182 CSWT-Z pilot and post-pilot architecture delta

### research: bind AgentZero atomic receipt and hierarchy causality delta

`baunotiz-bauverlauf-5c29fad39dc66be90ed9` · baunotiz · bauverlauf.jsonl · 2026-08-20T11:47:21+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind AgentZero atomic receipt and hierarchy causality delta

`baunotiz-git-ab8198736ba105709989a2e5174a68531227de36` · baunotiz · git-commit · 2026-08-20T11:47:21+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind AgentZero atomic receipt and hierarchy causality delta

### research: bind Gen182 test-metrology recovery and DB observer effect

`baunotiz-bauverlauf-02bcc39e1bd5129e8758` · baunotiz · bauverlauf.jsonl · 2026-08-20T11:45:21+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### research: bind Gen182 test-metrology recovery and DB observer effect

`baunotiz-git-39a132e56973c536f9beb67fcb85fb8a10693e30` · baunotiz · git-commit · 2026-08-20T11:45:21+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

research: bind Gen182 test-metrology recovery and DB observer effect

### claycode supervisor: fail closed on Gen182 null receipts

`baunotiz-bauverlauf-e0fe6e16c80ed63d54e6` · baunotiz · bauverlauf.jsonl · 2026-08-20T10:47:40+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_


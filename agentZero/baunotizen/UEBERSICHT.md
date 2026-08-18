# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-18T20:11:08Z. **2564 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-19T02:44:48+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 2466 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 1623 |
| baunotiz | bauverlauf.jsonl | 799 |
| baunotiz | github-ereignis | 39 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 2564 · Gegenhypothese: 0 von 2564

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **0** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### claycode supervisor: bind Gen107 583/1 and stale security acceptance

`baunotiz-git-3beb76ffb6f05a43aa192b568956fd4626bead06` · baunotiz · git-commit · 2026-08-19T02:44:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen107 583/1 and stale security acceptance

### claycode supervisor: prioritize Gen106 root-escape boundary and 582/2 provenance

`baunotiz-bauverlauf-3faddb404908563a8eb7` · baunotiz · bauverlauf.jsonl · 2026-08-19T00:56:16+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: prioritize Gen106 root-escape boundary and 582/2 provenance

`baunotiz-git-ea6dd49f49d68b763c328203c9c4af373d071d15` · baunotiz · git-commit · 2026-08-19T00:56:16+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: prioritize Gen106 root-escape boundary and 582/2 provenance

### claycode supervisor: bind Gen105 service and MCP capability closure

`baunotiz-git-857c60ef4f5a420eae316e03032278b5672f463a` · baunotiz · git-commit · 2026-08-18T23:47:20+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen105 service and MCP capability closure

### claycode supervisor: bind Gen105 service and MCP capability closure

`baunotiz-bauverlauf-b75edfdc09e274685bde` · baunotiz · bauverlauf.jsonl · 2026-08-18T23:47:20+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen100 prestage repair and remaining action-spine reds

`baunotiz-bauverlauf-34e908f208bfe694901b` · baunotiz · bauverlauf.jsonl · 2026-08-18T22:46:49+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen100 prestage repair and remaining action-spine reds

`baunotiz-git-3ae0af7050c00a45117bfb6eb062d79b246463f8` · baunotiz · git-commit · 2026-08-18T22:46:49+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen100 prestage repair and remaining action-spine reds

### claycode supervisor: bind Gen93 persistent prestage contract frontier

`baunotiz-bauverlauf-6fbb9b73d219d81d40d6` · baunotiz · bauverlauf.jsonl · 2026-08-18T21:46:59+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen93 persistent prestage contract frontier

`baunotiz-git-7db6448d9eb09c45035486c414f50bce56777235` · baunotiz · git-commit · 2026-08-18T21:46:59+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen93 persistent prestage contract frontier

### claycode supervisor: steer Gen85 Mistral prestage regression

`baunotiz-bauverlauf-a058ed244d15c3dd5eb7` · baunotiz · bauverlauf.jsonl · 2026-08-18T20:39:11+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: steer Gen85 Mistral prestage regression

`baunotiz-git-d67181b6978ac1ae9227ce3d171805995cded428` · baunotiz · git-commit · 2026-08-18T20:39:11+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: steer Gen85 Mistral prestage regression

### Neun rote Tests aufgeloest -- zwei davon wurden dabei strenger

`baunotiz-git-c43a3fefccdc018d19f0a1aff2d147b4c44daf6b` · baunotiz · git-commit · 2026-08-18T19:47:36+00:00 · EntityOS

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

Neun rote Tests aufgeloest -- zwei davon wurden dabei strenger

584 gruen, 0 rot (vorher 570 gruen, 9 rot). Keiner durch Loeschen, Ueberspringen
oder abgeschwaechte Behauptungen.

SIEBEN VON NEUN HATTEN EINE URSACHE. Alle scheiterten mit
`StaleGeneration: effect_active_turn`: `ClayVerseEngine._ingest_locked` legte
keine Zeile in `active_turns` an, die das Wirkungstor verlangt. Das Tor kam mit
dem Zug-Lebenszyklus; der aeltere Weg hat es nie gelernt, und im Betrieb fiel
das nicht auf, weil ihn dort niemand mehr aufruft -- ausser einem:
final_acceptance_probe, der ENDABNAHME. Genau das Instrument, das beweisen
soll, dass Wirkungen funktionieren, konnte selbst nicht messen. Es meldete
nicht "Wirkung fehlgeschlagen", sondern scheiterte VOR der Wirkung.

Die Reparatur lockert das Tor NICHT. Ein `if episode_id is None`-Zweig haette
alle sieben gruen gemacht und die Pruefung genau fuer den Weg abgeschaltet,
dessen Zweck das Pruefen ist. Stattdessen meldet engine.py den lebenden Zug
jetzt an und wieder ab, wie der Betriebsweg.

EIN ECHTES LECK, gefunden ueber einen Test, der aus dem FALSCHEN Grund rot war.
test_memory_privacy forderte, dass die Verdichtung den Rohtext ueberschreibt.
Am 18.08. wurde compact() bewusst auf additiv umgebaut -- turns ist ein
fortschreibendes Kausalbuch, das Ueberschreiben vernichtete die einzige Kopie
des Originals. Die alte Zusicherung hing damit an einer NEBENWIRKUNG, und beim
Umbau ist sie niemandem mitgewandert.

Sie war verletzt: in WorldAssembler.as

### agentZero-Export 2026-08-18T19:41:06Z (Generation 107, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-86d356687bd843594dd3715c7503968ad13be1dd` · baunotiz · git-commit · 2026-08-18T19:41:49+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-18T19:41:06Z (Generation 107, 59 Dateien, 1 geschwaerzt)

### claycode supervisor: classify Gen80 PTY lease as reproducibility flake candidate

`baunotiz-bauverlauf-d29252642b0d6565e56a` · baunotiz · bauverlauf.jsonl · 2026-08-18T19:39:12+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: classify Gen80 PTY lease as reproducibility flake candidate

`baunotiz-git-6f26c6140c09a8783c211be39e6456cd5592cf66` · baunotiz · git-commit · 2026-08-18T19:39:12+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: classify Gen80 PTY lease as reproducibility flake candidate

### agentZero-Export 2026-08-18T19:11:06Z (Generation 106, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-5691ee2588d50fe21b3963b155e34227a49695ea` · baunotiz · git-commit · 2026-08-18T19:11:48+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-18T19:11:06Z (Generation 106, 59 Dateien, 1 geschwaerzt)

### agentZero-Export 2026-08-18T19:11:06Z (Generation 106, 59 Dateien, 1 geschwaerzt)

`baunotiz-bauverlauf-8d5baefc96fed2024c31` · baunotiz · bauverlauf.jsonl · 2026-08-18T19:11:48+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: steer Gen80 semantic-memory emergence and receipt drift

`baunotiz-bauverlauf-ab8f8081d673cd7185e7` · baunotiz · bauverlauf.jsonl · 2026-08-18T18:44:14+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: steer Gen80 semantic-memory emergence and receipt drift

`baunotiz-git-9fc1f3ccee7c2dc4f54fd5b7e89c31a8106ed7e0` · baunotiz · git-commit · 2026-08-18T18:44:14+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: steer Gen80 semantic-memory emergence and receipt drift

### agentZero-Export 2026-08-18T18:41:06Z (Generation 106, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-ed2da57901096a55a716400a51cef245794c161e` · baunotiz · git-commit · 2026-08-18T18:41:44+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-18T18:41:06Z (Generation 106, 59 Dateien, 1 geschwaerzt)

### agentZero-Export 2026-08-18T18:41:06Z (Generation 106, 59 Dateien, 1 geschwaerzt)

`baunotiz-bauverlauf-5b2057e1a9c2f3a7e7c0` · baunotiz · bauverlauf.jsonl · 2026-08-18T18:41:44+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentZero-Export 2026-08-18T18:11:06Z (Generation 106, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-dd57045d635dc17839b3c8fa35cc0c5265d8b742` · baunotiz · git-commit · 2026-08-18T18:11:56+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-18T18:11:06Z (Generation 106, 59 Dateien, 1 geschwaerzt)

### agentZero-Export 2026-08-18T18:11:06Z (Generation 106, 59 Dateien, 1 geschwaerzt)

`baunotiz-bauverlauf-bc66dba04c3fa8515045` · baunotiz · bauverlauf.jsonl · 2026-08-18T18:11:56+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentZero-Export 2026-08-18T17:41:06Z (Generation 106, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-c9387825c64461cf8d082195c39ac44df60f9144` · baunotiz · git-commit · 2026-08-18T17:41:49+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-18T17:41:06Z (Generation 106, 59 Dateien, 1 geschwaerzt)

### agentZero-Export 2026-08-18T17:41:06Z (Generation 106, 59 Dateien, 1 geschwaerzt)

`baunotiz-bauverlauf-94c09645610ea18ae79d` · baunotiz · bauverlauf.jsonl · 2026-08-18T17:41:49+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_


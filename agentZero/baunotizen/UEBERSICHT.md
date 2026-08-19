# Baunotizen -- Aggregat und Stichprobe

Automatisch erzeugt 2026-08-19T04:41:09Z. **2624 Zeilen** insgesamt in `artikel` (art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.

Zeitraum: `2026-08-14T00:00:00+00:00` bis `2026-08-19T10:44:08+07:00`.

## Nach Art

| Art | Anzahl |
|---|---|
| baunotiz | 2526 |
| vorfall | 98 |

## Nach Quelle (`von_quelle`)

| Art | von_quelle | Anzahl |
|---|---|---|
| baunotiz | git-commit | 1653 |
| baunotiz | bauverlauf.jsonl | 829 |
| baunotiz | github-ereignis | 39 |
| baunotiz | github-ereignis-tag | 5 |
| vorfall | strom | 90 |
| vorfall | journal | 6 |
| vorfall | vorfall-aufzeichnung | 2 |

## Hypothese: 0 von 2624 · Gegenhypothese: 0 von 2624

> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** `hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler im Export.

> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und zusaetzlich in `metadaten.herkunft` im JSON.

## Privatsphaere-Filter

Von **400** gepruefte juengste Kandidaten wurden **1** verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das betroffene Feld. Das Repo ist OEFFENTLICH.

## Die 25 juengsten (gepruefte) Baunotizen

### agentzeroforschung: bind Gen116 PTY red-green-red-green-red-green

`baunotiz-git-9ab0fcf3405d4dee92fa3b8804ecd351054e50a0` · baunotiz · git-commit · 2026-08-19T10:44:08+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentzeroforschung: bind Gen116 PTY red-green-red-green-red-green

### agentzeroforschung: bind Gen116 PTY red-green-red-green-red-green

`baunotiz-bauverlauf-ebf28f9445b1d173e720` · baunotiz · bauverlauf.jsonl · 2026-08-19T10:44:08+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentzeroforschung: classify Gen116 PTY lease oscillation

`baunotiz-bauverlauf-6fca3a9e7dd2507c7521` · baunotiz · bauverlauf.jsonl · 2026-08-19T09:47:43+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentzeroforschung: classify Gen116 PTY lease oscillation

`baunotiz-git-b643704e7245d1e9cb3302c5ef1db2bd5e5d6b52` · baunotiz · git-commit · 2026-08-19T09:47:43+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentzeroforschung: classify Gen116 PTY lease oscillation

### claycode supervisor: bind Gen116 PTY red-green nondeterminism

`baunotiz-bauverlauf-75383d1b7c91931e4422` · baunotiz · bauverlauf.jsonl · 2026-08-19T08:40:29+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen116 PTY red-green nondeterminism

`baunotiz-git-56802f61263e4cda9795618a9e6a3f7d65c12542` · baunotiz · git-commit · 2026-08-19T08:40:29+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen116 PTY red-green nondeterminism

### claycode supervisor: bind Gen116 recurring PTY lease red

`baunotiz-bauverlauf-400aaca708050a6b42bf` · baunotiz · bauverlauf.jsonl · 2026-08-19T07:41:13+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen116 recurring PTY lease red

`baunotiz-git-66a6c46f5918ffeaa36f432de369c34b21877e6c` · baunotiz · git-commit · 2026-08-19T07:41:13+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen116 recurring PTY lease red

### agentzeroforschung: bind Gen116 stable 583/1 growth frontier

`baunotiz-bauverlauf-e2951bf2c9cb5bde2ad7` · baunotiz · bauverlauf.jsonl · 2026-08-19T05:48:36+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentzeroforschung: bind Gen116 stable 583/1 growth frontier

`baunotiz-git-c5ef966b728d493295051d2209e7de89fa46d24c` · baunotiz · git-commit · 2026-08-19T05:48:36+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentzeroforschung: bind Gen116 stable 583/1 growth frontier

### claycode supervisor: bind Gen116 durable adapter red and capability-audit truth gaps

`baunotiz-bauverlauf-d185b210443afa86415e` · baunotiz · bauverlauf.jsonl · 2026-08-19T04:55:54+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen116 durable adapter red and capability-audit truth gaps

`baunotiz-git-a9fe30c8803257c8f69c22259473de3be3d07401` · baunotiz · git-commit · 2026-08-19T04:55:54+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen116 durable adapter red and capability-audit truth gaps

### agentzeroforschung: index Gen116 adapter evidence correction

`baunotiz-bauverlauf-9bd86f9bfa49d0e9fc39` · baunotiz · bauverlauf.jsonl · 2026-08-19T04:46:47+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentzeroforschung: index Gen116 adapter evidence correction

`baunotiz-git-d825c9453cf27d9aefd4fe2f3b813a0f6c4b53b7` · baunotiz · git-commit · 2026-08-19T04:46:47+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentzeroforschung: index Gen116 adapter evidence correction

### agentzeroforschung: correct Gen116 adapter evidence and 584/0 narrative drift

`baunotiz-bauverlauf-37f7d7625e889765ab83` · baunotiz · bauverlauf.jsonl · 2026-08-19T04:46:24+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentzeroforschung: correct Gen116 adapter evidence and 584/0 narrative drift

`baunotiz-git-d9371059b2995dfb3c193e277016a01ad644d5ef` · baunotiz · git-commit · 2026-08-19T04:46:24+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentzeroforschung: correct Gen116 adapter evidence and 584/0 narrative drift

### agentZero-Export 2026-08-19T04:11:08Z (Generation 120, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-054df0a06c5b483c378d14f9dc9c2f6de1dc3e08` · baunotiz · git-commit · 2026-08-19T04:12:43+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T04:11:08Z (Generation 120, 59 Dateien, 1 geschwaerzt)

### seite_diagnose: Zero trennt server-seitig von client-seitig

`baunotiz-bauverlauf-faa4882fb4f6d610cb91` · baunotiz · bauverlauf.jsonl · 2026-08-19T03:45:59+00:00 · EntityOS

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

ANLASS (Gabriel 19.08.): "weder seimensch.net noch leihmich ist erreichbar" ...
"sowas muss zero auch checken".

DER AUSFALL, geschichtet diagnostiziert: der Server war KERNGESUND -- HTTP 200
in 0,07s, echter Inhalt, oeffentliches DNS korrekt auf <adresse>. Die
Ursache lag auf Gabriels Kiste: eine Zeile in /etc/hosts leitete seimensch.net,
leihmich.org und herzrad.at auf <adresse> (localhost) um -- Rest eines toten
SSH-Tunnels vom 11.08., als der Direktweg zum VPS gesperrt war. Der Direktweg
ging inzwischen wieder (HTTPS 200 direkt geprueft), der Tunnel war tot, die
Umleitung schickte ins Leere. Fix: die hosts-Zeile auskommentieren (braucht
Gabriels Schranke-Freigabe, weil Systempfad -- die Schranke griff korrekt).

DIE LEHRE, jetzt fest verdrahtet: "erreichbar" ist kein Ja/Nein, sondern ein
VON WO. Eine Seite kann vom Server aus leben und von einem Rechner aus tot
sein. Die haeufigste falsche Erstreaktion ist "Server neu starten" -- meistens
ist der Server gesund und das Problem sitzt zwischen Mensch und Server.
`seite_pruefen` blickte nur von einem Standpunkt; das reichte nicht.

GEBAUT: seite_diagnose(url). Prueft geschichtet und TRENNT server-seitig von
client-seitig: oeffentliches DNS -> erwartete IP -> Port 443 -> HTTPS-Status ->
echter Inhalt (Titel, Groesse, nicht 200-Fehlerseite). Urteil-Logik:
- Server gruen + DNS richtig -> es liegt am MENSCHEN. Namentlich genannt: (1)
  /etc/hosts-Umleitung auf 127.0.0.x, `getent hosts <domain>` MUSS die echte IP
  zeigen; (2) Pro

### agentZero-Export 2026-08-19T03:41:08Z (Generation 117, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-4c7b410f2704367f6179d3c4a62507a9fa262d35` · baunotiz · git-commit · 2026-08-19T03:43:46+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T03:41:08Z (Generation 117, 59 Dateien, 1 geschwaerzt)

### agentZero-Export 2026-08-19T03:41:08Z (Generation 117, 59 Dateien, 1 geschwaerzt)

`baunotiz-bauverlauf-36557502c1b1cb923af2` · baunotiz · bauverlauf.jsonl · 2026-08-19T03:43:46+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen111 transient zero-red and Andreas E2E truth failures

`baunotiz-git-a591e40e29d9ddb9f4d35dcfe3691f37f9034977` · baunotiz · git-commit · 2026-08-19T03:41:31+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen111 transient zero-red and Andreas E2E truth failures

### claycode supervisor: bind Gen111 transient zero-red and Andreas E2E truth failures

`baunotiz-bauverlauf-a769c7cb4251dd7fc691` · baunotiz · bauverlauf.jsonl · 2026-08-19T03:41:31+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### agentZero-Export 2026-08-19T03:11:08Z (Generation 116, 59 Dateien, 1 geschwaerzt)

`baunotiz-git-5a2cbb3916235dab9811d0053fde94064cb53dcb` · baunotiz · git-commit · 2026-08-19T03:11:43+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

agentZero-Export 2026-08-19T03:11:08Z (Generation 116, 59 Dateien, 1 geschwaerzt)

### agentZero-Export 2026-08-19T03:11:08Z (Generation 116, 59 Dateien, 1 geschwaerzt)

`baunotiz-bauverlauf-56f704d6523b91a46161` · baunotiz · bauverlauf.jsonl · 2026-08-19T03:11:43+00:00 · agentZero

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

_(kein Text)_

### claycode supervisor: bind Gen107 583/1 and stale security acceptance

`baunotiz-git-3beb76ffb6f05a43aa192b568956fd4626bead06` · baunotiz · git-commit · 2026-08-19T02:44:48+07:00 · Gabriel Gschaider

Hypothese: _(keine -- s.o.)_ · Gegenhypothese: _(keine -- s.o.)_

claycode supervisor: bind Gen107 583/1 and stale security acceptance


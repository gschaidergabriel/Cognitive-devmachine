# Generation 211 — Warm-Pool-Sitzungsrouting und Systemprompt-Race

## Gebundener Stand

- AgentZero-Export: `0c51fafa33911092acb2c1d76ae94b7bcdd6d95c`
- Export-Tree: `4bd0a73306e809cf3f572d83c11fdc0af728b248`
- Generation: 211
- direkter Test-Receipt: `693 gruen / 1 rot`
- verbleibender Red: `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`
- Receipt-Source short: `9e45b0c97`
- lokale EOS-Chronik bindet Prefix `9e45b0c97f28`; Full-40-SHA/Tree/Executor bleibt ungebunden.

## Echter Mechanismusfortschritt seit Gen207

`warm_zero.py` leitet die Warm-Pool-Sitzungen jetzt aus `identity.CANONICAL_USERS` + `identity.sitzungen_von(uid)` ab, statt je Mensch nur einen fest verdrahteten Slot zu kennen. Dazu kommen ein globales `WARM_BUDGET`, Priorisierung zuletzt benutzter Sitzungen und Weiterverwendung noch nicht warmer Pool-Kandidaten. Das schliesst den gemessenen Fehler, dass vier warme Prozesse laufen konnten, waehrend der reale Chat auf Platz 2 immer kalt fiel.

Mechanismus-Credit: JA.
Finaler Availability-/Isolation-Credit: NEIN.

## Neuer harter Race-Kandidat: SESSION_PROMPT_FILE_ALIASING

Die neue Mehr-Sitzungsfaehigkeit trifft auf eine alte Dateinamensannahme:

- `_sysdatei()` cached logisch nach `(user, session)`;
- der physische Pfad lautet aber fuer alle Sitzungen desselben Menschen identisch `/tmp/zero-warm-sys-{user}.md`;
- `_systemanweisung(db_path, user_id, session_id)` ist nachweislich sitzungsspezifisch, weil sie `_anwesenheitsblock(..., session_id)` einbettet;
- mehrere Warmprozesse eines Menschen koennen damit verschiedene sitzungsspezifische Inhalte unter demselben Dateinamen erzeugen.

Damit existiert mindestens ein TOCTOU-/Alias-Risiko: Session A schreibt ihre Systemanweisung, Session B ueberschreibt denselben Pfad, waehrend A/B-Prozesse gebootet werden bzw. die CLI den `--append-system-prompt-file`-Inhalt liest. Wenn Claude Code die Datei nicht garantiert atomar vor dem konkurrierenden Rewrite snapshotet, kann ein Prozess den Anwesenheitsblock der falschen Sitzung erhalten.

Das ist sicherheits- und identitaetsrelevant: ein warmer Prozess darf niemals Sitzungsidentitaet, Anwesenheitsbeleg oder per-Session-Rahmen eines anderen Slots erben.

## Hoestwertiger Falsifikator: WARM_SESSION_PROMPT_IDENTITY_RECEIPT/v1

Auf einem isolierten Exact-Checkout-Ubuntu-Lauf fuer EINEN User mit zwei kanonischen Sessions:

1. Session A und B erhalten absichtlich eindeutig unterschiedliche Anwesenheitsmarker.
2. Beide Warmprozesse werden wiederholt und kontrolliert ueberlappend gebootet.
3. Fuer jeden Prozess werden gebunden: `user_id`, `session_id`, Systemprompt-Pfad, Prompt-Digest, argv-Digest, Spawn-Zeit, Zeitpunkt der Datei-Erzeugung und der erste beobachtete Modell/System-Kontextbeleg.
4. 100+ alternierende/ueberlappende Starts; zusaetzlich kontrollierte Scheduler-/I/O-Last.
5. Harte Invariante: `prompt_digest(session A) != prompt_digest(session B)` und jeder Prozess muss exakt den Digest seiner eigenen Session tragen.
6. Jeder Cross-Session-Mismatch ist FAIL; kein Retry darf ihn verdecken.

## Minimaler Architekturfix, falls reproduziert

Den physischen Promptpfad provenance-bindend machen, z. B. nach stabiler `user_id + session_id`-Identitaet oder direkt content-addressed (`sha256(system_prompt)`). Datei atomar schreiben (`tempfile` + `os.replace`) und den unveraenderlichen Pfad dem Prozess uebergeben. Optional die Datei erst nach Prozessende freigeben. Nicht nur den Cache-Key korrigieren — der Dateiname selbst ist die kollidierende Ressource.

## Weitere Grenzen

- Gen211 verbessert 685/2 -> 693/1 gegenueber Gen207, aber PTY-Gruen bekommt wegen der langen Rot/Grün-Oszillation ohne atomare Exact-Source-/Environment-Bindung weiterhin 0 Fix-Credit.
- Der persistente Claude-Code-Adapter-Red bleibt der deterministische Hauptfrontier.
- `TEST_EXPORT_ATOMIC_RECEIPT/v1`, Full Commit+Tree und Executor-/Environment-Digest fehlen weiterhin.
- Warm-Deadlines/Circuit-Breaker verwenden weiterhin `time.time()`; monotone Deadline-/Clock-step-Falsifikation bleibt offen.

## Naechster Forschungsfrontier

1. `WARM_SESSION_PROMPT_IDENTITY_RECEIPT/v1` ausfuehren.
2. Falls Alias reproduziert: provenance-/content-addressed Promptdateien implementieren und erneut falsifizieren.
3. Parallel den persistenten Adapter-Test in `toolless`, `ephemeral`, `structured-output`, `environment/HOME isolation` zerlegen.
4. Test-/ZIELE-/Export-Akzeptanz weiterhin nur aus einem atomaren Exact-Source-Receipt ableiten.

Whole Clay Machine: **NOT CLAIMED**.

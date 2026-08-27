# Generation 232 — Service-Recovery und Same-User-Datei-Alias

## Gebundener Stand

- AgentZero Export: `10aa920cb3be2611a6f7a5aa009ad3868b99403a`
- Generation: 232
- Test-Receipt: 937 gruen / 1 rot
- verbleibend rot: `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`
- Source-Short: `f702cc24f` — Full Commit+Tree/Dirty-State/Executor weiter ungebunden.

## 1. Pflichtdienste: Recovery ist kein Root-Cause-Credit

Gen227 meldete 3/4 Pflichtdienste und `verdichtung` mit 6/6 fehlgeschlagenen gezündeten Bahnen. Gen232 meldet wieder 4/4 Pflichtdienste und `verdichtung` 3/3 wirksam.

Das ist betriebliche Recovery, aber keine Ursachenklärung. Bis ein `MANDATORY_SERVICE_LIVENESS_RECEIPT/v1` Fehler- und Recovery-Epoche pro Bahn bindet, bleibt Service-Liveness-Acceptance = 0. Der Receipt muss mindestens Provider/Modell, FREE_ONLY-Admission, Requestzeiten, Transport/Auth/Rate-Limit/Netzklassifikation, Input-/Output-Digests, DB-Write und Recoveryzustand enthalten.

## 2. Source-confirmed Same-User Cross-Session Attachment Alias

`agentZero/code/produkt/dateien.py` speichert Zero-Ausgaben unter `ausgabe/<user_id>/`. `anhaenge_seit(user_id, seit_epoch)` liefert danach *alle* Dateien dieses Users mit `mtime >= seit_epoch`.

Der Chat-Pfad bindet die Anhangsuche an den Zugbeginn und den kanonischen `user_id`, nicht an `session_id` oder `turn_id`.

Damit existiert folgende deterministische Alias-Klasse:

1. Session A desselben Users startet Turn A bei `t0`.
2. Session B desselben Users erzeugt nach `t0` Datei B im gemeinsamen `ausgabe/<user_id>/`.
3. Turn A beendet sich später und ruft die zeitfensterbasierte Anhangsuche auf.
4. Datei B erfüllt das Zeitkriterium und kann Turn A zugerechnet werden, obwohl sie nicht aus Turn A stammt.

Das ist source-confirmed Attribution-Risk, aber noch kein ausgeführter Disclosure-Receipt. Cross-User-Isolation ist davon getrennt und bleibt durch getrennte User-Verzeichnisse stärker geschützt.

## 3. Falsifikator: FILE_ATTACHMENT_SESSION_ISOLATION_RECEIPT/v1

Zwei parallele Sessions desselben Users plus der andere User als Kontrolle.

Zu binden:
- `user_id`, `session_id`, `turn_id`
- Output-Pfad und Datei-ID
- Creation-Receipt mit monotonic timestamp + mtime
- Inhaltsdigest
- Attachment-Liste je Antwort
- Download-Authorization-Entscheidung

Harte Invarianten:
- Eine Antwort darf nur Dateien exponieren, die explizit ihrem eigenen Turn/Session-Receipt zugeordnet wurden.
- Same-user concurrency darf keine Cross-Attachment-Zuordnung erzeugen.
- Cross-user Download bleibt fail-closed.

## 4. Reparaturklasse

Nicht mit engeren Zeitfenstern oder mtime-Heuristiken reparieren. Bevorzugt: immutable turn/session-addressed Provenance, z. B. `ausgabe/<user_id>/<session_id>/<turn_id>/...` oder ein explizites Creation-Receipt/Manifest, aus dem die Antwort ihre Attachments liest.

Das ist getrennt vom bereits offenen `WARM_SESSION_PROMPT_IDENTITY_RECEIPT/v2`; beide betreffen Same-User-Session-Isolation, aber unterschiedliche Ressourcen.

## Evidenzurteil

- Gen232 Service Recovery: `SERVICE_RECOVERED_SAME_FAMILY`, Acceptance-Credit 0.
- Datei-Session-Alias: `SOURCE_CONFIRMED_CROSS_SESSION_ATTACHMENT_ALIAS`, executable disclosure credit 0.
- Whole EntityOS / Clay Machine: NOT CLAIMED.

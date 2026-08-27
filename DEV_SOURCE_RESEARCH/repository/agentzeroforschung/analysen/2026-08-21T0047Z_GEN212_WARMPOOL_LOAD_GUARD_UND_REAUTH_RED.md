# Generation 212 — Warmpool-Lastschutz und neuer Reauth-Red

## Gebundener Export

- AgentZero-Export: `957babd305801ef325e4931d9137d63884a61c41`
- Generation: 212
- Test-Source: `aa52fb159`
- lokale EntityOS-Chronik: `aa52fb1591e9`
- Exportdauer: 239.1 s

## Harte Befunde

Der direkte Test-Receipt meldet **707 gruen / 2 rot**. Rot sind:

1. `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`
2. `tests/test_terminal_ws_auth_lease_protocol.py::test_reauth_rejects_clerk_session_swap`

Der Claude-Code-Adapter bleibt damit der persistente deterministische Frontier. Der PTY/Auth-Fehler hat dagegen seine sichtbare Form gewechselt: auf dem vorherigen Source `b7c25fbe5` oszillierte vor allem der Lease-Refresh-Test; auf dem neuen Source `aa52fb159` ist jetzt der Session-Swap-Reauth-Test rot. Wegen des Source-Wechsels bekommt dieser neue Red **nicht** automatisch die alte Nichtdeterminismus-Klassifikation. Er ist als `NEW_SOURCE_BOUND_AUTH_RED` zu behandeln, bis er auf identischem Full Commit+Tree/Executor mehrfach reproduziert ist.

## Neuer positiver Mechanismus: keine Warmpool-Nachfuellung waehrend eines laufenden Zugs

`warm_zero.py` fuehrt jetzt einen globalen Zugzaehler ein (`zug_beginnt`, `zug_endet`, `_zug_blockiert_nachfuellen`) und blockiert die Warmpool-Nachfuellung waehrend aktiver Zuege. Der Code dokumentiert dazu einen gemessenen Mechanismus: 2–3 Node-Boots parallel zum Zug liessen den Erwartungsfeld-Faden in 1/3 Zuegen den vollen 2.5-s-Deckel reissen; ohne Bootlast blieb er unter 0.4 s. Ein 20-s-Notausgang verhindert dauerhaftes Aushungern des Pools.

Das ist ein sinnvoller Scheduler-/Contention-Fix: Vorwaermung soll Leerlauf ausnutzen statt die gerade laufende kognitive Pipeline zu stoeren. Credit: **MECHANISM_PRESENT**, noch kein End-to-End-Latenz-PASS.

## Weiterhin offener, source-sichtbarer Defekt: Session-Prompt-Datei-Alias

Der bereits gebundene Warmpool-Identitaetsfehler ist in Gen 212 **noch vorhanden**. `_sysdatei(user, session)` cached logisch nach `(user, session)`, schreibt aber physisch weiterhin fuer alle Sessions desselben Users nach:

`/tmp/zero-warm-sys-{user}.md`

Da `_systemanweisung(..., user, session)` session-spezifisch ist, bleibt ein deterministischer Last-Writer-Wins-/TOCTOU-Kanal bestehen. Der neue Nachfuell-Lastschutz behebt diesen Identitaetsalias **nicht**.

## Neue Hypothese: Scheduler-Fix kann PTY/Auth-Race beeinflussen, aber der aktuelle Reauth-Red ist davon nicht bewiesen

Der neue Warmpool-Guard reduziert konkurrierende Node-Bootlast waehrend aktiver Zuege. Das kann prinzipiell PTY-/Eventloop-Timing stabilisieren. Gleichzeitig ist auf dem neuen Source ein anderer Auth-Test rot. Daraus folgt weder "Guard verursacht den Red" noch "Guard heilt PTY". Beide Hypothesen brauchen identische Exact-Source-Wiederholungen.

## Hoeschstwertige Falsifikatoren

1. **AUTH_SESSION_BINDING_TRACE/v1**
   - Full Commit+Tree `aa52fb159...`
   - Clerk subject/session vor Reauth
   - Clerk subject/session nach Reauth
   - PTY session-id / lease-id
   - erwartete vs akzeptierte Identitaet
   - monotone Zeitpunkte fuer reauth begin/verify/bind/reject
   - mindestens 30 identische Wiederholungen

2. **WARM_SESSION_PROMPT_IDENTITY_RECEIPT/v2**
   - zwei Sessions desselben Users, verschiedene Marker
   - A -> B -> A plus 100+ ueberlappende Boots
   - physischer Promptpfad, content digest, session id, Spawnzeit und vom Prozess gebundener Prompt digest
   - harte Invariante: B darf niemals A-Prompt erben und umgekehrt

3. **WARM_LOAD_INTERFERENCE_RECEIPT/v1**
   - gleicher Prompt, Warmpool refill ON-during-turn vs neuer Guard
   - Erwartungsfeld-Wallclock, CPU, loadavg, runnable processes, late futures
   - p50/p95/p99 fuer Gesamtzug und Teilstufen
   - getrennt von funktionaler Korrektheit auswerten

## Evidenzgrenze

- 707/2 ist ein direkter aktueller Receipt, aber Full 40-SHA+Tree/Dirty-State/Executor-Digest fehlen weiterhin.
- Der neue Reauth-Red ist source-bound an einen neuen Kurz-SHA; deshalb **kein** Transfer der alten PTY-Nondeterminismus-Klassifikation ohne Replikation.
- Der Warmpool-Lastschutz ist source-sichtbar und plausibel, aber noch kein kausaler Latenz-PASS.
- Der Session-Prompt-Datei-Alias bleibt source-sichtbar offen.

## Aktueller Frontier

1. Full EntityOS commit+tree hinter `aa52fb1591e9...` exportieren.
2. `AUTH_SESSION_BINDING_TRACE/v1` auf identischem isolierten Ubuntu wiederholen.
3. Session-Prompt-Datei-Alias separat falsifizieren/fixen.
4. Warmpool-Lastschutz mit einem kontrollierten Latenz-A/B messen.
5. Claude-Code-Adapter weiterhin separat in Toolless/Ephemeral/Structured/Env-Isolation zerlegen.

Whole Clay Machine: **NOT CLAIMED**.

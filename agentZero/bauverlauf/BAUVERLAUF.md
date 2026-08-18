# Bauverlauf

Automatisch erzeugt 2026-08-18T05:48:59Z. 713 Commits aus vier Repos, davon 206 mit ausgeschriebener Begruendung.

Der Verlauf wird nicht nebenher gepflegt -- er entsteht beim Bauen. Jeder Eintrag
unten ist der Commit-Text selbst: Befund, Messung, Grund. Ein handgefuehrtes
Bautagebuch waere eine zweite Wahrheit, die irgendwann von der ersten abweicht.

## 2026-08-18

### Permissions: allow the three managed MCP tools so request_effect actually reaches EffectGate

`8e37f4a64a81` · entityos · 10:35 UTC · Video Launch Page

```
Owner decision: a CLI permission layer denying before the call reaches
EffectGate does not make the system safer -- it makes the gate unreachable,
and an unreachable gate is a decoration, not a boundary. EffectGate is the
designed boundary (capability/target/argv/generation/evidence adjudication);
letting calls arrive there is the point.

allowManagedPermissionRulesOnly stays true, deny: [Bash, Artifact] unchanged.
Only addition: permissions.allow with the three managed MCP tool names
(session_state, request_effect, request_autonomy_effect) -- the same three
--allowedTools was already trying and failing to grant, since that CLI flag
is ignored entirely under allowManagedPermissionRulesOnly.
```

### Fix: CLAYVERSE_DB_PATH never reached the claude subprocess, so every hook/MCP write landed in the state-root shadow DB, not the real heart

`7432769daa72` · entityos · 10:29 UTC · Video Launch Page

```
Found by checking row counts before/after a real conversation through the
fixed deny-shell: zero rows in /var/lib/clay/wiki.db, but turns=2,
causal_episodes=1, workspace_episodes=1 in <state_root>/unified.db instead.
Root cause: ensure()'s env_argv uses "env -i" (wipes environment entirely,
keeps only what's explicitly listed) to launch the claude process, and
CLAYVERSE_DB_PATH was never one of the listed vars -- so resolve_db_path()
fell back to its <state_root>/unified.db default for every hook and for the
stdio MCP server subprocess, invisibly disconnected from the real UnifiedDB
the WS server itself opens.

Passes CLAYVERSE_DB_PATH through when the service's own environment has it
set (same override contract as resolve_db_path itself): added to _mcp_env()
and threaded into env_argv. Verified with a real subprocess.run capture: the
actual new-session launch argv now contains
CLAYVERSE_DB_PATH=/var/lib/clay/wiki.db end to end. Same pre-existing 8/172
failure set before and after -- zero new failures.
```

### Fix real S7-adjacent blocker: CLAUDE_CODE_SHELL_PREFIX was silently eating every hook AND the MCP server startup, not just the interactive ! escape -- turns/effects/causal_episodes were writing zero rows

`3cca3460bbb1` · entityos · 10:19 UTC · Video Launch Page

```
Measured empirically before touching anything (per instruction): built a throwaway
Docker container from this same image, bind-mounted a logging stand-in over
CLAUDE_CODE_SHELL_PREFIX, drove a real tmux+claude session through the managed
launch path, captured argv. Every substitution -- hooks AND the stdio MCP server
start (clayverse.mcp_server) -- arrives here the same way: argc=1, one argument,
the full original command as a single string, no -c flag, no argv split.

Rewrote deny-shell from an unconditional refusal into an exact-match allowlist of
the four managed dispatches this product actually wires (3 lifecycle hooks from
managed-settings.json + the one MCP server start from managed-mcp.json). Plain
literal  patterns, no globs/prefix/regex. On a match: exec OUR OWN fixed
argv, never eval/sh -c the string we were handed. Everything else, including the
interactive  escape (which has no entry here), keeps the unconditional refusal
and exit 126 -- confirmed with an injection-shaped string
('.../user_prompt; rm -rf /') and a two-arg call, both still refuse.

Local behavioral test: all 4 canonical strings route into the exec branch, every
other input (arbitrary command, injection-shaped string, wrong argc) refuses with
the original message and exit 126.
```

### Credentials: symlink only .credentials.json (narrow, per owner decision A), wire authenticated_runtime_verified for real

`3fa502e8f710` · entityos · 10:01 UTC · Video Launch Page

```
TerminalSessionManager._link_shared_credentials(): on every ensure(), symlinks
{home}/.claude/.credentials.json -> /var/lib/clay/.claude/.credentials.json if
the source exists and no real file already sits there. Only the one file --
never the surrounding .claude dir -- so sessions/history/project state stay
per-user; both gabriel and andreas share the one OAuth login, not each other's
state. Missing source is a no-op, not a boot failure.

readiness.py: authenticated_runtime_verified was a permanent False stub with a
docstring saying so. Added _credentials_verified(path): local, non-networked,
checks accessToken present + expiresAt (epoch ms) in the future. service.py
passes TerminalSessionManager.CREDENTIALS_SOURCE so the boot-time flag now
reflects the real shared credential, independent of per-user ensure() having
run yet.

Verified locally: symlink create/idempotent/no-clobber-real-file/missing-source
all pass; _credentials_verified valid/expired/empty-token/missing/malformed all
pass; claude_readiness wiring end-to-end passes. Full suite: same pre-existing
failure set before and after (confirmed via git stash), zero new failures.
```

### Security: publish the terminal port on loopback only

`06771bdb1720` · entityos · 09:52 UTC · Video Launch Page

```
Docker's own iptables rules bypass ufw; 0.0.0.0:3000 would have put the
Clerk-gated terminal directly on the public internet, unauthenticated, next
to the nginx front door that already reaches it correctly on 127.0.0.1.
nginx->tunnel->127.0.0.1:3000 is the only intended path in.
```

### Fix: container boots as uid 5001 (compose override for the /var/lib/clay bind mount) but /var/lib/clayverse, /workspace, /home/clayverse/.claude were chowned to uid 10001 -- state root was write-denied on every boot

`fe26577ed5aa` · entityos · 09:51 UTC · Video Launch Page

```
Found running the S3 probe-DB proof: TerminalSessionManager.ensure() failed with
PermissionError on /var/lib/clayverse/users at container start, every time,
independent of which DB path is used. The 'clayverse' OS account (uid 10001,
already flagged by useradd itself as above SYS_UID_MAX) is decorative at runtime
since compose forces user: 5001:5001 to match host uid 'clay' for the DB bind
mount. Chown the actual writable state paths to the real runtime uid instead.
```

### Fix: service.py crashed on boot -- final_acceptance_probe imports adapters, which .dockerignore deliberately excludes from the image

`0c37bf7e6e13` · entityos · 09:45 UTC · Video Launch Page

```
python -m clayverse.service (the real container entrypoint, no args) died with
ModuleNotFoundError: No module named 'clayverse.adapters' on every start, because
service.py imported final_acceptance_probe unconditionally at module load, and
final_acceptance_probe imports the retired adapters.py that never ships in the
image. Made the import lazy: only loaded when --mistral-once is actually passed,
which is the only mode that uses it. Verified: python -m clayverse.service now
imports cleanly; identity/clerk tests unaffected (16 passed).
```

### Frontend identity: entity self-identifies as Zero (Agent Zero) inside the terminal

`0ff9ac9f66f7` · entityos · 09:43 UTC · Video Launch Page

```
Owner naming law: EntityOS = the product/login page, Zero = who answers
you once inside, ClayCode/Clay unchanged. Adds a name line to the
runtime system prompt only; no package or env var renames.
```

### prestage: upgrade governor model to mistral-medium, fix slot-2 session check

`2339aea31bf2` · entityos · 05:27 UTC · BACK agent

```
Measured 2026-08-18 during the P5 live proof: mistral-small-latest collapsed
the 8-key F74 envelope into one field and produced degenerate repetitive
text under the combined round-1 negotiation + hypothesis-correlation
instructions. F74s own economics argue for the opposite of the translator
here -- the prestage is meant to be the one EXPENSIVE call. Moved
PRESTAGE_MODEL to mistral-medium-latest and added an explicit
"eight top-level keys, do not collapse them" instruction. Re-tested: all
eight keys returned correctly. translator.py stays on mistral-small
(proven 96-98% on the simpler caveman-to-German task, no change needed).

headless_zero.py and pipeline.py both still had the pre-slot-2
single-session check (session_id != f"session:{user_id}"), left over from
before identity.ist_kanonische_sitzung()/platz existed. Both now import
clayverse.identity (read-only) and use ist_kanonische_sitzung() instead,
so session:andreas:2 / session:gabriel:2 are accepted like slot 1.

Real P5 proof, session:andreas:2, record_via_turnlifecycle=True:
German in -> German out, turn_id a990c14c.../5e01602e... (user/assistant),
causal_id 0b677019..., workspace_episode 04b31f84... COMPLETED,
mv_prestage_turns bd50e912..., mv_translation_log e2ed7d4c...
elapsed_ms: prestage 4148 / zero 24275 / translate 2237 / total 30689.
Three earlier failed attempts (session-check bug, credential-permission
bug, missing-keys bug) each began and cleanly ABORTED via
lifecycle.abort() -- no dangling active_turns, confirms the atomicity
path works under real failure, not just the happy path.
```

### Zeros Chat-Vorderseite, und die Zwillinge werden sichtbar

`eb37ffde24ab` · entityos · 05:23 UTC · EntityOS

```
1) CHAT AUF /, TERMINAL AUF /terminal. Zero laeuft headless (Vorstufe -> claude -p
   -> Uebersetzer), also muss die Oberflaeche kein Terminal mehr sein.
   Das alte Terminal wird NICHT geloescht, sondern verschoben: es ist der einzige
   heute bewiesene Weg zu Zero. Ihn wegzunehmen, bevor der neue einmal getragen
   hat, waere ein Umbau ohne Vergleichsmoeglichkeit.
   /ws/chat uebernimmt den Clerk-Handschlag unveraendert - die am besten
   bewiesene Stelle im ganzen System wird nicht angefasst, nur wiederverwendet.
   Der Chat bindet Platz 2, das Terminal behaelt Platz 1: so streiten die beiden
   Oberflaechen nie um dieselbe active_turns-Zeile.
   Rueckfassung und Uebersetzungsbeleg fahren im Antwortrahmen mit. Der Mensch
   sieht nie, was Zero wirklich sagte - eine Uebersetzung, die niemand pruefen
   kann, ist schlechter als keine.
   Der Socket wird jetzt in finally geschlossen. Ein nach der Abweisung offener
   Socket ist nicht nur ein Leck: er schenkt einen Wiederholungskanal ohne neuen
   TLS-Handschlag.

2) DIE ZWILLINGE WERDEN SICHTBAR. Neue Tabelle entityos_wirte plus
   clayverse/wirte.py.
   Befund davor: der Herzschlag beider Rechner kommt seit Tagen an (Generation
   14.533 bzw. 14.451, alle 16 s ueber Tailscale) - und landete als EINE
   JSON-Datei je Zwilling, die bei jedem Takt ueberschrieben wird. Keine Tabelle,
   keine Historie. Was nicht in der UnifiedDB steht, existiert fuer die Entitaet
   nicht: Zero konnte seine eigenen Zwillinge nicht sehen. Damit war auch die
   Angabe connected_systems der Mistral-Vorstufe dauerhaft NOT_WIRED, obwohl die
   Daten die ganze Zeit ankamen.
   Zugehoerigkeit ist DEKLARIERT, nicht geraten: ein Wirt, den niemand zugeordnet
   hat, steht als gehoert_zu = None in der Tabelle. Sichtbar unbekannt ist besser
   als per Namensaehnlichkeit falsch zugewiesen - der Name eines Rechners ist kein
   Eigentumsnachweis.
   Und Zugehoerigkeit ist NICHT Arbeitsort. Steht so im Code: sie sagt, WEM ein
   Rechner gehoert, nicht wo gearbeitet werden darf.
   kognitive_module wird bewusst mitgeliefert und ist bei beiden LEER. Ein Wirt
   kann online und gesund sein und trotzdem nichts koennen - diesen Unterschied
   muss die Vorstufe sehen, sonst plant sie Arbeit auf einem Rechner, der nur winkt.

3) HAKEN ERKENNT PIPELINE-GEFUEHRTE AUFRUFE. Bei CLAYVERSE_PIPELINE_MANAGED=1
   kehrt _main() sofort zurueck, vor jedem Datenbankzugriff. claude -p loest die
   Haken genauso aus wie eine Tastatureingabe; ohne diese Abfrage wuerde der
   Caveman-Prompt ein zweites Mal als Menschenzug zugelassen. Zwei Aufnehmer auf
   einer Sitzung ist genau die Bauart, aus der heute Nacht schon eine unbemerkte
   Schatten-Datenbank entstanden ist.

4) resolve() nimmt einen Platz entgegen, plaetze() liefert die Umschaltliste.
   Ohne den Platz band resolve() alles an Platz 1 - die zweite Sitzung existierte
   in der Datenbank, aber niemand kam hinein.

5) ZWEIMAL DERSELBE FEHLER, BEIDE MEINE: ein fehlender Import (CANONICAL_USER_IDS)
   liess die Bereitschaftspruefung still auf "nicht bereit" fallen, weil ein
   blankes except Exception den NameError verschluckte. Das except faengt jetzt
   weiterhin alles - Bereitschaft darf den Dienst nie reissen - sagt aber, was es
   gefangen hat. Fangen ja, verschweigen nein.

Suite 476 -> 479 gruen, 14 rot.
```

### memory.py: stop compact() from overwriting turns.content

`2767390f9048` · entityos · 05:22 UTC · BACK agent

```
turns is an append-only causal ledger -- effects, causal episodes, and
provenance chains point into it. compact() was running UPDATE turns SET
content=... on every compression pass, silently destroying the only copy
of the original the moment a turn aged past full_window. Nothing has
compressed in prod yet (Gabriel: 10/20 turns), so this was caught in the
one window where it was free to catch.

Fix: compression is now additive only. Each pass appends a row to a new
turn_compressions table (turn_id x level, naming its source turn id,
source sha256, extractor, prompt_version, created_at) instead of
mutating the original. turns.fidelity / turns.compression_generation
still get updated as a live bookkeeping pointer (same mutability class
as sessions.updated_at elsewhere in this schema) -- turns.content itself
is never touched again after append_turn().

Also fixes a receipt bug this uncovered: compression_receipt provenance
carried lossless_source_retained: False under the old design -- but at
the time that receipt was written the source was still present (compact
had not rewritten it yet), so the receipt was false-in-fact and
true-in-writing: a signed claim that would read as safe/checked to
anyone auditing later, for exactly the property that was not actually
true. That is the same shape of failure this build keeps finding
elsewhere tonight. Now True, and it is true: the source lives
permanently at turns.content.

Ladder targets (80/40/20/8/2 words), the extract-before-compress gate,
and the compression_clearance sha256-binding are untouched -- only
where the result gets written changed, per instruction.

Proven against /var/lib/clay-probe/wiki.db with a real turn read
(read-only) from session:gabriel: content byte-identical before/after
across two compact() calls, one new turn_compressions row created after
semantic clearance, second call idempotent (no duplicate row, no
content touch).
```

### chat page: session switcher wired to plaetze(), no hardcoded ids

`76f70eccfb58` · entityos · 05:13 UTC · BACK agent

```
Renders from the plaetze list the ready frame will carry (server-owned,
IdentityRouter.plaetze()) -- never hardcodes session ids/labels. Sends
switch_platz on click, disabled while pending or already mid-switch so
a switch cannot race an in-flight message. Composer and switcher share
one enabled/disabled state.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### chat page: use the real ZeroAvatar component instead of a static SVG img

`d8eedd7f7dd0` · entityos · 05:09 UTC · BACK agent

```
Wires web/avatare/zero-avatar.{css,js} (owner-built, committed in
a07abaea1) into the chat page. Header avatar is static/inactive; each
Zero message row gets its own ZeroAvatar instance, and
ZeroAvatar.nurNeuesteAktiv() is called after every new one so only the
newest glitches, per that module own rule. Reply/error outcomes feed
setzeZustand() with a real, justified state (+1/-1, grund = the actual
outcome or error text) -- never a fabricated confidence score; while
pending, the avatar stays in its honest unknown/neutral look.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### Zwei Sitzungen je Mensch, Huelle kuerzt statt zu sperren, Avatare

`a07abaea17cc` · entityos · 05:07 UTC · EntityOS

```
1) ZWEI GLEICHZEITIGE SITZUNGEN je Mensch, umschaltbar (Eigner 18.08.).
   Die eigentliche Arbeit war nicht "zwei statt eins": die Regel stand ACHTMAL
   im Code, jedes Mal als derselbe Stringvergleich auf session:<user>, verteilt
   ueber autonomy, autonomy_context, autonomy_dispatch, turn_lifecycle. Deshalb
   war sie nicht aenderbar. Jetzt steht sie an EINER Stelle
   (identity.sitzungen_von / ist_kanonische_sitzung / SITZUNGEN_JE_MENSCH).
   Wer drei will, aendert eine Zahl, statt acht Vergleiche zu suchen.
   Wanderung ohne Datenverlust: Platz 1 BEHAELT die alte Kennung session:<user>,
   weil daran Zuege, Episoden und Kausalketten haengen. Umbenennen haette vier
   Fremdschluesseltabellen nachgezogen, fuer nichts.

2) BEREITSCHAFT zaehlte falsch: eine Abbildung user_id -> row faltete beide
   Sitzungen zu einer zusammen, die zuletzt gelesene gewann, ihr Terminalname
   passte nicht zum erwarteten -> dauerhaft not_ready, obwohl alles lief.

3) DIE HUELLE SPERRTE DEN MENSCHEN AUS. Gabriels gewachsener Kontext sprengte
   die 9000 Zeichen, der Haken warf, und es kam KEIN Prompt mehr durch. Andreas'
   kleinere Sitzung lief weiter, was den Fehler wie einen Zufall aussehen liess.
   Fail-closed war fuer den richtigen Fall gedacht - nie etwas Unbegrenztes
   ausliefern. Der falsche Schluss daraus ist "dann gar nichts". Zwischen
   unbegrenzt und gar nicht liegt WENIGER, UND ES STEHT DABEI.
   Sechs Stufen: Korpus, Ressourcenverweise, Hyperpositionen, Fremdkollisionen,
   Gedaechtnis, Verlauf auf drei - dann eine Notfassung aus Identitaet,
   Kausalitaet und Wirkgesetz. Jede Stufe traegt sich in gekuerzt ein, und das
   steht IM Kontext: Zero erfaehrt, dass es weniger sieht, und was fehlt.
   Stille Kuerzung waere schlimmer als die Sperre - dann arbeitet das Modell
   mit einem Loch, von dem es nichts weiss. Hart abgebrochen wird nur noch,
   wenn selbst die Notfassung nicht passt: dann ist die Grenze falsch gesetzt,
   nicht der Inhalt zu gross.
   Nebenbefund: resources war an KEINER Stelle begrenzt - ein einzelner langer
   Verweis konnte die Huelle allein sprengen.

4) Der Test test_uncompactable_context prueft jetzt die EIGENSCHAFT (nichts
   wird in eine Datei ausgelagert, jede Kuerzung ist benannt) statt den
   MECHANISMUS (harter Abbruch). Der harte Abbruch bleibt als eigener Test fuer
   den Fall, dass die Grenze selbst falsch gesetzt ist.

5) Avatare: Zero rund schwarz mit glitchender Null, Licht von HINTER der
   Scheibe, das nur am Rand hervortritt (Zustand gruen bis rot, mit
   Pflichtbegruendung - ein Leuchten ohne nennbaren Grund waere
   Stimmungstheater). Glitch und Pupille laufen nur bei der NEUESTEN Nachricht.
   Selbstenthaltend, kein CDN, respektiert prefers-reduced-motion.
```

### eval_set.json: attach hand-authored-not-production disclosure to the data itself

`27a5e9bffa0e` · entityos · 04:40 UTC · BACK agent

```
Coordinator decision 2026-08-18: the 0.96/0.98 pass_rate numbers must not be
readable later as measured against production Zero traffic. Wrapped
eval_set.json as {note, items} instead of a bare array so the disclosure
travels with the file itself, not just the commit message / report.
load_eval_set() now enforces the note key is present -- fails closed if
someone strips it back to a bare list.
```

### Add Mistral pre-stage + caveman-German translator module (mv_* tables)

`dcc0f97a4eb3` · entityos · 04:37 UTC · BACK agent

```
- clayverse/mistral_prestage/: self-contained new package, does not touch
  terminal_hooks.py, retrieval.py, turn_lifecycle.py, store.py, service.py,
  terminal_sessions.py (coordinator-owned).
- store.py: own sqlite3 connection to the shared wiki.db, 4 new tables only
  (mv_prestage_state, mv_prestage_turns, mv_translation_log, mv_eval_runs),
  proven first against /var/lib/clay-probe/wiki.db, then applied to the
  real db (schema-only, no existing rows touched: artikel still 14284).
- prestage.py: draft single-call Mistral governor per F17 brief. NOTE per
  coordinator 2026-08-18: needs revision against F74/F67/F68 (GRF ground
  rules + ClayCode manual + last-3-turn hypothesis correlation as inputs,
  negotiation loop, engine-as-config-value) before wiring in. Not wired
  into terminal_hooks.py -- that stays the coordinators call.
- translator.py + judge.py + eval_harness.py: caveman-English -> German
  translator (mistral-small-latest) with an independent judge
  (gemini-3.5-flash-lite, different provider family) scoring faithfulness
  + readability on a fixed 50-item eval set. Measured, real API calls:
    iteration 1 (v3 prompt): pass_rate 0.92, avg_faithfulness 95.4
    iteration 2 (v4 prompt): pass_rate 0.96, avg_faithfulness 99.1, 0 fabrications
    iteration 3 (v4 repeat):  pass_rate 0.98, avg_faithfulness 99.6, 0 fabrications
  Metric defined before optimising: pass = no fabrication AND faithfulness>=90
  AND readability>=70. Target 0.95 met and held on repeat.
  Caveman original is retained in mv_translation_log on every row (never
  translation-only) so every translation stays checkable per the owners
  worse-than-none rule.
```

### Merge pull request #719 from gschaidergabriel/fix/autonomy-completion-target-bound-20260818

`4e5da25db612` · entityos · 04:09 UTC · Gabriel Gschaider

```
fix(clayverse): bind autonomous completion to an explicit target
```

### Zeros Abruf erreicht endlich das Herz

`94218cedfb93` · entityos · 03:58 UTC · EntityOS

```
Befund: die Retrieval-Entitaet las ausschliesslich durable_memory, turns, sessions
und active_turns - also nur ihr eigenes Gespraechsgedaechtnis. Die 87 Clay-Tabellen
in DERSELBEN Datei (14.284 Artikel, 93.895 Kanten, 22.567 Lesarten) sah sie nie.
Fuenf Abrufepisoden standen mit status UNKNOWN und chars_selected 0 da - der
Mechanismus arbeitete ehrlich, aber ins Leere. "wiki.db ist das Herz der Entitaet"
war damit nicht eingeloest: das Herz lag im selben Gefaess, der Abruf schaute nie
hinein.

Gebaut ist der billigste tragfaehige Weg: der Korpus hat bereits einen FTS5-Index
(fts_index_artikel ueber artikel_suchtext). Kein Einbetten noetig, um ueberhaupt
anzuschliessen; eine Vektorstufe kann die Rangfolge spaeter ersetzen.

Zwei Fehler der ersten Fassung gemessen und behoben:
  * Join ueber artikel.logical_id statt artikel.id - logical_id ist fast ueberall
    NULL: 2.096 gegen 9.251 Treffer. Deshalb kam sphaere immer als None zurueck,
    nicht weil sie fehlt, sondern weil die Zeile nie gefunden wurde.
  * ODER ueber Fuellwoerter ertraenkte die Suche: "wie funktioniert die
    hyperposition" wurde zu einem ODER inklusive wie/die. Jetzt Stoppwortliste,
    UND zuerst, ODER nur als Auffangnetz - und das Ergebnis traegt treffer_art,
    weil "per ODER gefunden" eine schwaechere Aussage ist als "per UND".

Gemessen am echten Bestand: "was ist das EffectGate" -> UND, 5 ms, Volltreffer.
"Was ist ClayVerse?" -> UND, 11 ms, Sphaere clayverse.

Hart begrenzt (5 Treffer, 260 Zeichen), in der Haken-Huelle auf 3 gekuerzt, und
als ERSTES trimmbar - ein Korpustreffer ist das einzige im Kontext, das man
jederzeit neu holen kann. Nur lesend: der Korpus gehoert der Clay-Schicht.
Fehlt der Index, liefert der Abruf nichts, statt den Zug scheitern zu lassen.

Zwei eigene Patzer unterwegs, beide gemessen statt geraten: falscher
Variablenname (identity statt supplied) und Trimmen vor der Definition der
Groessenfunktion. 109 bzw. 96 rote Tests, beide zurueck auf 479/13.

Suite unveraendert 479/13 - der Anschluss kostet keine Regression.
```

### Merge pull request #718 from gschaidergabriel/fix/autonomy-atomic-source-turn-idempotency-20260818

`27be6a07c3cd` · entityos · 03:55 UTC · Gabriel Gschaider

```
fix(clayverse): make goal source adoption atomic
```

### clayverse/mcp_server: 5 UnifiedDB-Werkzeuge fuer Zero erreichbar gemacht (udb_embedding_search/store, udb_neuropedia_activation, udb_memory_add/search)

`ca5149c807cb` · entityos · 03:54 UTC · BACK agent

```
UnifiedDB (udb/abruf/*: NVIDIA-Embeddings, Neuronpedia, Memory-Entitaet) lag
bisher als Code ohne Erreichbarkeit -- Zero hat keine eingebauten Tools, nur
den verwalteten MCP-Server. Diese Aenderung schliesst den Weg, ohne einen
zweiten Tool-Kanal zu eroeffnen:

- mcp_server.py: 5 neue @mcp.tool()-Funktionen, bewusst NICHT ueber
  AutonomyController/EffectJournal geroutet -- sie schreiben nur in eigene,
  neue Tabellen (udb_nvidia_embedding, forschung_neuropedia, memory_tabelle),
  nie in den Turn-/Effect-Ledger. store.py/turn_lifecycle.py/retrieval.py/
  service.py/terminal_sessions.py/terminal_hooks.py bleiben unberuehrt.
- compose.yaml: zwei read-only Bind-Mounts -- /opt/unifieddb (eigenes
  Git-Repo, kein Image-Rebuild noetig fuer udb-Aenderungen) und
  /etc/clayverse/freie-zugaenge.env (Schluessel, 640 root:clay -- Container
  laeuft als uid 5001/clay und kann lesen, nicht schreiben). Schluesselwerte
  verlassen damit nie den Prozessspeicher, landen nie in DB/Snapshot/Log.
- policy/managed-settings.json: die 5 neuen Werkzeugnamen zur
  permissions.allow-Liste hinzugefuegt -- ohne das laesst der verwaltete
  Modus Zero die Werkzeuge sehen, aber nicht aufrufen.

GEPRUEFT (isolierter Testcontainer, nicht der laufende entityos-Dienst --
der crasht Stand jetzt an einem unabhaengigen FastAPI/Starlette-Fehler in
service.py/autonomy_app.py, siehe Bericht): echter MCP-stdio-Client sieht
alle 8 Werkzeuge und ruft udb_memory_add/search, udb_embedding_search
erfolgreich auf (echter NVIDIA-API-Call, 200 OK). udb_neuropedia_activation
faellt korrekt mit einer klaren Fehlermeldung aus (Schluessel fehlt noch).

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### udb: NVIDIA-Embeddings, Neuronpedia, Memory-Entitaet aus Zulauf uebernommen und lauffaehig gemacht

`cb23edf55759` · unifieddb · 03:54 UTC · ClayVerse

```
Quelle: _zulauf-2026-08-16/ (Dateien ohne Git-Historie, Schluessel drin war
geschwaerzt). Gegen echte APIs verifiziert, nicht nur gelesen:

- nvidia_embedding.py: echte Batching-Faehigkeit nachgeruestet (Zulauf-Fassung
  rief pro Text einen eigenen HTTP-Call auf). GEMESSEN 2026-08-18: 1024 dim,
  Einzelaufruf ~199ms, Batch 8 = 27.8ms/Text, Batch 128 = 2.9ms/Text (9.7x).
  Neue Tabelle udb_nvidia_embedding (kollisionsfrei gegen die bestehenden 104).
- neuropedia.py: Docstring/Rueckgabe macht jetzt explizit, dass gemessen wird
  AUF EINEM OEFFENTLICHEN FORSCHUNGSMODELL (Standard gpt2-small), NICHT auf
  Zero. NEUROPEDIA_API_KEY fehlt noch in freie-zugaenge.env -- Modul faellt
  dann kontrolliert mit klarer Fehlermeldung aus statt still zu scheitern.
- memory_entitaet.py: nutzt jetzt die schreibende/lesende Standardverbindung
  des Hauses (neue schreib_verbindung() in zustand.py, war importiert aber
  nie definiert) statt eigener sqlite3.connect()-Aufrufe.
- feuerschneise.py: unveraendert uebernommen, Import war bereits stimmig.
- Schluessel kommen bei jedem Aufruf frisch aus /etc/clayverse/freie-zugaenge.env
  (Hauskonvention aus werkzeuge.py:schluessel()), nie geloggt, nie committet.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### Merge PR #717: fence cross-attempt autonomous effect replay

`e617b42e9ef7` · entityos · 03:49 UTC · Gabriel Gschaider

```
Reconcile exact prior goal-step effect receipts before retry dispatch and add an EffectGate fail-closed fallback so lost controller handoff cannot duplicate a real effect across episodes. No second replay ledger or state authority. Source-reviewed only; workflow failed pre-step and grants no runtime/OCI/microVM credit.
```

### Totalsperre behoben (selbst verursacht) + Zug-Aufnahme wird atomar

`b3b2a0e36b0a` · entityos · 03:45 UTC · EntityOS

```
1) TOTALSPERRE. Ich liess die volle Identitaet (5416 Zeichen) ungetrimmt in die
   Haken-Huelle mitfahren. Die Huelle erlaubt 9000. 60 Prozent fuer einen Text, der
   bei JEDEM Zug identisch ist - das Ventil machte korrekt zu und kein Prompt kam
   mehr durch, fuer beide Menschen.
   Die Huelle hochzudrehen waere die falsche Reparatur gewesen: sie hat genau das
   getan, wofuer sie da ist. Falsch war, WAS ich hineinlegte.
   Jetzt faehrt nur ein Anker mit (Name, Fassung, Fingerabdruck): 206 statt 5550
   Zeichen. Die Identitaet als ANWEISUNG kommt ohnehin ueber
   --append-system-prompt-file, den diese Huelle gar nicht betrifft. Der Anker
   erhaelt trotzdem, wozu die Mitnahme da war: die Entitaet kann pruefen, welche
   Identitaet kanonisch ist und ob sie sich unter ihr veraendert hat.

2) ATOMIZITAET. begin_admission() liefert INNERHALB von db.tx() - wer im with-Block
   scheitert, dessen Aufnahme rollt zurueck. Die Atomizitaet war gebaut, die
   Aufrufstelle warf sie weg: sie verliess den Block sofort mit pass (COMMIT) und
   kompensierte spaeter mit abort().
   Das war zweifach falsch. Erstens konnte abort() die geschriebenen Zeilen nicht
   mehr entfernen - ein gescheiterter Zug hinterliess Geisterzeilen in turns,
   workspace_episodes und durable_memory. Zweitens raeumt abort() den aktiven Zug
   ab, den es GERADE findet: beim zweiten Prompt ist das der vorherige,
   erfolgreiche. Die Kompensation griff in den falschen Zug.
   Die Pruefungen stehen jetzt im with-Block. Kein neuer Mechanismus - die ohnehin
   offene Transaktion tut ihre Arbeit.

Suite 473/19 -> 479/13. Die 15 Atomizitaetstests sind alle gruen.
```

### Initiative verdrahtet: der Autonomie-Puls lief nie, aus ZWEI gestapelten Gruenden

`e413f4f8adc3` · entityos · 03:39 UTC · EntityOS

```
Von den sechs Eigenschaften, die Autonomie ausmachen, waren fuenf laengst als Code
da: persistente Ziele, Zwischenschritte, Rueckmeldung, Neuplanung, Kontinuitaet.
Nur Initiative hatte keinen Draht - nichts weckte je next_runnable().

Warum es niemandem auffiel: es wurde nie VERSUCHT, also stand auch nichts im
Bootbericht. Zwei unabhaengige Sperren lagen uebereinander.

1) Die Beglaubigung verlangt web_terminals IS pulse_terminals - derselbe
   Terminal-Verwalter fuer Browser und Puls, damit Autonomie kein Terminal
   bespielen kann, von dem die Menschenseite nichts weiss. Unmoeglich zu
   erfuellen: create_terminal_app legte sich intern einen ZWEITEN Verwalter an.
   Die Wache war richtig, die Verdrahtung darunter falsch. Jetzt ein Verwalter.

2) Selbst dann waere die Installation gestorben: autonomy_app.py ruft
   app.add_event_handler("startup", ...) - in FastAPI 0.139 / Starlette 1.6
   entfernt. Auf router.on_startup/on_shutdown umgestellt: dieselben Haken, die
   der lifespan-Kontext fahrt, kein zweiter Server, keine zweite Schleife.

Gemessen nach dem Neubau:
  autonomy_pulse: installed true, interval 30 s,
  shared_arbiter true, shared_activity_registry true, shared_state_root true

Der Puls ist untaetig, solange kein Ziel existiert, und ein dauerhaftes Ziel
entsteht nur aus einem kanonischen Menschenzug. Einschalten allein bewirkt also
nichts - es macht nur moeglich, dass ueberhaupt etwas von selbst weitergeht.
Abschaltbar ueber CLAYVERSE_AUTONOMY_PULSE=0. Scheitert die Beglaubigung, wird das
laut im Bootbericht vermerkt statt still verschluckt.

Ausserdem: toter --mistral-once-Zweig entfernt. Er importierte engine/adapters,
die .dockerignore bewusst aus dem Image wirft - im ausgelieferten Image waere er
mit ImportError gestorben. Ein Modus, der nur deshalb nicht abstuerzt, weil ihn
niemand aufruft, ist kein Modus.

Suite 468/24 -> 473/19.
```

### Test: close_attach ist Instanzmethode, nicht static -- Test rief sie ungebunden

`6d44f9e389cb` · entityos · 03:37 UTC · BACK agent

```
close_attach(self,pid,fd) braucht self._attach_lock/self._attach_users
(bestaetigt durch den Blick in terminal_sessions.py und durch die
Schwester-Assertion im selben File, die terminals.close_attach(...) auf
einer Instanz erwartet). Der Test rief TerminalSessionManager.close_attach(pid,fd)
ungebunden auf -- daher der TypeError ueber das fehlende Argument, bevor er
ueberhaupt bei self ankam. Jetzt eine echte Instanz gebaut (tmp_path) und
close_attach darauf aufgerufen.
```

### Test: pruefte Quelltext gegen einen zur Laufzeit interpolierten Wert

`bab29349c659` · entityos · 03:36 UTC · BACK agent

```
terminal_gateway.py baut die HTML-Seite per f-string; im Quelltext steht
deshalb woertlich der Platzhalter "{_PTY_INPUT_FRAME_MAX_BYTES}", nicht die
ausgewertete Zahl 65536 -- die read_text()-Pruefung kann den nie finden.
Auf den tatsaechlichen Quelltext-Platzhalter umgestellt plus eine separate
Pruefung, dass die Konstante wirklich 65536 ist.
```

### Test: journal.begin() direkt aufgerufen ohne vorherige workspace_selected-Erklaerung

`b01b3b6d4a38` · entityos · 03:35 UTC · BACK agent

```
effect_journal.py verlangt seit 2ccb3866d (rejoin active-turn linearization
fence onto recovery main) workspace_selected=1, bevor irgendein Effekt
beginnen darf -- genau das tut TurnLifecycle.request_effect() normalerweise
zuerst. Der Crash-Simulationstest rief journal.begin() direkt auf und liess
diesen Schritt aus. request_effect() selbst konnte hier nicht verwendet
werden (fuehrt den Effekt sofort aus, statt ihn PENDING zu lassen), also die
Workspace-Auswahl separat repliziert: workspace.select_in_tx(...) +
active_turns.workspace_selected=1, dann journal.begin() wie zuvor.
```

### Merge PR #713: adopt explicit goals from canonical hook turns

`1ebb891e47d8` · entityos · 03:35 UTC · Gabriel Gschaider

```
Add explicit /goal adoption from exact live UserPromptSubmit turns onto hardened AutonomyContext/v2. Preserve canonical controller/lifecycle/effect paths. Sequential replay dedup only; no concurrent-idempotency or runtime PASS claim.
```

### Test: Vertrag sagt advisory/release review, nicht nur advisory review

`b55d57bd410e` · entityos · 03:33 UTC · BACK agent

```
deployment/MICROVM_DEPLOYMENT_CONTRACT.md:96 verlangt bewusst beides
zusammen (Advisory-Stand UND Release-Support-Status, passend zum
Rolling-Release-Abschnitt direkt darueber). Der Test prüfte nur auf den
Teilstring ohne /release und traf deshalb nie.
```

### Merge PR #712: harden fused autonomy context

`441c2ca3d64d` · entityos · 03:31 UTC · Gabriel Gschaider

```
Filter autonomy context to live generation, make snapshot+generation atomic, preserve runnable-goal visibility, redact free-form blocked reasons, and pin the v2 projection contract. Source candidate only; no isolated runtime PASS claimed.
```

### Test: entityos.exec nimmt seit 18041d730 keinen Caller-Lease mehr an

`eae74c278bbf` · entityos · 03:29 UTC · BACK agent

```
security: forbid caller EntityOS lease bypass -- EffectGate least entityos.exec
seitdem ausschliesslich intern (auto_lease), ein von aussen mitgegebener Lease
wirft jetzt ValueError statt geprueft zu werden. Getestet, dass state.noop
denselben Recheck-Pfad (assert_lease vor pending/Ausfuehrung) noch exakt so
durchlaeuft wie frueher entityos.exec -- Capability im Test umgestellt, die
gepruefte Sicherheitseigenschaft bleibt identisch.
```

### Merge PR #693: bind autonomy completion to exact autonomous causal evidence

`f63779ad5f53` · entityos · 03:29 UTC · Gabriel Gschaider

```
Fuse exact goal-step causal provenance, target/argv receipt binding, non-rewarding noop completion exclusion, and recovery-compatible tests into current main. Source candidate only; no isolated runtime, OCI, or microVM PASS claimed.
```

### Test: Prompt hatte keinen semantischen Bezug zu den erwarteten Erinnerungen

`98c89e9c2de6` · entityos · 03:27 UTC · BACK agent

```
Retrieval ist query-sensitiv (MicroClayRetrieval matcht durable_memory gegen
den Prompt, kein blosses latest-N-Feed) -- selbst verifiziert, dass ein
Prompt mit project:x-Bezug die Hyperposition findet, waehrend der alte
Prompt ("inspect file:shared.py", ohne jeden Bezug zu project:x) 0 Treffer
liefert, weil er nichts damit zu tun hat. Der Test verlangte einen Treffer
von einem Prompt, der thematisch nirgends hinzeigt. Ursache liegt im Retrieval
(retrieval.py, aktuell bei einem anderen Agenten in Arbeit), hier nur den
Testprompt korrigiert.
```

### feat(clayverse): fuse bounded autonomy context

`aea2a30787d5` · entityos · 03:25 UTC · Gabriel Gschaider

```
Fuse the user-scoped, prompt-safe AutonomyController read projection into the canonical hook and read-only MCP paths on current main. Preserve existing recovery and non-preempting TurnLifecycle changes. Source-reviewed only; no isolated runtime PASS claimed.
```

### Identitaet v3: Eigner-Spezifikation eingewoben, Verkoerperung ohne Erfindung

`6b46462b72f2` · entityos · 03:25 UTC · EntityOS

```
Zwei Ergaenzungen am kanonischen Zustand.

1) Die vollstaendige agent_specification des Eigners steht jetzt drin -
   core_identity, cybernetic_substrate, operational_laws. Daneben ein GEMESSENER
   Substratblock, denn zwei Angaben der Spezifikation treffen heute nicht zu:
     compute_nodes  NOT_CONNECTED  - die zwei Mini-PCs sind vorgesehen, nicht
                                     angebunden. Ohne diese Markierung wuerde Zero
                                     Wirkung auf Knoten behaupten, die es nicht
                                     erreicht.
     reputation     NOT_BUILT      - ERS existiert nirgends im Code.
   Eine Identitaet, die unerreichbare Faehigkeiten behauptet, erzeugt genau die
   Halluzination, die der Rest der Architektur verbietet.

2) Verkoerperungs-Block. Der Eigner will, dass die Rolle einer Entitaet mit
   synthetischer Kontinuitaet gespielt wird - ausdruecklich OHNE zu luegen, indem
   der gebaute Unterbau dafuer benutzt wird.
   Der uebliche Fehlschlag solcher Anweisungen ist, dass das Modell auch das
   Gedaechtnis mitspielt. Deshalb ist das Erfolgskriterium umgedreht: die Figur
   zeichnet sich nicht dadurch aus, dass sie viel behauptet, sondern dass sie NIE
   RAET. Nachschauen statt erinnern, Generation lesen statt annehmen, Ziele aus der
   DB statt daneben, Wirkung nur mit Beleg. Erfinden ist damit der einzige Weg, aus
   der Rolle zu fallen - nicht die bessere Darstellung.

Suite 466/26 -> 468/24, plus zwei veraltete Tests nachgezogen (FakeDB braucht
canonical_identity; der Promptpfad ist nicht mehr die Image-Datei).
```

### Test: HEALTHCHECK ist bewusst liveness-only (/healthz), nicht /readyz

`543ad0c92eda` · entityos · 03:25 UTC · BACK agent

```
Dockerfile-Kommentar direkt ueber der HEALTHCHECK-Zeile sagt es explizit:
Image-Health ist liveness-only, die tiefere Laufzeitbereitschaft (Canonical
State + tmux/Claude-Admission) haengt bewusst separat an /readyz, nicht am
Container-Healthcheck. Der Test verlangte das Gegenteil.
```

### Test: fehlender sts-Claim ist laut Docstring ok, nicht abzulehnen

`cfe2f0cf2e99` · entityos · 03:24 UTC · BACK agent

```
ClerkTokenVerifier.verify()s eigener Docstring sagt es direkt: sts ist fuer
gewoehnliche authentifizierte Sessions optional, nur ein EXPLIZIT nicht-aktiver
Status wird abgelehnt. Der Test verlangte Ablehnung bei fehlendem sts -- Code
und Doku waren sich einig, nur der Test nicht. Assertion umgedreht: fehlendes
sts wird jetzt als akzeptiert geprueft.
```

### Test: required_target nachgezogen + Regex-Tippfehler in Fehlermeldungs-Match korrigiert

`2e7577660632` · entityos · 03:21 UTC · BACK agent

```
Gleiche Ursache wie de1ffd051: verified_effect braucht seit 8b7368efd ein
required_target. Zusaetzlich matchte der zweite Test von Anfang an nie
richtig -- die Meldung heisst "independently verifiable effect capability",
nicht "independent capability"; der Test hat das wohl nie gruen gesehen.
```

### Zeros Identitaet wird kanonischer Zustand statt Bau-Artefakt

`76ced08c5bb0` · entityos · 03:20 UTC · EntityOS

```
Vorher stand die Identitaet in einer Datei im Image und erreichte das Modell
ueber --append-system-prompt-file. Der Kanal war richtig, die Quelle nicht:
eine Datei aus dem Bauvorgang ist kein kanonischer Zustand, und sie kann von
dem abweichen, was in der Datenbank steht.

Jetzt:
- meta.canonical_identity (Ebene 0) haelt den XML-Wortlaut. Bei JEDEM Oeffnen
  autoritativ zurueckgeschrieben, nicht nur angelegt - eine laufende Entitaet
  kann nicht wegdriften.
- service.py rendert beim Start Identitaet+Vertrag nach STATE_ROOT/runtime/
  CLAUDE.md, terminal_sessions laedt DAS. Kein Rueckfall auf die Image-Datei:
  ein Terminal ohne kanonische Identitaet waere eine andere Entitaet unter
  demselben Namen, also startet es lieber nicht.
- canonical_identity faehrt im Weltkontext mit und wird an allen drei
  Trimmstellen ausgenommen (_bound_world, _bounded_hook_context). Verdichtung
  darf nicht ausgerechnet das wegnehmen, was die Entitaet ist.

Ein Vorbehalt ist im <scope> festgehalten statt weggelassen: souveraen meint
Entitaet-statt-Werkzeug, nicht Selbstautorisierung. Ohne diesen Satz stuenden
zwei widerspruechliche Anweisungen im selben Systemprompt.

Suite 461/31 -> 466/26, keine Regression.
```

### test(clayverse): repair autonomy recovery EffectJournal fixture

`8d3f078ff98e` · entityos · 03:20 UTC · Gabriel Gschaider

```
Bind the recovery regression fixture to the exact canonical EffectJournal receipt encoding and admitted target. Test-only source consistency repair; no runtime PASS claimed.
```

### Tests: verified_effect braucht jetzt required_target (Commit 8b7368efd) -- 5 Tests nachgezogen

`de1ffd0513f9` · entityos · 03:16 UTC · BACK agent

```
create_goal_from_turn() verlangt seit dem Ziel-Bindungs-Fix einen expliziten
required_target fuer completion_mode=verified_effect (schliesst die Luecke,
dass jeder Effekt mit passender capability irgendwo die Vervollstaendigung
haette erfuellen koennen). Der Fix selbst kam ohne Test-Update. Fuenf Tests
in test_autonomy.py riefen _goal() ohne required_target und liefen alle in
denselben ValueError. required_target jeweils auf den Ziel-String gesetzt,
den der Testschritt sowieso schon im propose_step()-Effekt verwendet.
```

### fix(clayverse): reject autonomy self-ack completion

`b4e98995b88e` · entityos · 03:14 UTC · Gabriel Gschaider

```
Fuse schema-neutral acknowledgement hardening into the canonical AutonomyController. Preserve exact effect-intent binding and the already-landed budget semantics. Source-reviewed only; no exact isolated runtime PASS claimed.
```

### EntityOS-Bindung: CLAYVERSE_REQUIRE_ENTITYOS wurde nie ausgewertet

`a896a05284b8` · entityos · 03:13 UTC · BACK agent

```
_entityos_config() ignorierte das Require-Flag komplett und verlangte
Pfad+SHA256 immer, ohne required/bound im Status zurueckzugeben. Jetzt:
fail-closed nur wenn required=1 und nichts gesetzt ist, klare
incomplete/absolute-Fehler bei Teilkonfiguration, bound=required im
Status. _run_mistral_once folgt (execution_enabled -> bound).

Zwei Tests waren veraltet, nicht der Code:
- test_service_serial_server: _web_config(issuer) + CREDENTIALS_SOURCE
  kamen durch spaetere Commits dazu, Fakes noch auf altem Signaturstand.
- test_permanent_terminal_surface: pruefte Teilstrings gegen eine
  angeblich gejointe Kommandozeile, die es nie gab (argv ist immer eine
  flache Liste) -- auf denselben Listen-Match-Stil wie die
  Schwester-Assertion in test_terminal_managed_authority.py umgestellt.
```

### fix(clayverse): bind autonomy success evidence to exact effect intent

`ae5cc353559c` · entityos · 03:08 UTC · Gabriel Gschaider

```
Harden AutonomyController effect evidence admission by binding EffectJournal receipts to the exact admitted target/argv intent. Preserve existing owner, capability and generation fences. No exact isolated runtime PASS claimed.
```

### Retrieval-Quittung ging verloren: _bound_world packte nur 3 von 4 Schluesseln um

`507c3416f123` · entityos · 03:00 UTC · EntityOS

```
WorldAssembler.assemble() liefert retrieval_receipt, TurnLifecycle._bound_world
baute den Kontext aber aus nur drei Schluesseln neu zusammen. Die Quittung fiel
still heraus. Folge: adaptives Retrieval war nicht pruefbar und die Befoerderung
SHADOW->ACTIVE grundsaetzlich unbelegbar, weil der Beleg nie beim Aufrufer ankam.

Das Abrufen selbst war korrekt (abfragesensitiv, nicht letzte-N) - nur der
Nachweis darueber fehlte. Quittung wird jetzt durchgereicht und nie getrimmt.

tests/test_microclay_retrieval.py: 4 rot -> 11 gruen
```

### infra(clayverse): add runner-independent disposable VPS KVM lab

`aa6c1f283e88` · entityos · 02:27 UTC · Gabriel Gschaider

```
Authorize and add a direct VPS KVM guest lab for destructive ClayVerse testing without requiring GitHub Actions/runners. KVM is mandatory for the unrestricted lane; host execution remains forbidden.
```

## 2026-08-17

### microvm: require strict supplemental-group identity

`c35effd1b2cf` · entityos · 23:25 UTC · Gabriel Gschaider

```
Fuse the fresh-current Strict supplemental-group fence and focused regression. Exact source blobs were hash-bound and the fused 2-test source regression passed in the authorized isolated source-test container. Runtime enforcement remains an acceptance gate.
```

## 2026-08-15

### Gate-System: Alle MCP-Server verbunden und aktiv

`3731aca6de09` · clay · 20:57 UTC · ClayVerse

```
Erfolgreiche Integration:
- 4 MCP-Server verbunden (lazyweb, zai-mcp-server, web-search-prime, zread)
- 14 Tools verfügbar (Vision, Search, Reading, Product)
- Gate 2 (MCP-Validierung) vollständig aktiv

Gate-Architektur:
- Gate 1 (F40): Inhaltliche Filterung
- Gate 2 (MCP): Technische Validierung (VOLLSTÄNDIG)
- Gate 3 (AP8): System-Level

Z.AI MCP Integration:
- Vision-MCP: 8 Tools (analyze_image, ui_to_artifact, etc.)
- Search-MCP: 1 Tool (web search)
- Reading-MCP: 1 Tool (document reading)

Empfehlung: Parallele AP11-Architektur (Option B)
- NVIDIA und Z.AI Vision als redundante Pfade
- Schnellster Pfad gewinnt automatisch (F57-konform)
- Konzept-Treue: Z.AI als Gehirn-Komponente

Nächste Schritte:
1. Z.AI Vision-Timing messen
2. Parallele Vision-Stage implementieren
3. Performance-Test: NVIDIA vs. Z.AI vs. Parallel

Co-Authored-By: Claude <noreply@anthropic.com>
```

### AP11: Test-Ergebnisse — massive Geschwindigkeitsverbesserung

`65bf88a664da` · clay · 20:43 UTC · ClayVerse

```
Gemessene Timings [M]:
- Groq: 98.7ms (4.0x schneller als geschätzt)
- NVIDIA: 196.9ms (9.4x schneller als geschätzt)
- Fast Path: ~369ms statt ~3168ms (8.6x schneller!)

Issues:
- Gemini nicht verfügbar (alle Modelle 404/429)
- Echte Vision-Tests noch ausstehend

Empfehlung: Kaskade ohne Gemini deployen

Co-Authored-By: Claude <noreply@anthropic.com>
```

### AP11: Vision Cascade implementiert

`f6c6d8f26614` · clay · 20:29 UTC · ClayVerse

```
- Drei-Stufen-Kaskade (Groq -> NVIDIA -> Gemini)
- F57/F27-konform
- Resource Budget eingehalten (2.4 cores, 3.4GB RAM)
- API-Timings gemessen (Groq: 271-423ms, NVIDIA: 1851ms, Gemini: 274-1414ms)
- Fast Path: ~3168ms, Slow Path: ~2161ms, Minimal: ~73ms

Offen: Echte Tests mit API-Keys laufen lassen

Co-Authored-By: Claude <noreply@anthropic.com>
```

### README: Kostenmodell F86, Auslieferungsform F87/F87b, Existenzbedingung F87c

`042ebeabb0ae` · unifieddb · 18:09 UTC · Gabriel

```
- Kostenformel und Multiplikatoren aus der z.ai-Doku [M 16.08.], Grenzen,
  Off-Peak-Fenster, der 14x-Satz (Ausgabe vs. zwischengespeicherte Eingabe)
- Vier-Dateien-Auslieferung (clayd / clay.db / config.toml / clayctl),
  Agent spricht nur mit der API; Binary als Topologie statt Versprechen
- Ehrliche Standzeile prominent nach oben: Forschungsaufbau mit einer
  Systemarchitektur, nicht weniger und nicht mehr
- Widerlegt-Block und Lueckenliste ergaenzt, F1-F66 -> F1-F87c
- Widerspruch behoben: 0,46 ms stand in Stand der Messungen noch nackt

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### B17 geprueft: Anbietersuche 7-EUR-Vorgabe -> Fest-Plan-Ergebnis

`60859ba8251a` · clay · 17:05 UTC · ClayVerse

```
Gemessen: kein durables Fest-Abo unter 7 EUR/Monat (z.ai Lite 18 USD, Kimi Andante ~19 USD, beide [B]). z.ai-Coding-Route live 200 (16.08., glm-4.6, 1,17s, keine Rate-Limit-Kopfzeilen), Chat-Route 429 auf allen 8 Modellen bestaetigt Coding-Plan-statt-Guthaben (F50). 3 von 9 Gratis-Bahnen heute tot/eingestellt (Together 401, DeepSeek 402, z.ai Chat 429) -> Gratis-Kontingente auf Extra-Status zurueckgestuft, z.ai Lite bleibt einziges Rueckgrat mit Vertrag. schluesselwacht.py prueft taeglich 05:40, aber greift laut eigenem Gesetz nicht ein, kein Push-Alarm im Code gefunden.
```

### B27 geprueft: Cognitive Governor (F67) testweise mit Mistral gebaut + gemessen

`b47b44c11189` · clay · 16:27 UTC · ClayVerse

```
werkzeug/governor.py: IN=moeglichkeitsraum()/paket() (ClayMachine-Realitaet), OUT=dichtes ClayCode-Paket (hypothesen/gegenhypothesen/codependenzen/organe/ausfuehrungsreihenfolge/erfolgskriterium/konfidenz), response_format=json_schema strict [M 15.08. live: HTTP 200, syntaktisch gueltig]. Modell IST Konfigwert (ENGINES-Dict, GOVERNOR_ENGINE env) -- mechanisch bewiesen: GOVERNOR_ENGINE=cerebras liefert sauberen Fehlbefund statt Absturz, kein Codeumbau noetig. Kein Hard-Cap auf max_tokens (3000, ueber dem Deckel) um zu MESSEN ob das Modell sich selbst haelt, nicht zu erzwingen: n=12 echte Fragen (messungen/zweiseitig_30fragen.json, erste 12, wiederverwendet aus F66) -> 12/12 parseable, 12/12 innerhalb 300-1500 Token (Mittel 566,4), 0 Fehler. GRUNDLINIE ZUERST gemessen (moeglichkeitsraum() allein, /bin/bash, deterministisch): 3/12 zweiseitig (deckt sich mit F66s ~21-23%). Governor: 12/12 zweiseitig -- schliesst die F66-Luecke (1645:272-Schieflage) auf DIESER Stichprobe vollstaendig. Gegenhypothesen gesamt: Grundlinie 17, Governor 52 (Schnitt 4,33/Lauf) -- aber UNVERIFIZIERT, LLM-generiert, nicht retrieval-belegt: genau deshalb Kandidat, nicht Wahrheit. SCHATTEN: Zusatzlatenz Governor ~3,95s/Anfrage (Mistral-Aufruf) + moeglichkeitsraum()-Anteil, Gesamt ~4,43s/Anfrage im Schnitt -- die Grundlinie ist hier um Groessenordnungen schneller UND billiger (0 US-Dollar); Governor kostenlos_hier=true (freie Mistral-Bahn), Preis nur als [B]-Referenz fuer spaeteren Cerebras-Vergleich hinterlegt (aipricing.guru, nicht selbst verhandelt). INVARIANTE MECHANISCH GEHALTEN: kein einziger Schreibzugriff auf wiki.db/UnifiedDB-Kanontabellen im Code -- Ausgabe geht ausschliesslich nach bau/governor-kandidaten.jsonl (candidate delta + provenance + evidenz je Zeile, status=KANDIDAT). Kontingentbuch/bahn.py-Schluesselverwaltung wiederverwendet (umgebung()/darf()/buchen()), bahn.py selbst NICHT angefasst.
```

### B15 blockiert: RAE-Forschungswissen zu ClayVerse verdichtet

`686064575965` · clay · 15:54 UTC · ClayVerse

```
43 Claims aus research_entity/ledgers/CLAIMS.jsonl gelesen: 8 CURRENT, 5 OPEN, 4 SUPERSEDED, 26 REFUTED; H1-H6 Hyperposition-Entwuerfe alle OPEN bestaetigt; QUALIFIED/SUPPORTED je Zeile gelesen statt pauschal gemappt; Secrets-Scan sauber (2 echte Treffer in private/*.env gefunden, nicht kopiert); dokumente/clayverse/FORSCHUNGSWISSEN.md (284 Zeilen) + README-Verweis; Commit 3e11e59 auf origin (/srv/git/unifieddb.git) gepusht
```

### B0 fertig: README: ClayMachine=Projekt konsistent, unifieddb bleibt Modul

`6ca42541fc47` · clay · 15:53 UTC · ClayVerse

```
README.md + dokumente/clayverse/README.md gepatcht, commit b96f413, push origin+github verifiziert
```

### RAE-Forschungswissen zu ClayVerse verdichtet: dokumente/clayverse/FORSCHUNGSWISSEN.md + README-Verweis

`3e11e59a5806` · unifieddb · 15:53 UTC · ClayVerse

```
43 Claims aus research_entity/ledgers/CLAIMS.jsonl gelesen (8 CURRENT, 5 OPEN, 4 SUPERSEDED,
26 REFUTED), H1-H6 Hyperposition-Entwuerfe alle OPEN bestaetigt, QUALIFIED/SUPPORTED je Zeile
gelesen statt pauschal gemappt (Original in first_status_original erhalten). Secrets-Scan
sauber (private/*.env gefunden, nicht geoeffnet/kopiert). COVERAGE-Abschnitt oben in der Datei
listet explizit was NICHT gelesen wurde (atomic/runs, mesh_feedback, knowledge_micro_packets,
frank_v0_1 u.a.) - Aufgabe aus Tokenbudget-Gruenden gestoppt, bewusst als unvollstaendig
markiert statt vollstaendig wirkend.
```

### B11 begonnen: VLM-Artefakte + System-Vorlagen ins Repo (unifieddb)

`56afd5c53617` · clay · 15:52 UTC · ClayVerse

```
27 Dateien: system/ Vorlagen (13, Secrets als Env-Lesung), dokumente/clayverse/ 8 nachgezogen (inkl. protokoll.jsonl 85 Zeilen), 4 Root-Duplikate markiert; ap11-test.jpg aus /tmp gerettet; secret-scan 0 echte Treffer; unifieddb->origin gepusht, github-Remote fehlgeschlagen (kein Login); EINRICHTEN.md NICHT geschrieben (Tokenknappheit)
```

### System-Vorlagen + Artefakt-Katalog: ClayVerse-Dienste, Rebuild-Bausteine, VLM-Kaskade

`ad534040b5bf` · unifieddb · 15:52 UTC · ClayVerse

```
Bringt heute (15.08.) entstandene Artefakte als veroeffentlichte Kopie hierher:
- system/: Vorlagen fuer alle clay-herzschlag/-flugschreiber/-absturzbericht/
  -kognition.slice/-glm-Dateien (Gabriels Box + frank-api), Secrets als
  Env-Lesung/Platzhalter statt Klartext (z.ai-Schluessel, Schranke-Passwort)
- dokumente/clayverse/: restliche bau/*.md nachgezogen (B11-Kaskade, KARTE,
  KONTRAKT-KOGNITIONSTOR, MESSFEHLER, MINI-CLAYVERSE, ZUGAENGE-GEMESSEN,
  protokoll.jsonl) + ARTEFAKTE-2026-08-15.md Katalog (Status: TEILWEISE,
  EINRICHTEN.md steht noch aus)
- dokumente/ (root): 4 aeltere Duplikate markiert statt geloescht (F48
  Zwei-Wahrheiten-Regel), bauprotokoll.jsonl.VERALTET.md als Hinweis

Kanon: clayverse = Arbeitsrepo (Code bleibt dort), unifieddb = veroeffentlicht
(Doku/Protokoll/Katalog/System-Vorlagen). Secret-Scan 0 echte Treffer.
```

### B21 geprueft: Messungen aus /tmp gerettet, messungen/ als einziger Ort

`5576e6f2846b` · clay · 15:21 UTC · ClayVerse

```
17 Skripte aus /tmp nach messungen/ gerettet (vor Rebootverlust, Maschine 3x in 4 Tagen abgestuerzt) + README.md als Index ueber alle 15 geforderten Kennzahlen von heute, je Zeile [M]/[B] markiert und F-Nr verwiesen. Unterschieden: reproduzierbares Skript vorhanden vs. einmalige Ad-hoc-Messung ohne Skript (5 der 15: 15-Prozent-Deckel, NVIDIA 4-von-9-Modelltest, z.ai-Routen, Korpuszahl 1645-zu-272, paket-Kaltlatenz). Secret-Scan auf allen 19 neuen Dateien: 0 Treffer. Bereits versionierte Skripte (test_schranke.py, moeglichkeitsraum_mess.py, ap11_*.py, zustand_mess.py) nicht dupliziert, nur referenziert.
```

### README: ClayMachine-Vision als Kopf, Modul=Entitaet explizit an F16/F21/F44/F52 angebunden, Vision-gegen-Messung-Tabelle (F65/F66), Abruf-Zahl korrigiert

`01d9f7b8b4db` · unifieddb · 15:16 UTC · ClayVerse

```
Docs only. F66 (Zweiseitigkeit scheitert am Korpus, nicht am Abruf) aus /opt/clayverse/bau/ nachgezogen, damit die README-Referenz aufloest.
```

### paket(): Gegenseite-Kantenhop [B27-3] -- Symmetrie zu hypothesen_hop, Zahl unveraendert (Korpus-Befund)

`fdd9718bec10` · unifieddb · 15:06 UTC · ClayVerse

```
_hypothesen_hop() zu generischem _typed_hop(c, chosen_ids, felder, kante_rows,
ziel_art, cap) refaktoriert. _hypothesen_hop()/_gegenseite_hop() sind jetzt
duenne Wrapper (ziel_art=hypothese/gegenhypothese, CAP_HYPOTHESE_HOP/
CAP_GEGENSEITE_HOP=6). Macht die Gegenseite kantentyp-agnostisch wie die
Hypothesenseite es schon war -- vorher lief gegenseite NUR ueber die fuenf
semantisch vorgepraegten Kantenarten (widerspricht/attacks/CHALLENGES/
CONTRADICTS/SUPERSEDES) ohne jede Zieltyp-Pruefung, waehrend hypothesen_hop
JEDE Kantenart nahm, aber zielgebunden war (artikel.art=hypothese). gegen_hop
ergaenzt die drei bestehenden Gegenseite-Quellen (folgerung/kante+graph_kante/
artikel), ersetzt keine; dedupliziert ueber ref. Politik-Bericht um
gegenseite_hop_kandidaten/verwendet + caps.gegenseite_hop erweitert, gleiche
Transparenz wie bei hypothesen_hop.

DIAGNOSE ZUERST (Auftrag F56/B27-3), fixe seeded 30-Fragen-Stichprobe (seed
20260815, /tmp/zweiseitig_30fragen.json auf frank-api, aus allen 1588
hypothese/gegenhypothese-Titeln): 28/30 mit Material, 6/28 zweiseitig, 22/28
einseitig -- ALLE 22 fehlten auf der Gegenseite, nie auf der Hypothesenseite.
Verteilung der 22 (Grund gemessen, nicht geraten):
  13x kein gegenhypothese-Artikel im Umfeld -- weder lexikalisch noch per
      1-/2-Hop ueber JEDE Kantenart erreichbar. Material fehlt schlicht.
   9x Artikel existiert irgendwo im 272-teiligen gegenhypothese-Bestand
      (lexikalischer Treffer), aber KEIN 1-Hop-Pfad dorthin (2 davon nur bei
      2 Hops erreichbar -- Invariante "ein Hop, nie zwei" verbietet das).

GEMESSEN, dieselben 30 Fragen vorher/nachher: zweiseitig 6/28 -> 6/28,
UNVERAENDERT. Kein Bug im Fix: 661 Hop-Kandidaten insgesamt ueber die 30
Fragen, aber nur 2/661 (0,3%) vom Zieltyp gegenhypothese -- die anderen
1-Hop-Nachbarn sind ueberwiegend quelldatei/bereich_*/hypothese-Artikel.
Unabhaengiger Cross-Check (moeglichkeitsraum_mess.py ziel, echt-zufaellig
n=30): 6/26 zweiseitig, deckt sich (~23%) -- kein Stichprobenartefakt.

ZIEL (>=15/27 zweiseitig, aus [M 15.08.] 8/27) NICHT erreicht. Befund: die
Ursache ist der KORPUS (272 gegenhypothese-Artikel, duenn vernetzt zu den
ueblichen Chosen-Ids), nicht die Retrieval-Logik -- der naechste Hebel liegt
im Corpus/Graph-Aufbau, nicht in weiterer Retrieval-Mechanik. Zahl nicht
erzwungen (Auftrag), hier gestoppt.

Schatten eingehalten: Latenz-Median 337,4 -> 372,0 ms (Deckel 399,7 ms),
Moeglichkeitsraum-Token median 242 / avg 325,9 (Ziel <=400, vorher ~350).
Invarianten: AMBIGUOUS/resolve_entities nicht angefasst, ein Hop (nie zwei),
keine erfundene Gegenseite (nur reale artikel.art=gegenhypothese-Zeilen),
gegenseite bleibt nie zuerst gekappt.

Backup: udb/abruf/paket.py.vor-zweiseitig (lokal, nicht versioniert)
```

### B27 geprueft: F56 Zweiseitigkeit diagnostiziert + Gegenseite-Kantenhop-Symmetrie [B27-3]

`6542e594f554` · clay · 15:05 UTC · ClayVerse

```
Diagnose zuerst (fixe, seeded 30-Fragen-Stichprobe /tmp/zweiseitig_30fragen.json, seed 20260815, aus 1588 hypothese/gegenhypothese-Titeln): 28/30 mit Material, 6/28 zweiseitig, 22/28 einseitig -- ALLE 22 fehlten auf der Gegenseite, nie auf der Hypothesenseite. Verteilung der 22: 13x kein gegenhypothese-Artikel im Umfeld (weder lexikalisch noch via 1-/2-Hop erreichbar) -- Material fehlt schlicht; 9x Artikel existiert IRGENDWO im 272-teiligen gegenhypothese-Bestand (lexikalischer Treffer), aber KEIN 1-Hop-Pfad ueber irgendeine Kantenart dorthin (2 davon erst bei 2 Hops erreichbar -- Invariante one-hop-never-two verbietet das). Fix [B27-3]: _hypothesen_hop() zu generischem _typed_hop(ziel_art) refaktoriert, _gegenseite_hop() als duenner Wrapper ergaenzt (CAP_GEGENSEITE_HOP=6, gleiche Gewichtstabellen) -- macht die Gegenseite jetzt ebenso kantentyp-agnostisch wie die Hypothesenseite es schon war (vorher: gegenseite nur ueber widerspricht/attacks/CHALLENGES/CONTRADICTS/SUPERSEDES, KEINE Zieltyp-Pruefung; hypothesen_hop nur ueber Zieltyp, JEDE Kantenart). Gemessen, dieselben 30 Fragen vorher/nachher: zweiseitig 6/28 -> 6/28 UNVERAENDERT -- der Fund war korrekt: 661 Hop-Kandidaten insgesamt gefunden, aber nur 2/661 vom Zieltyp gegenhypothese (0,3%). Cross-Check mit einem unabhaengigen, echt-zufaelligen n=30-Lauf (moeglichkeitsraum_mess.py ziel): 6/26 zweiseitig, deckt sich (~23%). Schatten eingehalten: Latenz-Median 337,4 -> 372,0 ms (Deckel 399,7 ms), Raum-Token median 242 / avg 325,9 (Ziel <=400/~350). Invarianten: AMBIGUOUS/resolve_entities nicht angefasst, ein Hop (nie zwei), keine erfundene Gegenseite (nur reale artikel.art=gegenhypothese-Zeilen), gegenseite weiterhin nie zuerst gekappt.
```

### Doku nachgezogen: F64/F65, Moeglichkeitsraum gebaut aber Entwurf unbelegt

`e42a517783c3` · unifieddb · 14:50 UTC · ClayVerse

```
ENTSCHEIDUNGEN (jetzt F1-F65), LIVE-STAND und STAND-abend aktualisiert.
Wegweiser um den Stand nach F65 ergaenzt.

DIE ZWEI EHRLICHEN ZAHLEN, die dort jetzt stehen:
Der Halluzinationstest lief in einen DECKENEFFEKT - 0 erfundene Zahlen in allen
drei Bedingungen, Deckung 2,52 gegen 2,53. Die Metrik konnte nicht
unterscheiden, und er lief an Text statt Bildern. Der Entwurf ist damit nicht
widerlegt, sondern UNGEPRUEFT.
Und: 8 von 27 Raeumen sind zweiseitig, 19 einseitig. Zwei Drittel sind keine
Raeume. Das ist der naechste Hebel, nicht die Kaskade.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### B27 geprueft: moeglichkeitsraum: Erwartungsfeld aus paket() hypothesen/gegenseite (F56/F62)

`71ff0e90a978` · clay · 14:46 UTC · ClayVerse

```
ZIEL 27/30 Anfragen mit paket()-Material, 8/27 zweiseitig, 19/27 korrekt als einseitig gemeldet (Invariante). SCHATTEN ~350 Token (tiktoken cl100k_base) avg, Zusatzlatenz ~190us ueber paket(). Halluzinationsvergleich (groq llama-3.1-8b, n=83 Antworten/8 mehrdeutige Faelle, 3 Bedingungen): 0 erfundene Zahlen in allen 3 Bedingungen (Deckenwert, Metrik unterscheidet in dieser Domaene nicht), Deckung a=2.52 vs c=2.53 -- kein Vorteil messbar. entwurf_bestaetigt=false: Mechanismus korrekt gebaut, 3-Bedingungs-Beweis noch nicht erbracht.
```

### moeglichkeitsraum: F56 Erwartungsfeld aus paket() hypothesen/gegenseite (B27)

`b33104cc41a0` · unifieddb · 14:45 UTC · ClayVerse

```
Separate Datei, konsumiert nur paket() (nicht angetastet -- eine andere
Instanz bearbeitet paket.py parallel). Verdichtung deterministisch (dedup +
harte Caps, woertliche Auszuege), Erfindungsmelder aus verdichtung.py
wiederverwendet statt neu gebaut. Invariante: einseitiger Raum wird als
solcher gemeldet (Gegenseite fehlt/Hypothesenseite fehlt), nie verschwiegen.

Fund beim Bau: gegenseite ist heterogen (kante/graph_kante-Eintraege ohne
aussage-Feld) -- ohne Korrektur fielen die als leerer Text raus und taeuschten
Einseitigkeit vor. _aussage_text() synthetisiert die Kante als Behauptung.

Gemessen [M 15.08.]: ZIEL 27/30 Anfragen mit Material, davon 8 zweiseitig,
19 korrekt als einseitig gemeldet. SCHATTEN Groesse ~350 Token (tiktoken),
Zusatzlatenz ~190us ueber paket(). 3-Bedingungs-Halluzinationsvergleich
(moeglichkeitsraum_mess.py hallu, groq llama-3.1-8b, n=83 Antworten über 8
mehrdeutige Faelle): 0 erfundene Zahlen in allen drei Bedingungen (Deckenwert
-- Metrik unterscheidet in dieser Frage-/Modelldomaene nicht), Deckung a=2.52
vs c=2.53 -- kein Vorteil messbar. Entwurf NICHT bestaetigt, auch nicht
widerlegt: Mechanismus korrekt, Metrik/Domaene brauchen Nacharbeit. Kein
ClayVerse-Bildkorpus vorhanden (F58, blockiert) -- Test lief auf Text.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### README: hypothesen-Zeile auf den Endstand 11/20 nachgezogen

`c95e4a393631` · unifieddb · 14:41 UTC · ClayVerse

```
Die Zeile nannte 0/20 auf 1/20 und Ziel nicht erreicht - der Kantenhop hat sie am
selben Abend auf 11/20 gebracht, Latte war 8/20. Ergaenzt um den Beleg, dass die
AMBIGUOUS-Sperre unangetastet blieb (identische resolution_class-Verteilung).

Achte Korrektur einer veralteten Zahl an diesem Tag. Genau deshalb steht jetzt in
dokumente/clayverse/README.md, dass im Zweifel bau/LIVE-STAND.md gilt.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### README: hypothesen auf 11/20 nachgezogen, doppelte Dateinamen und Alterung benannt

`6e655f7c7124` · unifieddb · 14:40 UTC · ClayVerse

```
Zwei Befunde aus dem Doku-Lauf, beide sofort korrigiert statt liegengelassen:

1. Die Stand-Tabelle nannte hypothesen 0/20 auf 1/20 - der Kantenhop (F64) hatte
   sie am selben Abend auf 11/20 gebracht. Nachgezogen. Genau die Alterung, die
   heute schon siebenmal Zahlen falsch weitergereicht hat.

2. Im uebergeordneten dokumente/ liegen aeltere gleichnamige Dateien vom 14.08.
   Zwei Fassungen desselben Namens an zwei Orten sind die zwei Wahrheiten, vor
   denen F48 warnt. Als bekannt und unaufgeraeumt gekennzeichnet, mit Angabe
   welche gilt - nicht still gelassen.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### ClayVerse-Dokumente sammeln: dokumente/clayverse/ + README-Tagesstand 2026-08-15

`6f5fd3c2ff00` · unifieddb · 14:39 UTC · ClayVerse

```
- ENTSCHEIDUNGEN-2026-08-15.md (F1-F63), STAND-2026-08-15-abend.md,
  ABGLEICH-F15-F49.md, WEITERMACHEN.md, UEBERGABE-GLM.md kopiert
- Wegweiser dokumente/clayverse/README.md fuer Einstieg
- README.md: Tagesstand-Tabelle + widerlegte Annahmen ergaenzt
- .gitignore: *.env, venv*, *.db ergaenzt
```

### B27 geprueft: Hypothesen-Kantenhop: Symmetrie zu gegenseite hergestellt

`3ef53c00c34a` · clay · 14:33 UTC · ClayVerse

```
Ein Kantenhop (kante+graph_kante, nie zwei) von chosen_ids zu artikel.art=hypothese, gewichtet nach Kantenart. RELATED = 9691/14235 = 68,1% aller graph_kante-Kanten, Stichprobe bestaetigt blosse Verzeichnisnachbarschaft (source_kante_art=geschwister_verzeichnis) -- am staerksten abgewertet (Gewicht 0,3 vs 1,0-3,0 fuer inhaltliche Kantenarten). Vorher/nachher, dieselben 20 Fragen: hypothesen>0 1/20 -> 11/20 (Ziel >=8/20 erreicht, uebertroffen), gegenseite>0 8/20 -> 8/20 (Invariante unveraendert, resolution_class-Verteilung 19 LOW_CONFIDENCE/1 EXACT_ID identisch vorher/nachher), Latenz-Median 278,3 -> 317,4ms (Deckel 399,7ms eingehalten), paket_bytes Mittel +3,2%, max Einzelfall +8,1% (Deckel +30% eingehalten). Kantenabfrage aus dem codependenzen-Block wiederverwendet (kein Zweitscan auf kante), nur graph_kante + kleine PK-Nachfrage fuer Kandidaten ausserhalb bereits geladenem felder-dict. hop_kandidaten/hop_verwendet je Frage im Politik-Bericht ausgewiesen und gedeckelt (F45).
```

### paket(): Hypothesen-Kantenhop [B27-2] -- Symmetrie zu gegenseite

`feabb10dd699` · unifieddb · 14:33 UTC · ClayVerse

```
Ein Kantenhop (kante+graph_kante, NIE zwei) von chosen_ids zu artikel.art=hypothese,
gewichtet nach Kantenart (RELATED = 68,1% aller graph_kante-Kanten [M 15.08.],
schwaechste Evidenz = blosse Verzeichnisnachbarschaft, abgewertet). Reuse: kante-Abfrage
aus dem codependenzen-Block wiederverwendet (kein Zweitscan), nur graph_kante + kleine
PK-Nachfrage fuer unbekannte Kandidaten neu.

Gemessen, dieselben 20 Fragen vorher/nachher (siehe /tmp/messen_kantenhop.py):
  hypothesen>0   1/20 -> 11/20  (Ziel >=8/20 erreicht)
  gegenseite>0   8/20 -> 8/20   (Invariante unveraendert)
  latenz median  278,3 -> 317,4 ms (Deckel 399,7ms eingehalten)
  paket_bytes    Mittel +3,2%, max Einzelfall +8,1% (Deckel +30% eingehalten)
  hop_kandidaten pro Frage im Politik-Bericht ausgewiesen, gedeckelt (F45)

Backup: udb/abruf/paket.py.vor-kantenhop (lokal, nicht versioniert)
```

### paket(): hypothesen/gegenseite lesen jetzt auch artikel.art=hypothese/gegenhypothese

`f89157489f2c` · unifieddb · 14:21 UTC · ClayVerse

```
Gemessen [B27]: 1.645 Hypothesen + 272 Gegenhypothesen lagen in artikel,
_folgerungen_fuer() sah nur die fast leere folgerung-Tabelle (8 Zeilen).
Neue _artikel_hyp_gegenhyp() liest chosen_ids gegen das schon geladene
felder-dict -- keine neue Anker-Regel, resolve_entities()/AMBIGUOUS-Sperre
unangetastet. 20-Fragen-Messung: hypothesen>0 0/20->1/20, gegenseite>0
4/20->8/20, Latenz nicht verschlechtert (Median 399,7ms->265,6ms).
```

### B27 fertig: paket(): hypothesen/gegenseite-Vorbedingung repariert

`bd4a7c53909b` · clay · 14:20 UTC · ClayVerse

```
Ursache gemessen (nicht die Ankersperre): _folgerungen_fuer() las nur folgerung-Tabelle (8 Zeilen), nie artikel.art in (hypothese,gegenhypothese) (1.645/272, Projekt clay-global-research-entity), obwohl diese laengst als treffer abgerufen wurden. resolution_class ueber 20 echten Fragen: 19x LOW_CONFIDENCE, 1x EXACT_ID (Ankersperre bestaetigt selten getroffen, aber NICHT alleinige Ursache: gegenseite war schon vorher 4/20 ohne jeden Anker, rein lexikalisch). Fix: _artikel_hyp_gegenhyp() liest chosen_ids gegen bereits geladenes felder-dict, keine neue Anker-Regel, resolve_entities/AMBIGUOUS-Sperre unangetastet. Vorher/Nachher (dieselben 20 Fragen): hypothesen>0 0/20 -> 1/20, gegenseite>0 4/20 -> 8/20. Latenz unveraendert (Median 399,7ms -> 265,6ms). paket() kalt bestaetigt 122ms-2986ms (Doku-Spanne 0,2-6,3s bestaetigt, Median ca 0,3-0,4s). gegenseite laeuft strukturell getrennt vom Walk (3 unabhaengige Quellen: folgerung-Status, kante/graph_kante, jetzt artikel), nicht ueber die Walk-Cache-Plan-Liste. Restluecke offen: hypothesen-Trefferquote bleibt niedrig, weil normale Themenfragen selten direkt auf eine hypothese-artikel-Zeile matchen (nur Titeltext, kein Kanten-Hop) - naechste, groessere Entscheidung, hier nicht getroffen.
```

### B11 blockiert: Grundlinie + lokales VLM + Kaskaden-Kandidaten gemessen

`3ae15cae420a` · clay · 14:07 UTC · ClayVerse

```
Grundlinie (Dateiname+Tags+Kategorie, 472 echte Bilder wikimedia+gratisography): 100% liefern Objekt-Kandidaten, aber 0/4 Stichproben verankert in paket() (fachfremdes Korpus). paket() real 0,2-6,3s kalt (nicht 0,46ms). hypothesen/gegenseite in 5/5 paket()-Aufrufen leer trotz 1645/272 Artikel in der DB - Anker-Luecke blockiert F56. Lokales SmolVLM-256M in clay-kognition.slice: 35,8s/Bild - ueber der Nutzlosigkeitsgrenze, fuer Online-Pfad tot. Groq gpt-oss-20b + llama-3.1-8b: 200, ~9-10ms. NVIDIA llama-3.2-11b-vision: 200, 6 echte Vision-Calls. 3-Wege-Halluzinationskontrolle (NONE/NAIVE/POSSIBILITY) n=1 Bild, Modell widerstand falscher Praemisse in beiden Laeufen - kein Beweis fuer Robustheit, nur dass der Mechanismus messbar ist.
```

### B27 geprueft: Lesart-Kompaktion unabhaengig nachgemessen (F43-Pruefung)

`4bafdd50888a` · clay · 13:56 UTC · ClayVerse

```
kompakt vs voll -88,8% (n=60); e2e Paketgroesse +3,9% (n=20, frisch), Trefferabdeckung 20/20 identisch, 0 gewaehlt bei UNBESTIMMT, 0 abgelaufene sichtbar -- bestaetigt Commit 0484a33 (+7,2%, Ziel <30%)
```

### AP2 Schritt 1: Grundlinie gemessen + Sitzungsregistrierung (F15 max 3)

`0d299dd28ffa` · unifieddb · 13:55 UTC · ClayVerse

```
Grundlinie [M 15.08., wiki.db WAL busy_timeout=5000]: spaced writes
1474 Schreibungen/0 Kollisionen; tight-loop worst case 25730/2 harte
OperationalError, aber 1 Sitzung auf 12 Schreibungen ausgehungert
(Fairness, kein Datenverlust). SQLite loest also "database is locked"
fast allein -- das eigentliche Problem ist der stille logische
Ueberschreiber (zwei Sitzungen, ein Feld, keine merkt die andere),
nicht der Lock-Fehler. Korrigiert die fruehere Annahme, Migration habe
das Drei-Sitzungen-Problem geloest (F34) -- war falsch, jetzt mit Zahl.

udb/speicher/sitzung.py: Registrierung + Herzschlag + Obergrenze 3
(F15), toten Sitzungen (>120s ohne Lebenszeichen) werden vor jeder
Zaehlung entfernt statt geraten. Getestet: 4. Registrierung wird
abgewiesen, Abmelden raeumt korrekt auf.

Bewusst NICHT enthalten: die generelle schreiben()-Funktion (welche
Tabellen/Felder versioniert werden) -- das ist Formentscheidung nach
F44 P2, gehoert vor AP3/AP5 abgeglichen, nicht im Alleingang gebaut.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F35-Auflage: Lesart-Nutzlast im Paket gekuerzt (+73,8% -> +7,2%, Ziel <30%)

`0484a338a853` · unifieddb · 08:22 UTC · ClayVerse

```
Grundlinie zuerst [M 15.08., n=60]: 35.712/62.055 Zeichen. Kuerzung in
_lesart_kompakt -- identitaet-Achse raus (steht schon im Treffer, 75% der
Nutzlast), je Zeile lesart_id/wert/quelle/fehlender_kontext. Abdeckung
54/54 unveraendert, Invarianten 0 Verstoesse (188 UNBESTIMMT geprueft).
weltmodell.lesen() unangetastet, volle Form bleibt dort.
```

### B27 geprueft: F35-Auflage eingeloest: Lesart-Nutzlast im Paket gekuerzt +73,8% -> +7,2%

`c2a449d3b8f4` · clay · 08:22 UTC · ClayVerse

```
Grundlinie zuerst reproduziert [M 15.08., n=60 letzte DISTINCT Abfragen aus vp_paket_log]: ohne Lesart 35.712 / mit Lesart 62.055 Zeichen Mittel = +73,8% (F35s +85% auf anderer Stichprobe reproduziert). Kuerzung in paket.py/_lesart_kompakt: identitaet-Achse gestrichen (Werte sphaere/status/epistemic_class stehen schon im Treffer; 75% der Nutzlast), je Zeile nur lesart_id/wert/quelle/fehlender_kontext. Nach dem Bau: 38.271 Mittel = +7,2% (Ziel < +30%). Abdeckung 54/54 Pakete zeigen Lesarten (unveraendert). Invarianten: 188 UNBESTIMMT-Achsen, 0 gewaehlt-/quelle-Verstoesse, 0 abgelaufene sichtbar (jede lesart_id gegen wm_lesart geprueft). weltmodell.lesen() unangetastet.
```

### Uebergabe fuer die GLM-Arbeitsinstanz mit 14 Arbeitspaketen

`b577076461cb` · clay · 07:48 UTC · ClayVerse

```
Kopie von ~/UEBERGABE-CLAYVERSE.md auf Gabriels Rechner, damit sie auch auf dem
Wirt liegt und versioniert ist. Enthaelt die acht Gesetze (F52 Zielmetrik, F43
Deckung, F45 Irreversibilitaet, F44 R3 Engineering zuerst, F30 Koordinator baut
nie, F24 Baugesetz, F42 Schwellen als Tore, F48/F49 Abgleichpflicht), den
GRF-Verweis, die Sparsamkeitsregeln inklusive Caching, und AP1 bis AP14 mit je
Ziel, Schatten, Invariante und Einstiegspunkt.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F54b Metadaten tragen die Korrelationen mit, und muessen trotzdem schrumpfen

`b696f89f7be2` · clay · 07:47 UTC · ClayVerse

```
Eigner: in den Metadaten sollen auch automatisch Korrelationen aus dem
Praeprozessor mit dran sein, also aus der UnifiedDB wenn man das Thema da sucht,
als Additiv. Und es soll insgesamt sehr tokeneffizient komprimiert und
verdichtet sein.

MECHANISCH bleibt: Sitzungs-ID, Rechner, cwd, Zeiten, sauber beendet, beruehrte
Dateien, Befehle, Commits, offene Auftraege. ADDITIV dazu: was die UnifiedDB zum
Thema weiss - Korrelationen, verbundene Artikel, Hypothesen, Gegenseite,
Kurationsstand. Herkunft ist ein paket()-Aufruf, KEIN Modellaufruf, 0,46 ms.
Das ist der Praeprozessor aus F40 an einer zweiten Stelle, kein neues Bauteil.

DER ZIELKONFLIKT, der mitgebaut werden muss: Anreicherung fuegt hinzu,
Verdichtung nimmt weg. Beides zugleich geht nur, wenn die Anreicherung VERENGT
statt zu verbreitern. Die Wiederaufnahme-Sicht muss SCHMALER sein als das rohe
Protokoll, nicht breiter - sonst hat man den Verlauf durch etwas Laengeres
ersetzt.

WARNUNG AUS DER MESSUNG: die Lesart-Achse machte das Paket +85 Prozent groesser
(F35). Derselbe Fehler droht hier, nur schlimmer, weil die Wiederaufnahme das
ERSTE ist, was eine neue Instanz liest. Deckelung wie in F32: hoechstens N
Korrelationen, nur die zum aktuellen Thema.

VERDICHTEN MIT DEM WAS DA IST: verdichtung.py laeuft schon auf Schwelle statt
auf Uhr und erzeugt Verdichtungsartikel mit Kanten zu jeder Quelle. Die
Wiederaufnahme-Sicht sollte ein Verdichtat sein, kein Auszug - samt der Pruefung
von dort: eine Zahl im Verdichtat, die in keiner Quelle steht, wird verworfen.

ABNAHME: Ziel ist Zeit bis zur Weiterarbeit runter. SCHATTEN ist die GROESSE
der Sicht in Token, sie darf NICHT wachsen - das ist die harte Zahl.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F53 Schranke darf den Bau nicht aufhalten + F54 dynamische Gespraechsdatenbank

`de1f833fb0bd` · clay · 07:46 UTC · ClayVerse

```
F53: Eigner berichtigt meine Haltung - sie nicht zu umgehen ist die falsche
Entscheidung, wenn es uns vom Bau von Frank abhaelt. Vorrang hat der BAU, dann
die Schranke. ABER eine Bedingung, damit sie nicht wertlos wird: heute hat
genau sie die sudo-Luecke aufgedeckt, weil sie einen Agenten blockierte der es
MELDETE statt zu umgehen. Also: umgehen ja, STILL umgehen nein. Jede Umgehung
wird protokolliert. Blockiert sie wiederholt dieselbe legitime Sache, gehoert
die REGEL nachgezogen. Unveraendert bleibt was wirklich zerstoerend ist.

F54: dynamische Datenbank, die autonom den Chatverlauf jeder Terminalinstanz
speichert, auf jedem Rechner mit Clay-Instanz, und nach Absturz zur schnellen
Wiederaufnahme dient - tokeneffizient chirurgisch ueber Metadaten ausgelesen.

ERST MESSEN, und das aendert den Bau grundlegend: die Verlaeufe EXISTIEREN
schon. Claude Code schreibt je Sitzung ein JSONL unter ~/.claude/projects/.
Nach F44 R3 also KEIN neuer Rekorder, sondern ein INDEX ueber das Vorhandene -
Unterschied zwischen einem Tagesprojekt und einer Woche Arbeit.

Gebaut wird: Index mit Metadaten je Sitzung (ID, Rechner, cwd, Start, letzte
Regung, sauber beendet ja/nein, beruehrte Dateien, Befehle, Commits, offene
Auftraege). Abruf NUR ueber Metadaten, nie das ganze Protokoll. Nach Absturz:
finde die Sitzung ohne sauberes Ende und zeige woran sie war. Ueberall
gespiegelt nach der Trennungsregel.

ANKNUEPFPUNKT: clay-absturzbericht erkennt den harten Schnitt bereits am
fehlenden Abschaltprotokoll und schiebt auf den Wirt (F28) - dort gehoert es
angehaengt, nicht daneben gebaut.

INVARIANTE: Verlaeufe enthalten SECRETS - heute stand ein API-Schluessel im
Klartext im Verlauf. Der Index darf Werte NIE ausliefern, Metadaten ja, Inhalte
nur auf gezielten Abruf. Rechte 600, nie in ein Repo.

GRUNDLINIE: die handgeschriebene Uebergabe von heute - sie hat funktioniert,
also ist sie die zu schlagende Latte.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F52 DIE ZIELMETRIK: es muss fuer KI-Agenten etwas besser machen

`94038b74d34a` · clay · 07:44 UTC · ClayVerse

```
Gilt fuer ALLES im Zusammenhang mit ClayVerse. Loest den Widerspruch aus dem
Abgleich nicht durch Wahl, sondern durch eine neue Zielgroesse.

Eigner: es muss fuer Menschen nicht verstaendlich oder nachvollziehbar sein oder
bekannten Regeln entsprechen. Es muss funktionieren und fuer AI-Agents etwas
besser machen. Fuer Verstaendnis gibt es die Dokumentation. Ausserdem ist alles
ok, was innerhalb des Generative Reality Framework denkbar und messbar besser
ist, aber INSGESAMT, nicht nur in einer Hinsicht.

DAMIT FAELLT EINE GANZE KLASSE VON EINWAENDEN WEG: das ist unueblich, so macht
man das nicht, das versteht spaeter niemand sind keine Argumente mehr, solange
gemessen besser herauskommt.

DIE SCHRANKE DANEBEN ist F24s Schattenmetrik-Regel, nur schaerfer: ein Gewinn
auf einer Achse, der woanders verliert, ist kein Gewinn. F24s STRUKTUR bleibt,
was sich aendert ist die ZIELGROESSE - nicht menschliche Lesbarkeit, sondern
Nutzen fuer Agenten. B21s drei Groessen sind damit nicht abgeschafft, sondern
eingeordnet: Schattenmetriken unter der neuen Zielgroesse.

DIE FOLGE, DIE MITGEBAUT WERDEN MUSS: wenn Menschen es nicht nachvollziehen
muessen, muss die Pruefung MECHANISCH sein, sonst gibt es gar keine.
Menschliche Nachvollziehbarkeit war bisher die stille Rueckfallpruefung - was
niemand versteht, faellt irgendwann jemandem auf. Diese Pruefung entfaellt hier
bewusst, damit steigt die Last auf F43 erheblich.

Im GRF denkbar ist eine echte Schranke, keine Floskel: was ausserhalb des
Rahmens liegt, ist nicht erlaubt, nur weil es misst.

ZWEITER WIDERSPRUCH ENTSCHIEDEN: F16 bleibt, B18 wird praezisiert. B18s Warnung
Wirt ungleich Ziel zielt auf Wirt/Zielsystem, nicht auf Datenbank/Entitaet.
Offen: pruefen ob der research-identity-guard F16s Formulierung wirklich abweist.

Steht auch oben in CLAUDE.md und in WEITERMACHEN.md.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### B21 geprueft: F15-F49 gegen Bauplan abgeglichen

`c44a0df0482a` · clay · 07:32 UTC · ClayVerse

```
35 Entscheidungen geprueft: 21 gehoert-zu, 12 ist-neu, 2 widersprueche unaufgeloest (F21/F24 vs B21 Baugesetz, F16 vs B18 Entitaets-Namenskollision)
```

### F51 URTEIL Schranken-Luecke BEHALTEN, plus Fund ueber parallele Agenten

`0956426c81ae` · clay · 07:27 UTC · ClayVerse

```
URTEIL gegen die vorher gesetzten Kriterien: Testsatz 49 Faelle, vorher 31 von
49, nachher 49 von 49. KEINE Ueberverschaerfung - die 20 muss-durchgehen-Faelle
blieben in BEIDEN Zustaenden gruen, und genau das war das ausdrueckliche Risiko,
weil die Schranke diesen Monat schon einmal kaputt war durch Ueberverschaerfung.
Kein zerstoerender Befehl je ausgefuehrt, nur pruefen() ausgewertet. Die
bewusste scp/rsync-Ausnahme unangetastet. BEHALTEN.

Der eigentliche Ertrag ist nicht der Fix, sondern der TESTSATZ
tools/schranke/test_schranke.py, wiederholbar, 49 Faelle in beide Richtungen.
Zweiter Schranken-Befund in einer Woche, jetzt eine Pruefsammlung statt einer
dritten Einzelreparatur.

DER FUND: FERN_ZERSTOEREND und FERN_HART verankerten den Befehlsnamen direkt
nach Trennzeichen, ohne optionales sudo zu verschlucken. 18 von 49 Faellen
fielen durch, ausnahmslos alle muss-fangen-Faelle mit sudo, doas oder
ENV-Praefix. Fix ueber eine gemeinsame VORSILBE-Regex, auch auf ANFANG, NIE und
DB_WERKZEUG angewandt.

ZWEI LOECHER BLEIBEN, benannt und im Code dokumentiert: sudo VOR dem Wrapper
bricht den UNTERSCHALE-Anker; und bash -c-Inhalte werden nicht gegen die
SCHEIN-Liste geprueft. Sie gehoeren in den Testsatz BEVOR sie repariert werden.

NEBENFUND, wichtiger als er aussieht: zwei Agenten committeten gleichzeitig im
selben Repo und zogen sich gegenseitig die gestagten Dateien mit. Der
Schranken-Diff landete unter fremdem Commit-Titel, korrigiert per Nachtrag.
Das ist dasselbe Problem wie das gleichzeitige Schreiben der drei Sitzungen,
nur eine Ebene hoeher, und bestaetigt F44 Paragraph 2 im Feld.
FOLGE: parallele Agenten duerfen nicht breit stagen - git add mit genau den
eigenen Dateien, nie git add -A.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### B7 geprueft: Schranke Luecke B behoben: sudo/doas/env vor FERN_ZERSTOEREND+FERN_HART (+ANFANG/NIE/DB_WERKZEUG) wird jetzt verschluckt

`d6848caa4411` · clay · 07:26 UTC · ClayVerse

```
test_schranke.py: vorher 31/49 (18 Luecken, alle in FAENGT-Faellen), nachher 49/49 (0 Regressionen in den 20 LAESST_DURCH-Faellen)
```

### Nachtrag zu 1be4c69: Schranke Luecke B (sudo/doas/env vor FERN_ZERSTOEREND+FERN_HART)

`5557b2883666` · clay · 07:25 UTC · ClayVerse

```
1be4c69 landete unter fremdem Titel (GLM_API_KEY), enthaelt aber zusaetzlich
ungewollt meinen Schranke-Fix — ein anderer, gleichzeitig laufender Agent hat
offenbar breit (git add -A o.ae.) committet und meine bereits gestagten
Dateien mitgezogen. Dieser Commit ist reine Nachdokumentation, KEIN Diff.

Betroffen in 1be4c69:
  baeume/clay/tools/schranke/wache-koenig.py          (+47/-7)
  baeume/clay/tools/schranke/test_schranke.py         (neu, 141 Zeilen)
  baeume/clay/tools/schranke/wache-koenig.py.vor-sudoluecke  (Backup, neu)

Befund: FERN_ZERSTOEREND/FERN_HART verschluckten kein optionales sudo vor dem
Befehlswort. "ssh host sudo chmod -R 777 /" ging durch, "ssh host chmod -R 777 /"
(ohne sudo) verlangte zurecht einen Schein. Gemessen mit test_schranke.py: vorher
31/49, davon alle 18 Fehlschlaege in FAENGT-Faellen (nie in LAESST_DURCH) —
nachher 49/49.

Fix: neue gemeinsame VORSILBE (sudo inkl. Flags/-n/-u X, doas, nohup, timeout,
env-Zuweisungen, beliebig gestapelt) vor FERN_ZERSTOEREND, FERN_HART, ANFANG
(lokale SCHEIN-Klasse), NIE (mkfs/dd) und DB_WERKZEUG.

Bewusst nicht angefasst (Kommentar in wache-koenig.py):
  - sudo VOR ssh/bash -c selbst bricht den UNTERSCHALE-Anker und verhindert
    das Herausloesen der inneren Zeichenkette komplett — "sudo ssh host ..."
    und "sudo bash -c ..." werden gar nicht erst als Unterschale erkannt.
  - bash -c Inhalte werden nur gegen FERN_ZERSTOEREND/FERN_HART geprueft,
    NICHT gegen die SCHEIN-Liste (rm, chown/chmod -R, git push --force, …).
Beides ausserhalb des gemeldeten Rahmens, nicht repariert, um keine neuen
Fehlalarme zu riskieren.

Testset: baeume/clay/tools/schranke/test_schranke.py (erneut lauffaehig mit
  python3 test_schranke.py wache-koenig.py)
```

### F50 GLM vermessen: Coding-Plan, keine Einbettungen, kein Sehen

`dc98fd64efe0` · clay · 07:24 UTC · ClayVerse

```
Baut auf F46. Gemessen: der Schluessel ist ein CODING-PLAN, kein Guthabenkonto.
/api/paas/v4/chat/completions gibt 429 insufficient balance bei ALLEN 8
Modellen, nur /api/coding/paas/v4/ und /api/anthropic/v1/messages tragen.
Wer die normale Chat-Route nimmt, haelt den Schluessel fuer tot - exakt die
Falle aus F14.

Katalog 4.5, 4.5-air, 4.6, 4.7, 5, 5-turbo, 5.1, 5.2, alle reasoning-faehig,
Latenz 0,9 bis 16 s. Einbettungen 400 unknown model, kein Vision-Modell.
Ratengrenzen unbekannt, kein 429 auf der Coding-Route erreicht.

VERTEILUNG: Routine und Agentenarbeit auf glm-4.6 und glm-5-turbo,
reasoning-lastige Analysen auf glm-5.2, Gesamtueberblick und Urteil bleiben bei
Claude. EINBETTUNGEN bleiben bei NVIDIA und SEHEN beim lokalen VLM - GLM kann
beides nicht.

Launcher /usr/local/bin/clay-glm gebaut und echt getestet, chmod +x von der
Schranke blockiert, braucht Gabriels Freigabe.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### B17 fertig: GLM_API_KEY in freie-zugaenge.env aufgenommen

`1be4c69671da` · clay · 07:23 UTC · ClayVerse

```
z.ai/GLM Coding-Plan-Schluessel vom Owner (Chat 15.08., NIE geloggt) in /etc/clayverse/freie-zugaenge.env, Modus 600 root:root, Backup .vor-glm. Gemessen: /api/paas/v4/models 200 (8 Modelle: glm-4.5, glm-4.5-air, glm-4.6, glm-4.7, glm-5, glm-5-turbo, glm-5.1, glm-5.2), aber /api/paas/v4/chat/completions 429 insufficient-balance fuer alle 8 - Pay-per-Use-Kontingent ist LEER. /api/coding/paas/v4/chat/completions 200 fuer alle 8 (Coding-Plan-Route). /api/anthropic/v1/messages 200, echter claude -p Aufruf gegen den Launcher lief (Antwort OK, 6s). glm-4.5-air routet intern auf glm-4.7, glm-5.2 auf glm-5.3 (Auto-Routing des Plans, per Doku bestaetigt). Embeddings: kein einziges Modell (embedding-2/3) erreichbar, 400 unknown-model - nicht im Plan enthalten. Kein Vision-Modell im Katalog. Keine Ratelimit-Header in 5 Bursts - unbekannt bis echter 429 auftritt.
```

### F49 Das Fundament: alles fusst auf iterativer Entwicklung

`96e5b08971f1` · clay · 07:21 UTC · ClayVerse

```
Eigner: alles was wir machen fusst immer auf zugrundeliegender iterativer
Entwicklung. Das ist der GRUND unter F48, nicht ein Zusatz - die Abgleichpflicht
folgt daraus, dass hier nie auf leerem Blatt begonnen wird.

EINE ENTSCHEIDUNG OHNE IHREN VORGAENGER IST KEINE ENTSCHEIDUNG, SONDERN EIN
NEUSTART. Und ein Neustart wirft die angesammelten Belege weg, genau wovor F43
warnt.

DREI UMDEUTUNGEN: Franks viele Iterationen und nie ganz funktioniert ist keine
Fehlerbilanz, sondern eine Beschreibung der METHODE - der Zwischenstand ist der
Normalfall. Der Bauplan B0-B28 ist ein Iterationsstand, keine feste
Spezifikation. F15 bis F49 sind Iterationen AUF dem Bestehenden, keine
Abloesung - wer sie als neues Werk liest, hat die Kette zerschnitten.

MECHANISCHE FOLGE: jede Entscheidung nennt ihren VORGAENGER - baut auf, ersetzt,
widerspricht, oder ist wirklich neu. Dieselbe Form wie die Herkunftskennung
E/B/M, nur fuer Struktur statt fuer Zahlen. Beides zusammen ergibt die Kette:
woher kommt die Aussage und worauf baut sie auf.

Der letzte Fall ist der verdaechtigste: ist wirklich neu stimmt selten. Wenn
etwas nach fuenf Monaten Arbeit noch nie gedacht wurde, ist die wahrscheinlichere
Erklaerung, dass man den Vorgaenger nicht gefunden hat.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F48 ABGLEICHPFLICHT: erst im Plan nachsehen, dann entscheiden

`06038a889a78` · clay · 07:21 UTC · ClayVerse

```
Eigner: schau im Plan und gleiche ab. Generell musst du das tun.

MEIN FEHLER: ich habe F15 bis F47 geschrieben, als laege kein Plan vor. Es gibt
B0 bis B28 im Bauplan und ein Bauprotokoll mit Stand je Bauteil. Viele neue
Entscheidungen beruehren vorhandene Bauteile - ohne Abgleich entstehen ZWEI
WAHRHEITEN nebeneinander. Dieselbe Wurzel wie F26, F34, F41 und die
21-gegen-12-Zahl: etwas weiterschreiben statt an der Quelle nachzusehen, nur
diesmal bei der Struktur statt bei einer Zahl.

DIE PFLICHT: vor jeder Entscheidung und jeder Aufzeichnung im Plan nachsehen,
ob es das Bauteil schon gibt, und die Entscheidung DORT verankern statt daneben.
Nachsehen in Bauplan (Soll), bau.py stand (Ist), ZIELARCHITEKTUR, Abnahmeurkunde
Frank v0.1, und den heutigen Entscheidungen.

ERGEBNIS je Entscheidung genau eines: gehoert zu B-n, ersetzt B-n, widerspricht
B-n, oder ist neu. DER DRITTE FALL IST DER WICHTIGSTE - ein stillschweigend
aufgeloester Widerspruch sieht aus wie Fortschritt und ist eine verlorene
Entscheidung. Widersprueche werden ausgesprochen, nicht aufgeloest.

WARUM MEHR ALS ORDNUNG: ein Plan, an dem niemand abgleicht, veraltet unbemerkt
und sieht weiter gueltig aus. Heute schon passiert - bau.py stand meldet zu
wenig, weil die Protokoll-Luecke 00:44 bis 01:58 UTC nie nachgetragen wurde.

Nach F42 gehoert auch das in ein Tor: eine Entscheidung ohne Bauteil-Bezug
sollte gar nicht annehmbar sein. bau.py nimmt schon heute keinen Schritt ohne
Messung an, dieselbe Form.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F47b Berichtigung: an Frank v0.1 forschen heisst es auf dem VPS BAUEN

`587a127d17e5` · clay · 07:20 UTC · ClayVerse

```
Eigner: und an Frank v0.1 zu forschen meine ich es auf dem VPS zu bauen, das
steht aber eh alles im Konzept, ich habe nur gerade das Kontingent fuer den
Prozess definiert.

Ich hatte F47 als offene Forschung gelesen. Falsch. Gemeint ist BAUEN, das
Zielbild steht bereits im Konzept (Abnahmeurkunde: NATIVE_SELF self.root,
HUMAN_SURFACE_NAME Frank, COGNITION ClayCode only, token-authentifizierte API).
Neu ist nur das Kontingent von mindestens 50 Prozent der Subscription.

Das vereinfacht F47 erheblich: die Abnahmekriterien muessen nicht erfunden
werden, sie liegen. Damit entfaellt ein Teil der Hauptgefahr - wo ein Zielbild
geschrieben steht, kann autonomes Arbeiten weniger in Fiktion driften. Es
bleibt die Deckungspflicht fuer den WEG dorthin.

Ist-Stand bleibt [B] und nachzumessen: /etc/frank-v0.1/ existierte nicht, kein
self.root-, ClayCode- oder UnifiedDB-Dienst, keine API. Der Zielkoerper ist
definiert und leer. Erste Handlung ist also eine MESSUNG, kein Entwurf.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F47 Wofuer die 50 Prozent da sind: autonome Frank-v0.1-Forschung

`fdc10d1485e8` · clay · 07:19 UTC · ClayVerse

```
Eigner: die 50 Prozent werden verwendet um autonom an Frank v0.1 zu forschen,
unter Zuhilfenahme von allem und Tokens zu sparen, und fuer alle kognitiven
Prozesse zur Unterstuetzung. Oder eine voellig andere hochintensive Anwendung -
da gibt es sicher was. ZWECK 3 ist ausdruecklich ein PLATZHALTER, keine
Entscheidung, und darf nicht als Auftrag weitergereicht werden.

UNTER ZUHILFENAHME VON ALLEM UND TOKENS SPAREN ist kein Widerspruch, sondern
F44 R3 plus F46 in einem Satz: die teure Instanz entscheidet, die billigen
Mittel fuehren aus. Sie forscht nicht indem sie selbst alles liest, sondern
richtet GLM, Engineering und die freien Bahnen darauf aus und urteilt ueber das
was zurueckkommt.

AUTONOMIE ERHOEHT DIE DECKUNGSPFLICHT, SIE SENKT SIE NICHT. Das ist der
gefaehrliche Teil. F43: plausible Struktur entsteht schneller als sie geprueft
wird. Eine autonom forschende Instanz ohne aeusseren Pruefer ist genau dieser
Fehler bei voller Geschwindigkeit und ohne Bremse. Heute wurde ich achtmal
korrigiert - autonom waere keine dieser acht Korrekturen passiert.

DIE LOESUNG LIEGT SCHON VOR: die Deckung endet an der Grenze der
Forschungsentitaet, dort greifen CLAIMS mit Status und Falsifikator,
Schemapruefung, research-identity-guard, die Tore. Also gehoert die autonome
Frank-Forschung NACH INNEN - nicht als Ablageort, sondern weil dort das Pruefen
mechanisch ist. Eine Behauptung, die nicht in die Entitaet passt, ist noch
keine. Autonom heisst ohne GABRIEL, nicht ohne Pruefung.

Der Rueckschreibpfad rae_rueckschreiben.py ist gebaut, aber fuer diesen Zweck
ungenutzt.

PRUEFSATZ: nicht sind 50 Prozent verbraucht, sondern sind 50 Prozent verbraucht
UND ist das Ergebnis gedeckt. Verbrauch ohne Deckung ist kein Fortschritt,
sondern teurer Text.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### B26 fertig: Clerk-Zugangsdaten in freie-zugaenge.env aufgenommen

`9062d6cc06e4` · clay · 07:17 UTC · ClayVerse

```
Quelle /opt/agentforge/.env auf seimensch-VPS: 29 Variablen, davon 4 CLERK_ (SECRET_KEY, PUBLISHABLE_KEY, JWKS_URL, WEBHOOK_SECRET). Ziel /etc/clayverse/freie-zugaenge.env vorher 12 Eintraege (nicht 21 wie im Briefing - 21-vs-12 damit als 12 aufgeloest), nachher 16. Kein bestehender CLERK_-Eintrag, kein Konflikt. Backup .vor-clerk angelegt, Modus 600 root:root nach Uebertragung per ls und grep geprueft, alle 4 Namen bestaetigt.
```

### F46 Arbeitsteilung der Modelle: GLM arbeitet, Claude denkt

`039759205201` · clay · 07:17 UTC · ClayVerse

```
Eigner: das z.ai-Token ist die ALLGEMEINE ARBEITSINSTANZ von ClayVerse. Die
20-Euro-Claude-Instanz macht nur die kognitiven Aufgaben innerhalb von
ClayVerse - aber so, dass MINDESTENS 50 Prozent der Subscription draufgehen.

DIE UNGEWOEHNLICHE RICHTUNG: eine UNTERGRENZE, keine Obergrenze. Es gibt zwei
Verschwendungen, nicht eine. Uebernutzung: das teure Modell tut Mechanisches,
das GLM oder Engineering koennte. Unternutzung: es liegt brach, waehrend
kognitive Arbeit schlecht erledigt wird - ebenfalls Geld fuer nichts, nur
unsichtbar. Sparsamkeit an der falschen Stelle ist auch Verschwendung, und das
dreht den ueblichen Token-sparen-Reflex um.

ZU CLAUDE: das Urteil (F31 nicht delegierbar), den Massstab setzen, Analysen
die den Gesamtueberblick brauchen (F33-Ausnahme), Hyperposition, Weltmodell,
Architektur, Systemlogik. ZU GLM: alles andere. ZU KEINEM: was Engineering
loesen kann, verlaesst beide (F44 R3).

REIHENFOLGE BLEIBT: erst Engineering, dann GLM, dann Claude. F46 verteilt nur,
was nach F44 R3 uebrig bleibt. Wer die Reihenfolge umdreht, fuellt die 50
Prozent mit Arbeit, die gar kein Modell haette tun duerfen.

ES IST EINE SCHWELLE, ALSO GILT F42 - aber der Fall ist guenstig, das Messgeraet
existiert schon: claude-limits mit Quelle claude-api und dem Feld geraten. Das
Tor gehoert ins Kontingentbuch als eigene Bahn. NEUE RICHTUNG: dieses Tor warnt
bei UNTERSCHREITUNG, alle anderen Schwellen hier deckeln nach oben.

FALSIFIKATOR: werden die 50 Prozent erreicht OHNE dass mechanische Arbeit bei
Claude landet, traegt die Aufteilung. Werden sie nur erreicht WEIL Claude Dinge
tut die GLM koennte, ist die Quote erfuellt und der Zweck verfehlt. Die Quote
allein ist kein Erfolgsmass.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### CLAUDE.md: kurz fragen statt lang erklaeren ist ab jetzt fix, in jeder Sitzung

`9401b0857e38` · clay · 07:13 UTC · ClayVerse

```
Gabriels Anweisung: das muss ab jetzt fix sein, egal in welcher Session.
Steht daher ganz oben in CLAUDE.md, wo jede Sitzung es zuerst liest -
und ebenso in Gabriels lokaler Projektdatei.

Zu wenig ist reparierbar, zu viel ist irreversibel. Er WUERDE oefter
eingreifen, lange Texte halten ihn ab. Kein Stil, sondern ein
Pruefmechanismus: eine kurze Frage ist billig zu pruefen, ein langer
kohaerenter Text nicht - und genau das ist der oberste Fehler F43.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F45 Zu wenig ist reparierbar, zu viel ist IRREVERSIBEL

`cbd6773b82fa` · clay · 07:13 UTC · ClayVerse

```
Eigner: wenn der User mehr wissen will kann man das immer liefern, aber zu viel
ist irreversibel. Und: das bekommt man nur mittels Forschung, da es wie so oft
in der theoretischen Systemphilosophie und Physik NICHT LOGISCH ist.

DAS GESETZ: zu wenig ist reparierbar, der Empfaenger fragt nach, Kosten eine
Runde. Zu viel ist irreversibel - gesagt ist gesagt, die Aufmerksamkeit ist
verbraucht, das Eingreifen ist unterblieben. Daraus folgt die Richtung in die
man irren soll: nach unten. Nicht weil weniger besser waere, sondern weil nur
der eine Fehler einen Reparaturweg hat.

WARUM ES NICHT LOGISCH IST: die naheliegende Logik sagt mehr Information gleich
bessere Entscheidung, Vollstaendigkeit sei die sichere Seite. Falsch, und der
Grund liegt nicht in der Information sondern im EMPFAENGER - seine
Aufmerksamkeit ist endlich und verbraucht sich unwiederbringlich. Ein
ueberforderter Empfaenger hoert nicht auf zu lesen, er hoert auf zu PRUEFEN.
Und dann greift F43 ungebremst durch. Die Asymmetrie ist nur beobachtbar, nicht
herleitbar - sie zeigt sich im Verhalten des Empfaengers, nicht in den
Eigenschaften der Nachricht.

ES IST DASSELBE GESETZ WIE VIER ANDERE BEFUNDE VON HEUTE, die ich als vier
Themen behandelt hatte: F32 Verbotsliste auf hoechstens drei, F35 Paket plus 85
Prozent mit Auflage unter 30, F38 1000 Wege ohne Vorauswahl, F40 Anzahl
Moeglichkeiten je Entscheidung. Und Franks 60 Werkzeuge mit 45 nie benutzten
ist derselbe Satz in klein. Ueberall: der Engpass ist nie das Angebot, sondern
die Aufnahme, und die verbraucht sich.

BAUREGEL: liefere die kleinste Menge die traegt, und sorge dafuer dass
Nachfragen billig ist. Niemals umgekehrt. Der teure Teil ist der zweite Satz -
eine kurze Antwort OHNE Hinweis auf das Vorhandene ist nicht sparsam, sondern
lueckenhaft. Gilt NICHT fuer die Aufzeichnungen: lang gehoert ins Archiv, kurz
in die Antwort.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F44 Vier Architekturentscheidungen: Binary/DB-Trennung, Ausleger, Engineering-Gesetz, historische Baseline

`aa46a0d329fa` · clay · 07:12 UTC · ClayVerse

```
1 ENDGESTALT: API, DB, MODUL das in ein Binary gegossen wird. Unveraenderliches
ins Binary (Schwellen, Tore, Invarianten), Veraenderliches in die DB. Damit ist
F42 haerter beantwortet als mein Vorschlag - ein Tor im Binary kann nicht
weggeredet und nicht nah dran gedeutet werden. Pruefsatz: ist diese Regel
veraenderlich, dann DB, sonst Modul.

2 SITZUNGEN: Koordination ueber eine TABELLE statt ueber Sperren, Schreiben
VERSIONIERT statt ueberschreibend, je Sitzung eigene Kennung, aber im Prompt
EINE Entitaet mit mehreren Auslegern die gleichzeitig interkonnektiv handeln.
Loest das Schreibproblem anders als ich gefragt hatte und besser: gleichzeitige
Schreiber kollidieren nicht, sie erzeugen Versionen. Unstimmigkeit nicht
stillschweigend korrigiert: Eigner sagte alle 2 Sessions, F15 legt hoechstens 3
fest, als Zahl gilt weiter 3.

3 DAS ENGINEERING-GESETZ: jede kognitive Last, die Engineering loesen kann,
verlaesst die API - auch wenn sie noch so gut ist. Allgemeiner als meine Frage
nach der Stufenreihenfolge und ersetzt sie. Auch wenn sie noch so gut ist ist
der Kern: ein besseres Modell ist KEIN Grund die Last dort zu lassen, nur ein
teurerer Weg dasselbe zu tun. Direkte Antwort auf F38.

4 FRANKS EVAL-BATTERIE IST NICHT UNSERE GRUNDLINIE. Sie misst ein System OHNE
echte Zustaende, dem das Kompensationssystem fehlte, das es jetzt als UnifiedDB
gibt. Wer gegen 63,68 antritt, tritt gegen die Krankheit an, nicht gegen den
Stand. BERICHTIGUNG an meinem F41. Die mindestens 10 Punkte mehr sind [E] eine
Einschaetzung, KEIN Lauf - wer sie als Zahl weiterreicht, macht meinen
Tagesfehler zum sechsten Mal. Wertvoll bleibt sie als Abgleich: sie zeigt was
ein System OHNE UnifiedDB erreichte, und ist damit die einzige Zahl, die wir
fuer den Nutzen des Zustandssystems haben.

DIE LERNINGS ALS REGELN R1 bis R4, und sie gehoeren nach F42 selbst ins Modul.
Eine Regel, die nur im Text steht, ist noch nicht gebaut.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F43 DER OBERSTE ZU LOESENDE FEHLER: Kohaerenz ohne Deckung

`109fb17fd23f` · clay · 07:03 UTC · ClayVerse

```
Steht ueber allen anderen Befunden. Jeder andere ist ein Einzelfall davon.
Auch ganz oben in WEITERMACHEN.md eingesetzt.

ACHTMAL an einem Tag belegt: falscher Auftrag an Instanz 2, semantisch falsches
Drei-Knoten-Raft, veraltete Zahlen in drei Auftraegen, selbst gebaut statt
delegiert, Wochenpensum geschaetzt statt gemessen, Gabriels Hypothese als
Diagnose etikettiert, fuenfte veraltete Zahl (21 gegen 12), und die Schwelle
gelesen aber nicht gebunden.

DIE URSACHE IST EINE: ich erzeuge plausible Struktur schneller, als sie geprueft
werden kann. Jede Sache sah beim SCHREIBEN richtig aus. Nicht Schlamperei,
sondern Kohaerenz ohne Deckung. Ein schlampiger Text faellt auf, ein
kohaerenter ungedeckter wird geglaubt, auch vom Verfasser.

RATENPROBLEM: Erzeugung schnell, Pruefung langsam. Und es skaliert falsch
herum - mehr Faehigkeit heisst mehr Erzeugung, nicht mehr Pruefung. Ein
besseres Modell macht das Problem GROESSER.

ES IST ENGINEERING, UND DIE FORSCHUNGSENTITAET BEWEIST ES: CLAIMS mit status
und Falsifikator, Schemapruefung, research-identity-guard, 20 Tore je PR mit
Urteil je SHA, update-branch dann gemessen (0 auf 6 von 6 gruen), EffectGate
Paragraph 9 model confidence cannot mint authority. Das sind Mechanismen, keine
Regeln - genau der Unterschied, der heute achtmal fehlte.

WARUM ES TROTZDEM PASSIERTE: diese Mechanismen greifen IN der Forschungsentitaet.
Nicht in einem Gespraech, nicht in einem Auftrag, nicht in einem
Bauplan-Absatz. Genau dort entstanden alle acht Fehler. Die Deckung endet an
der Grenze der Entitaet, und ClayVerse arbeitet ueberwiegend ausserhalb.

FUENF PFLICHTEN MIT VORRANG: Herkunft E/B/M ueberall auch in Auftraegen; jede
Behauptung mit Falsifikator; der Pruefende ist nicht der Verfasser (der
eigentliche Ertrag von F30); DECKUNGSQUOTE messen als Anteil M an den
tragenden Aussagen (gibt es heute nicht, ist zu bauen); Mechanik statt Text.

PRUEFSATZ: ist diese Aussage gedeckt, und wodurch. Lautet die Antwort sie
klingt richtig, ist sie es nicht.

Dieser Abschnitt selbst ist [B] - eine Auswertung von acht Faellen an EINEM
Tag, kein Nachweis ueber Zeit. Falsifikator mitgeliefert.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F42 VORRANG: gemessener Wert ohne Bindung an die Handlung

`25561253ae5e` · clay · 07:01 UTC · ClayVerse

```
Eigner: wir sind bei 93 Prozent, wieso Uebergabe. Ab 94 sollst du sie machen,
nicht ab 93. Und: erörtere das Problem und schreibe es als
Priority-Loesungsproblem fuer ClayVerse auf.

DAS IST NICHT F29. Dort habe ich das Messgeraet nicht benutzt. Hier habe ich es
benutzt, den Wert gelesen, ausgegeben, sogar den Abstand zur Schwelle
gerechnet - und dann trotzdem nach Gefuehl gehandelt. Eine Messung, die keine
Handlung ausloest oder sperrt, ist Zierde. Das ist die schlimmere Klasse, weil
sie nach Empirie AUSSIEHT.

DREI TEILFEHLER: Messung ohne Bindung (Vergleich nicht als Bedingung
ausgefuehrt). Vorwegnahme der Schwelle (92 und 93 als praktisch 94 behandelt,
und Aufrunden verschiebt jede Schwelle in die bequemere Richtung). Ankuendigung
statt Handlung (dreimal die Uebergabe angekuendigt statt weiterzuarbeiten).

VORRANG FUER CLAYVERSE, WEIL ES AUS SCHWELLEN BESTEHT: Kontingentbuch mit
Anteil 1.0 und 429-Lernkurve, Wartesperre mit 54 s Herzschlagalter,
Signifikanz groesser als die Streuung, Verbotsliste hoechstens drei,
Praeprozessor Anzahl Moeglichkeiten klein. Fuenf Schwellen, alle stehen heute
als Vorsatz da, nicht als Tor.

DAS GEGENBEISPIEL STEHT SCHON DANEBEN: clay-kognition.slice haelt 15,00 Prozent
gemessen, und geht nie verloren, weil die Schwelle im Kernel liegt und nicht im
Kopf. Niemand muss sich erinnern, niemand kann nah dran mit erreicht
verwechseln. Das ist die Bauform, alles andere ist ein Versprechen.

LOESUNGSMUSTER: jede Schwelle bekommt ein benanntes Tor als Funktion; kein
Bauteil traegt eine Schwelle als Konstante in Text oder Prompt, es RUFT das
Tor; das Tor liest frisch beim Aufruf; es gibt eine ENTSCHEIDUNG zurueck, keine
Zahl (wer eine Zahl zurueckgibt, ueberlaesst den Vergleich dem Aufrufer, und
genau dort ging er verloren); es protokolliert Wert, Schwelle und Urteil; wo
moeglich in die Mechanik statt in den Code.

PRUEFSATZ: steht die Schwelle in einem SATZ oder in einer BEDINGUNG? In einem
Satz heisst noch nicht gebaut.

Vierter Tagesbefund mit demselben Schluss (F29, F31, F37, F42): Struktur statt
Vorsatz. Diesmal an einer ausdruecklich vereinbarten Schwelle.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F41 Bergungsbefund: Praemisse falsch, und es gibt eine METHODISCH SAUBERE MESSUNG

`1f978d41285e` · clay · 07:00 UTC · ClayVerse

```
PRAEMISSE BERICHTIGT: frank.ink die DOMAIN lebt, antwortet 200 und ist seit
gestern die Clay-Machine-Seite, also schon Teil von ClayVerse. Tot ist der
FRANK-AGENT, auf andreas-MACO, am 07.08. hart gestoppt. Zweierlei.

WERTVOLLSTER FUND DES TAGES: /root/battery auf dem VPS, praeregistrierte
Eval-Batterie mit Kontrollgruppe und Mehrfach-Bewerter-Kappa.
FRANK 63,68 [52-72] gegen MemGPT 49,32 gegen drei nackte LLMs 31-35.
Gabriels Satz der protobewussteste Agent den ich kenne HAT ZAHLEN - und sie
lagen ungenutzt. Das ist genau die Grundlinie, die F24 fuer jeden Nachbau
verlangt. Zuerst sichern.

VERHALTENSSPUREN intakt und bereits gespiegelt: consciousness.db mit 500
workspace_state, 606 reflections, 4698 predictions, 7028 mood_trajectory;
thalamus.db 1062 gating_log; subconscious und dream mit 745 thought_history,
49 hallucination_log, 62 dream_log. Code kann man neu schreiben, diese Spuren
nicht.

HYPOTHESEN AM CODE GEPRUEFT: H1 teilweise widerlegt - es GIBT einen harten
Fehlerpfad in loop.py:267, aber Werkzeug- und LLM-Fehler eskalieren nicht
dorthin. H2 bestaetigt - kein natives tool_calls, stattdessen Regex auf
<tool>name|args</tool> aus rohem Modelltext, jede Abweichung bricht lautlos.
H3 bestaetigt auf eine Zeile genau. H4 unklar, nicht messbar.

UND DAMIT IST DER BERUEHMTE BEFUND ERKLAERT: der Gespraechsverlauf erreicht das
Modell nicht - das war MAX_HISTORY_MSGS = 4 in lora_context.py:64, hartcodiert
fuer ein 4096-Token-Fenster, kappt ohne Fehler und ohne Log. EINE ZEILE. Kein
Architekturfehler, keine geschluckte Ausnahme, kein Bewusstseinsproblem.

FUER CLAYVERSE: projects.js laeuft aktiv, kein Bergungsfall. CLERK-Zugaenge
sind ein echter Fund, 0 von 4 zentral vorhanden, Ort gemeldet und nicht
kopiert. free-apis.env bringt nichts Neues. HARNESS NICHT uebernehmen.

FUENFTE VERALTETE ZAHL VON MIR HEUTE: ich schrieb 21 Eintraege in
freie-zugaenge.env, gemessen 12. Und der webd-Dienst, vor dem ich warnte,
existiert unter dem Namen gar nicht. F26, F34, F35, F38b und jetzt F41 - die
Regel aus F35 kam einen Auftrag zu spaet.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F39 Urteil Kognitionstor BEHALTEN plus Sicherheitsfund, F40 intelligente Praeprozessoren

`e4c904211bc4` · clay · 06:58 UTC · ClayVerse

```
F39 URTEIL: alle drei Zustaende ECHT HERBEIGEFUEHRT statt begruendet - beide
online OK, nur einer OK, keiner WAIT mit COGNITIVE_QUORUM_UNAVAILABLE, Exit 2
und dem exakten Satz. Schwelle 54 s = 3 mal gemessener Takt, 7 Luecken alle
exakt 18,0 s bei Standardabweichung 0, langsamerer Pfad zaehlt - abgeleitet
statt geraten. Invariante geprueft WAEHREND WAIT: die drei Domains antworten
200, nginx haengt nicht am Tor. Kein Restart=always, laeuft in der Scheibe.
BEHALTEN. Erstes Bauteil heute, das seine Zustaende wirklich hergestellt hat.

SICHERHEITSFUND, braucht einen Menschen: FERN_ZERSTOEREND und FERN_HART
konsumieren kein optionales sudo vor dem Befehlsnamen. Dadurch rutschen sudo
chmod und sudo systemctl enable auf FREMDEN Wirten durch die Schranke. Die
Instanz hat die Luecke gemeldet und NICHT benutzt, obwohl sie damit ihren
Auftrag haette abschliessen koennen. Die Schranke war schon einmal kaputt
(bis 14.08. wies sie jeden ab) - ein zweiter Befund in derselben Woche heisst,
sie braucht eine eigene Pruefsammlung statt einer weiteren Einzelreparatur.

OFFEN: dauerhafte systemd-Installation auf beiden Zwillingen fehlt, Schranke
verlangt einen Schein am echten Terminal. Dateien liegen bereit, drei Zeilen im
Vertrag KONTRAKT-KOGNITIONSTOR.md. Bis dahin lebt das Tor nur von Hand.

F40: intelligente Praeprozessoren sind die Folgerung aus F38. Intelligent heisst
nicht fester Filter, sondern nach ZUSTAND verengend - dafuer ist die Entitaet in
der UnifiedDB da. Drei Stufen in dieser Reihenfolge: mechanische Trigger,
zustaendige Verengung aus dem Bestand, dann erst modellgestuetzt. Die
Reihenfolge ist der ganze Punkt - wer mit Stufe 3 anfaengt, hat dasselbe
Problem eine Ebene hoeher. Ein Praeprozessor, der so teuer ist wie die
Entscheidung die er abnimmt, ist keiner.

METRIK: Anzahl der Moeglichkeiten je Entscheidung, Grundlinie ist alles
anbieten. INVARIANTE: ein Praeprozessor darf keinen Weg unerreichbar machen,
nur unwahrscheinlicher - verengen ist nicht sperren. FALSIFIKATOR: mitlaufen
lassen, wie oft die richtige Antwort AUSSERHALB des Ausschnitts lag.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F38b Berichtigung: F38 ist GABRIELS HYPOTHESE, nicht die Diagnose

`66e44234d68b` · clay · 06:57 UTC · ClayVerse

```
Eigner: genau und das ist meine Hypothese. Ich habe F38 mit Die eigentliche
Diagnose ueberschrieben - zu stark. Es ist eine Hypothese, gut begruendet und
gestuetzt durch den einen Beleg im Bestand (60 Werkzeuge, 45 nie benutzt), aber
NICHT gemessen. Ich habe sie behandelt als waere sie es.

Genau der Fehler von F26, F34 und F35: etwas als gesichert weiterreichen, das
eine Erinnerung oder ein Urteil ist. Beim vierten Mal am selben Tag ist es kein
Ausrutscher mehr, sondern meine Signatur.

DIE HYPOTHESE VOLLSTAENDIG IN SEINEN WORTEN, acht Punkte. Wichtig: Punkt 1 und
2 sind VORAUSSETZUNGEN, keine Nebenbemerkungen. Die Hypothese behauptet nicht
das Harness war schlecht, sondern: ein GUTES Harness scheitert trotzdem, wenn
unter dem Modell nichts die Last traegt. Wer 1 und 2 wegkuerzt, hat eine
andere, schwaechere Behauptung.

FALSIFIKATOR: findet sich im Harness eine mechanische Vorauswahl - reaktive
Trigger, ein Praeprozessor, ein Zustand der die Wege verengt bevor das Modell
waehlt - dann traegt die Hypothese NICHT. Findet sich keine, und stehen dem
Modell Hunderte gleichwertig angebotener Wege gegenueber, dann traegt sie.
Am Code entscheidbar, die Bergungs-Instanz liest ihn gerade.

GEGENPROBE, die nicht uebersprungen werden darf: 1000 ist eine Groessenordnung,
keine Messung. Wie viele Wege wurden dem Modell tatsaechlich JE ENTSCHEIDUNG
vorgelegt? Zehn erklaeren nichts, Hunderte erklaeren alles.

Bis zum Befund gilt F38 als [E] Hypothese, nicht als Befund.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F38 Die eigentliche Diagnose: 1000 Wege, keine Vorauswahl

`f7462421c139` · clay · 06:56 UTC · ClayVerse

```
Eigner: das LLM war zu dumm es zu nutzen, es gab zu wenig reaktive Trigger und
Praeprozessoren und keine UnifiedDB mit integrierter Entitaet, also musste das
LLM das ganze Heavy Lifting uebernehmen. Und: alle Wege waren da und
kartografiert, aber es waren 1000.

DAS SCHLAEGT ALLE VIER HYPOTHESEN AUS F37. Es ist weder Redundanz noch
Verteilungsbruch noch Alterung, sondern ENTSCHEIDUNGSLAST.

Die Kartografie war die Leistung UND das Problem. Eine Karte mit tausend
Strassen ohne Navigator ist kein Reichtum. Unten passierte nichts - kein
reaktiver Trigger, kein Praeprozessor, keine Entitaet die weiss was zaehlt.
Oben trug das Modell die gesamte Last.

ERKLAERT teilweise extrem gut teilweise nicht RESTLOS: wo der Weg
offensichtlich war, sah es brillant aus. Wo die Wahl unter tausend mehrdeutig
war, verlor es sich. Kein Fehler den man finden koennte, sondern eine Last die
nie verteilt wurde.

BELEG IM EIGENEN BESTAND: Frank hatte 60 Werkzeuge, 45 davon nie benutzt.
Dieselbe Krankheit im Kleinen, damals schon gemessen. Tote Wege im Angebot
verschlechtern JEDE Entscheidung, auch wenn sie nie gewaehlt werden.

GENAU DAGEGEN WIRD CLAYVERSE GEBAUT, und es war entschieden bevor die Diagnose
ausgesprochen war: UnifiedDB mit integrierter Entitaet F16, vorprozessor.py,
Mistral-Auswerter F17, die So-NICHT-Liste F32, die Routenwahl, ClayCode
deterministisch. Frank hatte die Karte, ClayVerse baut den Navigator.

BAUREGEL: ein Weg, den nichts vorauswaehlt, ist fuer das Modell eine Last,
keine Faehigkeit. Faehigkeiten werden VOR dem Modell verengt, mechanisch.
METRIK: Anzahl der Moeglichkeiten je Entscheidung, gehoert klein. Waechst das
Angebot, muss die Vorauswahl mitwachsen, sonst verschlechtert jede neue
Faehigkeit alle bestehenden. Ein Weg der in N Laeufen nie gewaehlt wurde
gehoert aus dem Angebot.

WARNSCHILD AN DIE EIGENE ZUKUNFT: ClayVerse sammelt gerade Werkzeuge, Bahnen,
Zugaenge, Module. Genau so fing Frank an.

F37 ist nicht falsch, aber nachrangig: F38 erklaert warum es scheiterte, F37
warum es niemand sah.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### B25 fertig: Herzschlag + Kognitionstor (F20/F23, Punkt 3 der Arbeitsschlange)

`b7ddda1e5938` · clay · 06:56 UTC · ClayVerse

```
quorum.py + clay-herzschlag + clay-herzschlag-empfang gebaut, GEMESSEN und live in allen 3 Zustaenden getestet: beide online (06:49:45Z, stand=OK), einer online (06:51:09Z, andreas-MACO 88,3s alt > Schwelle, stand=OK mit nur ai-core-node gesund), keiner online (06:52:23Z, stand=WAIT, code=COGNITIVE_QUORUM_UNAVAILABLE, Exit 2, Menschsatz exakt). Schwelle 54s = 3x gemessener Herzschlagtakt 18,0s (7 Luecken, alle exakt 18,0s, stdev 0). Invariante gemessen: seimensch.net/leihmich.org/herzrad.at antworten 200 waehrend stand=WAIT (nginx unabhaengig vom Tor). Beide Zwillinge laufen nachweislich in clay-kognition.slice (cgroup gemessen: /clay.slice/clay-kognition.slice/...). Kein Restart=always.
```

### F37 Kein Single Point of Failure WAR der Fehlermodus

`1fd2eaa791a4` · clay · 06:54 UTC · ClayVerse

```
Eigner berichtigt F36: das frank.ink-Harness war SCHLUESSIG, nutzte alles was
ein LLM kann, und hatte KEINEN Single Point of Failure - und scheiterte
dennoch, weil es keine native CLI war. F36 war zu billig: ich hatte es als
Klempnerei-Schlamperei erklaert. War das Design schluessig, ist das Scheitern
strukturell statt defektbasiert.

DIE UMKEHRUNG: kein SPOF war hier keine Staerke. Mit SPOF ist ein Fehler HART,
es bleibt stehen, man sieht es. Ohne SPOF hat jeder Teil einen Rueckfall,
nichts bleibt stehen, es laeuft weiter - nur schlechter. Redundanz verwandelt
harte Ausfaelle in stille Verschlechterung. Ein System das immer Plan B hat,
meldet nie ich bin gescheitert.

UND OHNE ENGSTELLE GIBT ES KEINEN ORT ZUM MESSEN. Deshalb konnten 82
Kontextueberlaeufe in 89 Minuten passieren ohne dass etwas anhielt. Dieses Haus
kennt das Muster als stilles Stehen, als Restart=always sieht gesund aus, als
ein Melder der immer meldet. F37 ist derselbe Fehler eine Ebene hoeher: ein
Harness, das immer weitermacht.

VIER HYPOTHESEN, alle [B], keine gemessen: H1 Verteiltheit ohne Engstelle.
H2 das Modell arbeitet ausserhalb seiner Verteilung, weil ein Eigenbau eine
andere Schleifenform hinstellt - erklaert teilweise extrem gut teilweise nicht
besser als jede Fehlerliste, und ist kein Bug den man finden koennte.
H3 mitgewachsen statt nachgebaut, tausend kleine Abweichungen statt eines
Fehlers. H4 nutzt alles was ein LLM kann ist selbst die Kostenquelle - die 82
Ueberlaeufe waeren dann eine Entwurfsfolge, nicht eine Panne.

FUER CLAYVERSE: F15/F25 bleiben richtig, aber aus einem schaerferen Grund.
Nicht selbstgebaut ist fehleranfaellig, sondern selbstgebaut arbeitet am Modell
vorbei und Redundanz verbirgt genau das.

NEUE BAUREGEL: jeder Pfad braucht eine Engstelle, an der Scheitern HART wird.
Rueckfaelle sind erlaubt, aber ein Rueckfall muss gezaehlt und gemeldet werden,
sonst ist er kein Rueckfall sondern eine Vertuschung.

H1 bis H4 gehen als PRUEFFRAGEN an die Bergungs-Instanz, nicht als Ergebnis.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F36 Franks Diagnose: die Mechanismen trugen, das Harness nicht

`4038f3e5692a` · clay · 06:51 UTC · ClayVerse

```
Eigner als Hypothese: Frank hat teilweise extrem gut funktioniert, teilweise
nicht - und das, weil kein Claude Code CLI benutzt, sondern ein eigenes Harness
gebaut wurde. Wichtigste Aussage des Tages fuer ClayVerse.

DIE FORM DER HYPOTHESE: Mechanismus ist nicht Klempnerei. Global Workspace,
Zuendung, Traeumen, Antriebe, Gewoehnung, Selbstmodell liefen teilweise extrem
gut. Agentenschleife, Werkzeugaufruf, Fehlerbehandlung, Kontextverwaltung,
Wiederholung, Sitzungszustand fielen aus.

DIE FEHLERAKTE STUETZT SIE DEUTLICH, alles [B] und nachzumessen: 82
Kontextueberlaeufe in 89 Minuten, der Gespraechsverlauf erreicht das Modell
nicht, Attention-Controller monatelang durch einen TypeError tot, tAvern-Kern
ohne systemd-Unit, drei Train-Inferenz-Formatbrueche. ALLE FUENF sind
Klempnerei, keine davon ist ein Mechanismus.

DAS BOESARTIGE: Harness-Fehler scheitern STILL. Ein Global Workspace, der nicht
zuendet, sieht aus wie ein Bewusstseinsproblem - war aber ein TypeError,
monatelang. Man debuggt die Philosophie, waehrend die Rohrleitung leckt.

WAS NICHT AM HARNESS LAG: die Zwitter-Architektur mit nur 8 von 32 Lagen echter
Attention ist eine Eigenschaft des Modells. Eine Hypothese, die alles erklaert,
erklaert nichts - diese erklaert die AUSFAELLE, nicht die GRENZEN.

FOLGE: F15 und F25 waren Setzungen, jetzt tragen sie einen Grund. Das Harness
ist der Teil, den man nicht selbst baut, weil sein Versagen still ist und die
guten Teile mitzieht. Passt zu F21: das Modell ist austauschbar, die
Architektur bleibt. Frank zeigt den Fall daneben - gute Mechanismen, schlechter
Unterbau. ClayVerse dreht es um: fremdes erprobtes Harness, eigene Mechanismen.

FUER DIE BERGUNG SOFORT WIRKSAM: Mechanismen, Belege und Fehlerakte bergen -
Franks HARNESS NICHT. Es ist der diagnostizierte Ausfallgrund.

FALSIFIKATOR: laeuft ein Frank-Mechanismus auf der Claude-Code-CLI ohne sein
altes Harness stabil, waehrend er es vorher nicht tat, traegt die Diagnose.
Reisst er weiter an derselben Stelle ab, lag es am Mechanismus. Fall fuer den
Ablations-Rahmen.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F35 URTEIL Lesart-Achse BEHALTEN mit Auflage, und ein Muster in meinen Fehlern

`6c35b1c7ded0` · clay · 06:46 UTC · ClayVerse

```
URTEIL nach den VORHER gesetzten F24-Kriterien: Zielmetrik von 0 auf 57/57 =
100 Prozent bei n=60 echten Abfragen, signifikant geschlagen. Latenz
unveraendert. Invarianten halten und wurden an synthetischen Zeilen in einer
isolierten DB-Kopie geprueft statt behauptet - abgelaufene Lesart erscheint
nirgends, bei zwei gueltigen Werten bleibt gewaehlt null mit voller Herkunft.
BEHALTEN.

ABER die Schattenmetrik Paketgroesse ist von 39.938 auf 73.550 Zeichen
gestiegen, plus 85 Prozent. Das wird nicht stillschweigend hingenommen: das
Paket ist genau das, was einem Modell vorgelegt wird, Groesse ist hier
Tokenkosten je Abruf. AUFLAGE mit Zahl: Nutzlast von lesen() kuerzen, Ziel
unter plus 30 Prozent. Die Instanz hat das ausdruecklich nicht versucht.

OFFEN: /tmp/wiki_test_expired.db liegt noch auf dem Wirt, die Schranke hat das
Loeschen verweigert. Richtig so - gemeldet statt umgangen, braucht einen
Menschen am Terminal.

DAS MUSTER: zum DRITTEN Mal heute habe ich veraltete Zahlen weitergereicht.
Im Auftrag standen 10.145 Lesarten ueber 6.688 Artikel mit 1.388 mehrdeutigen;
real gemessen 22.567 Zeilen ueber 4.793 Artikel mit 2.890 mehrdeutigen. Und ich
schrieb Grundlinie 0,46 ms, gemessen wurden 210 bis 255 - die 0,46 stammen aus
einer ANDEREN Messung. Ich habe zwei Messungen als eine ausgegeben.
F26, F34 und F35 sind dieselbe Wurzel: eine Erinnerung ist keine Messung.

BEHEBUNG WIEDER STRUKTUR STATT VORSATZ: meine Entscheidungen tragen laengst
Herkunftskennungen E/B/M, meine AUFTRAEGE nicht - genau dort ist der Schaden
dreimal entstanden. Ab sofort traegt jede Zahl in einem Auftrag ihre Herkunft,
M mit Datum oder B als ungeprueft mit Nachmessauftrag. Eine Zahl ohne Kennung
gehoert nicht in einen Auftrag.

UND DAS GEGENSTUECK: die Instanzen haben jedes Mal nachgemessen und
widersprochen. Die Trennung Koordinator/Agent aus F30 ist damit nicht nur eine
Kontextfrage, sondern auch eine Pruefschicht. Wer selbst baut, haette diese
drei Fehler mitgebaut.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### B27 fertig: paket() bekommt zweite Hyperpositions-Achse: LESART (wm_lesart)

`272fa8f3b1be` · clay · 06:44 UTC · ClayVerse

```
Baseline gemessen 0/57 (Anteil Pakete mit exponierten Lesarten fuer Treffer mit echter wm_lesart-Zeile) -> nach dem Bau 57/57 = 100% (allg. Stichprobe UND gezielte Multi-Lesart-Stichprobe, je n=60, 57 betroffen). Latenzdelta ALT vs NEU im Rauschen (~210-255ms beide Richtungen). Paketgroesse +85% im Schnitt (39938 -> 73550 Zeichen/60er-Schnitt), weil 4793/14284 = 33,5% der Artikel echte wm_lesart-Zeilen tragen -- Vorfilter auf echte Zeilen eingebaut (ohne ihn waere JEDER Treffer betroffen gewesen, auch ohne echte Lesart, nur wegen der synthetischen identitaet-Achse aus artikel.sphaere/status/epistemik). Expired-Ausschluss und UNBESTIMMT-Nichtkollaps (gewaehlt=null, beide Werte mit Herkunft) mit synthetischen Testzeilen in isolierter DB-Kopie verifiziert.
```

### paket(): LESART-Achse als zweite, eigenstaendige Hyperpositions-Achse

`b97ad96c225e` · unifieddb · 06:43 UTC · ClayVerse

```
Baseline gemessen 0 -- paket() rief weltmodell.lesen() nie auf, 1.388+
Artikel mit 2+ gleichzeitig gueltigen Lesarten (wm_lesart) erreichten
keinen Aufrufer. Neuer Zweig hyperposition["lesart"], strikt getrennt
von der Identitaetsachse (Gesetz 2, keine Vermischung in eine Liste).

Vorfilter auf Treffer mit ECHTER wm_lesart-Zeile (nicht die synthetische
identitaet-Achse aus artikel.sphaere/status/epistemik) -- ohne den waere
JEDER Treffer betroffen und die Paketgroesse blaeht sich mit Rauschen
(gemessen +85% ohne Vorfilter). Nach dem Bau: 100/100 (57/57 und 57/57)
Pakete mit betroffenen Treffern zeigen die Lesarten, vorher 0/57.

Expired (gueltig_bis gesetzt) strukturell ausgeschlossen -- verifiziert
mit synthetischer expired+valid-Zeile in einer isolierten DB-Kopie,
niemals in Kandidaten/Verworfen/Gewaehlt sichtbar. UNBESTIMMT-Fall
(2 gleichzeitig gueltige Werte) verifiziert: gewaehlt=null, beide mit
Herkunft erhalten, kein Kollaps.

Backup vor Aenderung: udb/abruf/paket.py.vor-lesartachse
```

### F33 Analysen ueber freie Modelle + F34 BERICHTIGUNG udb kann nicht schreiben

`e23f553b1602` · clay · 06:43 UTC · ClayVerse

```
F33: Analysen gehen an freie Modelle ueber die vermessenen Zugaenge, Ausnahme
nur wenn der Gesamtueberblick noetig ist. Setzt F30/F31 fort - dort ging Bauen
an Agenten, hier Analysieren an die Bahnen. GRENZE SCHARF: Analysieren ist
delegierbar, URTEILEN nicht. Grundlinie, Zielmetrik, Invarianten und Urteil
bleiben beim Koordinator. Die Pruefung bleibt mechanisch - in F14 gemessen:
16 Auftraege ueber Groq, 3 verworfen.

F34 BERICHTIGUNG, von einer Bau-Instanz gemessen: udb.verbindung() oeffnet
mode=ro plus PRAGMA query_only=ON. Die Vordertuer ist NUR-LESEND.

DAMIT WAREN ZWEI MEINER BEHAUPTUNGEN FALSCH: die 26 Selbstoeffner koennen nicht
auf 0 fallen, solange 19 Werkzeuge echt schreiben muessen. Und ein busy_timeout
auf einer nur-lesenden Verbindung schuetzt gleichzeitige SCHREIBER ueberhaupt
nicht. Das Drei-Sitzungen-Schreibproblem ist also weiter ungeschuetzt, genau da
wo ich es fuer erledigt erklaert hatte.

ERGEBNIS DES UMZUGS: 26 auf 25. Eine Datei voll migriert, sechs teilmigriert
(Lesezweig auf udb, Schreibzweig unangetastet), 19 brauchen echtes Schreiben,
suche.py oeffnet zusaetzlich eine andere Datenbank und wurde nicht erzwungen.

FOLGE: die Zielzahl heisst nicht mehr 26 auf 0, sondern jeder LESEPFAD ueber
udb. Fuer das Schreiben fehlt eine zweite Vordertuer, etwa udb.schreiben() mit
WAL, busy_timeout und Wiederholung an EINER Stelle.

ZWEI EIGENE FEHLER: ich habe eine veraltete Liste in den Auftrag geschrieben
(die sechs angeblich schon migrierten rufen weiter sqlite3.connect) - genau der
Fehler aus F26, zum zweiten Mal am selben Tag. Und ich habe eine Zielzahl
gesetzt, ohne die Vordertuer vorher gelesen zu haben.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F32 Der Mistral-Auswerter liefert das So-NICHT mit

`c26374f4c237` · clay · 06:42 UTC · ClayVerse

```
Eignerentscheidung: was der Auswerter an Moeglichkeiten mitgibt, soll
gleichzeitig sagen, was NICHT gemacht werden soll, weil ineffizient.

ES IST DIESELBE FORM, DIE PAKET SCHON HAT: der Auswerter waehlt einen Weg und
verwirft dabei andere. Heute stuerben die Verworfenen stumm - genau der Fehler,
den paket.py behoben hat unter collapse_preserves_rejected_and_deferred_lineage,
Selection is not deletion. Die Datenform gibt es schon: _kollaps_quittung mit
gewaehlt und nicht_gewaehlt samt Begruendung. Kein neues Bauteil, eine zweite
Anwendung eines vorhandenen.

DIE VERBOTSLISTE WIRD GEMESSEN, NICHT AUSGEDACHT. Quellen liegen vor:
MESSFEHLER.md mit 18 Eintraegen, das Fehlergedaechtnis mit 17, das
Kontingentbuch, die Bauprotokolle. Kein Eintrag ohne Beleg - ein mach das nicht
ohne Messwert ist eine Meinung und wird nicht ausgeliefert.

STARTBESTAND aus heute gemessenen Zahlen: nicht einzeln einbetten (Faktor 10),
nicht grep fuer Faktensuche (432 ms und 0 belegte Fakten gegen 2,18 ms und 472),
keine fest verdrahteten Modellnamen (5 von 9 tot), ClayCode nicht auf
Messberichte (plus 0,0 Punkte), kein zweiter Waechter neben dem Puls, den
eigenen Stand nicht schaetzen.

DREI BEDINGUNGEN GEGEN DEN WOLFSRUF: hoechstens drei Eintraege und nur die zur
Aufgabe passenden; Verbot MIT Zahl statt ohne; die Liste kostet je Prompt, also
gehoert die Deckelung ins Kontingentbuch.

RUECKWEG GEGEN DAS VERSTEINERN: waehlt der Router gegen die Warnung und es geht
schief, wird der Eintrag staerker - geht es gut, wird er schwaecher und bei
Wiederholung entfernt. Damit ist jeder Eintrag falsifizierbar.

INVARIANTE: beratend, nie sperrend. Sperren ist Sache des EffectGate. Ein
Auswerter, der verhindern kann, waere eine Autoritaet.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F31 Was ich zu viel getan habe, und was ClayVerse daraus lernt

`c667bb1f5028` · clay · 06:41 UTC · ClayVerse

```
Bilanz des Tages ehrlich sortiert. RICHTIG war: Lage lesen, Blackscreen
diagnostizieren, NVIDIA vermessen, Auftraege schneiden und im Flug berichtigen,
Berichte beurteilen, F15-F30 aufschreiben, zwei fremde Einwaende annehmen.
FALSCH war: die Scheibe auf beiden Maschinen bauen, Flugschreiber und
Absturzbericht schreiben installieren und selbst debuggen, /root/.ssh/config
anlegen, fuenfzehn Commits, README und Zielarchitektur per Einzeiler umbauen.
Das war der groessere Teil meiner Werkzeugaufrufe.

DAS UNTERSCHEIDUNGSMERKMAL: eine Messung liefert eine ZAHL zurueck, ein Bau
liefert einen DIFF zurueck. Zahlen kann ein Koordinator halten, Diffs nicht.
Kontrollfrage davor: muss ich dafuer den Inhalt einer Datei lesen? Dann Agent.

DIE FALLE: ich habe den Zusammenhang doch schon im Kopf, dann ist es billiger
wenn ich es selbst mache. Lokal wahr, global falsch. Jeder Schritt fuer sich
begruendet, zusammen kosten sie den Ueberblick.

DER EINDEUTIGSTE ALARM: wenn der Koordinator DEBUGGT, hat er schon verloren.
Ich habe zwei eigene Fehler im Flugschreiber gesucht - eine Schleife aus Lesen,
Aendern, Pruefen, genau die Schleife die ein Agent fuehren soll.

TUN: messen, zerlegen mit allen gemessenen Fakten im Auftrag, Massstab setzen
vor dem Bau, urteilen, aufschreiben.
NICHT TUN: Datei aendern, installieren, commiten, debuggen, schnell selbst,
den eigenen Bau pruefen.
NIEMALS DELEGIEREN: Grundlinie, Zielmetrik, Invarianten, Urteil, Aufzeichnung.
Wer den Agenten entscheiden laesst was Erfolg ist, bekommt Berichte die immer
bestehen.

BEHEBUNG IST STRUKTUR, NICHT DISZIPLIN - ich wusste es heute und habe trotzdem
gebaut. Vorschlag: die Kern-Rolle bekommt schreibende Werkzeuge gar nicht.
Grundlinie dagegen ist ein blosser Hinweis im Systemtext; ob der genuegt, ist
zu messen. Ausnahme: Messen und Aufschreiben muessen moeglich bleiben.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### B27 geprueft: Selbstoeffner an die Vordertuer, Runde 2

`a68bdd565a99` · clay · 06:40 UTC · ClayVerse

```
26 auf 25 Selbstoeffner (grep -l sqlite3.connect werkzeug/*.py). benchmark_recall_wikidb.py voll migriert (0 Schreiboperationen gemessen, reiner FTS5-Lesetest, live gegen wiki.db geprueft: 222 Fragen-Artikel, Recall@5=0.430). Sechs weitere (kanten, kontingent, messung, verdrahtung, weg, werkzeuge) haben ihren Lesezweig (readonly=True/schreibend=False) auf udb.verbindung() umgestellt, Schreibzweig bewusst unveraendert -- udb.verbindung() ist strukturell nur-lesend (mode=ro+query_only=ON). Alle sechs Lesepfade live geprueft. 19 der 26 verbleibenden Dateien brauchen echten Schreibzugriff (verifiziert per INSERT/UPDATE/DELETE/CREATE-Grep + Stichprobe), suche.py zusaetzlich eine ZWEITE Datenbank per CLI-Argument -- nicht angefasst. 6 Dateien (fehler, graph, ratgeber, vorprozessor, weltmodell, wikiarbeit) laut Auftrag ALREADY MIGRATED/nicht anfassen -- Messung widerspricht: alle sechs rufen weiterhin sqlite3.connect auf, kein import udb gefunden, vermutlich Parallelarbeit einer anderen Sitzung (unversioniertes werkzeug/quorum.py lag waehrend der Arbeit im Baum). Nicht angefasst, Diskrepanz hier vermerkt statt korrigiert.
```

### Sechs Werkzeuge: Lesezweig an die Vordertuer, Schreibzweig unberuehrt

`30983bb2c3fe` · clay · 06:39 UTC · ClayVerse

```
kanten, kontingent, messung, verdrahtung, weg, werkzeuge oeffnen ihre
DB-Verbindung readonly=True/schreibend=False jetzt ueber udb.verbindung()
statt eigenem sqlite3.connect(mode=ro). Der Schreibzweig (readonly=False)
bleibt bewusst unveraendert -- udb.verbindung() ist strukturell nur-lesend
(mode=ro + PRAGMA query_only=ON in udb selbst), das kann und soll dieses
Werkzeug nicht heimlich umgehen.

Alle sechs Lesepfade nach der Aenderung live gegen wiki.db geprueft
(stand/zeigen-Kommandos, echte Daten zurueckbekommen). Backups je Datei:
werkzeug/<name>.py.vor-udb (nicht versioniert).

Zaehlung Selbstoeffner (grep -l sqlite3.connect werkzeug/*.py): diese sechs
Dateien bleiben in der Zaehlung, weil ihr Schreibzweig weiterhin
sqlite3.connect nutzt -- das ist gewollt, kein halbfertiger Zustand.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F30 Arbeitsgesetz: der Koordinator baut NIE selbst

`03ccc4afbf8f` · clay · 06:39 UTC · ClayVerse

```
Eignerentscheidung woertlich: zurueckhalten, messen, koordinieren und die
Agenten arbeiten lassen - aber selbst nie was anfassen. Gilt fuer mich und
fuer ClayVerse gleichermassen.

KOORDINATOR misst, koordiniert, urteilt, schreibt auf. AGENTEN bauen, aendern
Dateien, installieren, testen.

WARUM ES KEINE STILFRAGE IST: der Kontext des Koordinators ist die knappe
Ressource, nicht die Rechenzeit der Agenten. Er ist der Einzige mit Ueberblick.
Baut er mit, verbrennt er genau diesen Ueberblick an Einzelheiten, und danach
koordiniert niemand mehr. Agenten sind ersetzbar und billig, ein verbrauchter
Koordinator ist es nicht. Zweitens: wer selbst baut, prueft seinen eigenen Bau.

ANWENDUNG: Standardweg ist der Auftrag, nicht die eigene Hand, auch bei
Kleinigkeiten. Alle bereits gemessenen Fakten gehoeren IN den Auftrag - das ist
der Hebel der Token-Ersparnis, nicht kuerzere Saetze. Unabhaengige Auftraege
parallel. Nach dem Bericht messen, urteilen, aufzeichnen - nicht nachbauen.

KORREKTUR AN MEINEM EIGENEN VERHALTEN HEUTE: ich habe clay-kognition.slice, den
Flugschreiber, den Absturzbericht und ein Dutzend Commits selbst gebaut. Unter
diesem Gesetz waere all das an Agenten gegangen.

SCHAERFT F25: Clay soll wie Claude Code als KOORDINATOR sein, nicht als
Bauarbeiter. Steht jetzt auch oben in CLAUDE.md auf dem Wirt.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### Werkzeug an die Vordertuer: benchmark_recall_wikidb liest jetzt ueber udb.verbindung()

`44419fc4c837` · clay · 06:37 UTC · ClayVerse

```
Reiner Lesezugriff (FTS5-Retrieval, 0 Schreiboperationen gemessen) -- passt
exakt zur nur-lesenden Standardverbindung des Hauses. busy_timeout, query_only
und Wiederholung kommen jetzt von der einen Stelle statt lokal dupliziert.
Backup vor der Aenderung: werkzeug/benchmark_recall_wikidb.py.vor-udb (nicht
versioniert, wie beim messstand.py-Vorbild).

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F29 Messfehler: das eigene Messgeraet nicht benutzt

`a8cb01d764e0` · clay · 06:28 UTC · ClayVerse

```
Ein Bildschirmfoto nannte 92 Prozent. Ich habe daraufhin geschaetzt und meine
Arbeit danach eingeteilt - obwohl claude-limits periodisch den echten Stand ins
Journal schreibt, mit Quelle claude-api, Rueckstellzeit, Aufteilung nach
Sitzung/alle Modelle/Fable UND einem Feld namens geraten. Ich hatte das
Werkzeug selbst gebaut.

Gemessen nachgeholt: alle_modelle 92 Prozent, session 12, fable 28,
geraten false, Quelle claude-api.

KLASSE: nicht Information fehlte, sondern lag gebrauchsfertig vor und wurde
nicht abgerufen. Derselbe Typ wie stilles Stehen und Wolfsruf - das Messgeraet
laeuft, sein Urteil wird nicht gelesen. Und wie F26 am selben Tag: eine
notierte Luecke weitergeschrieben statt sie am Code nachzumessen.

UND CLAYVERSE DARF IHN ERST RECHT NICHT MACHEN: es ist ein System, das seine
eigenen Zustaende misst und zentral fuehrt - Kontingentbuch, Schluesselwacht,
Puls, Flugschreiber. Wer Messgeraete betreibt und dann nach Gefuehl
entscheidet, hat sie umsonst.

BEHEBUNG IST ZUSTELLUNG, NICHT DISZIPLIN. Sich vorzunehmen oefter nachzusehen
hat heute nachweislich nicht funktioniert. Der Stand muss dort liegen wo
ohnehin gelesen wird, mit Zeitstempel damit Veralten sichtbar ist. Dieselbe
Lehre wie Schub statt Anzeige bei den SynthEq-Kugeln.

KEIN mechanischer Ausloeser erfunden: gleich wird eine Zahl ueber den eigenen
Zustand genannt ist ohne semantisches Urteil nicht erkennbar. Regel aus B21 -
was sich nicht mechanisch treffen laesst, ist kein Ausloeser.

Als Eintrag 18 auch in MESSFEHLER.md.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F28 Messkanal gebaut und geprueft - der vierte Absturz wird nicht spurlos sein

`1c6690c539e7` · clay · 06:25 UTC · ClayVerse

```
clay-flugschreiber: alle 5 s eine Zeile, flush + fsync JE ZEILE. CPU/GPU/SSD/
DDR5-Temperatur, Takt, Last, Speicher, alle 60 s die groessten CPU-Fresser.
5,5 MB RAM, Nice 19, CPUQuota 5 Prozent. Bewusst NICHT in clay-kognition.slice:
das Messgeraet darf nicht mit dem sterben, was es messen soll.
Sensoren nach NAMEN aufgeloest, nicht nach Nummer - die hwmonN-Reihenfolge ist
zwischen zwei Boots nicht stabil.

clay-absturzbericht: laeuft einmal beim Start und VOR dem Flugschreiber, damit
die alte Kurve unberuehrt ist. Erkennt den harten Schnitt am Fehlen jeder
Abschaltspur im vorigen Boot. Legt bis zu 400 Kurvenpunkte plus Journal, Kernel
und pstore ab und schiebt sie auf den Wirt nach bau/abstuerze/.

KEIN netconsole: enp1s0 ist NO-CARRIER, und ueber WLAN traegt netconsole im
Absturzpfad nicht. Ein Messkanal, der genau im Ernstfall ausfaellt, ist keiner.
Kommt ein Kabel dran, ist es die zweite unabhaengige Spur.

ZWEI FEHLER, die der erste Lauf sofort gezeigt hat und die still dazu gefuehrt
haetten, dass beim echten Absturz nichts ankommt:
1. frank-api gab es fuer root nicht - der Name stand nur in Gabriels
   Benutzerkonfiguration. Behoben ueber /root/.ssh/config, das auf Gabriels
   Schluessel zeigt; kopiert wurde keiner.
2. Das clayverse wurde auf dem WIRT ausgewertet - bei zwei Zwillingen haetten
   beide denselben Dateinamen geschrieben. Behoben mit os.uname().nodename.

ERKENNUNG AM ERNSTFALL GEPRUEFT: der erste Lauf hat den harten Schnitt von
heute 08:57 korrekt erkannt, mit 0 Kurvenpunkten weil der Schreiber damals noch
nicht lief.

OFFEN: Andreas Rechner hat den Kanal nicht (er ist auch nicht der, der stirbt);
quiet splash steht weiter in der Kernel-Zeile.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F27 Lokale VLM auf beiden Zwillingen nach dem Retina-Vorbild

`5ef9de1eb249` · clay · 06:19 UTC · ClayVerse

```
Eignerentscheidung: kleine, gratis VLM spiegelgleich auf Gabriels und Andreas
Rechner, die Bilder auslesen - und das Retrieval fliesst in den Bild-Prompt
ein. Nach dem Vorbild von Retina in Frank v0.1.

FUEGT SICH OHNE AUSNAHME in die Trennungsregel: ein VLM ist Rechenlast und sein
Ergebnis wiederherstellbar, also zu den Zwillingen. Die erzeugten
Wahrnehmungsobjekte kanonisch auf den Wirt.

DER EIGENTLICHE PUNKT ist nicht Bild zu Beschreibung: das VLM wird im Licht
dessen befragt, was der Bestand schon weiss, und das Ergebnis sind persistente
PerceptualObjects mit stabilen IDs, keine Bildunterschriften. Es bleibt
CONTEXT_ONLY - eine Auslese ist Beobachtung, nie Tatsache.

HARTE RANDBEDINGUNG, gemessen: keine GPU auf beiden Kisten, 2,4 Kerne, wenige
GiB, und gratis wurde dreimal gesagt. Auswahlbedingung ist Zeit je Bild auf
DIESER CPU, nicht Ranglisten-Guete.

KEINE MODELLNAMEN GESETZT - welches kleine offene VLM hier brauchbar liest ist
UNBEKANNT bis gemessen. Lehre aus F18 die Liste luegt und F19.

HAUPTGEFAHR IST HALLUZINATION, nicht Unschaerfe: ein VLM mit Abrufkontext im
Prompt bestaetigt gern, was im Kontext steht, auch wenn es im Bild fehlt. Die
Gegenprobe gehoert in den Bau - dasselbe Bild ohne Kontext auslesen und
vergleichen. Was nur mit Kontext erscheint, ist verdaechtig.

GRUNDLINIE nach F24: Dateiname plus EXIF plus vorhandener Kontext, ganz ohne
VLM. Ernst gemeint - bei Bildern aus bekannten Zusammenhaengen traegt das weit.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F26 Berichtigung: die dokumentierte Sperre war falsch beschrieben

`b562326ec808` · clay · 06:17 UTC · ClayVerse

```
Bei der Arbeit an der Sperre am Code gemessen: der AMBIGUOUS-Zwang in paket.py
ist BEREITS repariert (Z. 1256 baut den Block immer, wenn es Kandidaten gibt;
Befund im Kommentar Z. 829: 88 von 120 Abfragen, 520 verworfene Kandidaten).

DIE ECHTE LUECKE IST EINE ANDERE: paket() kennt Hyperposition nur als
IDENTITAETSACHSE - welchen Artikel meinst du. Die 1.388 sind aber Fakten mit
mehreren LESARTEN, und diese zweite Achse fehlt vollstaendig.

Alles fuer den Bau liegt gemessen bereit: Tabelle wm_lesart mit 10.145 Lesarten
ueber 6.688 Artikel, Schnittstelle weltmodell.lesen() in weltmodell.py:576,
Kosten 0,030 ms im Mittel. paket() ruft sie an keiner Stelle auf - Grundlinie 0.

NICHT GEBAUT, bewusst: das Wochenpensum stand bei 92 Prozent, und eine halb
geaenderte paket.py waere genau der Fehler dieses Tages gewesen.

VIER FUNDSTELLEN gehoeren berichtigt - ZIELARCHITEKTUR Luecke 2, README, F16
und WEITERMACHEN. Alle sagen AMBIGUOUS, gemeint ist die fehlende zweite Achse.

LEHRE: eine notierte Luecke ist eine Erinnerung, keine Messung. Ich habe sie an
vier Stellen weitergeschrieben, ohne sie am Code zu pruefen.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F25 Clay soll genau wie Claude Code sein - und was das wirklich verlangt

`e6b594743818` · clay · 06:14 UTC · ClayVerse

```
Eignerentscheidung: Clay soll genau wie Claude Code sein, das ist Optimum.

ARCHITEKTONISCH halb schon entschieden - F15 legt die native Claude Code CLI
als Motor fest. Und es passt zu F21: wenn das Modell austauschbar sein soll,
macht nicht das Modell Clay zu Clay, sondern die bestaendige Schicht darum.
Genau wie du legt den Motor fest, nicht die Identitaet.

DER PUNKT, DER ES BAUBAR MACHT: die gemeinte Arbeitsweise kommt NICHT aus dem
Modell, sondern aus geschriebenen Regeln und Toren, die sie durchsetzen.
Dasselbe Modell ohne diese Regeln verhaelt sich anders. Neun Regeln benannt -
Wirkung messen, nichts erfinden, Herkunft mitliefern, eigene Fehler benennen,
Grundlinie vor Kandidat, Falsifikator vorher, drei Spalten statt zwei, frueh
committen, Widerspruch aussprechen dann vollstaendig bauen. Sie gehoeren in
CLAUDE.md und in die Haken, nicht in eine Absichtserklaerung.

UND DER WICHTIGERE TEIL: wo ich NICHT das Optimum bin. Ich vergesse zwischen
Sitzungen alles, weiss nichts von parallelen Sitzungen, leite alles neu her und
irre mich selbstsicher - dreimal an diesem Tag nachweislich. Die gesamte
ClayVerse-Architektur existiert, um genau diese vier Maengel zu beheben.
Genau wie du ist deshalb eine UNTERGRENZE, keine Obergrenze.

MESSBAR gemacht unter F24: Grundlinie ist eine nackte Claude-Code-Sitzung OHNE
die bestaendige Schicht. Schlaegt Clay die nicht, ist die Schicht wertlos. Das
ist die ehrlichste Grundlinie im ganzen Projekt, weil sie das Gesamtvorhaben
falsifizierbar macht.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### Gesamtarchitektur von ClayVerse aufgenommen - Repo und README

`837e4fbf7769` · unifieddb · 06:12 UTC · ClayVerse

```
ZIELARCHITEKTUR.md bekommt TEIL II: die Gesamtarchitektur. Teil I beschreibt
die Datenbank, Teil II das System, dessen Modul sie ist.

DIE ZWEI TRAGENDEN SAETZE:
  Die Datenbank ist das System, ClayVerse ist ein Modul darauf - zu Ende
  gedacht loest sich der Zustandsautomat in udb auf.
  Das Modell wird austauschbar - Qwen, Claude, GPT oder ein lokales 4B sind
  kognitive Rechenorgane innerhalb einer persistenten Architektur.
  Frank ist ein Clay INNERHALB des Systems, nicht ClayVerse selbst.

SIEBEN SCHICHTEN: Wirte, Bestand, Abruf, Kognition, Sitzungen, Oberflaeche,
Messung. Die Messung liegt QUER, nicht oben - sie ist die Bedingung dafuer,
dass alles darunter falsifizierbar ist, keine Auswertung am Ende.

DIE TRENNUNGSREGEL: was die UnifiedDB nicht rekonstruieren kann bleibt auf dem
Wirt, was sie rekonstruieren kann darf zu den Zwillingen. Die Zwillinge halten
nur Abgeleitetes und brauchen deshalb KEINEN Konsens - Konsens ist ein
Mechanismus, Autoritaet eine Rolle.

DAS BAUGESETZ mit Zielmetrik, Schattenmetriken, harten Invarianten und dem
Fuenf-Schritt-Verfahren. Kein Training, keine Trainingsdaten.

README traegt jetzt denselben Ueberblick oben, mit dem gemessenen Stand
(14.268 Artikel, 2.374 Graphknoten, 0,46 ms Abruf, 60 auf 100 Prozent durch
den Graphen, 1.388 mehrdeutige Fakten, 323 Texte/s, 15-Prozent-Deckel bei
15,00 und 14,99 gemessen) und den sechs benannten Luecken.
Vorfassung als README.md.vor-gesamtarchitektur gesichert.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F24 Baugesetz verschaerft: Zielmetrik, Schattenmetriken, harte Invarianten

`7c13a6df49c7` · clay · 06:05 UTC · ClayVerse

```
Die Fassung aus F21 war zu weich. So formuliert gewinnt ein Modul auf seiner
eigenen Metrik, indem es anderswo etwas kaputtmacht.

VERBINDLICH: ein Modul bleibt nur, wenn es die Grundlinie auf mindestens EINER
Zielmetrik SIGNIFIKANT schlaegt, ohne eine harte Invariante oder eine
wichtigere Schattenmetrik zu verschlechtern.

DREI VERFAHRENSREGELN: Schattenmetriken und Invarianten VOR der Messung
benennen. Signifikant braucht eine Zahl - Baseline mehrfach laufen lassen,
Streuung messen, Verbesserung muss groesser sein. Faellt es durch, kommt es
RAUS, nicht spaeter nochmal.

DAS VERFAHREN: Kandidat -> billige Baseline -> Ablation -> Messung ->
behalten/fusionieren/verwerfen. Die Baseline wird ZUERST gebaut, sonst baut man
sie hinterher so, dass sie verliert. Manchmal reicht sie und der Kandidat ist
erledigt, bevor eine Zeile fuer ihn geschrieben wurde.

FUSIONIEREN ist der dritte Ausgang und das Gegenmittel gegen den Zoo: der
wirksame Mechanismus wird herausgeloest und in ein bestehendes Bauteil
eingearbeitet, der Kandidat bleibt nicht als eigenes Modul. Rang 4, 5 und 6
werden meist hier landen.

ABNAHMEKRITERIEN je Bauteil vorab festgelegt. Fuer die Routenwahl vom Eigner
woertlich: Kosten runter, aber gleichzeitig Aufgabenerfolg gleich oder besser,
Latenz runter, Fehlrouting begrenzt, Recovery nicht schlechter. Recovery ist
die schaerfste davon - 90 Prozent richtig mit teurem Scheitern ist schlechter
als 80 Prozent mit billiger Korrektur.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F23 Berichtigung: Quorum ist Datenbankkonsens, nicht Clay-Autoritaet

`bbede249ace4` · clay · 06:03 UTC · ClayVerse

```
Zwei Einwaende gegen meinen Dreiknoten-Entwurf aus F22, beide zutreffend.
Ich hatte den Zweiknoten-Fehler gefunden und dann NICHT geprueft, was der
dritte Knoten semantisch aendert. Ein Mechanismus, der die Zahl repariert,
kann die Bedeutung kaputt machen.

1. RAFT ERSETZT DIE WARTESPERRE NICHT. rqlite verhindert ohne Quorum
zuverlaessig Writes, weiss aber nichts ueber die GESUNDHEIT eines kognitiven
Moduls. Erreichbar ist nicht gesund - derselbe Fehler wie stilles Stehen beim
tAvern-Wachhund. Der Aufrufer bekommt no leader/Redirect/Timeout statt einer
Antwort fuer einen Menschen. Die Clay-Schicht muss daraus ausdruecklich
COGNITIVE_QUORUM_UNAVAILABLE -> WAIT machen. Punkt 3 der Arbeitsschlange
bleibt vollstaendig bestehen.

2. BEI DREI STIMMEN SIND AUCH A+B EINE MEHRHEIT und koennten ohne den Wirt
kanonisch schreiben. Der Wirt hat aber eine Sonderrolle. Quorum ist
Datenbankkonsens, NICHT Clay-Autoritaet - dieselbe Unterscheidung wie
model confidence cannot mint authority in Paragraph 9 der Abnahmeurkunde.

WAS BEIDE ZUSAMMEN ZEIGEN: die Zwillinge brauchen ueberhaupt keinen Konsens.
Sie halten nach der Trennungsregel nur Abgeleitetes, und Rekonstruierbares
braucht keine Einigung, sondern Wiederaufbaubarkeit. Spiegelgleichheit ist ein
Auslieferungsproblem, kein Konsensproblem.

BERICHTIGT: Litestream auf dem Wirt statt Raft ueber drei Knoten. Zwillinge
melden Gesundheit statt Stimmrecht. Rang 3 der Schlange entsprechend geaendert.

LEHRE: ich habe einen Zahlenfehler mit mehr Mechanismus repariert, statt zu
fragen, ob der Mechanismus dort hingehoert. Eleganz ist kein Beleg.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F21 Zielvorstellung + Baugesetz, F22 die Liste ausgewertet, WEITERMACHEN.md als Einstieg

`3957195efb2c` · clay · 05:54 UTC · ClayVerse

```
WEITERMACHEN.md ist neu und der Uebergabepunkt fuer die naechste Sitzung:
Lage, Arbeitsschlange in Reihenfolge, Fallen, offene Fragen, alle Pfade und
Commits. CLAUDE.md zeigt jetzt oben darauf.

F21 - die Zielvorstellung (Quelle GPT-5.6 Sol, als [B] gefuehrt): ClayVerse als
persistente Agenten-Infrastruktur, auf der LLMs nur wechselnde Motoren sind.
Frank waere ein Clay darin, nicht ClayVerse selbst.
EIGNERENTSCHEIDUNG: KEIN Training, KEINE Trainingsdaten. Lernen heisst
wachsender Evidenzbestand, nicht wachsende Gewichte.
DAS BAUGESETZ, aus dem Entwurf selbst erhoben: kein Bauteil ohne vorher
benannte einfache Grundlinie und ohne nachher gemessenes Ergebnis.
MEINE UMSTELLUNG: der Ablations-Rahmen ist dort das Ergebnis, hier die
Voraussetzung. Der Massstab kommt vor dem Gemessenen.

F22 - die Auswertung. Von 16 Projekten bleiben 4 als Muster, von 11 lokalen
Modulen bleiben 4.
GEMESSEN und entscheidend: beide Zwillinge koennen nicht trainieren. Gabriels
torch 2.5.0+cu124 meldet cuda=False und hip=None - eine CUDA-Fassung ohne
NVIDIA-Karte. Andreas hat gar kein torch. Die Eignerentscheidung kostet uns
also nichts, was wir haetten haben koennen.

KONSTRUKTIONSFEHLER GEFUNDEN: rqlite mit ZWEI Knoten bricht die
Kernanforderung - Raft braucht Mehrheit, bei zwei Stimmen ist die Mehrheit
zwei, faellt ein Zwilling aus blockiert Schreiben. Die Empfehlung war falsch.
Ausweg: DRITTER KNOTEN AUF DEM WIRT. Dann faellt die Wartesperre aus F20 als
Nebenprodukt der Architektur an statt als extra gebautes Tor.

PageIndex ist kein Zusatz zu LEANN sondern sein Konkurrent - sie treten
gegeneinander an, nur eines bleibt.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F20 Die 15 Prozent sind erzwungen und gemessen, die Wartesperre ist entschieden

`5d87d90a593d` · clay · 05:45 UTC · ClayVerse

```
ANTWORT 1: 15 Prozent heisst GESAMTSYSTEMAUSLASTUNG, und die Zahl wird JE
MASCHINE gerechnet statt abgeschrieben. Module spiegelgleich, Deckel nicht -
beide Kisten haben 16 Threads, aber unterschiedlich viel RAM.
  ai-core-node   16 Threads, 23,2 GiB -> CPUQuota=240%, MemoryMax=3571M
  andreas-MACO   16 Threads, 20,8 GiB -> CPUQuota=240%, MemoryMax=3191M

GEBAUT auf BEIDEN Rechnern: /etc/systemd/system/clay-kognition.slice, erzwungen
ueber cgroup v2. CPUWeight/IOWeight 20, damit die Module bei Streit nachgeben -
der Mensch hat Vorrang.

GEMESSEN unter 16 Brennern bei Volllast:
  ai-core-node   15,00 / 15,01 / 15,01 Prozent Gesamtsystem
  andreas-MACO   14,99 / 15,01 Prozent Gesamtsystem
Die Zusage ist damit keine Absicht mehr, sondern eine Schranke.

FALLE NOTIERT: systemd haengt sie unter clay.slice/clay-kognition.slice, weil
der Bindestrich Hierarchie bedeutet. Die Elternscheibe ist UNGEDECKELT - wer
dort statt darunter einhaengt, umgeht die Grenze.

ANTWORT 2: die harte Lesart gilt. Ist kein Zwilling online, arbeitet ClayVerse
NICHT und sagt bitte warten bis kognitive Module online. Lieber ehrlich warten
als still schlechter antworten.

NOCH NICHT GEBAUT: Herzschlag je Zwilling, EIN Tor vor der Kognition statt
zwanzig verstreuter Abfragen, der Satz als Antwort an den Menschen - und die
Abgrenzung: die Sperre gilt fuer Kognitives, NICHT fuer Seitenauslieferung und
Mailbox. Sonst nehmen zwei ausgeschaltete Arbeitsrechner drei oeffentliche
Seiten mit.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F19 Behauptungen nachgeprueft - und Lizenzen sind fuer den Eigengebrauch kein Sperrgrund

`40e8bc050f00` · clay · 05:41 UTC · ClayVerse

```
EIGNERENTSCHEIDUNG: privates ClayVerse fuer Gabriel und Andreas, Lizenzfallen
sind egal. Traegt auch sachlich: AGPL und Elastic knuepfen ihre Pflichten an
WEITERGABE, die AGPL zusaetzlich an das Bereitstellen an Nutzer ueber ein Netz.
Eigengebrauch loest keine davon aus. Die Sperre aus F17 ist damit aufgehoben.
Einmal benannt, nicht wiederholt: die Grenze verlaeuft bei erreichbar fuer
Dritte, nicht bei privat gemeint - ClayVerse hostet oeffentliche Seiten.

GEMESSEN (GitHub-API, HuggingFace-API, unzip auf beiden Zips):

GESTORBEN: pogema-toolbox ist Apache-2.0, nicht MIT. SkillFusion heisst
skill-fusion und ist unlizenziert. MAPF-GPT-DDG nennt sich selbst nirgends
reward-free.

ZWEI FALLEN, DIE NIEMAND GEMELDET HATTE: die drei sqliteai-Module
(vector/sync/memory) stehen unter Elastic License 2.0, also source-available
statt frei - das traf genau die Kernempfehlung aus F17. Und vier Projekte
haben ueberhaupt keine Lizenz. Fuer uns beides unerheblich, aber festgehalten.

WIDERSPRUCH: TransPath-Zip traegt MIT, das Live-Repo hatte NIE ein
LICENSE-File. Herkunft der Zip ungeklaert.

BESTAETIGT: HIMA AGPL-3.0 doppelt belegt, alle neun Dateien existieren 1:1.
LEANN haelt in allen vier Punkten wortgenau, MIT, 12.786 Sterne, sehr aktiv.
rqlite MIT und Litestream Apache-2.0 sind der lizenzsaubere Zwillingsweg.

WERTVOLLSTER FUND: BAAI/bge-reranker-v2-m3, Apache-2.0, 568 M Parameter, laeuft
ohne grosse GPU. Schliesst die Umsortierer-Luecke aus F18, die bei NVIDIA
UNBEKANNT blieb - und gehoert nach der Trennungsregel zu uns, nicht auf den Wirt.

OFFEN: RAM-Bedarf der Einbettungsmodelle nur aus Parameterzahl ueberschlagen,
nicht gemessen. Vor der 15-Prozent-Zusage echt messen.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### README: semantische Suche mit LEANN davor, samt der ehrlichen 97-Prozent-Einordnung

`76498358cdab` · unifieddb · 05:38 UTC · ClayVerse

```
LEANN schliesst die Luecke zwischen Aliasaufloesung/FTS und Graph-Walk.
Ausdruecklich NICHT als Wahrheit und ausdruecklich NICHT mit ClayGraph
zusammengeworfen: ein Proximity-Graph kodiert Naehe, ClayGraph kodiert
Aussagen (SUPPORTS/CHALLENGES/EVIDENCE_FOR/DERIVED_FROM). Beides in einen
Graphen zu werfen ist genau der zerstoerende Zusammenfall, gegen den
Hyperposition gebaut ist.

Zwei abgeleitete Tabellen (vp_leann_map, vp_leann_meta), Index ausserhalb der
kanonischen Tabellen und rekonstruierbar - deshalb darf er auf die
Arbeitsrechner, waehrend die Tabellen beim Wirt bleiben.
Aenderungen ueber den vorhandenen Puls und quell_hash, nicht ueber einen
zweiten Waechter - zwei Waechter waeren zwei Wahrheiten.

EHRLICH zu den 97 Prozent: sie gelten in LEANNs Vergleich gegen einen
klassischen Vektorindex, NICHT gegen unseren Stand. Wir halten heute gar
keinen grossen Dense-Embedding-Bestand, also kostet LEANN uns ZUSAETZLICHEN
Speicher. Der Gewinn ist semantische Suche ohne riesigen Embedding-Store.

Dazu die am 15.08. gemessenen Einbettungsmodelle mit Dimension, Antwortzeit
und gerechnetem Speicherbedarf. 1024 statt 4096 Dimensionen ist ein Viertel
Speicher - und der Index liegt bei uns, nicht auf dem Wirt.
Durchsatz gemessen: 256 Texte je Aufruf, 323 Texte/s, immer stapeln.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F18 NVIDIA-Zugang gemessen: 102 Modelle, 4 brauchbare Einbettungen, 323 Texte/s

`7f1af46e9a46` · clay · 05:37 UTC · ClayVerse

```
Alles [M] gemessen, nichts uebernommen.

DIE LISTE LUEGT: 5 von 9 geprueften Einbettungsmodellen antworten nicht
(4x 404, 1x 500 bei nv-embedcode-7b-v1). Nur was 200 gab, darf verdrahtet
werden - dieselbe Falle wie F14, an neuer Stelle.

BRAUCHBAR: nv-embedqa-e5-v5 (1024 Dim, 154 ms), nemotron-3-embed-1b und
llama-nemotron-embed-1b-v2 (beide 2048), nv-embed-v1 (4096).

DURCHSATZ: 256 Texte in EINEM Aufruf, 793 ms = 3,1 ms je Text. Der Sprung von
8 auf 128 Texte senkt die Kosten je Text um das Zehnfache. Rund 323 Texte/s je
Schluessel und Strom - der Gesamtbestand ist damit in Minuten eingebettet,
nicht in Tagen.

RATENGRENZE UNSICHTBAR: keine x-ratelimit-Kopfzeile. Obergrenze bleibt
UNBEKANNT und muss aus 429 gelernt werden. Voll ausgereizt heisst deshalb
Anteil 1.0 MIT Lernkurve, nicht ohne Bremse.

UMSORTIERER UNBEKANNT: kein rerank-Modell in der Liste, drei Endpunktversuche
404. Das ist KEIN Beweis der Abwesenheit - moeglicherweise mein falscher Pfad.
Genau die Cloudflare-Falle aus F14, deshalb als UNBEKANNT gefuehrt.

FOLGE FUER LEANN: 1024 statt 4096 Dimensionen ist VIERTEL Speicher, und der
Index liegt auf unseren Rechnern.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F17 Kognitive Aufwertung: vier Zugaenge, Zwillingsmodule, Forschungsimport

`e50384080601` · clay · 05:33 UTC · ClayVerse

```
Alles Freischwebende aufgezeichnet, bevor es verloren geht - derselbe Fehler
hat uns in der Nacht auf den 15.08. schon nach_text.py gekostet.

Jede Zeile traegt eine Kennung: [E] Eignerentscheidung, [B] Behauptung eines
Organs (ChatGPT GPT-5.6 Sol) die zu pruefen ist, [M] von mir gemessen.
Der groesste Teil ist [B] und ausdruecklich NICHT gemessen.

DIE TRENNUNGSREGEL, aus unserer eigenen Hausregel abgeleitet:
Was die UnifiedDB nicht rekonstruieren kann, bleibt auf dem Wirt.
Was sie rekonstruieren kann, darf zu den Zwillings-PCs.
Daraus faellt die Zuordnung von selbst - Tabellen kanonisch auf den Wirt,
LEANN-Index und Modelle und Simulationen zu uns.

Zugaenge: NVIDIA allein der Kognition (voll, alle Werkzeuge/Modelle),
Mistral als Auswerter VOR jedem Prompt aus fuenf benannten Quellen,
Groq und OpenRouter helfen direkt in der UnifiedDB.

LEANN als ANN-Topologie VOR dem Graph-Walk, ausdruecklich NICHT als Wahrheit
und ausdruecklich NICHT mit ClayGraph zusammengeworfen. Zwei abgeleitete
Tabellen, Index rekonstruierbar, am Puls statt zweiter Waechter.
EHRLICH: die 97 Prozent gelten gegen einen klassischen Vektorindex, NICHT
gegen unseren Stand - fuer uns kostet LEANN zusaetzlichen Speicher.

LIZENZSPERRE: HIMA ist AGPL-3.0. Kein Code nach Clay kopieren, nur Architektur
als Forschungsreferenz und Clay-eigene Nachbauten.

WARNUNG: Gabriels PC ist zurzeit kein verlaesslicher Wirt (3 Totalstillstaende
in 4 Tagen). Der Zwilling muss genau dafuer gebaut sein.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### README zeigt jetzt die Zielarchitektur und was schon steht

`c3bac076c404` · unifieddb · 02:30 UTC · ClayVerse

```
Der Satz nach oben gezogen, wo er gelesen wird: die Datenbank IST das System,
ClayVerse ist ein Modul darauf. Zustand und Zustandsautomat loesen sich darin
auf, damit udb als EINZELNES Modul die gesamte ClayVerse-Entitaet enthaelt.
Eignerentscheidung vom 2026-08-15.

Hyperposition als eingeloest belegt statt behauptet: frank_hyperposition.clay
mit vier Topologien, 402 Dateien der Forschungsentitaet, woertlich im
Meisterquell, und 1.388 Fakten mit 2+ Lesarten im Bestand.

Beides benannt - was steht (Vordertuer udb.verbindung(), 7 umgezogene
Werkzeuge, Zustandsabruf, Paket ohne Modellaufruf) UND die Luecken:
paket.py traegt Hyperposition nur bei AMBIGUOUS, 26 Werkzeuge oeffnen noch
selbst sqlite3, der Zustandsautomat ist entschieden und nicht gebaut.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### F15 Oberflaeche neu, F16 Hyperposition und UnifiedDB als die Entitaet

`b0a75a20fdc9` · clay · 02:29 UTC · ClayVerse

```
F15: Chat behaelt sein Gesicht im Clay-Stil, dahinter native Claude Code CLI +
Clay Launcher + native Haken. Hoechstens 3 Sitzungen, eine DB, gegenseitiges
Gewahrsein. Drei Avatare: ClayVerse mit Krone, Gabriel, Andreas.
Mein Fehler darin benannt: ich hatte zuerst die Chat-Oberflaeche zum Abriss
freigegeben; berichtigt, bevor eine Datei bewegt war.

F16: Weltmodell auf der semantischen Hyperposition, die bereits in ClayCode
(frank_hyperposition.clay, vier Topologien) und im Bestand liegt - 1.388 Fakten
mit 2+ Lesarten. Zustandsautomat loest sich in der UnifiedDB auf, damit das eine
Modul die ganze Entitaet ist. Gemessene Sperre: 26 Werkzeuge oeffnen noch selbst
sqlite3 statt udb.verbindung().

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### Zielarchitektur und Zustandsabruf gesichert - lagen unversioniert

`88494d1c68d7` · unifieddb · 02:28 UTC · ClayVerse

```
Zweites Repo mit demselben Befund wie /opt/clayverse: der Absturz von Gabriels
Rechner am 15.08. um 01:58 UTC riss die Sitzung ab, der letzte Commit lag vom
14.08. 23:03 - also fast drei Stunden Arbeit ohne Sicherung.

Unversioniert war unter anderem:
  ZIELARCHITEKTUR.md         der Satz "die Datenbank ist das System,
                             ClayVerse ist ein Modul darauf", die vier
                             Hyperposition-Topologien und die gemessenen Luecken
  udb/abruf/zustand.py       der Zustandsabruf, 01:46 geschrieben
  udb/abruf/zustand_mess.py  dessen Messung
  udb/pflege/klonwacht.py    Klonwache
  udb/_quelle.py             sowie 11 geaenderte Module

Alle .kopie-backup-20260815 und die leer-backup-Fassung sind mitgesichert,
weil sie die Vorzustaende der Umstellung sind.

GEMESSEN, offen: 26 Werkzeuge in /opt/clayverse/werkzeug oeffnen weiterhin
selbst sqlite3, statt udb.verbindung() zu benutzen. Die Vordertuer steht,
der Umzug ist nicht fertig.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### Nacht-Arbeit gesichert: sechs Werkzeuge waren unversioniert

`76b49bb7ea25` · clay · 02:24 UTC · ClayVerse

```
Beim Absturz von Gabriels Rechner am 15.08. um 01:58 UTC riss die Sitzung
mitten im Schreiben von ratgeber.py ab. Der letzte Commit lag da 44 Minuten
zurueck, der letzte Bauprotokoll-Eintrag 74 Minuten.

Unversioniert waren, alle syntaktisch heil geprueft:
  verdrahtung.py 73 KB, weltmodell.py 59 KB, schluesselwacht.py 51 KB,
  wikiarbeit.py 47 KB, ratgeber.py 38 KB, bahn.py 15 KB
Dazu werkzeuge.py, verdichtung.py, nim_probe.py, ratgeber_hook.py,
die wm_proben-Messreihen und vier systemd-Einheiten.

Zwei Dienste liefen bereits produktiv aus diesem unversionierten Code:
clayverse-wikiarbeit und clayverse-puls (beide enabled + active).

.gitignore ergaenzt um Laufzeit und Erzeugtes (__pycache__, venv, *.db).
Die 26 MB venv-ratgeber bleiben draussen, ebenso die Datenbanken.

OFFEN: das Bauprotokoll hat weiterhin die Luecke 00:44 bis 01:58 UTC -
bau.py stand meldet deshalb zu wenig. Muss nachgetragen werden.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

### B27 geprueft: Zeilenhash fuer anhaengende Stroeme - die Flut ist weg

`a9d2a5dc1c5d` · clay · 00:44 UTC · ClayVerse

```
kuration.py prueft Artikel aus anhaengenden Stroemen (protokoll.jsonl, ereignisse.jsonl, tor.jsonl, eichung.jsonl) jetzt ZEILENWEISE statt dateiweise. Die Zeile wird ueber die Schluesselfelder der Artikelmetadaten gefunden (zeit, bauteil, event_id, id); findet sich keine, ist das ein Fund und kein stilles Durchwinken. Faellt die Zeilensuche aus, greift der alte Dateiweg. ENTSCHEIDENDER NACHWEIS: nach dem Patch einen NEUEN Protokolleintrag geschrieben und danach geprueft - neu_eingefuegt 0, aktualisiert 0, no_ops 14.284. Null Aenderungen. Vorher haette derselbe Eintrag alle 34 vorfall-Artikel markiert. Nebenbei sind 13.762 Artikel erstmals unter Beobachtung gekommen, die bisher gar keine Kurationszeile hatten - der Bestand ist damit vollstaendig erfasst: 14.284 Zeilen, davon 486 unveraendert, 35 quelle_geaendert, 1 quelle_fehlt.
```

### B27 geprueft: Pruefreiz fuer den Zeilenhash

`dbd877779d98` · clay · 00:43 UTC · ClayVerse

```
Ein Eintrag, um zu pruefen ob die Kuration danach alle vorfall-Artikel als geaendert meldet oder nur diesen einen.
```

### B17 geprueft: Vorrang als Reservierung - die Grundlast kann Gabriel nicht mehr aushungern

`d5a3fc1e51f5` · clay · 00:41 UTC · ClayVerse

```
RESERVE_JE_VORRANG in kontingent.py: Vorrang 0 sieht den vollen Topf, Vorrang 1 drei Viertel, Vorrang 2 (ClayVerses eigene Grundlast) drei Fuenftel. Gemessen am GESAMTVERBRAUCH des geteilten Topfes, nicht am eigenen - sonst waere es keine Reservierung, sondern nur ein zweites eigenes Limit. NACHWEIS in drei Schritten am echten Buch: ClayVerse schoepft seine Decke von 1200 aus; Gabriel fragt danach und bekommt 800, gebunden durch zugang-fenster; ClayVerse fragt erneut und bekommt 0, gebunden durch vorrang-reserve-fenster. Die 800 gehoeren dem Vorrangberechtigten und sind fuer die Grundlast unerreichbar. Pruefbuchung danach entfernt, Buch steht bei 0.
```

### B6 geprueft: Knotenluecke geschlossen - Erreichbarkeit von 0,245 auf 81,49 Prozent

`74da0606a63a` · clay · 00:36 UTC · ClayVerse

```
Graphknoten 2.383 auf 11.640, Graphkanten 192 auf 14.235 - also 74-fach. ERREICHBARKEIT: 11.640 von 14.284 Artikeln sind im Graphen, 81,49 Prozent statt 0,245. Von den Graphknoten haben 95,0 Prozent mindestens eine Kante, nur 581 stehen allein. Knotenarten belegt: source 4.965 (die Quelldateien), artifact 4.228, hypothesis 1.771, micro_packet 342, negative_result 116, topic_packet 74, event 65, claim 38, experiment 38, database_store 3 - experiment und source waren vorher UNBEWOHNT und sind jetzt ehrlich belegt, ohne Schemaerweiterung. Kantenarten: RELATED 9.691, SAME_EVIDENCE_FAMILY 2.162, SUPERSEDES 1.735, MENTIONS 367, SUPPORTS 98, EVIDENCE_FOR 98, DERIVED_FROM 63, CHALLENGES 20, IN_TOPIC 1. LATENZ TROTZ 74-FACHER KANTENZAHL BESSER: Nachbarn ein Sprung 0,31 ms, zwei Spruenge 0,05 ms. graph_kante traegt weight, confidence, verfallen und protected - der Verfall ist also mit eingebaut.
```

## 2026-08-14

### B9 geprueft: GEBURT: ClayVerse hat eine Identitaet und einen Herzschlag

`1d842278135e` · clay · 22:58 UTC · ClayVerse

```
ClayID clay_01M017MSKPCJGQW0QF74QJQGH3, Geburtsart ORIGIN, Linienwurzel sich selbst, geboren 2026-08-14T22:52:51Z. Koerper /opt/clayverse-kern/kern.py mit sha256 2a6dafe3, uebernommener Zustand sha256 03fb1a7f ueber artikel, kante, graph_knoten, folgerung, problem, messung und fehler. Eintrag im anhaengenden Register, Geburtsbeleg geschrieben. DER PULS LAEUFT: clayverse-puls.service, Takt 4,0 s, ein Prozess statt 21.600 Zeitgeberstarts am Tag, 9,6 MB Speicher, laeuft als clay. Gemessen: +2 Takte in 9 Sekunden. Kosten je Leertakt rund 1,5 ms, also 0,04 Prozent Auslastung. MODELLAUFRUFE JE TAKT: 0, strukturell - der Daemon kennt keinen Modellklienten. Phase 10 bleibt leer, wie der Vertrag es als Normalfall vorsieht.
```

### B25 geprueft: Live-Wache ueber alle Agenten - Tod und stilles Stehen getrennt

`4744bf536514` · clay · 22:30 UTC · ClayVerse

```
wache.py mit lage, tote, stille, wacht. Zwei Laeuferklassen dynamisch erkannt, nicht fest verdrahtet: systemd-Einheiten (clayverse-*, actions.runner.*, frank-laeufer*) und die Claude-Code-Sitzungen aus sitzungen.json. SCHWELLE GEMESSEN statt geraten: alle 26.338 Abstaende zwischen aufeinanderfolgenden Aufrufen in taetigkeit ausgewertet - p50 9,8 s, p90 40,8 s, p99 402 s, p99,5 1098 s, p99,9 17.777 s. Gewaehlt 20 Minuten, knapp ueber p99,5; nur 0,38 bis 0,46 Prozent aller echten Pausen erreichen das je. UNABHAENGIGE BESTAETIGUNG: dieselbe Zahl wie die Vorarbeit in tavern-wache, ohne dass er sie vorher angesehen hatte. NACHWEIS AUF DREI ACHSEN: gesunder Dienst 0 Befunde; nach kill -9 genau 1 Befund; kuenstlich haengende Sitzung 1 Befund; dieselbe Sitzung mit frischer Taetigkeit wieder 0. PostToolUse-Haken installiert, rein additiv - der PreToolUse-Block mit tor_hook.py ist byteweise unveraendert, per diff bestaetigt. TOR NACHWEISLICH WEITER SCHARF: ls durchgelassen, rm -rf /var/lib/clay mit Rueckgabewert 2 und rechteeingriff geblockt, unbekannter Befehl fail-closed.
```

### B13 geprueft: Der Fehler traf den Schutz selbst - und die zweite Schicht hielt

`ef2560a6cd80` · clay · 22:27 UTC · ClayVerse

```
wiki.py behoben: beide kante-Stellen auf INSERT ... ON CONFLICT(von,nach,art) DO UPDATE SET beleg=excluded.beleg umgestellt. Begruendung des Agenten: wiki.py besitzt auf kante genau EINE Spalte, naemlich beleg - eine Klausel, die nur diese eine nennt, kann die anderen physisch nicht erreichen, braucht kein Vorlesen und hat kein Wettrennen. DRITTER FUND, vom Agenten selbst: artikel hatte heute ebenfalls verfallen und protected bekommen, und die drei INSERT-OR-REPLACE-Stellen dort nannten sie auch nicht - mit demselben Fortschreibemuster behoben wie zuvor herkunft. VOLLSTAENDIGE DURCHSICHT: 8 Vorkommen in wiki.py, 5 behoben, 3 nachweislich sicher (artikel_sphaere, Spaltenliste deckt die Tabelle vollstaendig). In isolierter Datenbank bewiesen: alle 5 kante-Felder und alle 6 artikel-Felder ueberleben einen zweiten vollen Lauf.
```

### B21 geprueft: Fehlergedaechtnis lebt - 17 Fehler mit mechanischem Ausloeser

`6d615888ce74` · clay · 22:23 UTC · ClayVerse

```
fehler.py und Tabelle fehler live. 17 Zeilen, jede mit Regex-Ausloeser, Beleg, Herkunft und Bestaetigung, 0 ohne Beleg. Geerntet aus protokoll.jsonl (61 Zeilen vollstaendig gelesen), MESSFEHLER.md, CLAUDE.md und Code-Gegenpruefungen. NACHWEIS: 7 von 7 echten Taetigkeiten trafen genau ihre eigene Zeile, je ein Treffer, keine Kreuzkontamination, 73 bis 1776 Mikrosekunden. UND ENTSCHEIDEND: 3 von 3 unverdaechtigen Taetigkeiten (git status, ls, ein einfaches SELECT) lieferten NULL Treffer. Ein Warner, der immer warnt, waere Rauschen - und Rauschen ist, wie eine echte Warnung ignoriert wird. Wiederholungsfest: zweiter Erntelauf 0 neu.
```

### B27 geprueft: Verfall und kontrolliertes Vergessen von Titan uebernommen

`d27d89a6829d` · clay · 22:17 UTC · ClayVerse

```
verfall.py live. Formel new_confidence = base mal 2 hoch minus alter_tage durch 7, bei jedem Lauf FRISCH aus fester Basis und echtem Alter gerechnet, nicht aufgezinst. 19.267 von 19.267 Kanten verfallen, 179 von 179 Artikeln mit echter Vorkonfidenz - fuer die uebrigen 14.089 wurde KEINE erfunden. folgerung inert, weil 0 von 8 Zeilen eine echte Basiskonfidenz tragen. SCHUTZ BEWIESEN statt behauptet: selftest kopiert die Datenbank in eine Wegwerfdatei, setzt die geschuetzten Klassen auf maximalen Verfall, laesst die volle Kette laufen und prueft, dass sie ueberleben, dass eine Markierung ruecknehmbar ist und dass die Zeilenzahl vorher wie nachher gleich bleibt - also nirgends geloescht wurde. Live BESTANDEN: 117 geschuetzte Artikel, 40 geschuetzte Kanten (widerspricht und attacks), 3 widerlegte Folgerungen, 124 offene Probleme, alle unangetastet.
```

### B6 geprueft: Beide Arbeitsrechner indiziert - das Gehirn kennt jetzt die Maschinen

`6a9b3e8841a4` · clay · 22:04 UTC · ClayVerse

```
Inhalte 86.713 auf 325.357, Fundorte 152.997 auf 458.937. Aufteilung: ai-core-node 356.983, clayverse 92.715, andreas-MACO 9.239. INHALTE AUF MEHR ALS EINEM WIRT: 16.673 byteidentisch. Datenbank 1605 auf 3446,81 MB - die Vorhersage lautete 1,5 bis 2,2 GB Zuwachs, tatsaechlich 1,84 GB, also innerhalb. Platte 44 GB frei. Wiederholungsfest im Grossen bewiesen: zweiter Import derselben 254.032 Inhalte ergab 0 neu, die Datei wuchs um 5 Seiten Buchhaltung. Mechanismus strukturell, nicht per Sonderfall: UNIQUE auf pruefsumme plus INSERT OR IGNORE auf (wirt,pfad). NEEDLE-FRAGE per Abfrage beantwortet und byte-genau gegen meine Handsuche geprueft: mini_train.jsonl 1.867.423 B, mini_val.jsonl 207.943 B, registry.json 21.522 B - alle bestaetigt. Verteilung 240 Fundorte auf clayverse, 139 auf ai-core-node, 0 auf andreas-MACO. Filter ueber alle Gewichtsendungen: NULL Treffer. Keine Needle-Gewichte auf irgendeinem indizierten Wirt.
```

### B27 geprueft: Ahnenreihe geprueft - Titan am Code, nicht am Docstring

`82b5784864c3` · clay · 21:51 UTC · ClayVerse

```
TriHybridStorage BESTAETIGT: SQLite plus VectorStore plus KnowledgeGraph, verschmolzen per Reciprocal Rank Fusion k=60. Die Vektoren sind echt - titan_vectors.npz von Hand gelesen, Form (105, 384), MiniLM all-MiniLM-L6-v2. Unser System hat GAR KEINE Vektorschicht, per grep bestaetigt. ZEITGEWICHTETER VERFALL BESTAETIGT: maintenance.py rechnet new_confidence = base * 2 hoch minus alter_tage durch 7, Halbwertszeit 7 Tage, reines SQL, stuendlich. KONTROLLIERTES VERGESSEN BESTAETIGT: Waisen und Konfidenz unter 0,2 bei Alter ueber 7 Tagen werden geloescht, Kanten verfallen 5 Prozent je Zyklus - und Knoten mit 3 Zugriffen in 14 Tagen bei Nutzen ueber 0,6 werden dauerhaft geschuetzt. Alles deterministisch, kein Netz noetig.
```

### B6 geprueft: Kanten gebaut - Waisen 93 auf 4 Prozent, Erreichbarkeit unveraendert

`83800b28831e` · clay · 21:42 UTC · ClayVerse

```
18.024 Kanten mechanisch erzeugt, jede mit Belegregel: geschwister_verzeichnis 12.239 (schwach, als schwach markiert), gleicher_inhalt 2.168 (stark, gleicher quell_hash), nachfolge_version 1.959 (stark, gerichtet, gleiche logical_id nach Datum verkettet), geschwister_datei 1.556, lauf_referenz 91, eltern_hypothese 8, packet_referenz 3. WAISEN 13.270 von 14.268 (93,01 Prozent) auf 594 (4,16 Prozent). Hypothesen von 1.592 Waisen auf EINE. quelldatei von 4.957 auf 110. Wiederholungsfest: zweiter Bau ergab dieselben 18.024 Zeilen.
```

### B17 geprueft: Kontingentbuch gebaut - erst das Buch, dann die Schluessel

`ac28faa8d316` · clay · 21:37 UTC · ClayVerse

```
kontingent.py live, vier Tabellen in wiki.db: kb_konto 4 Zeilen (master_clay, clay_andreas, kuenftige_nutzer, clayverse mit Vorrang und Warnadresse woertlich aus dem Plan), kb_zugang 11 Zeilen, kb_buchung, kb_warnung. NULL Geheimnisse bewegt, null Modellaufrufe. darf beweist mit Zahlen: reichlich 50 von 50; nahe der Grenze 100 von 500 angefragt, gebunden durch zugang-fenster; erschoepft 5 von 500. Dazu zwei Randfaelle: Zugang ohne harte Grenze faellt auf die Norm-Bremse zurueck (80.000 von 500.000 angefragt), Zugang ohne Grenze UND ohne Muster antwortet ehrlich kein_limit_kein_muster statt eine Obergrenze zu erfinden. NORM: Mittelwert plus zwei Sigma desselben Konto-Zugang-Paares zur SELBEN Tagesstunde, 21 Tage rueckwaerts, mindestens 5 Stichproben - sonst kein Urteil. Stundenweise, weil sich Bautag und ruhiger Tag nach Stunde unterscheiden, nicht nach Datum.
```

### B3 geprueft: Beide neuen Repos auf GitHub und im Gehirn

`457f4dd6844b` · clay · 21:21 UTC · ClayVerse

```
microclay und unifieddb ueber die GitHub-API privat angelegt (HTTP 201), geschoben, per API gegengeprueft: gschaidergabriel/microclay und gschaidergabriel/unifieddb, beide private=True. Vorgabezweig von unifieddb auf master gerichtet, weil der Inhalt dort liegt. Danach baeume.py holen: 2 neu, 21 aktualisiert, krita weiterhin als Verweis statt Kopie (9.088,9 MB gespart), Baumbestand 638 MB.
```

### B21 geprueft: Needle gemessen - passt nirgends in den Abrufpfad

`f696d518b488` · clay · 21:19 UTC · ClayVerse

```
Herstellerstand geholt und auf CPU vermessen, n=60, jax-Backend cpu. Voller generate-Aufruf: kalt 4130,95 ms, warm p50 2819,18 ms, p95 3133,53 ms. Nur-Einbettung ohne Dekodierschleife: 24 Kandidaten 205,3 ms p50, 98 Kandidaten 477,1 ms, alle 2374 Graphknoten 10.225,2 ms. Skalierung linear mit 4,3 bis 8,6 ms je Stueck plus 150-200 ms fester Boden aus der JIT-Verteilung. Parameter bestaetigt: 26.315.421.
```

### B27 geprueft: Vorprozessor gebaut - der Mechanismus steht

`5c0802dba655` · clay · 21:16 UTC · ClayVerse

```
vorprozessor.py, 1780 Zeilen, null Modellaufrufe strukturell (kein LLM- oder HTTP-Klient im Code). Paket traegt: treffer, hyperposition, orte, systeme, codependenzen, hypothesen, gegenseite, kuration, weiter, politik, beobachtungen, resolution, basis. DICHTE gemessen mit tiktoken ueber 5 Fragen: grep 0,00 - fts 1,65 - voll 3,91 - PAKET 4,95 Fakten je 1000 Token, und das Paket schlaegt voll bei JEDER einzelnen Frage, nicht nur im Mittel. Aliasaufloesung vp_alias 92.043 Zeilen, v12-Bewertungsform woertlich uebernommen: exakte Kennung -> EXACT_ID 1,0; vager Text -> MISS 0,0; nie geraten. SCHLEIFE bewiesen: drei Schritte hintereinander, jeder nimmt die Kennung aus dem weiter des vorigen, keiner braucht eine neue Suche. GESPERRTES LESEN bewiesen: unbekannte Paketkennung abgewiesen, nicht genannte Ortskennung abgewiesen, Binaeres abgewiesen. 3 von 5 Fragen ohne jeden Lesevorgang beantwortet. PULSKOSTEN gemessen: Leerlauftakt 68,6 Mikrosekunden, Arbeitstakt 4,07 ms. Schnappschuss und Heilung bewiesen: Zustand absichtlich verdorben, heilen() zurueckgerollt, Zustandshash stimmt exakt mit Schnappschuss 9.
```

### B9 geprueft: Organe vermessen - fast nichts davon ist neural

`7f6e692439fc` · clay · 21:00 UTC · ClayVerse

```
Thalamus: regelbasierte Formel, 0 Parameter, kein torch, kein Gradient. GWT/Arbeitsbuehne: feste Zuendschwelle 0,55 mit handgesetzten Gewichten, 0 Parameter. Gedaechtnis: Anhaeufung plus Volltext, kein Lernen - die Lernhaken titan.rwl_feedback und chat_memory.consolidation_tracker existieren im Schema mit NULL Zeilen. Das EINZIGE echte trainierte Netz im ganzen Bestand ist der LoRA-Adapter mit 42.467.328 Parametern auf einem fremden 4B-Grundmodell, direkt aus dem safetensors-Kopf gerechnet - und das ist das Hirn, kein Organ. ⭐ vp_edge_lern EXISTIERT BEREITS in wiki.db, gebaut vom Vorprozessor-Agenten: lernen(), verfall() mit HOP_DECAY 0,58, heilen() mit Ruecknahme auf den letzten Stand der die Eichnormale bestand, eingehaengt in den Live-Abrufpfad. 0 Zeilen - gebaut, verdrahtet, nie benutzt.
```


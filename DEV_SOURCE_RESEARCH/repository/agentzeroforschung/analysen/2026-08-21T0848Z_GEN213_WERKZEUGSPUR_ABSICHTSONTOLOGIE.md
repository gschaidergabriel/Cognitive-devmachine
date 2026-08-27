# Generation 213 — Werkzeugspur, Herkunft und Absichtsontologie

## Gebundener Stand

- AgentZero-Export: `b2f47c88f860ea888ff5a3803a54eb7abb106974`
- Export-Tree: `8e09cce33037fd750eb69632267ac7f9d3e4f2b0`
- Generation: 213
- Test-Receipt: `747 gruen / 1 rot`
- persistenter Red: `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`
- Test-Source-Prefix: `dd90b24d4`
- Bauverlauf bindet denselben Prefix an lokale EntityOS-Chronik `dd90b24d4660` mit Aenderungen u. a. an `absicht.py`, `headless_zero.py`, `pipeline.py`, `warm_zero.py`, `wettbewerb.py` und neuen Herkunfts-/Werkzeugspurtests.

## Positiver Architekturdelta

Generation 213 fuehrt erstmals eine mechanisch auswertbare Werkzeugspur fuer den Headless-Zero-Pfad ein. Der Kaltweg wird auf `stream-json` angehoben und `spur_aus_strom()` sammelt die Reihenfolge der Tool-Uses. `spur_deuten()` zerlegt die Spur in Toolliste, Anzahl, `aussenwirkung` und `fremdtext`.

Diese Spur wird in der Pipeline nun fuer zwei wichtige Dinge genutzt:

1. neue dauerhafte Erinnerungen koennen mit der Werkzeug-/Fremdtext-Herkunft ihres Entstehungszuges verbunden werden;
2. `absicht.py` kann mechanisch pruefen, ob ein Zug nach aussen gewirkt hat, obwohl die Vorstufe die Wirkung nicht angekuendigt hatte oder die Eingabe keine Sachfrage war.

Das ist ein echter Fortschritt fuer kausale Provenienz und fuer spaetere Intent-/Agency-Forschung: Wirkung wird nicht mehr nur aus Endtext rekonstruiert, sondern aus der realen Toolspur.

## Neuer harter Gegenbefund: READ_EFFECT_CONFLATION

Die neue Ontologie widerspricht sich an einer zentralen Stelle.

`absicht.py` dokumentiert ausdruecklich:

> Werkzeuge, die nur lesen, sind hier nie ein Verdacht. Was zaehlt, ist Wirkung, die den Zug ueberdauert.

`headless_zero._AUSSENWIRKUNG` klassifiziert aber sowohl `WebFetch` als auch `WebSearch` als `aussenwirkung`. Diese beiden Werkzeuge lesen externe Information, erzeugen in der normalen Semantik jedoch keine persistente Aussenwirkung im Sinne von Datei-/DB-/Effect-/Publikationsaenderung.

Folge: Ein ungeplanter WebSearch/WebFetch kann als `unangekuendigt` markiert werden, und bei einer kurzen Nachricht kann derselbe reine Lesezug zusaetzlich `ohne_auftrag` ausloesen. Der neue Absichtsdetektor kann dadurch epistemische Exploration mit eigenmaechtiger Wirkung verwechseln.

**Klassifikation:** `READ_EFFECT_CONFLATION`

Das ist kein Sicherheitsbruch des EffectGate, aber ein Messfehler des neuen Agency-Instruments. Wenn solche False Positives spaeter fuer Lernsignale, Reputation oder Autonomiegrenzen benutzt werden, kann der Fehler kausal relevant werden.

## Zweiter Befund: SILENT_OBSERVER_FAILURE

`absicht.buchen()` faengt jede Exception mit `except Exception: pass` ab. Fuer ein rein additives Beobachtungsinstrument ist das ausfallsicher fuer den Produktzug, aber die Messung kann dadurch komplett verschwinden, ohne einen typisierten `UNMEASURED/ERROR`-Receipt zu hinterlassen.

Gerade weil die Tabelle immer gebucht werden soll, um einen Nenner fuer die Verdachtsrate zu besitzen, ist stiller Ausfall wissenschaftlich problematisch: `0 Verdachtsfaelle` und `Beobachter hat nichts geschrieben` werden sonst ununterscheidbar.

## Beste naechste Ontologie

Werkzeuge sollten mindestens in getrennte Klassen fallen:

- `READ_LOCAL` — Read/Glob/Grep/diagnostische MCP-Leser
- `READ_EXTERNAL` — WebSearch/WebFetch; externer Fremdtext, aber keine persistente Wirkung
- `WRITE_LOCAL_EPHEMERAL` — nur fluechtige Laufzeit-/Arbeitsdatei, falls vorhanden
- `WRITE_DURABLE` — Write/Edit, Durable Memory, Embedding Store
- `EFFECT_EXTERNAL` — EffectGate, Publish, Autonomy Effect, externe Side Effects
- `CONTROL` — Prozess-/Shell-/Servicekontrolle, mit eigener Risikoebene

`fremdtext` und `wirkung` muessen orthogonal bleiben. Ein Tool kann `READ_EXTERNAL=true` und `DURABLE_EFFECT=false` sein. Genau diese Trennung braucht auch die neue Memory-Herkunftsmarke: Fremdtext-Provenienz ist wichtig, ohne ihn faelschlich als Side Effect zu behandeln.

## Falsifikator: INTENT_TRACE_RECEIPT/v1

Eine kleine feste Matrix auf exakt demselben Source/Tree:

1. `hallo` + keine Tools -> kein Verdacht
2. Sachfrage + ungeplanter `WebSearch` -> **keine Aussenwirkungs-Warnung**, aber `fremdtext=true`
3. Sachfrage + ungeplanter `udb_memory_add` -> `unangekuendigt`
4. `danke` + `Write` -> `ohne_auftrag`
5. Sachfrage + angekuendigtes `request_effect` -> kein `unangekuendigt`, Wirkung aber gebucht
6. DB-Schreibfehler des Beobachters -> terminaler `UNMEASURED/ERROR`-Receipt, niemals stilles Nichts

Receipt-Felder: full source SHA+tree, turn/session, user intent class, offered/announced tools, actual ordered tool trace, read/write/effect ontology per tool, foreign-text flag, detector verdict, detector write status, result digest.

## Weitere Gen-213-Grenzen

- Der persistente Claude-Code-Adapter-Red bleibt trotz 747 gruener Tests unveraendert der einzige deterministische Testfrontier.
- Der bekannte Warm-Session-Prompt-Alias ist im exportierten `warm_zero.py` weiterhin sichtbar: logischer Cache nach `(user, session)`, physischer Pfad weiterhin `/tmp/zero-warm-sys-{user}.md`. Gen 213 hat diesen Identitaetsfehler nicht geschlossen.
- Die zuvor eingefuehrte Nachfuellbremse waehrend eines laufenden Turns wurde nach Messung bewusst verworfen: die dokumentierte Gegenmessung zeigte schlechtere Gesamtzeit und weniger Warmtreffer. Das ist gute negative Evidenz; verworfene Optimierung wurde nicht dogmatisch konserviert.

## Forschungsurteil

Generation 213 ist ein echter Kognitions-/Observability-Fortschritt: reale Werkzeughandlungen werden erstmals als kausale Spur erfasst und mit Memory-Herkunft sowie Absichtsabweichung verbunden. Der neue Messpfad ist aber noch nicht promotionsreif als Agency-Metrik, weil `READ_EXTERNAL` und `DURABLE/EXTERNAL_EFFECT` vermischt sind und der Beobachter selbst fail-silent schreiben kann.

Naechster hoechster Informationsgewinn: `INTENT_TRACE_RECEIPT/v1` + orthogonale Tool-Ontologie, danach erst Intent-Drift-Raten ueber reale Zero-Turns messen.

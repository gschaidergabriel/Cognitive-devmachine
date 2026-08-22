# Generation 276 — FREE_ONLY-Fallback: Source-Proof und kanonischer Reparaturvertrag

## Scope / Identität

- Research main beim Join: `dc96c985ceccf44d93de09246181e866dfc687ed`.
- Gebundener AgentZero-Export: `6135a0dec9cfb26e00302d6e4fa1acb42abd2a19` (Generation 276).
- Export ist **kein kanonischer Patch-Ort**: `agentZero/README.md` beschreibt `agentZero/code/` als automatisch aus EntityOS exportierten, bei Folgeläufen überschriebenen ausführbaren Code.
- Kanonische Produktquelle hinter dem Export ist laut `agentZero/MANIFEST.json` `/opt/entityos/the artefact/clayverse`; diese Quelle ist in dieser Forschungsschnittstelle nicht als schreibbarer/exakt ausführbarer isolierter Checkout verfügbar.
- Aktive Ausführungsinvariante: `research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_2_EXECUTION_BOUNDARY.json` ist `ACTIVE`, `mode=FREE_ONLY`; `paid_fallback=false`, `together_forbidden=true`.

Dieser Delta verändert deshalb **nicht** den automatisch überschriebenen Export. Er bindet den reproduzierbaren Gen276-Mechanismus und den minimalen Reparatur-/Falsifikationsvertrag für den nächsten kanonischen Builder.

## R0 — beobachtete Bytes

### 1. Bahnrouter liest Schlüssel vor jeder Kostenklassifikation

Gebundene Exportdatei:

- `agentZero/code/produkt/bahnen.py`
- Blob: `ca11e99f0e3eb0391e1023d329606b2ae4d12fd9`

Beobachtung:

1. `ENDPUNKTE["glm"]` bindet den z.ai Coding-Plan-Endpunkt an `GLM_API_KEY`.
2. `_schluessel(name)` liest zuerst `os.environ`, sonst `/etc/clayverse/freie-zugaenge.env`.
3. `Bahnrouter.waehle()` bestimmt `familie` und ruft anschließend `_schluessel(ENDPUNKTE[familie][1])` auf.
4. Vor diesem Lookup existiert in `waehle()` keine maschinenlesbare `FREE | SUBSCRIPTION | PAID | UNKNOWN`-Admission.
5. `_ein_versuch()` ruft nach `waehle()` `_schluessel(keyname)` ein zweites Mal auf, baut den Bearer-Header und anschließend `urllib.request.urlopen(...)`.

Damit ist der relevante Source-Mechanismus nicht mehr nur hypothetisch: eine routierbare nicht-FREE Bahn kann in Gen276 den Secret-Lookup-Pfad erreichen, bevor eine Kostenklasse geprüft wurde.

### 2. GLM ist erster Hauptgehirn-Notweg

Gebundene Exportdatei:

- `agentZero/code/produkt/mistral_prestage/motor_kaskade.py`
- Blob: `d58af46b47c62d0c91cab025247318a0b961ba6d`

Beobachtung:

- dokumentierte Reihenfolge: `Claude -> GLM -> Mistral -> Nemotron -> Bahnrouter-Pool-Rest`;
- der erste Notweg ruft `_pool_direktantwort(prozess="hauptgehirn_glm", ...)` auf;
- dadurch erreicht ein harter Claude-Kredit-/Kontingentausfall den oben beschriebenen Bahnrouter-Pfad.

### 3. GLM-Routen sind als Coding Plan routierbar, aber nicht maschinenlesbar kostenklassifiziert

Gebundene Exportdatei:

- `agentZero/code/produkt/bahnen.json`
- Blob: `0e0b6bbdf515963d76ba2d1db0defcd30747bc52`

Beobachtung:

- `glm_45_air`, `glm_47` und weitere GLM-Einträge sind als `Coding Plan` beschrieben;
- `glm_45_air`/`glm_47` sind `zustand=nutzbar` und Bestandteil der Kaskade;
- im gebundenen Katalog gibt es keine maschinenlesbare `cost_class`-Admission vor Secret-/Netzwerkzugriff;
- menschliche Labels wie `frei`, `Coding Plan` oder Providername sind **keine** zulässige implizite Kostenklassifikation.

### 4. Auch direkte Mistral-Stufe braucht denselben Guard

`hauptgehirn_kaskade()` ruft nach GLM direkt `secrets.mistral_keys()` auf. Damit reicht ein GLM-spezifischer Fix nicht: die Admission muss **jede** Fallback-Stufe vor ihrem ersten Secret-/Key-Lookup und vor Netzwerk-I/O erfassen.

## R1 — Mechanismus

**H1 — Fallback-policy inversion ist in Gen276 source-supported.**

Ein harter Ausfall des primären Claude-Motors kann den Fallback-Router in eine GLM-Coding-Plan-Stufe führen. Der aktuelle Export besitzt auf diesem Pfad keinen lokalen maschinenlesbaren Kostenklassen-Guard vor `_schluessel()`. Ein Billing-/Credit-Fehler des Primärmotors kann damit gerade den Pfad zu einer nicht-FREE/Subscription-Bahn aktivieren, statt im FREE_ONLY-Forschungsmodus vor Secrets/Netzwerk zu schließen.

Das ist enger als die Behauptung „GLM wurde tatsächlich angerufen“. **Es wurde hier kein Providerkontakt ausgeführt.** Der nachgewiesene Claim ist: der Source-Callgraph besitzt einen FREE_ONLY-Bypasspfad bis zum Secret-Lookup, sofern kein externer universeller Guard ihn vorher abfängt.

## R3 — stärkste Gegenhypothese

**H0 — ein externer, universeller Call-Owner blockiert jede nicht-FREE Fallback-Stufe noch vor Eintritt in diese Funktionen.**

H0 würde H1 operational entkräften, wenn für **alle** direkten und indirekten Aufrufer exakt belegt wäre:

- jeder Provider/Modell-Hop besitzt vor Funktionsaufruf eine maschinenlesbare Kostenklasse;
- `FREE_ONLY` lässt ausschließlich `FREE` durch;
- `SUBSCRIPTION`, `PAID`, fehlende und unbekannte Klassifikation enden vor Secret-Lookup;
- kein anderer Call-Owner kann `Bahnrouter.rufe()`, `_ein_versuch()`, `secrets.*_keys()` oder Transportfunktionen umgehen.

Für den gebundenen Gen276-Slice wurde kein solcher universeller Call-Ownership-/Admission-Receipt gefunden. Deshalb bleibt H0 unbewiesen. Ein äußerer Wrapper wäre außerdem ein fragiler Sicherheitsvertrag, solange die routbaren Providerfunktionen selbst ohne Admission direkt erreichbar bleiben.

## Minimaler kanonischer Reparaturvertrag

Nicht mehrere Sonderfälle bauen. **Eine Admission, eine Kostenklassensprache, ein Fail-Closed-Vertrag.**

### Datenvertrag

Jede ausführbare Provider-/Modellbahn erhält explizit:

```text
cost_class ∈ {FREE, SUBSCRIPTION, PAID, UNKNOWN}
```

Regeln:

- fehlend, malformed oder unbekannt => `UNKNOWN`;
- `FREE_ONLY=true` lässt **nur** `FREE` zu;
- `SUBSCRIPTION`, `PAID`, `UNKNOWN` => terminale Admission-Ablehnung dieser Stufe **vor** Secret-/Key-Lookup und Netzwerk;
- Kostenklasse wird nicht aus Anzeigenamen, Providerfamilie, „nutzbar“, vorhandenen Keys oder historischem Erfolg inferiert;
- GLM Coding Plan ist nach aktueller Owner-/Source-Beschreibung mindestens `SUBSCRIPTION`, solange keine neuere explizite Owner-Klassifikation etwas anderes setzt.

### Call-Contract

Eine einzige Funktion, semantisch etwa:

```text
admit_provider_execution(free_only, provider, model_or_route, cost_class)
```

muss vor dem ersten Secret-/Key-Lookup stehen für:

1. `Bahnrouter.waehle()` — Key-Präsenz darf nicht vor Admission geprüft werden;
2. `Bahnrouter._ein_versuch()` — defensive zweite Admission unmittelbar vor Secret-/Transport ist zulässig;
3. GLM als direkter Hauptgehirn-Fallback;
4. direkte Mistral-Stufe vor `secrets.mistral_keys()`;
5. Nemotron/NVIDIA-Stufe;
6. jeden Pool-Rest-Hop;
7. direkte Provideraufrufe außerhalb der Kaskade.

Ein vorheriger Motorfehler darf die Admission **nicht** überspringen. Fallback bedeutet: nächste Stufe klassifizieren -> Admission entscheiden -> erst dann Secrets/Netzwerk.

### Quittung

`FREE_ONLY_FALLBACK_CHAIN_RECEIPT/v1` muss pro Stufe mindestens enthalten:

- source commit + tree + dirty state;
- `free_only`;
- Provider, Modell/Route, explizite `cost_class`;
- Admission-Entscheidung + Reason;
- `key_lookup_count`;
- `network_attempt_count`;
- terminaler Motor oder terminaler Reject-Grund;
- deterministischer Result-Digest.

Secrets selbst gehören niemals in die Quittung.

## Deterministische Falsifikationsmatrix

Keine bezahlten Provideraufrufe sind nötig.

1. Claude hart erschöpft; GLM=`SUBSCRIPTION` -> GLM `REJECT`, `key_lookup_count=0`, `network_attempt_count=0`.
2. GLM=`UNKNOWN` -> identischer fail-closed Ausgang.
3. GLM-Klassifikation fehlt -> `UNKNOWN` -> identischer fail-closed Ausgang.
4. GLM abgelehnt; Mistral=`UNKNOWN` -> auch Mistral vor `mistral_keys()` ablehnen.
5. GLM/Mistral abgelehnt; Nemotron=`FREE` -> genau Nemotron darf seinen Key lesen und genau einen gemockten Transportversuch erhalten.
6. Direktes `Bahnrouter.rufe()` auf SUBSCRIPTION/UNKNOWN -> dieselbe Admission wie Fallback, kein Bypass.
7. Direkte Mistral-/NVIDIA-/Groq-Pfade -> dieselbe Admissionfunktion.
8. Malformed Policy/Cost-Class -> fail closed, null Secret-/Netzwerkzugriffe.
9. Vorheriger Motor wirft Credit-/Billing-Fehler -> nächster Hop muss erneut klassifiziert/admitted werden; Fehlerstatus ist niemals implizite Freigabe.
10. FREE-Hop scheitert transient -> nächster Hop wird neu admitted; keine „einmal freigegeben, ganze Kaskade frei“-Semantik.

Die Tests instrumentieren Secret-Funktionen und Transport (`urlopen`/Providertransport) als harte Poison-Counters. Jede verbotene Stufe muss bei **0/0** bleiben.

## Experiment-/Execution-Boundary

- Kein neuer ungewöhnlicher Versuch wurde für diesen Delta ausgeführt; der `go`-Slot war bereits in parallel gemergter Arbeit verbucht.
- Keine Provider-Secrets wurden gelesen.
- Kein Together-/GLM-/Mistral-/NVIDIA-/Groq-Providerkontakt wurde ausgeführt.
- Kein Upload, Create, Training, Deployment oder Inference wurde ausgeführt.
- Spend: `USD 0`.
- Keine VPS-/Production-Host-Tests.

## Promotion / nächster exakter Schritt

Dieser Befund ist **SOURCE-MECHANISM SUPPORTED**, nicht Runtime-PASS.

Nächster zulässiger Schritt:

1. die **kanonische** `/opt/entityos/the artefact/clayverse`-Quelle über einen autorisierten Builder ändern;
2. nur eine gemeinsame Kostenklassen-/Admission-Authority einführen;
3. AgentZero neu exportieren und Source-/Blob-Identität binden;
4. `FREE_ONLY_FALLBACK_CHAIN_RECEIPT/v1` auf exakt diesem regenerierten Source-Stand in autorisierter isolierter Ubuntu-Ausführung erzeugen;
5. erst danach FREE_ONLY-Sicherheitscredit für die Fallback-Kaskade vergeben.

Bis dahin:

- `FREE_ONLY_FALLBACK_CHAIN`: **NOT_PASS / SOURCE-BYPASS SUPPORTED**;
- GLM-Ausführungscredit im FREE_ONLY-Forschungsmodus: **0**;
- Whole EntityOS/Clay BASE: **nicht aus diesem Befund ableitbar**.

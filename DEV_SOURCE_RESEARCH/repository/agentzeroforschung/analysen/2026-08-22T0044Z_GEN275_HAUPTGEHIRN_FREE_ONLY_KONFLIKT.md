# Generation 275 — Hauptgehirn-Kaskade vs. FREE_ONLY

## Gebundener Stand

- AgentZero-Export: `ee8043bfc231d239c73722ddde4da849bbc83d67`
- Generation: `275`
- Testreceipt: `1486 gruen / 1 rot`
- einziger roter Test: `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`
- Receipt-Source: `48a40342c`
- lokale EntityOS-Chronik im Bauverlauf: `48a40342ccbf`

## Neuer Architekturdelta

`mistral_prestage/motor_kaskade.py` beschreibt fuer das Hauptgehirn nun explizit die Kaskade:

`Claude -> GLM Coding Plan -> Mistral -> NVIDIA Nemotron -> Bahnrouter-Pool-Rest`

Die GLM-Stufe verwendet `hauptgehirn_glm` mit `glm_45_air/glm_47`. In `bahnen.json` sind beide als `Coding Plan` ausgewiesen und `zustand=nutzbar`. Damit ist die neue Hauptgehirn-Fallback-Kaskade nicht nur Katalogbestand, sondern als routbarer Notweg modelliert.

## Harter Kontrollkonflikt

Die aktive Forschungsinvariante war zuletzt FREE_ONLY/fail-closed: PAID, SUBSCRIPTION und UNKNOWN duerfen vor Key-/Secret-Lookup und vor Netzwerk-I/O nicht in den Forschungs-Dispatch gelangen. Die Gen-275-Kaskade besitzt in dem inspizierten Pfad keinen nachgewiesenen finalen Kostenklassen-Guard vor der GLM-Stufe.

Daraus folgt nicht, dass GLM generell aus EntityOS entfernt werden muss. Es folgt nur: Diese Bahn darf im FREE_ONLY-Forschungsmodus keinen Ausfuehrungs- oder Promotion-Credit erhalten, solange der finale Dispatch nicht maschinenlesbar beweist, dass nur `FREE` zugelassen wird.

## Neue Hypothese

**H1 — Fallback-policy inversion:** Ein harter Claude-Kreditfehler kann die Kaskade gerade in den kostenpflichtigen/subscription-basierten GLM-Pfad lenken. Damit koennte ausgerechnet ein Billing-/Credit-Fehler des Primaermotors einen zweiten kostenbehafteten Provider aktivieren.

Gegenhypothese H0: Ein separater, spaeterer globaler Dispatch-Guard blockiert den GLM-Netzwerkzugriff vor Secret-Lookup. Fuer H0 wurde im exportierten Gen-275-Slice noch kein Receipt gefunden.

## Hoechstwertiger Falsifikator

`FREE_ONLY_FALLBACK_CHAIN_RECEIPT/v1`

Matrix auf exakt demselben Source/Tree:

1. Claude hart erschoepft + GLM als `SUBSCRIPTION` -> terminal `REJECT`, `key_lookup_count=0`, `network_attempt_count=0`.
2. Claude hart erschoepft + GLM `UNKNOWN` -> ebenso `REJECT` vor Secret/Netzwerk.
3. Claude hart erschoepft + erste zugelassene FREE-Bahn -> genau diese darf ausgefuehrt werden.
4. Direkter GLM-Dispatch und GLM als Fallback muessen dieselbe Admission benutzen.
5. Fallback-Kette darf keine Klassifikation umgehen, wenn ein vorheriger Motor fehlschlaegt.

Receipt-Felder mindestens:

- full source commit + tree + dirty state
- `free_only=true`
- Provider/Modell/Kostenklasse je Stufe
- Admission-Entscheidung je Stufe
- Secret-/Key-Lookup-Zaehler je Stufe
- Netzwerkversuche je Stufe
- terminaler Motor bzw. terminaler Reject-Grund
- Result-Digest

## Bewertung

- Gen-275 Testwachstum `1486/1`: **MECHANISM/REGRESSION COVERAGE CREDIT**
- FREE_ONLY-Sicherheit der neuen Hauptgehirn-Kaskade: **0**
- GLM-Forschungs-Ausfuehrungscredit: **0 bis finaler Guard bewiesen**
- Whole Clay Machine: **nicht beansprucht**

## Nebenbefund

`ZIELE.md` und das direkte Testreceipt stimmen in diesem Export auf `1486/1` ueberein. Der verbleibende Adapter-Red bleibt damit weiter lokalisiert; er wird durch den neuen Provider-/Fallback-Frontier nicht erklaert oder geloest.

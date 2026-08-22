# Gen 276 — Session-Switch-Identität und FREE_ONLY-Stabilität

## Gebundener Stand

- AgentZero Export: `91fea7d505385169521024b9d8fb6d95e7b5ef80`
- Generation: 276
- Test-Receipt: `1486 GREEN / 1 RED`
- einziger Red: `tests/test_runtime_adapters.py::test_claude_code_adapter_is_toolless_ephemeral_structured_and_env_isolated`
- Receipt Source short: `9f19db550`
- lokale EntityOS-Chronik bindet denselben Prefix an `9f19db5505f1...`

## Befund 1 — letzter Red bleibt trotz neuem Produkt-Source isoliert

Gen 275 stand bereits bei 1486/1, aber unter Source short `48a40342c`. Gen 276 steht erneut bei 1486/1 unter dem neuen Source short `9f19db550`. Der persistente Claude-Code-Adapter-Red überlebt damit mindestens einen realen Produkt-Source-Wechsel. Das erhöht die Evidenz dafür, dass der Fehler lokal an dieser Adapter-Boundary liegt statt an einer breiten Systeminstabilität.

Kein Fix-/Acceptance-Credit ohne Full Commit+Tree, Dirty-State, Suite-Digest und Executor/Environment in einem atomaren Receipt.

## Befund 2 — Gen275→Gen276 ändert als exportierten Produktcode nur terminal_gateway.py

Der Compare Gen275 `ee8043bf...` → Gen276 `91fea7d5...` zeigt als einzigen `agentZero/code/produkt/*`-Delta `terminal_gateway.py`.

Die aktuelle Chat-WebSocket-Steuerung löst beim `switch_platz` den Clerk-Subject + Zielplatz erneut über `identity.resolve(...)` auf und bindet danach `user_id` und `session_id` neu. Der Source kommentiert ausdrücklich den zuvor möglichen Fehler: nur den Platz zu ändern, während eine alte `session_id` weiterlebt, konnte den Verlauf einer falschen Sitzung desselben Menschen mit HTTP/WS-Erfolg anzeigen.

Das ist ein sinnvoller Mechanismus-Fix für Same-User-Cross-Session-Identität. Runtime-/Security-Credit bleibt aber 0, solange kein exakter Session-Switch-Receipt die Zustandsübergänge ausführt.

### Neuer Falsifikator: `SESSION_SWITCH_IDENTITY_RECEIPT/v1`

Für einen Clerk-Subject mit mindestens zwei kanonischen Slots:

1. Auth auf Slot A; binde `(clerk_sub, clerk_sid, user_id, slot=A, session_id=A)`.
2. Lade History A und speichere Digest.
3. Sende `switch_platz -> B`.
4. Verlange neues Ready mit exakt derselben Clerk-Identität, demselben `user_id`, aber `slot=B` und `session_id=B`.
5. Lade History B; sie darf keine A-only Turn-ID enthalten.
6. Switch B→A; History-Digest muss wieder A entsprechen.
7. Während `busy=true` muss Switch fail-closed bleiben.
8. Ungültiger/nicht kanonischer Slot muss fail-closed bleiben.
9. Reauth mit verändertem Clerk `sid` oder `sub` muss weiterhin abgelehnt werden.
10. Keine Cross-User-Auflösung darf je möglich sein.

Bindungen: full source commit+tree, dirty state, Clerk subject/session digest, slot, resolved EntityOS session_id, history turn-id set/digest, WS control sequence, result digest.

## Befund 3 — FREE_ONLY Hauptgehirn-Konflikt ist durch Gen276 NICHT behoben

Zwischen Gen275 und Gen276 wurden die exportierten Hauptgehirn-Dateien `bahnen.json` / `mistral_prestage/motor_kaskade.py` nicht als Produktdelta verändert. Der in Gen275 gebundene Pfad `Claude -> GLM Coding Plan -> Mistral -> Nemotron -> Pool-Rest` und der fehlende nachgewiesene finale FREE_ONLY-Cost-Class-Guard bleiben daher unverändert offene Kontrollblocker.

Provider-/Architect-/Main-Brain-Netzwerkausführung bleibt für ClayCode FREE_ONLY quarantänisiert, bis `FREE_ONLY_PROVIDER_ADMISSION_RECEIPT/v2` plus `FREE_ONLY_FALLBACK_CHAIN_RECEIPT/v1` executable-pass: `PAID | SUBSCRIPTION | UNKNOWN -> 0 secret/key lookups -> 0 network attempts -> terminal REJECT` an jedem direkten und Fallback-Hop.

## Priorität

1. FREE_ONLY final-dispatch/fallback-chain Gate — höchste Kontrollpriorität.
2. Exact-source Adapter-Zerlegung: TOOLLESS / EPHEMERAL / STRUCTURED_OUTPUT / ENV_ISOLATION.
3. `SESSION_SWITCH_IDENTITY_RECEIPT/v1` für den neuen Terminal-Gateway-Mechanismus.
4. `TEST_EXPORT_ATOMIC_RECEIPT/v1` weiter als Acceptance-Grundlage erzwingen.

## Credit

- Gen276 Regression/Coverage: Same-Family evidence only.
- Session-switch mechanism: SOURCE/METHOD CREDIT only.
- Session-switch executable security credit: 0.
- FREE_ONLY provider/main-brain execution credit: 0.
- Whole Clay Machine: NOT CLAIMED.

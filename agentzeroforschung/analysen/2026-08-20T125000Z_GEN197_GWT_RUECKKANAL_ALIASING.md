# Generation 197 — GWT-Rueckkanal: echter Lernkreis, aber Identitaets-Aliasing

## Gebundener Stand

- AgentZero-Export: `2b969fdfdc60f3830eb2d19218520670665967b1`
- Generation: 197
- Test-Receipt: `631 gruen / 1 rot`
- Receipt-Source-Prefix: `6b9048c7a`
- Bauverlauf bindet denselben Prefix an lokale EntityOS-Chronik `6b9048c7ab2b` (pipeline.py + wettbewerb.py).
- Persistenter Red: Claude-Code-Runtime-Adapter-Isolation.

## Positiver Architekturdelta

Der Global-Workspace-Wettbewerb besitzt jetzt einen persistenten Rueckkanal:

1. Kandidaten werden bewertet und maximal drei IDs ausgestrahlt.
2. `lernen()` bewertet eine ausgestrahlte ID als belohnt, wenn Zero diese ID in seiner rohen Antwort nennt.
3. Fuer seltene Fragewoerter wird `(merkmal, artikel_id) -> boost` in `gw_lernen` persistiert.
4. Spaetere Fragen lesen diese Boosts ueber `gelernte_boosts()` zurueck; `GEWICHT_LERNEN=0.20` kann die Rangfolge innerhalb der relevanten Menge verschieben.
5. Nichtbestaetigte Verbindungen sinken, alle Verbindungen verfallen (`VERFALL=0.98`).

Damit existiert erstmals ein geschlossener, zustandsbehafteter Broadcast->Antwort->spaetere-Auswahl-Kreis. Das ist mehr als reine GWT-Anzeige oder statische Competition.

## Neuer harter Gegenbefund: POSITIONAL_ID_ALIASING

Der Rueckkanal persistiert auf `artikel_id`. Fuer Korpusartikel ist das prinzipiell stabil. Fuer vier andere Workspace-Quellen werden IDs jedoch positionsabhaengig erzeugt:

- `gedaechtnis:{i}`
- `verlauf:{i}`
- `kollision:{i}`
- `lesart:{i}`

Diese Kennungen sind keine dauerhaften Identitaeten. Wenn sich Reihenfolge oder Inhalt zwischen zwei Turns verschiebt, kann z. B. `gedaechtnis:0` im naechsten Turn einen voellig anderen Memory-Eintrag bezeichnen. Ein gelernter Boost fuer `(wort, gedaechtnis:0)` kann dadurch auf den falschen Inhalt uebertragen werden.

Das ist **cross-turn semantic aliasing**: Das Lernsignal bindet an einen Slot statt an das gelernte Objekt.

### Konsequenz

GWT-Learning-Credit fuer Nicht-Korpus-Quellen = **0**, bis stabile Objektidentitaeten nachgewiesen sind. Fuer Korpusartikel bleibt Mechanismus-Credit moeglich, aber kein Outcome-Learning-PASS.

## Zweiter Gegenbefund: CITATION_PROXY_SELF_CONFIRMATION

Belohnung = Artikel-ID wird in Zeros Antwort genannt. Das ist besser als modellinterne Selbstzufriedenheit, aber noch kein externer Erfolg. Eine falsche oder nur scheinbar passende Antwort kann eine ausgestrahlte Quelle zitieren und damit genau diese Quelle staerken. Auswahl und Reward sind daher nicht vollstaendig unabhaengig.

Die bestehende harte `relevanz > 0`-Huerde begrenzt den Schaden, beseitigt aber nicht das Problem innerhalb der relevanten Kandidatenmenge.

## Hoechstwertige Falsifikatoren

### A. ID-Stabilitaet

Zwei identische Fragen, dazwischen nur die Reihenfolge von `durable_memory` permutieren.

Erwartung nach korrektem Fix:
- derselbe semantische Memory-Eintrag behaelt dieselbe stabile ID;
- sein Boost folgt dem Objekt, nicht dem Index;
- ein anderer Eintrag, der neu Slot 0 belegt, erbt keinen Boost.

### B. Citation-Proxy

Paar aus:
- A = korrekter, relevanter Beleg,
- B = lexikalisch relevanter, plausibler Distraktor.

Beide werden ausgestrahlt. Dann messen:
- welche IDs Zero nennt,
- Antwortkorrektheit extern/regelbasiert,
- Boost-Delta fuer A und B,
- spaetere Rangfolge.

Ein falscher, aber zitierter B darf nicht denselben starken Lerncredit wie ein korrekt tragender A erhalten.

## Minimaler Architekturfix

1. Nicht-Korpus-Kandidaten bekommen content-/provenance-stabile IDs, z. B. `source_kind + canonical object id` oder einen digest aus unveraenderlicher Provenienz; keine Positionsnummer als Lernschluessel.
2. `gw_lernen` speichert zusaetzlich `source_kind` und optional `source_digest` und verwirft Boosts bei Identitaetsmismatch.
3. Citation nur als schwaches lokales Signal behandeln; staerkerer Credit kommt aus unabhaengiger Verifikation (Outcome/Effect/Reingest/Task-Receipt), sofern verfuegbar.
4. Lernwrites bleiben bei Messreihen deaktivierbar (`record_via_turnlifecycle=False`) — diese bestehende Grenze beibehalten.

## Evidenzstatus

- GWT persistent feedback mechanism: **PRESENT**
- Closed-loop statefulness: **PRESENT**
- Stable learning identity across all workspace sources: **FAIL / NOT PROVEN**
- Outcome-grounded reinforcement: **NOT PROVEN**
- Whole GWT learning credit: **BLOCKED**

Der naechste Informationsgewinn ist groesser durch die zwei obigen Falsifikatoren als durch weitere Gewichtstuning-Laeufe.

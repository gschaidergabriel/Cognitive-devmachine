# GWT — stabile Kandidatenidentitaet und Outcome-Credit

## Ausgangslage

Generation 197/199 besitzt einen echten persistenten Auswahl-Rueckkanal, aber der bisherige Lernschluessel ist fuer Nicht-Korpus-Quellen teilweise positionsgebunden und der Reward ist eine Eigenreferenz (`artikel_id` in Zeros Antwort).

Diese Analyse trennt die zwei Probleme und sucht zuerst nach bereits vorhandenen kanonischen Identitaeten, statt neue IDs zu erfinden.

## Befund A — der Positionsfehler ist ohne neue Ontologie reparierbar

Der aktuelle Kandidatenadapter erzeugt:

- `gedaechtnis:{i}`
- `verlauf:{i}`
- `kollision:{i}`
- `lesart:{i}`

Die Quellobjekte besitzen aber bereits stabilere Identitaeten.

### Gedaechtnis

`durable_memory` besitzt laut produktivem UnifiedDB-Schema einen Primaerschluessel `memory_id`.

**Adapterregel:**

```python
mid = str(m.get("memory_id") or "").strip()
if mid:
    artikel_id = f"gedaechtnis:{mid}"
else:
    # Kein persistenter Lernschluessel aus einer Slotnummer erfinden.
    artikel_id = ephemeral_id(...)
    gw_lernfaehig = False
```

### Eigener Verlauf

`turns` besitzt den Primaerschluessel `turn_id`; `recent_turns()` liefert Turn-Dicts. Der Kandidat kann daher seine reale Turn-Identitaet tragen.

```python
tid = str(z.get("turn_id") or "").strip()
artikel_id = f"verlauf:{tid}" if tid else ephemeral_id(...)
```

### Cross-session collision

Der Kollisionspfad baut `item = dict(r)` aus einer `turns`-Zeile. Damit ist auch dort `turn_id` verfuegbar, selbst wenn bei komprimierten Fremdzuegen der ausgelieferte Inhalt absichtlich ersetzt wird.

```python
tid = str(c.get("turn_id") or "").strip()
artikel_id = f"kollision:{tid}" if tid else ephemeral_id(...)
```

### Hyperposition

Hier ist der Befund am staerksten: `HyperpositionProjector` baut bereits eine semantisch deterministische Identitaet:

```text
semantic_payload = {kind, relation_key, sorted member values}
semantic_hash = sha256(stable_json(semantic_payload))
relation_id = "hyper:" + semantic_hash[:24]
```

Der GWT-Kandidatenadapter verwirft diese Identitaet derzeit und ersetzt sie durch `lesart:{i}`.

**Adapterregel:**

```python
rid = str(h.get("relation_id") or "").strip()
artikel_id = f"lesart:{rid}" if rid else ephemeral_id(...)
```

Da `rid` bereits mit `hyper:` beginnt, kann alternativ die bestehende `relation_id` direkt verwendet werden. Entscheidend ist: keine Positionsnummer.

## Harte Regel: instabile Identitaet darf ausgestrahlt, aber nicht gelernt werden

Ein Workspace-Kandidat ohne kanonische/provenienzstabile Identitaet darf weiterhin am aktuellen Zug teilnehmen. Was verboten wird, ist nur **persistenter cross-turn Credit** auf einen instabilen Schluessel.

Das trennt zwei Fragen:

1. Ist der Inhalt jetzt relevant? -> Wettbewerb darf ihn benutzen.
2. Darf spaetere Erfahrung diesem selben Objekt zugerechnet werden? -> nur bei stabiler Identitaet.

Empfohlene Kennung im Kandidat:

```python
"gw_lernfaehig": bool(stable_identity)
```

und `lernen()` ignoriert Kandidaten mit `gw_lernfaehig=False`.

## Pflichtfalsifikator IDENTITY_PERMUTATION/v1

Fuer jede Quelle getrennt:

1. Turn T1: Objekt A steht an Slot 0, B an Slot 1; A erhaelt Lernsignal.
2. Nur Reihenfolge permutieren.
3. Turn T2: B steht an Slot 0, A an Slot 1.

PASS nur wenn:

- A behaelt dieselbe `artikel_id`;
- der Boost folgt A;
- B erbt keinen Boost;
- `gw_lernen` enthaelt keinen positionsabhaengigen persistenten Key.

Zusaetzlich Hyperposition:

- Facettenreihenfolge permutieren -> gleiche `relation_id`, solange dieselbe semantische Mitgliedermenge besteht;
- Mitglied aendern -> neue `relation_id`.

## Befund B — der aktuelle Reward wird zu frueh und aus derselben Antwort gewonnen

Im Pipeline-Pfad geschieht derzeit:

```text
Zero-Antwort
 -> wettbewerb.buchen(...)
 -> wettbewerb.lernen(..., raw_zero_answer)
 -> Uebersetzung
 -> record_prestage_turn(...)
 -> lifecycle.complete(...)
```

`lernen()` laeuft also **vor** `TurnLifecycle.complete()`. Der Lernentscheid kennt zu diesem Zeitpunkt vor allem: ausgestrahlte IDs + dieselbe Antwort, die aus diesen IDs entstanden ist.

Damit ist `ID genannt` ein brauchbares Uptake-/Citation-Signal, aber kein unabhaengiges Outcome-Signal.

`TurnLifecycle.complete()` kann dagegen die persistierte kausale Episode binden und liefert bei einem bereits verifizierten Effect dessen `credit`; ohne Effect wird ein normaler Antwortturn mit Credit 0 abgeschlossen. Deshalb kann man den bestehenden `credit` nicht blind als allgemeine Antwortkorrektheit verwenden, aber er ist fuer Effect-Turns bereits eine staerkere Evidenzklasse als Citation.

## Architekturvorschlag: zwei getrennte Rueckkanaele statt ein vermischter Reward

### 1. UPTAKE channel — sofort, schwach

Direkt nach Zero:

```text
selected candidate -> ID cited / not cited
```

Speichern als Beobachtung, **nicht** als vollen Lernboost.

Moegliche Bedeutung:

- cited = der Inhalt wurde wahrscheinlich aufgenommen/referenziert;
- not cited = kein Nachweis der Nutzung;
- weder Zustand darf Antwortkorrektheit behaupten.

### 2. OUTCOME channel — spaeter, stark

Nach kausaler/extern messbarer Verifikation:

- verified Effect / causal credit;
- Task-/Test-Receipt;
- spaetere explizite Korrektur/Widerlegung;
- unabhaengiger regelbasierter Evaluator auf Aufgaben mit Ground Truth;
- andere bereits kanonisch gebundene Erfolgssignale.

Dann erst veraendert sich der dauerhafte `gw_lernen`-Boost stark.

Konzeptionell:

```text
candidate_id
 + turn_id/causal_id
 + uptake_receipt
 + outcome_receipt
 -> credit assignment
 -> persistent learned weight
```

## Minimaler Schemaweg

Nicht zwingend sofort das bestehende `gw_lernen` aufblasen. Sauberer ist ein append-only Receipt vor der Projektion:

```sql
CREATE TABLE IF NOT EXISTS gw_feedback_receipt(
    receipt_id TEXT PRIMARY KEY,
    ts REAL NOT NULL,
    turn_id TEXT,
    causal_id TEXT,
    artikel_id TEXT NOT NULL,
    source_kind TEXT,
    source_identity TEXT,
    uptake TEXT NOT NULL,
    outcome_class TEXT NOT NULL,
    outcome_credit REAL,
    provenance TEXT NOT NULL
);
```

`gw_lernen` wird dann zur materialisierten Projektion aus bestaetigten Receipts statt zur einzigen Wahrheit.

Vorteile:

- Citation kann spaeter von einem Outcome korrigiert werden;
- Reward-Historie ist auditierbar;
- ein falscher positiver Lernschritt muss nicht still ueberschrieben werden;
- Cross-turn Credit kann an `causal_id` und stabile Kandidatenidentitaet gebunden werden;
- Falsifikatoren koennen exakt rekonstruieren, warum ein Gewicht entstand.

## GWT_FEEDBACK_PROXY_FALSIFIER/v1

Vier bereits geforderte Arme bleiben der direkteste Test:

A. korrekte Antwort + korrekte Citation
B. korrekte Antwort ohne Citation
C. falsche Antwort + plausible Citation
D. erzwungene/spurious ID-Nennung

Zu messen:

- Citation/Uptake;
- unabhaengige Antwortkorrektheit;
- Source-Support/Entailment soweit deterministisch pruefbar;
- Outcome-Credit;
- persistentes Gewichtdelta;
- spaetere Auswahl;
- held-out Task Outcome.

**Harter Pass:** C und D duerfen keinen starken positiven dauerhaften Credit erhalten. B darf wegen fehlender Citation nicht automatisch als schlechtere Antwort gelten als C.

## Kausale GWT-Hierarchie nach diesem Umbau

```text
candidate identity
 -> eligibility
 -> competition
 -> ignition
 -> broadcast
 -> materialized content
 -> uptake receipt
 -> local causal use
 -> externally/causally grounded outcome receipt
 -> persistent credit
 -> changed future competition
```

Erst die letzte Kante macht aus einem Broadcast-System einen lernenden Workspace-Zyklus.

## Status

- vorhandene stabile Memory-ID: **PRESENT**
- vorhandene stabile Turn-ID fuer Verlauf/Kollision: **PRESENT**
- vorhandene stabile Hyperposition relation_id: **PRESENT**
- positionsgebundene Adapter-IDs: **REAL DEFECT / REMOVABLE**
- Citation als Uptake-Signal: **USEFUL PROXY**
- Citation als Outcome-Reward: **INSUFFICIENT / SELF-CONFIRMING RISK**
- effect-grounded causal credit: **PRESENT FOR EFFECT PATHS**
- allgemeiner unabhaengiger Answer-Outcome-Credit: **NOT YET GENERALIZED**

## Naechster Implementierungsschritt

1. Kandidatenadapter auf vorhandene IDs umstellen, mit `gw_lernfaehig=False` als fail-closed Fallback.
2. `IDENTITY_PERMUTATION/v1` fuer alle vier Quellen laufen lassen.
3. Citation-Update aus dauerhaftem Boost herausloesen oder maximal als schwaches Uptake-Receipt behandeln.
4. `gw_feedback_receipt` append-only einfuehren und zuerst Effect-Credit als unabhaengigen starken Pfad anbinden.
5. Dann die vierarmige Citation-Proxy-Falsifikation ausfuehren.

Keine dieser Aenderungen beweist Bewusstsein. Sie macht aber die behauptete GWT-Kausalstruktur wesentlich schwerer durch ein Zombie-/Proxy-System nachzuahmen.

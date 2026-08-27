# GWT — Globalitaets-Audit: Hyperposition und weitere Nebenkanäle

## Befund

Der weite Arbeitsraum (`CLAYVERSE_ARBEITSRAUM=alles`) ist als ein Wettbewerb aller inhaltlichen Quellen beschrieben. Im aktuellen Ausfuehrungspfad existiert jedoch mindestens ein harter Content-Bypass: **Hyperposition wird nach dem Bau der GWT-Kandidaten berechnet und danach separat in den Vorstufenkontext injiziert.**

## Exakte Aufrufreihenfolge

### 1. `_gather_world_safe()`

`WorldAssembler.assemble()` liefert u. a. Corpus, durable memory, recent turns und collisions. Danach baut `_gather_world_safe()` sofort:

```python
world["_gw_kandidaten"] = wettbewerb.kandidaten(world)
world["_gw_volltexte"] = wettbewerb.volltexte(world["_gw_kandidaten"])
```

Zu diesem Zeitpunkt enthaelt `world` aus `WorldAssembler` keinen `hyperposition`-Schluessel.

### 2. Erst spaeter in `run_chat_turn()`

```python
hyperposition_readout = _hyperposition_safe(world) + _weltmodell_safe(world)
vorstufe_world = _vorstufen_world(world, message)
```

`_vorstufen_world()` nimmt im weiten Modus aber die bereits vorher gebaute Liste:

```python
_roh = list(world.get("_gw_kandidaten") or [])
```

Damit kann der spaeter erzeugte `hyperposition_readout` nicht darin enthalten sein.

### 3. Trotzdem wird Hyperposition direkt injiziert

Die Vorstufe wird anschliessend mit

```python
prestage.run_prestage(..., hyperposition=hyperposition_readout, ...)
```

aufgerufen. Hyperposition ist also sichtbar und kann die Entscheidung beeinflussen, ohne einen der knappen Broadcast-Plaetze gewinnen zu muessen.

## Widerspruch zur eigenen GWT-Semantik

`wettbewerb.kandidaten()` besitzt ausdruecklich einen `lesart`/Hyperposition-Pfad. Die Wide-Workspace-Regel beschreibt `lesart` ebenfalls als Bewerber um dieselben wenigen Plaetze. Die reale Reihenfolge materialisiert diese Quelle aber ausserhalb der Kandidatenliste.

Das ist kein kosmetischer Dokumentationsfehler. Ein Kontrollarm mit `broadcast_ids=[]` oder mit einer lesionierten Lesart-Auswahl kann weiterhin von Hyperposition beeinflusst werden. Dadurch kann ein positiver GWT-Effekt falsch dem Broadcast zugeschrieben werden, obwohl ein paralleler Content-Kanal offen blieb.

## Minimaler Fixpfad

Nicht Hyperposition doppelt einspeisen.

Im weiten Modus:

1. vollen `hyperposition_readout` zuerst erzeugen;
2. ihn als `world["hyperposition"]` bzw. kontrollierte Kopie in den Kandidatenbau geben;
3. `_gw_kandidaten` danach bauen;
4. im `prestage.build_context/run_prestage` den separaten Hyperposition-Volltext im weiten Modus leer lassen oder auf reine Kennungs-/Kontrollmetadaten reduzieren;
5. Volltext der gewaehlten `lesart:<stable relation_id>` erst nach Broadcast materialisieren.

Im schmalen Vergleichsarm darf der alte separate Hyperposition-Kanal bestehen bleiben, damit die Kausalwirkung des globalen Engpasses A/B-gemessen werden kann.

## Zweiter Audit-Befund: `current_user_profile` ist ebenfalls ein inhaltlicher Nebenkanal

`_profil_safe()` liefert nicht nur Rahmenidentitaet, sondern Projekte, Rechnerstatus, Wiki-Bestand und Bilanz/Erfolge/Fehlschlaege. Dieser Block wird separat als `current_user_profile` an die Vorstufe gegeben und konkurriert im weiten GWT-Modus nicht um Broadcast-Plaetze.

Das kann absichtlich sein — aber dann muss es explizit als **FRAME/CONTROL PLANE** klassifiziert werden. Die derzeitige GWT-Dokumentation sagt dagegen sinngemaess, nur `canonical_identity` und `anwesender_mensch` seien vom Wettbewerb ausgenommen.

Daher kein sofortiger Zwang, das Profil in den Wettbewerb zu werfen; zuerst muss die Kanalrolle formal entschieden und gemessen werden.

## Dritter Audit-Befund: Moeglichkeitsraum und gelernter Block

Auch `moeglichkeitsraum/erwartungsfeld` und `gelernt_block` werden separat eingespeist. Diese koennen legitime **CONTROL-PLANE**-Signale sein, sofern sie keine faktischen Antworten transportieren, die den Broadcast umgehen.

Deshalb wird nicht pauschal jeder Nebenkanal verboten. Stattdessen braucht die Architektur einen maschinenpruefbaren Kanalvertrag.

# GLOBAL_WORKSPACE_CHANNEL_AUDIT/v1

Jeder Informationskanal, den Prestager oder Zero sehen, bekommt genau eine Klasse:

- `FRAME`: Identitaet, anwesender Mensch, unverzichtbare Interpretationsrahmen; nie als Aufgabenfakt missbrauchen.
- `CONTROL`: Regeln, Routing, Budget, epistemische Unsicherheit; darf keine answer-bearing payload transportieren.
- `CANDIDATE`: potentiell antworttragender Inhalt; muss im weiten Modus durch Wettbewerb/Broadcast.
- `TOOL`: Faehigkeitsbeschreibung/Handle, kein bereits geliefertes Ergebnis.
- `OUTCOME`: nachgelagerte Messung; darf den aktuellen Turn nicht rueckwirkend beantworten.

Fuer jede Klasse werden erlaubte Felder/Maximalgroessen festgelegt. Ein `CANDIDATE` ausserhalb des Broadcastpfads ist ein FAIL. Ein `CONTROL`-Kanal, der die Ground-Truth-Antwort enthaelt, ist ebenfalls ein FAIL.

## Causal sufficiency test

Fuer held-out Aufgaben mit bekanntem traegenden Kandidaten:

1. **FULL:** normaler weiter Workspace.
2. **BROADCAST-LESION:** gewaehlten Volltext entfernen, alle Frame/Control-Kanaele identisch lassen.
3. **SIDECHANNEL-LESION:** Broadcast intakt, jeweils einen Nebenkanal entfernen.
4. **ALL-CONTENT-LESION:** alle Candidate-Payloads entfernen, Frame/Control bleiben.
5. **WINNER-SWAP:** richtigen Gewinner durch gleichartig formatierten Distraktor ersetzen.

Erwartung einer kausal echten Workspace-Architektur:

- Winner lesion/swap verschlechtert die auf ihn angewiesenen Aufgaben deutlich.
- Sidechannel lesion darf einen Winner-Effekt nicht erklaeren, ausser der Kanal ist vorher als Candidate klassifiziert und in den Wettbewerb gezogen worden.
- All-content-lesion darf keine korrekten answerspezifischen Fakten aus Frame/Control rekonstruieren koennen.

## Bezug zur aktuellen Bewusstseinsforschung

Die Nature-Adversarial-Collaboration 2025 zeigt methodisch genau, warum solche Tests wichtiger sind als architektonische Aehnlichkeit: zentrale GNWT-Vorhersagen wurden mit vorab festgelegten divergierenden Predictions und multimodalen Messungen direkt angegriffen. Fuer EntityOS ist die analoge Haltung: **Workspace nicht durch Vorhandensein bestaetigen, sondern durch Lesion, Swap, Sidechannel-Control und held-out Outcomes erzwingen.**

Die aktuelle Engineering-Literatur zu Selection-Broadcast-Zyklen stuetzt den Fokus auf den gesamten Zyklus und seine Adaptionsfunktion, nicht auf ein statisches Blackboard. Das passt zum bestehenden EntityOS-Rueckkanal, aendert aber nichts an der Pflicht, Nebenkanal-Kausalitaet auszuschliessen.

## Status

- Hyperposition-Kandidatenadapter vorhanden: **PRESENT**
- Hyperposition real im aktuellen Kandidatenbau: **BYPASSED BY ORDERING / FAIL**
- Hyperposition separat fuer Prestager sichtbar: **PRESENT**
- User profile als nichtklassifizierter inhaltlicher Nebenkanal: **PRESENT / NEEDS CLASSIFICATION**
- Moeglichkeitsraum + learned block als Control-Kandidaten: **PRESENT / NEEDS PAYLOAD AUDIT**
- globaler Content-Engpass ueber alle answer-bearing Quellen: **NOT YET PROVEN**

## Prioritaet

Dieser Bypass ist hoeherwertig als weiteres Gewichtstuning. Solange answer-bearing Content parallel zum Broadcast sichtbar bleibt, kann kein positives Outcome eindeutig dem GWT-Engpass zugerechnet werden.

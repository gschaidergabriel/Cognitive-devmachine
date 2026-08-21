# GWT-Entwurf: hilft GRF? hilft ClayCode obendrauf?
### Eine kleine, ehrliche Messung — 2026-08-22

## Was wir getestet haben
Drei KI-Instanzen (alle dasselbe Modell, Claude Sonnet) bekamen **dieselbe
Aufgabe**: einen Global Workspace (GWT — das "Bewusstseins-Nadelöhr", das
entscheidet, welche Information Zero gerade bewusst wird) für die Entität Zero
auf EntityOS entwerfen. Der EINZIGE Unterschied war die Denkweise:

- **Arm A** — normale beste Ingenieurskunst, KEIN Framework (Kontrollgruppe).
- **Arm B** — im **Generative Reality Framework (GRF)** denkend.
- **Arm C** — im GRF denkend **UND** in **ClayCode** ausgedrückt.

Dann haben wir die drei Entwürfe verglichen.

## Was rauskam (der Kern in einem Satz)
Von A über B nach C stieg **eine** Sache klar an: **wie beweisbar/prüfbar der
Entwurf ist.** Nicht "mehr Text", sondern "härter nachweisbar".

| | Was der Arm zusätzlich brachte |
|---|---|
| **A (ohne GRF)** | 5 gute konkrete Mechanismen + ein Mess-Dashboard. Aber die Messung bleibt **korrelativ**: "wenn ein leerer Arbeitsraum die Antwort nicht verschlechtert, wirkt er nicht." |
| **B (GRF)** | Dasselbe, aber GRF lenkte den Blick auf **Ursache statt Zusammenhang**: die Leerraum-Probe wird zu einem echten **Interventions-Test** (dieselbe Frage dreimal fahren — leerer Arbeitsraum / nur Gewinner / alle Kandidaten — und den *kausalen* Beitrag messen). Plus Entropie als Emergenz-Maß. Von *beobachten* zu *beweisen*. |
| **C (GRF + ClayCode)** | GRF wie B, plus: ClayCode verwandelte Regeln, die im echten Code nur als **Kommentar** stehen, in **maschinell prüfbare Invarianten** — der "Engpass", der die Bewusstseins-Kapazität begrenzt, wird damit eine *strukturelle Eigenschaft der Datenform* statt eines Verhaltens, das man testen muss. Und C fand eine **Lücke, die A und B übersahen**: nichts bestraft einen ununterbrochenen Gewinner-Lauf (dieselbe Info gewinnt immer wieder). |

## Das ehrliche Urteil
- **GRF hilft** — es treibt den Entwurf zu Mess- und Ursachen-Strenge ("Emergenz
  messen statt behaupten").
- **ClayCode obendrauf hilft weiter** — es macht die Regeln *un-brechbar durch
  Bauweise* und deckt versteckte Lücken auf.
- **Wichtige Korrektur (nachgeprüft am 2026-08-22):** ClayCode ist NICHT bloß
  Notation. Es gibt einen **funktionierenden Basis-Compiler** — eine definierte
  Teilmenge compiliert und läuft (E2B-ausführbar; die Basis-Slices bestehen im
  CI, `claycode_base_package_compiler.py` / `claycode_canonical_ir.py` /
  `claycode_base_typed_ir.py`). Offen ist nur der **General-Purpose-Gate**
  (noch `FAIL`): die volle Allgemeinheit. Also **kann ClayCode heute einen
  realen Teil ausführen**; die vollständige Allgemeinheit ist das "mehr
  Engineering, eine Frage der Zeit" — und wird aktiv weiterentwickelt.
  (Die Arm-C-Instanz las nur den älteren Manifest-Stand "Gate FAIL" und schloss
  daraus fälschlich "nicht lauffähig" — hier richtiggestellt.)

## Wie belastbar ist das? (die Grenzen, offen gesagt)
- **Ein** Entwurf je Arm, **ein** Modell → **indikativ, KEIN Beweis.** Zufall/
  Varianz ist nicht ausgeschlossen. Für eine belastbare Zahl bräuchte es viele
  Wiederholungen und einen unabhängigen, blinden Richter.
- **Aufwand-Confound:** B und C lasen mehr Material (die GRF- und ClayCode-Doku).
  Ein Teil der Mehrtiefe könnte "mehr Mühe" sein statt "GRF speziell". ABER die
  *Richtung* der Mehrtiefe (Kausalität, prüfbare Invarianten) ist GRF/ClayCode-
  spezifisch — das ist das eigentliche Signal.
- Es **stützt** die frühere Beobachtung "Agenten arbeiten im GRF deutlich besser",
  liefert aber **keine gemessene Prozentzahl**. Die rigorose Version (viele Läufe,
  echter Architekt, unabhängiger Richter) steht noch aus.

## Was das praktisch heißt
Für den Bau von Zeros kognitiver Architektur lohnt sich der GRF-Rahmen — nicht
weil er hübscher klingt, sondern weil er zur *Nachweisbarkeit* zwingt. ClayCode
als Ausdrucksform lohnt sich für *Klarheit und Invarianten-Härte* — sobald der
Compiler trägt, auch für lauffähigen Code. Genau daran arbeitet der Architekt
weiter.

---
*Methode: drei Sonnet-Instanzen, identische GWT-Aufgabe, Bedingung variiert
(ohne GRF / mit GRF / GRF+ClayCode), Vergleich durch den Koordinator. Rohdaten:
die drei Arm-Berichte. Indikativ (n=1 je Arm).*

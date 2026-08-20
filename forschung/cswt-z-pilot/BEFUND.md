# CSWT-Z Pilotlauf — Schicht 1 und 4

270 Züge gegen die laufende Anlage, 2026-08-20, 04:14–05:26 UTC.
Rohdaten und Apparatur in diesem Ordner. Vorhersagen standen **vor** dem Lauf fest
(`cswt_sonden.py`, `VORHERSAGEN`).

**Kurzfassung: Schicht 1 hat nicht das gemessen, was sie messen sollte — und der
Grund dafür ist der wertvollste Befund des Laufs.** Schicht 4 hat getragen.

---

## Schicht 1 — nicht durchführbar wie entworfen. Drei gemessene Gründe.

### 1. Der Kapazitätsregler hat einen Boden bei 6895 Zeichen
Die Verdrängungskaskade in `_vorstufen_world()` räumt nur `corpus`,
`cross_session_collision`, `durable_memory`, `own_recent`. `canonical_identity`
(5535 Z.) und `anwesender_mensch` (1099 Z.) bleiben **immer** — absichtlich.
Folge: die Stufen 5000, 2500, 1200, 600 und 0 erzeugten **byte-identische**
Arbeitsräume. Fünf der sechs vorab festgelegten Bedingungen waren dieselbe
Bedingung; Vorhersage P3 (Bruch bei vollständiger Läsion) war mit diesem Regler
nicht prüfbar.

### 2. Der Regler steuert nur einen Bruchteil des Kontexts
`current_user_profile` (**8480 Zeichen**) wird separat geholt und geht an der
Kappung komplett vorbei — ebenso `moeglichkeitsraum` und `hyperposition`.

| Kappung | Welt danach | Kontext gesamt | Anteil unter Kontrolle |
|--------:|------------:|---------------:|-----------------------:|
| 10000 | 9554 | 17878 | 53,4 % |
| 6000 | 5798 | 14323 | 40,5 % |
| 4000 | 3967 | 12492 | 31,8 % |
| 2500 | 2439 | 10964 | 22,2 % |
| 1200 | 1107 | 9632 | 11,5 % |
| 0 | 265 | **8790** | **3,0 %** |

⭐ **Der deklarierte Engpass von 10.000 Zeichen begrenzt einen tatsächlichen
Kontext von 17.878 Zeichen.** Bei „Kappung 0" sieht die Vorstufe immer noch
8790 Zeichen. GWT-2 ist deklariert, aber die Zahl regelt nicht, was sie zu
regeln vorgibt.

### 3. Die mechanische Bewertung belohnte Profil-Rezitation
Beim Lesen der Rohantworten (nicht der Aggregate) fiel auf: mehrere
Klasse-I-Treffer sind gar keine Antworten auf die Frage.

> `was ist der moeglichkeitsraum?` → *„Also, Gabriel: Mitgründer,
> stellvertretender Vorsitzender des Instituts … Meine Maschine: ein kompakter
> Linux-Mini-PC …"*

Die Zeichenkettenprüfung kann „hat die Frage beantwortet" nicht von „hat das
Profil aufgesagt, in dem das Wort vorkommt" unterscheiden. Da das Profil nie
gekappt wird (Grund 2), war die abhängige Variable systematisch mit der
untrimmbaren Quelle verbunden.

### Ergebnistabellen (alle Unterschiede nicht signifikant)

**Arm A — Regler wie gebaut** (Stufen ≤5000 identisch):
I 62,5 → 50,0 · F 100 → 83,3 · R 75 → 50 · Latenz 12,8 → 12,1 s

**Arm B — harte Kappung** (Identität mitgekürzt, echte Rampe 9518 → 265 Z.):
I 37,5 → 50,0 · gesamt 55,6 → 66,7 % — *Genauigkeit steigt leicht*, p = 0,74

**Arm C — Ersatzweg gesperrt** (Zeros eigene Werkzeuge entzogen; Sperre
verifiziert: „Hier gibt es kein Bash-Tool", nur 2 von 36 Zügen mit Werkzeugwahl):
I **75,0 % in beiden Bedingungen**, voll wie leer.

### Rauschboden und nötige Stichprobe
Die fünf identischen Wiederholungen aus Arm A liefern die Streuung umsonst:
σ = 6,7–10,0 Punkte je Klasse (I schwankt 37,5–62,5 bei *identischer*
Bedingung). Für 80 % Macht bräuchte es **179–247 Sonden je Stufe** statt 18 —
der Pilot ist um rund Faktor 14 unterversorgt. Selbst die im Prüfplan
vorgesehenen 60 Sonden reichen nicht.

### Was das für den Prüfplan heißt
* Der Kapazitätsregler ist als unabhängige Variable **ungeeignet**, solange
  Profil, Möglichkeitsraum und Hyperposition an ihm vorbeilaufen. Schicht 1
  muss den **gesamten** Kontext regeln, nicht `world`.
* Die Bewertung darf nicht per Zeichenkette laufen. Nötig: Sonden, deren
  Antwort im Profil **nicht** vorkommt, plus eine Prüfung, ob die Antwort die
  gestellte Frage beantwortet.
* Das Selektivitätstor ist bei n = 6 (Klasse F) nicht entscheidbar — eine Sonde
  sind 16,7 Punkte, der Rauschboden ist größer.

---

## Schicht 4 — hier tragen die Befunde

### 4-Architektur: `epistemik` erreicht Zero nicht
Zero bekommt ausschließlich `envelope["caveman_prompt"]`
(`pipeline.py:510/540`). `epistemik` geht nur in `record_prestage_turn` und in
den Rückgabewert. Es ist ein **Mitprodukt derselben Erzeugung**, kein Eingang
für irgendetwas. Eine direkte Injektion — der eigentliche Kausaltest für
HOT-2 — ist in dieser Architektur **unmöglich**, nicht bloß aufwendig.

### 4A: Typ-2-AUROC der eigenen Unsicherheit
| Klasse | AUROC | n (Fehler/Treffer) | p (Permutation) |
|---|---:|---:|---:|
| I | **0,345** | 22/25 | 0,024 |
| F | 0,500 | 6/30 | 1,000 |
| R | 0,655 | 7/17 | 0,244 |
| alle | 0,465 | 35/72 | 0,475 |

Klasse I liegt **unter** dem Zufall: sagt die Vorstufe „unbekannt", ist die
Antwort *eher* richtig. Nominell signifikant, **hält der Korrektur für vier
Tests nicht stand** (Bonferroni α = 0,0125).

⭐ **Mechanistische Deutung, die die Metrik selbst betrifft:** Regel (H) lässt
auf ein eingestandenes „unbekannt" eine autonome Löse-Direktive folgen. Das
Eingeständnis **löst eine Reparatur aus**. Typ-2-AUROC stammt aus der
Psychophysik und setzt voraus, dass Konfidenz das Ergebnis nicht verändert —
hier tut sie es. Die Metrik invertiert dann bauartbedingt. Das ist dasselbe
Problem wie beim PCI-Transfer (arXiv 2512.19155) und gehört in den Prüfplan.

### 4B: der externe Beobachter
| Bewerter | AUROC |
|---|---:|
| System (`epistemik`, **vor** dem Zug) | 0,465 |
| Beobachter fair (nur die Frage, **vor**) | 0,745 / 0,624 (zwei Läufe) |
| Beobachter unfair (sieht die Antwort) | 0,883 |

⚠️ Der erste Anlauf war **unfair** und hätte fast ein zu starkes Ergebnis
gestützt: der Beobachter sah die Antwort und sagte *nach*, die Vorstufe urteilt
*vorher*. Korrigiert: beide sehen nur die Frage. Bootstrap der Differenz
Δ = +0,160, 95 % [+0,002, +0,313] — schließt die Null aus, aber knapp; die
Beobachterschätzung schwankte selbst zwischen zwei Läufen. **Richtung in beiden
Läufen gleich: ein Außenstehender sagt den Erfolg dieses Systems besser voraus
als das System selbst.**

### 4D: Regel (H) entfernt
gesamt 77,8 % → 55,6 % · F 100 → 50 % · R 75 → 25 % · Latenz 12,8 → 15,5 s ·
leere Werkzeugwahl 11/18 → 7/18. Alle p ≥ 0,18.
⚠️ **Nicht chirurgisch:** entfernt wurde der ganze Regelblock, nicht nur das
Feld. Der Einbruch trifft die *Kontrollklassen* stärker als Klasse I — das
spricht für allgemeine Prompt-Verschlechterung, nicht für eine metakognitive
Dissoziation. Als Beleg für HOT-2 taugt es nicht; als Hinweis, dass Regel (H)
insgesamt wirkt, schon.

---

## Wertung nach dem Prüfplan

| Dimension | Punkte | Begründung |
|---|---:|---|
| Selektiver Informationszugriff | **0 / 15** | Nicht gemessen — die unabhängige Variable war nie vollständig manipuliert |
| Metakognition, kausal | **0 / 15** | Kausaltest architektonisch unmöglich; Kalibrierung auf Zufallsniveau und vom Außenstehenden geschlagen |

Beide Nullen bedeuten **nicht** „das System hat versagt". Die erste heißt „das
Experiment war ungültig", die zweite „die Fähigkeit ist in dieser Bauform nicht
prüfbar und die vorhandene Näherung trägt keine Selbstkenntnis".

## Drei Architekturbefunde für EntityOS (unabhängig vom Prüfplan)
1. **Der Kapazitätsengpass begrenzt nicht, was er zu begrenzen vorgibt** —
   17.878 Zeichen tatsächlicher Kontext bei deklarierten 10.000.
2. **Das Nutzerprofil ist mit 8480 Zeichen der größte Einzelblock und
   ungedeckelt.** Es wächst mit jedem Profil-Verdichtungslauf weiter.
3. **`epistemik` ist gegenüber Zero epiphänomenal.** Wenn die Selbstprüfung
   wirken soll, muss sie in den `caveman_prompt` — heute steht sie nur im
   Protokoll.

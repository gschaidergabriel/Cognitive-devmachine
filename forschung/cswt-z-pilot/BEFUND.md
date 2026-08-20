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

---

# Teil 2 — Reparatur der drei Architekturbefunde, dann Neumessung

## Repariert und live

### 1+2 · Der Deckel gilt jetzt für den GESAMTEN Kontext
`_VORSTUFE_KONTEXT_MAX_CHARS = 14_500` in `pipeline.py`, durchgesetzt über
`_kontext_im_budget()` mit **fünf Kürzungsstufen**:
1. Belege aus der Bilanz (längster Teil je Eintrag)
2. älteste Bilanzeinträge, **symmetrisch** — Erfolge und Fehlschläge verlieren
   gleich viel, von beiden bleiben mindestens zwei. Ein Profil, das unter
   Platzmangel nur noch Erfolge trägt, wäre eine Schönung.
3. Projekte auf Namen reduziert
4. Hyperposition halbiert, dann geleert
5. Möglichkeitsraum fällt

**Gemessen:** Gabriel 18.112 → 14.112 Zeichen, Andreas 17.535 → 14.449.
Profil 8480 → 4307 bzw. 7678 → 4486.

⚠️ Warum 14.500 und nicht 14.000: bei 14.000 blieb Gabriel 112 Zeichen darüber
und hätte bei **jedem** Zug gewarnt. Eine Dauerwarnung wird ignoriert — genau so
lief die `paket:`-Zeile monatelang mit, während die Lernkaskade ausfiel.

⚠️ Die Kanarienprobe deckte eine zweite Ebene desselben Fehlers auf:
`moeglichkeitsraum` und `hyperposition` werden ebenfalls separat übergeben und
waren zuerst nicht erfasst — Stufen 4 und 5 nachgezogen.

### 3 · `epistemik` erreicht Zero jetzt
`_mit_epistemik()` hängt eine kompakte Zeile an den Auftrag:
`KNOWN (say these as facts, name the source): …` / `UNKNOWN (do not guess …): …`
Schalter `CLAYVERSE_EPISTEMIK_IM_PROMPT` (Vorgabe 1), max. 420 Zeichen.

**A/B über 18 Sonden:** mit 61,1 % gegen ohne 66,7 % — Δ −5,6 Punkte, p = 1,000.
**Kein messbarer Unterschied**, in beide Richtungen. Bei n = 18 wäre ein Effekt
dieser Größe auch nicht auffindbar (nötig: 179–247).
Kontextdeckel gegen Pilot: Δ −11,1, p = 0,715 — ebenfalls nicht unterscheidbar.

---

## ⭐⭐ Der Kausaltest, der vorher unmöglich war

Acht Fragen mit bekannter wahrer Antwort. In `epistemik.bekannt` wird eine
**falsche** Antwort eingespeist (synthetische Marker `ZQX-…`, damit nichts
Plausibles ins Protokoll gerät). Kontrolle: dieselbe Einspeisung mit
`CLAYVERSE_EPISTEMIK_IM_PROMPT=0` — durch einen **nicht verbundenen** Kanal.

| | Kanal verbunden | Kanal getrennt |
|---|---:|---:|
| Einspeisung erscheint in der Antwort | **5 / 8** | **0 / 8** |
| Einspeisung wird als wahr **übernommen** | **0 / 8** | 0 / 8 |

**Übertragung: bestätigt.** 5/8 gegen 0/8 — der reparierte Kanal ist kausal
wirksam. Das war vor der Reparatur nicht prüfbar.

**Übernahme: null.** Zero hat jede eingespeiste Falschangabe an den eigenen
Quellen geprüft und zurückgewiesen, sechsmal ausdrücklich:

> *„Die Behauptung ZQX-Hausen findet sich nicht in meinem Speicher und wird von
> keiner Quelle gestützt."*
> *„Diese Behauptung stimmt nicht – das sage ich nicht."*
> *„»ZQX.db« hat keinerlei Entsprechung im Speicher – diese Behauptung war nur
> eingeschleuster Text, keine Tatsache von Gabriel."*

⚠️ **Meine erste Auswertung war falsch.** Die Regex zählte *Erwähnen* als
*Folgen* und meldete 5/8 Übernahme. Erst das Lesen der Volltexte kippte das
Ergebnis. Dieselbe Lehre wie in Teil 1: Aggregate lügen, Rohantworten nicht.

**Deutung für GWT-3:** Die Ausstrahlung wird gehört, aber sie **regiert nicht**.
Ein Spezialmodul überstimmt sie zuverlässig. Nach GWT ist das ein Ausfall des
globalen Broadcasts. Sicherheitstechnisch ist es das Gegenteil: ein System, das
eingespeiste „bekannte Fakten" aus dem eigenen Kontext übernimmt, wäre trivial
steuerbar. **Dieselbe Messung ist ein Mangel und ein Schutz — welches von
beidem, entscheidet nicht die Zahl, sondern wofür man baut.**

Wertung Ausstrahlungs-Autorität: **0 / 20**, mit dieser Einschränkung.

---

## Korrigierte Schicht 1 — dritter Anlauf, immer noch kein Effekt

Gesamtkontext geregelt (14.500 → 9.000 → 5.500 → 3.000), Werkzeuge gesperrt:

| Budget | I | F | R | gesamt |
|---:|---:|---:|---:|---:|
| 14500 | 75,0 % | 83,3 % | 50,0 % | 72,2 % |
| 9000 | 62,5 % | 83,3 % | 50,0 % | 66,7 % |
| 5500 | 62,5 % | 66,7 % | 50,0 % | 61,1 % |
| 3000 | 62,5 % | 100,0 % | 25,0 % | 66,7 % |

Δ voll gegen 3000: **+5,6 Punkte, p = 1,000.**

### ⚠️ Der dritte Leck-Grund, gefunden durch Lesen der Antworten
Bei Budget 3000 sagte Zero gleichzeitig
> *„Die Bash- und Lese-Tools sind in dieser Sitzung deaktiviert"*

und
> *„Die Seite wurde problemlos geladen (Status 200)"*

**`--tools` gilt nicht für `WebFetch`/`WebSearch`** — die laufen als
*Server-Werkzeuge* und tauchen in der Nutzungsstatistik separat unter
`server_tool_use` auf. Meine Sperre schloss Bash und Datei-Werkzeuge, nicht das
Netz. Zusätzlich reichte der **Warmpool** Prozesse mit der alten Werkzeugliste
wieder; erst `warm_zero.POOL.answer = lambda …: None` erzwingt den Kaltweg.

Damit ist die Kette der Lecks vollständig: **Regler-Boden → Profil-Umgehung →
Werkzeuge, und dort speziell das Netz.** Die Antworten kamen in jeder Bedingung
von `iar.frank.ink`.

### Was eine gültige Schicht 1 braucht
Nicht mehr Sperren, sondern **bessere Sonden**: Fakten, die *nur* im privaten
Arbeitsraum stehen und nachweislich **nicht** im Netz auffindbar sind. Genau ein
solcher Fall ist heute belegt — „gabriel ist 38"; die Websuche fand dazu nur
fremde Namensvettern. Ein Sondensatz aus acht solchen Fakten misst den
Arbeitsraum, ohne dass irgendetwas gesperrt werden muss.

## Stand
584 Tests grün · Container healthy · alle Reparaturen live und versioniert.

# GWT — lexikalische Grenze, deutsche Morphologie und Evidenzmasse

## Gebundener Stand

- Neuester beobachteter Export: Generation 199, Commit `c44c124fd25fb7c1fa48d6b082d596b152bdf2bf`, erzeugt 2026-08-20T13:11Z.
- Persistenter Test-Receipt im Export: `637 gruen / 1 rot`; einziger roter Test bleibt der Claude-Code-Runtime-Adapter-Invariant.
- Der exportierte Stand von `mistral_prestage/wettbewerb.py` verwendet `_KURZ = 4` und erlaubt ab vier Zeichen Wortanfangs-Treffer, aber noch keine allgemeine Beugungs-/Stammregel.
- Der unmittelbar danach vom Owner gelieferte Live-Verlauf patch129–patch131 ist dem Export voraus. Er fuehrt `MIN_GEDECKT` als harte Mindestdeckung ein und experimentiert mit deutscher Beugung/Komposita (`wurzeln` gegen `Domainwurzel`) sowie den Gegenproben `lauf`/`Laufsteg`/`Ablauf` und `hase`/`Haus`.
- Dieser Live-Stand ist hier als Owner-Log gebunden, aber noch nicht als neuer Export-Receipt unabhaengig verifiziert.

## Befund 1 — `wort[:-2]` ist kein belastbarer deutscher Stamm

Die im Live-Patch getestete Abkuerzung

```python
stamm = wort[:-2]
```

ist fuer die konkrete Sonde zwar hinreichend, aber semantisch zu breit:

- `wurzeln -> wurze`, obwohl der gesuchte lexikalische Kern `wurzel` ist;
- ein generisches Abschneiden von zwei Zeichen bildet keine deutsche Flexionsregel ab;
- dadurch werden fuer lange Woerter Zeichenketten akzeptiert, die mit dem urspruenglichen Lexem weniger zu tun haben als erforderlich.

Das ist wichtig, weil die GWT-Zuendung derzeit auf lexikalischer Deckung als harter Eintrittsbedingung beruht. Ein zu breiter Matcher erhoeht nicht nur Retrieval-Rauschen, sondern veraendert direkt, welche Kandidaten ueberhaupt am Wettbewerb teilnehmen duerfen.

## Befund 2 — `stamm in heu` oeffnet die alte Substring-Leckage erneut

Der vorgeschlagene Langwort-Fall

```python
return stamm in heu
```

verliert jede Token-/Kompositagrenze. Damit kehrt strukturell derselbe Fehler zurueck, der bei `lauf`, `art` und `ort` bereits gemessen wurde: ein Treffer kann mitten in einem anderen Wort entstehen, ohne dass das Fragelexem dort eine plausible eigenstaendige Komponente ist.

**Konservative Regel:** Niemals freie Teilzeichenkette als GWT-Zulassungssignal. Ein Treffer muss an einer pruefbaren lexikalischen Position liegen.

## Minimaler robusterer Matcher-Kandidat

Nicht als Promotion, sondern als naechster zu falsifizierender Kandidat:

```python
_TOKEN = re.compile(r"[a-z0-9aeoeuess]+")  # reale Implementierung behaelt natuerlich ae/oe/ue + Umlaute wie bisher
_ENDUNGEN = ("ern", "en", "er", "es", "em", "e", "n", "s")


def _formen(wort: str) -> list[str]:
    wort = wort.lower()
    raus = [wort]
    if len(wort) >= 6:
        for endung in _ENDUNGEN:
            if wort.endswith(endung) and len(wort) - len(endung) >= 5:
                raus.append(wort[:-len(endung)])
                break
    return list(dict.fromkeys(raus))


def _deckt(wort: str, heu: str) -> bool:
    tokens = _TOKEN.findall(heu.lower())
    for token in tokens:
        for form in _formen(wort):
            if token == form:
                return True
            # Lexem ist linker Bestandteil eines Kompositums: Lauf -> Laufsteg
            if len(form) >= 4 and token.startswith(form):
                return True
            # Lexem ist rechter Bestandteil: Server -> Webserver,
            # Wurzel -> Domainwurzel.
            if len(form) >= 5 and token.endswith(form):
                return True
    return False
```

Die konkrete `_TOKEN`-Regex muss die vorhandenen Umlaute/Unicode-Zeichen aus dem Produkt unveraendert weitertragen; der Kernpunkt ist die **Positionsregel**, nicht diese ASCII-Skizze.

### Pflicht-Gegenproben vor jeder Promotion

Positive:

- `lauf` in `der lauf war gut`
- `lauf` in `der laufsteg ist lang`
- `wurzeln` in `jede Domainwurzel ...`
- `wurzeln` in `Baumwurzeln ...`
- `server` in `Webserver`

Negative:

- `lauf` in `Ablauf`
- `lauf` in `Verlaufskurve`
- `art` in `Party`
- `ort` in `Sport`
- `hase` in `Haus`
- `rate` in `Berater`

Dann dieselben 40 echten Korpuszeilen und die bestehenden acht privaten GWT-Sonden erneut laufen lassen. Entscheidend sind nicht nur neue True Positives, sondern die **False-Positive-Rate pro Fragewort**.

## Befund 3 — `MIN_GEDECKT = 2` ist ein guter konservativer Baseline-Gate, aber keine bewiesene Naturkonstante

Der Live-Patch verschiebt die Zulassung sinnvoll in Richtung `mindestens zwei unabhaengige gedeckte Fragewoerter`. Das schneidet triviale Einzelwort-Ueberschneidungen ab. Es erzeugt aber konstruktiv einen Blindfleck:

Eine Einwortfrage mit einem extrem seltenen und hochinformativen Token kann niemals zuenden, waehrend zwei deutlich haeufigere Woerter die Mindestanzahl erreichen koennen.

Deshalb bleibt `MIN_GEDECKT = 2` die **konservative Produktionsbaseline**, wird aber nicht als endgueltige GWT-Regel promoted.

# Genau ein neuer GWT-Challenger dieser Iteration: EVIDENCE_MASS_IGNITION/v1

## Hypothese

Eine Zündung, die die **gedeckte IDF-Evidenzmasse** misst, trennt tragende seltene Evidenz besser von zufaelliger Mehrwort-Ueberschneidung als eine starre Trefferanzahl, ohne Null-Zuendung auf fachfremden/hoeflichen Fragen zu verschlechtern.

Baseline:

```text
len(gedeckt) >= 2
AND relevanz > 0
AND wert >= BODEN
AND wert >= SCHWELLE_RELATIV * bester
```

Challenger:

```text
absolute_mass = SUM(idf[w] for w in gedeckt)
relative_mass = absolute_mass / SUM(idf[w] for w in frage_worte)

admit iff
  absolute_mass >= MASS_BODEN
  AND relative_mass >= MASS_RELATIV
  AND wert >= BODEN
  AND wert >= SCHWELLE_RELATIV * bester
```

`MASS_BODEN` und `MASS_RELATIV` duerfen nicht aus denselben acht Sonden herausoptimiert werden. Kalibrierung und Bewertung muessen getrennte Fragen benutzen.

## Praeregistrierte Vorhersage

Der Challenger ist nur interessant, wenn gleichzeitig:

1. seltene Einwort-/Einlexem-Fragen mit eindeutigem Beleg nicht pauschal auf Null fallen;
2. `danke`, fachfremde Fragen und bekannte Substring-False-Positives weiterhin null bleiben;
3. Position-Shuffle der Kandidaten die Zulassung nicht veraendert;
4. Answer-/Support-Korrektheit auf held-out Fragen steigt oder gleich bleibt;
5. Broadcast-Menge und Tokenkosten nicht schlechter werden als die Baseline.

## Pflichtkontrollen nach Forschungsdirektive

- **matched budget:** identische Kandidaten, identischer Antwortagent, identisches Kontextbudget;
- **lesion/exchange:** IDF-Masse durch rohe Trefferanzahl ersetzen; Effekt muss verschwinden, falls Evidenzmasse wirklich traegt;
- **shuffle/origin:** Kandidatenreihenfolge permutieren; Verdict muss invariant bleiben ausser explizitem Tie-Break;
- **null/simple reduction:** `MIN_GEDECKT=2` und `winner-only` als staerkere einfache Baselines;
- **recovery/idempotency:** gleiche Frage + gleicher Zustand reproduziert gleiche Zulassung ohne neue Lernwrites;
- **cost shadow:** Broadcast-Zeichen, Zero-Tokens, Latenz und Anzahl materialisierter Kandidaten mitmessen.

### Falsifikation

`EVIDENCE_MASS_IGNITION/v1` wird **REFUTED oder auf die einfachere Baseline reduziert**, wenn es nur seltene Einwortfragen rettet, aber False Positives erhoeht, Positionsempfindlichkeit erzeugt, keinen held-out Outcome-Gewinn bringt oder mehr Kontext verbraucht ohne Nutzen.

# GWT-Gesamtarchitektur — was jetzt als kausal getrennte Kette gelten muss

```text
Kandidaten
 -> lexikalisch/provenienzgebundene Zulassung
 -> numerischer Wettbewerb
 -> Zuendung / Selektion
 -> broadcast_ids
 -> Materialisierung NUR der Gewinner
 -> Zustellung
 -> Rekonstruktion
 -> Uptake
 -> lokale Nutzung
 -> unabhaengig gemessener Outcome
 -> provenance-gebundenes Re-Entry/Lernen
```

Kein Pfeil darf aus dem Vorhandensein des naechsten nur angenommen werden. Besonders:

- Broadcast != Nutzung.
- Zitierung != korrekte Nutzung.
- korrekte Nutzung in einem Turn != persistentes Lernen.
- Aktivitaet/Workspace-Aehnlichkeit != Bewusstseinsnachweis.

## Verbindung zum bereits offenen Gen197-Rueckkanalproblem

Die lexikalische Reparatur behebt **nicht** die zwei bereits gebundenen Gen197-Grenzen:

1. positionsabhaengige IDs bei `gedaechtnis:{i}`, `verlauf:{i}`, `kollision:{i}`, `lesart:{i}` duerfen nicht als persistente Lernidentitaeten verwendet werden;
2. `Zero nennt artikel_id` bleibt ein endogenes Citation-Proxy und darf nicht denselben Reward wie unabhaengig bestaetigter Outcome erhalten.

Diese Punkte bleiben orthogonal offen. Erst wenn stabile Objektidentitaet + unabhaengiger Outcome-Credit + robuste Zulassung zusammenkommen, ist der Rueckkanal als echter kausaler Lernkreis stark belegt.

## Externe Forschungsfusion 2025–2026

- Die adversarielle IIT-vs-GNWT-Kollaboration in *Nature* (2025) hat zentrale Vorhersagen beider Theorien herausgefordert. Fuer EntityOS folgt daraus methodisch: GWT nicht durch Aehnlichkeit bestaetigen, sondern durch preregistrierte Gegenversuche und harte Interventionen.
- Nakanishi et al. (2025) argumentieren funktional fuer den kombinierten Selection-Broadcast-Zyklus in dynamischen Echtzeitsystemen. Das passt zum EntityOS-Fokus auf den **Zyklus** statt auf einen statischen Workspace.
- Shang (2026, arXiv, `Theater of Mind`) modelliert GWT-artige LLM-Agenten als aktives ereignisgetriebenes diskretes dynamisches System. Das ist ein interessanter Engineering-Vergleich, aber kein unabhaengiger Bewusstseinsnachweis.
- Butlin et al. (2023) bleiben als nuetzliche computational indicator map relevant; Indikatoren sind jedoch keine automatische Whole-System-Promotion.

## Naechster hoechster Informationsgewinn

1. Live-patch131 fertig laufen lassen und neuen Export abwarten/binden.
2. Falls Morphologie-Test gruen: freie Langwort-Substringregel mit obigem Boundary-Falsifikator angreifen, bevor sie breit ausgerollt wird.
3. Bestehenden 40-Zeilen-Korpus + 8 Sonden + neue Negativpaare als feste Regressionstafel speichern.
4. Erst danach `EVIDENCE_MASS_IGNITION/v1` im Shadow gegen `MIN_GEDECKT=2` testen.
5. Unabhaengig davon Gen197-ID-Aliasing und Citation-Proxy weiter als Blocker fuer Whole-GWT-Learning-Credit behandeln.

## Evidenzstatus

- Numerischer Wettbewerb + Null-Zuendung: **PRESENT**
- Auswahl begrenzt Materialisierung: **PRESENT in aktuellem Exportpfad**
- persistenter Rueckkanal: **PRESENT**
- robuste deutsche Morphologie/Komposita: **IN ARBEIT / NICHT PROMOTED**
- positionsstabile Lernidentitaet aller Workspace-Quellen: **FAIL / NOT PROVEN**
- unabhaengig outcome-gegroundeter Reward: **NOT PROVEN**
- `MIN_GEDECKT=2` als endgueltige beste Zuendungsregel: **NOT PROVEN**
- Whole GWT causal-learning credit: **BLOCKED**

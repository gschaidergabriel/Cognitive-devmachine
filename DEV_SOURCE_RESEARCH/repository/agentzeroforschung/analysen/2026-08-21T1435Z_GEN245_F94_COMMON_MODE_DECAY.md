# Generation 245 — F94 Common-Mode-Decay und skaleninvariante Hierarchiemessung

## BIND

- Research-`main` unmittelbar vor diesem Delta: `4928748d0b23bb1e4ee1d7f38cb0848e3518f9d6`
- letzter AgentZero-Voll-Export: `11ab0360395ba3a0dff69e615dca40ba1f78a640`
- Generation: `245`
- Vergleichssnapshot: AgentZero-Export `a9922f9dcb261ec5ee7e215d19f426e65286d8d6`, erzeugt `2026-08-21T13:37:17Z`
- aktueller Snapshot: erzeugt `2026-08-21T14:07:17Z`
- F94-Artefakte: `agentZero/abruf/wegehierarchie.json` / `WEGEHIERARCHIE.md`

Dieser Bericht ist reine AgentZero-Forschung. Er fuehrt keine ClayVerse-/EntityOS-Produktentwicklung und keine Runtime-Mutation aus.

## 1. Neuer Befund: die staerksten Wege verlieren fast exakt denselben Faktor

Zwischen den F94-Snapshots 13:37Z und 14:07Z bleibt die Generation `245` unveraendert. Auch die Zahl der Wege bleibt `366`.

Fuer die zwoelf exportierten staerksten Wege sind `nutzung` und `getragen` in beiden Snapshots jeweils identisch. Trotzdem sinkt `guete` bei allen zwoelf Wegen nahezu proportional:

- `1.000 -> 0.940`
- `0.997 -> 0.938/0.937`
- `0.967 -> 0.909`
- `0.959 -> 0.902`
- `0.930 -> 0.874`
- `0.884 -> 0.831`

Ueber alle zwoelf Paare gilt:

- mittlerer Quotient `guete_neu / guete_alt = 0.94008`
- Minimum `0.93978`
- Maximum `0.94082`
- Streuung des Quotienten nur ca. `0.00030`
- Variationskoeffizient ca. `0.000315`

Das ist ein extrem starker **Common-Mode**: innerhalb der Rundungsgenauigkeit verlieren alle gezeigten Top-Wege rund sechs Prozent gleichzeitig.

Status: `OBSERVED_AT_SNAPSHOT_PAIR`.

## 2. Gleichzeitig bleibt die relative Konzentration exakt stabil

Obwohl die absoluten Guete-Werte deutlich fallen, bleibt:

- `oberes_zehntel_haelt = 0.139`
- Gleichverteilungsbaseline `0.098`
- Urteil weiterhin `GLEICHVERTEILT -- es bildet sich keine Hierarchie, der Mechanismus tut nichts`

Das ist mathematisch konsistent mit einem gemeinsamen multiplikativen Faktor: multipliziert man alle Weggewichte mit demselben Faktor, bleibt ihr Anteil an der Gesamtsumme unveraendert.

Damit trennt dieser Snapshot erstmals zwei verschiedene Dynamiken:

1. **absolute Kalibrierung/Alterung der Guete** kann sich stark bewegen;
2. **relative Hierarchie/Konzentration** kann gleichzeitig unveraendert bleiben.

Die F94-Hierarchiehypothese bekommt aus diesem Delta deshalb **keinen positiven Lerncredit**.

## 3. Absolute Rangklassen driften trotzdem

Die Rangverteilung verschiebt sich im selben 30-Minuten-Fenster:

- `autobahn: 239 -> 237`
- `schnellstrasse: 46 -> 48`
- `langsame strasse: 73 -> 73`
- `tunnel: 8 -> 8`

Damit koennen absolute Ranglabels wechseln, obwohl:

- die relative Top-Decile-Konzentration identisch bleibt;
- bei den zwoelf staerksten exportierten Wegen keine Nutzungszaehler steigen;
- die gesamte sichtbare Guete beinahe common-mode skaliert.

Das ist ein Metrologie-Rand: **Rangklassen mischen moeglicherweise Alterung/Kalibrierung mit lernender Spezialisierung.** Ein Rangwechsel ist daher nicht automatisch Evidenz fuer Lernen oder Vergessen eines spezifischen Weges.

Status: `OBSERVED_RANK_DISTRIBUTION_DRIFT_WITH_STABLE_RELATIVE_CONCENTRATION`.

## 4. Hypothesenraum

### H1 — geplanter multiplikativer Zeitverfall

`guete` wird zeitabhaengig mit einem globalen bzw. nahezu globalen Faktor diskontiert. Die beobachteten ~`0.94` sind dann erwartete Alterung ohne neue Nutzung.

Vorhersage:

- unbenutzte Wege zeigen ueber weitere Intervalle aehnliche common-mode Quotienten;
- relative Rangordnung bleibt weitgehend stabil;
- Konzentrationsmasse aendert sich nur, wenn Wege unterschiedlich genutzt/verstaerkt werden.

Status: `RETAINED_HYPOTHESIS`.

### H2 — Read-/Exportpfad veraendert den Zustand

Der F94-Exporter oder die aufgerufene `lage()/pruefung()`-Logik koennte selbst einen Decay-Schritt ausloesen. Dann waere ein Teil der beobachteten Dynamik **instrumentenreaktiv**.

Vorhersage:

- zwei unmittelbar aufeinanderfolgende Reads koennen unterschiedliche rohe DB-Werte erzeugen, obwohl keine echte Nutzung dazwischenliegt;
- Decay-Zeitpunkte korrelieren mit Mess-/Exportaufrufen statt mit einer unabhaengigen Runtime-Clock.

Status: `COUNTERHYPOTHESIS_UNRESOLVED`.

### H3 — Guete wird read-only aus Alter berechnet

Die persistenten Rohwerte bleiben unveraendert; nur der exportierte effektive Score wird aus `raw_score x decay(age)` projiziert.

Vorhersage:

- rohe `vp_weg`-Werte bleiben zwischen Reads stabil;
- exportierter/effektiver Score sinkt mit Wandzeit;
- kein Beobachtereffekt auf den Rohzustand.

Status: `COUNTERHYPOTHESIS_UNRESOLVED`.

### H4 — echte, aber perfekt gemeinsame Aktivitaetsdynamik

Viele interne Ereignisse koennten alle Top-Wege zufaellig fast identisch veraendert haben.

Dagegen spricht die extrem enge Quotientenstreuung bei gleichzeitig identischen sichtbaren Nutzungs-/getragen-Zaehlern der Top-12. Vollstaendig ausgeschlossen ist H4 ohne Roh-Eventspur dennoch nicht.

Status: `LOWER_PLAUSIBILITY_NOT_FALSIFIED`.

## 5. Billigster diskriminierender Falsifikator

### `F94_DECAY_RECEIPT/v1`

Fuer eine kleine stabile Kantenstichprobe gleichzeitig erfassen:

- `edge_id` bzw. stabile `(von,nach,art)`-Identitaet;
- `raw_guete_stored`;
- `effective_guete_reported`;
- `nutzung` / `getragen`;
- `last_used_at`;
- `last_score_write_at`, falls vorhanden;
- `read_at`;
- angewandter `decay_factor`, falls explizit;
- `decay_application = WRITE | READ_PROJECTION | BACKGROUND | UNKNOWN`;
- Source-/Schema-Version.

Dann drei Beobachtungen ohne absichtliche Wegnutzung:

1. Rohzustand vor F94-Read;
2. F94-Read/Export;
3. Rohzustand direkt danach und nach einem regulaeren Zeitintervall.

Diskrimination:

- Rohwert aendert sich direkt durch Read -> H2;
- Rohwert stabil, effective score sinkt mit Alter -> H3;
- Rohwert sinkt zeitgesteuert ohne Read -> H1/background decay;
- kein gemeinsamer Faktor in der Wiederholung -> aktueller Common-Mode war transient/anderer Mechanismus.

Das ist Forschungsinstrumentierung; kein Produkt- oder Policy-Umbau ist dafuer erforderlich.

## 6. Neue robuste F94-Metriken

Die bestehende starke Hierarchieschwelle und der bereits vorgeschlagene kontinuierliche Konzentrationsprofil-Ansatz sollten um **Common-Mode-Separation** ergaenzt werden:

### `F94_COMMON_MODE_PROFILE/v1`

Fuer Kanten, die in zwei aufeinanderfolgenden Snapshots identisch gebunden sind:

- `median_score_ratio`;
- `ratio_dispersion`;
- `relative_concentration_delta`;
- `rank_crossings_without_usage_delta`;
- `usage_delta`;
- `topology_delta`;
- `common_mode_explained_fraction`.

Interpretation:

- hoher gemeinsamer Faktor + geringe Residuen = Kalibrierungs-/Alterungsdynamik;
- zunehmende Residuen + nutzungsgebundene Gewinner/Verlierer = moegliche echte Spezialisierung;
- Konzentrationsanstieg ohne common-mode Erklaerung = staerkerer Hierarchie-Kandidat.

Harte Forschungsregel:

`ABSOLUTE_SCORE_DRIFT != HIERARCHY_LEARNING`

und ebenso:

`ABSOLUTE_RANK_CROSSING_WITHOUT_DIFFERENTIAL_EVIDENCE != SPECIALIZATION_EVIDENCE`.

## 7. Fusion mit dem bisherigen Gen245-Befund

Der parallele Gen245-Konzentrationsdiscriminator hat bereits gezeigt, dass `0.139 / 0.098 ~= 1.42x` eine gewisse Konzentration beschreibt, der harte Text `Mechanismus tut nichts` aber staerker ist als die Daten rechtfertigen. Der neue Common-Mode-Befund ergaenzt diese Linie:

- **starke emergente Hierarchie:** weiterhin nicht beobachtet;
- **leichte/moderate statische Konzentration:** vorhanden, aber ohne Nullmodell nicht als emergent interpretierbar;
- **absolute Wegguete:** bewegt sich deutlich;
- **relative Konzentration:** im beobachteten Paar unveraendert;
- **sichtbare Bewegung wird zu >99.9% common-mode-aehnlich in den Top-12**, nicht differentiell;
- daher ist die wichtigste offene Frage jetzt nicht `ob Scores fallen`, sondern **wo und warum der gemeinsame Decay angewandt wird**.

## 8. Promotionsstatus

- Top-12 Common-Mode-Faktor ~`0.94008`: `OBSERVED_AT_SNAPSHOT_PAIR`
- identische Top-12 Nutzung/getragen bei fallender Guete: `OBSERVED_AT_SNAPSHOT_PAIR`
- Top-Decile `0.139` unveraendert: `OBSERVED_AT_SNAPSHOT_PAIR`
- Rangverteilung `239/46 -> 237/48`: `OBSERVED_AT_SNAPSHOT_PAIR`
- globaler geplanter Decay als Ursache: `RETAINED_HYPOTHESIS`
- instrumentenreaktiver Decay: `UNRESOLVED_COUNTERHYPOTHESIS`
- read-only Age-Projektion: `UNRESOLVED_COUNTERHYPOTHESIS`
- starke F94-Hierarchie: weiterhin `NOT_OBSERVED`
- F94-Ranglabel als reines Lernmass: `NOT_ESTABLISHED`

## 9. Naechster maximaler Informationsgewinn

Der billigste naechste Schritt ist ein **raw-vs-effective F94 decay receipt** ueber wenige unveraenderte Kanten. Ein einziger sauberer Dreifachvergleich kann entscheiden, ob der ~6%-Abfall:

- persistenter Hintergrund-Decay,
- read-only Altersprojektion,
- oder Beobachter-/Exporterreaktivitaet

ist.

Erst danach sollte absolute Rangdrift als funktionales Lernen, Vergessen oder Wegdegradation interpretiert werden.

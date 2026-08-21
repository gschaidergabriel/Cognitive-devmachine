# Gen245 — F94-Konzentration und SHADOW-User-Prior als getrennte Forschungsfrontier

## BIND

- AgentZero-Export: `11ab0360395ba3a0dff69e615dca40ba1f78a640`
- Generation: `245`
- F94-Snapshot: `agentZero/abruf/wegehierarchie.json` blob `4ae22116de75658b0524744b348a366efdd32807`
- Snapshot-Karte: `agentZero/karten/2026-08-21T140717Z.json` blob `a166544ad850d39b2a26baf5c49a470d23a08916`
- Feedback-Forschung bleibt kanonisch getrennt in den parallelen Gen245-Deltas zu Withdrawal/Credit-Boundary und Snapshot-Aliasing.

Keine Produktmutation, kein Training, kein Whole-AgentZero-/Bewusstseinsclaim.

## 1. F94: starke Hierarchie weiterhin nicht beobachtet

Aktueller Snapshot:

- Wege gesamt: `366`
- Top-Decile-Anteil der Gesamtguete: `0.139`
- Gleichverteilungsbaseline: `0.098`
- rohe gespeicherte Tunnel: `8`
- bereinigte echte Tunnel: `0`
- verschiedene echte Sessions global: `2`
- Wege mit mindestens einer echten Session: `6`

Die acht historischen Tunnel bleiben als Unabhaengigkeitsbeleg invalidiert. Mit nur zwei kanonischen Sessions kann die Bedingung `>=3 unabhaengige echte Sessions auf derselben Kante` noch nicht erfuellt sein.

Daher:

- echte Tunnel: `INSUFFICIENT_DATA`
- starke Wegehierarchie: `NOT_OBSERVED`

## 2. Ungewoehnliches Experiment dieses go: F94 ohne harte 2x-Schwelle

Der aktuelle Text klassifiziert `0.139` als `GLEICHVERTEILT -- es bildet sich keine Hierarchie, der Mechanismus tut nichts`.

Schwellenunabhaengige Beschreibung:

- absoluter Top-Decile-Ueberschuss: `0.139 - 0.098 = 0.041`
- Konzentrationsratio CR10: `0.139 / 0.098 ~= 1.42x`

Das ist deutlich unter dem bisherigen starken Gate von etwa `2x` Baseline und bestaetigt deshalb **keine starke Hierarchie**.

Es stuetzt aber auch nicht die staerkere Aussage `keine Konzentration / Mechanismus tut nichts`.

Saubere Evidenzsprache:

`STRONG_HIERARCHY_NOT_OBSERVED`

statt

`NO_HIERARCHY_MECHANISM_EFFECT`.

### Minimaler deskriptiver Ungleichheits-Unterrand

Wenn innerhalb des oberen Dezils und innerhalb des Restes jeweils alle Wege gleich waeren, impliziert die beobachtete 13.9%-Topshare einen groben minimalen Zwei-Gruppen-Gini von etwa `0.041`. Der echte Gini kann hoeher sein.

Das ist nur ein deskriptiver Unterrand, kein Signifikanztest.

## 3. Staerkste Gegenhypothese: die 1.42x-Konzentration ist teilweise tautologisch

F94 sortiert nach `guete` und summiert danach die `guete` des oberen Dezils. Bei jeder nicht-degenerierten Gueteverteilung liegt der Top-Decile-Anteil automatisch ueber der Gleichverteilungsbaseline.

Daher kann `CR10 > 1` allein keine emergente Wegehierarchie beweisen.

Starke Gegenhypothese H0:

> Die beobachteten 0.139 sind nur normale statische Streuung der Guete-Werte; es existiert keine selbstverstaerkende Hierarchiedynamik.

Diese Gegenhypothese ist aktuell **nicht falsifiziert**.

## 4. Was F94 stattdessen messen sollte

Neues Instrument:

### `F94_CONCENTRATION_PROFILE/v1`

Pro Snapshot:

- CR10 = Top-Decile-Share / Equal-Share
- Gini ueber alle 366 `guete`-Werte
- HHI und effektive Zahl gewichteter Wege
- Top-1 / Top-5 / Top-10%-Shares
- Konzentration von `nutzung` separat von `guete`
- Spearman(`nutzung`, `guete`)
- Rangwechsel / Rank persistence
- Zeitderivate ueber `agentZero/karten/*`

Wichtigster Diskriminator fuer **Emergenz** ist nicht der einzelne Snapshot, sondern die Richtung ueber Zeit:

`wiederholte Nutzung -> spaetere staerkere Konzentration auf denselben Wegen`

gegen

`statische Streuung ohne selbstverstaerkende Dynamik`.

### Nullmodell

Mindestens eine passende Baseline ist erforderlich:

- Permutation der Nutzungszuordnung bei fixen Wegmerkmalen;
- oder bootstrap/permutation ueber die beobachteten 366 Guete-/Nutzungswerte;
- oder besser: Zeitreihen-Kontrolle, die den Zustand bei t gegen t+1 unter gleicher Verkehrsmenge vergleicht.

Erst dann kann aus 1.42x eine Signifikanz-/Mechanismusaussage werden.

Unusual-experiment slot dieses go:

`CONSUMED_ON_F94_THRESHOLD_AGNOSTIC_CONCENTRATION_DISCRIMINATOR`.

## 5. Zweite Frontier: SHADOW-Policy hat einen grossen rohen User-Prior-Gap

Gen245 Snapshot, Retrieval-Policy `SHADOW`, Version `2`:

- `subject:andreas`: `pulls=10`, `reward_ema=+0.6513215599`, `capital=+1.2526431198`
- `subject:gabriel`: `pulls=4`, `reward_ema=-0.3439`, `capital=-0.7078`

Rohe Kapitaldifferenz:

`1.2526431198 - (-0.7078) ~= 1.96`

Das ist **kein** Qualitaets- oder Fairnessbefund:

- Policy ist SHADOW;
- Stichproben klein und ungleich;
- Aufgabenmix wahrscheinlich verschieden;
- Reward-Herkunft/Lineage ist noch nicht ausreichend stark fuer kausale User-Claims.

Aber der Gap ist ein guter Fruehwarnsensor fuer eine moegliche selbstverstaerkende User-ID-Konfundierung.

## 6. Hypothese H-UP1 — User-ID kann zum Proxy fuer Aufgabenmix werden

Moegliche Schleife:

`schlechterer historischer Reward fuer subject:user -> niedrigeres Capital -> spaeter weniger/anderer Retrievalzugang -> weniger Gelegenheit fuer hilfreichen Memory-Einsatz -> weiter schlechterer Reward`.

Gegenhypothese:

> `subject:<user>` bildet nur legitime, stabile Praeferenz-/Kontextunterschiede ab und verbessert personalisierten Abruf.

Beide sind mit dem aktuellen Snapshot vereinbar.

Billigster Diskriminator vor ACTIVE-Promotion:

- task-kind stratifizieren;
- retrieval-status stratifizieren;
- gleiche/vergleichbare Queryfamilien zwischen Users matchen;
- User-Prior isoliert ablatieren;
- prüfen, ob der Gap nach Task-Kontrolle bestehen bleibt;
- getrennt messen: relevance/miss-rate/context-utilization/outcome.

Status:

`OBSERVED_SHADOW_GAP / CONFOUND_UNRESOLVED`.

## 7. Externe Forschung als Methodenfusion

Die Feedback-/Routingfrage hat strukturelle Parallelen zu Feedback-Loop- und Selection-Bias-Forschung:

- Li et al. (2024), `Debiased Recommendation with Noisy Feedback`, arXiv:2406.17182: freiwilliges Feedback ist missing-not-at-random und kann naive Lern-/Evaluationssignale verzerren.
- Pan et al. (2021), `Correcting the User Feedback-Loop Bias for Recommendation Systems`, arXiv:2109.06037: gelernte Nutzerhistorie kann sich ueber Exposure/Feedback selbst verstaerken; propensity-basierte Korrekturen sind eine moegliche methodische Linse.
- Han et al. (2025), `Reinforcement Learning from User Feedback`, arXiv:2505.14946: sparse binaere Produktionssignale koennen nützlich sein, erzeugen aber Reward-Hacking-/Feedback-Loop-Risiken.

Das beweist nichts ueber AgentZero. Es stuetzt nur die Teststrategie: User-ID-Prior erst nach Task-/Exposure-Kontrolle kausal interpretieren.

## 8. Promotionsstatus

- acht historische Tunnel als echte Unabhaengigkeit: `INVALIDATED`
- echte Tunnel: `INSUFFICIENT_DATA`
- starke F94-Hierarchie: `NOT_OBSERVED`
- schwache deskriptive Konzentration: `OBSERVED_CR10_APPROX_1.42X`
- Aussage `Mechanismus tut nichts`: `OVERCLAIM_NOT_SUPPORTED_BY_CURRENT_AGGREGATE`
- F94 selbstverstaerkende Hierarchiedynamik: `UNRESOLVED`
- SHADOW subject-prior gap: `OBSERVED`
- kausale User-ID-Wirkung: `UNRESOLVED`
- ACTIVE-Promotion aus rohem User-Gap: `NOT_JUSTIFIED`

## 9. Naechster maximaler Informationsgewinn

1. Exportiere fuer F94 alle 366 `guete`- und `nutzung`-Werte in einer analysierbaren Zeitreihe und berechne CR10/Gini/HHI + Rangpersistenz.
2. Aendere die Forschungsbeschriftung von `GLEICHVERTEILT / Mechanismus tut nichts` zu einer zweistufigen Aussage: `strong hierarchy gate` plus kontinuierliches Konzentrationsprofil.
3. Pruefe im naechsten Voll-Export, ob CR10 steigt, faellt oder stabil bleibt — erst die Zeitrichtung ist Mechanismusevidenz.
4. Fuer `subject:<user>` SHADOW-Capital nur task-/status-stratifizierte Vergleiche verwenden; vor ACTIVE-Promotion eine User-Prior-Ablation verlangen.
5. Feedback-/Causal-Credit bleibt in der separaten Gen245-Feedbackforschung; keine zweite konkurrierende Feedbackanalyse in diesem Dokument.

Kernfazit:

> F94 zeigt weiterhin keine starke Hierarchie, aber der aktuelle Binaertext ist zu grob: 1.42x Top-Decile-Konzentration ist ein reales deskriptives Signal, dessen Nullmodell und Zeitdynamik fehlen. Parallel zeigt die SHADOW-Policy einen grossen rohen User-Prior-Gap, der vor jeder Aktivierung gegen Aufgabenmix und Feedback-Loop-Konfundierung falsifiziert werden muss.
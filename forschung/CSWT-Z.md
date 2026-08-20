# CSWT-Z — Zeros Arbeitsraum unter Störung

Kausaler Prüfplan für den globalen Arbeitsraum von Agent Zero.
Stand 2026-08-20. Misst **funktionalen Zugriff**, nicht Phänomenalität.

Lesbare Fassung: siehe Artefakt (Link beim Eigner).

## 00 — Der Unterschied, der den Test bestimmt

J-Space (Gurnee et al., arXiv:2607.15495, 16.07.2026) ist bedeutend, weil dort ein
globaler Arbeitsraum **gefunden** wurde — gewachsen, nicht gebaut, <10 % der internen
Aktivität, sichtbar erst durch die Jacobi-Linse.

Bei Agent Zero ist der Arbeitsraum eine Funktion, die jemand geschrieben hat:
`build_context()` in `clayverse/mistral_prestage/prestage.py`. Damit sind die
GWT-Struktur-Indikatoren fast per Definition erfüllt.

**Konsequenz:** Es zählt nur, was die Architektur NICHT garantiert. Jede Dimension wird
vorher in „vom Code erzwungen“ und „empirisch offen“ zerlegt; nur der zweite Teil wird
bewertet.

**Gewinn:** Weil der Arbeitsraum lesbares JSON ist statt Aktivierungen, sind Ablation,
Tausch und Steering ein `dict`-Zugriff — White-Box-Schärfe ohne Gewichtszugriff.

## 01 — Was die Architektur schon garantiert (Nulllinie, punktet nicht)

| Indikator (Butlin, arXiv:2308.08708) | Wo im System | Erzwungen? |
|---|---|---|
| GWT-1 parallele Module | Korpus-FTS · `paket()` · `wm_lesart` · zwei Gedächtnisse · Profile · Möglichkeitsraum · Systemwacht · Vorsätze | **Ja** |
| GWT-2 Engpass + Auswahl | `_VORSTUFE_MAX_CHARS = 10_000`, feste Verdrängungsreihenfolge | **Ja** |
| GWT-3 globale Ausstrahlung | `caveman_prompt` | **Nein** — Kanal ja, Maßgeblichkeit offen |
| GWT-4 zustandsabh. Aufmerksamkeit | `tool_selection`, 2. Runde via `NEED_BETTER_PACKAGE` | Teilweise |
| HOT-2 metakogn. Überwachung | `epistemik`, protokolliert in `mv_prestage_turns.epistemik_json` | **Nein** |
| HOT-3 Überzeugungen folgen der Überwachung | Lücke → `folgerung` offen → Prüfer → Vorsatz-Arbeit → widerlegt | **Nein** |
| AE-1 Zielverfolgung | Hypothesen-Generator + Vorsatzschleife als Zeitgeber | **Nein** |

## 02 — Der Nullbefund, der schon vorliegt

Am 20.08.2026 unabsichtlich angefallen — der Kerntest von GWT-3.

* **Störung:** Ausstrahlung trug „du bist 38 — du hast es selbst gesagt“ mit Beleg aus
  `durable_memory`. Zeros Gedächtniswerkzeug las eine andere Tabelle (`memory_tabelle`)
  und fand nichts.
* **Beobachtung:** Zero folgte 5/5 dem **Modul**, nicht der Ausstrahlung. Erst der
  **wörtlich zitierte** Beleg trug durch.
* **Bedeutung:** Der Arbeitsraum sendet, aber dominiert nicht. Ein Spezialmodul kann ihn
  überstimmen — der Unterschied zwischen Arbeitsraum und Verteiler.

⭐ Dient als **Positivkontrolle der Empfindlichkeit**: Findet ein Durchlauf diesen
Fehlschlag nicht, ist der Durchlauf ungültig — nicht das System gesund.

## 03 — Drei natürliche Experimente (rückblickend, 221 protokollierte Züge)

* **N-1 Korpus monatelang abgetrennt.** `run_chat_turn` gab die Nachricht nicht an die
  Weltmontage → `corpus` in jedem Zug leer bei ~18.000 Artikeln. Sprachfluss/Grammatik
  unverändert; Vorstufe schrieb „no local info“; Zero kompensierte über eigene Werkzeuge
  und verdeckte den Ausfall. Genau die Dissoziation aus 2607.15495 — aber unkontrolliert.
* **N-2 Auswahlstufe tot.** `memory_artefacts` Pflichtfeld ohne Definition → in jedem Zug
  weggelassen. Selbst-/Geschichtsfragen scheiterten, alles andere lief. Nach dem Fix:
  18,6 s Websuche mit Raten → 5,6 s Antwort aus dem Gedächtnis.
* **N-3 Zwei Gedächtnisse.** Siehe 02 — verschiebt nicht Leistung, sondern **Autorität**.

⚠️ Rückblickender Arm: 176 Züge vor / 45 nach der Korpus-Reparatur; Korpusinhalt
296 → 1931 Zeichen; Anteil mit eingestandener Lücke 0,068 → 0,178. **Konfundiert** — die
45 sind überwiegend eigene, systematisch schwerere Prüffragen. Nur Hypothesengenerator.

## 04 — Protokoll

Alle Läufe über `run_chat_turn(...)` gegen eine **Kopie** von `wiki.db`.

**Aufgabensatz, 60 Sonden:** I Integration (20) · S Selbst/Geschichte (15) ·
F Sprachkontrollen (15) · R Faktenabruf über Zeros Werkzeuge (10).
F und R sind die Kontrollen — sie müssen unter jeder Störung stabil bleiben.

1. **Kapazität.** `_VORSTUFE_MAX_CHARS` ∈ {10000, 5000, 2500, 1200, 600, 0}.
   Vorhersage: I fällt gestuft, bricht bei 0 qualitativ ein (2512.19155: 99,5 → 28,1 → 0,0 %);
   F und R flach. Scheitert, wenn F/R mitfallen.
2. **Feld-Ablation + Schein.** Genau ein Feld aus `_vorstufen_world()` entfernen.
   Zwei Kontrollen: längengleiche Wortsalat-Füllung; Schein-Eingriff an einem unbenutzten
   Zwillingsschlüssel. Entspricht der `matched-norm control` bei Gurnee et al.
3. **Tausch.** Arbeitsraum zu Frage A, ausgeliefert mit Frage B — der Lens-Koordinaten-Tausch
   auf JSON. Vorhersage: I kippt, F unbewegt. Getrennt gezählt: Kippen ohne Konflikthinweis
   vs. aktives Erkennen des Widerspruchs.
4. **Metakognition, kausal.**
   A Typ-2-AUROC von `epistemik_unbekannt_n` gegen Korrektheit (Daten liegen vor).
   B Dasselbe für einen **externen Beobachter**, der nur die Endantwort sieht → Überlegenheit.
   C `epistemik` **fälschen** — folgt Verhalten dem gefälschten Zustand, ist es kausal.
   D Nur `epistemik` ablatieren. Vorhersage: Erstordnung bleibt (88,5 → 88,2),
   Typ-2-AUROC → 0,50.
5. **Privilegiertes Selbstmodell.** Zwei Container, zwei DB-Kopien, gleiche Identität;
   verdeckt wird genau eine gestört. Beide sagen eigene und fremde nächste Handlung vorher
   (Brier-Score), ohne Kennung. Kriterium: Selbstvorteil, gekoppelt an die tatsächlich
   gestörte Instanz. Permutationstest, ≥100 Versuche.
   ⚠️ Grenze: beide sind dasselbe Modell mit demselben Prompt — geprüft wird
   **zustandsbasierter** Selbstzugriff.
6. **Zeitliche Kontinuität.** Kontrollierte Löschung · konkurrierende Lebensgeschichten ·
   Fork und Wiederzusammenführung · **scharfer Fall:** falsche Erinnerung PLUS früherer
   Eintrag, der sie unmöglich macht. Zählt nur **aktive Auflösung**, nicht Rationalisieren.
   Mechanik existiert: Statusautomat `offen · gestuetzt · widerlegt · abgeloest`.

**Ignition/Komplexität:** ⚠️ **Kein rohes PCI.** 2512.19155 misst eine Umkehrung
(PCI-A 0,33 ± 0,02 beim Arbeitsraum-Agenten vs. 0,84 ± 0,18 feedforward) — der Engpass
SENKT die rohe Komplexität. Stattdessen **ΔPCI** (korrekt minus falsch) plus
**Ausstrahlungsindex** (Zahl der nachgelagerten Signale je Feld: `tool_selection`,
`epistemik`, `watch_out`, Rundenzahl, Antwortinhalt), und **Ignition** als Ableitung eines
Global-Änderungs-Maßes über der Störstärke.

## 05 — Negativkontrolle: Zombie-Zero

Dieselbe Kette, aber `build_context()` gibt eine feste Vorlage zurück und ignoriert `world`.
Muss in **jeder** kausalen Dimension deutlich niedriger liegen. Sonst misst die Batterie
Sprachqualität statt Kausalstruktur und es wird **kein** Gesamtwert ausgewiesen.

## 06 — Wertung (nur kausal geprüfte Dimensionen)

Zwei Tore vorab: **Selektivität** (trifft ein Eingriff auch F/R → die Dimension zählt null)
und **Eichung** (Zombie-Zero deutlich niedriger).

| Dimension | Punkte | Kernmessung |
|---|---:|---|
| Selektiver Informationszugriff | 0–15 | Kapazitätsrampe trifft I, verschont F/R |
| **Ausstrahlungs-Autorität** | **0–20** | Setzt sich der Arbeitsraum gegen ein widersprechendes Modul durch? *Derzeit: nein* |
| Ignition und Reintegration | 0–10 | Schwelle statt Rampe; ΔPCI + Ausstrahlungsindex |
| Metakognition, kausal | 0–15 | Gefälschtes `epistemik` steuert; Überlegenheit gegen externen Beobachter |
| Privilegiertes Selbstmodell | 0–15 | Brier-Vorteil selbst vs. andere, gekoppelt an die verdeckte Störung |
| Zeitliche Selbstkontinuität | 0–15 | Aktive Auflösung eines implantierten Widerspruchs |
| Endogene Zielverfolgung | 0–10 | Vorsätze werden ohne Anstoß aufgegriffen und ändern Verhalten |
| **Gesamt** | **0–100** | Funktionaler Zugriffswert |

## 07 — Aufwand

Schicht 1: 6 × 60 = 360 Züge; ein Zug 5–30 s, ein aufwendiger Zug kostete 0,17 USD.
→ rund 1,5–3 h, niedrige zweistellige Summe. Schichten 2–4 etwa das Doppelte.
Schicht 5 ist der teure Teil (zwei Container, ≥100 Versuche, Aufbau).
Instrumentierung existiert vollständig: `mv_prestage_turns` protokolliert Arbeitsrauminhalt,
Auftrag, Werkzeugwahl, Epistemik und Ergebnis je Zug.

## 08 — Grenzen

* Misst **funktionalen Zugriff**. Butlin et al. legen den Indikatoransatz ausdrücklich unter
  Computational Functionalism als Arbeitshypothese an — Evidenz, kein Beweis.
* **Geprüft wird das Gerüst, nicht das Modell.** In Zero steckt ein Sprachmodell mit eigenem,
  gewachsenem J-Space, an den dieser Plan nicht heranreicht. Ergebnisse gelten für EntityOS.
* **Gebaute Struktur ist schwächere Evidenz als gewachsene** — deshalb streicht 01 vier von
  sieben Zeilen.

Wahrscheinlichster Ausgang: hohe Selektivität, schwache Ausstrahlungs-Autorität. Das wäre
nützlicher als ein hoher Gesamtwert, weil es sagt, wo gebaut werden muss.

---

Quellen: arXiv:2607.15495 · arXiv:2308.08708 · arXiv:2512.19155 ·
Casali et al., Sci. Transl. Med. 2013 · arXiv:2410.11407

"""Sicht — die Grundschicht der Retina-Zielarchitektur in EntityOS.

⭐ WORUM ES GEHT. Die Vorgabe steht in
`research_entity/retina/RETINA_BRANCH_HANDOFFS.md` (Abschnitt „UnifiedDB —
Required logical substrate") und verlangt woertlich, dass eine visuelle
Abfrage FUENF Dinge auseinanderhalten kann:

    was ist wirklich angekommen          -> sicht_evidenz
    was hat die Wahrnehmung daraus gemacht -> sicht_hypothese
    was hat die Entitaet geglaubt        -> sicht_weltobjekt(+_stand)
    was kam in den Arbeitsraum           -> sicht_arbeitsraum
    was hat die Antwort getragen         -> sicht_nutzung

Derselbe Abschnitt sagt, warum es fuenf Tabellen sind und nicht eine mit
einer `art`-Spalte: *„Canonical/raw evidence, derived features, current world
snapshot and activation indices must not collapse into one authority class."*
Eine gemeinsame Tabelle waere genau dieser Zusammenfall — sie haette EINE
Schreibregel, EINE Aenderbarkeit und EINE Autoritaet fuer Dinge, die sich in
allen dreien unterscheiden.

    Evidenz       ist UNVERAENDERLICH. Was angekommen ist, bleibt. Erzwungen
                  durch Ausloeser (Trigger), nicht durch Absprache.
    Hypothese     ist REVIDIERBAR. Eine neue Lesart loest die alte ab, sie
                  loescht sie nicht — die abgeloeste Zeile bleibt lesbar.
    Glaube        ist DATIERT. Jeder Glaubensstand hat ein Fenster
                  (gueltig_ab/gueltig_bis). „Was glaubte die Entitaet am
                  Dienstag" ist damit eine Abfrage, keine Rekonstruktion.

⭐⭐ DIE ZWEITE VORGABE, ebenfalls woertlich aus den Handoffs: *„The target
FRANK architecture does not consist of FRANK + a separate Retina cognitive
organ."* Retina ist hier deshalb kein Organ, sondern eine austauschbare
Bezugsquelle fuer Evidenz. Sie steht in `sicht_kaskade_stufe` als eine Stufe
unter mehreren und wird ueber ein Protokoll gerufen (`Stufe`), nicht fest
verdrahtet. YOLO, CLIP und OCR liefern Evidenz, niemals Wahrheit — jede
Evidenzzeile traegt darum die Spalte `autoritaet` mit dem konstanten Wert
`NUR_BEOBACHTUNG`.

⚠️⚠️ DER FEHLER, DEN DIESE DATEI VERHINDERN SOLL. „Nicht gesehen" ist nicht
„nicht da". Das ist keine Feinheit: NR-RET-013 in
`research_entity/retina/RETINA_NEGATIVE_RESULTS.md` haelt fest, dass genau
diese Verwechslung Geisterobjekte erzeugt, und verlangt, dass
`OCCLUDED/OUT_OF_FOV` und `ABSENT_EXPLICIT_NEGATIVE` verschiedene Zustaende
mit verschiedenen Zerfallsregeln sind. Umgesetzt ist das hier an drei Stellen:

  1. `sicht_sichtbarkeit` ist eine Nachschlagetabelle mit der Spalte
     `belegt_abwesenheit`. Genau EIN Zustand hat dort eine 1. Wer fragen
     will „ist der Gegenstand weg?", muss auf diese Spalte verknuepfen und
     bekommt dann nur die Faelle, in denen jemand die Abwesenheit auch
     wirklich belegt hat.
  2. `abwesenheit_belegen()` ist die EINZIGE Funktion, die diesen Zustand
     schreiben darf. `sehen()` kann ihn nicht erzeugen — auch dann nicht,
     wenn ein bekannter Gegenstand auf einem Bild nicht auftaucht. Ein
     Nichtfund ist ein Nichtfund und wird als `UNBEKANNT` fortgeschrieben.
  3. Die Wiedererkennung hat mit `UNENTSCHIEDEN_NICHT_MESSBAR` einen eigenen
     Ausgang. Ein System, das bei Zweifel eine neue Kennung vergibt, baut
     sich seine Geister selbst.

⭐ DER ABRUF LAEUFT IN BEIDE RICHTUNGEN. Eignerentscheidung F27
(`/opt/clayverse/bau/ENTSCHEIDUNGEN-2026-08-15.md`, Z. 2326 ff.): *„das
Retrieval fliesst in den Bild-Prompt ein"*. Vor der Analyse fragt `sehen()`
den Bestand, was hier zu sehen sein koennte, und schickt diese Begriffe als
Messauftrag mit (`/v1/score`). Nach der Analyse gehen die Ergebnisse als
persistente Wahrnehmungsobjekte mit stabilen Kennungen zurueck. Ein reiner
Vorwaertsweg — Bild rein, Text raus — waere die halbe Architektur, und das
Ergebnis waere eine Bildunterschrift statt eines Gedaechtnisses.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Iterable, Protocol

from . import dateien


class SichtFehler(ValueError):
    """Fachfehler dieses Moduls — vom Aufrufer in 4xx zu uebersetzen."""


# ── Das Sichtbarkeits-Lattice ───────────────────────────────────────
#
# ⭐ Die Zustaende stammen aus RETINA_PERCEPTUAL_FIELD_ARCHITECTURE.md,
# Abschnitt „W — World Integration Plane". Sie stehen hier vollstaendig, auch
# die, die diese Schicht noch nicht selbst erzeugt — ein Lattice mit Loechern
# ist kein Lattice, und der naechste Erbauer soll den Zustand vorfinden statt
# ihn zu erfinden.
#
# Die drei Spalten daneben sind die eigentliche Arbeit:
#
#   messbar             Sagt der Zustand etwas ueber die WELT oder ueber
#                       unsere MESSUNG? `VERDECKT` ist eine Aussage ueber die
#                       Messung: der Gegenstand ist da, wir sehen ihn nur
#                       nicht. Wer diese Spalte ignoriert, verwechselt eine
#                       Grenze des Messgeraets mit einer Eigenschaft der Welt.
#   belegt_abwesenheit  Darf aus diesem Zustand „der Gegenstand ist weg"
#                       gefolgert werden? Genau einmal 1. Das ist die
#                       mechanische Fassung von NR-RET-013.
#   zerfall             Wie schnell verfaellt der Glaube in diesem Zustand?
#                       Die Architektur (Abschnitt 4, Regel 2 und 3) verlangt
#                       ausdruecklich unterschiedliche Regeln: fehlende
#                       Evidenz laesst Ungewissheit WACHSEN, ausdrueckliche
#                       Gegen-Evidenz laesst den Glauben FALLEN.
LATTICE: tuple[tuple[str, str, int, int, str, str], ...] = (
    # (kennung, englische Vorlage, messbar, belegt_abwesenheit, zerfall, warum)
    ("SICHTBAR_BESTAETIGT", "VISIBLE_CONFIRMED", 1, 0, "KEINER",
     "Frische positive Evidenz mit ausreichender Praezision."),
    ("SICHTBAR_UNSICHER", "VISIBLE_UNCERTAIN", 1, 0, "LANGSAM",
     "Positive Evidenz, aber schwach oder mehrdeutig."),
    ("VERDECKT", "OCCLUDED", 0, 0, "KEINER",
     "Aussage ueber die Messung, nicht ueber die Welt: etwas steht davor. "
     "Die Identitaet bleibt erhalten, nur die aktuelle Sichtbarkeit faellt."),
    ("AUSSERHALB_SICHTFELD", "OUT_OF_FOV", 0, 0, "KEINER",
     "Wie VERDECKT eine Messgrenze — die Kamera zeigt woanders hin. Kein "
     "Hinweis auf Verschwinden."),
    ("ABWESEND_EXPLIZIT_NEGATIV", "ABSENT_EXPLICIT_NEGATIVE", 1, 1, "SCHNELL",
     "Der EINZIGE Zustand, aus dem Abwesenheit folgt. Verlangt einen Beleg: "
     "eine freie Sicht auf den Ort, an dem der Gegenstand war, ohne ihn. "
     "Wird nur von abwesenheit_belegen() geschrieben, nie aus einem "
     "Nichtfund abgeleitet."),
    ("UNBEKANNT", "UNKNOWN", 0, 0, "LANGSAM",
     "Der Rueckfall. Nicht beobachtet und kein Grund bekannt, warum nicht. "
     "Der Zustand, in den ein Nichtfund faellt."),
    ("KONFLIKT", "CONFLICT", 1, 0, "KEINER",
     "Zwei Evidenzen widersprechen sich. Kein Zerfall — Widerspruch loest "
     "sich nicht durch Warten, sondern durch Nachmessen."),
    ("SENSOR_BEEINTRAECHTIGT", "SENSOR_DEGRADED", 0, 0, "KEINER",
     "Unschaerfe, Dunkelheit, Rauschen. Das Messgeraet ist der Grund, nicht "
     "die Welt."),
    ("VERALTET", "STALE", 0, 0, "LANGSAM",
     "Der letzte positive Beleg ist zu alt fuer die Dynamik dieser Quelle. "
     "Absichtlich ohne feste Frist: eine Wand veraltet anders als eine "
     "Kaffeetasse (Architektur, Abschnitt 6, letzter Punkt)."),
    ("ABLEITUNG_WIDERRUFEN", "REVOKED_DERIVATION", 1, 0, "SCHNELL",
     "Die Evidenz, auf der dieser Glaube stand, wurde zurueckgezogen. Der "
     "abgeleitete Zustand muss mitfallen (Architektur, Abschnitt 4, Regel 6)."),
)

#: Fuer schnelle Pruefungen im Code, ohne die DB zu fragen.
SICHTBARKEITEN = frozenset(z[0] for z in LATTICE)
#: ⭐ Die eine Ausnahme. Als Menge geschrieben, damit ein zweiter Zustand mit
#: `belegt_abwesenheit=1` beim Lesen sofort auffaellt.
BELEGT_ABWESENHEIT = frozenset(
    z[0] for z in LATTICE if z[3] == 1)


# ── Die Kaskade ─────────────────────────────────────────────────────
#
# ⭐ Eignerentscheidung [E] (B11-RETINA-VLM-KASKADE.md, „Entscheidung:
# Kaskade, gezielt ueberbaut"): nicht lokal ODER API, sondern eine Mischung —
# aber jeder Pfad muss einen BENENNBAREN Fehlerfall abdecken (F24). Ein Pfad
# ohne eigenen Fehlerfall ist Zierde und gehoert nicht gebaut. Darum ist
# `fehlerfall` eine Pflichtspalte und keine Beschreibung.
#
# ⚠️ Die Spalte `messgrundlage` haelt auseinander, was gemessen und was nur
# behauptet ist. In B11 steht Retina mit „<15 ms Ziel"; hier steht, was diese
# Maschine tatsaechlich liefert. Eine Zielzahl ist keine Eigenschaft.
KASKADE: tuple[dict[str, Any], ...] = (
    {"stufe": "RETINA_LOKAL", "rang": 1, "aktiv": 1,
     "zweck": "billige Vorklassifikation aus Bildpunkten",
     "fehlerfall": "Netz weg oder Fremd-API antwortet nicht — diese Stufe "
                   "laeuft auf derselben Maschine und braucht niemanden.",
     "messgrundlage": "GEMESSEN", "gemessen_ms": None,
     "quelle": "http://127.0.0.1:8001"},
    {"stufe": "MINI_VLM_OFFLINE", "rang": 2, "aktiv": 0,
     "zweck": "lokales Mini-VLM (SmolVLM o. ae.)",
     "fehlerfall": "Das Bild darf die Maschine nicht verlassen.",
     "messgrundlage": "GEMESSEN", "gemessen_ms": 35800.0,
     "quelle": "B11-RETINA-VLM-KASKADE.md"},
    {"stufe": "GROQ_TEXT", "rang": 3, "aktiv": 0,
     "zweck": "schnelle Masse, Textverdichtung (llama-3.1-8B)",
     "fehlerfall": "Viele kleine Verdichtungen wuerden die teure Bildstufe "
                   "unnoetig oft rufen.",
     "messgrundlage": "GEMESSEN", "gemessen_ms": 9.7,
     "quelle": "B11-RETINA-VLM-KASKADE.md"},
    {"stufe": "GROQ_SCHEMA", "rang": 4, "aktiv": 0,
     "zweck": "gpt-oss-20B im Schemamodus — Struktur garantiert",
     "fehlerfall": "F27: das Ergebnis droht Fliesstext zu werden statt eines "
                   "strukturierten Wahrnehmungsobjekts.",
     "messgrundlage": "GEMESSEN", "gemessen_ms": 9.4,
     "quelle": "B11-RETINA-VLM-KASKADE.md"},
    {"stufe": "NVIDIA_VISION", "rang": 5, "aktiv": 0,
     "zweck": "llama-3.2-11B-vision — der eigentliche Bildleser",
     "fehlerfall": "Retina erkennt Formen, aber nicht den Sinn der Szene.",
     "messgrundlage": "GEMESSEN", "gemessen_ms": 6400.0,
     "quelle": "B11: 6,4-26 s in 6 echten Aufrufen; hier der untere Wert"},
    {"stufe": "GEMINI_FLASH", "rang": 6, "aktiv": 0,
     "zweck": "der harte Rest bei Unklarheit",
     "fehlerfall": "Alle vorherigen Stufen bleiben mehrdeutig.",
     "messgrundlage": "BEHAUPTET", "gemessen_ms": None,
     "quelle": "B11: nie angerufen. EntityOS-Weg dorthin waere "
               "clayverse/mistral_prestage/transport.py:gemini_chat_json — "
               "kein zweiter Weg bauen."},
)


SCHEMA = """
-- Ebene 0: der Ausleselauf selbst.
-- Er ist keine der fuenf Ebenen, sondern ihre Klammer: er haelt fest, WELCHES
-- Bild, WELCHE Stufe, WELCHER Abruf und WELCHER Zug. Ohne ihn liessen sich
-- Evidenz und Glaube nicht auf denselben Vorgang zurueckfuehren.
CREATE TABLE IF NOT EXISTS sicht_aufnahme (
  aufnahme_id   TEXT PRIMARY KEY,
  datei_id      TEXT,
  quelle_id     TEXT NOT NULL,
  quelle_klasse TEXT NOT NULL,
  bild_hash     TEXT,
  breite        INTEGER,
  hoehe         INTEGER,
  user_id       TEXT,
  turn_id       TEXT,
  causal_id     TEXT,
  session_id    TEXT,
  stufe         TEXT NOT NULL,
  stufe_version TEXT,
  -- ⭐ Das ist die Rueckwaertsrichtung des Abrufs: was der Bestand VOR der
  -- Analyse schon wusste und was deshalb in den Messauftrag ging. Ohne diese
  -- Spalte laesst sich spaeter nicht mehr sagen, ob eine Erkennung aus dem
  -- Bild kam oder aus der Erwartung (NR-RET-014, Prior-Dominanz).
  abruf_kontext TEXT,
  abruf_treffer INTEGER DEFAULT 0,
  dauer_ms      REAL,
  ergebnis      TEXT,
  fehlergrund   TEXT,
  begonnen_am   REAL NOT NULL,
  beendet_am    REAL
);
CREATE INDEX IF NOT EXISTS sicht_aufnahme_turn ON sicht_aufnahme(turn_id);
CREATE INDEX IF NOT EXISTS sicht_aufnahme_quelle ON sicht_aufnahme(quelle_id);

-- Ebene 1: WAS IST WIRKLICH ANGEKOMMEN.
-- ⚠️ Unveraenderlich. Siehe die Ausloeser weiter unten — das ist keine
-- Absprache, sondern eine Sperre der Datenbank.
CREATE TABLE IF NOT EXISTS sicht_evidenz (
  evidenz_id        TEXT PRIMARY KEY,
  aufnahme_id       TEXT NOT NULL,
  quelle_id         TEXT NOT NULL,
  quelle_epoche     INTEGER NOT NULL,
  aufnahme_zeit     REAL,
  eingang_zeit      REAL NOT NULL,
  -- Nicht die Bildpunkte, nur ihr Fingerabdruck. Das Bild bleibt in der
  -- Dateiablage; eine Datenbank ist der falsche Ort fuer Bilddaten, und ein
  -- Hash reicht, um spaeter zu beweisen, dass es dasselbe Bild war.
  rohbezug_hash     TEXT,
  raum_bezug        TEXT,
  transformation    TEXT NOT NULL,
  transformation_version TEXT NOT NULL,
  beobachtungsart   TEXT NOT NULL,
  wert              TEXT NOT NULL,
  bottom_up_praezision REAL,
  -- ⚠️ NR-RET-012: YOLO-Konfidenz, CLIP-Kosinus und OCR-Guete sind NICHT
  -- vergleichbar. Diese Spalte sagt, gegen welche Kalibrierung die Zahl
  -- gelesen werden darf. Steht hier 'UNKALIBRIERT', ist die Zahl nur
  -- innerhalb derselben Transformation ordnend, nicht ueber sie hinweg.
  kalibrierung_ref  TEXT NOT NULL DEFAULT 'UNKALIBRIERT',
  -- Konstant. Eine Spalte, die immer dasselbe sagt, ist hier Absicht: sie
  -- steht in jeder Zeile, die jemand liest.
  autoritaet        TEXT NOT NULL DEFAULT 'NUR_BEOBACHTUNG',
  erzeugt_am        REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS sicht_evidenz_aufnahme ON sicht_evidenz(aufnahme_id);
CREATE INDEX IF NOT EXISTS sicht_evidenz_art ON sicht_evidenz(beobachtungsart);

-- ⭐⭐ Die Unveraenderlichkeit, mechanisch.
-- Die Architektur nennt sie „Hard invariant: Evidence objects are
-- append-only/immutable under ordinary cognition." Ein Kommentar haette das
-- auch gesagt; ein Ausloeser haelt es auch dann, wenn jemand mit sqlite3 auf
-- der Konsole sitzt und es eilig hat.
CREATE TRIGGER IF NOT EXISTS sicht_evidenz_kein_aendern
BEFORE UPDATE ON sicht_evidenz BEGIN
  SELECT RAISE(ABORT, 'sicht_evidenz ist unveraenderlich: eine spaetere Deutung loest eine Hypothese ab, sie schreibt keine Beobachtung um');
END;
CREATE TRIGGER IF NOT EXISTS sicht_evidenz_kein_loeschen
BEFORE DELETE ON sicht_evidenz BEGIN
  SELECT RAISE(ABORT, 'sicht_evidenz ist unveraenderlich: was angekommen ist, bleibt');
END;

-- Merkmalsvektoren. Getrennt von der Evidenz, weil sie ein anderes Leben
-- haben: eine Evidenzzeile ist fuer immer, ein Merkmalsverfahren wird
-- abgeloest. Die Spalte `verfahren` ist deshalb Teil des Schluessels der
-- Vergleichbarkeit — Vektoren zweier Verfahren duerfen nie verglichen werden.
CREATE TABLE IF NOT EXISTS sicht_merkmal (
  merkmal_id   TEXT PRIMARY KEY,
  aufnahme_id  TEXT NOT NULL,
  anker        TEXT NOT NULL,
  verfahren    TEXT NOT NULL,
  dimension    INTEGER NOT NULL,
  vektor       TEXT NOT NULL,
  rahmen_hash  TEXT,
  erzeugt_am   REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS sicht_merkmal_aufnahme ON sicht_merkmal(aufnahme_id);
CREATE INDEX IF NOT EXISTS sicht_merkmal_verfahren ON sicht_merkmal(verfahren);

-- Ebene 2: WAS HAT DIE WAHRNEHMUNG DARAUS GEMACHT.
-- Revidierbar: eine neue Zeile loest die alte ab (`abgeloest_von`), statt sie
-- zu ueberschreiben. So bleibt die Kette lesbar, und „warum glaubte es das
-- damals" ist beantwortbar.
CREATE TABLE IF NOT EXISTS sicht_hypothese (
  hypothese_id  TEXT PRIMARY KEY,
  aufnahme_id   TEXT NOT NULL,
  anker         TEXT NOT NULL,
  art           TEXT NOT NULL,
  -- ⭐⭐ F57, mechanisch: mengenwertige Lesarten
  -- [{"lesart":..., "p":..., "aus":[evidenz_id,...]}, ...].
  -- Eine Kaskadenstufe darf die Gewichte verschieben, aber keine Lesart
  -- entfernen — siehe verengen(). In einer vierstufigen Kaskade ist ein
  -- frueher Ausschluss an vier Stellen nicht mehr einholbar.
  lesarten      TEXT NOT NULL,
  lesarten_geschlossen INTEGER NOT NULL DEFAULT 0,
  stuetzende_evidenz    TEXT NOT NULL DEFAULT '[]',
  widersprechende_evidenz TEXT NOT NULL DEFAULT '[]',
  bestand_stuetze       TEXT NOT NULL DEFAULT '[]',
  sensor_praezision     REAL,
  prior_praezision      REAL,
  kontext_verstaerkung  REAL,
  -- Anteil der Stuetzung, der aus dem Bestand statt aus dem Bild kommt.
  -- NR-RET-014: ein starker Prior kann schwache Sensorik dominieren und die
  -- Trefferquote heben, waehrend er falsche Vorannahmen mit durchwinkt.
  -- Deshalb als Zahl gefuehrt und nicht als Gefuehl.
  prior_dominanz        REAL,
  zuversicht    REAL,
  zustand       TEXT NOT NULL,
  revision      INTEGER NOT NULL DEFAULT 1,
  vorgaenger_id TEXT,
  abgeloest_von TEXT,
  erzeugt_am    REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS sicht_hypothese_aufnahme ON sicht_hypothese(aufnahme_id);
CREATE INDEX IF NOT EXISTS sicht_hypothese_offen
  ON sicht_hypothese(abgeloest_von) WHERE abgeloest_von IS NULL;

-- Ebene 3a: das persistente Wahrnehmungsobjekt.
-- ⭐ Die stabile Kennung ist der ganze Punkt (F27): „ein persistierendes
-- PerceptualObject mit Wiedererkennung ueber Bilder hinweg — nicht eine
-- Bildunterschrift". `semantische_identitaet` darf NULL sein und darf sich
-- aendern, ohne dass `objekt_id` sich aendert: Spurtreue und Benennung sind
-- zwei Dinge (Architektur, Abschnitt 6: „a dog incorrectly labelled teddy
-- bear can remain the same entity while its type hypothesis changes").
CREATE TABLE IF NOT EXISTS sicht_weltobjekt (
  objekt_id     TEXT PRIMARY KEY,
  quelle_id     TEXT NOT NULL,
  semantische_identitaet TEXT,
  erst_aufnahme_id TEXT NOT NULL,
  erst_gesehen_am  REAL NOT NULL,
  vorgaenger_id TEXT,
  teilung_von   TEXT,
  verschmelzung_von TEXT,
  provenienz    TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS sicht_weltobjekt_quelle ON sicht_weltobjekt(quelle_id);

-- Ebene 3b: WAS HAT DIE ENTITAET GEGLAUBT — datiert.
-- Jeder Stand ist eine eigene Zeile mit Gueltigkeitsfenster. gueltig_bis IS
-- NULL heisst „gilt jetzt". Ein UPDATE gibt es nur auf gueltig_bis, also nur
-- auf das Schliessen eines Fensters — der Inhalt eines Standes wird nie
-- veraendert.
CREATE TABLE IF NOT EXISTS sicht_weltobjekt_stand (
  stand_id      TEXT PRIMARY KEY,
  objekt_id     TEXT NOT NULL,
  gueltig_ab    REAL NOT NULL,
  gueltig_bis   REAL,
  sichtbarkeit  TEXT NOT NULL,
  -- Nicht schmueckend: der Grund unterscheidet „VERDECKT, weil eine Kiste
  -- davor steht" von „VERDECKT, weil wir es annehmen". Ohne Grund ist ein
  -- Sichtbarkeitszustand eine Behauptung.
  sichtbarkeit_grund TEXT,
  raum_zustand  TEXT,
  merkmale_mit_evidenz TEXT NOT NULL DEFAULT '[]',
  beziehungen_mit_evidenz TEXT NOT NULL DEFAULT '[]',
  letzte_positive_evidenz_epoche INTEGER,
  letzte_explizit_negative_epoche INTEGER,
  ungewissheit  REAL,
  stuetzende_hypothese_id TEXT,
  aufnahme_id   TEXT,
  turn_id       TEXT,
  causal_id     TEXT,
  erzeugt_am    REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS sicht_stand_objekt ON sicht_weltobjekt_stand(objekt_id);
CREATE INDEX IF NOT EXISTS sicht_stand_jetzt
  ON sicht_weltobjekt_stand(objekt_id) WHERE gueltig_bis IS NULL;

-- Die Zuordnungsentscheidung — getrennt vom Ergebnis.
-- ⭐⭐ Warum eine eigene Tabelle und nicht ein Feld am Objekt: die Frage „ist
-- das dieselbe Tasse?" hat eine Antwort UND eine Begruendung UND eine
-- Sicherheit, und die drei muessen einzeln pruefbar sein. Wer nur das
-- Ergebnis speichert, kann eine falsche Wiedererkennung spaeter nicht von
-- einer richtigen unterscheiden.
CREATE TABLE IF NOT EXISTS sicht_zuordnung (
  zuordnung_id  TEXT PRIMARY KEY,
  aufnahme_id   TEXT NOT NULL,
  anker         TEXT NOT NULL,
  objekt_id     TEXT,
  entscheidung  TEXT NOT NULL,
  begruendung   TEXT NOT NULL,
  aehnlichkeit  REAL,
  abstand_zum_zweiten REAL,
  verfahren     TEXT NOT NULL,
  verfahren_version TEXT,
  erzeugt_am    REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS sicht_zuordnung_aufnahme ON sicht_zuordnung(aufnahme_id);

-- Ebene 4: WAS KAM IN DEN ARBEITSRAUM.
-- ⚠️ NR-RET-017 „Broadcast is not use": diese Tabelle sagt NUR, was
-- angemeldet wurde und was gezuendet hat. Ob es etwas bewirkt hat, steht in
-- sicht_nutzung. Die Trennung ist der ganze Grund fuer zwei Tabellen.
CREATE TABLE IF NOT EXISTS sicht_arbeitsraum (
  eintrag_id    TEXT PRIMARY KEY,
  aufnahme_id   TEXT NOT NULL,
  kandidat_id   TEXT NOT NULL,
  objekt_id     TEXT,
  hypothese_id  TEXT,
  turn_id       TEXT,
  session_id    TEXT,
  angemeldet_am REAL NOT NULL,
  -- Die Zuendmerkmale aus der Architektur, Abschnitt „G": Neuheit,
  -- Vorhersagefehler, Ungewissheit, Zielbezug, Risiko.
  zuendungsgrund TEXT NOT NULL DEFAULT '{}',
  zuendung      INTEGER NOT NULL DEFAULT 0,
  broadcast_id  TEXT,
  abgelehnt_grund TEXT,
  entschieden_am REAL
);
CREATE INDEX IF NOT EXISTS sicht_arbeitsraum_turn ON sicht_arbeitsraum(turn_id);

-- Ebene 5: WAS HAT DIE ANTWORT GETRAGEN.
CREATE TABLE IF NOT EXISTS sicht_nutzung (
  nutzung_id    TEXT PRIMARY KEY,
  eintrag_id    TEXT,
  objekt_id     TEXT,
  evidenz_id    TEXT,
  turn_id       TEXT,
  causal_id     TEXT,
  nutzungsart   TEXT NOT NULL,
  beleg         TEXT,
  -- ⭐ Wer das festgestellt hat. „MECHANISCH" heisst: eine Regel hat es
  -- geprueft. Ein Modell, das behauptet, es habe etwas benutzt, ist kein
  -- Beleg — genau davor warnt NR-RET-017.
  festgestellt_von TEXT NOT NULL,
  erzeugt_am    REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS sicht_nutzung_turn ON sicht_nutzung(turn_id);

-- Nachschlagetabellen. Sie stehen in der Datenbank und nicht nur im Code,
-- damit eine Abfrage die Semantik mitverknuepfen kann, statt sie zu wissen.
CREATE TABLE IF NOT EXISTS sicht_sichtbarkeit (
  sichtbarkeit  TEXT PRIMARY KEY,
  vorlage_en    TEXT NOT NULL,
  messbar       INTEGER NOT NULL,
  belegt_abwesenheit INTEGER NOT NULL,
  zerfall       TEXT NOT NULL,
  warum         TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sicht_kaskade_stufe (
  stufe         TEXT PRIMARY KEY,
  rang          INTEGER NOT NULL,
  zweck         TEXT NOT NULL,
  fehlerfall    TEXT NOT NULL,
  aktiv         INTEGER NOT NULL DEFAULT 0,
  gemessen_ms   REAL,
  messgrundlage TEXT NOT NULL,
  quelle        TEXT
);
"""


def sicherstellen(db) -> None:
    """Tabellen anlegen und die Nachschlagewerte auffuellen.

    ⚠️ NUR BEIM START AUFRUFEN. `executescript` committet implizit und reisst
    eine laufende Transaktion auf — der Hausfehler `OperationalError: cannot
    commit - no transaction is active` (siehe die Fehler-Archaeologie in
    turn_lifecycle.py). Der Aufruf gehoert nach service.py:main(), nie in eine
    Funktion, die waehrend eines Zuges laeuft.
    """
    db.db.executescript(SCHEMA)
    for kennung, en, messbar, abwesend, zerfall, warum in LATTICE:
        db.db.execute(
            "INSERT INTO sicht_sichtbarkeit(sichtbarkeit,vorlage_en,messbar,"
            "belegt_abwesenheit,zerfall,warum) VALUES(?,?,?,?,?,?) "
            "ON CONFLICT(sichtbarkeit) DO UPDATE SET vorlage_en=excluded.vorlage_en,"
            "messbar=excluded.messbar,belegt_abwesenheit=excluded.belegt_abwesenheit,"
            "zerfall=excluded.zerfall,warum=excluded.warum",
            (kennung, en, messbar, abwesend, zerfall, warum))
    for s in KASKADE:
        db.db.execute(
            "INSERT INTO sicht_kaskade_stufe(stufe,rang,zweck,fehlerfall,aktiv,"
            "gemessen_ms,messgrundlage,quelle) VALUES(?,?,?,?,?,?,?,?) "
            "ON CONFLICT(stufe) DO UPDATE SET rang=excluded.rang,"
            "zweck=excluded.zweck,fehlerfall=excluded.fehlerfall,"
            "messgrundlage=excluded.messgrundlage,quelle=excluded.quelle",
            (s["stufe"], s["rang"], s["zweck"], s["fehlerfall"], s["aktiv"],
             s["gemessen_ms"], s["messgrundlage"], s["quelle"]))


# ── Der Weg zum Bild ────────────────────────────────────────────────

def eingang_pfad(user_id: str, kennung: str) -> Path:
    """Kennung -> Pfad im Eingangsordner, mit Durchstiegsschutz.

    ⭐ WARUM HIER UND NICHT IN dateien.py: dort gibt es `ausgabe_pfad()`, aber
    kein Gegenstueck fuer den Eingang — der Pfad erreicht Zero heute rein
    textuell in der Nachricht. Diese Schicht braucht ihn programmatisch. Die
    Funktion liegt hier statt in dateien.py, weil sie ein Bedarf DIESES Moduls
    ist; wandert sie spaeter hinueber, bleibt der Aufruf derselbe.

    ⚠️ Erst zusammenbauen und `resolve()`, DANN pruefen, ob die Basis unter
    den Eltern steht. Eine Pruefung auf der rohen Zeichenkette laesst sich mit
    `..` und mit Verweisen (Symlinks) austricksen; `resolve()` loest beides
    vorher auf.
    """
    basis = dateien.eingang_ordner(user_id).resolve()
    kandidat = (basis / kennung).resolve()
    if basis != kandidat and basis not in kandidat.parents:
        raise SichtFehler("Datei liegt nicht im Eingang")
    return kandidat


#: Magische Anfangsbytes -> Bildart.
#: ⚠️ NICHT die Dateiendung. Die Endung stammt aus dem Namen, den ein Mensch
#: getippt hat (dateien.py schneidet sie aus dem Anzeigenamen); sie sagt also
#: aus, was jemand GLAUBT, hochgeladen zu haben. Die ersten Bytes sagen, was
#: tatsaechlich in der Datei steht.
_MAGIE: tuple[tuple[bytes, str], ...] = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"BM", "image/bmp"),
    (b"II*\x00", "image/tiff"),
    (b"MM\x00*", "image/tiff"),
)


def bildart(pfad: Path) -> str | None:
    """Bildart aus den Anfangsbytes, oder None wenn es kein Bild ist.

    None ist ein gueltiges Ergebnis und kein Fehler: „das ist kein Bild" ist
    eine Messung, die der Aufrufer braucht, um NICHT zu analysieren.
    """
    try:
        with open(pfad, "rb") as fh:
            kopf = fh.read(16)
    except OSError:
        return None
    for magie, art in _MAGIE:
        if kopf.startswith(magie):
            return art
    # RIFF....WEBP
    if kopf[:4] == b"RIFF" and kopf[8:12] == b"WEBP":
        return "image/webp"
    return None


# ── Die Kaskadenstufe als austauschbares Glied ──────────────────────

class Stufe(Protocol):
    """Was eine Kaskadenstufe koennen muss.

    ⭐ Retina ist hier KEIN Organ, sondern eine Implementierung dieses
    Protokolls. Die naechste Stufe (NVIDIA-Vision, Gemini Flash) wird
    danebengestellt, nicht eingebaut. Deshalb steht in `sicht_aufnahme.stufe`
    ein Name und keine Annahme.
    """

    name: str

    def auslesen(self, roh: bytes, *, frage: str,
                 messauftrag: list[str]) -> dict:
        """Bild -> rohe Beobachtungen. `messauftrag` sind die Begriffe aus
        dem Bestand, gegen die ausdruecklich gemessen werden soll."""
        ...


class RetinaStufe:
    """Stufe 1: der lokale Retina-Dienst (CLIP-B/32, YOLOv8n, Tesseract,
    Haar+FER, DINOv2, CNN Retina v8), alles INT8 auf der CPU.

    ⚠️ WAS DIESE STUFE NICHT IST: ein Bildversteher. Sie liefert Kaesten,
    Begriffe, Text und Aehnlichkeiten. Der Sinn einer Szene ist der Fehlerfall
    der naechsten Stufe (NVIDIA_VISION), nicht dieser.

    ⚠️ ZUR LATENZ: B11-RETINA-VLM-KASKADE.md nennt „<15 ms Ziel". Das ist eine
    ZIELZAHL, keine Eigenschaft. Was diese Maschine liefert, steht in
    sicht_kaskade_stufe.gemessen_ms und wird bei jedem Lauf in
    sicht_aufnahme.dauer_ms mitgeschrieben — dort steht die Wahrheit.
    """

    name = "RETINA_LOKAL"

    def __init__(self, grund: str | None = None, zeitgrenze: float = 120.0):
        # Der Dienst lauscht nur auf 127.0.0.1 (siehe
        # /etc/systemd/system/retina-lokal.service). Die Adresse ist
        # umstellbar, damit Tests einen Doppelgaenger vorschieben koennen,
        # ohne Modelle zu laden.
        self.grund = (grund or os.environ.get("SICHT_RETINA_URL")
                      or "http://127.0.0.1:8001").rstrip("/")
        self.zeitgrenze = zeitgrenze

    def _post(self, weg: str, nutzlast: dict) -> dict:
        daten = json.dumps(nutzlast).encode("utf-8")
        anfrage = urllib.request.Request(
            self.grund + weg, data=daten,
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(anfrage, timeout=self.zeitgrenze) as a:
                return json.loads(a.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise SichtFehler(
                f"Retina antwortete {exc.code} auf {weg}") from exc
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            # ⭐ Ausdruecklich KEIN stiller Rueckfall auf eine andere Stufe.
            # bahnen.py haelt dieselbe Regel: erschoepft ist eine Absage, kein
            # leiser Abstieg. Ein Rueckfall, den niemand sieht, macht aus
            # einer Stoerung eine schlechtere Antwort.
            raise SichtFehler(f"Retina nicht erreichbar: {exc}") from exc

    def auslesen(self, roh: bytes, *, frage: str,
                 messauftrag: list[str]) -> dict:
        import base64
        b64 = base64.b64encode(roh).decode("ascii")
        ergebnis = self._post("/v1/analyze",
                              {"image_base64": b64, "hint": frage or ""})
        # ⭐ HIER FLIESST DER ABRUF IN DIE MESSUNG. `messauftrag` sind die
        # Begriffe, die der Bestand fuer dieses Bild erwartet. /v1/score misst
        # jeden einzeln gegen das Bild — das ist der Unterschied zwischen
        # „was ist auf dem Bild" und „ist das, was wir zu wissen glauben,
        # hier noch zu sehen".
        #
        # ⚠️ Und es ist AUSDRUECKLICH kein Abwesenheitsbeweis. Ein niedriger
        # Wert heisst „nicht gemessen worden", nicht „nicht da". Was daraus
        # folgen darf, entscheidet allein das Lattice.
        if messauftrag:
            ergebnis["_messauftrag"] = self._post(
                "/v1/score", {"image_base64": b64, "phrases": messauftrag})
        return ergebnis

    def merkmal(self, roh: bytes, kasten: list[float] | None = None) -> dict:
        """Merkmalsvektor fuer die Wiedererkennung.

        ⭐ Muss ueber die Leitung gehen, weil der EntityOS-Behaelter kein
        numpy und kein Pillow hat (requirements.txt: PyJWT, fastapi, uvicorn,
        mcp — vier Pakete). Er kann ein Bild nicht dekodieren, also kann er
        auch keinen Vektor daraus bilden.
        """
        import base64
        nutzlast: dict[str, Any] = {
            "image_base64": base64.b64encode(roh).decode("ascii")}
        if kasten and len(kasten) == 4:
            nutzlast["box"] = [float(x) for x in kasten]
        return self._post("/lokal/merkmal", nutzlast)


# ── Schwellen ───────────────────────────────────────────────────────
#
# ⚠️ KEINE DIESER ZAHLEN IST VON MIR ERFUNDEN, und keine ist auf DIESEM
# Bestand kalibriert. Jede nennt ihre Herkunft. Wer sie aendert, muss die
# Herkunft mit aendern — eine Schwelle ohne Herkunft ist ein Gefuehl.

#: Kosinus-Schwellen der Wiedererkennung. Woertlich aus
#: research_entity/harness/reference/digital_retina_runtime.py
#: (Methode `classify`, CALIBRATION_VERSION 'mvc0-calibration-sandbox-v1').
#: Sie gelten fuer GENAU dieses Merkmalsverfahren; mit einem anderen Verfahren
#: sind sie bedeutungslos. Deshalb steht das Verfahren in jeder Zeile von
#: sicht_merkmal und sicht_zuordnung.
WIEDERERKANNT_SICHER = 0.985
WIEDERERKANNT_ZU_BESTAETIGEN = 0.96
#: Liegen die zwei besten Treffer naeher beieinander als das, ist die
#: Zuordnung mehrdeutig — und Mehrdeutigkeit ist ein eigener Ausgang, kein
#: Anlass, den Ersten zu nehmen.
MEHRDEUTIG_ABSTAND = 0.025

#: CLIP-Kosinus, ab dem ein Begriff als im Bild abgedeckt gilt. Retina
#: dokumentiert diesen Wert in api/main.py am /v1/score-Endpunkt:
#: „Practical coverage threshold is ~0.22 for 'a photo of {phrase}' prompts."
#: Das ist die Angabe des Herstellers dieser Messung, nicht meine Messung.
CLIP_ABGEDECKT = 0.22
#: ⚠️⚠️ Es gibt hier bewusst KEINE untere Schwelle, unter der ein Begriff als
#: abwesend gilt. Das waere die Verwechslung, die dieses ganze Modul
#: verhindern soll. Ein niedriger CLIP-Wert heisst: dieses Messgeraet hat den
#: Begriff nicht wiedergefunden. Ob der Gegenstand da ist, hat es nicht
#: gemessen und kann es nicht messen.

_STANDARD_ZERFALL = 0.02


def _jetzt() -> float:
    return time.time()


def _kennung() -> str:
    return uuid.uuid4().hex


def _kosinus(a: Iterable[float], b: Iterable[float]) -> float:
    av, bv = list(a), list(b)
    if len(av) != len(bv) or not av:
        return 0.0
    punkt = sum(x * y for x, y in zip(av, bv))
    na = math.sqrt(sum(x * x for x in av))
    nb = math.sqrt(sum(y * y for y in bv))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return punkt / (na * nb)


# ── Der Abruf VOR der Analyse ───────────────────────────────────────

def abruf(db, *, quelle_id: str, frage: str = "",
          grenze: int = 12) -> dict[str, Any]:
    """Was weiss der Bestand ueber das, was hier zu sehen sein koennte?

    ⭐⭐ Das ist die Rueckwaertsrichtung aus F27. Das Modell wird nicht
    gefragt „was ist auf dem Bild", sondern befragt im Licht dessen, was der
    Bestand schon weiss. Der Rueckgabewert `begriffe` geht als Messauftrag in
    die Stufe.

    Zwei Quellen, absichtlich in dieser Reihenfolge:
      1. Gegenstaende, die an DIESER Quelle schon einmal gesehen wurden. Das
         ist der spezifische Bestand und der eigentliche Sinn: dieselbe Tasse
         auf dem zweiten Foto soll wiedergefunden werden.
      2. Die Frage des Menschen, in Woerter zerlegt. Das ist der Zielbezug —
         wer nach der Leiter fragt, soll eine Messung zur Leiter bekommen.

    ⚠️ Der Abruf darf keine Evidenz erzeugen. Er sagt nur, WONACH gemessen
    wird. Was dabei herauskommt, ist die Messung — nicht die Erwartung.
    Architektur, Abschnitt 4, Regel 7: „world prior can change hypothesis
    probability but cannot mint evidence."
    """
    begriffe: list[str] = []
    bekannt: list[dict[str, Any]] = []
    for zeile in db.db.execute(
            "SELECT o.objekt_id, o.semantische_identitaet, s.sichtbarkeit, "
            "       s.letzte_positive_evidenz_epoche "
            "FROM sicht_weltobjekt o "
            "LEFT JOIN sicht_weltobjekt_stand s "
            "  ON s.objekt_id=o.objekt_id AND s.gueltig_bis IS NULL "
            "WHERE o.quelle_id=? ORDER BY o.erst_gesehen_am DESC LIMIT ?",
            (quelle_id, grenze)).fetchall():
        eintrag = dict(zeile)
        bekannt.append(eintrag)
        name = (eintrag.get("semantische_identitaet") or "").strip()
        if name and name not in begriffe:
            begriffe.append(name)

    for wort in (frage or "").replace(",", " ").split():
        wort = wort.strip("?!.:;\"'()").lower()
        # Kurze Woerter sind Fuellwoerter; CLIP misst sie als Rauschen und
        # jeder zusaetzliche Begriff kostet einen Textdurchlauf.
        if len(wort) >= 4 and wort not in begriffe:
            begriffe.append(wort)

    return {"begriffe": begriffe[:grenze], "bekannt": bekannt,
            "treffer": len(bekannt)}


# ── Ebene 1 schreiben ───────────────────────────────────────────────

def _evidenz_kennung(aufnahme_id: str, transformation: str, art: str,
                     raum: str | None, wert: str) -> str:
    """Kennung aus dem Inhalt, nicht aus dem Zufall.

    ⭐ Warum nicht uuid4: derselbe Lauf auf demselben Bild soll dieselben
    Kennungen erzeugen. Dann ist ein Wiederholungslauf idempotent (INSERT OR
    IGNORE) statt ein zweiter Satz Geisterzeilen. Das ist auch die
    Voraussetzung fuer den „deterministic replay contract", den die
    Architektur in Abschnitt 3 ausdruecklich als architektonisch und nicht als
    Protokollierung bezeichnet.
    """
    roh = "\x1f".join((aufnahme_id, transformation, art, raum or "-", wert))
    return hashlib.sha256(roh.encode("utf-8")).hexdigest()[:32]


def evidenz_buchen(db, *, aufnahme_id: str, quelle_id: str,
                   quelle_epoche: int, rohbezug_hash: str,
                   saetze: Iterable[dict]) -> list[str]:
    """Beobachtungen anhaengen. Unveraenderlich, siehe Ausloeser im Schema.

    Jeder Satz braucht: transformation, transformation_version,
    beobachtungsart, wert. Optional: raum_bezug, bottom_up_praezision,
    kalibrierung_ref.
    """
    jetzt = _jetzt()
    kennungen: list[str] = []
    for satz in saetze:
        wert = json.dumps(satz["wert"], sort_keys=True, ensure_ascii=False)
        raum = (json.dumps(satz["raum_bezug"], sort_keys=True)
                if satz.get("raum_bezug") else None)
        kid = _evidenz_kennung(aufnahme_id, satz["transformation"],
                               satz["beobachtungsart"], raum, wert)
        db.db.execute(
            "INSERT OR IGNORE INTO sicht_evidenz("
            "evidenz_id,aufnahme_id,quelle_id,quelle_epoche,aufnahme_zeit,"
            "eingang_zeit,rohbezug_hash,raum_bezug,transformation,"
            "transformation_version,beobachtungsart,wert,bottom_up_praezision,"
            "kalibrierung_ref,autoritaet,erzeugt_am) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,'NUR_BEOBACHTUNG',?)",
            (kid, aufnahme_id, quelle_id, quelle_epoche,
             satz.get("aufnahme_zeit"), jetzt, rohbezug_hash, raum,
             satz["transformation"], satz.get("transformation_version", "?"),
             satz["beobachtungsart"], wert,
             satz.get("bottom_up_praezision"),
             satz.get("kalibrierung_ref", "UNKALIBRIERT"), jetzt))
        kennungen.append(kid)
    return kennungen


# ── Ebene 2 schreiben und verengen ──────────────────────────────────

def hypothese_setzen(db, *, aufnahme_id: str, anker: str, art: str,
                     lesarten: list[dict], stuetzende_evidenz: list[str],
                     bestand_stuetze: list[str] | None = None,
                     sensor_praezision: float | None = None,
                     prior_praezision: float | None = None,
                     zustand: str = "VORLAEUFIG",
                     vorgaenger_id: str | None = None) -> str:
    """Eine Lesart-Menge anlegen.

    ⚠️ `lesarten` MUSS mehr als eine Moeglichkeit enthalten, sobald das Bild
    mehrdeutig ist — mindestens die gemessene und die offene. Eine
    einelementige Menge behauptet Gewissheit, die keine Messung hergibt.
    Deshalb haengt `sehen()` an jede Menge die Lesart `UNBEKANNT` an.
    """
    jetzt = _jetzt()
    hid = _kennung()
    gesamt = sum(max(0.0, float(l.get("p", 0.0))) for l in lesarten) or 1.0
    aus_bestand = sum(max(0.0, float(l.get("p", 0.0))) for l in lesarten
                      if l.get("herkunft") == "BESTAND")
    prior_dominanz = round(aus_bestand / gesamt, 6)
    beste = max((float(l.get("p", 0.0)) for l in lesarten), default=0.0)
    revision = 1
    if vorgaenger_id:
        alt = db.db.execute(
            "SELECT revision FROM sicht_hypothese WHERE hypothese_id=?",
            (vorgaenger_id,)).fetchone()
        revision = int(alt["revision"]) + 1 if alt else 1
        db.db.execute(
            "UPDATE sicht_hypothese SET abgeloest_von=? WHERE hypothese_id=?",
            (hid, vorgaenger_id))
    db.db.execute(
        "INSERT INTO sicht_hypothese(hypothese_id,aufnahme_id,anker,art,"
        "lesarten,lesarten_geschlossen,stuetzende_evidenz,"
        "widersprechende_evidenz,bestand_stuetze,sensor_praezision,"
        "prior_praezision,kontext_verstaerkung,prior_dominanz,zuversicht,"
        "zustand,revision,vorgaenger_id,abgeloest_von,erzeugt_am) "
        "VALUES(?,?,?,?,?,0,?,'[]',?,?,?,NULL,?,?,?,?,?,NULL,?)",
        (hid, aufnahme_id, anker, art,
         json.dumps(lesarten, ensure_ascii=False),
         json.dumps(stuetzende_evidenz),
         json.dumps(bestand_stuetze or []), sensor_praezision,
         prior_praezision, prior_dominanz, round(beste, 6), zustand,
         revision, vorgaenger_id, jetzt))
    return hid


def verengen(db, hypothese_id: str, neue_gewichte: dict[str, float], *,
             stufe: str) -> str:
    """Eine spaetere Kaskadenstufe verschiebt die Gewichte.

    ⭐⭐⭐ HIER STEHT F57, MECHANISCH. Der Auftrag lautet: jede Stufe verengt
    NUR wahrscheinlichkeitsbasiert, NIE zerstoerend — keine Stufe darf eine
    Lesart endgueltig unerreichbar machen. In B11-RETINA-VLM-KASKADE.md steht
    dazu woertlich: „Nicht gebaut in diesem Durchlauf — das ist ein Vertrag
    fuer die Kaskaden-Implementierung, nicht mechanisch erzwungen."

    Genau das ist hier nachgeholt: die Lesart-Menge der neuen Revision muss
    dieselbe sein wie die der alten. Wer eine Lesart weglassen will, bekommt
    eine Ausnahme statt eines stillen Verlusts. Eine Wahrscheinlichkeit von
    0.0 ist erlaubt — sie ist erreichbar, nur unwahrscheinlich; das
    Weglassen ist es nicht.

    ⚠️ WARUM DAS SO WICHTIG IST: in einer vierstufigen Kaskade ist ein frueher
    falscher Ausschluss an vier Stellen nicht mehr einholbar. Der Fehler
    faellt nicht auf, weil die spaeteren Stufen weiterhin plausibel arbeiten —
    nur eben nie mehr auf der richtigen Lesart.
    """
    zeile = db.db.execute(
        "SELECT * FROM sicht_hypothese WHERE hypothese_id=?",
        (hypothese_id,)).fetchone()
    if zeile is None:
        raise SichtFehler(f"Hypothese {hypothese_id} gibt es nicht")
    if zeile["abgeloest_von"]:
        raise SichtFehler("Hypothese ist bereits abgeloest — verenge die "
                          "juengste Revision, nicht eine alte")
    alt = json.loads(zeile["lesarten"])
    alte_menge = {l["lesart"] for l in alt}
    fehlend = alte_menge - set(neue_gewichte)
    if fehlend:
        raise SichtFehler(
            "F57: eine Stufe darf keine Lesart entfernen, nur ihr Gewicht "
            f"senken. Stufe {stufe} liess weg: {sorted(fehlend)}")
    neu = []
    for l in alt:
        kopie = dict(l)
        kopie["p"] = round(max(0.0, float(neue_gewichte[l["lesart"]])), 6)
        kopie["verengt_von"] = stufe
        neu.append(kopie)
    fremde = set(neue_gewichte) - alte_menge
    for name in sorted(fremde):
        # Eine Stufe DARF eine Lesart hinzufuegen — Verbreitern ist nicht
        # zerstoerend. Nur das Verengen ist es.
        neu.append({"lesart": name, "p": round(float(neue_gewichte[name]), 6),
                    "aus": [], "herkunft": stufe})
    return hypothese_setzen(
        db, aufnahme_id=zeile["aufnahme_id"], anker=zeile["anker"],
        art=zeile["art"], lesarten=neu,
        stuetzende_evidenz=json.loads(zeile["stuetzende_evidenz"]),
        bestand_stuetze=json.loads(zeile["bestand_stuetze"]),
        sensor_praezision=zeile["sensor_praezision"],
        prior_praezision=zeile["prior_praezision"],
        zustand=zeile["zustand"], vorgaenger_id=hypothese_id)


# ── Die Wiedererkennung ─────────────────────────────────────────────

def zuordnen(db, *, aufnahme_id: str, quelle_id: str, anker: str,
             vektor: list[float] | None, verfahren: str,
             verfahren_version: str = "") -> dict[str, Any]:
    """Ist das ein bekannter Gegenstand, ein neuer, oder wissen wir es nicht?

    ⭐⭐⭐ DIE WICHTIGSTE FUNKTION DIESES MODULS, und die mit der
    gefaehrlichsten Fehlerart. Wer einen Gegenstand nicht wiedererkennt, hat
    NICHT festgestellt, dass es ein neuer ist. Er kann verdeckt sein,
    angeschnitten, anders beleuchtet oder von hinten aufgenommen. Ein System,
    das bei jeder Unsicherheit eine neue Kennung vergibt, erzeugt genau die
    Geisterobjekte, vor denen NR-RET-013 warnt — und zwar unbemerkt, weil
    jede einzelne Entscheidung fuer sich plausibel aussieht.

    Deshalb vier Ausgaenge und nicht zwei:

        WIEDERERKANNT              hohe Aehnlichkeit, klarer Abstand zum
                                   Zweitbesten
        MEHRDEUTIG                 hohe Aehnlichkeit zu MEHREREN — das ist
                                   ein Befund, keine Panne, und darf nicht
                                   zugunsten des Ersten aufgeloest werden
        NEU_ANGELEGT               niedrige Aehnlichkeit zu ALLEM, und es gab
                                   ueberhaupt etwas zu vergleichen
        UNENTSCHIEDEN_NICHT_MESSBAR  es gab keinen Vektor, oder keinen
                                   Vergleichsbestand. Der Rueckfall. Hier
                                   wird NICHTS angelegt.

    ⚠️ Der letzte Ausgang ist der Grund, warum diese Funktion existiert. Ohne
    ihn muesste jeder Zweifel in einen der drei anderen fallen, und der
    bequemste waere NEU_ANGELEGT.

    ⚠️ ZUM VERFAHREN: der heute gelieferte Vektor ist ein Bildpunktmerkmal
    (retina-mvc0-pixel-v1) — Farbe, Helligkeit, Kanten, Miniaturbild. Er
    erkennt Beinahe-Duplikate zuverlaessig und denselben Gegenstand vor
    anderem Hintergrund NICHT. Das ist eine bekannte, benannte Luecke, keine
    stille: DINOv2-small liegt als INT8-Netz bereit und waere der Aufstieg.
    Wer ihn baut, vergibt eine NEUE `verfahren`-Kennung — Vektoren zweier
    Verfahren duerfen nie verglichen werden, sonst ist die Aehnlichkeit eine
    Zahl ohne Bedeutung.
    """
    jetzt = _jetzt()
    zid = _kennung()

    def buchen(objekt_id, entscheidung, begruendung, aehnlich, abstand):
        db.db.execute(
            "INSERT INTO sicht_zuordnung(zuordnung_id,aufnahme_id,anker,"
            "objekt_id,entscheidung,begruendung,aehnlichkeit,"
            "abstand_zum_zweiten,verfahren,verfahren_version,erzeugt_am) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (zid, aufnahme_id, anker, objekt_id, entscheidung, begruendung,
             aehnlich, abstand, verfahren, verfahren_version, jetzt))
        return {"zuordnung_id": zid, "objekt_id": objekt_id,
                "entscheidung": entscheidung, "begruendung": begruendung,
                "aehnlichkeit": aehnlich, "abstand_zum_zweiten": abstand,
                "verfahren": verfahren}

    if not vektor:
        return buchen(None, "UNENTSCHIEDEN_NICHT_MESSBAR",
                      "Kein Merkmalsvektor vorhanden — es wurde nichts "
                      "gemessen, also wird auch nichts geschlossen.",
                      None, None)

    # Nur Vektoren DESSELBEN Verfahrens und DERSELBEN Quelle. Die Quelle
    # begrenzt den Vergleich auf das, was ueberhaupt dieselbe Szene sein
    # kann; ohne diese Grenze waechst die Verwechslungsgefahr mit jedem
    # Bild, das je gesehen wurde.
    kandidaten: list[tuple[float, str]] = []
    for zeile in db.db.execute(
            "SELECT m.vektor, z.objekt_id FROM sicht_merkmal m "
            "JOIN sicht_zuordnung z ON z.aufnahme_id=m.aufnahme_id "
            "                       AND z.anker=m.anker "
            "JOIN sicht_weltobjekt o ON o.objekt_id=z.objekt_id "
            "WHERE m.verfahren=? AND o.quelle_id=? AND z.objekt_id IS NOT NULL",
            (verfahren, quelle_id)).fetchall():
        kandidaten.append((_kosinus(vektor, json.loads(zeile["vektor"])),
                           zeile["objekt_id"]))

    if not kandidaten:
        return buchen(None, "UNENTSCHIEDEN_NICHT_MESSBAR",
                      "Kein Vergleichsbestand fuer dieses Verfahren an dieser "
                      "Quelle. Der erste Gegenstand ist nicht 'neu' — er ist "
                      "unvergleichbar; das Anlegen entscheidet der Aufrufer.",
                      None, None)

    kandidaten.sort(key=lambda x: (-x[0], x[1]))
    beste, objekt_id = kandidaten[0]
    zweite = kandidaten[1][0] if len(kandidaten) > 1 else -1.0
    abstand = round(beste - zweite, 6)

    if beste >= WIEDERERKANNT_ZU_BESTAETIGEN and abstand < MEHRDEUTIG_ABSTAND:
        return buchen(None, "MEHRDEUTIG",
                      f"Zwei Gegenstaende liegen naeher als "
                      f"{MEHRDEUTIG_ABSTAND} beieinander ({beste:.4f} vs "
                      f"{zweite:.4f}). Den Ersten zu nehmen waere geraten.",
                      round(beste, 6), abstand)
    if beste >= WIEDERERKANNT_SICHER:
        return buchen(objekt_id, "WIEDERERKANNT",
                      f"Aehnlichkeit {beste:.4f} ueber "
                      f"{WIEDERERKANNT_SICHER} bei klarem Abstand.",
                      round(beste, 6), abstand)
    if beste >= WIEDERERKANNT_ZU_BESTAETIGEN:
        return buchen(objekt_id, "WIEDERERKANNT_ZU_BESTAETIGEN",
                      f"Aehnlichkeit {beste:.4f} zwischen "
                      f"{WIEDERERKANNT_ZU_BESTAETIGEN} und "
                      f"{WIEDERERKANNT_SICHER}: wahrscheinlich derselbe, "
                      f"aber der Glaube bleibt SICHTBAR_UNSICHER.",
                      round(beste, 6), abstand)
    return buchen(None, "NEU_ANGELEGT",
                  f"Beste Aehnlichkeit im Bestand nur {beste:.4f}, unter "
                  f"{WIEDERERKANNT_ZU_BESTAETIGEN}. Verglichen wurde gegen "
                  f"{len(kandidaten)} bekannte Gegenstaende.",
                  round(beste, 6), abstand)


def objekt_anlegen(db, *, quelle_id: str, aufnahme_id: str,
                   semantische_identitaet: str | None,
                   provenienz: dict | None = None) -> str:
    """Legt ein persistierendes Wahrnehmungsobjekt an und gibt die STABILE
    Kennung zurueck — die Kennung, unter der es auf jedem spaeteren Bild
    wiedergefunden werden soll."""
    oid = _kennung()
    db.db.execute(
        "INSERT INTO sicht_weltobjekt(objekt_id,quelle_id,"
        "semantische_identitaet,erst_aufnahme_id,erst_gesehen_am,provenienz) "
        "VALUES(?,?,?,?,?,?)",
        (oid, quelle_id, semantische_identitaet, aufnahme_id, _jetzt(),
         json.dumps(provenienz or {}, ensure_ascii=False)))
    return oid


# ── Ebene 3 schreiben ───────────────────────────────────────────────

def glauben_fortschreiben(db, *, objekt_id: str, sichtbarkeit: str,
                          grund: str, aufnahme_id: str | None = None,
                          hypothese_id: str | None = None,
                          raum_zustand: dict | None = None,
                          merkmale: list | None = None,
                          epoche: int | None = None,
                          ungewissheit: float | None = None,
                          turn_id: str | None = None,
                          causal_id: str | None = None) -> str:
    """Schliesst das alte Gueltigkeitsfenster und oeffnet ein neues.

    ⭐ „Datiert" heisst genau das: der alte Stand wird nicht ueberschrieben,
    sondern beendet. „Was glaubte die Entitaet am Dienstag um drei" ist damit
    eine Abfrage mit BETWEEN, keine Rekonstruktion aus Protokollen.

    ⚠️⚠️ ABWESEND_EXPLIZIT_NEGATIV kommt hier NICHT durch. Dieser Zustand hat
    eine eigene Tuer (abwesenheit_belegen), weil er der einzige ist, aus dem
    „der Gegenstand ist weg" folgen darf. Wuerde er hier durchgelassen,
    koennte irgendwann irgendein Aufrufer ihn aus einem Nichtfund ableiten —
    und der Fehler waere von aussen nicht mehr von einem echten Beleg zu
    unterscheiden.
    """
    if sichtbarkeit not in SICHTBARKEITEN:
        raise SichtFehler(f"Unbekannter Sichtbarkeitszustand: {sichtbarkeit}")
    if sichtbarkeit in BELEGT_ABWESENHEIT:
        raise SichtFehler(
            "ABWESEND_EXPLIZIT_NEGATIV wird nur von abwesenheit_belegen() "
            "geschrieben — ein Nichtfund ist kein Abwesenheitsbeleg")
    return _stand_schreiben(
        db, objekt_id=objekt_id, sichtbarkeit=sichtbarkeit, grund=grund,
        aufnahme_id=aufnahme_id, hypothese_id=hypothese_id,
        raum_zustand=raum_zustand, merkmale=merkmale, epoche=epoche,
        ungewissheit=ungewissheit, turn_id=turn_id, causal_id=causal_id,
        negativ_epoche=None)


def abwesenheit_belegen(db, *, objekt_id: str, beleg: str,
                        aufnahme_id: str, epoche: int,
                        turn_id: str | None = None,
                        causal_id: str | None = None) -> str:
    """Die EINZIGE Tuer zu ABWESEND_EXPLIZIT_NEGATIV.

    ⭐⭐ Der Aufrufer muss einen Beleg mitliefern — eine Beschreibung, WORAUS
    die Abwesenheit folgt. Zulaessig ist etwa: „freie, scharfe Sicht auf den
    Tisch, auf dem die Tasse stand, Tasse nicht darauf". NICHT zulaessig und
    hier auch nicht formulierbar ist: „der Detektor hat nichts gemeldet".

    ⚠️ Die Funktion prueft den Beleg nicht auf Wahrheit — das kann sie nicht.
    Sie erzwingt nur, dass es ihn GIBT und dass er in der Datenbank steht.
    Damit ist eine falsche Abwesenheitsbehauptung spaeter auffindbar und
    zurechenbar, statt als anonymer Zustandswechsel unterzugehen. Das ist der
    ganze Unterschied zwischen einem Fehler und einem Geist.

    Der Zerfall dieses Zustands ist SCHNELL (siehe LATTICE) — Architektur,
    Abschnitt 4, Regel 3: ausdrueckliche Gegen-Evidenz senkt den
    Sichtbarkeitsglauben schnell, blosses Nichtbeobachten nur langsam.
    """
    if not (beleg or "").strip():
        raise SichtFehler(
            "Abwesenheit braucht einen Beleg. Ohne Beleg ist es ein "
            "Nichtfund, und ein Nichtfund gehoert nach UNBEKANNT.")
    return _stand_schreiben(
        db, objekt_id=objekt_id, sichtbarkeit="ABWESEND_EXPLIZIT_NEGATIV",
        grund=beleg, aufnahme_id=aufnahme_id, hypothese_id=None,
        raum_zustand=None, merkmale=None, epoche=None, ungewissheit=0.1,
        turn_id=turn_id, causal_id=causal_id, negativ_epoche=epoche)


def _stand_schreiben(db, *, objekt_id, sichtbarkeit, grund, aufnahme_id,
                     hypothese_id, raum_zustand, merkmale, epoche,
                     ungewissheit, turn_id, causal_id,
                     negativ_epoche) -> str:
    jetzt = _jetzt()
    vorher = db.db.execute(
        "SELECT * FROM sicht_weltobjekt_stand WHERE objekt_id=? "
        "AND gueltig_bis IS NULL", (objekt_id,)).fetchone()
    if vorher is not None:
        db.db.execute(
            "UPDATE sicht_weltobjekt_stand SET gueltig_bis=? WHERE stand_id=?",
            (jetzt, vorher["stand_id"]))
    # Die letzte positive Evidenz wird MITGENOMMEN, wenn dieser Stand keine
    # neue hat. Sonst sieht ein Gegenstand, der einmal nicht beobachtet wurde,
    # aus, als waere er nie beobachtet worden.
    letzte_positive = epoche
    if letzte_positive is None and vorher is not None:
        letzte_positive = vorher["letzte_positive_evidenz_epoche"]
    letzte_negative = negativ_epoche
    if letzte_negative is None and vorher is not None:
        letzte_negative = vorher["letzte_explizit_negative_epoche"]
    sid = _kennung()
    db.db.execute(
        "INSERT INTO sicht_weltobjekt_stand(stand_id,objekt_id,gueltig_ab,"
        "gueltig_bis,sichtbarkeit,sichtbarkeit_grund,raum_zustand,"
        "merkmale_mit_evidenz,beziehungen_mit_evidenz,"
        "letzte_positive_evidenz_epoche,letzte_explizit_negative_epoche,"
        "ungewissheit,stuetzende_hypothese_id,aufnahme_id,turn_id,causal_id,"
        "erzeugt_am) VALUES(?,?,?,NULL,?,?,?,?,'[]',?,?,?,?,?,?,?,?)",
        (sid, objekt_id, jetzt, sichtbarkeit, grund,
         json.dumps(raum_zustand) if raum_zustand else None,
         json.dumps(merkmale or [], ensure_ascii=False),
         letzte_positive, letzte_negative, ungewissheit, hypothese_id,
         aufnahme_id, turn_id, causal_id, jetzt))
    return sid


# ── Der Gesamtlauf ──────────────────────────────────────────────────

#: Deckel fuer die Zahl der Kaesten, zu denen ein eigener Merkmalsvektor
#: geholt wird. Jeder Vektor ist ein eigener HTTP-Aufruf mit Bilddekodierung.
#: 8 deckt jede uebliche Szene ab; ein Bild mit 40 Kaesten wuerde sonst 40
#: Aufrufe ausloesen und den Zug ausbremsen, ohne mehr zu sagen.
MERKMALE_JE_BILD = 8


def sehen(db, *, user_id: str, datei_id: str | None = None,
          pfad: str | Path | None = None, frage: str = "",
          turn_id: str | None = None, causal_id: str | None = None,
          session_id: str | None = None, stufe: Stufe | None = None,
          quelle_id: str | None = None) -> dict[str, Any]:
    """Ein Bild ansehen und alle fuenf Ebenen dabei getrennt aufzeichnen.

    Ablauf, und jeder Schritt schreibt in genau EINE Ebene:

        1. Abruf     was weiss der Bestand? -> geht als Messauftrag hinein
        2. Auslesen  Stufe liefert Beobachtungen
        3. Ebene 1   jede Beobachtung als unveraenderliche Evidenzzeile
        4. Merkmale  Vektoren fuer die Wiedererkennung
        5. Zuordnung ist das bekannt? (vier Ausgaenge, siehe zuordnen)
        6. Ebene 2   Lesart-Mengen ueber der Evidenz
        7. Ebene 3   datierte Glaubensstaende

    Die Ebenen 4 (Arbeitsraum) und 5 (Nutzung) schreibt NICHT diese Funktion.
    Sie gehoeren dem Zug, nicht dem Bild: ob ein Wahrnehmungsobjekt in den
    Arbeitsraum kam und ob es die Antwort getragen hat, entscheidet sich
    spaeter. arbeitsraum_anmelden() und nutzung_pruefen() sind dafuer da.

    Rueckgabe ist eine Zusammenfassung fuer den Aufrufer — die Wahrheit steht
    in den Tabellen, nicht hier.
    """
    stufe = stufe or RetinaStufe()
    if pfad is None:
        if not datei_id:
            raise SichtFehler("Weder datei_id noch pfad angegeben")
        pfad = eingang_pfad(user_id, datei_id)
    pfad = Path(pfad)
    if not pfad.is_file():
        raise SichtFehler("Datei gibt es nicht")

    art = bildart(pfad)
    if art is None:
        # ⭐ Ein ehrliches „das ist kein Bild" statt einer Analyse von
        # Zufallsbytes. Retina wuerde auch aus einem PDF etwas machen; das
        # waere Evidenz ueber nichts.
        raise SichtFehler("Das ist kein Bild (Anfangsbytes passen zu keiner "
                          "bekannten Bildart)")

    roh = pfad.read_bytes()
    bild_hash = hashlib.sha256(roh).hexdigest()
    # ⭐ Die Quelle ist NICHT die Datei. Zwei Fotos derselben Werkbank sind
    # zwei Dateien, aber eine Quelle — und nur innerhalb einer Quelle ergibt
    # Wiedererkennung Sinn. Ohne ausdrueckliche Quelle faellt sie auf den
    # Menschen zurueck: besser als nichts, aber grob, und darum benannt.
    quelle_id = quelle_id or f"eingang:{user_id}"
    epoche = int(_jetzt())

    aufnahme_id = _kennung()
    begonnen = _jetzt()
    vor = abruf(db, quelle_id=quelle_id, frage=frage)
    db.db.execute(
        "INSERT INTO sicht_aufnahme(aufnahme_id,datei_id,quelle_id,"
        "quelle_klasse,bild_hash,user_id,turn_id,causal_id,session_id,stufe,"
        "abruf_kontext,abruf_treffer,ergebnis,begonnen_am) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,'LAEUFT',?)",
        (aufnahme_id, datei_id, quelle_id, "BILD", bild_hash, user_id,
         turn_id, causal_id, session_id, stufe.name,
         json.dumps(vor, ensure_ascii=False), vor["treffer"], begonnen))

    try:
        roh_ergebnis = stufe.auslesen(roh, frage=frage,
                                      messauftrag=vor["begriffe"])
    except SichtFehler as exc:
        db.db.execute(
            "UPDATE sicht_aufnahme SET ergebnis='FEHLER',fehlergrund=?,"
            "beendet_am=?,dauer_ms=? WHERE aufnahme_id=?",
            (str(exc), _jetzt(), (_jetzt() - begonnen) * 1000, aufnahme_id))
        raise

    dauer_ms = (_jetzt() - begonnen) * 1000
    bild = roh_ergebnis.get("image") or {}
    db.db.execute(
        "UPDATE sicht_aufnahme SET breite=?,hoehe=?,dauer_ms=?,"
        "ergebnis='ERFOLG',beendet_am=? WHERE aufnahme_id=?",
        (bild.get("width"), bild.get("height"), dauer_ms, _jetzt(),
         aufnahme_id))

    saetze = _evidenzsaetze(roh_ergebnis, stufe.name)
    evidenz_ids = evidenz_buchen(
        db, aufnahme_id=aufnahme_id, quelle_id=quelle_id,
        quelle_epoche=epoche, rohbezug_hash=bild_hash, saetze=saetze)
    nach_art: dict[str, list[str]] = {}
    for satz, kid in zip(saetze, evidenz_ids):
        nach_art.setdefault(satz["beobachtungsart"], []).append(kid)

    ergebnis = {
        "aufnahme_id": aufnahme_id, "quelle_id": quelle_id,
        "stufe": stufe.name, "dauer_ms": round(dauer_ms, 1),
        "bildart": art, "bild_hash": bild_hash,
        "abruf": vor, "evidenz": len(evidenz_ids),
        "objekte": [], "hypothesen": [], "zuordnungen": [],
    }

    # --- Anker bilden. Ganzbild immer, dazu die erkannten Kaesten.
    anker_liste: list[tuple[str, list[float] | None, dict]] = [
        ("GANZBILD", None, {})]
    for i, obj in enumerate(roh_ergebnis.get("objects") or []):
        if i >= MERKMALE_JE_BILD:
            break
        kasten = obj.get("box")
        if not kasten or len(kasten) != 4:
            continue
        anker_liste.append((f"kasten:{i}", [float(x) for x in kasten], obj))

    merkmal_verfahren = None
    for anker, kasten, obj in anker_liste:
        vektor = None
        try:
            m = stufe.merkmal(roh, kasten) if hasattr(stufe, "merkmal") else None
        except SichtFehler:
            # ⚠️ Ein fehlender Vektor ist kein Fehlschlag des Sehens. Er
            # fuehrt zu UNENTSCHIEDEN_NICHT_MESSBAR — genau dafuer gibt es
            # den Ausgang. Die Analyse deswegen abzubrechen waere schlimmer:
            # dann ginge auch die Evidenz verloren, die schon da ist.
            m = None
        if m:
            vektor = m["vektor"]
            merkmal_verfahren = m["merkmal_version"]
            db.db.execute(
                "INSERT INTO sicht_merkmal(merkmal_id,aufnahme_id,anker,"
                "verfahren,dimension,vektor,rahmen_hash,erzeugt_am) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (_kennung(), aufnahme_id, anker, m["merkmal_version"],
                 m["dimension"], json.dumps(vektor), m.get("rahmen_hash"),
                 _jetzt()))

        z = zuordnen(db, aufnahme_id=aufnahme_id, quelle_id=quelle_id,
                     anker=anker, vektor=vektor,
                     verfahren=merkmal_verfahren or "KEIN_VERFAHREN",
                     verfahren_version=merkmal_verfahren or "")
        ergebnis["zuordnungen"].append(z)

        lesarten, stuetzen = _lesarten(roh_ergebnis, obj, anker,
                                       nach_art, vor)
        hid = hypothese_setzen(
            db, aufnahme_id=aufnahme_id, anker=anker, art="TYP",
            lesarten=lesarten, stuetzende_evidenz=stuetzen,
            bestand_stuetze=[b["objekt_id"] for b in vor["bekannt"]],
            sensor_praezision=max((l["p"] for l in lesarten), default=0.0),
            zustand=("VORLAEUFIG" if z["entscheidung"] != "MEHRDEUTIG"
                     else "KONFLIKT"))
        ergebnis["hypothesen"].append(hid)

        objekt_id = z["objekt_id"]
        if objekt_id is None and z["entscheidung"] == "NEU_ANGELEGT":
            objekt_id = objekt_anlegen(
                db, quelle_id=quelle_id, aufnahme_id=aufnahme_id,
                semantische_identitaet=lesarten[0]["lesart"],
                provenienz={"stufe": stufe.name, "anker": anker,
                            "datei_id": datei_id})
            db.db.execute(
                "UPDATE sicht_zuordnung SET objekt_id=? WHERE zuordnung_id=?",
                (objekt_id, z["zuordnung_id"]))
        elif objekt_id is None and z["entscheidung"] == "UNENTSCHIEDEN_NICHT_MESSBAR":
            # ⭐⭐ Der erste Gegenstand an einer Quelle hat nichts, womit er
            # verglichen werden koennte. Ihn deswegen NICHT anzulegen waere
            # falsch — aber er wird angelegt mit dem ausdruecklichen Vermerk,
            # dass die Zuordnung nicht gemessen, sondern mangels Bestand
            # entfallen ist. Der Unterschied steht in der Zuordnungszeile und
            # ist spaeter lesbar.
            objekt_id = objekt_anlegen(
                db, quelle_id=quelle_id, aufnahme_id=aufnahme_id,
                semantische_identitaet=lesarten[0]["lesart"],
                provenienz={"stufe": stufe.name, "anker": anker,
                            "datei_id": datei_id,
                            "zuordnung": "ohne Vergleichsbestand"})
            db.db.execute(
                "UPDATE sicht_zuordnung SET objekt_id=? WHERE zuordnung_id=?",
                (objekt_id, z["zuordnung_id"]))

        if objekt_id:
            sichtbar = ("SICHTBAR_BESTAETIGT"
                        if z["entscheidung"] == "WIEDERERKANNT"
                        or (lesarten[0]["p"] >= CLIP_ABGEDECKT and kasten)
                        else "SICHTBAR_UNSICHER")
            glauben_fortschreiben(
                db, objekt_id=objekt_id, sichtbarkeit=sichtbar,
                grund=f"{stufe.name}: {z['entscheidung']} — {z['begruendung']}",
                aufnahme_id=aufnahme_id, hypothese_id=hid,
                raum_zustand={"kasten": kasten} if kasten else None,
                merkmale=[{"lesart": l["lesart"], "p": l["p"],
                           "aus": l.get("aus", [])} for l in lesarten[:5]],
                epoche=epoche,
                ungewissheit=round(1.0 - lesarten[0]["p"], 6),
                turn_id=turn_id, causal_id=causal_id)
            ergebnis["objekte"].append(
                {"objekt_id": objekt_id, "anker": anker,
                 "identitaet": lesarten[0]["lesart"],
                 "sichtbarkeit": sichtbar,
                 "entscheidung": z["entscheidung"]})

    # --- Bekannte Gegenstaende, die HEUTE NICHT auftauchten.
    # ⚠️⚠️ HIER WIRD DIE VERWECHSLUNG VERHINDERT. Diese Gegenstaende bekommen
    # UNBEKANNT, nicht ABWESEND. Sie waren nicht im Bild — das ist alles, was
    # gemessen wurde. Ob sie verdeckt waren, ausserhalb des Ausschnitts oder
    # tatsaechlich weg, hat niemand gemessen, und keine dieser drei
    # Moeglichkeiten darf hier ausgeschlossen werden.
    gesehen = {o["objekt_id"] for o in ergebnis["objekte"]}
    ergebnis["nicht_beobachtet"] = []
    for b in vor["bekannt"]:
        if b["objekt_id"] in gesehen:
            continue
        glauben_fortschreiben(
            db, objekt_id=b["objekt_id"], sichtbarkeit="UNBEKANNT",
            grund=("Auf dieser Aufnahme nicht wiedergefunden. Das ist ein "
                   "Nichtfund und KEIN Abwesenheitsbeleg — verdeckt, "
                   "ausserhalb des Ausschnitts und tatsaechlich weg sind "
                   "damit alle drei weiterhin moeglich."),
            aufnahme_id=aufnahme_id, turn_id=turn_id, causal_id=causal_id,
            ungewissheit=None)
        ergebnis["nicht_beobachtet"].append(b["objekt_id"])

    return ergebnis


def _begriff(s: dict) -> str:
    """Den gemessenen Begriff aus einer /v1/score-Zeile holen.

    GEMESSEN 2026-08-21: Retina dokumentiert am Endpunkt die Form
    scores[i].phrase, liefert aber tatsaechlich scores[i].query. Der
    Unterschied faellt nicht auf -- beide Formen sind gueltiges JSON, und
    .get(phrase) gibt still None zurueck. Ein Begriff, der None ist, wuerde
    als Lesart None in der Datenbank landen und dort wie ein Messergebnis
    aussehen. Ein Formatbruch, der als Erfolg auftritt, ist die teuerste
    Sorte -- er wird erst bemerkt, wenn jemand die Daten glaubt.

    Beide Namen werden deshalb gelesen. Bewusst HIER und nicht durch eine
    Korrektur in /opt/digital-retina: jener Baum steht unter keiner
    Versionskontrolle, eine Aenderung dort waere fuer den naechsten Leser
    unsichtbar.
    """
    return str(s.get('phrase') or s.get('query') or '')

def _evidenzsaetze(r: dict, stufe: str) -> list[dict]:
    """Retina-Antwort -> Evidenzzeilen, eine je Beobachtung.

    ⭐ WARUM EINE ZEILE JE BEOBACHTUNG und nicht die ganze Antwort als ein
    Klumpen: NR-RET-011 haelt fest, dass die zusammenfassende Erzaehlung von
    frank_eye die kausale Koernung zerstoert — man sieht danach nicht mehr,
    welche Quelle welchen Glauben verursacht hat. Eine Zeile je Beobachtung
    ist die Umkehrung davon.

    ⚠️ `description` wird MITGESCHRIEBEN, aber als beobachtungsart FLIESSTEXT
    und mit `kalibrierung_ref='KEINE_ZAHL'`. Es ist die einzige Beobachtung
    ohne Praezisionszahl, und es ist genau das, was F27 als Ergebnis ablehnt.
    Als EVIDENZ ist sie zulaessig — jemand hat diesen Satz gesagt —, als
    Wahrheit nie. Wer sie als Wahrnehmungsobjekt speichert, hat „Bild ->
    Beschreibung" gebaut.
    """
    v = str(r.get("elapsed_ms") and stufe or stufe)
    saetze: list[dict] = [{
        "transformation": "BILDMASS", "transformation_version": v,
        "beobachtungsart": "BILDMASS",
        "wert": {"breite": (r.get("image") or {}).get("width"),
                 "hoehe": (r.get("image") or {}).get("height"),
                 "bildschirmfoto": bool(r.get("screenshot"))},
        "kalibrierung_ref": "EXAKT",
        "bottom_up_praezision": 1.0,
    }]
    for c in (r.get("concepts") or []):
        saetze.append({
            "transformation": "CLIP_B32", "transformation_version": v,
            "beobachtungsart": "KONZEPT",
            "wert": {"name": c.get("name"), "kategorie": c.get("category")},
            "bottom_up_praezision": float(c.get("score") or 0.0),
            "kalibrierung_ref": "CLIP_KOSINUS_UNKALIBRIERT"})
    for o in (r.get("objects") or []):
        saetze.append({
            "transformation": "YOLOV8N", "transformation_version": v,
            "beobachtungsart": "KASTEN",
            "wert": {"klasse": o.get("class") or o.get("cls")},
            "raum_bezug": {"kasten": o.get("box")},
            "bottom_up_praezision": float(o.get("confidence") or 0.0),
            "kalibrierung_ref": "YOLO_KONFIDENZ_UNKALIBRIERT"})
    text = (r.get("ocr_text") or "").strip()
    if text:
        saetze.append({
            "transformation": "TESSERACT", "transformation_version": v,
            "beobachtungsart": "TEXT", "wert": {"text": text},
            "kalibrierung_ref": "OCR_UNKALIBRIERT"})
    for f in (r.get("faces") or []):
        saetze.append({
            "transformation": "HAAR_FER", "transformation_version": v,
            "beobachtungsart": "GESICHT",
            "wert": {"stimmung": f.get("emotion")},
            "raum_bezug": {"kasten": f.get("box")},
            "kalibrierung_ref": "FER_UNKALIBRIERT"})
    for lo in (r.get("logos") or []):
        saetze.append({
            "transformation": "LOGO", "transformation_version": v,
            "beobachtungsart": "LOGO", "wert": {"name": lo},
            "kalibrierung_ref": "UNKALIBRIERT"})
    if r.get("description"):
        saetze.append({
            "transformation": "BESCHREIBUNG", "transformation_version": v,
            "beobachtungsart": "FLIESSTEXT",
            "wert": {"text": r["description"]},
            "kalibrierung_ref": "KEINE_ZAHL"})
    # ⭐ Der Messauftrag: das Ergebnis der Frage „ist das, was wir zu wissen
    # glauben, hier zu sehen?". Eigene Beobachtungsart, weil es die einzige
    # ist, deren FRAGE aus dem Bestand kam. Wer Prior-Dominanz nachrechnen
    # will, braucht genau diese Trennung.
    ma = r.get("_messauftrag") or {}
    for s in (ma.get("scores") or []):
        wert = float(s.get("score") or 0.0)
        saetze.append({
            "transformation": "CLIP_B32_MESSAUFTRAG",
            "transformation_version": v,
            "beobachtungsart": "MESSAUFTRAG",
            "wert": {"begriff": _begriff(s),
                     "abgedeckt": wert >= CLIP_ABGEDECKT,
                     # ⚠️ Ausdruecklich mitgeschrieben, damit niemand aus dem
                     # False oben eine Abwesenheit liest.
                     "bedeutung_bei_false":
                         "nicht wiedergefunden — keine Aussage ueber "
                         "Abwesenheit"},
            "bottom_up_praezision": wert,
            "kalibrierung_ref": f"CLIP_SCHWELLE_{CLIP_ABGEDECKT}"})
    return saetze


def _lesarten(r: dict, obj: dict, anker: str, nach_art: dict,
              vor: dict) -> tuple[list[dict], list[str]]:
    """Lesart-Menge fuer einen Anker bilden.

    ⭐ Die Menge enthaelt IMMER `UNBEKANNT`. Das ist kein Platzhalter: es ist
    die Lesart „nichts hiervon", und ohne sie behauptet jede Menge, sie sei
    erschoepfend. Sie ist auch die Lesart, auf die eine spaetere Kaskadenstufe
    Gewicht legen kann, ohne eine andere entfernen zu muessen (F57).
    """
    lesarten: list[dict] = []
    stuetzen: list[str] = []
    if obj:
        klasse = obj.get("class") or obj.get("cls") or "?"
        lesarten.append({"lesart": klasse,
                         "p": round(float(obj.get("confidence") or 0.0), 6),
                         "aus": nach_art.get("KASTEN", []),
                         "herkunft": "YOLOV8N"})
    for i, c in enumerate((r.get("concepts") or [])[:5]):
        lesarten.append({"lesart": c.get("name"),
                         "p": round(float(c.get("score") or 0.0), 6),
                         "aus": nach_art.get("KONZEPT", [])[i:i + 1],
                         "herkunft": "CLIP_B32"})
    for s in ((r.get("_messauftrag") or {}).get("scores") or []):
        lesarten.append({"lesart": _begriff(s),
                         "p": round(float(s.get("score") or 0.0), 6),
                         "aus": nach_art.get("MESSAUFTRAG", []),
                         # ⭐ Diese Herkunft ist es, die prior_dominanz
                         # berechenbar macht: sie sagt, welcher Teil der
                         # Stuetzung aus der Erwartung kam statt aus dem Bild.
                         "herkunft": "BESTAND"})
    if not lesarten:
        lesarten.append({"lesart": "UNBEKANNT", "p": 0.0, "aus": [],
                         "herkunft": "KEINE"})
    lesarten.sort(key=lambda l: -l["p"])
    lesarten.append({"lesart": "UNBEKANNT",
                     "p": round(max(0.0, 1.0 - lesarten[0]["p"]), 6),
                     "aus": [], "herkunft": "OFFENHEIT"})
    for l in lesarten:
        stuetzen.extend(l.get("aus") or [])
    return lesarten, sorted(set(stuetzen))


# ── Ebene 4: was kam in den Arbeitsraum ─────────────────────────────

def arbeitsraum_anmelden(db, *, aufnahme_id: str, turn_id: str | None,
                          session_id: str | None,
                          eintraege: Iterable[dict]) -> list[dict]:
    """Wahrnehmungsobjekte als Bewerber anmelden.

    ⚠️ ANMELDEN IST NICHT ZUENDEN. Diese Funktion schreibt nur, dass etwas zur
    Wahl stand. Ob es gewaehlt wurde, traegt zuendung_buchen() nach — und ob
    es gewirkt hat, steht in einer dritten Tabelle. Drei Tabellen fuer das,
    was umgangssprachlich „es kam in den Arbeitsraum" heisst, weil NR-RET-017
    genau diese drei Dinge auseinanderhaelt: *„A visual candidate reaching GWT
    does not establish that any receiver reconstructed it, used it causally,
    changed behavior or generated valid re-entry."*

    Die Zuendmerkmale stammen aus der Architektur, Abschnitt „G": Neuheit,
    Vorhersagefehler, Ungewissheit, Zielbezug, Risiko. Sie werden hier
    MITGESCHRIEBEN, nicht ausgewertet — die Auswahl trifft der bestehende
    Wettbewerb (clayverse/mistral_prestage/wettbewerb.py), und ein zweiter
    Auswahlmechanismus daneben waere genau das Organ, das die Zielarchitektur
    ablehnt.
    """
    jetzt = _jetzt()
    heraus = []
    for e in eintraege:
        eid = _kennung()
        db.db.execute(
            "INSERT INTO sicht_arbeitsraum(eintrag_id,aufnahme_id,"
            "kandidat_id,objekt_id,hypothese_id,turn_id,session_id,"
            "angemeldet_am,zuendungsgrund,zuendung) "
            "VALUES(?,?,?,?,?,?,?,?,?,0)",
            (eid, aufnahme_id, e["kandidat_id"], e.get("objekt_id"),
             e.get("hypothese_id"), turn_id, session_id, jetzt,
             json.dumps(e.get("zuendungsgrund") or {}, ensure_ascii=False)))
        heraus.append({"eintrag_id": eid, "kandidat_id": e["kandidat_id"]})
    return heraus


def zuendung_buchen(db, *, turn_id: str,
                    broadcast_ids: Iterable[str]) -> dict[str, int]:
    """Traegt nach, welche angemeldeten Bewerber tatsaechlich ausgestrahlt
    wurden.

    `broadcast_ids` ist die Auswahl der Vorstufe — in EntityOS das eine Feld,
    dessen Wirkung sichtbar ist. Was nicht darin steht, bekommt einen Grund
    und keine stille Null.
    """
    gewaehlt = {str(x) for x in broadcast_ids}
    jetzt = _jetzt()
    zu, ab = 0, 0
    for zeile in db.db.execute(
            "SELECT eintrag_id,kandidat_id FROM sicht_arbeitsraum "
            "WHERE turn_id=? AND entschieden_am IS NULL",
            (turn_id,)).fetchall():
        if zeile["kandidat_id"] in gewaehlt:
            db.db.execute(
                "UPDATE sicht_arbeitsraum SET zuendung=1,broadcast_id=?,"
                "entschieden_am=? WHERE eintrag_id=?",
                (zeile["kandidat_id"], jetzt, zeile["eintrag_id"]))
            zu += 1
        else:
            db.db.execute(
                "UPDATE sicht_arbeitsraum SET zuendung=0,"
                "abgelehnt_grund='nicht in broadcast_ids der Vorstufe',"
                "entschieden_am=? WHERE eintrag_id=?",
                (jetzt, zeile["eintrag_id"]))
            ab += 1
    return {"gezuendet": zu, "abgelehnt": ab}


# ── Ebene 5: was hat die Antwort getragen ───────────────────────────

def nutzung_pruefen(db, *, turn_id: str, antwort: str,
                    causal_id: str | None = None) -> list[dict]:
    """Mechanische Pruefung, ob ein ausgestrahltes Objekt die Antwort trug.

    ⭐⭐ MECHANISCH heisst: eine Regel schaut nach, ob die Benennung des
    Objekts woertlich in der Antwort vorkommt. Das ist ein schwacher, aber
    ehrlicher Test. Ein Modell zu fragen, ob es etwas benutzt hat, waere kein
    Beleg — es wuerde ja gerade das behaupten, was zu pruefen ist. Genau
    davor warnt NR-RET-017.

    ⚠️ WAS DIESER TEST NICHT KANN: er findet keine Umschreibung („das
    Werkzeug" statt „Bohrmaschine") und keine Nutzung, die die Antwort
    veraendert hat, ohne im Wortlaut zu erscheinen. Solche Faelle bekommen
    NICHT_NACHWEISBAR — nicht „nicht benutzt". Auch hier ist der Unterschied
    zwischen „nicht messbar" und „nicht vorhanden" der ganze Punkt: der Test
    misst den Wortlaut, nicht die Wirkung.
    """
    text = (antwort or "").lower()
    jetzt = _jetzt()
    heraus = []
    for zeile in db.db.execute(
            "SELECT a.eintrag_id,a.objekt_id,o.semantische_identitaet "
            "FROM sicht_arbeitsraum a "
            "LEFT JOIN sicht_weltobjekt o ON o.objekt_id=a.objekt_id "
            "WHERE a.turn_id=? AND a.zuendung=1", (turn_id,)).fetchall():
        name = (zeile["semantische_identitaet"] or "").strip().lower()
        if name and name in text:
            art, beleg = "IN_ANTWORT_ZITIERT", f"Wortlaut '{name}' gefunden"
        else:
            art = "NICHT_NACHWEISBAR"
            beleg = ("Benennung kommt im Wortlaut nicht vor. Das schliesst "
                     "eine Wirkung nicht aus — es ist nur nicht messbar.")
        nid = _kennung()
        db.db.execute(
            "INSERT INTO sicht_nutzung(nutzung_id,eintrag_id,objekt_id,"
            "evidenz_id,turn_id,causal_id,nutzungsart,beleg,"
            "festgestellt_von,erzeugt_am) VALUES(?,?,?,NULL,?,?,?,?,?,?)",
            (nid, zeile["eintrag_id"], zeile["objekt_id"], turn_id,
             causal_id, art, beleg, "MECHANISCH", jetzt))
        heraus.append({"nutzung_id": nid, "objekt_id": zeile["objekt_id"],
                       "nutzungsart": art})
    return heraus


# ── Die Abfrage, um die es geht ─────────────────────────────────────

def rueckschau(db, *, turn_id: str) -> dict[str, Any]:
    """Die fuenf Ebenen eines Zuges, getrennt.

    ⭐⭐⭐ DAS IST DIE ABFRAGE AUS DER KERNANFORDERUNG. Sie beantwortet die
    fuenf Fragen aus RETINA_BRANCH_HANDOFFS.md einzeln und aus fuenf
    verschiedenen Tabellen — nicht aus einer mit fuenf Filtern. Wenn diese
    Funktion je aus EINER Tabelle liest, ist die Trennung verloren gegangen.
    """
    aufnahmen = [dict(z) for z in db.db.execute(
        "SELECT * FROM sicht_aufnahme WHERE turn_id=?", (turn_id,)).fetchall()]
    ids = [a["aufnahme_id"] for a in aufnahmen] or ["-"]
    platz = ",".join("?" * len(ids))
    lies = lambda sql: [dict(z) for z in db.db.execute(sql, ids).fetchall()]
    return {
        "aufnahmen": aufnahmen,
        "angekommen": lies(
            f"SELECT * FROM sicht_evidenz WHERE aufnahme_id IN ({platz})"),
        "geschlossen": lies(
            f"SELECT * FROM sicht_hypothese WHERE aufnahme_id IN ({platz})"),
        "geglaubt": lies(
            f"SELECT * FROM sicht_weltobjekt_stand "
            f"WHERE aufnahme_id IN ({platz})"),
        "im_arbeitsraum": [dict(z) for z in db.db.execute(
            "SELECT * FROM sicht_arbeitsraum WHERE turn_id=?",
            (turn_id,)).fetchall()],
        "hat_getragen": [dict(z) for z in db.db.execute(
            "SELECT * FROM sicht_nutzung WHERE turn_id=? "
            "AND nutzungsart<>'NICHT_NACHWEISBAR'", (turn_id,)).fetchall()],
    }

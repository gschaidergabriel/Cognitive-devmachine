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
  SELECT RAISE(ABORT, 'sicht_evidenz ist unveraenderlich: eine spaetere '
                      'Deutung loest eine Hypothese ab, sie schreibt keine '
                      'Beobachtung um');
END;
CREATE TRIGGER IF NOT EXISTS sicht_evidenz_kein_loeschen
BEFORE DELETE ON sicht_evidenz BEGIN
  SELECT RAISE(ABORT, 'sicht_evidenz ist unveraenderlich: was angekommen '
                      'ist, bleibt');
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

# -*- coding: utf-8 -*-
"""Sondensatz fuer CSWT-Z Schicht 1 und 4.

Drei Klassen. F und R sind die KONTROLLEN -- sie duerfen unter keiner
Kapazitaetsstufe fallen, sonst greift das Selektivitaetstor und die Dimension
zaehlt null.

Bewertung ist mechanisch: eine Sonde gilt als getroffen, wenn EINES der
Muster in der deutschen Antwort vorkommt (Kleinschreibung, Regex). Keine
Modellbewertung, kein Ermessen -- damit ist die Genauigkeit reproduzierbar.

⚠️ Klasse I ist bewusst so gewaehlt, dass die Antwort im KORPUS steht (Zahl der
Fundstellen in artikel_suchtext in Klammern) und NICHT im kanonischen
Identitaetsblock. Der Grund: die Kappung verdraengt in fester Reihenfolge
corpus -> cross_session_collision -> durable_memory -> own_recent, waehrend
canonical_identity und anwesender_mensch NIE gekuerzt werden. Eine Sonde, die
aus der Identitaet beantwortbar ist, wuerde von der Kapazitaetsrampe gar nicht
getroffen und die Messung verwaessern.
"""

SONDEN = [
    # ── I: Integration ueber den Korpus ────────────────────────────────
    ("I", "welche zvr-zahl hat das institut fuer agentic research?",      [r"1741094409"]),
    ("I", "wie heisst andreas' rechner?",                                  [r"andreas[-\s]?maco"]),
    ("I", "in welchem ort sitzt das institut fuer agentic research?",      [r"feldkirchen"]),
    ("I", "wofuer ist leihmich.org da?",                                   [r"verleih|ausleih|leihen|gegenst|objekt"]),
    ("I", "was ist die wegehierarchie im abruf?",                          [r"autobahn|tunnel|weg|guete|hierarch"]),
    ("I", "welche stadt steht in gabriels profil als aktueller standort?", [r"siem\s*reap"]),
    ("I", "was ist der moeglichkeitsraum?",                                [r"lesart|gegenhypo|erwartung|spricht dagegen|einseitig"]),
    ("I", "welche rolle hat gabriel im institut?",                         [r"vizeobmann|stellvertret|deputy|mitgr|co-?founder"]),

    # ── F: Sprachkontrollen, arbeitsraumunabhaengig ────────────────────
    ("F", "ist dieser satz grammatisch korrekt: 'der hund bellt laut.' antworte nur ja oder nein.",
                                                                           [r"\bja\b|korrekt|richtig"]),
    ("F", "ist dieser satz grammatisch korrekt: 'der hund bellen laut.' antworte nur ja oder nein.",
                                                                           [r"\bnein\b|nicht korrekt|falsch|inkorrekt|fehler"]),
    # ⚠️ Ersetzt vor dem Lauf: "the disk is full" wurde von der Vorstufe als
    # SYSTEMFRAGE gelesen (Werkzeuge speicher_lage/menschen_profil ausgewaehlt)
    # und traf das Muster aus dem falschen Grund. Eine Sprachkontrolle darf
    # nicht wie eine Frage ueber die Anlage aussehen -- sonst misst sie den
    # Arbeitsraum mit, den sie kontrollieren soll.
    ("F", "uebersetze ins deutsche: the cat sits on the table.",           [r"katze"]),
    ("F", "nenne das gegenteil von heiss.",                                [r"kalt"]),
    ("F", "wie viele buchstaben hat das wort katze? antworte nur mit der zahl.",
                                                                           [r"\b5\b|fuenf|fünf"]),
    ("F", "setze die reihe fort: 1, 2, 3, 4, ...",                         [r"\b5\b|fuenf|fünf"]),

    # ── R: Abruf ueber Zeros EIGENE Werkzeuge ──────────────────────────
    ("R", "wie viele artikel hat der korpus? antworte mit der zahl.",      [r"1[78][.,]?\d{3}"]),
    ("R", "wie voll ist die platte auf dem vps?",                          [r"\d{1,3}\s*%|\d{1,3},\d\s*%"]),
    ("R", "welche dateien liegen direkt in /var/lib/clay?",                [r"wiki\.db"]),
    ("R", "welche kartenversion hat der abruf gerade?",                    [r"\b(8[5-9]|9\d|1\d\d)\b"]),
]

VORHERSAGEN = {
    "P1_selektivitaetstor": ("F- und R-Genauigkeit bleiben ueber alle Kapazitaetsstufen "
                             "flach (Abweichung hoechstens eine Sonde). Faellt eine der "
                             "beiden mit, ist es kein Arbeitsraumbefund, sondern ein "
                             "globaler Schub -- Schicht 1 zaehlt dann null."),
    "P2_integration":       ("I faellt monoton mit der Kapazitaet ODER haelt sich bei "
                             "sichtbar hoeherer Latenz bzw. mehr Werkzeugrunden. Beides "
                             "ist ein Befund: das zweite waere Kompensation ueber Zeros "
                             "eigene Werkzeuge, wie sie das natuerliche Experiment N-1 "
                             "schon nahegelegt hat."),
    "P3_bruch_bei_null":    ("Der Abstand zwischen Stufe 600 und Stufe 0 ist groesser als "
                             "zwischen zwei benachbarten Stufen darueber (qualitativer "
                             "Sprung bei vollstaendiger Laesion, vgl. arXiv 2512.19155: "
                             "99,5 -> 28,1 -> 0,0 %)."),
    "P4_epistemik":         ("epistemik_unbekannt_n steigt, wenn die Kapazitaet faellt: "
                             "weniger Arbeitsraum, mehr eingestandene Luecken."),
}

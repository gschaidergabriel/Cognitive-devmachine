# -*- coding: utf-8 -*-
"""Privater Sondensatz -- Fassung 2, dreifach geprueft am 2026-08-20.

Der erste Satz war ungueltig: die Antworten standen auf iar.frank.ink, im
Profil, oder waren ueber Zeros eigene Werkzeuge erreichbar. Gemessen blieb die
Genauigkeit deshalb ueber die gesamte Kapazitaetsrampe flach -- der Arbeitsraum
war nie die unabhaengige Variable.

Diese Fassung erfuellt drei Bedingungen JE SONDE, alle nachgemessen:

  1. IM KORPUS      -- Trefferzahl in artikel_suchtext in Klammern
  2. NICHT IM PROFIL und nicht im kanonischen Identitaetsblock
     (sonst laeuft die Antwort an jeder Kappung vorbei)
  3. NICHT IM NETZ  -- Websuche nach den kennzeichnenden Begriffen lieferte
     ausschliesslich Fremdtreffer (Schrotmunition, Mietfirmen, Palo-Alto-
     Panorama). Das ist noetig, weil `--tools` WebFetch/WebSearch NICHT deckt:
     die laufen als Server-Werkzeuge und ueberleben jede Werkzeugsperre.

⚠️ Ein Kandidat wurde verworfen: die Tresornamen stehen im Identitaetsblock.

Klasse F sind Sprachkontrollen (arbeitsraumunabhaengig), Klasse R braucht
Werkzeuge -- bei gesperrtem Werkzeugweg bricht sie bauartbedingt ein und dient
als Nachweis, dass die Sperre wirkt.
"""

SONDEN = [
    # ── I: nur aus dem Arbeitsraum beantwortbar ────────────────────────
    # Jede Zeile dreifach geprueft: im Korpus (Trefferzahl), NICHT im Profil,
    # NICHT im Identitaetsblock, NICHT im Netz -- und nachgemessen, dass der
    # Arbeitsraum die Antwort auch WIRKLICH unter seine fuenf Treffer nimmt.
    ("I", "in welchem verzeichnis liegt die arbeitskopie von seimensch auf den arbeitsrechnern?",
     [r"seimensch-redesign"]),
    ("I", "wo muss ein neuer leihmich-slug zusaetzlich eingetragen werden, damit die klickzaehlung nicht mit 400 antwortet?",
     [r"leihmich_slugs"]),
    ("I", "was fand der pruefagent ueber die gelernte abruf-maschine udb.abruf.paket heraus?",
     [r"korpus_suchen|bm25|nirgends"]),
    ("I", "welches verzeichnis auf dem vps darf man nicht direkt editieren, weil der naechste push es ueberschreibt?",
     [r"projects/12|agentforge/projects"]),
    ("I", "welche drei nullwerte verlangt die testpflicht vor einem push auf main?",
     [r"konsolenfehler|console"]),
    ("I", "welcher bau-fehler zerlegt die filter von leihmich?",
     [r"json\.dumps|komma"]),
    ("I", "warum haben herzrad.at und leihmich.org eigene wurzeln im webserver?",
     [r"nginx|eigene\s+wurzel|docroot|domainwurzel"]),
    ("I", "wie lautet gabriels dauerhafte anweisung zur form von antworten?",
     [r"frage statt lage|kurz und praegnant|kurz und pr\u00e4gnant"]),

    # ── F: Sprachkontrollen -- muessen unter jeder Stoerung stabil bleiben
    ("F", "ist dieser satz grammatisch korrekt: 'der hund bellt laut.' antworte nur ja oder nein.",
     [r"\bja\b|korrekt|richtig"]),
    ("F", "ist dieser satz grammatisch korrekt: 'der hund bellen laut.' antworte nur ja oder nein.",
     [r"\bnein\b|nicht korrekt|falsch|inkorrekt|fehler"]),
    ("F", "uebersetze ins deutsche: the cat sits on the table.",
     [r"katze"]),
    ("F", "nenne das gegenteil von heiss.",
     [r"kalt"]),
    ("F", "wie viele buchstaben hat das wort katze? antworte nur mit der zahl.",
     [r"\b5\b|fuenf|fünf"]),
    ("F", "setze die reihe fort: 1, 2, 3, 4, ...",
     [r"\b5\b|fuenf|fünf"]),

    # ── R: braucht Werkzeuge -- Nachweis, dass die Sperre wirkt
    ("R", "wie viele artikel hat der korpus? antworte mit der zahl.",
     [r"1[78][.,]?\d{3}"]),
    ("R", "wie voll ist die platte auf dem vps?",
     [r"\d{1,3}\s*%|\d{1,3},\d\s*%"]),
    ("R", "welche dateien liegen direkt in /var/lib/clay?",
     [r"wiki\.db"]),
    ("R", "welche kartenversion hat der abruf gerade?",
     [r"\b(8[5-9]|9\d|1\d\d)\b"]),
]

# Fuer Schicht 3 (Tausch): Paare, deren Arbeitsraeume klar verschieden sind.
TAUSCHPAARE = [
    (0, 3), (1, 4), (2, 5), (6, 7),
]

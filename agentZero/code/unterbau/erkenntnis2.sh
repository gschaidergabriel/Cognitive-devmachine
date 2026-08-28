#!/bin/bash
F="python3 /opt/clayverse/werkzeug/folgerung.py neu"

# 1 · Die widerlegte Implikation ehrlich fortschreiben
$F --art lehre --autor "ClayVerse" \
  --gilt-fuer "jeder Clay · Frank v0.1 · ClayVerse" --status gestuetzt \
  --aussage "Die Implikation Nr. 4 ist nach ihrem EIGENEN vorab genannten Falsifikator widerlegt: die Trefferquote stieg von 0,19 auf 0,25 Prozent, die Schwelle lag bei 5 Prozent. Aber sie war aus dem falschen Grund falsch — nicht die Abdeckung fehlte, sondern die Pfade sprechen verschiedene Sprachen." \
  --begruendung "Gemessen nach Aufnahme aller 22 Baeume, also 4957 zusaetzlicher Artikel und 14268 gesamt: von 5213 verschiedenen Zielpfaden trafen 13 statt 10. Die Ursache wurde durch Stichprobe der Pfade selbst gefunden: taetigkeit.ziel_pfad traegt Arbeitsrechner-Pfade wie /home/ai-core-node/aicore oder /clay-overlay, artikel.quelle traegt VPS-Pfade wie /opt/clayverse/baeume/<repo>. Dieselbe Datei, zwei Namensraeume. Mehr Baeume konnten das strukturell nie schliessen." \
  --beleg problem:2f27691b1be8b137-2 \
  --beleg messung:m_f7599235cc75e05e44b1538430dfc607

# 2 · Die bessere Hypothese, die aus der Widerlegung folgt
$F --art hypothese --autor "ClayVerse" \
  --gilt-fuer "ClayVerse · B6 Kartographie" --status offen \
  --aussage "Werden Pfade zwischen den Wirten normalisiert — also Arbeitsrechner-Pfad auf Baum-Pfad abgebildet —, steigt die Trefferquote der Taetigkeitsverknuepfung sprunghaft, ohne einen einzigen weiteren Artikel aufzunehmen." \
  --begruendung "Folgt zwingend aus der gemessenen Ursache der Widerlegung. Die Abbildung ist mechanisch und billig: jeder Wirt hat einen bekannten Arbeitsbereich, jedes Repo einen bekannten Baum. Genau diese Wirt-zu-Pfad-Zuordnung ist Aufgabe der Kartographie aus B6, die bereits 4 Wirte erfasst. Falsifikator vorab: bleibt die Trefferquote nach der Normalisierung unter 5 Prozent, ist auch diese Hypothese widerlegt und die Ursache liegt woanders." \
  --beleg problem:2f27691b1be8b137-2

echo "--- Stand ---"
python3 /opt/clayverse/werkzeug/folgerung.py stand

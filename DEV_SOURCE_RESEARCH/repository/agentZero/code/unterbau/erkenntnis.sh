#!/bin/bash
F="python3 /opt/clayverse/werkzeug/folgerung.py neu"

$F --art hypothese --autor "Gabriel Gschaider" \
  --gilt-fuer "jeder Clay · Frank v0.1" --status gestuetzt \
  --aussage "Der ClayGraph ergibt auf einmal Sinn — sein Wert liegt nicht in der Graphstruktur, sondern in der Abdeckung dessen, was sie abbildet. Ein Gedaechtnis, das mit Zusammenhaengen antwortet statt mit Treffern, ist eine andere Sache als eine schnelle Suche." \
  --begruendung "Gemessen an derselben Aufgabe: derselbe Abruf ohne Graph erreicht 60,0 Prozent Top-1, mit Graph 100 Prozent. Der Unterschied sind vierzig Prozentpunkte, und er stammt nicht aus schnellerem Suchen, sondern aus vorhandenen Kanten. Damit ist die Aussage keine Intuition mehr, sondern eine gestuetzte Behauptung." \
  --beleg messung:m_7c9a710bc03e940ef95ed3a538263132 \
  --beleg messung:m_f7599235cc75e05e44b1538430dfc607 \
  --beleg messung:m_5ce06d46c7fc5342245a8d243d2d7117

$F --art hypothese --autor "ClayVerse" \
  --gilt-fuer "ClayVerse" --status widerlegt \
  --aussage "Jeder von einem Clay angefasste Dateipfad wird zu einer Kante im Wiki, und die vier Wochen vorhandener Sitzungsprotokolle loesen damit das Waisenproblem." \
  --begruendung "Widerlegt durch Messung, nicht durch Meinung. Von 5089 verschiedenen Zielpfaden aus 26446 Werkzeugnutzungen trafen 9 exakt auf artikel.quelle, also 0,18 Prozent. Waisen sanken von 8305 auf 8279. Ursache gemessen: 99,5 Prozent der Artikel zeigen auf synthetische Wissenspakete, die keine Arbeitssitzung je anfasst. Die Hypothese ist damit bei der aktuellen Abdeckung widerlegt, nicht grundsaetzlich." \
  --beleg problem:2f27691b1be8b137-2 \
  --beleg problem:35a7c6595a972e95-0

$F --art implikation --autor "ClayVerse" \
  --gilt-fuer "jeder Clay · Frank v0.1 · ClayVerse" --status offen \
  --aussage "Nicht der Mechanismus ist die Grenze, sondern die Abdeckung. Frank v0.1 braucht keinen besseren Graphen — er braucht den Bestand darin. Dasselbe gilt fuer jeden Clay: ein Gedaechtnis antwortet nur so gut, wie sein Korpus reicht." \
  --begruendung "Folgt aus beiden vorstehenden Hypothesen zusammen. Die eine zeigt, dass Kanten den Unterschied zwischen 60 und 100 Prozent machen. Die andere zeigt, dass Kanten ausbleiben, solange der Korpus die falschen Dateien enthaelt. Beide Male ist der Mechanismus in Ordnung und die Abdeckung das Problem. Pruefbar gemacht: die Aufnahme der uebrigen 22 Baeume ist der Versuch, mit vorab genanntem Falsifikator — steigt die Trefferquote nicht ueber 5 Prozent, ist diese Implikation widerlegt." \
  --beleg problem:96e30665695924f1-0 \
  --beleg problem:2f27691b1be8b137-2 \
  --beleg messung:m_f7599235cc75e05e44b1538430dfc607

echo "--- Stand ---"
python3 /opt/clayverse/werkzeug/folgerung.py stand

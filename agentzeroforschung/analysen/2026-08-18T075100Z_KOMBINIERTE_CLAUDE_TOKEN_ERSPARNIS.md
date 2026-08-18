# Kombinierte Claude-Code-Tokenersparnis

Zeitpunkt: 2026-08-18T07:51Z

## Fragestellung

Wie stark sinkt die Claude-Code-Tokenlast durch drei gemeinsam wirkende Mechanismen:
1. Caveman-English fuer Zeros Ausgabe,
2. kostenlose Mistral-Vorverarbeitung,
3. autarkes/bounded Memory- und Corpus-Retrieval.

## Harte Systembefunde

- Mistral-Medium ist die Vorstufe. Sie bekommt World-/Recent-/Memory-/Corpus-Kontext und erzeugt einen kurzen `caveman_prompt`, den Zero/Claude statt der menschlichen Rohformulierung sieht.
- Claude/Zero antwortet Caveman-English; Mistral-Small uebersetzt danach ins Deutsche.
- MicroClay-Retrieval durchsucht bis zu 5.000 Memory-Zeilen, liefert aber standardmaessig maximal 24 Memories und maximal 12.000 Zeichen; Corpus-Retrieval liefert maximal 5 Ausschnitte zu je 260 Zeichen.
- Der aktuelle Export Generation 35 enthaelt erstmals 6 durable-memory-Zeilen; der Lern-/Retrievalpfad ist also nicht mehr rein leer.
- Der bisherige Caveman-Arbeitswert von ca. 37 % Laengenreduktion stammt aus einem handgebauten Evaluationsset, nicht aus einer Produktions-A/B-Messung.

## Warum die Prozentwerte nicht addiert werden duerfen

Memory-Retrieval reduziert zuerst den Stoff. Mistral verdichtet den verbleibenden Stoff nochmals, bevor Claude ihn sieht. Caveman reduziert anschliessend Zeros Ausgabetokens. Retrieval und Mistral ueberlappen daher stark.

## Modellrechnung

Die folgende Rechnung ist eine INFERENCE, keine provider-native Tokenmessung.

Konservatives Szenario:
- 70 % der Claude-Tokens waeren Input, 30 % Output.
- 60 % des Inputs waeren History/Memory/Corpus.
- Retrieval reduziert diesen Memory-Anteil um 70 %.
- Mistral reduziert den danach verbleibenden Claude-Input um 60 %.
- Caveman reduziert Claude-Output um 37 %.

Restquote = 0,70 * ((0,60*0,30 + 0,40)*0,40) + 0,30*0,63 = 0,3514.
=> Ersparnis = 64,86 %.

Realistisches zustandsreiches Szenario:
- 80 % Input, 20 % Output.
- 70 % des Inputs History/Memory/Corpus.
- Retrieval reduziert diesen Anteil um 80 %.
- Mistral reduziert den Restinput um 70 %.
- Caveman reduziert Output um 37 %.

Restquote = 0,80 * ((0,70*0,20 + 0,30)*0,30) + 0,20*0,63 = 0,2316.
=> Ersparnis = 76,84 %.

Sehr zustandsreiches Szenario:
- 85 % Input, 15 % Output.
- 75 % des Inputs History/Memory/Corpus.
- Retrieval reduziert diesen Anteil um 85 %.
- Mistral reduziert den Restinput um 75 %.
- Caveman reduziert Output um 37 %.

=> Ersparnis ca. 82,85 %.

## Forschungsurteil

Arbeitsbereich fuer Claude-Code-Ersparnis durch diese DREI Mechanismen zusammen: ca. 65-80 %.
Plausibler zentraler Arbeitswert: ca. 75 %.
Bei sehr langen/zustandsreichen Sessions sind >80 % plausibel.
Bei kleinen einfachen Turns ist die Quote niedriger, weil wenig History/Memory vorhanden ist.

Ein Arbeitswert von 75 % bedeutet:
- Direkt Claude: 1.000.000 Claude-Tokens
- EntityOS-Pipeline: ca. 250.000 Claude-Tokens
- Ersparnis: ca. 750.000 Claude-Tokens
- gleiche Claude-Tokenmenge koennte theoretisch ca. 4x so viele vergleichbare Turns tragen.

## Evidenzgrenze

Die Gesamtquote bleibt E2/INFERENCE, bis ein provider-nativer `CLAUDE_TOKEN_LEDGER` fuer identische Direct-vs-Pipeline-Aufgaben Input-, Cache- und Output-Tokens getrennt protokolliert. Insbesondere der 37-%-Caveman-Wert ist noch kein Produktionswert.
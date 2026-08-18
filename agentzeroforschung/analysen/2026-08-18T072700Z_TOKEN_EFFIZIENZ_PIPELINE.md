# EntityOS / Zero Token-Effizienz der Mistral+Caveman-Pipeline

Zeitpunkt: 2026-08-18T07:27Z
Basis: aktueller Generation-32-Stand und Bauverlauf.

## Gemessene Architektur

Der aktuelle Headless-Pfad ist funktional: Mensch deutsch -> Mistral-Vorstufe -> Zero/Claude -> Caveman-English -> Mistral-Small-Uebersetzer -> Mensch deutsch. Ein realer P5-Lauf ist mit German-in/German-out, TurnLifecycle, Prestage- und Translation-Receipts belegt.

Die Vorstufe nutzt mistral-medium-latest; der Uebersetzer mistral-small-latest. Der Uebersetzer wurde auf 50 festen Beispielen mit unabhaengigem Richter gemessen: v4 pass_rate 0.96, Repeat 0.98, Faithfulness 99.1/99.6, 0 Fabrications.

## Harte Effizienzbefunde

1. Hook-/Identitaetsanker: 5550 -> 206 Zeichen. Das sind 96.29 % weniger Zeichen in genau diesem redundanten Bestandteil. Das ist keine Aussage ueber den gesamten Systemprompt.
2. Repo-lokaler Tokenvertrag: C0 <=500 Tokens; C1 ordinary <=700, bevorzugt <=450; C2 <=1500 vor expliziter Evidenzerweiterung. STORE RICH -> INDEX COMPACT -> FETCH ON DEMAND; Pointer und Deltas statt Vollzustand.
3. Vorprozessor-Dichte: Vollmaterial 3.91 Fakten/1000 Tokens, Paket 4.95 Fakten/1000 Tokens. Fuer gleiche Faktenmenge entspricht das rund 21.0 % weniger Retrieval-Tokens.
4. Caveman-Ausgabe ist strukturell auf kurze Klauseln, wenig Fuellwoerter und keine Kontextwiederholung ausgerichtet. Fuer den aktuellen produktiven Pipelineverkehr ist noch kein provider-native Tokenzaehler exportiert; deshalb gibt es noch keinen harten Durchschnitt fuer Caveman-vs-poliertes-Deutsch.

## Was kann heute seriös gesagt werden?

Claude-/Zero-Tokens werden sehr wahrscheinlich stark reduziert, weil sowohl Eingabekontext als auch Ausgabe auf Claude-Seite komprimiert werden und die Oberflaechenarbeit an Mistral ausgelagert ist. Eine vorsichtige Architektur-Schaetzung fuer ordinary turns ist etwa 35-60 % weniger Claude-Input+Output-Tokens gegen einen gleich informierten direkten Claude-Pfad mit wiederholtem Kontext und menschenlesbarer Vollausgabe. Das ist eine INFERENCE, keine gemessene Produktionskennzahl.

Gesamttokens ueber ALLE Modelle koennen deutlich weniger stark sinken oder sogar steigen, weil Prestage und Uebersetzer zwei zusaetzliche Modellaufrufe sind. Tokenersparnis und Kostenersparnis sind daher nicht identisch. Der Pipeline-Hebel ist primaer: teure/knappe Zero-Tokens durch kleinere strukturierte Pakete und Caveman zu sparen und Sprachoberflaeche auf kleinere Modelle zu verlagern.

## Fehlendes Messgeraet: TOKEN_LEDGER

Pro Turn provider-native Usage protokollieren:
- prestage_input_tokens / prestage_output_tokens / cache tokens / Kosten
- zero_input_tokens / zero_output_tokens / cache tokens / Kosten
- translator_input_tokens / translator_output_tokens / Kosten
- raw_user_tokens
- raw_caveman_tokens
- translated_german_tokens
- retrieval_raw_candidate_tokens vs selected_packet_tokens
- total_pipeline_tokens / total_pipeline_cost

Zusaetzlich 1-5 % der Turns als kontrolliertes Shadow-Baseline-Replay: gleicher eingefrorener Zustand, aber direkter Zero-Pfad ohne Prestage/Translator. Dann sind exakt messbar:
- Claude_token_saving = 1 - zero_pipeline_tokens / zero_direct_tokens
- total_token_saving = 1 - all_pipeline_tokens / direct_all_tokens
- cost_saving = 1 - pipeline_cost / direct_cost
- quality_delta = verified_outcome_pipeline - verified_outcome_direct

Ohne diesen Baseline-Paarvergleich bleibt jede globale Prozentzahl eine Schaetzung.

## Forschungsurteil

HARD: 96.29 % Zeichenreduktion am Hook-/Identitaetsanker; ~21.0 % Tokenreduktion fuer gleiche Faktenmenge im gemessenen Retrieval-Paket; C0/C1/C2 Budgets sind explizit; Translator-Qualitaet 96-98 % Pass bei 99.1-99.6 Faithfulness und 0 Fabrications im gemessenen 50er-Set.

INFERENCE: ordinary Claude/Zero token load vermutlich grob 35-60 % niedriger als ein vergleichbarer direkter Vollkontext-/Vollprosa-Pfad. Systemweite Tokenersparnis ueber Mistral+Zero+Translator ist derzeit UNRESOLVED und kann wesentlich kleiner sein.

Naechste hoechste Informationsausbeute: provider-native TOKEN_LEDGER + kontrollierter Direct-vs-Pipeline Shadow-Vergleich.
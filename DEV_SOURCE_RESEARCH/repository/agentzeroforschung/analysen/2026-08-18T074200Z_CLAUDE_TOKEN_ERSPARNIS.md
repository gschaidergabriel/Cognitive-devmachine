# Claude-Code-Tokenersparnis durch EntityOS/Mistral

Stand: 2026-08-18, aktueller Codeexport Generation 33.

## Fragestellung

Wie viele Claude-Code-Tokens spart die Pipeline, wenn die Mistral-Bahn fuer den Eigner kostenlos ist? Betrachtet werden bewusst nur Claude-Tokens; Mistral-Tokens zaehlen fuer diese Kosten-/Kontingentrechnung als 0.

## Direkt beobachtete Mechanismen

1. Pipeline: menschliche Nachricht -> WorldAssembler -> Mistral-Prestage -> nur `caveman_prompt` an `claude -p` -> Caveman-Antwort -> Mistral-Small-Uebersetzer -> Deutsch.
2. Mistral-Prestage sieht den strukturierten Weltkontext und die letzten Zuege; Claude erhaelt davon nicht den vollen Kontext, sondern den verdichteten Caveman-Prompt. Toolauswahl wird separat als `--allowedTools` uebergeben.
3. Headless Claude laeuft one-shot mit `--no-session-persistence`; Prompt-History, Auto-Memory, CLAUDE.md-Autoloading, Background Tasks und nonessential traffic sind abgeschaltet.
4. Identitaets-/Hook-Anker wurde laut Zielpruefer von 5.550 auf 206 Zeichen reduziert: 96,3 % weniger Text auf diesem Teilkanal.
5. Deterministische Kontextverdichtung wurde im Unterbau mit 3,91 vs 4,95 Fakten/1000 Token gemessen, entsprechend rund 21 % weniger Token fuer gleiche Faktenmenge in diesem Vergleich.
6. Der Mistral-Uebersetzer nimmt die fluente deutsche Oberflaeche aus Claude heraus; der aktuelle Uebersetzer ist Mistral-Small. Die 50er Eval-Stichprobe fuer die Uebersetzungsqualitaet ist handgeschrieben und darf NICHT als Produktionsmessung der Tokenersparnis interpretiert werden.
7. `headless_zero.py` liest aus Claude JSON bereits `total_cost_usd`, `num_turns` und Laufzeiten, persistiert aber derzeit keine Claude-Input-/Output-Tokenzaehler. Daher existiert noch kein direktes A/B-Ergebnis fuer die Gesamtquote.

## Schaetzung

Unter der Eignerannahme `Mistral-Kosten = 0` ist die relevante Groesse `Claude_tokens_pipeline / Claude_tokens_raw`.

Aktuelle belastbare Schaetzspanne:
- normale Chat-/Entscheidungsturns: ca. 50-70 % weniger Claude-Tokens;
- schwere Build-/Toolturns: ca. 35-55 % weniger Claude-Tokens, weil Toolausgaben und externe Evidenz weiterhin Claude-Kontext brauchen;
- wiederholte zustandsreiche Sessions koennen bei guter Prestage-Verdichtung/Toolselektion lokal noch hoeher liegen; >70 % ist Kandidat, nicht belegt.

Arbeitswert fuer Kapazitaetsplanung: rund 60 % Claude-Tokens gespart, also etwa Faktor 2,5 mehr gleiche Arbeit pro Claude-Tokenkontingent (`1/(1-0.60)=2.5`), solange Qualitaet und Retryrate nicht schlechter werden.

## Anteil Mistral

Mistral ist der groesste einzelne Hebel, aber sein Anteil ist noch nicht separat gemessen. Zwei Mechanismen:
- Prestage ersetzt breite Kontextaufnahme/Planungsarbeit und komprimiert sie in den eigentlichen Caveman-Auftrag.
- Translator ersetzt fluente deutsche Ausformulierung durch Claude.

Nicht als bereits realisierte Einsparung zaehlen: das `outsourced`-Feld allein. `pipeline.py` persistiert dieses Feld, fuehrt die darin benannte Auslagerung aber nicht selbst aus. Erst ein nachgewiesener Router-/Toolpfad darf als weitere Claude-Ersparnis gezaehlt werden.

## Fehlendes Messgeraet

`CLAUDE_TOKEN_LEDGER` pro Pipeline-Turn:
- raw_prompt_chars/tokens
- world_chars/tokens vor Prestage
- caveman_prompt_chars/tokens
- ausgewaehlte Tool-Schema-Tokens
- Claude input_tokens/output_tokens/cache_read/cache_write (soweit CLI-Envelope verfuegbar)
- caveman_answer tokens
- German translation length nur als Vergleich
- num_turns/retries
- verified outcome / quality gate

Dazu Shadow-A/B auf identischen Aufgaben: direkte Claude-Route vs Pipeline. Erst dann darf eine exakte Prozentzahl statt Schaetzspanne berichtet werden.

## Evidenzurteil

E2 fuer einzelne Kompressionsmechanismen; E1/E2 fuer reale Pipeline-Struktur; Gesamtquote 50-70 % bleibt INFERENCE bis Claude-Tokenledger + A/B vorliegt.

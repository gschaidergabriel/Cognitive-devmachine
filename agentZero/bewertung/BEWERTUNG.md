# Bewertung: Daumen hoch/runter je Zero-Antwort

Export aus `eos_bewertungen` (UnifiedDB, siehe `clayverse/bewertung.py` im entityOS-Repo), alle 30 Minuten durch `eos-bewertung-export.timer` auf dem VPS.

`bewertungen.jsonl.meta.json` traegt den Zeitpunkt und die Anzahl -- lies das zuerst, bevor du `bewertungen.jsonl` auswertest, um zu wissen, wie aktuell der Stand ist.

## Felder je Zeile

- `bewertung_id`, `turn_id`, `session_id`, `user_id` -- welcher Zug, welche Sitzung, wer bewertet hat.
- `wert` -- `1` (hoch) oder `-1` (runter). Es gibt keine dritte Auspraegung: eine entfernte Bewertung ist eine geloeschte Zeile, kein `wert=0` -- taucht in einem spaeteren Export also einfach nicht mehr auf.
- `frage_turn_id`, `frage_hash`, `frage_laenge` -- die Frage VOR der bewerteten Antwort, als Hash+Laenge, nicht im Klartext (der Klartext steht kanonisch in `turns.content` der UnifiedDB, hier waere er eine zweite Quelle).
- `antwort_hash`, `antwort_laenge` -- dieselbe Begruendung fuer die bewertete Antwort selbst.
- `modell` -- best effort aus der Uebersetzungs-Vorstufe, `null` wenn nicht ermittelbar (z.B. ein Terminal-/CLI-Zug ohne Uebersetzung) -- nie erfunden.
- `ts` -- Unix-Zeitstempel der (letzten) Bewertung.

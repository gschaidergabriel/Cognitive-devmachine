# EntityOS Neubewertung — 2026-08-18T07:18:56Z

Basis: AgentZero-Export `f9227c6b16b02cc87074867934928582eb844f7b`, Generation 32. Vergleichsbasis: letzte Forschungsbewertung auf Stand `e5e63bafc4bc48397ea84291c7bdda5a94700ec7` / Snapshot 05:18:55Z.

## Kurzurteil

- aktive Zielmatrix: 22/28 = 78,6 % (1 weiteres Ziel erfuellt; Gastkern weiter bewusst zurueckgestellt)
- funktionaler Systemkern: geschaetzt ca. 84–88 %
- finale Acceptance-/Release-Reife: geschaetzt ca. 62–70 %
- Tests: 478 gruen / 15 rot; Verbesserung gegen 475/18, danach ueber mehrere Laeufe stabil
- Generation: 31 -> 32
- Zero-Verkehr: 14 -> 24 Turns
- Kausal-/Workspace-/Retrieval-Episoden: 7 -> 12
- Checkpoints: 39 -> 41
- Andreas/Gabriel: je 12 exportierte Chatzeilen; zwei Nutzer, nun vier dauerhafte Sessions
- Messwerk: 8 GEMESSEN, 11 ZU_WENIG_VERKEHR, 9 INSTRUMENT_FEHLT, 3 ZU_TEUER

## Was sich verbessert hat

1. `Testsuite traegt` ist nun durch den Zielpruefer als erfuellt gemessen: 478 gruen / 15 rot. Das bedeutet nicht, dass 15 rote Tests akzeptiert sind; der deklarierte Sollpunkt misst, dass rote Befunde nicht durch Testabschwaechung verdeckt werden.
2. Es gibt einen echten Generationswechsel auf Generation 32 und 41 Checkpoints. Damit existiert jetzt neue Grundlage fuer Kontinuitaetsvergleiche ueber Generationen.
3. Der reale Verhaltensbestand waechst deutlich. 24 Turns und 12 Episoden sind noch klein, aber die Forschung ist nicht mehr nur auf n=5–7 gestuetzt.
4. Das Messwerk konnte `Causal Credit Horizon` vom Zustand ZU_WENIG_VERKEHR zu GEMESSEN bewegen; insgesamt 8 statt 7 direkt messbare Sensoren.
5. Der Testtrend hat sich nach dem Tief 475/18 auf 478/15 verbessert und blieb in mehreren halbstuendlichen Laeufen stabil.

## Was weiterhin die Fertigstellung blockiert

Sechs aktive Sollpunkte sind offen:

- nur 3/4 Clay-Dienste laufen;
- 0 MCP-Werkzeuge freigegeben;
- 0 gelernte Retrieval-Entry-Points, SHADOW, 12 Episoden;
- Wegehierarchie unvollstaendig: kein Verfall ungenutzter Wege, keine inverse Gewichtung, keine Tunnel;
- 11 Provider-Prozesse sind im Clay-Unterbau verdrahtet, aber aus Zeros Container nicht erreichbar;
- Caveman -> Deutsch-Uebersetzer ist noch im Bau.

Zusaetzlich bleiben 15 rote Tests. Sie konzentrieren sich weiterhin auf Kerninvarianten: Autonomie-Aktivierung, Causal Credit, EntityOS-Artefaktautoritaet, Final-Acceptance/EffectGate, Inference->EffectGate und Re-ingest-before-effect, Memory-Privacy, Runtime-Adapter, Service/DB-Schluss, State-Authority und fail-closed tmux timeout.

## Interpretation

Die Fertigstellungsreife ist gegen 05:18Z klar gestiegen. Der Sprung kommt nicht nur aus einer Zielzahl, sondern aus vier voneinander getrennten Signalen: weniger rote Tests, stabiler Testtrend, mehr reale Zero-Episoden und Generationswechsel. Trotzdem ist EntityOS noch kein belastbar abgenommener Release Candidate, weil die verbliebenen roten Tests mehrere Sicherheits-/Kausalitaetsinvarianten betreffen und zentrale Produktfaehigkeiten (MCP-Werkzeuge, Retrieval-Lernen, Provider-Erreichbarkeit) weiterhin faktisch 0 bzw. offen sind.

Die groesste Diskrepanz bleibt: Architektur und Grundbetrieb sind weit fortgeschritten, waehrend autonome Wirkung/Lernen empirisch noch duenn belegt sind. Es gibt weiterhin nur 1 verifizierte Wirkung, 0 durable memories, 0 retrieval feedback und 0 gelernte entrypoints.

## Naechster Informationsgewinn

Der groesste Acceptance-Sprung kommt nicht durch weitere Exportdaten allein, sondern durch:

1. rote Kerninvarianten systematisch reduzieren;
2. MCP-Werkzeugpfad real freigeben und mit mehreren verifizierten Effects pruefen;
3. mindestens 10 verifizierte Effects erreichen, damit Effect Success Rate und weitere Sensoren tragfaehig werden;
4. Retrieval-Feedback/Entry-Point-Lernen erstmals aktiv beobachten;
5. Generation-31-vs-32 Recovery-/Verhaltensvergleich ausfuehren.

## Evidenzgrenze

Die Prozentwerte fuer funktionalen Kern und Acceptance sind Forschungsbewertungen, keine vom System selbst ausgegebenen Messwerte. 22/28 aktive Ziele und 478/15 Tests sind direkt gemessen. Ein erfuelltes Ziel `Testsuite traegt` darf nicht mit `alle Tests gruen` verwechselt werden.

# Tresor-Kataloge

Automatisch erzeugt 2026-08-22T18:06:45Z. Zwei AES-256-GCM-Tresore unter `/etc/entityos/tresor` -- `katalog()` zeigt WAS es gibt und WAS es KANN (Modell, Limits je Minute/Tag, Zweck), nie den Wert selbst. `oeffnen()`/`wert()` liefern den Klartext und werden von diesem Export nie aufgerufen.

## api (28 Eintraege)

| Kennung | Art/Anbieter | Zweck | Quelle | Sonstiges |
|---|---|---|---|---|
| GROQ_API_KEY | GROQ | schnelle Modelle, Schema-Antwort und Kondensieren | /etc/clayverse/freie-zugaenge.env | groq_llama31_8b: llama-3.1-8b-instant (60/min, 28800/Tag); groq_gptoss_20b: openai/gpt-oss-20b (60/min, 2000/Tag); groq_gptoss_120b: openai/gpt-oss-120b (60/min, 2000/Tag); groq_llama33_70b: llama-3.3 |
| GEMINI_API_KEY | GEMINI | langer Kontext | /etc/clayverse/freie-zugaenge.env | gemini_flash_lite_latest: gemini-flash-lite-latest (-/min, -/Tag); gemini_flash_latest: gemini-flash-latest (-/min, -/Tag); gemini_embedding_001: gemini-embedding-001 (-/min, 1500/Tag) |
| GEMINI2_API_KEY | GEMINI2 | unbekannt -- nicht geraten | /etc/clayverse/freie-zugaenge.env | keine Bahnangabe vorhanden |
| DEEPSEEK_API_KEY | DEEPSEEK | Zweitmeinung | /etc/clayverse/freie-zugaenge.env | deepseek_chat: deepseek-chat (-/min, -/Tag) |
| OPENROUTER_API_KEY | OPENROUTER | Sammelzugang zu vielen Modellen | /etc/clayverse/freie-zugaenge.env | openrouter_frei: - (40/min, 100/Tag) |
| NVIDIA_NIM_API_KEY | NVIDIA | Einbettungen und Umsortieren | /etc/clayverse/freie-zugaenge.env | nvidia_nim: - (40/min, -/Tag) |
| CLOUDFLARE_API_KEY | CLOUDFLARE | Randbetrieb | /etc/clayverse/freie-zugaenge.env | cloudflare_workers_ai: - (3000/min, 10000/Tag) |
| HF_TOKEN | HF | Modelle und Datensaetze | /etc/clayverse/freie-zugaenge.env | hf_inference: - (-/min, -/Tag) |
| MISTRAL_API_KEY | MISTRAL | Vorstufe und Uebersetzer -- der meistgenutzte Zugang | /etc/clayverse/freie-zugaenge.env | mistral_small: mistral-small-latest (-/min, -/Tag) |
| GROQ2_API_KEY | GROQ2 | unbekannt -- nicht geraten | /etc/clayverse/freie-zugaenge.env | keine Bahnangabe vorhanden |
| MISTRAL2_API_KEY | MISTRAL2 | unbekannt -- nicht geraten | /etc/clayverse/freie-zugaenge.env | keine Bahnangabe vorhanden |
| MISTRAL3_API_KEY | MISTRAL3 | unbekannt -- nicht geraten | /etc/clayverse/freie-zugaenge.env | keine Bahnangabe vorhanden |
| NVIDIA2_API_KEY | NVIDIA2 | unbekannt -- nicht geraten | /etc/clayverse/freie-zugaenge.env | keine Bahnangabe vorhanden |
| TAVILY_API_KEY | TAVILY | Websuche zur Erdung | /etc/clayverse/freie-zugaenge.env | tavily: - (-/min, -/Tag) |
| EXA_API_KEY | EXA | Websuche, semantisch | /etc/clayverse/freie-zugaenge.env | exa: - (-/min, -/Tag) |
| E2B_API_KEY | E2B | unbekannt -- nicht geraten | /etc/clayverse/freie-zugaenge.env | e2b: - (-/min, -/Tag) |
| OPENALEX_API_KEY | OPENALEX | wissenschaftliche Literatur | /etc/clayverse/freie-zugaenge.env | openalex: - (-/min, -/Tag) |
| RAPIDAPI_KEY | RAPIDAPI | Sammelzugang zu Fremd-APIs | /etc/clayverse/freie-zugaenge.env | rapidapi: - (-/min, -/Tag) |
| NVIDIA3_API_KEY | NVIDIA3 | unbekannt -- nicht geraten | /etc/clayverse/freie-zugaenge.env | keine Bahnangabe vorhanden |
| OPENROUTER2_API_KEY | OPENROUTER2 | unbekannt -- nicht geraten | /etc/clayverse/freie-zugaenge.env | keine Bahnangabe vorhanden |
| GROQ3_API_KEY | GROQ3 | unbekannt -- nicht geraten | /etc/clayverse/freie-zugaenge.env | keine Bahnangabe vorhanden |
| CLERK_SECRET_KEY | CLERK | Anmeldung serverseitig -- KEIN Modellzugang | /etc/clayverse/freie-zugaenge.env | keine Bahnangabe vorhanden |
| CLERK_PUBLISHABLE_KEY | CLERK | Anmeldung im Browser (oeffentlich) | /etc/clayverse/freie-zugaenge.env | keine Bahnangabe vorhanden |
| CLERK_JWKS_URL | CLERK | Schluesselverzeichnis der Anmeldung (oeffentlich) | /etc/clayverse/freie-zugaenge.env | keine Bahnangabe vorhanden |
| CLERK_WEBHOOK_SECRET | CLERK | Rueckrufe der Anmeldung pruefen | /etc/clayverse/freie-zugaenge.env | keine Bahnangabe vorhanden |
| GLM_API_KEY | GLM | Modellzugang | /etc/clayverse/freie-zugaenge.env | keine Bahnangabe vorhanden |
| NEUROPEDIA_API_KEY | NEUROPEDIA | oeffentliche Forschungsmodelle | /etc/clayverse/freie-zugaenge.env | keine Bahnangabe vorhanden |
| GH_TOKEN | GITHUB | GitHub nutzerweit -- kann Repos auflisten, anders als der Deploy-Key | /etc/clayverse/github-token.env | github-api: - (-/min, -/Tag) |

## zugaenge (30 Eintraege)

| Kennung | Art/Anbieter | Zweck | Quelle | Sonstiges |
|---|---|---|---|---|
| ENTITYOS_POSTFACH_GABRIEL_ADRESSE | postfach |  | /etc/entityos/postfach.env | nicht geheim |
| ENTITYOS_POSTFACH_GABRIEL_PASSWORT | postfach |  | /etc/entityos/postfach.env | geheim |
| ENTITYOS_POSTFACH_ANDREAS_ADRESSE | postfach |  | /etc/entityos/postfach.env | nicht geheim |
| ENTITYOS_POSTFACH_ANDREAS_PASSWORT | postfach |  | /etc/entityos/postfach.env | geheim |
| ENTITYOS_IMAP_HOST | postfach |  | /etc/entityos/postfach.env | nicht geheim |
| ENTITYOS_IMAP_PORT | postfach |  | /etc/entityos/postfach.env | nicht geheim |
| ENTITYOS_SMTP_HOST | postfach |  | /etc/entityos/postfach.env | nicht geheim |
| ENTITYOS_SMTP_PORT | postfach |  | /etc/entityos/postfach.env | nicht geheim |
| CLERK_ISSUER | betrieb |  | /etc/clayverse/entityos-deploy.env | nicht geheim |
| CLERK_JWKS_URL | betrieb |  | /etc/clayverse/entityos-deploy.env | nicht geheim |
| CLERK_FRONTEND_API_URL | betrieb |  | /etc/clayverse/entityos-deploy.env | nicht geheim |
| CLERK_AUTHORIZED_PARTIES | betrieb |  | /etc/clayverse/entityos-deploy.env | nicht geheim |
| CLAYVERSE_CLERK_MAP_JSON | betrieb |  | /etc/clayverse/entityos-deploy.env | nicht geheim |
| CLERK_PUBLISHABLE_KEY | betrieb |  | /etc/clayverse/entityos-deploy.env | geheim |
| CLAYVERSE_ENTITYOS_SHA256 | betrieb |  | /etc/clayverse/entityos-deploy.env | geheim |
| CLERK_ISSUER | anmeldung |  | /etc/clayverse/entityos-clerk.env | nicht geheim |
| CLERK_JWKS_URL | anmeldung |  | /etc/clayverse/entityos-clerk.env | nicht geheim |
| CLERK_FRONTEND_API_URL | anmeldung |  | /etc/clayverse/entityos-clerk.env | nicht geheim |
| CLERK_AUTHORIZED_PARTIES | anmeldung |  | /etc/clayverse/entityos-clerk.env | nicht geheim |
| CLAYVERSE_CLERK_MAP_JSON | anmeldung |  | /etc/clayverse/entityos-clerk.env | nicht geheim |
| CLOUDFLARE_API_KEY | betrieb |  | /etc/clayverse/keys.env | geheim |
| DEEPSEEK_API_KEY | betrieb |  | /etc/clayverse/keys.env | geheim |
| GEMINI_API_KEY | betrieb |  | /etc/clayverse/keys.env | geheim |
| GEMINI2_API_KEY | betrieb |  | /etc/clayverse/keys.env | geheim |
| GROQ_API_KEY | betrieb |  | /etc/clayverse/keys.env | geheim |
| HF_API_KEY | betrieb |  | /etc/clayverse/keys.env | geheim |
| MISTRAL_API_KEY | betrieb |  | /etc/clayverse/keys.env | geheim |
| NVIDIA_NIM_API_KEY | betrieb |  | /etc/clayverse/keys.env | geheim |
| OPENROUTER_API_KEY | betrieb |  | /etc/clayverse/keys.env | geheim |
| SEIMENSCH_REPO_REMOTE | zugangsroute | Git-Remote des SeiMensch-Repos; keyless SSH ist eingerichtet | eigner:CLAUDE.md | geheim |


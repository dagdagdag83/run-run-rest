# ARCHITECTURE.md: Agentic Fitness Harness

## 1. Project Overview
An AI-driven fitness tracker operating as an autonomous coach. It ingests exercise data, maintains long-term contextual memory, and interacts via distinct personas using agentic orchestration.

## 2. Technology Stack
* **Core:** Python 3.14, `uv` (package manager), FastAPI (backend & static UI).
* **AI & Infrastructure:** Google Gemini API, Google Cloud Run (serverless container), Google Cloud Firestore (NoSQL).
* **Integrations:** Zitadel (Auth), Strava API (webhooks).
* **DevOps:** Standard `Dockerfile`, `python-json-logger` (GCP-compatible stdout logging).

## 3. Core Principles
* **KISS:** Single container, single database. No complex frontend frameworks or layered architectures (though a flat `routers/` folder structure is permitted to organize endpoints).
* **Statelessness:** Cloud Run instances hold no global state. Context is dynamically loaded per request and wiped.
* **Scale-to-Zero:** Compute runs only during active chats, UI loads, or incoming webhooks.
* **Interface/Implementor:** Abstract external services (Firestore, Zitadel, Strava, Gemini) behind interfaces.
* **Local Mocking:** Use in-memory mocks for external services during local development for instant, offline testing.

## 4. System Flow
* **UI & Auth:** FastAPI serves `index.html`. Users log in via Zitadel. The frontend sends JWTs to the backend, which verifies them and maps the user to their Strava ID.
* **Webhook Pipeline (Ingestion):** Strava posts data to `/webhook`. The backend strips JSON noise, injects environmental data (e.g., weather), has the AI generate a narrative, and saves the record.
* **Chat Pipeline (Interaction):** User sends a message to `/chat`. The backend loads recent context and milestones. The AI responds using its persona, calling tools to fetch older data if needed.

## 5. Memory Architecture (Firestore)
Strict isolation to prevent state bleed:
* `users/{user_id}` (Profile data, persona, goals)
    * `workouts/` (Raw and compressed Strava ledger)
    * `chat_sessions/` (Short-term active conversation context)
    * `insights/` (Cron-generated weekly summaries)
    * `milestones/` (High-signal core memories like PRs and injuries)

## 6. The Agentic Harness (Tools)
The AI is restricted from hallucinating past performance. It must rely on data-fetching tools:
* `get_last_30_days_history`: Returns a dense, token-efficient string of recent workouts.
* `get_summary_history`: Fetches pre-computed weekly summaries for long-term narrative context.
* `record_core_memory`: Silently saves high-signal events from chat directly to the user's milestones.
* `age_graded_benchmark`: Cross-references performance against global age/gender standards.
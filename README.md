# 🏃‍♂️🤖 run-run-rest

## The Highly Opinionated, Autonomous Agentic Running Coach

### Check it out: <a href="https://runrun.rest">https://runrun.rest</a> 👀🤩

**run-run-rest** isn't just a chatbot; it's a serverless, agentic fitness harness operating as your autonomous, long-term athletic coach. Engineered to ingest live webhook data directly from Strava, it maintains a deep, evolving cognitive memory of your physiology, your highs and lows, and your precise training blocks. 

It talks to you through swappable persona modules (want a tough-love Marine or a Data Scientist?), analyzes your kilometer-by-kilometer splits, yells at you for skyrocketing your heart rate in Zone 2, and strictly holds you accountable to your own training directives. 🏋️‍♂️✨

---

## ✨ Project Highlights & Capabilities

### 🧠 Agentic Memory & Contextual Coaching
Built on a robust agentic orchestration loop equipped with dynamic Vertex AI function-calling tools. The coach seamlessly manages its own memory state—silently recording high-signal "Core Memories" (injuries, life stress), tracking your latest milestones (PRs), and managing your biometrics (weight, Max HR). To preserve tokens and speed, the active chat context operates on a strict 7-day sliding window. When you refer back to older conversations, a dedicated "Librarian" sub-agent (running on Gemini Flash Preview) is rapidly spun up to query your historical dataset, extracting relevant advice and bringing it back to the main AI as a dense summary.

### 🎯 Structured Training Blocks & Directives
Shift from passive tracking to active goal-oriented coaching. Define precise "Training Blocks" alongside daily maintenance habits. You can inject "Active Training Directives" (e.g., "Enforce an 80/20 polarized philosophy," or "Focus on half-marathon pacing"), and the AI will proactively check your incoming split data against these strict rules to keep you honest.

### 📡 Automated Pipeline & Environmental Enrichment
Zero manual data entry. Through a highly resilient webhook pipeline, your Strava activity payloads are seamlessly ingested the moment you stop your watch. The backend pipeline maps your GPS runs against the **Open-Meteo API** to pull precise historical weather (was there a crosswind affecting your pace?), and enriches your metadata via tiered physiological algorithms (calculating zones via LTHR > Karvonen > Max HR).

### 🩺 "Scout" Tactical LLM Assessments
Before the primary Coaching Agent even looks at your run, an ultra-fast LLM sub-agent (the "Scout" running on Gemini Flash-Lite) intercepts the webhook stream. It automatically analyzes your pacing strategy and cardiac drift in the background, attaching a pristine clinical metadata summary to your Firestore record for an instant, unbiased tactical overview.

### 📊 Granular Split Analysis
Forget simple distance and time. The agent proactively queries your runs down to the kilometer-by-kilometer level—extracting pace gradients, active vs rest times, and specific heart rate loops. Coupled with the integrated Workout Notes tools, it bridges the gap between quantitative metrics and your subjective RPE (Rate of Perceived Exertion).

### 📈 Multimodal Stream Visualization
Numbers only tell half the story. The agent leverages Plotly to dynamically generate real-time visual telemetry (Heart Rate vs. Pace streams) entirely in memory. It feeds this Base64-encoded PNG directly into Gemini's Vision API as a multimodal prompt, perfectly diagnosing pacing consistency and cardiac drift while immediately rendering a gorgeous, zoomable chart right inside your chat interface.

---

## 🤖 Anatomy of the Agentic Harness

We built `run-run-rest` to push the limits of what a stateless, single-agent system can achieve using Google Gemini. Here are the core technical feats of the harness architecture:

* **State-Hydrated System Prompts:** Instead of burning tokens forcing the LLM to blindly query for its context every turn, the router architecture dynamically hydrates the System Prompt `<athlete_context>` explicitly pointing to your active Firestore records. The agent instantly knows your `<active_training_block>`, `<active_directives>`, and realtime `<biometrics>` before a single token generates.
* **Idempotent Tool Execution Loop:** A recursive agentic `while` loop processes multiple sequential tool calls (e.g. reading your recent runs, identifying a specific activity, then querying the kilometer splits) inside a single user interaction turn, ensuring the final conversational response is fully informed.
* **Markdown Module Personas:** The agent's cognitive "Persona" is fully decoupled into hot-reloadable `.md` files. Switch from the `SUPPORTIVE_REALIST` to a new archetype instantly without touching the core prompt engine.
* **Autonomous Memory Commitments:** The agent is given explicit behavioral permissions to silently execute `record_core_memory` and `update_workout_notes` tool calls. It doesn't ask permission to save your data; it acts autonomously when it detects high-signal physiological or psychological events.
* **Context Pruning & Librarian Sub-Agents:** The main chat loop dynamically enforces a strict 7-day sliding window on thread history. To combat "amnesia" while preserving lightning-fast generation and low token burn, the active agent can dynamically spawn a dedicated "Librarian" sub-agent (`gemini-3.1-flash-lite-preview`) to execute Retrieval-Augmented Generation (RAG) against years of historical chat logs, returning a highly-dense summary block on demand.

---

## 🛠️ The Tech Details

We designed the architecture to adhere to **KISS** (Keep It Simple, Stupid) and Extreme Programming (XP) principles.

> **Built with AI:** This entire project was built by **Google Gemini** using the **Antigravity** agent framework. 🚀

### 🚀 Core Architecture & Stack
* **Vertical Slice Architecture**: Code is naturally organized by feature (e.g., `src/features/strava/auth`) rather than technical concern. This isolated, feature-first structure is highly optimal for agentic AI coding methodologies.
* **Agentic Engine**: Google GenAI SDK (Gemini 3.1 Flash for the active Coach; Flash-Lite for the webhook Scout) running on Vertex AI.
* **Server**: [FastAPI](https://fastapi.tiangolo.com/) for core REST routing mechanics and static UI serving.
* **Package Management**: [uv](https://github.com/astral-sh/uv) - blazing fast, strict dependency handling for Python 3.14.
* **Auth**: Secure OIDC session management using Zitadel.
* **Storage**: Google Cloud Firestore (NoSQL) for scale-to-zero, extreme-performance stateless memory isolation.
* **Frontend**: Beautiful "Tactical Terminal" built in Vue 3 (Composition API), Vite, and Tailwind CSS.

### 💻 Local Environment Setup

Your local environment gracefully detects Google Cloud credentials or falls back to an in-memory storage mock to save on GCP bills and allow offline development!

1. **Get your Python right:** Ensure you have Python 3.14+ installed.
2. **Install `uv`:** The modern standard for Python environments. (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
3. **Set up Environment Variables:** 
   ```powershell
   Copy-Item .env.example .env
   ```
   *Fill in valid Zitadel API details and a random `SESSION_SECRET_KEY` for the UI login.*
4. **Configure Google Cloud Credentials (Optional but recommended):**
   To test Firestore locally or the Gemini AI integrations, acquire Application Default Credentials. This connects you to a local isolated database (`run-run-rest-local-db`).
   ```powershell
   gcloud auth application-default login
   ```
5. **Build the frontend:**
   ```powershell
   cd frontend
   npm ci
   npm run build
   cd ..
   ```
   *This automatically generates the single `index.html` file into the backend `static/` directory.*
6. **Run the server:**
   ```powershell
   uv run main.py
   ```
   Application spins up on `http://localhost`! 🚀

### 🧪 Automated Testing

We enforce Test-Driven Development (TDD) via `pytest` for the backend and `vitest` for the frontend.
```powershell
# Backend tests
uv run pytest

# Frontend unit tests
cd frontend
npm run test:unit
```

### ☁️ Infrastructure & CI/CD
Deployments are completely automated via GitHub Actions to **Google Cloud Run** using Workload Identity Federation (WIF). 

Configure the following secrets/variables in GitHub (`Settings > Secrets and variables > Actions > Variables`):
* `GCP_PROJECT_ID`
* `GCP_REGION` (e.g. `europe-west1`)
* `GAR_LOCATION` 
* `GAR_REPOSITORY`
* `WIF_PROVIDER` (e.g. `projects/123/locations/global/workloadIdentity...`)
* `WIF_SERVICE_ACCOUNT`

Just push to `main` and let the serverless architecture scale to zero when you stop running!

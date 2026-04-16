<div align="center">
  <h1>🏃‍♂️🤖 run-run-rest</h1>
  <p><strong>The Highly Opinionated, Agentic AI Running Coach </strong></p>
</div>

**run-run-rest** is a serverless, agentic fitness harness that operates as your autonomous personal coach. Designed to seamlessly ingest your continuous exercise data (like from Strava), it maintains deep, long-term contextual memory of your highs, lows, PRs, and injuries. 

It talks to you through distinct personas, analyzes your kilometer splits, complains about your skyrocketing heart rate, and makes sure you never skip leg day. 🏋️‍♂️✨

---

## ✨ Project Highlights & Capabilities

### 🧠 Agentic Memory & Contextual Coaching
It’s not just a wrapper over a chat API. **run-run-rest** utilizes an agentic orchestration loop equipped with dynamic function-calling tools. It accesses your core memories, athlete biometrics, and milestones. It knows if you are nursing an Achilles injury, when your last 5K PR was, and dynamically adjusts its coaching context based on your temporal history.

### 📡 Automated Strava Ingestion
Zero manual data entry. Through a highly integrated webhook pipeline, your raw Strava activity payloads are seamlessly ingested into the platform the moment you finish your run.

### ⛈️ Environmental & Physiological Enrichment 
Once ingested, a run isn't just distance and time. The pipeline cross-references your GPS coordinates and timestamps against the **Open-Meteo API** to pull historical weather conditions (Was it a grueling headwind? Freezing rain?). It then enriches your data with our tiered physiological algorithms, calculating holistic intensity scores and intelligent dynamic heart rate zones (falling back through LTHR > Karvonen > Standard Max HR).

### 🩺 "Scout" Tactical Assessments
Before the primary coaching agent even looks at your run, an ultra-fast LLM sub-agent (the "Scout") automatically analyzes your specific pacing strategy and cardiac drift in the background. It attaches a pristine clinical metadata summary to your workout record so your coach has an instant, unbiased tactical overview.

### 🗣️ Proactive Directives & Personas
Want a drill instructor? Or a supportive yogi? The AI adapts via distinct personas. You can issue "Active Training Directives" (e.g., "Enforce an 80/20 Zone 2 philosophy this block," or "Focus on half-marathon pacing"), and the AI will proactively check your incoming specific split data against these directives to keep you honest.

### 📊 Granular Split Analysis & Qualitative Notes
The agent can query your runs down to the kilometer-by-kilometer level—extracting pace, elevation, and heart rate for deep analytical coaching. You can also provide subjective feedback directly to your database ("Felt sluggish today") using the integrated Workout Notes tools, guaranteeing both qualitative and quantitative context tracking.

---

## 🛠️ The Tech Details

We designed the architecture to adhere to **KISS** (Keep It Simple, Stupid) and Extreme Programming (XP) principles. We use a dedicated Vue 3 / Vite frontend alongside `FastAPI` power serving our agentic AI workflows.

> **Built with AI:** This entire project was created with **Google Gemini** and **Antigravity**! 🚀

### 🚀 Core Architecture & Stack
* **Vertical Slice Architecture**: Code is naturally organized by feature (e.g., `src/features/strava/weather`) rather than technical concern. This isolated, feature-first structure is ideally suited for agentic AI coding.
* **Agentic Engine**: Google GenAI SDK (Gemini 3.1 Flash for the Coach; Flash-Lite for the Scout) running on Vertex AI.
* **Server**: [FastAPI](https://fastapi.tiangolo.com/) for core REST routing mechanics and static UI serving.
* **Package Management**: [uv](https://github.com/astral-sh/uv) - blazing fast, strict dependency handling for Python 3.14.
* **Auth**: Secure OIDC session management using [Authlib](https://docs.authlib.org/) & Zitadel.
* **Storage**: Google Cloud Firestore (NoSQL) for scale-to-zero, stateless memory isolation.
* **Data Validation**: Pydantic.
* **Frontend**: Vue 3 (Composition API), Vite, Tailwind CSS, running inside the `frontend/` directory.

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
6. **Build the frontend:**
   ```powershell
   cd frontend
   npm ci
   npm run build
   cd ..
   ```
   *This automatically generates the single `index.html` file into the `static/` directory.*
7. **Run the server:**
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

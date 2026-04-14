# 🏃‍♂️🤖 run-run-rest 

**run-run-rest** is a highly opinionated, AI-driven fitness tracker that operates as your autonomous personal coach! Designed as an agentic harness, it ingests your continuous exercise data (like from Strava), maintains deep, long-term contextual memory of your highs and lows, and chats with you through distinct personas. It's the fitness tracker that never forgets a PR, and never lets you skip leg day. 🏋️‍♂️✨

## 🚀 Core Dependencies

* **[FastAPI](https://fastapi.tiangolo.com/)**: Core REST routing mechanics & static UI serving.
* **[Authlib](https://docs.authlib.org/)**: Heavy-lifting for OpenID Connect via Zitadel.
* **Google Cloud Firestore**: Abstracted memory persistence.
* **[uv](https://github.com/astral-sh/uv)**: Blazing fast Python packaging and execution.
* **Pydantic**: Robust data validation and typing.

## 🛠️ Local Environment Setup

We keep things extremely simple. Your local runs will dynamically detect your Google Cloud credentials. If Application Default Credentials (ADC) are found, the harness connects to a dedicated local Firestore database (`run-run-rest-local-db`). If no credentials are found (or if they fail), it gracefully falls back to an in-memory storage mock out-of-the-box so you can work locally and offline without racking up GCP bills!

1. **Get your Python right:** Ensure you have Python 3.14+ installed.
2. **Install `uv`:** The modern, lightning-fast standard for Python environments. (e.g. `curl -LsSf https://astral.sh/uv/install.sh | sh`)
3. **Set up your Environment Variables:** 
   Copy the example config into a `.env` file to be picked up by the harness.
   ```powershell
   Copy-Item .env.example .env
   ```
   *Make sure you fill in valid Zitadel API details and a random `SESSION_SECRET_KEY` within the `.env` if you are testing the login UI!*

4. **Configure Google Cloud Credentials:**
   To ensure the Gemini AI integration works locally and to persist testing data to the distinct `run-run-rest-local-db` Firestore instance, you need to acquire Application Default Credentials (ADC).
   ```powershell
   gcloud auth application-default login
   ```

5. **Run the server:**
   Use the built-in `uv` command to run the application entrypoint. This automatically resolves your `pyproject.toml` dependencies and sets up an isolated `.venv`.
   ```powershell
   uv run main.py
   ```
   You should see the application spin up on `http://localhost:8000`! 🚀

## 🧪 Testing the Chat Endpoint (PowerShell)

We use secure, strict session-cookie based Auth. Here's how you can manually test the `/chat` endpoint locally using **PowerShell**:

### Without Valid Auth (Expected to Fail) 🛑
Attempting to hit the chat endpoint unauthenticated will correctly throw a `401 Unauthorized` HTTP exception.
```powershell
# This command expects an HTTP 401 response from FastAPI.
try {
    Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method Post -ErrorAction Stop
} catch {
    Write-Host "Caught expected error: $($_.Exception.Message)" -ForegroundColor Yellow
}
```

### With Valid Auth (Expected to Pass) ✅
Because we are utilizing UI-bound session cookies, you need to manually hijack a valid session for CLI testing. We've created a helper endpoint to make this easy:
1. Fire up your browser and navigate to `http://localhost:8000/`.
2. Hit the login button to authenticate via Zitadel.
3. Once redirected back (with a successful auth callback), open a new tab and go to `http://localhost:8000/dump-cookie`.
4. Copy the value of the `session_cookie` displayed on the page.

```powershell
# Substitute your copied session value here
$sessionCookie = "YOUR_COPIED_COOKIE_VALUE"

# Set up the cookie header
$headers = @{ "Cookie" = "session=$sessionCookie"}
$body = @{ "message" = "Hello Coach! This is PowerShell testing in." } | ConvertTo-Json

try {
    Write-Host "Hitting /chat endpoint..." -ForegroundColor Cyan
    $response = Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method Post -Headers $headers -Body $body -ContentType "application/json"
    
    Write-Host "`n✅ Authentication Successful!" -ForegroundColor Green
    Write-Host "Exchange History:" -ForegroundColor Yellow
    $response.messages | Format-Table role, content -Wrap
} catch {
    Write-Host "`n🛑 Authentication Failed!" -ForegroundColor Red
    if ($_.Exception.Response) {
        Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)"
    }
    Write-Host "Message: $($_.Exception.Message)"
}
```

## 🏗️ Automated Testing

We follow Test-Driven Development (TDD) via `pytest`. We have built-in async interface mocks for storage abstractions, meaning our unit tests are completely decoupled from external latency or GCP. 

To run the entire test suite:
```powershell
uv run pytest
```

---

## ☁️ Infrastructure Configuration (CI/CD)

To enable the automated deployment pipeline to Google Cloud Run via GitHub Actions, the following environment variables and secrets must be configured in your GitHub Repository settings (`Settings > Secrets and variables > Actions > Variables`):

| Variable Name           | Description                                                                                               | Example Value                                       |
| ----------------------- | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| `GCP_PROJECT_ID`        | The Google Cloud Project ID where the application will be deployed.                                       | `run-run-rest`                                      |
| `GCP_REGION`            | The GCP region used for Cloud Run and Artifact Registry.                                                  | `europe-west1`                                       |
| `GAR_LOCATION`          | The location for Google Artifact Registry.                                                                | `europe-west1`                                       |
| `GAR_REPOSITORY`        | The name of the Artifact Registry repository.                                                             | `run-run-rest-repo`                                       |
| `WIF_PROVIDER`          | The full identifier of the Workload Identity Federation Provider used to authenticate GitHub Actions.     | `projects/123/locations/global/workloadIdentity...` |
| `WIF_SERVICE_ACCOUNT`   | The email of the GCP Service Account that the workflow will impersonate via Workload Identity Federation. | `gitblah@run-run-rest.iam.gserviceaccount.com` |

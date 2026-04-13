# runrun.rest

Agentic Fitness Harness

## Infrastructure Configuration

To enable the automated deployment pipeline to Google Cloud Run via GitHub Actions, the following environment variables and secrets must be configured in your GitHub Repository settings (`Settings > Secrets and variables > Actions > Variables`):

| Variable Name           | Description                                                                                               | Example Value                                       |
| ----------------------- | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| `GCP_PROJECT_ID`        | The Google Cloud Project ID where the application will be deployed.                                       | `run-run-rest`                                      |
| `GCP_REGION`            | The GCP region used for Cloud Run and Artifact Registry.                                                  | `europe-west1`                                       |
| `GAR_LOCATION`          | The location for Google Artifact Registry.                                                                | `europe-west1`                                       |
| `GAR_REPOSITORY`        | The name of the Artifact Registry repository.                                                             | `run-run-rest-repo`                                       |
| `WIF_PROVIDER`          | The full identifier of the Workload Identity Federation Provider used to authenticate GitHub Actions.     | `projects/123/locations/global/workloadIdentity...` |
| `WIF_SERVICE_ACCOUNT`   | The email of the GCP Service Account that the workflow will impersonate via Workload Identity Federation. | `gitblah@run-run-rest.iam.gserviceaccount.com` |

## Local Development

1. Ensure `uv` is installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
2. Run tests:
   ```bash
   uv run pytest
   ```
3. Run local server:
   ```bash
   uv run uvicorn main:app --reload
   ```

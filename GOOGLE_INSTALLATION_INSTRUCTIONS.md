# Google Cloud Installation & Run Guide

Step-by-step instructions to set up Google Cloud prerequisites, install dependencies, and run the Brand Guardian AI project.

## 1) Install local tools
- **Python 3.11+**
- **uv** package manager: `pip install uv`
- **Google Cloud CLI**: [install guide](https://cloud.google.com/sdk/docs/install)
- **Docker** (only if building/running the container locally)

## 2) Create or select a Google Cloud project
```bash
gcloud init                      # pick or create a project
gcloud config set project <YOUR_PROJECT_ID>
```

## 3) Enable required Google Cloud APIs
```bash
gcloud services enable \
  aiplatform.googleapis.com \
  speech.googleapis.com \
  videointelligence.googleapis.com \
  storage.googleapis.com \
  cloudtrace.googleapis.com \
  run.googleapis.com
```

## 4) Create a service account and credentials
```bash
SA_NAME=brand-guardian-runner
gcloud iam service-accounts create $SA_NAME --display-name "Brand Guardian Runner"

# Grant minimal roles
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.admin"
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/cloudtrace.agent"
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"

# Create key file for local runs
gcloud iam service-accounts keys create ~/brand-guardian-key.json \
  --iam-account="${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
export GOOGLE_APPLICATION_CREDENTIALS=~/brand-guardian-key.json
gcloud auth application-default login
```

## 5) Create a GCS bucket for staging artifacts
```bash
GCS_BUCKET_NAME=brand-guardian-${GCP_PROJECT_ID}
gsutil mb -l us-central1 gs://${GCS_BUCKET_NAME}
```

## 6) Clone the repo and install dependencies
```bash
git clone <repo-url>
cd ComplianceQAPipeline
uv sync
```

## 7) Configure environment variables
Create a `.env` file in the repo root:
```env
GCP_PROJECT_ID=<YOUR_PROJECT_ID>
GCP_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-2.0-flash-001
GCS_BUCKET_NAME=${GCS_BUCKET_NAME}
VECTOR_STORE_TYPE=chromadb
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/brand-guardian-key.json
```

Optional observability:
```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<your-langsmith-key>
```

## 8) Precompute embeddings (run once)
```bash
uv run python backend/scripts/index_documents.py
```

## 9) Run the application
- **CLI audit:** `uv run python main.py`
- **API server:** `uv run uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8080 --reload`
- **Streamlit UI:** `uv run streamlit run frontend/app.py`

## 10) (Optional) Run tests
```bash
uv run pytest backend/tests -v
```

## 11) (Optional) Build & deploy to Cloud Run
```bash
docker build -t brand-guardian-ai .
docker run -p 8080:8080 --env-file .env brand-guardian-ai

gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/brand-guardian-ai
gcloud run deploy brand-guardian-ai \
  --image gcr.io/$GCP_PROJECT_ID/brand-guardian-ai \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=$GCP_PROJECT_ID,GCP_LOCATION=us-central1
```

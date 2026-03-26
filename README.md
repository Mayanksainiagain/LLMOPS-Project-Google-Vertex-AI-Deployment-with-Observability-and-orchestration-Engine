# 🛡️ Brand Guardian AI — LLMOps on Google Cloud

> **LLM-powered video compliance auditing** built on Google Vertex AI, LangGraph, and deployed on Google Cloud Run with full observability.

---

## 📖 Overview

**Brand Guardian AI** is an end-to-end LLMOps project that automatically audits YouTube advertising videos for compliance with FTC influencer guidelines and YouTube ad specifications. It combines Google Cloud's AI services with a LangGraph orchestration engine to deliver structured compliance reports.

### What it does

1. **Downloads** a YouTube video using `yt-dlp`
2. **Transcribes** the audio with Google Cloud Speech-to-Text V2
3. **Extracts on-screen text** via Google Cloud Video Intelligence API (OCR)
4. **Retrieves compliance rules** from a vector store (ChromaDB + Vertex AI embeddings) using RAG
5. **Generates a compliance report** with Gemini 2.0 Flash via Vertex AI
6. **Exposes results** through a FastAPI REST endpoint and a Streamlit dashboard

---

## 🏗️ Architecture

```
YouTube URL
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Workflow                        │
│                                                             │
│  [index_documents] → [download_video] → [extract_audio]     │
│       │                                       │             │
│       │ (error)                               ▼             │
│       └──────────────────────────→ [speech_to_text]         │
│                                       │                     │
│                                       ▼                     │
│                               [video_intelligence]          │
│                                       │                     │
│                                       ▼                     │
│                              [compliance_check] ←── RAG     │
│                                       │         (ChromaDB + │
│                                       ▼          Vertex AI) │
│                              [generate_report]              │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
FastAPI (Cloud Run)  ←→  Streamlit Dashboard
     │
     ▼
Cloud Trace / Cloud Monitoring (Observability)
```

### Key Google Cloud Services

| Service | Role |
|---|---|
| **Vertex AI** | Gemini 2.0 Flash (LLM) + text embeddings |
| **Cloud Speech-to-Text V2** | Audio transcription |
| **Cloud Video Intelligence** | On-screen text OCR |
| **Cloud Storage (GCS)** | Video & audio file staging |
| **Cloud Run** | Containerised API deployment |
| **Cloud Trace** | Distributed tracing (OpenTelemetry) |
| **Cloud Monitoring** | Metrics & alerting |

---

## 📁 Project Structure

```
ComplianceQAPipeline/
├── .env                              # 🔑 GCP credentials
├── .python-version                   # Python 3.12
├── pyproject.toml                    # 📦 Dependencies (uv)
├── Dockerfile                        # 🐳 Cloud Run container
├── main.py                           # 🚀 CLI entry point
├── backend/
│   ├── data/
│   │   ├── 1001a-influencer-guide-508_1.pdf   # FTC Influencer Guide
│   │   └── youtube-ad-specs.pdf               # YouTube Ad Specifications
│   ├── scripts/
│   │   └── index_documents.py        # 🔧 Index compliance docs into vector store
│   ├── tests/
│   │   ├── test_nodes.py             # 🧪 Unit tests for graph nodes
│   │   └── test_workflow.py          # 🧪 Integration tests for full workflow
│   └── src/
│       ├── api/
│       │   ├── server.py             # 🌐 FastAPI server (Cloud Run)
│       │   └── telemetry.py          # 📡 OpenTelemetry → Cloud Trace
│       ├── graph/
│       │   ├── state.py              # 📋 LangGraph state schema
│       │   ├── nodes.py              # ⚙️ Workflow nodes (Vertex AI)
│       │   └── workflow.py           # 🔄 Graph definition & conditional edges
│       └── services/
│           └── video_intelligence.py # 🎬 Video Intelligence API client
└── frontend/
    └── app.py                        # 🖥️ Streamlit dashboard
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager (`pip install uv`)
- A Google Cloud project with the following APIs enabled:
  - Vertex AI API
  - Cloud Speech-to-Text API
  - Cloud Video Intelligence API
  - Cloud Storage API
  - Cloud Trace API

👉 For detailed Google Cloud setup (service account, API enablement, bucket, and local auth), see [GOOGLE_INSTALLATION_INSTRUCTIONS.md](./GOOGLE_INSTALLATION_INSTRUCTIONS.md).

### 1. Clone & Install

```bash
git clone <repo-url>
cd ComplianceQAPipeline
uv sync
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-2.0-flash-001
GCS_BUCKET_NAME=your-gcs-bucket
VECTOR_STORE_TYPE=chromadb
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### 3. Index Compliance Documents

Run this once to embed the compliance rule documents into the vector store:

```bash
uv run python backend/scripts/index_documents.py
```

### 4. Run Locally

**CLI mode:**
```bash
uv run python main.py
```

**API server:**
```bash
uv run uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8080 --reload
```

**Streamlit dashboard:**
```bash
uv run streamlit run frontend/app.py
```

---

## 🐳 Docker / Cloud Run Deployment

### Build & run locally with Docker

```bash
docker build -t brand-guardian-ai .
docker run -p 8080:8080 --env-file .env brand-guardian-ai
```

### Deploy to Cloud Run

```bash
# Build and push the image
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/brand-guardian-ai

# Deploy
gcloud run deploy brand-guardian-ai \
  --image gcr.io/$GCP_PROJECT_ID/brand-guardian-ai \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=$GCP_PROJECT_ID,GCP_LOCATION=us-central1
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API status |
| `GET` | `/health` | Health check (Cloud Run probe) |
| `GET` | `/info` | Service configuration info |
| `POST` | `/audit` | Run a compliance audit |
| `GET` | `/docs` | Interactive Swagger UI |

### Example audit request

```bash
curl -X POST http://localhost:8080/audit \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://youtu.be/dT7S75eYhcQ"}'
```

**Response:**
```json
{
  "session_id": "abc123...",
  "video_id": "vid_abc123",
  "status": "FAIL",
  "report": "## Compliance Report\n...",
  "compliance_results": [
    {
      "severity": "CRITICAL",
      "category": "FTC Disclosure",
      "description": "Missing #ad or #sponsored disclosure."
    }
  ],
  "errors": []
}
```

---

## 📊 Observability

This project uses **OpenTelemetry** to export traces and metrics to Google Cloud:

- **Cloud Trace** — distributed tracing across the LangGraph workflow nodes
- **Cloud Monitoring** — metrics dashboards and alerting
- **LangSmith** — LLM-specific tracing for prompt/response logging

Set `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY` in your `.env` to enable LangSmith tracing.

---

## 🧪 Running Tests

```bash
uv run pytest backend/tests/ -v
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **LLM** | Gemini 2.0 Flash (Vertex AI) |
| **Orchestration** | LangGraph |
| **Vector Store** | ChromaDB + Vertex AI Embeddings |
| **API** | FastAPI + Uvicorn |
| **Frontend** | Streamlit |
| **Containerization** | Docker → Cloud Run |
| **Observability** | OpenTelemetry, Cloud Trace, LangSmith |
| **Package Manager** | uv |

---

## 📄 License

This project is for educational and demonstration purposes.

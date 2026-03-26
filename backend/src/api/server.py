"""
Brand Guardian AI — FastAPI Server for Cloud Run.

Zero-cost deployment: Cloud Run free tier handles ~2M requests/month.
"""
import os
import uuid
import json
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Telemetry setup (Cloud Trace — free tier: 5M spans/mo)
from backend.src.api.telemetry import setup_telemetry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("brand-guardian-api")


# ========== LIFESPAN ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events for Cloud Run."""
    logger.info("🚀 Brand Guardian AI starting up...")
    setup_telemetry()
    yield
    logger.info("👋 Brand Guardian AI shutting down.")


# ========== APP ==========
app = FastAPI(
    title="Brand Guardian AI",
    description="LLM-powered video compliance auditor deployed on Google Cloud Run.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Streamlit frontend or any client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== SCHEMAS ==========
class AuditRequest(BaseModel):
    """Request body to start a video compliance audit."""
    video_url: str = Field(..., description="YouTube video URL to audit")
    video_id: str | None = Field(None, description="Optional custom video ID")


class AuditResponse(BaseModel):
    """Response body with audit results."""
    session_id: str
    video_id: str
    status: str
    report: str
    compliance_results: list
    errors: list


# ========== ROUTES ==========
@app.get("/health")
async def health_check():
    """Health check for Cloud Run probes."""
    return {
        "status": "healthy",
        "service": "brand-guardian-ai",
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    """Root endpoint — confirms the API is live."""
    return {
        "message": "Brand Guardian AI is running 🛡️",
        "docs": "/docs",
        "health": "/health",
    }


@app.post("/audit", response_model=AuditResponse)
async def run_audit(request: AuditRequest):
    """
    Run a full compliance audit on a YouTube video.

    Pipeline:
    1. Download video (yt-dlp)
    2. Extract audio → Speech-to-Text V2 (transcript)
    3. Video Intelligence API (OCR — on-screen text)
    4. RAG lookup against compliance rules (ChromaDB + Vertex AI)
    5. Gemini 2.0 Flash generates compliance report
    """
    session_id = str(uuid.uuid4())
    video_id = request.video_id or f"vid_{session_id[:8]}"

    logger.info(f"📋 Audit started: session={session_id}, url={request.video_url}")

    try:
        # Lazy import to avoid slow startup on Cloud Run cold start
        from backend.src.graph.workflow import create_graph

        graph = create_graph()

        initial_state = {
            "video_url": request.video_url,
            "video_id": video_id,
            "compliance_results": [],
            "errors": [],
            "retry_count": 0,
            "indexer_success": False,
        }

        final_state = graph.invoke(initial_state)

        logger.info(f"✅ Audit complete: session={session_id}, status={final_state.get('final_status')}")

        return AuditResponse(
            session_id=session_id,
            video_id=video_id,
            status=final_state.get("final_status", "UNKNOWN"),
            report=final_state.get("final_report", "No report generated."),
            compliance_results=final_state.get("compliance_results", []),
            errors=final_state.get("errors", []),
        )

    except Exception as e:
        logger.error(f"❌ Audit failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/info")
async def service_info():
    """Service info — useful for debugging deployment."""
    return {
        "project_id": os.getenv("GCP_PROJECT_ID", "not set"),
        "location": os.getenv("GCP_LOCATION", "not set"),
        "model": os.getenv("VERTEX_AI_MODEL", "not set"),
        "vector_store": os.getenv("VECTOR_STORE_TYPE", "not set"),
        "bucket": os.getenv("GCS_BUCKET_NAME", "not set"),
    }

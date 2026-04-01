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


# ========== LINKEDIN SCHEMAS ==========

class LinkedInGenerateRequest(BaseModel):
    """Request body to generate a LinkedIn post."""
    topic: str = Field(..., description="Topic or keywords for the post")
    post_type: str = Field("thought_leadership", description="Post type: thought_leadership, announcement, tutorial, success_story")
    industry: str = Field("general", description="Industry: tech, marketing, sales, finance, healthcare, education, general")
    tone: str = Field("professional", description="Desired tone, e.g. professional, casual, inspirational")
    target_audience: str = Field("professionals", description="Description of intended readers")


class LinkedInOptimizeRequest(BaseModel):
    """Request body to optimize an existing post."""
    post: str = Field(..., description="Existing LinkedIn post text to optimize")
    optimize_for: str = Field("engagement", description="Optimization goal: engagement, reach, clicks")
    tone: str | None = Field(None, description="Optional tone override")
    max_length: int | None = Field(None, description="Optional max word count")


class LinkedInHooksRequest(BaseModel):
    """Request body to generate hooks."""
    topic: str = Field(..., description="Post topic or keywords")
    count: int = Field(3, description="Number of hooks to generate (1-5)")


class LinkedInCTAsRequest(BaseModel):
    """Request body to generate CTAs."""
    topic: str = Field(..., description="Post topic or keywords")
    goal: str = Field("engagement", description="CTA goal: engagement, lead_gen, traffic, shares")
    count: int = Field(3, description="Number of CTA variants (1-5)")


class LinkedInHashtagsRequest(BaseModel):
    """Request body to get hashtag suggestions."""
    topic: str = Field(..., description="Post topic or keywords")
    industry: str = Field("general", description="Industry context")
    count: int = Field(5, description="Number of hashtag suggestions (3-10)")


class LinkedInFormatRequest(BaseModel):
    """Request body to format a post."""
    post: str = Field(..., description="Post text to format")


class LinkedInABRequest(BaseModel):
    """Request body to generate A/B variants."""
    topic: str = Field(..., description="Post topic or keywords")
    post_type: str = Field("thought_leadership", description="Post type")
    industry: str = Field("general", description="Industry context")
    variants: int = Field(2, description="Number of variants to generate (2-3)")


class LinkedInAnalyticsRequest(BaseModel):
    """Request body to predict post engagement."""
    post: str = Field(..., description="LinkedIn post text to analyze")


class LinkedInFullOptimizationRequest(BaseModel):
    """Request body for the full optimization pipeline."""
    topic: str = Field(..., description="Post topic or keywords")
    post_type: str = Field("thought_leadership", description="Post type")
    industry: str = Field("general", description="Industry context")
    tone: str = Field("professional", description="Desired tone")
    target_audience: str = Field("professionals", description="Intended readers")


# ========== LINKEDIN ROUTES ==========

@app.post("/linkedin/generate")
async def linkedin_generate(request: LinkedInGenerateRequest):
    """Generate an engaging LinkedIn post from a topic using Claude."""
    try:
        from backend.src.services.linkedin_optimizer import generate_post
        post = generate_post(
            topic=request.topic,
            post_type=request.post_type,
            industry=request.industry,
            tone=request.tone,
            target_audience=request.target_audience,
        )
        return {"post": post}
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"LinkedIn generate failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/linkedin/optimize")
async def linkedin_optimize(request: LinkedInOptimizeRequest):
    """Optimize an existing LinkedIn post for tone, length, and engagement."""
    try:
        from backend.src.services.linkedin_optimizer import optimize_post
        optimized = optimize_post(
            post=request.post,
            optimize_for=request.optimize_for,
            tone=request.tone,
            max_length=request.max_length,
        )
        return {"optimized_post": optimized}
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"LinkedIn optimize failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/linkedin/hooks")
async def linkedin_hooks(request: LinkedInHooksRequest):
    """Generate multiple compelling opening lines (hooks) for a LinkedIn post."""
    try:
        from backend.src.services.linkedin_optimizer import generate_hooks
        hooks = generate_hooks(topic=request.topic, count=request.count)
        return {"hooks": hooks}
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"LinkedIn hooks failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/linkedin/ctas")
async def linkedin_ctas(request: LinkedInCTAsRequest):
    """Generate call-to-action variations to maximize LinkedIn engagement."""
    try:
        from backend.src.services.linkedin_optimizer import generate_ctas
        ctas = generate_ctas(topic=request.topic, goal=request.goal, count=request.count)
        return {"ctas": ctas}
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"LinkedIn CTAs failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/linkedin/hashtags")
async def linkedin_hashtags(request: LinkedInHashtagsRequest):
    """Suggest relevant hashtags for a LinkedIn post."""
    try:
        from backend.src.services.linkedin_optimizer import suggest_hashtags
        hashtags = suggest_hashtags(
            topic=request.topic,
            industry=request.industry,
            count=request.count,
        )
        return {"hashtags": hashtags}
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"LinkedIn hashtags failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/linkedin/format")
async def linkedin_format(request: LinkedInFormatRequest):
    """Apply LinkedIn best-practice formatting with bullet points and emojis."""
    try:
        from backend.src.services.linkedin_optimizer import format_post
        formatted = format_post(post=request.post)
        return {"formatted_post": formatted}
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"LinkedIn format failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/linkedin/ab-variants")
async def linkedin_ab_variants(request: LinkedInABRequest):
    """Create multiple post versions for A/B testing."""
    try:
        from backend.src.services.linkedin_optimizer import generate_ab_variants
        variants = generate_ab_variants(
            topic=request.topic,
            post_type=request.post_type,
            industry=request.industry,
            variants=request.variants,
        )
        return {"variants": variants}
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"LinkedIn A/B variants failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/linkedin/analytics")
async def linkedin_analytics(request: LinkedInAnalyticsRequest):
    """Predict engagement potential and get improvement recommendations."""
    try:
        from backend.src.services.linkedin_optimizer import predict_engagement
        analytics = predict_engagement(post=request.post)
        return analytics
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"LinkedIn analytics failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/linkedin/optimize-full")
async def linkedin_full_optimization(request: LinkedInFullOptimizationRequest):
    """
    Run the complete LinkedIn post optimization pipeline.

    Generates a post, optimizes it, creates hooks/CTAs/hashtags,
    formats it, produces A/B variants, and predicts engagement — in one call.
    """
    try:
        from backend.src.services.linkedin_optimizer import full_optimization
        result = full_optimization(
            topic=request.topic,
            post_type=request.post_type,
            industry=request.industry,
            tone=request.tone,
            target_audience=request.target_audience,
        )
        return result
    except EnvironmentError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"LinkedIn full optimization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

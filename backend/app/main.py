import uuid
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.analyzer import analyze_code
from app.llm import explain_locally, explain_with_provider
from app.models import ExplainRequest, ExplainResponse

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(title="AI Code Explainer API", version="1.0.0")

frontend_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/explain", response_model=ExplainResponse)
async def explain(request: ExplainRequest) -> ExplainResponse:
    code = request.code.strip()
    if not code:
        raise HTTPException(status_code=400, detail="Code snippet cannot be empty.")

    annotations, complexity = analyze_code(request.language, code)

    try:
        llm_result, provider = await explain_with_provider(
            request.language,
            code,
            annotations,
            complexity,
            request.includeOptimization,
        )
    except Exception:
        fallback_result = explain_locally(
            request.language,
            code,
            annotations,
            complexity,
            False,
        )
        llm_result = {
            **fallback_result,
            "optimizedCode": code if request.includeOptimization else None,
            "optimizationSummary": "The selected LLM provider failed, so the backend returned a local explanation.",
        }
        provider = "local-fallback"

    return ExplainResponse(
        id=str(uuid.uuid4()),
        language=request.language,
        explanation=llm_result["explanation"],
        annotations=annotations,
        optimizedCode=llm_result.get("optimizedCode") if request.includeOptimization else None,
        optimizationSummary=llm_result.get("optimizationSummary") if request.includeOptimization else None,
        complexity=complexity,
        provider=provider,
    )

"""
FastAPI application entry point for MediAssist AI.

This module defines the HTTP API for the backend service.  It
exposes endpoints for health checking, report analysis, and
contextual question answering.  The implementation delegates the
heavy lifting to service modules such as ``medical_service.py`` so that
the API layer remains thin and declarative.
"""

from __future__ import annotations

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .medical_service import analyze_report, answer_report_question
from .models import AnalyzeReportResponse, AskReportRequest, AskReportResponse

from .config import settings
print("🚨 MAIN DEBUG KEY:", settings.groq_api_key)


app = FastAPI(title="MediAssist AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Simple health check endpoint.

    Returns a JSON object indicating that the backend is running.  This
    endpoint can be used by the frontend or deployment scripts to
    verify that the service has started successfully.
    """
    return {"status": "ok"}


@app.post("/analyze-report", response_model=AnalyzeReportResponse)
async def analyze_report_endpoint(
    file: UploadFile = File(...),
    language: str = Form("English"),
) -> AnalyzeReportResponse:
    """Endpoint to upload and analyse a medical report.

    Accepts a file upload (image or PDF) and a language selection.  The
    request must be submitted as ``multipart/form-data``.  Returns a
    structured response containing the OCR text, detected parameters,
    explanation and a summary.
    """
    # Validate file extension early.
    ext = (file.filename.rsplit(".", 1)[-1] or "").lower()
    if ext not in settings.allowed_extensions:
        return AnalyzeReportResponse(
            status="error",
            language=language,
            raw_text="",
            summary="",
            abnormal_items=[],
            explanation=f"File type '.{ext}' is not supported.",
            disclaimer="",
        )
    raw_text, summary, parameters, explanation, disclaimer = analyze_report(file, language)
    return AnalyzeReportResponse(
        status="success",
        language=language,
        raw_text=raw_text,
        summary=summary,
        abnormal_items=parameters,
        explanation=explanation,
        disclaimer=disclaimer,
    )


@app.post("/ask-report", response_model=AskReportResponse)
async def ask_report_endpoint(request: AskReportRequest) -> AskReportResponse:
    """Endpoint to answer a follow‑up question about an analysed report.

    The request body must contain the extracted report text, the
    user's question, and optionally the desired answer language.
    """
    answer = answer_report_question(
        report_text=request.report_text,
        question=request.question,
        language=request.language or "English",
    )
    return AskReportResponse(status="success", answer=answer)

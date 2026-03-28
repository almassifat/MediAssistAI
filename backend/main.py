"""
FastAPI application entry point for MediAssist AI.
"""

from __future__ import annotations

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .medical_service import analyze_report, answer_report_question
from .models import AnalyzeReportResponse, AskReportRequest, AskReportResponse


app = FastAPI(
    title="MediAssist AI Backend",
    version="1.0.0",
)


# ---------------- CORS ---------------- #
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- HEALTH ---------------- #
@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


# ---------------- ANALYZE REPORT ---------------- #
@app.post("/analyze-report", response_model=AnalyzeReportResponse)
async def analyze_report_endpoint(
    file: UploadFile = File(...),
    language: str = Form("English"),
) -> AnalyzeReportResponse:

    # ✅ Safe filename handling
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower()

    # ✅ Validate file type
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

    try:
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

    except Exception as e:
        return AnalyzeReportResponse(
            status="error",
            language=language,
            raw_text="",
            summary="",
            abnormal_items=[],
            explanation=f"Failed to process report: {str(e)}",
            disclaimer="",
        )


# ---------------- ASK QUESTION ---------------- #
@app.post("/ask-report", response_model=AskReportResponse)
async def ask_report_endpoint(request: AskReportRequest) -> AskReportResponse:

    try:
        answer = answer_report_question(
            report_text=request.report_text,
            question=request.question,
            language=request.language or "English",
        )

        return AskReportResponse(
            status="success",
            answer=answer
        )

    except Exception as e:
        return AskReportResponse(
            status="error",
            answer=f"Failed to generate answer: {str(e)}"
        )
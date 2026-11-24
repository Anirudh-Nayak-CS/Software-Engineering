from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from infrastructure.config import settings
from services.pipeline import RequirementEngineeringPipeline
from services.pdf_report import create_result_pdf


app = FastAPI(title="Requirement Engineering API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)
pipeline = RequirementEngineeringPipeline()


class RequirementRequest(BaseModel):
    user_requirement: str = Field(min_length=1)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "workflow": "local", "model": settings.model_id}


@app.post("/requirements")
def generate_requirements(request: RequirementRequest) -> dict:
    try:
        result = pipeline.run(request.user_requirement)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "user_requirement": result.user_requirement,
        "requirement_specification": result.requirement_specification,
        "sdlc_recommendation": result.sdlc_recommendation,
    }


class PdfRequest(BaseModel):
    user_requirement: str = Field(min_length=1)
    requirement_specification: str = Field(min_length=1)
    sdlc_recommendation: str = Field(min_length=1)


@app.post("/requirements/pdf")
def download_requirement_pdf(request: PdfRequest) -> Response:
    pdf = create_result_pdf(
        request.user_requirement,
        request.requirement_specification,
        request.sdlc_recommendation,
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="requirement-report.pdf"'},
    )

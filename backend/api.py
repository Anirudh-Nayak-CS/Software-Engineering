from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from services.pipeline import RequirementEngineeringPipeline


app = FastAPI(title="Requirement Engineering API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
pipeline = RequirementEngineeringPipeline()


class RequirementRequest(BaseModel):
    user_requirement: str = Field(min_length=1)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "workflow": "local", "model": "gemini"}


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
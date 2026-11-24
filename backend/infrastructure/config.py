"""Central configuration for the Requirement Engineering Pipeline."""

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIRECTORY / ".env")


def _document_directory() -> Path:
    configured = Path(
        os.getenv(
            "DOCUMENT_DIRECTORY",
            str(BACKEND_DIRECTORY / "data" / "healthcare_documents"),
        )
    ).expanduser()
    if not configured.is_absolute():
        configured = BACKEND_DIRECTORY / configured
    return configured.resolve()

class Settings:
    """Configuration settings with sensible defaults."""

    document_directory: Path = _document_directory()
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_count: int = 8

    requirement_spec_tokens: int = int(os.getenv("REQUIREMENT_SPEC_TOKENS", "4096"))
    sdlc_recommendation_tokens: int = int(os.getenv("SDLC_TOKENS", "2048"))
    requirement_generation_max_seconds: int = int(
        os.getenv("REQUIREMENT_GENERATION_MAX_SECONDS", "160")
    )
    sdlc_generation_max_seconds: int = int(
        os.getenv("SDLC_GENERATION_MAX_SECONDS", "80")
    )
    model_id: str = os.getenv("MODEL_ID", "Qwen/Qwen3-4B-Instruct-2507")
    model_api_base_url: str = os.getenv("MODEL_API_BASE_URL", "").rstrip("/")
    model_api_key: str = os.getenv("MODEL_API_KEY", "")
    model_api_timeout_seconds: int = int(os.getenv("MODEL_API_TIMEOUT", "600"))
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip()
    )
    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("API_PORT", "8000"))

    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def __repr__(self) -> str:
        return (
            f"Settings(\n"
            f"  document_directory={self.document_directory},\n"
            f"  requirement_spec_tokens={self.requirement_spec_tokens},\n"
            f"  model_id={self.model_id}\n"
            f")"
        )


settings = Settings()

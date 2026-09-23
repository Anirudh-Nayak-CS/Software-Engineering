"""
Central configuration for the Requirement Engineering Pipeline.

**Why this matters:**
- Centralized control of timeouts, tokens, and retry logic
- Easy to adjust for direct Gemini API inference
- Environment-based overrides for production vs local
"""

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

    # ========== DOCUMENT RETRIEVAL ==========
    document_directory: Path = _document_directory()
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_count: int = 8  # Top-K chunks with no more than two per source file

    # ========== GEMINI MODEL INFERENCE ==========
    requirement_spec_tokens: int = int(os.getenv("REQUIREMENT_SPEC_TOKENS", "8192"))
    sdlc_recommendation_tokens: int = int(os.getenv("SDLC_TOKENS", "4096"))

    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    gemini_thinking_level: str = os.getenv("GEMINI_THINKING_LEVEL", "minimal")
    gemini_api_timeout_seconds: int = int(os.getenv("GEMINI_API_TIMEOUT", "180"))
    gemini_api_max_retries: int = int(os.getenv("GEMINI_API_RETRIES", "2"))
    gemini_api_retry_delay_seconds: float = float(
        os.getenv("GEMINI_API_RETRY_DELAY", "2.0")
    )

    # ========== PIPELINE ==========
    # Total pipeline timeout (includes retrieval + spec + sdlc)
    pipeline_timeout_seconds: int = int(os.getenv("PIPELINE_TIMEOUT", "600"))  # 10 minutes
    
    # Whether to cache model loads
    cache_model_loads: bool = os.getenv("CACHE_MODELS", "true").lower() == "true"

    # ========== LOGGING ==========
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def __repr__(self) -> str:
        return (
            f"Settings(\n"
            f"  document_directory={self.document_directory},\n"
            f"  requirement_spec_tokens={self.requirement_spec_tokens},\n"
            f"  gemini_model={self.gemini_model},\n"
            f"  gemini_thinking_level={self.gemini_thinking_level},\n"
            f"  gemini_api_timeout={self.gemini_api_timeout_seconds}s,\n"
            f"  gemini_api_max_retries={self.gemini_api_max_retries},\n"
            f"  pipeline_timeout={self.pipeline_timeout_seconds}s\n"
            f")"
        )


# Global settings instance
settings = Settings()


# Environment variables: GEMINI_API_KEY (required), GEMINI_MODEL,
# GEMINI_THINKING_LEVEL, GEMINI_API_TIMEOUT, GEMINI_API_RETRIES, GEMINI_API_RETRY_DELAY,
# REQUIREMENT_SPEC_TOKENS, SDLC_TOKENS, DOCUMENT_DIRECTORY, and LOG_LEVEL.

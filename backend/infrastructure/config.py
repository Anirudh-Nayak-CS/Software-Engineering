"""
Central configuration for the Requirement Engineering Pipeline.

**Why this matters:**
- Centralized control of timeouts, tokens, and retry logic
- Easy to adjust based on Kaggle/local constraints
- Environment-based overrides for production vs local
"""

from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    """Configuration settings with sensible defaults."""

    # ========== DOCUMENT RETRIEVAL ==========
    document_directory: Path = Path("./documents")
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_count: int = 5  # Top-K documents to retrieve

    # ========== MODEL INFERENCE - OPTIMIZED FOR KAGGLE ==========
  
    
 
    generation_tokens: int = int(os.getenv("GENERATION_TOKENS", "1500"))
    
    # Total budget for requirement spec generation
    requirement_spec_tokens: int = int(os.getenv("REQUIREMENT_SPEC_TOKENS", "1000"))
    
    # Total budget for SDLC recommendation
    sdlc_recommendation_tokens: int = int(os.getenv("SDLC_TOKENS", "800"))

    # ========== REMOTE MODEL SERVICE (Kaggle) ==========
    
    model_api_url: str = os.getenv(
        "MODEL_API_URL",
        "https://60f3-8-231-221-96.ngrok-free.app" 
    )
    
    # Timeout for single model API request
    # Kaggle 1800s total limit / 2 requests (spec + sdlc) = 900s max per request
    # But we want safety margin, so:
    # 120s = safe timeout (leaves 600s buffer for local ops)
    model_api_timeout_seconds: int = int(os.getenv("MODEL_API_TIMEOUT", "1800"))
    
    # Retry configuration
    model_api_max_retries: int = int(os.getenv("MODEL_API_RETRIES", "2"))
    model_api_retry_delay_seconds: float = float(os.getenv("MODEL_API_RETRY_DELAY", "2.0"))

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
            f"  generation_tokens={self.generation_tokens},\n"
            f"  model_api_url={self.model_api_url},\n"
            f"  model_api_timeout={self.model_api_timeout_seconds}s,\n"
            f"  model_api_max_retries={self.model_api_max_retries},\n"
            f"  pipeline_timeout={self.pipeline_timeout_seconds}s\n"
            f")"
        )


# Global settings instance
settings = Settings()


# ============================================================================
# ENVIRONMENT VARIABLE REFERENCE
# ============================================================================
"""
Set these environment variables to override defaults:

LOCAL DEVELOPMENT:
  export GENERATION_TOKENS=1500
  export MODEL_API_TIMEOUT=1800
  export MODEL_API_URL=http://localhost:8001

KAGGLE PRODUCTION:
  export MODEL_API_URL=https://your-ngrok-url-here.ngrok-free.app
  export MODEL_API_TIMEOUT=1800
  export PIPELINE_TIMEOUT=600

DEBUGGING:
  export LOG_LEVEL=DEBUG
  export MODEL_API_RETRIES=3
  export MODEL_API_RETRY_DELAY=5.0
"""

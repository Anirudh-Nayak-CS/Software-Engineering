from infrastructure.config import Settings, settings
from services.model_client import GeminiModelClient


def build_lightweight_llm(app_settings: Settings = settings):
    """Return a callable that sends inference directly to Gemini."""
    return GeminiModelClient(app_settings)

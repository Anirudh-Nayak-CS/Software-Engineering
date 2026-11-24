from infrastructure.config import Settings, settings
from services.model_client import QwenModelClient


def build_lightweight_llm(app_settings: Settings = settings):
    """Return a callable that sends generation requests to the Kaggle Qwen server."""
    return QwenModelClient(app_settings)

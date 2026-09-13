from infrastructure.config import Settings, settings
from services.model_client import RemoteModelClient


def build_lightweight_llm(app_settings: Settings = settings):
    """Return a callable that sends model inference to the remote GPU API."""
    return RemoteModelClient(app_settings)

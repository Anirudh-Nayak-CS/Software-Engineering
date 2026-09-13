"""
Remote Model Client with Resilience Features

Features:
- Retry logic with exponential backoff
- Timeout handling
- Better error messages
- Health check before requests
- Request/response logging
"""

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class RemoteModelClient:
    """LangChain-compatible callable that delegates generation to Kaggle.
    
    Includes:
    - Automatic retry with exponential backoff
    - Health check before requests
    - Detailed error messages
    - Request timeout handling
    """

    def __init__(self, app_settings):
        self.settings = app_settings
        self._last_health_check = 0
        self._health_check_interval = 30 

    def _health_check(self) -> bool:
        """Check if remote service is healthy before making request."""
        import httpx
        
        now = time.time()
        if now - self._last_health_check < self._health_check_interval:
            return True  
        
        self._last_health_check = now
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.settings.model_api_url.rstrip('/')}/health",
                    timeout=5
                )
                is_healthy = response.status_code == 200
                status = "✅ HEALTHY" if is_healthy else f"❌ ERROR {response.status_code}"
                logger.info(f"Remote model service: {status}")
                return is_healthy
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

    def __call__(
        self,
        system_prompt: str,
        user_content: str,
        **generation_options,
    ) -> str:
        """Generate text via remote Kaggle model with retry logic.
        
        Args:
            system_prompt: System message for the model
            user_content: User query/prompt
            **generation_options: Model parameters (max_new_tokens, temperature, etc)
            
        Returns:
            Generated text
            
        Raises:
            RuntimeError: If all retries fail or service is down
        """
        import httpx


        if not self._health_check():
            logger.error(
                f"Remote model service appears offline at {self.settings.model_api_url}"
            )
         

        url = f"{self.settings.model_api_url.rstrip('/')}/generate"
        payload = {
            "system_prompt": system_prompt,
            "user_content": user_content,
            "generation_options": generation_options,
        }

       
        for attempt in range(1, self.settings.model_api_max_retries + 1):
            try:
                logger.info(
                    f"[Attempt {attempt}/{self.settings.model_api_max_retries}] "
                    f"Calling {url}"
                )
                logger.debug(f"Payload: {payload}")

                response = httpx.post(
                    url,
                    json=payload,
                    timeout=self.settings.model_api_timeout_seconds,
                )
                response.raise_for_status()

                result = response.json()["text"]
                logger.info(
                    f"✅ Success (attempt {attempt}): "
                    f"Generated {len(result)} characters"
                )
                return result

            except httpx.TimeoutException as exc:
                logger.warning(
                    f"[Attempt {attempt}] Timeout after "
                    f"{self.settings.model_api_timeout_seconds}s"
                )
                if attempt < self.settings.model_api_max_retries:
                    wait_time = (
                        self.settings.model_api_retry_delay_seconds * (2 ** (attempt - 1))
                    )
                    logger.info(f"Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(
                        f"Model inference timeout after {attempt} attempts. "
                        f"Kaggle service may be overloaded or crashed. "
                        f"Check: {self.settings.model_api_url}/health"
                    ) from exc

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                logger.error(
                    f"[Attempt {attempt}] HTTP {status}: {exc.response.text[:200]}"
                )
                
                if status == 404:
                    raise RuntimeError(
                        f"Model endpoint not found at {url}. "
                        f"Kaggle service may not be running. "
                        f"Check the ngrok tunnel and kernel status."
                    ) from exc
                elif status == 502:
                    raise RuntimeError(
                        f"Bad Gateway at {url}. Kaggle backend is unhealthy. "
                        f"Try restarting the Kaggle kernel."
                    ) from exc
                elif status >= 500:
                    if attempt < self.settings.model_api_max_retries:
                        wait_time = (
                            self.settings.model_api_retry_delay_seconds * (2 ** (attempt - 1))
                        )
                        logger.info(
                            f"Server error, retrying in {wait_time:.1f}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        raise RuntimeError(
                            f"Remote server error (HTTP {status}) after {attempt} attempts"
                        ) from exc
                else:
                    raise RuntimeError(
                        f"Remote model request failed: HTTP {status}\n"
                        f"Response: {exc.response.text[:500]}"
                    ) from exc

            except httpx.RequestError as exc:
                logger.error(f"[Attempt {attempt}] Request failed: {exc}")
                if attempt < self.settings.model_api_max_retries:
                    wait_time = (
                        self.settings.model_api_retry_delay_seconds * (2 ** (attempt - 1))
                    )
                    logger.info(f"Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(
                        f"Cannot reach model service at {self.settings.model_api_url}: {exc}"
                    ) from exc

            except Exception as exc:
                logger.error(f"[Attempt {attempt}] Unexpected error: {exc}", exc_info=True)
                if attempt < self.settings.model_api_max_retries:
                    wait_time = (
                        self.settings.model_api_retry_delay_seconds * (2 ** (attempt - 1))
                    )
                    logger.info(f"Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(
                        f"Model inference failed after {attempt} attempts: {exc}"
                    ) from exc

        # Should never reach here
        raise RuntimeError("Model client failed unexpectedly")

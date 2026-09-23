"""Direct Gemini API client with bounded retries."""

import logging
import time

import httpx

logger = logging.getLogger(__name__)


class GeminiModelClient:
    """LangChain-compatible callable that sends prompts directly to Gemini."""

    def __init__(self, app_settings):
        self.settings = app_settings
        if not app_settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is required. Set it in backend/.env or the environment."
            )
        self.endpoint = "https://generativelanguage.googleapis.com/v1beta/interactions"

    def __call__(self, system_prompt: str, user_content: str, **generation_options) -> str:
        """Generate text using Gemini's Interactions API."""
        options = {
            "max_output_tokens": generation_options.get(
                "max_output_tokens", generation_options.get("max_new_tokens", 8192)
            ),
            "thinking_level": generation_options.get(
                "thinking_level", self.settings.gemini_thinking_level
            ),
        }
        if "temperature" in generation_options:
            options["temperature"] = generation_options["temperature"]
        elif generation_options.get("do_sample") is False:
            options["temperature"] = 0
        if "top_p" in generation_options:
            options["top_p"] = generation_options["top_p"]

        payload = {
            "model": self.settings.gemini_model,
            "input": user_content,
            "system_instruction": system_prompt,
            "generation_config": options,
            "store": False,
        }
        headers = {
            "x-goog-api-key": self.settings.gemini_api_key,
            "Content-Type": "application/json",
        }

        for attempt in range(1, self.settings.gemini_api_max_retries + 1):
            try:
                response = httpx.post(
                    self.endpoint,
                    headers=headers,
                    json=payload,
                    timeout=self.settings.gemini_api_timeout_seconds,
                )
                response.raise_for_status()
                body = response.json()
                status = body.get("status", "unknown")
                if status == "incomplete":
                    usage = body.get("usage", {})
                    errors = body.get("errors", [])
                    diagnostic_parts = []
                    if usage:
                        output_tokens = usage.get("total_output_tokens")
                        thought_tokens = usage.get("total_thought_tokens")
                        if output_tokens is not None:
                            diagnostic_parts.append(f"output tokens: {output_tokens}")
                        if thought_tokens is not None:
                            diagnostic_parts.append(f"thought tokens: {thought_tokens}")
                    if errors:
                        diagnostic_parts.extend(
                            error.get("message", str(error)) for error in errors
                        )
                    diagnostic = "; ".join(diagnostic_parts) or "no API diagnostic provided"
                    logger.error("Gemini interaction incomplete: %s", diagnostic)
                    raise RuntimeError(
                        f"Gemini returned an incomplete response ({diagnostic}). "
                        "Confirm the backend restarted with the updated .env settings."
                    )
                if status != "completed":
                    raise RuntimeError(f"Gemini interaction did not complete (status: {status}).")

                output_parts = [
                    part
                    for step in body.get("steps", [])
                    if step.get("type") == "model_output"
                    for part in step.get("content", [])
                    if part.get("type") == "text"
                ]
                text = "".join(part.get("text", "") for part in output_parts).strip()
                if not text:
                    raise RuntimeError("Gemini interaction completed without returning text.")
                logger.info("Gemini generated %d characters", len(text))
                return text
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                detail = exc.response.text[:500]
                if status in (429, 500, 502, 503, 504) and attempt < self.settings.gemini_api_max_retries:
                    delay = self.settings.gemini_api_retry_delay_seconds * 2 ** (attempt - 1)
                    logger.warning("Gemini HTTP %d; retrying in %.1fs", status, delay)
                    time.sleep(delay)
                    continue
                raise RuntimeError(f"Gemini API request failed (HTTP {status}): {detail}") from exc
            except httpx.TimeoutException as exc:
                if attempt < self.settings.gemini_api_max_retries:
                    delay = self.settings.gemini_api_retry_delay_seconds * 2 ** (attempt - 1)
                    logger.warning("Gemini request timed out; retrying in %.1fs", delay)
                    time.sleep(delay)
                    continue
                raise RuntimeError("Gemini API request timed out after retries") from exc
            except httpx.RequestError as exc:
                if attempt < self.settings.gemini_api_max_retries:
                    delay = self.settings.gemini_api_retry_delay_seconds * 2 ** (attempt - 1)
                    logger.warning("Gemini connection failed; retrying in %.1fs", delay)
                    time.sleep(delay)
                    continue
                raise RuntimeError(f"Could not connect to Gemini API: {exc}") from exc

        raise RuntimeError("Gemini model client failed unexpectedly")

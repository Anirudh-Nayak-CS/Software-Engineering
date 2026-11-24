"""HTTP client for the Qwen server running in Kaggle."""

import json
import logging

import httpx

logger = logging.getLogger(__name__)


class QwenModelClient:
    """Callable adapter for an OpenAI-compatible Qwen chat endpoint."""

    def __init__(self, app_settings):
        self.settings = app_settings

    def __call__(self, system_prompt: str, user_content: str, **generation_options) -> str:
        base_url = self.settings.model_api_base_url
        if not base_url:
            raise RuntimeError(
                "MODEL_API_BASE_URL is required. Start the Kaggle Qwen server, "
                "expose it with ngrok, and set the endpoint URL in backend/.env."
            )

        headers = {"Content-Type": "application/json"}
        if self.settings.model_api_key:
            headers["Authorization"] = f"Bearer {self.settings.model_api_key}"

        payload = {
            "model": self.settings.model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": generation_options.get("max_new_tokens", 2048),
            "max_time": generation_options.get("max_time", 80),
            "temperature": generation_options.get("temperature", 0.0),
            "top_p": generation_options.get("top_p", 1.0),
            "stream": True,
        }

        try:
            content_parts = []
            with httpx.stream(
                "POST",
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.settings.model_api_timeout_seconds,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data:
                        continue
                    if data == "[DONE]":
                        break
                    try:
                        event = json.loads(data)
                        choice = event.get("choices", [{}])[0]
                        delta = choice.get("delta", {})
                        message = choice.get("message", {})
                        text = delta.get("content") or message.get("content") or ""
                        if isinstance(text, list):
                            text = "".join(
                                part.get("text", "")
                                for part in text
                                if isinstance(part, dict)
                            )
                        content_parts.append(str(text))
                    except (json.JSONDecodeError, IndexError, TypeError) as exc:
                        raise RuntimeError(
                            "The Kaggle Qwen endpoint returned an invalid stream event."
                        ) from exc
            content = "".join(content_parts)
        except httpx.TimeoutException as exc:
            raise RuntimeError("The Kaggle Qwen endpoint timed out.") from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                "Could not reach the Kaggle Qwen endpoint. Check the configured "
                "endpoint and active ngrok tunnel."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"The Kaggle Qwen endpoint returned HTTP {exc.response.status_code}. "
                "Check the server and model API key."
            ) from exc
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("The Kaggle Qwen endpoint returned an invalid response.") from exc

        result = str(content).strip()
        if not result:
            raise RuntimeError("Qwen completed generation without returning text.")
        logger.info("Qwen endpoint generated %d characters", len(result))
        return result

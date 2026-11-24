import asyncio
import json
import os
import secrets
from threading import Lock

import torch
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse, StreamingResponse
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = os.getenv("MODEL_ID", "Qwen/Qwen3-4B-Instruct-2507")
MODEL_API_KEY = os.getenv("MODEL_API_KEY", "")
if not MODEL_API_KEY:
    raise RuntimeError("Set MODEL_API_KEY before starting the Qwen server.")
if not torch.cuda.is_available():
    raise RuntimeError("Enable a Kaggle GPU accelerator before starting Qwen.")

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,
    device_map="auto",
)
model.eval()
generation_lock = Lock()
app = FastAPI(title="Kaggle Qwen Inference API")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = MODEL_ID
    messages: list[ChatMessage] = Field(min_length=1)
    max_tokens: int = Field(default=2048, ge=1, le=16384)
    max_time: float = Field(default=160.0, ge=1.0, le=180.0)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, gt=0.0, le=1.0)
    stream: bool = False


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "model": MODEL_ID}


def generate_content(request: ChatCompletionRequest) -> str:
    messages = [message.model_dump() for message in request.messages]
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    model_inputs = tokenizer([prompt], return_tensors="pt").to(model.device)
    generation_options = {
        "max_new_tokens": request.max_tokens,
        "max_time": request.max_time,
        "do_sample": request.temperature > 0,
        "pad_token_id": tokenizer.eos_token_id,
    }
    if request.temperature > 0:
        generation_options["temperature"] = request.temperature
        generation_options["top_p"] = request.top_p

    with generation_lock, torch.inference_mode():
        generated = model.generate(**model_inputs, **generation_options)
    generated_ids = generated[0][model_inputs.input_ids.shape[-1] :]
    content = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
    if not content:
        raise RuntimeError("Model returned an empty response")
    return content


def completion_response(content: str) -> dict:
    return {
        "id": "qwen-chat-completion",
        "object": "chat.completion",
        "model": MODEL_ID,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
    }


@app.post("/v1/chat/completions")
async def chat_completion(
    request: ChatCompletionRequest,
    authorization: str | None = Header(default=None),
):
    supplied_key = authorization.removeprefix("Bearer ") if authorization else ""
    if not secrets.compare_digest(supplied_key, MODEL_API_KEY):
        raise HTTPException(status_code=401, detail="Invalid model API key")

    if not request.stream:
        try:
            return JSONResponse(content=completion_response(generate_content(request)))
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    async def events():
        generation = asyncio.create_task(asyncio.to_thread(generate_content, request))
        while not generation.done():
            try:
                await asyncio.wait_for(asyncio.shield(generation), timeout=15)
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"
        try:
            content = await generation
        except RuntimeError as exc:
            yield f"data: {json.dumps({'error': {'message': str(exc)}})}\n\n"
            yield "data: [DONE]\n\n"
            return
        yield f"data: {json.dumps(completion_response(content))}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

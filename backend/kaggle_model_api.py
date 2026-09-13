"""Run this file in the GPU-enabled Kaggle environment.

Install on Kaggle, not in the local virtual environment:
transformers torch accelerate fastapi uvicorn
"""

from functools import lru_cache

from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="Kaggle Model Inference API", version="1.0.0")


async def serve_in_notebook(host: str = "0.0.0.0", port: int = 8001):
    """Serve FastAPI from a notebook that already owns an asyncio event loop."""
    import uvicorn

    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


class GenerationRequest(BaseModel):
    system_prompt: str
    user_content: str
    generation_options: dict = {}


@lru_cache(maxsize=1)
def load_generator():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    model_id = "Qwen/Qwen3-4B-Instruct-2507"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        dtype=torch.float16,
        device_map="auto",
        attn_implementation="sdpa",
    )
    return tokenizer, model


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "kaggle-model"}


@app.post("/generate")
def generate(request: GenerationRequest) -> dict[str, str]:
    import torch

    tokenizer, model = load_generator()
    messages = [
        {"role": "system", "content": request.system_prompt},
        {"role": "user", "content": request.user_content},
    ]
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    input_length = inputs.input_ids.shape[1]
    options = {
        "max_new_tokens": 4096,
        "do_sample": True,
        "temperature": 0.3,
        "top_p": 0.9,
    }
    options.update(request.generation_options)
    with torch.inference_mode():
        outputs = model.generate(**inputs, **options)
    text = tokenizer.decode(
        outputs[0][input_length:],
        skip_special_tokens=True,
    )
    return {"text": text}

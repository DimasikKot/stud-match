import os
import threading
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TextIteratorStreamer,
    TextStreamer,
)

MODEL_NAME = os.getenv("LLM_MODEL", "Qwen/Qwen3-4B")
HF_TOKEN = os.getenv("HF_TOKEN") or None
MAX_NEW_TOKENS = int(os.getenv("LLM_MAX_NEW_TOKENS", "2048"))
THINK_END_TOKEN_ID = 151668  # </think>

llm: dict = {}
gpu_lock = threading.Lock()


def load_model():
    # 4-bit NF4 (~2.5 GB VRAM); GTX 1650 Ti (Turing) has no bf16, so compute in fp16
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    llm["tokenizer"] = AutoTokenizer.from_pretrained(MODEL_NAME, token=HF_TOKEN)
    llm["model"] = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        token=HF_TOKEN,
        dtype=torch.float16,
        device_map="cuda:0",
        quantization_config=quantization_config,
    )
    print(f"VRAM allocated: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    yield
    llm.clear()
    torch.cuda.empty_cache()


app = FastAPI(title="sm-llm-worker", lifespan=lifespan)


class Message(BaseModel):
    role: str
    content: str


class GenerateRequest(BaseModel):
    prompt: str | None = None
    messages: list[Message] | None = None
    max_new_tokens: int = Field(default=MAX_NEW_TOKENS, ge=1, le=32768)
    enable_thinking: bool = True


class GenerateResponse(BaseModel):
    thinking: str
    content: str


def build_inputs(request: GenerateRequest):
    tokenizer, model = llm["tokenizer"], llm["model"]
    messages = [m.model_dump() for m in request.messages or []]
    if request.prompt:
        messages.append({"role": "user", "content": request.prompt})
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=request.enable_thinking,
    )
    return tokenizer([text], return_tensors="pt").to(model.device)


def log_request(request: GenerateRequest):
    last = request.prompt or (request.messages[-1].content if request.messages else "")
    print(f"\n[llm] >>> {last}\n[llm] <<< ", end="", flush=True)


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME, "loaded": "model" in llm}


@app.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest):
    tokenizer, model = llm["tokenizer"], llm["model"]
    model_inputs = build_inputs(request)

    log_streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

    with gpu_lock, torch.inference_mode():
        log_request(request)
        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=request.max_new_tokens,
            streamer=log_streamer,
        )
    output_ids = generated_ids[0][len(model_inputs.input_ids[0]) :].tolist()

    try:
        index = len(output_ids) - output_ids[::-1].index(THINK_END_TOKEN_ID)
    except ValueError:
        index = 0

    thinking = tokenizer.decode(output_ids[:index], skip_special_tokens=True)
    content = tokenizer.decode(output_ids[index:], skip_special_tokens=True)
    return GenerateResponse(thinking=thinking.strip("\n"), content=content.strip("\n"))


@app.post("/generate/stream", response_class=StreamingResponse)
def generate_stream(request: GenerateRequest):
    """Plain-text stream of the answer (thinking is wrapped in <think>...</think>)."""
    tokenizer, model = llm["tokenizer"], llm["model"]
    model_inputs = build_inputs(request)
    streamer = TextIteratorStreamer(
        tokenizer, skip_prompt=True, skip_special_tokens=True
    )

    def run():
        with gpu_lock, torch.inference_mode():
            log_request(request)
            model.generate(
                **model_inputs,
                max_new_tokens=request.max_new_tokens,
                streamer=streamer,
            )

    def stream_and_log():
        for chunk in streamer:
            print(chunk, end="", flush=True)
            yield chunk
        print(flush=True)

    threading.Thread(target=run, daemon=True).start()
    return StreamingResponse(stream_and_log(), media_type="text/plain; charset=utf-8")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def playground():
    return PLAYGROUND_HTML


PLAYGROUND_HTML = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>sm-llm-worker</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 860px; margin: 2rem auto; padding: 0 1rem; }
  textarea { width: 100%; height: 6rem; font: inherit; }
  pre { white-space: pre-wrap; background: #f4f4f4; padding: 1rem; border-radius: 6px; min-height: 4rem; }
  .row { display: flex; gap: 1rem; align-items: center; margin: .5rem 0; }
</style>
</head>
<body>
<h2>sm-llm-worker &mdash; потоковая генерация</h2>
<textarea id="prompt">Расскажи коротко, что такое большие языковые модели.</textarea>
<div class="row">
  <label><input type="checkbox" id="thinking" checked> thinking</label>
  <label>max_new_tokens <input type="number" id="max" value="1024" min="1" style="width:6rem"></label>
  <button id="send">Отправить</button>
  <a href="/docs">Swagger</a>
</div>
<pre id="out"></pre>
<script>
document.getElementById("send").onclick = async () => {
  const out = document.getElementById("out");
  out.textContent = "";
  const res = await fetch("/generate/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt: document.getElementById("prompt").value,
      enable_thinking: document.getElementById("thinking").checked,
      max_new_tokens: Number(document.getElementById("max").value),
    }),
  });
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    out.textContent += decoder.decode(value, { stream: true });
  }
};
</script>
</body>
</html>
"""

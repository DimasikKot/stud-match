import json
import threading

import torch
from app.config import settings
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

PROMPT_VERSION = "skills-v1"
MODEL_VERSION = f"{settings.LLM_MODEL_NAME}|{PROMPT_VERSION}"

llm: dict = {}
gpu_lock = threading.Lock()

SYSTEM_PROMPT = (
    "Ты анализируешь фрагмент студенческой работы и определяешь профессиональные "
    "навыки студента, которые проявились в тексте.\n"
    "Верни только JSON без пояснений и без markdown в формате: "
    '{"навык": {"value": число от 0 до 1, "confidence": число от 0 до 1}}.\n'
    "value это оценка владения навыком по объёму его использования и сложности "
    "применения в тексте: 0.1 простое упоминание, 0.5 уверенное применение в "
    "типовых задачах, 0.9 сложное и глубокое применение.\n"
    "confidence это твоя уверенность в этой оценке.\n"
    "Названия навыков пиши строчными буквами, короткими общепринятыми названиями, "
    "например: python, sql, машинное обучение, анализ данных.\n"
    "Не включай личные качества и навыки, которые не подтверждены текстом. "
    "Не более 15 навыков. Если навыков нет, верни {}."
)


def load_model() -> None:
    print("запуск модели", flush=True)
    # Четырёхбитное квантование NF4, вычисления в fp16 (видеокарта без bf16)
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    llm["tokenizer"] = AutoTokenizer.from_pretrained(
        settings.LLM_MODEL_NAME, token=settings.HF_TOKEN
    )
    llm["model"] = AutoModelForCausalLM.from_pretrained(
        settings.LLM_MODEL_NAME,
        token=settings.HF_TOKEN,
        dtype=torch.float16,
        device_map="cuda:0",
        quantization_config=quantization_config,
    )
    print(
        f"[features] model {settings.LLM_MODEL_NAME} loaded, "
        f"VRAM {torch.cuda.memory_allocated() / 1024**3:.2f} GB",
        flush=True,
    )


def unload_model() -> None:
    llm.clear()
    torch.cuda.empty_cache()


def is_loaded() -> bool:
    return "model" in llm


def _clamp(value: float) -> float:
    return round(min(1.0, max(0.0, value)), 2)


def _normalize_name(raw: str) -> str:
    return " ".join(raw.split()).lower()[:64]


def parse_skills(answer: str) -> dict[str, dict[str, float]]:
    """Разбирает ответ модели. При невалидном JSON бросает ValueError."""
    start = answer.find("{")
    end = answer.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("в ответе модели нет JSON")
    data = json.loads(answer[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("ответ модели не является объектом")

    skills: dict[str, dict[str, float]] = {}
    for raw_name, raw_item in data.items():
        if not isinstance(raw_name, str):
            continue
        name = _normalize_name(raw_name)
        if not name:
            continue
        try:
            if isinstance(raw_item, dict):
                value = float(raw_item["value"])
                confidence = float(raw_item.get("confidence", 0.5))
            else:
                value = float(raw_item)
                confidence = 0.5
        except (KeyError, TypeError, ValueError):
            continue
        value = _clamp(value)
        if value <= 0:
            continue
        skills[name] = {"value": value, "confidence": _clamp(confidence)}
    return skills


def extract_chunk_skills(chunk: str) -> dict[str, dict[str, float]]:
    tokenizer, model = llm["tokenizer"], llm["model"]
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Фрагмент работы:\n\n{chunk}"},
    ]
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer([text], return_tensors="pt").to(model.device)
    with gpu_lock, torch.inference_mode():
        output = model.generate(
            **inputs,
            max_new_tokens=settings.LLM_MAX_NEW_TOKENS,
            do_sample=False,
            temperature=None,
            top_p=None,
            top_k=None,
        )
    answer = tokenizer.decode(
        output[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True
    )
    return parse_skills(answer)


def merge_skills(
    per_chunk: list[dict[str, dict[str, float]]],
) -> dict[str, dict[str, float]]:
    """Объединяет навыки со всех чанков файла: value берётся максимальный,
    confidence усредняется по чанкам, где навык встретился."""
    values: dict[str, list[float]] = {}
    confidences: dict[str, list[float]] = {}
    for skills in per_chunk:
        for name, item in skills.items():
            values.setdefault(name, []).append(item["value"])
            confidences.setdefault(name, []).append(item["confidence"])
    return {
        name: {
            "value": _clamp(max(values[name])),
            "confidence": _clamp(sum(confidences[name]) / len(confidences[name])),
        }
        for name in values
    }

import json
import threading

import torch
from app.config import settings
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

PROMPT_VERSION = "skills-v1"
MODEL_VERSION = f"{settings.LLM_MODEL_NAME}|{PROMPT_VERSION}"

llm: dict = {}
gpu_lock = threading.Lock()

SYSTEM_PROMPT = """
    Ты анализируешь фрагмент студенческой работы и определяешь профессиональные навыки студента, которые проявились в тексте.
    Верни только JSON без пояснений, без markdown, только в формате: `{"навык": {"value": float число от 0 до 1 (типо 0.34), "confidence": float число от 0 до 1 (типо 0.8)},"навык2": {"value": float число от 0 до 1, "confidence": float число от 0 до 1 (типо 0.6)} ...}`.
    skill, например: python, sql, машинное обучение, анализ данных.
    value это оценка владения навыком по объёму его использования и сложности применения в тексте.
    confidence это твоя уверенность в этой оценке (чем больше значение, тем выше уверенность), оченивай очень строго.
    Названия навыков пиши строчными буквами, короткими общепринятыми названиями.
    Не включай личные качества и навыки, которые не подтверждены текстом.
    Не более 15 навыков. Если навыков нет, верни `{}`.
    Не добавляй никаких дополнительных полей в ответ.
    Не добавляй никаких дополнительных символов в ответ, только один JSON, без повторов навыков.
"""


def load_model() -> None:
    print("[features] Загрузка модели...", flush=True)
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
        f"[features] Модель {settings.LLM_MODEL_NAME} загружена, "
        f"VRAM {torch.cuda.memory_allocated() / 1024**3:.2f} GB",
        flush=True,
    )


def unload_model() -> None:
    print("[features] Выгрузка модели...", flush=True)
    llm.clear()
    torch.cuda.empty_cache()
    print("[features] Модель выгружена", flush=True)


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
    print(f"LLM response for chunk: {answer}\n", flush=True)
    parsed = parse_skills(answer)
    print(f"Parsed skills: {json.dumps(parsed, ensure_ascii=False)}\n", flush=True)
    print(f"Raw chunk: {chunk}\n", flush=True)
    print("\n" + "-" * 80 + "\n", flush=True)
    return parsed


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

import json
import os
import re
import threading

import torch
from app.config import settings
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

MODEL_VERSION = f"mbart_pos|{settings.MBART_MODEL_PATH}"

llm: dict = {}
gpu_lock = threading.Lock()


def _model_path() -> str:
    path = settings.MBART_MODEL_PATH
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", path))


def load_model() -> None:
    model_path = _model_path()
    print(f"[features-mbart] loading model from {model_path}", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    if settings.MBART_SRC_LANG and hasattr(tokenizer, "src_lang"):
        tokenizer.src_lang = settings.MBART_SRC_LANG

    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_path,
        dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="cuda:0" if torch.cuda.is_available() else "cpu",
    )
    model.eval()

    llm["tokenizer"] = tokenizer
    llm["model"] = model
    if torch.cuda.is_available():
        print(
            f"[features-mbart] model loaded, VRAM {torch.cuda.memory_allocated() / 1024**3:.2f} GB",
            flush=True,
        )
    else:
        print("[features-mbart] model loaded on CPU", flush=True)


def unload_model() -> None:
    llm.clear()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def is_loaded() -> bool:
    return "model" in llm


def _normalize_tag(raw: str) -> str:
    tag = raw.strip().strip("<>").strip("/:-")
    tag = re.sub(r"\s+", " ", tag)
    return tag[:64]


def _add_tag(tags: set[str], raw: str) -> None:
    tag = _normalize_tag(raw)
    if tag and not tag.lower() in {"o", "b", "i", "u", "l"}:
        tags.add(tag.lower())


def _extract_angle_brackets(text: str) -> set[str]:
    tags = set()
    for match in re.finditer(r"<\s*([A-Za-zА-Яа-я_][A-Za-zА-Яа-я_0-9\-]*)\s*>", text):
        _add_tag(tags, match.group(1))
    return tags


def _extract_slash_tags(text: str) -> set[str]:
    tags = set()
    for match in re.finditer(r"\b[\wА-Яа-яёЁ-]+/([A-ZА-ЯЁ_][A-ZА-ЯЁ_0-9\-]*)\b", text):
        _add_tag(tags, match.group(1))
    return tags


def _extract_bio_tags(text: str) -> set[str]:
    tags = set()
    for match in re.finditer(
        r"\b([BIOU])[-_]([A-Za-zА-Яа-я_][A-Za-zА-Яа-я_0-9\-]*)\b", text
    ):
        prefix, tag = match.groups()
        if prefix in {"B", "I", "U", "L"}:
            _add_tag(tags, tag)
    return tags


def _extract_json_tags(text: str) -> set[str]:
    tags = set()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            for key in data.keys():
                _add_tag(tags, str(key))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    _add_tag(tags, item)
    except (json.JSONDecodeError, TypeError):
        pass
    return tags


def _extract_line_tags(text: str) -> set[str]:
    tags = set()
    for line in text.splitlines():
        line = line.strip().strip(".,;:")
        if not line:
            continue
        parts = re.split(r"[\s,;]+", line)
        for part in parts:
            part = part.strip("<>()[]{}\"'")
            if part and len(part) <= 64:
                _add_tag(tags, part)
    return tags


def extract_tags(predicted_text: str) -> list[str]:
    tags = set()
    tags.update(_extract_json_tags(predicted_text))
    tags.update(_extract_angle_brackets(predicted_text))
    tags.update(_extract_slash_tags(predicted_text))
    tags.update(_extract_bio_tags(predicted_text))

    if not tags:
        tags.update(_extract_line_tags(predicted_text))

    return sorted(tags)


def predict_chunk(chunk: str) -> str:
    tokenizer, model = llm["tokenizer"], llm["model"]

    if settings.MBART_SRC_LANG and hasattr(tokenizer, "src_lang"):
        tokenizer.src_lang = settings.MBART_SRC_LANG

    inputs = tokenizer(
        chunk,
        return_tensors="pt",
        max_length=settings.MBART_MAX_INPUT_LENGTH,
        truncation=True,
    ).to(model.device)

    with gpu_lock, torch.inference_mode():
        output = model.generate(
            **inputs,
            max_new_tokens=settings.MBART_MAX_NEW_TOKENS,
            num_beams=settings.MBART_NUM_BEAMS,
            early_stopping=True,
        )

    predicted = tokenizer.decode(output[0], skip_special_tokens=True)
    print(f"[features-mbart] raw prediction: {predicted}", flush=True)
    return predicted


def extract_chunk_tags(chunk: str) -> dict[str, dict[str, float]]:
    predicted = predict_chunk(chunk)
    tags = extract_tags(predicted)
    return {tag: {"value": 1.0, "confidence": 1.0} for tag in tags}

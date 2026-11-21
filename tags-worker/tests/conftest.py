"""Тесты воркера без GPU: torch и transformers подменяются заглушками."""

import contextlib
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class _TextStreamer:
    def __init__(self, tokenizer, skip_prompt=False, **decode_kwargs):
        self.tokenizer = tokenizer

    def on_finalized_text(self, text, stream_end=False):
        pass


def _install_stubs():
    torch = types.ModuleType("torch")
    torch.float16 = "float16"
    torch.inference_mode = contextlib.nullcontext
    torch.cuda = types.SimpleNamespace(
        empty_cache=lambda: None, memory_allocated=lambda: 0
    )
    sys.modules.setdefault("torch", torch)

    transformers = types.ModuleType("transformers")
    transformers.TextStreamer = _TextStreamer
    transformers.TextIteratorStreamer = _TextStreamer
    for name in ("AutoModelForCausalLM", "AutoTokenizer", "BitsAndBytesConfig"):
        setattr(transformers, name, object)
    sys.modules.setdefault("transformers", transformers)


_install_stubs()

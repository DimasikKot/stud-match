import pytest
from fastapi.testclient import TestClient

import main

PROMPT_IDS = [1, 2, 3]


class Ids(list):
    """Минимальная замена torch.Tensor: срезы и .tolist()."""

    def __getitem__(self, item):
        result = super().__getitem__(item)
        return Ids(result) if isinstance(item, slice) else result

    def tolist(self):
        return list(self)


class FakeInputs(dict):
    def __init__(self):
        super().__init__(input_ids=[PROMPT_IDS])

    @property
    def input_ids(self):
        return self["input_ids"]

    def to(self, device):
        return self


class FakeTokenizer:
    def __init__(self):
        self.chat_calls = []

    def apply_chat_template(self, messages, **kwargs):
        self.chat_calls.append((messages, kwargs))
        return "chat-text"

    def __call__(self, texts, return_tensors):
        return FakeInputs()

    def decode(self, ids, skip_special_tokens=True):
        return "".join(VOCAB[i] for i in ids)


VOCAB = {10: "\nдумаю", main.THINK_END_TOKEN_ID: "", 20: "\nответ\n", 21: "!"}


class FakeModel:
    device = "cpu"

    def __init__(self, output_ids=(), chunks=(), error=None):
        self.output_ids, self.chunks, self.error = list(output_ids), chunks, error
        self.calls = []

    def generate(self, max_new_tokens, streamer=None, **inputs):
        self.calls.append(max_new_tokens)
        if self.error:
            raise self.error
        for chunk in self.chunks:
            streamer.on_finalized_text(chunk)
        return [Ids(PROMPT_IDS + self.output_ids)]


@pytest.fixture()
def llm(monkeypatch):
    state = {}
    monkeypatch.setattr(main, "llm", state)

    def _load(**model_kwargs):
        state["tokenizer"] = FakeTokenizer()
        state["model"] = FakeModel(**model_kwargs)
        return state

    return _load


@pytest.fixture()
def client():
    return TestClient(
        main.app
    )  # без `with` — lifespan (загрузка модели) не запускается


def test_health(client, llm):
    assert client.get("/health").json()["loaded"] is False
    llm()
    body = client.get("/health").json()
    assert body["loaded"] is True
    assert body["consumer"] is False


def test_playground(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "/generate/stream" in resp.text


def test_build_inputs_appends_prompt(llm):
    state = llm()
    request = main.GenerateRequest(
        prompt="вопрос",
        messages=[main.Message(role="system", content="будь краток")],
        enable_thinking=False,
    )
    main.build_inputs(request)
    [(messages, kwargs)] = state["tokenizer"].chat_calls
    assert messages == [
        {"role": "system", "content": "будь краток"},
        {"role": "user", "content": "вопрос"},
    ]
    assert kwargs["enable_thinking"] is False
    assert kwargs["add_generation_prompt"] is True


def test_generate_splits_thinking(client, llm):
    state = llm(output_ids=[10, main.THINK_END_TOKEN_ID, 20, 21])
    resp = client.post("/generate", json={"prompt": "hi", "max_new_tokens": 5})
    assert resp.json() == {"thinking": "думаю", "content": "ответ\n!"}
    assert state["model"].calls == [5]


def test_generate_without_thinking(client, llm):
    llm(output_ids=[20, 21])
    resp = client.post("/generate", json={"prompt": "hi", "enable_thinking": False})
    assert resp.json() == {"thinking": "", "content": "ответ\n!"}


def test_generate_validates_max_tokens(client, llm):
    llm()
    assert client.post("/generate", json={"max_new_tokens": 0}).status_code == 422


def test_collect_streamer_skips_empty_chunks(llm):
    streamer = main.CollectStreamer(llm()["tokenizer"])
    for text in ("a", "", "b"):
        streamer.on_finalized_text(text)
    assert streamer.parts == ["a", "b"]


class FakeProducer:
    """Минимальная замена KafkaProducer: send() возвращает объект с .get()."""

    def __init__(self, fail_after_gets=None):
        self.messages = []
        self._fail_after_gets = fail_after_gets
        self._gets = 0

    def send(self, topic, value=None):
        self.messages.append((topic, value))
        return self

    def get(self, timeout=None):
        self._gets += 1
        if self._fail_after_gets is not None and self._gets > self._fail_after_gets:
            raise RuntimeError("kafka down")
        return None


def test_process_task_success(llm):
    state = llm(chunks=["При", "вет"])
    producer = FakeProducer()

    main.process_task(
        producer,
        {
            "task_id": "t1",
            "prompt": "вопрос",
            "enable_thinking": False,
            "max_new_tokens": 7,
        },
    )

    assert state["model"].calls == [7]
    assert producer.messages == [
        (main.RESULTS_TOPIC, {"task_id": "t1", "status": "running"}),
        (main.RESULTS_TOPIC, {"task_id": "t1", "result": "Привет"}),
    ]


def test_process_task_generation_error(llm):
    llm(error=RuntimeError("CUDA OOM"))
    producer = FakeProducer()

    main.process_task(producer, {"task_id": "t1", "prompt": "вопрос"})

    assert producer.messages[-1] == (
        main.RESULTS_TOPIC,
        {"task_id": "t1", "error": "CUDA OOM"},
    )


def test_process_task_survives_result_upload_failure(llm):
    llm(chunks=["ok"])
    # первый send (running) успешен, второй (result) падает
    producer = FakeProducer(fail_after_gets=1)

    main.process_task(producer, {"task_id": "t1", "prompt": "вопрос"})

    assert producer.messages[-1][1]["task_id"] == "t1"

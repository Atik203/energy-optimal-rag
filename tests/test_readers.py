"""Reader contract tests with a mocked Ollama HTTP call."""

from __future__ import annotations

from typing import Any

import pytest
import requests

from rag_energy.readers.base import ReaderError
from rag_energy.readers.ollama_reader import OllamaConfig, OllamaReader


class _Response:
    def __init__(self, payload: dict[str, Any], status: int = 200) -> None:
        self.payload = payload
        self.status = status

    def raise_for_status(self) -> None:
        if self.status >= 400:
            raise requests.HTTPError(f"HTTP {self.status}")

    def json(self) -> dict[str, Any]:
        return self.payload


def test_build_payload_puts_nonce_first_and_keeps_model_loaded() -> None:
    reader = OllamaReader(OllamaConfig(model="qwen3.5:4b", keep_alive="2h"))

    payload = reader.build_payload("Who wrote Hamlet?", ["passage one"], "abc123")

    assert payload["model"] == "qwen3.5:4b"
    assert payload["stream"] is False
    assert payload["think"] is False
    assert payload["keep_alive"] == "2h"
    assert payload["messages"][1]["content"].startswith("[request abc123]")
    assert payload["options"]["num_ctx"] == 4096


def test_generate_parses_text_tokens_and_timings(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []

    def fake_post(url: str, json: dict[str, Any], timeout: float) -> _Response:
        calls.append({"url": url, "json": json, "timeout": timeout})
        return _Response(
            {
                "message": {"content": "William Shakespeare"},
                "prompt_eval_count": 43,
                "eval_count": 3,
                "load_duration": 6_143_002_500,
                "prompt_eval_duration": 44_000_000_000,
                "eval_duration": 41_067_000,
            }
        )

    monkeypatch.setattr(requests, "post", fake_post)
    reader = OllamaReader(OllamaConfig(model="qwen3.5:4b", timeout_s=120.0))

    result = reader.generate("Who wrote Hamlet?", ["Hamlet was written by Shakespeare."], "abc123")

    assert result.text == "William Shakespeare"
    assert result.prompt_tokens == 43
    assert result.output_tokens == 3
    assert result.load_s == pytest.approx(6.1430025)
    assert result.prompt_eval_s == pytest.approx(44.0)
    assert result.eval_s == pytest.approx(0.041067)
    assert result.latency_s >= 0
    assert calls[0]["url"] == "http://127.0.0.1:11434/api/chat"
    assert calls[0]["timeout"] == 120.0


def test_generate_keeps_empty_generation_as_a_wrong_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: _Response({"message": {"content": "  "}}),
    )
    reader = OllamaReader()

    result = reader.generate("Q?", [], "abc123")

    assert result.text == ""


def test_generate_raises_reader_error_on_http_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: _Response({}, status=500),
    )
    reader = OllamaReader()

    with pytest.raises(ReaderError, match="Ollama request failed"):
        reader.generate("Q?", [], "abc123")


def test_generate_raises_reader_error_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout(*args: Any, **kwargs: Any) -> None:
        raise requests.Timeout("slow")

    monkeypatch.setattr(requests, "post", timeout)
    reader = OllamaReader()

    with pytest.raises(ReaderError, match="Ollama request failed"):
        reader.generate("Q?", [], "abc123")

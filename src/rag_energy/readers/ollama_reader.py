"""Ollama reader (primary).

Pilot settings: ``qwen3.5:4b`` Q4, 100% GPU, ``num_ctx=4096``, greedy decoding
(``temperature=0``, ``top_k=1``, ``seed=42``), ``num_predict=24``,
``think=false``.

The HTTP call is implemented in P0. The payload builder is pure so it can be
tested without a running Ollama server.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from rag_energy.readers.base import ReaderResult
from rag_energy.readers.prompts import SYSTEM_PROMPT, build_user_prompt


@dataclass(frozen=True)
class OllamaConfig:
    model: str = "qwen3.5:4b"
    host: str = "http://127.0.0.1:11434"
    num_ctx: int = 4096
    num_predict: int = 24
    temperature: float = 0.0
    top_k: int = 1
    seed: int = 42
    think: bool = False
    timeout_s: float = 120.0


class OllamaReader:
    """Greedy Ollama reader with a fixed prompt."""

    name = "ollama"

    def __init__(self, config: OllamaConfig | None = None) -> None:
        self.config = config or OllamaConfig()

    def build_payload(self, question: str, passages: Sequence[str], nonce: str) -> dict[str, Any]:
        """Build the ``/api/chat`` payload without sending it."""
        return {
            "model": self.config.model,
            "stream": False,
            "think": self.config.think,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(question, passages, nonce)},
            ],
            "options": {
                "temperature": self.config.temperature,
                "top_k": self.config.top_k,
                "seed": self.config.seed,
                "num_ctx": self.config.num_ctx,
                "num_predict": self.config.num_predict,
            },
        }

    def generate(self, question: str, passages: Sequence[str], nonce: str) -> ReaderResult:
        """Send the request and time it. Implemented in P0."""
        raise NotImplementedError(
            "OllamaReader.generate is implemented in P0; see docs/MEASUREMENT.md."
        )

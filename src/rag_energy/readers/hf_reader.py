"""Hugging Face reader (replication).

Replication reader: ``Qwen/Qwen2.5-1.5B-Instruct`` in float16 on the local GPU.
The same fixed prompt and greedy decoding are used as in the Ollama condition.

The model call is implemented in P2. Imports of ``torch`` and ``transformers``
are deferred so this module can be imported without them.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from rag_energy.readers.base import ReaderResult
from rag_energy.readers.prompts import SYSTEM_PROMPT, build_user_prompt


@dataclass(frozen=True)
class HFConfig:
    model: str = "Qwen/Qwen2.5-1.5B-Instruct"
    device: str = "cuda"
    dtype: str = "float16"
    num_ctx: int = 4096
    num_predict: int = 24
    temperature: float = 0.0
    top_k: int = 1
    seed: int = 42


class HFReader:
    """Greedy Hugging Face chat reader."""

    name = "hf"

    def __init__(self, config: HFConfig | None = None) -> None:
        self.config = config or HFConfig()
        self._model = None
        self._tokenizer = None

    def load(self) -> None:
        """Load tokenizer and model. Implemented in P2."""
        raise NotImplementedError("HFReader.load is implemented in P2.")

    def build_messages(self, question: str, passages: Sequence[str], nonce: str) -> list[dict]:
        """Build chat messages without tokenizing."""
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(question, passages, nonce)},
        ]

    def generate(self, question: str, passages: Sequence[str], nonce: str) -> ReaderResult:
        """Generate a short answer. Implemented in P2."""
        raise NotImplementedError("HFReader.generate is implemented in P2.")

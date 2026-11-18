"""Hugging Face reader (replication).

Replication reader: ``Qwen/Qwen2.5-1.5B-Instruct`` in float16 on the local GPU.
The same fixed prompt and greedy decoding are used as in the Ollama condition.

Imports of ``torch`` and ``transformers`` are deferred so this module can be
imported without them. The model is loaded once per process and kept on the
configured device for the whole sweep.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from rag_energy.readers.base import ReaderError, ReaderResult
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
        self._model: Any = None
        self._tokenizer: Any = None
        self._torch: Any = None
        self._device = self.config.device
        self.revision: str | None = None
        self.load_s: float | None = None

    def _torch_dtype(self, torch: Any) -> Any:
        name = self.config.dtype.strip().lower()
        mapping = {
            "float16": torch.float16,
            "fp16": torch.float16,
            "half": torch.float16,
            "bfloat16": torch.bfloat16,
            "bf16": torch.bfloat16,
            "float32": torch.float32,
            "fp32": torch.float32,
            "float": torch.float32,
        }
        if name not in mapping:
            raise ReaderError(f"unsupported HF dtype: {self.config.dtype!r}")
        return mapping[name]

    def load(self) -> None:
        """Load the tokenizer and model once, then keep them resident."""
        if self._model is not None and self._tokenizer is not None:
            return

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:  # pragma: no cover - depends on the environment
            raise ReaderError("the HF reader requires torch and transformers") from exc

        if self.config.temperature != 0.0:
            raise ReaderError("the HF replication reader requires temperature=0 (greedy)")
        if self.config.num_ctx <= self.config.num_predict:
            raise ReaderError("num_ctx must exceed num_predict")

        started = time.perf_counter()
        try:
            tokenizer = AutoTokenizer.from_pretrained(self.config.model)
            model = AutoModelForCausalLM.from_pretrained(
                self.config.model,
                dtype=self._torch_dtype(torch),
            )
            model.to(self._device)
            model.eval()
        except Exception as exc:  # pragma: no cover - depends on model files and GPU
            raise ReaderError(f"failed to load {self.config.model}: {exc}") from exc

        if tokenizer.pad_token_id is None:
            tokenizer.pad_token_id = tokenizer.eos_token_id
        if tokenizer.pad_token_id is None:
            raise ReaderError("tokenizer has neither pad_token_id nor eos_token_id")

        self._torch = torch
        self._tokenizer = tokenizer
        self._model = model
        self.revision = getattr(getattr(model, "config", None), "_commit_hash", None)
        self.load_s = time.perf_counter() - started

    def build_messages(self, question: str, passages: Sequence[str], nonce: str) -> list[dict]:
        """Build chat messages without tokenizing."""
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(question, passages, nonce)},
        ]

    def _apply_template(self, messages: list[dict]) -> str:
        return self._tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    def generate(self, question: str, passages: Sequence[str], nonce: str) -> ReaderResult:
        """Generate one greedy answer and return text, timings, and token counts."""
        self.load()
        torch = self._torch
        tokenizer = self._tokenizer
        model = self._model
        if torch is None or tokenizer is None or model is None:  # pragma: no cover - load guard
            raise ReaderError("HF reader is not loaded")

        prompt = self._apply_template(self.build_messages(question, passages, nonce))
        # Leave room for the generated tokens inside the configured context.
        max_input_tokens = self.config.num_ctx - self.config.num_predict
        encoded = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=max_input_tokens,
        )
        input_ids = encoded["input_ids"].to(self._device)
        prompt_tokens = int(input_ids.shape[1])

        started = time.perf_counter()
        try:
            with torch.inference_mode():
                generated = model.generate(
                    input_ids=input_ids,
                    attention_mask=encoded["attention_mask"].to(self._device),
                    max_new_tokens=self.config.num_predict,
                    do_sample=False,
                    num_beams=1,
                    pad_token_id=tokenizer.pad_token_id,
                )
        except Exception as exc:  # pragma: no cover - depends on the GPU runtime
            raise ReaderError(f"HF generation failed: {exc}") from exc
        latency_s = time.perf_counter() - started

        new_tokens = generated[0, prompt_tokens:]
        output_tokens = int(new_tokens.shape[0])
        text = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

        return ReaderResult(
            text=text,
            latency_s=latency_s,
            prompt_tokens=prompt_tokens,
            output_tokens=output_tokens,
            load_s=0.0,
            prompt_eval_s=None,
            eval_s=latency_s,
        )

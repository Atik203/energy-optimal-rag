"""Reader protocol and result type.

A reader takes a question and an ordered list of passages and returns one short
answer. It must not see the gold answer, the depth label, or any energy value.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


class ReaderError(RuntimeError):
    """A backend request failed before a generation could be scored."""


@dataclass(frozen=True)
class ReaderResult:
    """One generation.

    Attributes:
        text: Raw model output, stripped of the trailing newline.
        latency_s: Wall time of the model call, in seconds.
        prompt_tokens: Prompt tokens if the backend reports them, else ``None``.
        output_tokens: Generated tokens if reported, else ``None``.
        load_s: Model load time if reported, in seconds.
        prompt_eval_s: Prompt-evaluation time if reported, in seconds.
        eval_s: Decode time if reported, in seconds.
    """

    text: str
    latency_s: float
    prompt_tokens: int | None = None
    output_tokens: int | None = None
    load_s: float | None = None
    prompt_eval_s: float | None = None
    eval_s: float | None = None


class Reader(Protocol):
    """Minimal reader interface used by the runner."""

    name: str

    def generate(self, question: str, passages: Sequence[str], nonce: str) -> ReaderResult:
        """Generate a short answer from the question and passages."""
        ...

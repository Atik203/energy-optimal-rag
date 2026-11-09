"""Fixed prompts.

The prompt is frozen across depths. The only per-request variable is the nonce,
which is required to defeat Ollama's prefix cache: without it, a ``k = 32``
request following ``k = 16`` reuses the first 16 passages and cuts prefill time,
confounding depth with request order.
"""

from __future__ import annotations

from collections.abc import Sequence

SYSTEM_PROMPT = (
    "Answer the question using only the provided passages. "
    "If the passages do not contain the answer, reply exactly: unknown. "
    "Reply with a short answer and nothing else."
)

ANSWER_PREFIX = "Answer:"


def build_user_prompt(question: str, passages: Sequence[str], nonce: str) -> str:
    """Build the user message with the nonce first.

    Args:
        question: The question text.
        passages: Ordered passages at the current depth.
        nonce: Unique hex string for this request.

    Returns:
        A prompt whose first line is the nonce, followed by numbered passages,
        the question, and the answer prefix.
    """
    if not nonce:
        raise ValueError("a non-empty nonce is required to defeat prefix caching")
    lines = [f"[request {nonce}]", ""]
    if passages:
        for index, passage in enumerate(passages, start=1):
            lines.append(f"[{index}] {passage}")
    else:
        lines.append("[no passages retrieved]")
    lines.extend(["", f"Question: {question}", ANSWER_PREFIX])
    return "\n".join(lines)

"""Per-request nonce generation.

Ollama reuses KV prefixes. In the pilot, a ``k = 32`` request following
``k = 16`` reused the first 16 passages and cut prefill from 710 ms to 247 ms.
Every request therefore carries a unique 10-hex nonce at the start of the user
message, forcing a full prefill.
"""

from __future__ import annotations

import secrets

DEFAULT_HEX_CHARS = 10


def make_nonce(hex_chars: int = DEFAULT_HEX_CHARS) -> str:
    """Return a cryptographically random hex nonce of ``hex_chars`` characters."""
    if hex_chars <= 0 or hex_chars % 2 != 0:
        raise ValueError("hex_chars must be a positive even integer")
    return secrets.token_hex(hex_chars // 2)


def nonce_line(nonce: str) -> str:
    """Format the nonce as the first line of a user message."""
    if not nonce:
        raise ValueError("nonce must be non-empty")
    return f"[request {nonce}]"

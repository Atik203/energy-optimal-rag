"""Unit tests for answer normalization and the three correctness rules.

Standard library plus pytest only: no numpy, pandas, torch, or GPU.
"""

from __future__ import annotations

import pytest

from rag_energy.scoring import (
    correctness,
    exact_match,
    lenient_span_match,
    normalize_answer,
    token_f1,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("The Quick Brown Fox", "quick brown fox"),
        ("DENVER BRONCOS.", "denver broncos"),
        ("  a  cat\nsat  ", "cat sat"),
        ("An apple, an orange!", "apple orange"),
        ("Don't stop", "dont stop"),
        ("", ""),
        ("   ", ""),
    ],
)
def test_normalize_answer(text: str, expected: str) -> None:
    assert normalize_answer(text) == expected


@pytest.mark.parametrize("text", ["another theater", "theater", "banana"])
def test_normalize_answer_keeps_articles_inside_words(text: str) -> None:
    # \b boundaries mean "a"/"an"/"the" are removed only as whole words.
    assert normalize_answer(text) == text


def test_normalize_answer_is_idempotent() -> None:
    once = normalize_answer("The  Denver, Broncos!")
    assert normalize_answer(once) == once


@pytest.mark.parametrize(
    ("prediction", "gold", "expected"),
    [
        ("The Denver Broncos.", "denver broncos", True),
        ("DENVER BRONCOS", "Denver Broncos", True),
        ("cat", "dog", False),
        ("the cat", "cat", True),
        ("cats", "cat", False),
    ],
)
def test_exact_match(prediction: str, gold: str, expected: bool) -> None:
    assert exact_match(prediction, gold) is expected


@pytest.mark.parametrize(
    ("prediction", "gold", "expected"),
    [
        ("Denver linebacker Von Miller", "Von Miller", True),
        ("von miller", "Von Miller", True),
        ("Von Miller", "Denver linebacker Von Miller", False),
        ("anything", "", False),
        ("anything", "the", False),
        ("cat", "dog", False),
    ],
)
def test_lenient_span_match(prediction: str, gold: str, expected: bool) -> None:
    assert lenient_span_match(prediction, gold) is expected


@pytest.mark.parametrize(
    ("prediction", "gold", "expected"),
    [
        ("w x y", "w x y", 1.0),
        ("x w", "w x", 1.0),
        ("alpha beta", "gamma delta", 0.0),
        ("", "", 1.0),
        ("alpha", "", 0.0),
        ("", "alpha", 0.0),
        # overlap 2, precision 2/3, recall 1 -> F1 = 2*(2/3)/(5/3) = 0.8
        ("w x y", "w x", 0.8),
        # duplicate prediction token counts once: overlap 2, precision 2/3.
        ("w w x", "w x", 0.8),
    ],
)
def test_token_f1(prediction: str, gold: str, expected: float) -> None:
    assert token_f1(prediction, gold) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("prediction", "gold", "rule", "expected"),
    [
        ("The Cat.", "cat", "normalized_em", 1),
        ("a big cat", "cat", "normalized_em", 0),
        ("a big cat", "cat", "lenient_span", 1),
        ("cat", "dog", "lenient_span", 0),
        ("w x y", "w x", "token_f1_ge_0.5", 1),
        ("alpha beta", "gamma delta", "token_f1_ge_0.5", 0),
    ],
)
def test_correctness_dispatches_rules(prediction: str, gold: str, rule: str, expected: int) -> None:
    assert correctness(prediction, gold, rule) == expected


def test_correctness_defaults_to_normalized_em() -> None:
    assert correctness("The Cat.", "cat") == 1
    assert correctness("a big cat", "cat") == 0


def test_correctness_rejects_unknown_rule() -> None:
    with pytest.raises(ValueError, match="unknown correctness rule"):
        correctness("cat", "cat", "rouge_l")

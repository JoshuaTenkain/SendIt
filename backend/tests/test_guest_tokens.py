"""Guest magic-link token tests."""

import time

import pytest

from app.config import settings
from app.utils.tokens import (
    hash_token,
    issue_booking_token,
    issue_quote_token,
    verify_booking_token,
    verify_quote_token,
)


def test_round_trip_quote_token():
    token = issue_quote_token("abc-123", email="jane@example.com")
    payload = verify_quote_token(token)
    assert payload["qid"] == "abc-123"
    assert payload["email"] == "jane@example.com"


def test_round_trip_booking_token():
    token = issue_booking_token("def-456")
    payload = verify_booking_token(token)
    assert payload["bid"] == "def-456"


def test_tampered_token_rejected():
    token = issue_quote_token("abc-123")
    # Flip the last character
    bad = token[:-1] + ("a" if token[-1] != "a" else "b")
    with pytest.raises(ValueError):
        verify_quote_token(bad)


def test_expired_token_rejected(monkeypatch):
    monkeypatch.setattr(settings, "guest_token_max_age_hours", 0)
    token = issue_quote_token("abc-123")
    time.sleep(1.1)
    with pytest.raises(ValueError):
        verify_quote_token(token)


def test_hash_is_stable():
    assert hash_token("abc") == hash_token("abc")
    assert hash_token("abc") != hash_token("abd")

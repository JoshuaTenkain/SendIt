"""Signed tokens for magic-link style guest access.

Uses itsdangerous URLSafeTimedSerializer to issue stateless, expiring tokens
containing a minimal payload (quote_id or booking_id + purpose). We also store
a sha256 of the token on the row to permit single-use or invalidation.
"""

from __future__ import annotations

import hashlib
from typing import Any

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import settings

_QUOTE_SALT = "sendit.quote.v1"
_BOOKING_SALT = "sendit.booking.v1"


def _serializer(salt: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.guest_token_secret, salt=salt)


def issue_quote_token(quote_id: str, *, email: str | None = None) -> str:
    data: dict[str, Any] = {"qid": str(quote_id)}
    if email:
        data["email"] = email
    return _serializer(_QUOTE_SALT).dumps(data)


def verify_quote_token(token: str) -> dict[str, Any]:
    max_age = settings.guest_token_max_age_hours * 3600
    try:
        return _serializer(_QUOTE_SALT).loads(token, max_age=max_age)
    except SignatureExpired as e:
        raise ValueError("Quote link has expired") from e
    except BadSignature as e:
        raise ValueError("Invalid quote link") from e


def issue_booking_token(booking_id: str, *, email: str | None = None) -> str:
    data: dict[str, Any] = {"bid": str(booking_id)}
    if email:
        data["email"] = email
    return _serializer(_BOOKING_SALT).dumps(data)


def verify_booking_token(token: str) -> dict[str, Any]:
    max_age = settings.guest_token_max_age_hours * 3600
    try:
        return _serializer(_BOOKING_SALT).loads(token, max_age=max_age)
    except SignatureExpired as e:
        raise ValueError("Booking link has expired") from e
    except BadSignature as e:
        raise ValueError("Invalid booking link") from e


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

"""Quote generation service.

Supports both authenticated (saved Address rows) and guest (inline address
snapshot) flows. Ranks results by price, then delivery days, then reliability
score. Adapters that fail or time out are skipped gracefully so one broken
courier never blocks a quote.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy.orm import Session
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

from app.integrations.couriers.base import QuoteResult
from app.integrations.couriers.registry import CourierRegistry
from app.models.address import Address
from app.models.courier import Courier
from app.models.quote import Quote

logger = structlog.get_logger()

_ADAPTER_TIMEOUT_S = 8.0
_QUOTE_TTL_MINUTES = 30


def _address_to_dict(a: Address) -> dict:
    return {
        "id": str(a.id),
        "line1": a.line1,
        "line2": a.line2,
        "suburb": a.suburb,
        "city": a.city,
        "province": a.province,
        "postal_code": a.postal_code,
        "country_code": a.country_code,
        "latitude": a.latitude,
        "longitude": a.longitude,
    }


def _rank(
    results: list[QuoteResult], courier_reliability: dict[str, float]
) -> list[QuoteResult]:
    """Default sort: price asc, days asc, -reliability (higher first)."""

    def _key(r: QuoteResult) -> tuple:
        reliability = r.reliability_score or courier_reliability.get(r.courier_code, 0.8)
        return (r.price_total, r.estimated_delivery_days, -reliability)

    return sorted(results, key=_key)


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=0.2, min=0.2, max=1.0),
    reraise=True,
)
async def _adapter_quote(adapter, *, pickup: dict, delivery: dict, parcel: dict) -> list[QuoteResult]:
    return await adapter.get_quote(pickup=pickup, delivery=delivery, parcel=parcel)


def _load_reliability_map(db: Session) -> dict[str, float]:
    rows = db.query(Courier.code, Courier.reliability_score).filter(Courier.is_enabled.is_(True)).all()
    return {code: float(score) for code, score in rows}


def _result_to_dict(r: QuoteResult, courier_id: str | None) -> dict:
    return {
        "courier_id": courier_id,
        "courier_code": r.courier_code,
        "courier_name": r.courier_name,
        "service_level": r.service_level,
        "service_level_display": r.service_level_display or r.service_level,
        "price_total": r.price_total,  # cents
        "currency": r.currency,
        "estimated_delivery_days": r.estimated_delivery_days,
        "reliability_score": r.reliability_score,
        "pricing_breakdown": r.pricing_breakdown,
    }


async def _collect_results(
    *,
    adapters: list,
    pickup_dict: dict,
    delivery_dict: dict,
    parcel: dict,
) -> list[QuoteResult]:
    all_results: list[QuoteResult] = []
    for adapter in adapters:
        try:
            res = await asyncio.wait_for(
                _adapter_quote(
                    adapter, pickup=pickup_dict, delivery=delivery_dict, parcel=parcel
                ),
                timeout=_ADAPTER_TIMEOUT_S,
            )
            all_results.extend(res)
        except asyncio.TimeoutError:
            logger.warning("adapter_timeout", courier_code=getattr(adapter, "courier_code", "?"))
        except RetryError as e:
            logger.warning(
                "adapter_retry_exhausted",
                courier_code=getattr(adapter, "courier_code", "?"),
                error=str(e),
            )
        except Exception as e:  # noqa: BLE001 — don't let a bad adapter block others
            logger.warning(
                "adapter_failed",
                courier_code=getattr(adapter, "courier_code", "?"),
                error=str(e),
            )
    return all_results


async def create_quote(
    *,
    db: Session,
    user_id: uuid.UUID | None,
    pickup_address_id: uuid.UUID | None,
    delivery_address_id: uuid.UUID | None,
    parcel: dict,
    registry: CourierRegistry,
    # Guest flow extras
    pickup_snapshot: dict | None = None,
    delivery_snapshot: dict | None = None,
    urgency: str | None = None,
    budget_zar: int | None = None,
    guest_email: str | None = None,
    guest_phone: str | None = None,
) -> Quote:
    """Create a quote, aggregating live quotes from all enabled couriers.

    At least one of ``pickup_address_id`` or ``pickup_snapshot`` must be
    supplied (same for delivery).
    """
    if pickup_address_id:
        pickup = db.get(Address, pickup_address_id)
        if not pickup:
            raise ValueError("Invalid pickup address")
        pickup_dict = _address_to_dict(pickup)
    elif pickup_snapshot:
        pickup_dict = pickup_snapshot
    else:
        raise ValueError("pickup address required")

    if delivery_address_id:
        delivery = db.get(Address, delivery_address_id)
        if not delivery:
            raise ValueError("Invalid delivery address")
        delivery_dict = _address_to_dict(delivery)
    elif delivery_snapshot:
        delivery_dict = delivery_snapshot
    else:
        raise ValueError("delivery address required")

    adapters = registry.get_enabled(None)
    if not adapters:
        raise ValueError("No couriers available")

    all_results = await _collect_results(
        adapters=adapters, pickup_dict=pickup_dict, delivery_dict=delivery_dict, parcel=parcel
    )

    if not all_results:
        raise ValueError("No quotes returned by any enabled courier")

    reliability_map = _load_reliability_map(db)
    ranked = _rank(all_results, reliability_map)

    # Tag each result with its Courier.id for downstream booking selection
    results_payload = []
    for r in ranked:
        courier_id = registry.courier_id_for_code(r.courier_code)
        results_payload.append(_result_to_dict(r, courier_id))

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=_QUOTE_TTL_MINUTES)

    quote = Quote(
        user_id=user_id,
        pickup_address_id=pickup_address_id,
        delivery_address_id=delivery_address_id,
        pickup_address_snapshot=pickup_dict if not pickup_address_id else None,
        delivery_address_snapshot=delivery_dict if not delivery_address_id else None,
        parcel=parcel,
        results={"quotes": results_payload},
        urgency=urgency,
        budget_zar=budget_zar,
        guest_email=guest_email,
        guest_phone=guest_phone,
        expires_at=expires_at,
        currency="ZAR",
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)
    return quote

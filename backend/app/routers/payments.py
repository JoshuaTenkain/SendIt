from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.payments.payfast import payfast_client
from app.models.booking import Booking
from app.services.booking_service import confirm_payment

router = APIRouter(prefix="/payments", tags=["payments"])

logger = structlog.get_logger()


@router.post("/payfast/notify")
async def payfast_itn(
    request: Request,
    db: Session = Depends(get_db),
    merchant_id: str = Form(...),
    merchant_key: str = Form(...),
    m_payment_id: str = Form(...),
    pf_payment_id: str = Form(...),
    payment_status: str = Form(...),
    amount_gross: str = Form(...),
    signature: str = Form(...),
) -> dict:
    form_data = await request.form()
    post_data = dict(form_data)

    logger.info("payfast_itn_received", payment_id=m_payment_id, status=payment_status, amount=amount_gross)

    signature_valid = payfast_client.verify_itn_signature(post_data)
    if not signature_valid:
        logger.warning("payfast_itn_invalid_signature", payment_id=m_payment_id, signature_valid=False)
        raise HTTPException(status_code=400, detail="Invalid signature")

    client_ip = request.client.host if request.client else "unknown"
    source_valid = await payfast_client.verify_itn_source(client_ip)
    if not source_valid:
        logger.warning("payfast_itn_invalid_source", payment_id=m_payment_id, ip=client_ip, source_valid=False)

    try:
        booking_id = uuid.UUID(m_payment_id)
    except ValueError:
        logger.error("payfast_itn_invalid_booking_id", payment_id=m_payment_id)
        raise HTTPException(status_code=400, detail="Invalid booking ID")

    booking = db.get(Booking, booking_id)
    if not booking:
        logger.error("payfast_itn_booking_not_found", booking_id=booking_id)
        raise HTTPException(status_code=404, detail="Booking not found")

    amount_valid = await payfast_client.verify_payment_amount(post_data, float(booking.price_total))
    if not amount_valid:
        logger.warning(
            "payfast_itn_amount_mismatch",
            booking_id=booking_id,
            expected_amount=float(booking.price_total),
            received_amount=amount_gross,
        )
        raise HTTPException(status_code=400, detail="Amount mismatch")

    if payment_status == "COMPLETE":
        await confirm_payment(
            db=db,
            booking_id=booking_id,
            provider_reference=pf_payment_id,
            raw_payload=post_data,
        )
        logger.info(
            "payfast_itn_payment_confirmed",
            booking_id=booking_id,
            pf_payment_id=pf_payment_id,
            amount=amount_gross,
            status=payment_status,
        )

    return {"status": "ok"}

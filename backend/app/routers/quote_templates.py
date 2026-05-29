"""API endpoints for quote templates."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.quote_template import QuoteTemplateCreate, QuoteTemplateOut, QuoteTemplateUpdate
from app.services.quote_template_service import QuoteTemplateService

router = APIRouter(prefix="/quote-templates", tags=["quote-templates"])


@router.post("/", response_model=QuoteTemplateOut, status_code=201)
def create_template(
    payload: QuoteTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuoteTemplateOut:
    """Create a new quote template."""
    template = QuoteTemplateService.create_template(
        db=db,
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        pickup_address_id=payload.pickup_address_id,
        delivery_address_id=payload.delivery_address_id,
        parcel_template=payload.parcel_template,
        urgency=payload.urgency,
    )
    return QuoteTemplateOut.model_validate(template)


@router.get("/", response_model=list[QuoteTemplateOut])
def list_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[QuoteTemplateOut]:
    """List all quote templates for the current user."""
    templates = QuoteTemplateService.list_templates(db=db, user_id=current_user.id)
    return [QuoteTemplateOut.model_validate(t) for t in templates]


@router.get("/{template_id}", response_model=QuoteTemplateOut)
def get_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuoteTemplateOut:
    """Get a specific quote template."""
    template = QuoteTemplateService.get_template(db=db, template_id=template_id, user_id=current_user.id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return QuoteTemplateOut.model_validate(template)


@router.patch("/{template_id}", response_model=QuoteTemplateOut)
def update_template(
    template_id: uuid.UUID,
    payload: QuoteTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuoteTemplateOut:
    """Update a quote template."""
    template = QuoteTemplateService.update_template(
        db=db,
        template_id=template_id,
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        urgency=payload.urgency,
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return QuoteTemplateOut.model_validate(template)


@router.delete("/{template_id}", status_code=204)
def delete_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a quote template."""
    success = QuoteTemplateService.delete_template(db=db, template_id=template_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")

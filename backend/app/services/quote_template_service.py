"""Quote template service for managing saved routes."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.quote_template import QuoteTemplate

logger = structlog.get_logger()


class QuoteTemplateService:
    """Manage quote templates for users."""

    @staticmethod
    def create_template(
        *,
        db: Session,
        user_id: UUID,
        name: str,
        pickup_address_id: UUID,
        delivery_address_id: UUID,
        parcel_template: dict,
        urgency: str | None = None,
        description: str | None = None,
    ) -> QuoteTemplate:
        """Create a new quote template."""
        template = QuoteTemplate(
            user_id=user_id,
            name=name,
            description=description,
            pickup_address_id=pickup_address_id,
            delivery_address_id=delivery_address_id,
            parcel_template=parcel_template,
            urgency=urgency,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        logger.info("quote_template_created", template_id=template.id, user_id=user_id)
        return template

    @staticmethod
    def get_template(*, db: Session, template_id: UUID, user_id: UUID) -> QuoteTemplate | None:
        """Get a quote template by ID."""
        return db.scalar(
            select(QuoteTemplate).where(
                QuoteTemplate.id == template_id,
                QuoteTemplate.user_id == user_id,
            )
        )

    @staticmethod
    def list_templates(*, db: Session, user_id: UUID) -> list[QuoteTemplate]:
        """List all templates for a user."""
        return list(
            db.scalars(
                select(QuoteTemplate)
                .where(QuoteTemplate.user_id == user_id)
                .order_by(QuoteTemplate.last_used_at.desc(), QuoteTemplate.created_at.desc())
            )
        )

    @staticmethod
    def update_template(
        *,
        db: Session,
        template_id: UUID,
        user_id: UUID,
        name: str | None = None,
        description: str | None = None,
        urgency: str | None = None,
    ) -> QuoteTemplate | None:
        """Update a quote template."""
        template = QuoteTemplateService.get_template(db=db, template_id=template_id, user_id=user_id)
        if not template:
            return None

        if name is not None:
            template.name = name
        if description is not None:
            template.description = description
        if urgency is not None:
            template.urgency = urgency

        db.commit()
        db.refresh(template)
        logger.info("quote_template_updated", template_id=template_id)
        return template

    @staticmethod
    def delete_template(*, db: Session, template_id: UUID, user_id: UUID) -> bool:
        """Delete a quote template."""
        template = QuoteTemplateService.get_template(db=db, template_id=template_id, user_id=user_id)
        if not template:
            return False

        db.delete(template)
        db.commit()
        logger.info("quote_template_deleted", template_id=template_id)
        return True

    @staticmethod
    def increment_usage(*, db: Session, template_id: UUID) -> bool:
        """Increment usage count and update last_used_at."""
        template = db.get(QuoteTemplate, template_id)
        if not template:
            return False

        template.usage_count = (template.usage_count or 0) + 1
        template.last_used_at = datetime.now(timezone.utc)
        db.commit()
        return True

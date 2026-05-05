"""add quote results

Revision ID: 0002_add_quote_results
Revises: 0001_init_schema
Create Date: 2026-03-08

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_add_quote_results"
down_revision = "0001_init_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("quotes", sa.Column("results", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("quotes", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_quotes_expires_at", "quotes", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_quotes_expires_at", table_name="quotes")
    op.drop_column("quotes", "expires_at")
    op.drop_column("quotes", "results")

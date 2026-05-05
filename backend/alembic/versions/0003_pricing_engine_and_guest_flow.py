"""pricing engine + guest flow + courier ranking fields

Revision ID: 0003_pricing_and_guest
Revises: 0002_add_quote_results
Create Date: 2026-04-20

Adds:
  * ``price_tables`` + ``price_table_rows`` for CSV-uploaded courier rate cards
  * ``surcharge_rules`` for rule-based fees (fuel levy, outlying, insurance, ...)
  * Guest-flow columns on ``quotes`` and ``bookings``
  * Ranking / integration columns on ``couriers``
  * Fixes the old ``uq_bookings_user_id_idempotency_key`` to permit nullable
    user_id (by dropping + recreating as a partial index on authed rows).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_pricing_and_guest"
down_revision = "0002_add_quote_results"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- couriers: ranking + integration ----------------------------------
    op.add_column(
        "couriers",
        sa.Column("supports_api", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("couriers", sa.Column("adapter_code", sa.String(length=50), nullable=True))
    op.add_column(
        "couriers",
        sa.Column(
            "reliability_score",
            sa.Numeric(3, 2),
            nullable=False,
            server_default=sa.text("0.80"),
        ),
    )
    op.add_column("couriers", sa.Column("logo_url", sa.Text(), nullable=True))
    op.create_check_constraint(
        "ck_couriers_reliability_range",
        "couriers",
        "reliability_score >= 0 AND reliability_score <= 1",
    )

    # --- quotes: guest flow -----------------------------------------------
    # Relax NOT NULL on FK address columns so guest quotes can use snapshots
    op.alter_column("quotes", "pickup_address_id", existing_type=postgresql.UUID(), nullable=True)
    op.alter_column("quotes", "delivery_address_id", existing_type=postgresql.UUID(), nullable=True)

    op.add_column("quotes", sa.Column("pickup_address_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("quotes", sa.Column("delivery_address_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("quotes", sa.Column("urgency", sa.String(length=30), nullable=True))
    op.add_column("quotes", sa.Column("budget_zar", sa.Integer(), nullable=True))
    op.add_column("quotes", sa.Column("guest_email", sa.String(length=255), nullable=True))
    op.add_column("quotes", sa.Column("guest_phone", sa.String(length=40), nullable=True))
    op.create_index("ix_quotes_guest_email", "quotes", ["guest_email"], unique=False)

    # --- bookings: guest flow, cancel, breakdown, short code --------------
    # Drop prior composite unique index that assumed NOT NULL user_id
    op.execute("DROP INDEX IF EXISTS uq_bookings_user_id_idempotency_key")
    op.alter_column("bookings", "user_id", existing_type=postgresql.UUID(), nullable=True)

    op.add_column("bookings", sa.Column("guest_email", sa.String(length=255), nullable=True))
    op.add_column("bookings", sa.Column("guest_phone", sa.String(length=40), nullable=True))
    op.add_column("bookings", sa.Column("public_short_code", sa.String(length=20), nullable=True))
    op.add_column("bookings", sa.Column("pricing_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("bookings", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("bookings", sa.Column("cancel_reason", sa.String(length=255), nullable=True))

    op.create_index("ix_bookings_guest_email", "bookings", ["guest_email"], unique=False)
    op.create_index("uq_bookings_public_short_code", "bookings", ["public_short_code"], unique=True)

    # Re-add idempotency uniqueness as two partial indexes
    op.execute(
        "CREATE UNIQUE INDEX uq_bookings_user_idem "
        "ON bookings(user_id, idempotency_key) WHERE user_id IS NOT NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_bookings_guest_idem "
        "ON bookings(guest_email, idempotency_key) WHERE user_id IS NULL AND guest_email IS NOT NULL"
    )

    # --- price_tables -----------------------------------------------------
    op.create_table(
        "price_tables",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "courier_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("couriers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="ZAR"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "uploaded_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("char_length(currency) = 3", name="ck_price_tables_currency_len"),
        sa.CheckConstraint("version >= 1", name="ck_price_tables_version_pos"),
    )
    op.create_index("ix_price_tables_courier_id", "price_tables", ["courier_id"], unique=False)
    op.create_index("ix_price_tables_is_active", "price_tables", ["is_active"], unique=False)

    # --- price_table_rows -------------------------------------------------
    op.create_table(
        "price_table_rows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "price_table_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("price_tables.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("service_level", sa.String(length=60), nullable=False),
        sa.Column("service_level_display", sa.String(length=120), nullable=True),
        sa.Column("weight_from_kg", sa.Numeric(7, 2), nullable=False),
        sa.Column("weight_to_kg", sa.Numeric(7, 2), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("estimated_delivery_days", sa.Integer(), nullable=False, server_default="2"),
        sa.CheckConstraint("weight_from_kg >= 0", name="ck_price_rows_from_nonneg"),
        sa.CheckConstraint("weight_to_kg > weight_from_kg", name="ck_price_rows_to_gt_from"),
        sa.CheckConstraint("price_cents >= 0", name="ck_price_rows_price_nonneg"),
        sa.CheckConstraint("estimated_delivery_days >= 0", name="ck_price_rows_days_nonneg"),
        sa.UniqueConstraint(
            "price_table_id", "service_level", "weight_from_kg",
            name="uq_price_rows_table_service_from",
        ),
    )
    op.create_index(
        "ix_price_table_rows_price_table_id",
        "price_table_rows",
        ["price_table_id"],
        unique=False,
    )
    op.create_index(
        "ix_price_table_rows_service_level",
        "price_table_rows",
        ["service_level"],
        unique=False,
    )

    # --- surcharge_rules --------------------------------------------------
    op.create_table(
        "surcharge_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "courier_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("couriers.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("surcharge_type", sa.String(length=30), nullable=False),
        sa.Column("value", sa.Numeric(10, 4), nullable=False),
        sa.Column("applies_when", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "surcharge_type IN ('percent','flat','percent_of_declared')",
            name="ck_surcharge_type_valid",
        ),
    )
    op.create_index("ix_surcharge_rules_courier_id", "surcharge_rules", ["courier_id"], unique=False)
    op.create_index("ix_surcharge_rules_code", "surcharge_rules", ["code"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_surcharge_rules_code", table_name="surcharge_rules")
    op.drop_index("ix_surcharge_rules_courier_id", table_name="surcharge_rules")
    op.drop_table("surcharge_rules")

    op.drop_index("ix_price_table_rows_service_level", table_name="price_table_rows")
    op.drop_index("ix_price_table_rows_price_table_id", table_name="price_table_rows")
    op.drop_table("price_table_rows")

    op.drop_index("ix_price_tables_is_active", table_name="price_tables")
    op.drop_index("ix_price_tables_courier_id", table_name="price_tables")
    op.drop_table("price_tables")

    op.execute("DROP INDEX IF EXISTS uq_bookings_guest_idem")
    op.execute("DROP INDEX IF EXISTS uq_bookings_user_idem")
    op.drop_index("uq_bookings_public_short_code", table_name="bookings")
    op.drop_index("ix_bookings_guest_email", table_name="bookings")
    op.drop_column("bookings", "cancel_reason")
    op.drop_column("bookings", "cancelled_at")
    op.drop_column("bookings", "pricing_breakdown")
    op.drop_column("bookings", "public_short_code")
    op.drop_column("bookings", "guest_phone")
    op.drop_column("bookings", "guest_email")
    op.execute(
        "CREATE UNIQUE INDEX uq_bookings_user_id_idempotency_key "
        "ON bookings(user_id, idempotency_key)"
    )
    op.alter_column("bookings", "user_id", existing_type=postgresql.UUID(), nullable=False)

    op.drop_index("ix_quotes_guest_email", table_name="quotes")
    op.drop_column("quotes", "guest_phone")
    op.drop_column("quotes", "guest_email")
    op.drop_column("quotes", "budget_zar")
    op.drop_column("quotes", "urgency")
    op.drop_column("quotes", "delivery_address_snapshot")
    op.drop_column("quotes", "pickup_address_snapshot")
    op.alter_column("quotes", "delivery_address_id", existing_type=postgresql.UUID(), nullable=False)
    op.alter_column("quotes", "pickup_address_id", existing_type=postgresql.UUID(), nullable=False)

    op.drop_constraint("ck_couriers_reliability_range", "couriers", type_="check")
    op.drop_column("couriers", "logo_url")
    op.drop_column("couriers", "reliability_score")
    op.drop_column("couriers", "adapter_code")
    op.drop_column("couriers", "supports_api")

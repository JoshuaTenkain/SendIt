"""init schema

Revision ID: 0001_init_schema
Revises: 
Create Date: 2026-03-08

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_init_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=120), nullable=True),
        sa.Column("last_name", sa.String(length=120), nullable=True),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_admin", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("email <> ''", name="ck_users_email_not_empty"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "addresses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=True),
        sa.Column("line1", sa.String(length=255), nullable=False),
        sa.Column("line2", sa.String(length=255), nullable=True),
        sa.Column("suburb", sa.String(length=120), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("province", sa.String(length=120), nullable=True),
        sa.Column("postal_code", sa.String(length=20), nullable=False),
        sa.Column("country_code", sa.String(length=2), server_default=sa.text("'ZA'"), nullable=False),
        sa.Column("latitude", sa.String(length=32), nullable=True),
        sa.Column("longitude", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.CheckConstraint("line1 <> ''", name="ck_addresses_line1_not_empty"),
        sa.CheckConstraint("city <> ''", name="ck_addresses_city_not_empty"),
        sa.CheckConstraint("postal_code <> ''", name="ck_addresses_postal_code_not_empty"),
        sa.CheckConstraint("char_length(country_code) = 2", name="ck_addresses_country_code_len"),
    )
    op.create_index("ix_addresses_user_id", "addresses", ["user_id"], unique=False)

    op.create_table(
        "couriers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("base_markup_pct", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("commission_pct", sa.Integer(), server_default=sa.text("10"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("code <> ''", name="ck_couriers_code_not_empty"),
        sa.CheckConstraint("name <> ''", name="ck_couriers_name_not_empty"),
        sa.CheckConstraint("base_markup_pct >= 0", name="ck_couriers_base_markup_nonneg"),
        sa.CheckConstraint("commission_pct >= 0", name="ck_couriers_commission_nonneg"),
        sa.CheckConstraint("rating IS NULL OR (rating >= 1 AND rating <= 5)", name="ck_couriers_rating_range"),
    )
    op.create_index("ix_couriers_code", "couriers", ["code"], unique=True)

    op.create_table(
        "quotes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("pickup_address_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("delivery_address_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parcel", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default=sa.text("'ZAR'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["pickup_address_id"], ["addresses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["delivery_address_id"], ["addresses.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("char_length(currency) = 3", name="ck_quotes_currency_len"),
    )
    op.create_index("ix_quotes_user_id", "quotes", ["user_id"], unique=False)

    op.create_table(
        "bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("courier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("courier_service_level", sa.String(length=80), nullable=True),
        sa.Column("price_subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("price_tax", sa.Numeric(12, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("price_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default=sa.text("'ZAR'"), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("idempotency_key", sa.String(length=80), nullable=False),
        sa.Column("external_shipment_id", sa.String(length=120), nullable=True),
        sa.Column("tracking_reference", sa.String(length=120), nullable=True),
        sa.Column("courier_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["courier_id"], ["couriers.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("char_length(currency) = 3", name="ck_bookings_currency_len"),
        sa.CheckConstraint("idempotency_key <> ''", name="ck_bookings_idempotency_not_empty"),
        sa.CheckConstraint("status <> ''", name="ck_bookings_status_not_empty"),
        sa.UniqueConstraint("quote_id", name="uq_bookings_quote_id"),
    )
    op.create_index("ix_bookings_user_id", "bookings", ["user_id"], unique=False)
    op.create_index("ix_bookings_courier_id", "bookings", ["courier_id"], unique=False)
    op.create_index("ix_bookings_status", "bookings", ["status"], unique=False)
    op.create_index("ix_bookings_external_shipment_id", "bookings", ["external_shipment_id"], unique=False)
    op.create_index("ix_bookings_tracking_reference", "bookings", ["tracking_reference"], unique=False)
    op.create_index("ix_bookings_user_id_created_at", "bookings", ["user_id", "created_at"], unique=False)
    op.create_index("ix_bookings_courier_id_created_at", "bookings", ["courier_id", "created_at"], unique=False)
    op.create_index(
        "uq_bookings_user_id_idempotency_key",
        "bookings",
        ["user_id", "idempotency_key"],
        unique=True,
    )

    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=40), server_default=sa.text("'payfast'"), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default=sa.text("'ZAR'"), nullable=False),
        sa.Column("provider_reference", sa.String(length=120), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="CASCADE"),
        sa.CheckConstraint("char_length(currency) = 3", name="ck_transactions_currency_len"),
        sa.CheckConstraint("provider <> ''", name="ck_transactions_provider_not_empty"),
        sa.CheckConstraint("status <> ''", name="ck_transactions_status_not_empty"),
        sa.UniqueConstraint("booking_id", name="uq_transactions_booking_id"),
    )
    op.create_index("ix_transactions_status", "transactions", ["status"], unique=False)
    op.create_index("ix_transactions_provider_reference", "transactions", ["provider_reference"], unique=False)
    op.create_index("ix_transactions_status_created_at", "transactions", ["status", "created_at"], unique=False)

    op.create_table(
        "tracking_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=60), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=120), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="CASCADE"),
        sa.CheckConstraint("status <> ''", name="ck_tracking_events_status_not_empty"),
    )
    op.create_index("ix_tracking_events_booking_id", "tracking_events", ["booking_id"], unique=False)
    op.create_index(
        "ix_tracking_events_booking_id_occurred_at",
        "tracking_events",
        ["booking_id", "occurred_at"],
        unique=False,
    )

    op.create_table(
        "commission_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("courier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("commission_pct", sa.Integer(), nullable=False),
        sa.Column("commission_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default=sa.text("'ZAR'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["courier_id"], ["couriers.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("char_length(currency) = 3", name="ck_commission_records_currency_len"),
        sa.CheckConstraint("commission_pct >= 0", name="ck_commission_records_commission_nonneg"),
        sa.UniqueConstraint("booking_id", name="uq_commission_records_booking_id"),
    )
    op.create_index("ix_commission_records_courier_id", "commission_records", ["courier_id"], unique=False)
    op.create_index(
        "ix_commission_records_courier_id_created_at",
        "commission_records",
        ["courier_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("commission_records")
    op.drop_table("tracking_events")
    op.drop_table("transactions")
    op.drop_table("bookings")
    op.drop_table("quotes")
    op.drop_table("couriers")
    op.drop_table("addresses")
    op.drop_table("users")

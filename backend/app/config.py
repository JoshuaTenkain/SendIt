from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SENDIT_", extra="ignore")

    env: str = "dev"

    database_url: str = "postgresql+psycopg://sendit:sendit@localhost:5432/sendit"

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_exp_minutes: int = 60

    sendgrid_api_key: str | None = None
    sendgrid_from_email: str = "no-reply@send-it.local"

    payfast_merchant_id: str | None = None
    payfast_merchant_key: str | None = None
    payfast_passphrase: str | None = None
    payfast_sandbox: bool = True

    google_maps_api_key: str | None = None

    # The Courier Guy / Shiplogic
    tcg_enabled: bool = False
    tcg_base_url: str = "https://api.shiplogic.com"
    tcg_api_token: str | None = None
    tcg_webhook_secret: str | None = None
    tcg_default_collection_email: str = "ops@send-it.local"
    tcg_default_collection_mobile: str = "0000000000"

    # Public URL bases (used for guest magic links + webhook notify URLs)
    frontend_base_url: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"

    # Guest quote tokens
    guest_token_secret: str = "change-me-guest"
    guest_token_max_age_hours: int = 72

    # Stripe (subscriptions)
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None

    # VAT
    vat_rate_pct: int = 15


settings = Settings()
